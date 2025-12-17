"""Guided Convergence Loop orchestration scaffolding."""
from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from llm_patch.patch_applier import PatchApplier, normalize_replacement_block
PATCH_CONSTRAINTS_TEXT = "\n".join(
    [
        "- Do not reformat unrelated code.",
        "- Do not rename symbols.",
        "- Change only within this method unless strictly necessary.",
        "- Prefer the smallest valid replacement and include only the lines that must change.",
    ]
)

PATCH_EXAMPLE_DIFF = (
    "ORIGINAL LINES:\n"
    "return tokens.stream()\n"
    "        .map(token -> token.equals(\"-\") && inPrefixContext(previous))\n"
    "                ? \"0-\" : token);\n"
    "NEW LINES:\n"
    "return tokens.stream()\n"
    "        .map(token -> token.equals(\"-\") && inPrefixContext(previous)\n"
    "                ? \"0-\" : token)\n"
    "        .collect(Collectors.toList());\n"
)

REPLACEMENT_BLOCK_PATTERN = re.compile(
    r"ORIGINAL LINES:\s*\n(?P<original>.*?)\nNEW LINES:\s*\n(?P<updated>.*?)(?=(?:\nORIGINAL LINES:|\Z))",
    re.DOTALL,
)

from ..base import PatchRequest, PatchResult, PatchStrategy, StrategyEvent, StrategyEventKind
from .phases import (
    GuidedIterationArtifact,
    GuidedLoopTrace,
    GuidedPhase,
    PhaseArtifact,
    PhaseStatus,
)
from .prompt_fragments import (
    CONSTRAINTS_FRAGMENT,
    CONTEXT_FRAGMENT,
    CRITIQUE_FRAGMENT,
    CRITIQUE_OUTPUT_FRAGMENT,
    DIAGNOSE_INSTRUCTIONS_FRAGMENT,
    DIAGNOSIS_RATIONALE_FRAGMENT,
    DIAGNOSIS_OUTPUT_FRAGMENT,
    DIAGNOSIS_SUMMARY_FRAGMENT,
    ERROR_FRAGMENT,
    EXAMPLE_REPLACEMENT_FRAGMENT,
    EXPERIMENT_INSTRUCTIONS_FRAGMENT,
    EXPERIMENT_SUMMARY_FRAGMENT,
    GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
    HISTORY_FRAGMENT,
    PATCH_DIAGNOSTICS_FRAGMENT,
    PRIOR_PATCH_FRAGMENT,
    PREVIOUS_DIFF_FRAGMENT,
    PROPOSE_INSTRUCTIONS_FRAGMENT,
    REFINEMENT_CONTEXT_FRAGMENT,
    PROPOSAL_SUMMARY_FRAGMENT,
    compose_prompt,
)


class LLMClient(Protocol):
    """Minimal client interface that the controller depends on."""

    def complete(self, *, prompt: str, temperature: float, model: Optional[str] = None) -> str:  # pragma: no cover - protocol
        """Return a text completion for ``prompt``."""


@dataclass(slots=True)
class GuidedLoopConfig:
    """Runtime configuration for the guided loop strategy."""

    max_iterations: int = 1
    refine_sub_iterations: int = 3
    interpreter_model: str = "planner"
    patch_model: str = "patcher"
    critique_model: Optional[str] = None
    temperature: float = 0.0
    auto_constraints: bool = True
    compile_check: bool = True

    def total_iterations(self) -> int:
        base = max(1, self.max_iterations)
        refinements = max(0, self.refine_sub_iterations)
        return base + refinements

@dataclass(slots=True)
class GuidedLoopInputs(PatchRequest):
    """Adds guided-loop specific context to the base patch request."""

    compile_command: Optional[Sequence[str]] = None
    additional_context: Mapping[str, Any] = field(default_factory=dict)
    history_seed: Sequence[str] = field(default_factory=tuple)
    initial_outcome: Optional[Mapping[str, Any]] = None


@dataclass(slots=True)
class GuidedLoopResult(PatchResult):
    """Extends the base ``PatchResult`` with a structured trace."""

    trace: GuidedLoopTrace | None = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None
    patch_diagnostics: Optional[str] = None


@dataclass(slots=True)
class IterationOutcome:
    """Container for deterministic critique + compile results."""

    diff_text: Optional[str] = None
    patched_text: Optional[str] = None
    patch_applied: bool = False
    patch_diagnostics: Optional[str] = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None
    critique_feedback: Optional[str] = None
    hypothesis_id: Optional[str] = None
    error_fingerprint: Optional[str] = None
    previous_error_fingerprint: Optional[str] = None
    diff_span: Optional[Tuple[int, int]] = None
    error_message: Optional[str] = None
    error_location: Optional[int] = None

    @property
    def compile_success(self) -> bool:
        return self.compile_returncode == 0 if self.compile_returncode is not None else False


class GuidedConvergenceStrategy(PatchStrategy):
    """High-level orchestration of the Guided Convergence Loop."""

    name = "guided-loop"

    PROMPT_TEMPLATES: Mapping[GuidedPhase, str] = {
        GuidedPhase.DIAGNOSE: compose_prompt(
            DIAGNOSE_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            ERROR_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.PLANNING: compose_prompt(
            EXPERIMENT_INSTRUCTIONS_FRAGMENT,
            DIAGNOSIS_OUTPUT_FRAGMENT,
            CRITIQUE_OUTPUT_FRAGMENT,
        ),
        GuidedPhase.PROPOSE: compose_prompt(
            PROPOSE_INSTRUCTIONS_FRAGMENT,
            REFINEMENT_CONTEXT_FRAGMENT,
            HISTORY_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PREVIOUS_DIFF_FRAGMENT,
            ERROR_FRAGMENT,
            EXPERIMENT_SUMMARY_FRAGMENT,
            CONTEXT_FRAGMENT
        ),
        GuidedPhase.GENERATE_PATCH: compose_prompt(
            GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PREVIOUS_DIFF_FRAGMENT,
            PROPOSAL_SUMMARY_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            CONTEXT_FRAGMENT,
            CONSTRAINTS_FRAGMENT,
            EXAMPLE_REPLACEMENT_FRAGMENT,
        ),
        GuidedPhase.CRITIQUE: (
            "Critique the replacement block(s). Do they respect the constraints? Identify non-minimal or risky edits."
        ),
    }

    def __init__(
        self,
        client: LLMClient | None = None,
        config: GuidedLoopConfig | None = None,
        observer=None,
    ) -> None:
        super().__init__(observer)
        self._client = client
        self._config = config or GuidedLoopConfig()
        self._patch_applier = PatchApplier()
        self._baseline_error_fingerprint: Optional[str] = None
        self._latest_diagnosis_output: Optional[str] = None
        self._critique_transcripts: list[str] = []

    def run(self, request: PatchRequest) -> GuidedLoopResult:
        inputs = self._ensure_inputs(request)
        self._latest_diagnosis_output = None
        self._critique_transcripts = []
        self._baseline_error_fingerprint = self._error_fingerprint(inputs.error_text)
        trace = self._plan_trace(inputs)
        planning_event = self._event(
            kind=StrategyEventKind.NOTE,
            message="Guided loop plan generated",
            data={"iterations": len(trace.iterations), "mode": "guided-loop"},
        )
        self.emit(planning_event)
        events: List[StrategyEvent] = [planning_event]
        history_log = self._initial_history(inputs)
        prior_outcome = self._seed_prior_outcome(inputs)
        iteration_outcome: IterationOutcome | None = prior_outcome
        for iteration in trace.iterations:
            history_context = self._format_history(history_log)
            iteration.history_context = history_context
            iteration_events, iteration_outcome = self._execute_iteration(
                iteration,
                inputs,
                prior_outcome=prior_outcome,
                history_context=history_context,
            )
            events.extend(iteration_events)
            if iteration_outcome:
                history_entry = self._history_entry(iteration.index, iteration_outcome)
                iteration.history_entry = history_entry
                history_log.append(history_entry)
                post_iteration_events = self._post_iteration_evaluation(iteration, iteration_outcome, prior_outcome)
                events.extend(post_iteration_events)
            prior_outcome = iteration_outcome
            if iteration_outcome and iteration_outcome.patch_applied and (
                not self._config.compile_check
                or not inputs.compile_command
                or iteration_outcome.compile_success
            ):
                break
        applied = iteration_outcome.patch_applied if iteration_outcome else False
        success = iteration_outcome.compile_success if iteration_outcome else False
        after_text = iteration_outcome.patched_text if iteration_outcome and iteration_outcome.patch_applied else None
        diff_text = iteration_outcome.diff_text if iteration_outcome else None
        compile_returncode = iteration_outcome.compile_returncode if iteration_outcome else None
        compile_stdout = iteration_outcome.compile_stdout if iteration_outcome else None
        compile_stderr = iteration_outcome.compile_stderr if iteration_outcome else None
        patch_diagnostics = iteration_outcome.patch_diagnostics if iteration_outcome else None
        notes = self._result_notes(iteration_outcome)
        return GuidedLoopResult(
            applied=applied,
            success=success,
            after_text=after_text,
            diff_text=diff_text,
            notes=notes,
            events=events,
            artifacts=[iteration.to_dict() for iteration in trace.iterations],
            trace=trace,
            compile_returncode=compile_returncode,
            compile_stdout=compile_stdout,
            compile_stderr=compile_stderr,
            patch_diagnostics=patch_diagnostics,
        )

    # ------------------------------------------------------------------
    def _ensure_inputs(self, request: PatchRequest) -> GuidedLoopInputs:
        if isinstance(request, GuidedLoopInputs):
            return request
        extra_context: Mapping[str, Any] = dict(request.extra or {})
        history_seed_value = extra_context.get("history_seed", [])
        if isinstance(history_seed_value, str):
            history_seed: Sequence[str] = (history_seed_value,)
        elif isinstance(history_seed_value, Sequence):
            history_seed = tuple(str(item) for item in history_seed_value)
        else:
            history_seed = tuple()
        initial_outcome_value = extra_context.get("initial_outcome")
        initial_outcome = initial_outcome_value if isinstance(initial_outcome_value, Mapping) else None
        return GuidedLoopInputs(
            case_id=request.case_id,
            language=request.language,
            source_path=request.source_path,
            source_text=request.source_text,
            error_text=request.error_text,
            manifest=request.manifest,
            extra=request.extra,
            additional_context=extra_context,
            history_seed=history_seed,
            initial_outcome=initial_outcome,
        )

    def _seed_prior_outcome(self, inputs: GuidedLoopInputs) -> IterationOutcome | None:
        payload = inputs.initial_outcome or inputs.additional_context.get("initial_outcome")
        if not payload or not isinstance(payload, Mapping):
            return None
        return IterationOutcome(
            diff_text=payload.get("diff_text"),
            patched_text=payload.get("patched_text"),
            patch_applied=bool(payload.get("patch_applied", False)),
            patch_diagnostics=payload.get("patch_diagnostics"),
            compile_returncode=payload.get("compile_returncode"),
            compile_stdout=payload.get("compile_stdout"),
            compile_stderr=payload.get("compile_stderr"),
            critique_feedback=payload.get("critique_feedback"),
        )

    def _initial_history(self, inputs: GuidedLoopInputs) -> List[str]:
        entries: List[str] = []
        entries.extend(self._coerce_history_entries(inputs.history_seed))
        entries.extend(self._coerce_history_entries(inputs.additional_context.get("history_seed")))
        return entries

    def _format_history(self, entries: Sequence[str], limit: int = 5) -> str:
        filtered = [entry for entry in entries if entry]
        if not filtered:
            return self._history_placeholder()
        tail = filtered[-limit:]
        return "\n".join(f"- {entry}" for entry in tail)

    def _history_entry(self, iteration_index: int, outcome: IterationOutcome) -> str:
        patch_state = "applied" if outcome.patch_applied else "not applied"
        if outcome.patch_applied:
            if outcome.compile_returncode is None:
                compile_desc = "compile/test skipped"
            elif outcome.compile_success:
                compile_desc = "compile/test passed"
            else:
                compile_desc = f"compile/test failed (rc={outcome.compile_returncode})"
        else:
            compile_desc = outcome.patch_diagnostics or "patch unavailable"
        critique_line = ""
        if outcome.critique_feedback:
            head = outcome.critique_feedback.strip().splitlines()[0].strip()
            if head:
                critique_line = f"critique: {head}"
        parts = [f"Loop {iteration_index}: patch {patch_state}", compile_desc]
        if critique_line:
            parts.append(critique_line)
        return "; ".join(parts)

    @staticmethod
    def _coerce_history_entries(source: Any) -> List[str]:
        if not source:
            return []
        if isinstance(source, str):
            text = source.strip()
            return [text] if text else []
        if isinstance(source, Sequence):
            entries: List[str] = []
            for item in source:
                if item is None:
                    continue
                text = str(item).strip()
                if text:
                    entries.append(text)
            return entries
        text = str(source).strip()
        return [text] if text else []

    def _plan_trace(self, request: GuidedLoopInputs) -> GuidedLoopTrace:
        trace = GuidedLoopTrace(
            strategy=self.name,
            target_language=request.language,
            case_id=request.case_id,
            build_command=" ".join(request.compile_command or []) or None,
        )
        primary_iterations = max(1, self._config.max_iterations)
        refine_iterations = max(0, self._config.refine_sub_iterations)
        total_iterations = primary_iterations + refine_iterations
        for iteration_index in range(1, total_iterations + 1):
            if iteration_index <= primary_iterations:
                iteration_kind = "primary"
                label = f"Loop {iteration_index}"
            else:
                iteration_kind = "refine"
                refine_position = iteration_index - primary_iterations
                label = f"Refine {refine_position}"
            iteration = GuidedIterationArtifact(index=iteration_index, kind=iteration_kind, label=label)
            for phase in self._phase_order(kind=iteration_kind):
                prompt = self._render_prompt(phase, request)
                artifact = PhaseArtifact(phase=phase, status=PhaseStatus.PLANNED, prompt=prompt)
                trace.add_phase(iteration, artifact)
            trace.iterations.append(iteration)
        trace.notes = (
            "Trace contains prompt templates only. Actual execution will attach responses, checks, "
            "and iteration history entries for each loop."
        )
        return trace

    def _phase_order(self, *, kind: str = "primary") -> List[GuidedPhase]:
        if kind == "refine":
            return [
                GuidedPhase.PLANNING,
                GuidedPhase.PROPOSE,
                GuidedPhase.GENERATE_PATCH,
                GuidedPhase.CRITIQUE,
            ]
        return [
            GuidedPhase.DIAGNOSE,
            GuidedPhase.PLANNING,
            GuidedPhase.PROPOSE,
            GuidedPhase.GENERATE_PATCH,
            GuidedPhase.CRITIQUE,
        ]

    def _render_prompt(
        self,
        phase: GuidedPhase,
        request: GuidedLoopInputs,
        *,
        context_override: Optional[str] = None,
        extra: Optional[Mapping[str, str]] = None,
    ) -> str:
        template = self.PROMPT_TEMPLATES[phase]
        filename = request.source_path.name
        context = context_override if context_override is not None else self._context_for_phase(phase, request)
        data: Dict[str, str] = {
            "language": request.language,
            "error": request.error_text or "(error unavailable)",
            "context": context,
            "filename": filename,
            "diagnosis": self._diagnosis_placeholder(),
            "diagnosis_explanation": self._diagnosis_explanation_placeholder(),
            "proposal": self._proposal_placeholder(),
            "constraints": PATCH_CONSTRAINTS_TEXT,
            "example_diff": PATCH_EXAMPLE_DIFF,
            "critique_feedback": self._critique_placeholder(),
            "previous_diff": self._previous_diff_placeholder(),
            "patch_diagnostics": "",
            "history_context": self._history_placeholder(),
            "prior_patch_summary": self._prior_patch_placeholder(),
            "refinement_context": self._refinement_context_placeholder(),
            "diagnosis_output": self._diagnosis_output_placeholder(),
            "experiment_summary": self._experiment_summary_placeholder(),
            "critique_output": self._critique_output_placeholder(),
        }
        if extra:
            data.update({key: value for key, value in extra.items() if value is not None})
        populated = template.format(**data)
        return self._strip_placeholder_sections(populated)

    @classmethod
    def _placeholder_texts(cls) -> set[str]:
        return {
            cls._history_placeholder(),
            cls._critique_placeholder(),
            cls._previous_diff_placeholder(),
            cls._diagnosis_placeholder(),
            cls._diagnosis_explanation_placeholder(),
            cls._proposal_placeholder(),
            cls._patch_diagnostics_placeholder(),
            cls._prior_patch_placeholder(),
            cls._refinement_context_placeholder(),
            cls._diagnosis_output_placeholder(),
            cls._experiment_summary_placeholder(),
            cls._critique_output_placeholder(),
        }

    def _strip_placeholder_sections(self, text: str) -> str:
        placeholder_texts = self._placeholder_texts()
        lines = text.splitlines()
        cleaned: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.rstrip().endswith(":") and i + 1 < len(lines):
                placeholder_candidate = lines[i + 1].strip()
                if placeholder_candidate in placeholder_texts:
                    i += 2
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    continue
            cleaned.append(line)
            i += 1
        # collapse excessive blank lines
        collapsed: list[str] = []
        previous_blank = True
        for line in cleaned:
            if line.strip():
                collapsed.append(line)
                previous_blank = False
            else:
                if not previous_blank:
                    collapsed.append("")
                previous_blank = True
        return "\n".join(collapsed).strip()

    # ------------------------------------------------------------------
    def _execute_iteration(
        self,
        iteration: GuidedIterationArtifact,
        request: GuidedLoopInputs,
        *,
        prior_outcome: IterationOutcome | None,
        history_context: str,
    ) -> tuple[List[StrategyEvent], IterationOutcome | None]:
        events: List[StrategyEvent] = []
        if iteration.kind == "refine":
            reset_events = self._reset_for_refinement(iteration)
            for event in reset_events:
                self.emit(event)
            events.extend(reset_events)
        outcome: IterationOutcome | None = None
        continue_execution = True
        previous_error_fingerprint = prior_outcome.error_fingerprint if prior_outcome else self._baseline_error_fingerprint
        for artifact in iteration.phases:
            if not continue_execution:
                break
            if artifact.status == PhaseStatus.PLANNED:
                self._prepare_phase_prompt(
                    artifact,
                    iteration,
                    request,
                    prior_outcome=prior_outcome,
                    history_context=history_context,
                )
            if artifact.phase == GuidedPhase.DIAGNOSE:
                if continue_execution:
                    events.extend(self._execute_diagnose(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.PLANNING:
                if continue_execution:
                    events.extend(self._execute_planning(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.PROPOSE:
                if continue_execution:
                    events.extend(self._execute_propose(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.GENERATE_PATCH:
                if continue_execution:
                    events.extend(self._execute_generate_patch(artifact, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.CRITIQUE:
                if continue_execution:
                    critique_events, outcome = self._execute_critique(artifact, iteration, iteration.index, request)
                    events.extend(critique_events)
                break
            else:
                break
        if outcome:
            outcome.previous_error_fingerprint = previous_error_fingerprint
            if outcome.error_fingerprint is None:
                outcome.error_fingerprint = previous_error_fingerprint
        return events, outcome

    def _reset_for_refinement(self, iteration: GuidedIterationArtifact) -> List[StrategyEvent]:
        event = self._event(
            kind=StrategyEventKind.NOTE,
            message="Refinement iteration skipping Diagnose; reusing most recent analysis",
            iteration=iteration.index,
        )
        return [event]

    def _execute_diagnose(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Diagnose phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Diagnose phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Diagnose phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        if artifact.response:
            self._latest_diagnosis_output = artifact.response
        if not artifact.response:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Diagnose phase returned an empty response."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Diagnose phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["diagnosis_text"] = artifact.response
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Diagnose phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_planning(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Planning phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Planning phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Planning phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events

        artifact.response = response.strip()
        if not artifact.response:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Planning phase returned an empty response."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Planning phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            iteration.failure_reason = "empty-response"
            self.emit(failure_event)
            events.append(failure_event)
            return events

        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["planning_notes"] = artifact.response
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Planning phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_propose(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Propose phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.patch_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Propose phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        artifact.response = response.strip()
        if not artifact.response:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Proposal response was empty."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["proposal"] = artifact.response
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Propose phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_generate_patch(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Generate Patch phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.patch_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Generate Patch phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Generate Patch phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Generate Patch phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_critique(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> tuple[List[StrategyEvent], IterationOutcome | None]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Critique checks",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)

        diff_text = self._find_phase_response(iteration, GuidedPhase.GENERATE_PATCH)
        if not diff_text:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Generate Patch did not produce a diff to critique."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique skipped: missing diff",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            iteration.failure_reason = "missing-diff"
            self.emit(failure_event)
            events.append(failure_event)
            return events, IterationOutcome(
                diff_text=None,
                patch_applied=False,
                patch_diagnostics="No diff available",
                critique_feedback=artifact.response or artifact.human_notes,
            )

        diff_stats = self._summarize_diff(diff_text)
        artifact.machine_checks = {
            "diffStats": diff_stats,
        }
        artifact.metrics = {
            "diff_added": float(diff_stats["added_lines"]),
            "diff_removed": float(diff_stats["removed_lines"]),
            "diff_hunks": float(diff_stats["hunks"]),
        }

        experiment_summary = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
        active_hypothesis_text = experiment_summary or self._experiment_summary_placeholder()
        error_text = request.error_text or "(error unavailable)"
        history_context = iteration.history_context or self._history_placeholder()
        pre_span, post_span = self._diff_spans(diff_text, source_text=request.source_text)
        before_snippet = self._critique_snippet(
            request.source_text,
            pre_span,
            fallback=self._focused_context_window(request),
        )
        outcome = IterationOutcome(diff_text=diff_text, critique_feedback=artifact.response)
        outcome.diff_span = pre_span

        if diff_stats["hunks"] == 0:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Diff contained no @@ hunks; cannot apply."
            iteration.failure_reason = "empty-diff"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: diff missing hunks",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"diff_excerpt": diff_text[:200]},
            )
            self.emit(failure_event)
            events.append(failure_event)
            outcome.patch_diagnostics = "Diff missing hunks"
            after_snippet = "Patched output unavailable because the diff has no hunks."
            self._finalize_critique_response(
                artifact,
                iteration_index,
                events,
                applied=False,
                history_context=history_context,
                error_text=error_text,
                active_hypothesis_text=active_hypothesis_text,
                before_snippet=before_snippet,
                after_snippet=after_snippet,
                diff_text=diff_text,
                diff_stats=diff_stats,
                outcome=outcome,
            )
            return events, outcome

        patched_text, applied = self._patch_applier.apply(request.source_text, diff_text)
        patch_message = "Patch applied successfully" if applied else "Patch applier could not locate context"
        artifact.machine_checks["patchApplication"] = {
            "applied": applied,
            "message": patch_message,
        }
        outcome.patch_applied = applied
        outcome.patch_diagnostics = patch_message
        if applied:
            outcome.patched_text = patched_text

        if not applied:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Patch application failed; queue another guided loop iteration to retry."
            iteration.failure_reason = "patch-apply"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: patch application",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"diagnostics": patch_message},
            )
            self.emit(failure_event)
            events.append(failure_event)
            after_snippet = "Patched output unavailable because the diff could not be applied."
            self._finalize_critique_response(
                artifact,
                iteration_index,
                events,
                applied=False,
                history_context=history_context,
                error_text=error_text,
                active_hypothesis_text=active_hypothesis_text,
                before_snippet=before_snippet,
                after_snippet=after_snippet,
                diff_text=diff_text,
                diff_stats=diff_stats,
                outcome=outcome,
            )
            return events, outcome

        compile_result = None
        if self._config.compile_check and request.compile_command:
            compile_result = self._run_compile(request, patched_text)
            artifact.machine_checks["compile"] = dict(compile_result)
            outcome.compile_returncode = compile_result.get("returncode")
            outcome.compile_stdout = compile_result.get("stdout")
            outcome.compile_stderr = compile_result.get("stderr")
            fingerprint_source: Optional[str]
            compile_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Compile command completed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={
                    "command": compile_result.get("command"),
                    "returncode": compile_result.get("returncode"),
                },
            )
            self.emit(compile_event)
            events.append(compile_event)
            if compile_result.get("returncode") == 0:
                fingerprint_source = None
            else:
                fingerprint_source = compile_result.get("stderr") or compile_result.get("stdout")
                error_message = (fingerprint_source or "").strip()
                outcome.error_message = error_message or None
                if error_message:
                    outcome.error_location = self._detect_error_line(error_message, request.source_path.name)
            outcome.error_fingerprint = self._error_fingerprint(fingerprint_source)
            if compile_result.get("returncode") != 0:
                artifact.status = PhaseStatus.FAILED
                artifact.completed_at = self._now()
                artifact.human_notes = "Compile/Test command failed; provide diagnostics to the next guided loop iteration."
                iteration.failure_reason = f"compile-{compile_result.get('returncode')}"
                failure_event = self._event(
                    kind=StrategyEventKind.NOTE,
                    message="Critique failed: compile",
                    phase=artifact.phase.value,
                    iteration=iteration_index,
                    data={
                        "returncode": compile_result.get("returncode"),
                        "stderr": compile_result.get("stderr", "")[:500],
                    },
                )
                self.emit(failure_event)
                events.append(failure_event)
                after_snippet = self._critique_snippet(
                    patched_text,
                    post_span,
                    fallback="Patched output unavailable.",
                )
                self._finalize_critique_response(
                    artifact,
                    iteration_index,
                    events,
                    applied=True,
                    history_context=history_context,
                    error_text=error_text,
                    active_hypothesis_text=active_hypothesis_text,
                    before_snippet=before_snippet,
                    after_snippet=after_snippet,
                    diff_text=diff_text,
                    diff_stats=diff_stats,
                    outcome=outcome,
                )
                return events, outcome

        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        after_snippet = self._critique_snippet(
            patched_text,
            post_span,
            fallback="Patched output unavailable.",
        )
        self._finalize_critique_response(
            artifact,
            iteration_index,
            events,
            applied=True,
            history_context=history_context,
            error_text=error_text,
            active_hypothesis_text=active_hypothesis_text,
            before_snippet=before_snippet,
            after_snippet=after_snippet,
            diff_text=diff_text,
            diff_stats=diff_stats,
            outcome=outcome,
        )
        iteration.failure_reason = None
        iteration.accepted = outcome.patch_applied and (
            not self._config.compile_check or not request.compile_command or outcome.compile_success
        )
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Critique checks completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={
                "patch_applied": outcome.patch_applied,
                "compile_success": outcome.compile_success,
            },
        )
        self.emit(completion_event)
        events.append(completion_event)
        if not outcome.critique_feedback:
            outcome.critique_feedback = artifact.response or artifact.human_notes
        return events, outcome

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _prepare_phase_prompt(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        request: GuidedLoopInputs,
        *,
        prior_outcome: IterationOutcome | None,
        history_context: str,
    ) -> None:
        critique_feedback = prior_outcome.critique_feedback if prior_outcome else self._critique_placeholder()
        previous_diff = (
            prior_outcome.diff_text if (prior_outcome and prior_outcome.diff_text) else self._previous_diff_placeholder()
        )
        context_override = self._focused_context_window(request)
        prior_patch_summary = self._format_prior_patch_summary(prior_outcome)
        is_refine_iteration = iteration.kind == "refine"
        refinement_context_text = self._refinement_context_placeholder()
        if is_refine_iteration:
            refinement_context_text = self._build_refinement_context(prior_outcome)

        phase_history_context = history_context
        phase_previous_diff = previous_diff
        phase_critique_feedback = critique_feedback
        phase_prior_patch_summary = prior_patch_summary

        if artifact.phase == GuidedPhase.DIAGNOSE:
            artifact.prompt = self._render_prompt(
                GuidedPhase.DIAGNOSE,
                request,
                context_override=context_override,
                extra={
                    "critique_feedback": phase_critique_feedback,
                    "previous_diff": phase_previous_diff,
                    "history_context": phase_history_context,
                    "prior_patch_summary": phase_prior_patch_summary,
                },
            )
        elif artifact.phase == GuidedPhase.PLANNING:
            diagnosis_output = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
            if not diagnosis_output:
                diagnosis_output = self._latest_diagnosis_output
            critique_transcript = self._critique_history_text()
            artifact.prompt = self._render_prompt(
                GuidedPhase.PLANNING,
                request,
                context_override=context_override,
                extra={
                    "diagnosis_output": diagnosis_output or self._diagnosis_output_placeholder(),
                    "critique_output": critique_transcript or self._critique_output_placeholder(),
                },
            )
        elif artifact.phase == GuidedPhase.PROPOSE:
            experiment_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            artifact.prompt = self._render_prompt(
                GuidedPhase.PROPOSE,
                request,
                context_override=context_override,
                extra={
                    "experiment_summary": experiment_result or self._experiment_summary_placeholder(),
                    "critique_feedback": phase_critique_feedback,
                    "history_context": phase_history_context,
                    "previous_diff": phase_previous_diff,
                    "prior_patch_summary": phase_prior_patch_summary,
                    "refinement_context": refinement_context_text,
                },
            )
        elif artifact.phase == GuidedPhase.GENERATE_PATCH:
            planning_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            active_hypothesis_text = planning_result or self._experiment_summary_placeholder()
            proposal_summary = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PROPOSE))
            artifact.prompt = self._render_prompt(
                GuidedPhase.GENERATE_PATCH,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": active_hypothesis_text,
                    "diagnosis_explanation": active_hypothesis_text,
                    "proposal": proposal_summary or self._proposal_placeholder(),
                    "critique_feedback": phase_critique_feedback,
                    "history_context": phase_history_context,
                    "previous_diff": phase_previous_diff,
                    "prior_patch_summary": phase_prior_patch_summary,
                    "refinement_context": refinement_context_text,
                },
            )

    def _format_prior_patch_summary(self, prior_outcome: IterationOutcome | None, *, max_chars: int = 4000) -> str:
        placeholder = self._prior_patch_placeholder()
        if not prior_outcome:
            return placeholder
        if prior_outcome.diff_text:
            diff_text = prior_outcome.diff_text.strip()
            if not diff_text:
                return placeholder
            if len(diff_text) > max_chars:
                truncated = diff_text[:max_chars].rstrip()
                return f"{truncated}\n…"
            return diff_text
        diagnostics = (prior_outcome.patch_diagnostics or "").strip()
        if diagnostics:
            return diagnostics
        return placeholder

    def _build_refinement_context(self, prior_outcome: IterationOutcome | None) -> str:
        return "Refinement iterations reuse the most recent Diagnose output; do not rerun Diagnose."

    def _critique_history_text(self, limit: Optional[int] = None) -> Optional[str]:
        if not self._critique_transcripts:
            return None
        transcripts = self._critique_transcripts[-limit:] if limit else self._critique_transcripts
        separator = "\n\n---\n\n"
        return separator.join(transcripts)

    def _find_phase_response(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[str]:
        for artifact in iteration.phases:
            if artifact.phase == phase and artifact.response:
                return artifact.response
        return None

    @staticmethod
    def _coerce_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            text = value
        elif isinstance(value, (int, float)):
            text = str(value)
        else:
            text = str(value)
        stripped = text.strip()
        return stripped or None

    @staticmethod
    def _record_iteration_telemetry(
        iteration: GuidedIterationArtifact | None,
        key: str,
        payload: Any,
        *,
        append: bool = False,
    ) -> None:
        if not iteration:
            return
        if iteration.telemetry is None:
            iteration.telemetry = {}
        if append:
            bucket = iteration.telemetry.setdefault(key, [])
            bucket.append(payload)
        else:
            iteration.telemetry[key] = payload

    def _record_critique_transcript(self, transcript: Optional[str]) -> None:
        if transcript:
            self._critique_transcripts.append(transcript)
    def _post_iteration_evaluation(
        self,
        iteration: GuidedIterationArtifact,
        outcome: IterationOutcome,
        previous_outcome: IterationOutcome | None,
    ) -> List[StrategyEvent]:
        events: List[StrategyEvent] = []
        if not outcome:
            return events

        stall_summary = self._detect_stall(previous_outcome, outcome)
        if stall_summary:
            iteration.failure_reason = "stall"
            self._record_iteration_telemetry(iteration, "stall", stall_summary, append=True)
            stall_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Stall detected: diff and error signature repeated",
                iteration=iteration.index,
                data=stall_summary,
            )
            self.emit(stall_event)
            events.append(stall_event)
            return events

        prev_fp = outcome.previous_error_fingerprint
        curr_fp = outcome.error_fingerprint
        if prev_fp is not None and curr_fp is not None and prev_fp == curr_fp:
            iteration.failure_reason = iteration.failure_reason or "unchanged-error"
            payload = {"previous": prev_fp, "current": curr_fp}
            self._record_iteration_telemetry(iteration, "unchangedError", payload, append=True)
            unchanged_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Error signature unchanged after patch",
                iteration=iteration.index,
                data=payload,
            )
            self.emit(unchanged_event)
            events.append(unchanged_event)
            return events

        return events

    def _detect_stall(
        self,
        previous_outcome: IterationOutcome | None,
        current_outcome: IterationOutcome | None,
    ) -> Optional[Dict[str, Any]]:
        prev_signature = self._stall_signature(previous_outcome)
        curr_signature = self._stall_signature(current_outcome)
        if not prev_signature or not curr_signature:
            return None
        if prev_signature != curr_signature:
            return None
        message, location, diff_span = curr_signature
        return {
            "errorMessage": message,
            "errorLocation": location,
            "diffSpan": list(diff_span),
        }

    def _stall_signature(self, outcome: IterationOutcome | None) -> Optional[Tuple[str, Optional[int], Tuple[int, int]]]:
        if not outcome or not outcome.patch_applied:
            return None
        if outcome.compile_returncode in (None, 0):
            return None
        if not outcome.diff_span:
            return None
        message = outcome.error_message or outcome.compile_stderr or outcome.compile_stdout or outcome.error_fingerprint
        if not message:
            return None
        normalized_message = re.sub(r"\s+", " ", message.strip())
        if not normalized_message:
            return None
        return normalized_message, outcome.error_location, outcome.diff_span

    @staticmethod
    def _ensure_machine_checks_dict(artifact: PhaseArtifact) -> Dict[str, Any]:
        if isinstance(artifact.machine_checks, dict):
            return artifact.machine_checks
        materialized = dict(artifact.machine_checks or {})
        artifact.machine_checks = materialized
        return materialized


    @staticmethod
    def _error_fingerprint(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return None
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _diagnosis_placeholder() -> str:
        return "Diagnosis not available yet; run the Diagnose phase first."

    @staticmethod
    def _diagnosis_explanation_placeholder() -> str:
        return "Diagnosis rationale not available yet; run the Diagnose phase first."

    @staticmethod
    def _diagnosis_output_placeholder() -> str:
        return "Diagnose phase output unavailable yet."

    @staticmethod
    def _proposal_placeholder() -> str:
        return "Proposal not available yet; run the Propose phase first."

    @staticmethod
    def _experiment_summary_placeholder() -> str:
        return "Experiment phase output unavailable yet."

    @staticmethod
    def _critique_output_placeholder() -> str:
        return "No critique transcripts are available yet."

    @staticmethod
    def _patch_diagnostics_placeholder() -> str:
        return "No patch diagnostics available yet."

    @staticmethod
    def _critique_placeholder() -> str:
        return "No prior critique feedback yet; this is the initial attempt."

    @staticmethod
    def _previous_diff_placeholder() -> str:
        return "No previous replacement attempt has been recorded."

    @staticmethod
    def _prior_patch_placeholder() -> str:
        return "No prior suggested patch is available yet."

    @staticmethod
    def _history_placeholder() -> str:
        return "No prior iterations have run yet."

    @staticmethod
    def _refinement_context_placeholder() -> str:
        return "No refinement guidance for this iteration."

    def _context_for_phase(self, phase: GuidedPhase, request: GuidedLoopInputs) -> str:
        if phase in (GuidedPhase.DIAGNOSE, GuidedPhase.PROPOSE, GuidedPhase.GENERATE_PATCH):
            return self._focused_context_window(request)
        return self._default_context_slice(request)

    def _default_context_slice(self, request: GuidedLoopInputs, limit: int = 2000) -> str:
        source = request.source_text.strip()
        if not source:
            return "Source unavailable."
        if len(source) <= limit:
            return source
        return source[:limit].rstrip() + "\n…"

    def _focused_context_window(self, request: GuidedLoopInputs, radius: int = 5) -> str:
        source = request.source_text
        if not source:
            return "Source unavailable."
        lines = source.splitlines()
        if not lines:
            return "Source unavailable."
        error_line = self._detect_error_line(request.error_text or "", request.source_path.name)
        if error_line is None:
            start = 1
            end = min(len(lines), start + (radius * 2))
        else:
            center = max(1, min(error_line, len(lines)))
            start = max(1, center - radius)
            end = min(len(lines), center + radius)
        snippet = lines[start - 1 : end]
        return self._format_numbered_block(snippet, start)

    @staticmethod
    def _format_numbered_block(lines: Sequence[str], starting_line: int) -> str:
        formatted: List[str] = []
        line_no = starting_line
        for line in lines:
            formatted.append(f"{line_no:>4} | {line}")
            line_no += 1
        return "\n".join(formatted) if formatted else "Source unavailable."

    def _diff_spans(
        self,
        diff_text: str,
        *,
        source_text: str | None = None,
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        pattern = re.compile(r"@@ -(?P<start_a>\d+)(?:,(?P<len_a>\d+))? \+(?P<start_b>\d+)(?:,(?P<len_b>\d+))? @@")
        spans_a: List[tuple[int, int]] = []
        spans_b: List[tuple[int, int]] = []
        for line in diff_text.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            start_a = int(match.group("start_a"))
            len_a = int(match.group("len_a") or 1)
            start_b = int(match.group("start_b"))
            len_b = int(match.group("len_b") or 1)
            spans_a.append((start_a, start_a + max(len_a, 1) - 1))
            spans_b.append((start_b, start_b + max(len_b, 1) - 1))

        if spans_a or spans_b:
            return self._aggregate_spans(spans_a), self._aggregate_spans(spans_b)

        if source_text and "ORIGINAL LINES:" in diff_text and "NEW LINES:" in diff_text:
            return self._replacement_diff_spans(diff_text, source_text)

        return None, None

    @staticmethod
    def _aggregate_spans(spans: List[tuple[int, int]]) -> tuple[int, int] | None:
        if not spans:
            return None
        start = min(span[0] for span in spans)
        end = max(span[1] for span in spans)
        return start, end

    def _replacement_diff_spans(
        self,
        diff_text: str,
        source_text: str,
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        before_spans: List[tuple[int, int]] = []
        after_spans: List[tuple[int, int]] = []
        source_lines = source_text.splitlines()
        blocks = self._parse_replacement_blocks(diff_text)
        for original_lines, updated_lines in blocks:
            if not original_lines:
                continue
            index = self._patch_applier.find_context(source_lines, original_lines)
            if index is None:
                continue
            start_line = index + 1
            before_span = (start_line, start_line + max(len(original_lines), 1) - 1)
            after_span = (start_line, start_line + max(len(updated_lines), 1) - 1)
            before_spans.append(before_span)
            after_spans.append(after_span)
        return self._aggregate_spans(before_spans), self._aggregate_spans(after_spans)

    @staticmethod
    def _parse_replacement_blocks(diff_text: str) -> List[tuple[List[str], List[str]]]:
        blocks: List[tuple[List[str], List[str]]] = []
        text = diff_text.strip()
        for match in REPLACEMENT_BLOCK_PATTERN.finditer(text):
            original_lines = GuidedConvergenceStrategy._split_block_lines(match.group("original"))
            updated_lines = GuidedConvergenceStrategy._split_block_lines(match.group("updated"))
            blocks.append((original_lines, updated_lines))
        return blocks

    @staticmethod
    def _split_block_lines(block: str | None) -> List[str]:
        return normalize_replacement_block(block)

    def _critique_snippet(
        self,
        text: Optional[str],
        span: tuple[int, int] | None,
        *,
        radius: int = 5,
        fallback: str,
    ) -> str:
        if not text:
            return fallback
        lines = text.splitlines()
        if not lines:
            return fallback
        if not span:
            return fallback
        start = max(1, span[0] - radius)
        end = min(len(lines), span[1] + radius)
        excerpt = lines[start - 1 : end]
        return self._format_numbered_block(excerpt, start)

    def _build_critique_prompt(
        self,
        *,
        applied: bool,
        history_context: str,
        error_text: str,
        active_hypothesis_text: str,
        before_snippet: str,
        after_snippet: str,
        diff_text: str,
        validation_summary: str,
    ) -> str:
        header = (
            "Summarize the critique of the applied patch in three focused sections."
            if applied
            else "Summarize concerns about the proposed patch before it is applied."
        )
        checklist = (
            "Address each item in order:\n"
            "1) Outcome summary — Did the patch resolve the issue? Mention compile/test status.\n"
            "2) Could the patch be applied? — If not, explain why.\n"
            "3) If the patch could not be applied or it did not fix the original error, state the hypothesis name and declare it to be 'REJECTED' ."
        )
        sections = [
            header,
            checklist,
            f"Validation summary:\n{validation_summary}",
            f"Recent iteration history:\n{history_context}",
            f"Original error:\n{error_text}",
            f"Active hypothesis summary:\n{active_hypothesis_text}",
            "Original Code before suggested replacement was applied:\n" + (before_snippet or "Source unavailable."),
            "Replacement block(s) that were applied:\n" + diff_text.strip(),
            "Updated Code after suggested replacement was applied:\n" + (after_snippet or "Source unavailable."),
        ]
        return "\n\n".join(sections).strip()

    def _finalize_critique_response(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        events: List[StrategyEvent],
        *,
        applied: bool,
        history_context: str,
        error_text: str,
        active_hypothesis_text: str,
        before_snippet: str,
        after_snippet: str,
        diff_text: str,
        diff_stats: Mapping[str, Any],
        outcome: IterationOutcome,
    ) -> None:
        summary = self._format_critique_summary(diff_stats, outcome)
        artifact.prompt = self._build_critique_prompt(
            applied=applied,
            history_context=history_context,
            error_text=error_text,
            active_hypothesis_text=active_hypothesis_text,
            before_snippet=before_snippet,
            after_snippet=after_snippet,
            diff_text=diff_text,
            validation_summary=summary,
        )
        critique_text = self._invoke_critique_model(artifact, iteration_index, events)
        if critique_text:
            normalized = critique_text.strip()
            artifact.response = f"{normalized}\n\nValidation summary: {summary}"
        else:
            artifact.response = summary
        outcome.critique_feedback = artifact.response
        self._record_critique_transcript(artifact.response)

    def _invoke_critique_model(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        events: List[StrategyEvent],
    ) -> Optional[str]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        model_name = (
            self._config.critique_model
            or self._config.patch_model
            or self._config.interpreter_model
        )
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=model_name,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            if not artifact.human_notes:
                artifact.human_notes = f"Critique phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return None
        return response.strip()

    @staticmethod
    def _detect_error_line(error_text: str, filename: str) -> Optional[int]:
        if not error_text:
            return None
        pattern = re.compile(rf"{re.escape(filename)}:(\d+)")
        match = pattern.search(error_text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        generic = re.search(r":(\d+):", error_text)
        if generic:
            try:
                return int(generic.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        fallback = re.search(r"line\s+(\d+)", error_text)
        if fallback:
            try:
                return int(fallback.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        return None

    # ------------------------------------------------------------------
    @staticmethod
    def _summarize_diff(diff_text: str) -> Dict[str, Any]:
        if "ORIGINAL LINES:" in diff_text and "NEW LINES:" in diff_text:
            return GuidedConvergenceStrategy._summarize_replacement_blocks(diff_text)
        added = 0
        removed = 0
        hunks = 0
        for line in diff_text.splitlines():
            if line.startswith("@@"):
                hunks += 1
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1
        return {
            "added_lines": added,
            "removed_lines": removed,
            "hunks": hunks,
            "delete_only": added == 0 and removed > 0,
        }

    @staticmethod
    def _summarize_replacement_blocks(diff_text: str) -> Dict[str, Any]:
        blocks = GuidedConvergenceStrategy._parse_replacement_blocks(diff_text)
        hunks = len(blocks)
        added = sum(len(updated) for _, updated in blocks)
        removed = sum(len(original) for original, _ in blocks)
        return {
            "added_lines": added,
            "removed_lines": removed,
            "hunks": hunks,
            "delete_only": added == 0 and removed > 0,
        }

    def _run_compile(self, request: GuidedLoopInputs, patched_text: str) -> Dict[str, Any]:
        command = list(request.compile_command or [])
        if not command:
            return {"command": [], "returncode": None, "stdout": "", "stderr": ""}
        try:
            with tempfile.TemporaryDirectory(prefix="llm_patch_guided_") as tmpdir:
                tmp_path = Path(tmpdir)
                for rel_path in self._compile_target_paths(request, command):
                    destination = tmp_path / rel_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(patched_text, encoding="utf-8")
                proc = subprocess.run(
                    command,
                    cwd=str(tmp_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return {
                    "command": command,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
        except OSError as exc:  # pragma: no cover - defensive
            return {
                "command": command,
                "returncode": None,
                "stdout": "",
                "stderr": str(exc),
            }

    def _compile_target_paths(self, request: GuidedLoopInputs, command: Sequence[str]) -> List[Path]:
        """Return the relative file paths that should contain the patched source."""

        source_suffix = Path(request.source_path.name).suffix.lower()
        targets: List[Path] = []
        for token in command:
            if not token or token.startswith("-"):
                continue
            candidate = Path(token)
            suffix = candidate.suffix.lower()
            if not suffix or (source_suffix and suffix != source_suffix):
                continue
            if candidate.is_absolute():
                relative_candidate = Path(candidate.name)
            else:
                relative_candidate = candidate
            if relative_candidate not in targets:
                targets.append(relative_candidate)
        if not targets:
            targets.append(Path(request.source_path.name))
        return targets

    @staticmethod
    def _format_critique_summary(diff_stats: Mapping[str, Any], outcome: IterationOutcome) -> str:
        if not outcome.patch_applied:
            return outcome.patch_diagnostics or "The patch could not be applied to the source file."
        if outcome.compile_returncode is None:
            return "The diff was applied, and compile/test was skipped."
        if outcome.compile_success:
            return "The diff was applied and compile/test succeeded."
        return (
            "The diff was applied, but compile/test exited with return code "
            f"{outcome.compile_returncode}, so importantly the original issue still persists and we know the diff is erroneous."
        )

    @staticmethod
    def _result_notes(outcome: IterationOutcome | None) -> str:
        if outcome is None:
            return "Guided loop planned prompts but critique was not executed."
        if not outcome.patch_applied:
            return outcome.patch_diagnostics or "Patch application failed."
        if outcome.compile_returncode is None:
            return "Patch applied; compile/test skipped."
        if outcome.compile_success:
            return "Patch applied and compile/test succeeded."
        return f"Patch applied but compile/test exited with {outcome.compile_returncode}."
