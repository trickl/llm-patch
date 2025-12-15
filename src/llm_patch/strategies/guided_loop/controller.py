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
from .hypothesis import Hypothesis, HypothesisManager, HypothesisStatus
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
    DIAGNOSE_INSTRUCTIONS_FRAGMENT,
    DIAGNOSIS_RATIONALE_FRAGMENT,
    DIAGNOSIS_SUMMARY_FRAGMENT,
    ERROR_FRAGMENT,
    EXAMPLE_REPLACEMENT_FRAGMENT,
    GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
    HISTORY_FRAGMENT,
    HYPOTHESIS_CONTEXT_FRAGMENT,
    PATCH_DIAGNOSTICS_FRAGMENT,
    PRIOR_HYPOTHESIS_FRAGMENT,
    PRIOR_PATCH_FRAGMENT,
    PREVIOUS_DIFF_FRAGMENT,
    PROPOSE_INSTRUCTIONS_FRAGMENT,
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
            PRIOR_HYPOTHESIS_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            ERROR_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.PROPOSE: compose_prompt(
            PROPOSE_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            PRIOR_HYPOTHESIS_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PREVIOUS_DIFF_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            HYPOTHESIS_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT
        ),
        GuidedPhase.GENERATE_PATCH: compose_prompt(
            GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            PRIOR_HYPOTHESIS_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PREVIOUS_DIFF_FRAGMENT,
            PROPOSAL_SUMMARY_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            HYPOTHESIS_CONTEXT_FRAGMENT,
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
        self._hypothesis_manager: HypothesisManager | None = None
        self._active_hypothesis_id: str | None = None
        self._baseline_error_fingerprint: Optional[str] = None

    def run(self, request: PatchRequest) -> GuidedLoopResult:
        inputs = self._ensure_inputs(request)
        self._hypothesis_manager = HypothesisManager()
        self._active_hypothesis_id = None
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
            if self._hypothesis_manager:
                iteration.hypotheses = self._hypothesis_manager.snapshot()
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
            if self._hypothesis_manager:
                iteration.hypotheses = self._hypothesis_manager.snapshot()
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
        phases = [
            GuidedPhase.DIAGNOSE,
            GuidedPhase.PROPOSE,
            GuidedPhase.GENERATE_PATCH,
            GuidedPhase.CRITIQUE,
        ]
        return phases

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
            "hypothesis_claim": self._hypothesis_claim_placeholder(),
            "hypothesis_region": self._hypothesis_region_placeholder(),
            "hypothesis_effect": self._hypothesis_effect_placeholder(),
            "hypothesis_structure": self._hypothesis_structure_placeholder(),
            "constraints": PATCH_CONSTRAINTS_TEXT,
            "example_diff": PATCH_EXAMPLE_DIFF,
            "critique_feedback": self._critique_placeholder(),
            "previous_diff": self._previous_diff_placeholder(),
            "patch_diagnostics": "",
            "history_context": self._history_placeholder(),
            "prior_hypothesis": self._prior_hypothesis_placeholder(),
            "prior_patch_summary": self._prior_patch_placeholder(),
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
            cls._hypothesis_claim_placeholder(),
            cls._hypothesis_region_placeholder(),
            cls._hypothesis_effect_placeholder(),
            cls._hypothesis_structure_placeholder(),
            cls._patch_diagnostics_placeholder(),
            cls._prior_hypothesis_placeholder(),
            cls._prior_patch_placeholder(),
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
            outcome.hypothesis_id = iteration.selected_hypothesis_id
        return events, outcome

    def _reset_for_refinement(self, iteration: GuidedIterationArtifact) -> List[StrategyEvent]:
        events: List[StrategyEvent] = []
        if not self._hypothesis_manager:
            self._active_hypothesis_id = None
            return events
        expired_ids = self._hypothesis_manager.expire_active("Refinement iteration resetting hypotheses")
        self._active_hypothesis_id = None
        if expired_ids:
            event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Refinement iteration cleared prior hypotheses",
                iteration=iteration.index,
                data={"expired": expired_ids},
            )
            events.append(event)
        return events

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
        analysis = self._analyze_diagnose_response(artifact.response)
        if analysis:
            machine_checks = self._ensure_machine_checks_dict(artifact)
            machine_checks["analysis"] = analysis
        hypothesis_events = self._ingest_hypotheses(iteration, analysis)
        for event in hypothesis_events:
            self.emit(event)
            events.append(event)
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
        summary = self._summarize_proposal_response(artifact.response)
        if summary:
            machine_checks = self._ensure_machine_checks_dict(artifact)
            machine_checks["proposal"] = summary
        intent = self._coerce_string(summary.get("intent") if summary else None)
        structural_change = self._coerce_string(summary.get("structural_change") if summary else None)
        if not structural_change:
            structural_change = artifact.response
        if not intent:
            intent = structural_change
        if not structural_change.strip():
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Proposal response did not describe any change."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events

        hypothesis = self._ensure_active_hypothesis(iteration)
        if hypothesis is None:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "No active hypothesis available for proposal."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed: missing hypothesis",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events

        hypothesis.structural_change = structural_change

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

        analysis_payload = self._phase_machine_payload(iteration, GuidedPhase.DIAGNOSE, "analysis")
        diagnosis_struct = self._coerce_string(analysis_payload.get("diagnosis"))
        diagnosis_fallback = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
        diagnosis_text = diagnosis_struct or diagnosis_fallback or self._diagnosis_placeholder()
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
                diagnosis_text=diagnosis_text,
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
                diagnosis_text=diagnosis_text,
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
                    diagnosis_text=diagnosis_text,
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
            diagnosis_text=diagnosis_text,
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
        prev_diagnostics = prior_outcome.patch_diagnostics if prior_outcome else ""
        context_override = self._focused_context_window(request)
        prior_hypothesis_text = self._format_prior_hypothesis(prior_outcome)
        prior_patch_summary = self._format_prior_patch_summary(prior_outcome)
        is_refine_iteration = iteration.kind == "refine"
        if is_refine_iteration:
            prior_hypothesis_text = self._prior_hypothesis_placeholder()
            prior_patch_summary = self._prior_patch_placeholder()
        limited_phase = is_refine_iteration and artifact.phase in {
            GuidedPhase.PROPOSE,
            GuidedPhase.GENERATE_PATCH,
        }
        phase_history_context = history_context if not limited_phase else self._history_placeholder()
        phase_previous_diff = previous_diff if not limited_phase else self._previous_diff_placeholder()
        phase_critique_feedback = (
            critique_feedback if not limited_phase else self._critique_placeholder()
        )
        phase_prior_hypothesis = (
            prior_hypothesis_text if not limited_phase else self._prior_hypothesis_placeholder()
        )
        phase_prior_patch_summary = (
            prior_patch_summary if not limited_phase else self._prior_patch_placeholder()
        )

        if artifact.phase == GuidedPhase.DIAGNOSE:
            artifact.prompt = self._render_prompt(
                GuidedPhase.DIAGNOSE,
                request,
                context_override=context_override,
                extra={
                    "critique_feedback": phase_critique_feedback,
                    "previous_diff": phase_previous_diff,
                    "history_context": phase_history_context,
                    "prior_hypothesis": phase_prior_hypothesis,
                    "prior_patch_summary": phase_prior_patch_summary,
                },
            )
        elif artifact.phase == GuidedPhase.PROPOSE:
            analysis_payload = self._phase_machine_payload(iteration, GuidedPhase.DIAGNOSE, "analysis")
            diagnosis_struct = self._coerce_string(analysis_payload.get("diagnosis"))
            diagnosis_explanation = self._coerce_string(analysis_payload.get("rationale"))
            diagnosis_fallback = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
            self._ensure_active_hypothesis(iteration)
            hypothesis_fields = self._hypothesis_prompt_fields()
            artifact.prompt = self._render_prompt(
                GuidedPhase.PROPOSE,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": diagnosis_struct or diagnosis_fallback or self._diagnosis_placeholder(),
                    "diagnosis_explanation": diagnosis_explanation or self._diagnosis_explanation_placeholder(),
                    "critique_feedback": phase_critique_feedback,
                    "history_context": phase_history_context,
                    "previous_diff": phase_previous_diff,
                    "prior_hypothesis": phase_prior_hypothesis,
                    "prior_patch_summary": phase_prior_patch_summary,
                    **hypothesis_fields,
                },
            )
        elif artifact.phase == GuidedPhase.GENERATE_PATCH:
            analysis_payload = self._phase_machine_payload(iteration, GuidedPhase.DIAGNOSE, "analysis")
            diagnosis_struct = self._coerce_string(analysis_payload.get("diagnosis"))
            diagnosis_explanation = self._coerce_string(analysis_payload.get("rationale"))
            diagnosis_fallback = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
            proposal_payload = self._phase_machine_payload(iteration, GuidedPhase.PROPOSE, "proposal")
            proposal_struct = self._coerce_string(proposal_payload.get("structural_change"))
            proposal_summary = proposal_struct or self._find_phase_response(iteration, GuidedPhase.PROPOSE)
            self._ensure_active_hypothesis(iteration)
            hypothesis_fields = self._hypothesis_prompt_fields()
            artifact.prompt = self._render_prompt(
                GuidedPhase.GENERATE_PATCH,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": diagnosis_struct or diagnosis_fallback or self._diagnosis_placeholder(),
                    "diagnosis_explanation": diagnosis_explanation or self._diagnosis_explanation_placeholder(),
                    "proposal": proposal_summary or self._proposal_placeholder(),
                    "critique_feedback": phase_critique_feedback,
                    "history_context": phase_history_context,
                    "previous_diff": phase_previous_diff,
                    "prior_hypothesis": phase_prior_hypothesis,
                    "prior_patch_summary": phase_prior_patch_summary,
                    **hypothesis_fields,
                },
            )

    def _format_prior_hypothesis(self, prior_outcome: IterationOutcome | None) -> str:
        placeholder = self._prior_hypothesis_placeholder()
        if not prior_outcome or not prior_outcome.hypothesis_id or not self._hypothesis_manager:
            return placeholder
        hypothesis = self._hypothesis_manager.get(prior_outcome.hypothesis_id)
        if not hypothesis:
            return placeholder
        lines: list[str] = []
        lines.append(f"ID: {hypothesis.id}")
        if hypothesis.claim:
            lines.append(f"Claim: {hypothesis.claim}")
        if hypothesis.affected_region:
            lines.append(f"Affected region: {hypothesis.affected_region}")
        if hypothesis.expected_effect:
            lines.append(f"Expected effect: {hypothesis.expected_effect}")
        if hypothesis.selection_rationale:
            lines.append(f"Selection rationale: {hypothesis.selection_rationale}")
        if hypothesis.structural_change:
            lines.append(f"Suggested structural change: {hypothesis.structural_change}")
        return "\n".join(lines) if lines else placeholder

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

    def _find_phase_response(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[str]:
        for artifact in iteration.phases:
            if artifact.phase == phase and artifact.response:
                return artifact.response
        return None

    def _ingest_hypotheses(
        self,
        iteration: GuidedIterationArtifact,
        analysis: Mapping[str, Any] | None,
    ) -> List[StrategyEvent]:
        events: List[StrategyEvent] = []
        if not analysis or self._hypothesis_manager is None:
            return events
        raw_entries = analysis.get("hypotheses") if isinstance(analysis, Mapping) else None
        parsed_entries: List[Dict[str, Any]] = []
        if isinstance(raw_entries, list):
            for entry in raw_entries:
                normalized = self._normalize_hypothesis_entry(entry)
                if normalized:
                    parsed_entries.append(normalized)
        diagnosis_summary = self._coerce_string(analysis.get("diagnosis"))
        rationale = self._coerce_string(analysis.get("rationale"))
        created_ids: List[str] = []
        label_lookup: Dict[str, str] = {}
        claim_lookup: Dict[str, str] = {}
        fallback_created = False
        selection_label = self._coerce_string(analysis.get("selected_hypothesis"))
        selection_rationale = self._coerce_string(analysis.get("selection_rationale"))
        selection_binding = self._coerce_string(analysis.get("binding_region"))
        if parsed_entries:
            require_multiple = self._hypothesis_manager.active_count() == 0
            if require_multiple and len(parsed_entries) < 2:
                events.append(
                    self._event(
                        kind=StrategyEventKind.NOTE,
                        message="Diagnose produced fewer than two hypotheses; requesting broader exploration.",
                        iteration=iteration.index,
                        data={"count": len(parsed_entries)},
                    )
                )
            for entry in parsed_entries:
                hypothesis = self._hypothesis_manager.create(
                    claim=entry["claim"],
                    affected_region=entry["affected_region"],
                    expected_effect=entry["expected_effect"],
                    diagnosis=diagnosis_summary,
                    rationale=entry.get("explanation")
                    or entry.get("rationale")
                    or rationale,
                    structural_change=entry.get("structural_change"),
                    confidence=entry.get("confidence"),
                    kind=entry.get("kind"),
                    binding_region=entry.get("binding_region"),
                )
                created_ids.append(hypothesis.id)
                if hypothesis.claim:
                    claim_lookup[self._selection_key(hypothesis.claim)] = hypothesis.id
                identifier = entry.get("identifier")
                if identifier:
                    label_lookup[self._selection_key(identifier)] = hypothesis.id
        elif self._hypothesis_manager.active_count() == 0:
            fallback = self._synthesize_hypothesis_from_analysis(diagnosis_summary, rationale)
            if fallback:
                created_ids.append(fallback.id)
                if fallback.claim:
                    claim_lookup[self._selection_key(fallback.claim)] = fallback.id
                fallback_created = True
        if created_ids:
            events.append(
                self._event(
                    kind=StrategyEventKind.NOTE,
                    message="Recorded structural hypotheses",
                    iteration=iteration.index,
                    data={"hypotheses": created_ids, "synthetic": fallback_created},
                )
            )
            telemetry_payload = {"ids": created_ids, "count": len(created_ids)}
            if fallback_created:
                telemetry_payload["synthetic"] = True
            self._record_iteration_telemetry(
                iteration,
                "hypothesesCreated",
                telemetry_payload,
                append=True,
            )
        else:
            return events
        iteration.hypotheses = self._hypothesis_manager.snapshot()
        if selection_label and not fallback_created:
            selection_event = self._activate_selected_hypothesis(
                iteration,
                selection_label,
                selection_rationale,
                selection_binding,
                label_lookup=label_lookup,
                claim_lookup=claim_lookup,
                created_ids=created_ids,
            )
            if selection_event:
                events.append(selection_event)
        if not iteration.selected_hypothesis_id:
            self._select_active_hypothesis(iteration, preferred_ids=created_ids)
        return events

    def _normalize_hypothesis_entry(self, entry: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(entry, Mapping):
            return None
        claim = self._coerce_string(entry.get("claim") or entry.get("hypothesis"))
        if not claim:
            return None
        identifier = self._coerce_string(
            entry.get("id")
            or entry.get("hypothesis_id")
            or entry.get("hypothesisId")
            or entry.get("label")
            or entry.get("key")
        )
        kind = self._canonical_hypothesis_kind(entry.get("kind"))
        affected_region = self._coerce_string(
            entry.get("affected_region") or entry.get("region") or entry.get("scope")
        ) or "Unspecified region"
        expected_effect = self._coerce_string(
            entry.get("expected_effect") or entry.get("effect") or entry.get("observable")
        ) or claim
        structural_change = self._coerce_string(entry.get("structural_change") or entry.get("structuralDelta"))
        explanation = self._coerce_string(entry.get("explanation") or entry.get("evidence") or entry.get("rationale"))
        confidence = self._coerce_confidence(entry.get("confidence") or entry.get("plausibility"))
        binding_region = self._coerce_string(entry.get("binding_region") or entry.get("bindingRegion"))
        return {
            "claim": claim,
            "affected_region": affected_region,
            "expected_effect": expected_effect,
            "structural_change": structural_change,
            "explanation": explanation,
            "confidence": confidence,
            "identifier": identifier,
            "kind": kind,
            "binding_region": binding_region,
        }

    def _synthesize_hypothesis_from_analysis(
        self,
        diagnosis_summary: Optional[str],
        rationale: Optional[str],
    ) -> Optional[Hypothesis]:
        if self._hypothesis_manager is None:
            return None
        basis = self._coerce_string(diagnosis_summary) or self._coerce_string(rationale)
        if not basis:
            return None
        headline = basis.strip().splitlines()[0].strip()
        if not headline:
            return None
        if len(headline) > 160:
            headline = f"{headline[:160].rstrip()}…"
        hypothesis = self._hypothesis_manager.create(
            claim=headline,
            affected_region="Unspecified region",
            expected_effect=headline,
            diagnosis=diagnosis_summary or headline,
            rationale=rationale or "Synthesized from diagnosis details.",
        )
        hypothesis.add_falsification_note("Synthesized from diagnosis due to missing structured hypotheses.")
        return hypothesis

    def _activate_selected_hypothesis(
        self,
        iteration: GuidedIterationArtifact,
        selection_label: str,
        selection_rationale: Optional[str],
        selection_binding: Optional[str],
        *,
        label_lookup: Mapping[str, str],
        claim_lookup: Mapping[str, str],
        created_ids: Sequence[str],
    ) -> Optional[StrategyEvent]:
        if not self._hypothesis_manager:
            return None
        candidate_id = self._resolve_selected_hypothesis_id(
            selection_label,
            label_lookup=label_lookup,
            claim_lookup=claim_lookup,
            created_ids=created_ids,
        )
        if not candidate_id:
            return self._event(
                kind=StrategyEventKind.NOTE,
                message="Diagnose selection did not match any hypothesis",
                iteration=iteration.index,
                data={"selection": selection_label},
            )
        hypothesis = self._hypothesis_manager.get(candidate_id)
        if not hypothesis:
            return None
        self._active_hypothesis_id = candidate_id
        iteration.selected_hypothesis_id = candidate_id
        if selection_rationale:
            hypothesis.selection_rationale = selection_rationale
        if selection_binding:
            hypothesis.binding_region = selection_binding
        self._record_iteration_telemetry(
            iteration,
            "hypothesisSelection",
            {
                "id": candidate_id,
                "rationale": selection_rationale,
                "bindingRegion": selection_binding,
            },
            append=True,
        )
        return self._event(
            kind=StrategyEventKind.NOTE,
            message="Diagnose selected active hypothesis",
            iteration=iteration.index,
            data={
                "hypothesisId": candidate_id,
                "rationale": selection_rationale,
                "bindingRegion": selection_binding,
            },
        )

    def _resolve_selected_hypothesis_id(
        self,
        selection_label: str,
        *,
        label_lookup: Mapping[str, str],
        claim_lookup: Mapping[str, str],
        created_ids: Sequence[str],
    ) -> Optional[str]:
        normalized = self._selection_key(selection_label)
        if not normalized:
            return None
        if self._hypothesis_manager:
            direct = self._hypothesis_manager.get(selection_label)
            if direct:
                return direct.id
        if normalized in label_lookup:
            return label_lookup[normalized]
        if normalized in claim_lookup:
            return claim_lookup[normalized]
        if normalized.startswith("h") and normalized[1:].isdigit():
            candidate_id = selection_label
            if self._hypothesis_manager and self._hypothesis_manager.get(candidate_id):
                return candidate_id
        if normalized.isdigit():
            index = int(normalized) - 1
            if 0 <= index < len(created_ids):
                return created_ids[index]
        return None

    @staticmethod
    def _selection_key(value: str) -> str:
        return value.strip().lower()

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
    def _coerce_confidence(value: Any) -> Optional[float]:
        if value is None:
            return None
        numeric: Optional[float]
        if isinstance(value, (int, float)):
            numeric = float(value)
        elif isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            if stripped.endswith("%"):
                stripped = stripped[:-1].strip()
                if not stripped:
                    return None
                try:
                    numeric = float(stripped) / 100.0
                except ValueError:
                    return None
            else:
                try:
                    numeric = float(stripped)
                except ValueError:
                    return None
        else:
            return None
        if numeric is None:
            return None
        if numeric > 1.0 and numeric <= 100.0:
            numeric = numeric / 100.0
        numeric = max(0.0, min(1.0, numeric))
        return numeric

    @staticmethod
    def _canonical_hypothesis_kind(value: Any) -> Optional[str]:
        text = GuidedConvergenceStrategy._coerce_string(value)
        if not text:
            return None
        normalized = text.lower().replace("-", "_").strip()
        if "group" in normalized or "preced" in normalized:
            return "grouping_precedence"
        if "token" in normalized or "semicolon" in normalized or "delimiter" in normalized:
            return "token_absence"
        return normalized

    def _ensure_active_hypothesis(self, iteration: GuidedIterationArtifact | None) -> Optional[Hypothesis]:
        hypothesis = self._active_hypothesis()
        if hypothesis:
            if iteration and not iteration.selected_hypothesis_id:
                iteration.selected_hypothesis_id = hypothesis.id
            return hypothesis
        return self._select_active_hypothesis(iteration)

    def _select_active_hypothesis(
        self,
        iteration: GuidedIterationArtifact | None,
        *,
        preferred_ids: Optional[Sequence[str]] = None,
    ) -> Optional[Hypothesis]:
        if self._hypothesis_manager is None:
            return None
        candidates = list(self._hypothesis_manager.active())
        if not candidates:
            self._active_hypothesis_id = None
            if iteration:
                iteration.selected_hypothesis_id = None
            return None

        def sort_key(hyp: Hypothesis) -> tuple:
            pref_bonus = 1 if preferred_ids and hyp.id in preferred_ids else 0
            confidence = hyp.confidence if hyp.confidence is not None else 0.0
            return (pref_bonus, confidence, -hyp.retry_count, -self._hypothesis_numeric_id(hyp.id))

        candidates.sort(key=sort_key, reverse=True)
        selected = candidates[0]
        self._active_hypothesis_id = selected.id
        if iteration:
            iteration.selected_hypothesis_id = selected.id
        return selected

    @staticmethod
    def _hypothesis_numeric_id(hypothesis_id: str) -> int:
        match = re.search(r"(\d+)$", hypothesis_id)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return 0
        return 0

    def _active_hypothesis(self) -> Optional[Hypothesis]:
        if not self._hypothesis_manager or not self._active_hypothesis_id:
            return None
        return self._hypothesis_manager.get(self._active_hypothesis_id)

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

    def _hypothesis_prompt_fields(self) -> Dict[str, str]:
        hypothesis = self._active_hypothesis()
        if not hypothesis:
            return {
                "hypothesis_claim": self._hypothesis_claim_placeholder(),
                "hypothesis_region": self._hypothesis_region_placeholder(),
                "hypothesis_effect": self._hypothesis_effect_placeholder(),
                "hypothesis_structure": self._hypothesis_structure_placeholder(),
            }
        region_text = (
            hypothesis.binding_region
            or hypothesis.affected_region
            or self._hypothesis_region_placeholder()
        )
        return {
            "hypothesis_claim": hypothesis.claim or self._hypothesis_claim_placeholder(),
            "hypothesis_region": region_text,
            "hypothesis_effect": hypothesis.expected_effect or self._hypothesis_effect_placeholder(),
            "hypothesis_structure": hypothesis.structural_change or self._hypothesis_structure_placeholder(),
        }

    def _mark_hypothesis_status(
        self,
        hypothesis: Hypothesis,
        status: HypothesisStatus,
        *,
        iteration: GuidedIterationArtifact | None,
        reason: Optional[str] = None,
    ) -> Optional[StrategyEvent]:
        if not self._hypothesis_manager:
            return None
        self._hypothesis_manager.set_status(hypothesis.id, status)
        if self._active_hypothesis_id == hypothesis.id and status is not HypothesisStatus.ACTIVE:
            self._active_hypothesis_id = None
        event = self._event(
            kind=StrategyEventKind.NOTE,
            message=f"Hypothesis {hypothesis.id} marked {status.value}",
            iteration=iteration.index if iteration else None,
            data={
                "hypothesis": hypothesis.to_dict(),
                "reason": reason,
            },
        )
        if iteration:
            self._record_iteration_telemetry(
                iteration,
                "hypothesisStatuses",
                {
                    "id": hypothesis.id,
                    "status": status.value,
                    "reason": reason,
                },
                append=True,
            )
        return event

    def _post_iteration_evaluation(
        self,
        iteration: GuidedIterationArtifact,
        outcome: IterationOutcome,
        previous_outcome: IterationOutcome | None,
    ) -> List[StrategyEvent]:
        events: List[StrategyEvent] = []
        if not outcome or not outcome.hypothesis_id or not self._hypothesis_manager:
            return events
        hypothesis = self._hypothesis_manager.get(outcome.hypothesis_id)
        if not hypothesis or hypothesis.status is not HypothesisStatus.ACTIVE:
            return events

        if not outcome.patch_applied:
            self._register_retry(hypothesis, iteration, outcome.patch_diagnostics or "Patch not applied")
            self._select_active_hypothesis(iteration)
            return events

        stall_summary = self._detect_stall(previous_outcome, outcome)
        if stall_summary:
            iteration.failure_reason = "stall"
            stall_summary["hypothesisId"] = hypothesis.id
            self._record_iteration_telemetry(iteration, "stall", stall_summary, append=True)
            stall_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Stall detected: diff and error signature repeated",
                iteration=iteration.index,
                data=stall_summary,
            )
            self.emit(stall_event)
            events.append(stall_event)
            self._register_retry(
                hypothesis,
                iteration,
                "No new information detected; identical diff span and error output",
            )
            if hypothesis.status is HypothesisStatus.ACTIVE:
                archive_event = self._mark_hypothesis_status(
                    hypothesis,
                    HypothesisStatus.ARCHIVED,
                    iteration=iteration,
                    reason="Hypothesis stalled with identical diff and error",
                )
                if archive_event:
                    self.emit(archive_event)
                    events.append(archive_event)
            self._select_active_hypothesis(iteration)
            return events

        prev_fp = outcome.previous_error_fingerprint
        curr_fp = outcome.error_fingerprint
        if prev_fp is not None and curr_fp is not None and prev_fp == curr_fp:
            self._register_retry(hypothesis, iteration, "Error output unchanged after patch")
            self._record_iteration_telemetry(
                iteration,
                "unchangedError",
                {
                    "previous": prev_fp,
                    "current": curr_fp,
                    "hypothesisId": hypothesis.id,
                },
                append=True,
            )
            if hypothesis.status is HypothesisStatus.ACTIVE:
                event = self._mark_hypothesis_status(
                    hypothesis,
                    HypothesisStatus.REJECTED,
                    iteration=iteration,
                    reason="Error output unchanged after patch",
                )
                if event:
                    self.emit(event)
                    events.append(event)
            self._select_active_hypothesis(iteration)
            return events

        if outcome.compile_returncode not in (None, 0):
            self._register_retry(
                hypothesis,
                iteration,
                f"Compile/test failed with return code {outcome.compile_returncode}",
            )
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

    def _register_retry(
        self,
        hypothesis: Hypothesis,
        iteration: GuidedIterationArtifact,
        reason: Optional[str],
    ) -> None:
        if not self._hypothesis_manager:
            return
        retries = self._hypothesis_manager.increment_retry(hypothesis.id) or 0
        retry_event = self._event(
            kind=StrategyEventKind.NOTE,
            message="Hypothesis retry recorded",
            iteration=iteration.index,
            data={"hypothesisId": hypothesis.id, "retryCount": retries, "reason": reason},
        )
        self.emit(retry_event)
        self._record_iteration_telemetry(
            iteration,
            "retries",
            {"hypothesisId": hypothesis.id, "retryCount": retries, "reason": reason},
            append=True,
        )
        if retries >= 2 and hypothesis.status is HypothesisStatus.ACTIVE:
            expire_event = self._mark_hypothesis_status(
                hypothesis,
                HypothesisStatus.EXPIRED,
                iteration=iteration,
                reason="Exceeded retry limit",
            )
            if expire_event:
                self.emit(expire_event)
            self._select_active_hypothesis(iteration)

    def _phase_machine_payload(
        self,
        iteration: GuidedIterationArtifact,
        phase: GuidedPhase,
        key: str,
    ) -> Mapping[str, Any]:
        for artifact in iteration.phases:
            if artifact.phase != phase:
                continue
            machine_checks = getattr(artifact, "machine_checks", None)
            if not isinstance(machine_checks, Mapping):
                continue
            payload = machine_checks.get(key)
            if isinstance(payload, Mapping):
                return payload
        return {}

    @staticmethod
    def _ensure_machine_checks_dict(artifact: PhaseArtifact) -> Dict[str, Any]:
        if isinstance(artifact.machine_checks, dict):
            return artifact.machine_checks
        materialized = dict(artifact.machine_checks or {})
        artifact.machine_checks = materialized
        return materialized

    def _analyze_diagnose_response(self, text: str) -> Mapping[str, Any]:
        if not text:
            return {}
        analysis: Dict[str, Any] = {"diagnosis": text.strip()}
        hypotheses = self._extract_plain_hypotheses(text)
        if hypotheses:
            analysis["hypotheses"] = hypotheses
        selection_label, selection_rationale = self._active_hypothesis_from_text(text)
        if selection_label:
            analysis["selected_hypothesis"] = selection_label
            if selection_rationale:
                analysis["selection_rationale"] = selection_rationale
                analysis.setdefault("rationale", selection_rationale)
            normalized = self._selection_key(selection_label)
            for entry in hypotheses:
                identifier = entry.get("identifier")
                if identifier and self._selection_key(identifier) == normalized:
                    region = entry.get("affected_region")
                    if region:
                        analysis["binding_region"] = region
                    break
        return analysis

    def _summarize_proposal_response(self, text: str) -> Mapping[str, Any]:
        summary = self._coerce_string(text)
        if not summary:
            return {}
        intent = self._first_sentence(summary) or summary
        return {
            "intent": intent,
            "structural_change": summary,
        }

    @staticmethod
    def _first_sentence(text: str) -> Optional[str]:
        if not text:
            return None
        match = re.search(r"(.+?[.!?])(\s|$)", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        lines = text.splitlines()
        return lines[0].strip() if lines else text.strip()

    def _extract_plain_hypotheses(self, text: str) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if not text:
            return entries
        pattern = re.compile(r"\*\*(H\d+[^*]*)\*\*(.*?)(?=\n\s*\*\*H\d+|\Z)", re.S)
        matches = list(pattern.finditer(text))
        if not matches:
            pattern = re.compile(r"(H\d+[^:]*):(.*?)(?=\n\s*H\d+|\Z)", re.S)
            matches = list(pattern.finditer(text))
        for match in matches:
            label = match.group(1).strip()
            block = match.group(2).strip()
            claim = self._extract_markdown_field(block, "Structural Claim")
            if not claim:
                first_line = block.splitlines()[0].strip() if block else label
                claim = re.sub(r"^[-•\s]+", "", first_line)
            affected = self._extract_markdown_field(block, "Affected Code Region") or "Unspecified region"
            effect = self._extract_markdown_field(block, "Expected Effect")
            evidence = (
                self._extract_markdown_field(block, "Evidence")
                or self._extract_markdown_field(block, "Explanation")
                or self._extract_markdown_field(block, "Rationale")
            )
            expected_effect = effect or evidence or claim
            confidence_text = self._extract_markdown_field(block, "Confidence")
            confidence = self._coerce_confidence(confidence_text) if confidence_text else None
            entries.append(
                {
                    "claim": claim,
                    "affected_region": affected,
                    "expected_effect": expected_effect,
                    "explanation": evidence,
                    "identifier": label,
                    "confidence": confidence,
                }
            )
        return entries

    @staticmethod
    def _extract_markdown_field(block: str, label: str) -> Optional[str]:
        if not block:
            return None
        pattern = re.compile(rf"{re.escape(label)}\s*[:|-]\s*(.+)", re.IGNORECASE)
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = line.lstrip("-*•").strip()
            line = re.sub(r"[\*_`]", "", line)
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        return None

    def _active_hypothesis_from_text(self, text: str) -> tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        match = re.search(r"Active Hypothesis[^:]*:\s*(.+)", text, re.IGNORECASE)
        if not match:
            return None, None
        label_text = match.group(1).strip()
        label_match = re.search(r"(H\d+)", label_text, re.IGNORECASE)
        label = label_match.group(1).upper() if label_match else label_text
        remainder = text[match.end():]
        justification_match = re.search(r"Justification\s*[:|-]\s*(.+?)(?:\n\s*\n|$)", remainder, re.IGNORECASE | re.DOTALL)
        rationale = justification_match.group(1).strip() if justification_match else remainder.strip()
        return label, rationale or None

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
    def _proposal_placeholder() -> str:
        return "Proposal not available yet; run the Propose phase first."

    @staticmethod
    def _hypothesis_claim_placeholder() -> str:
        return "No active hypothesis claim has been selected yet."

    @staticmethod
    def _hypothesis_region_placeholder() -> str:
        return "No active hypothesis region is available yet."

    @staticmethod
    def _hypothesis_effect_placeholder() -> str:
        return "No expected effect recorded; generate hypotheses during Diagnose."

    @staticmethod
    def _patch_diagnostics_placeholder() -> str:
        return "No patch diagnostics available yet."

    @staticmethod
    def _hypothesis_structure_placeholder() -> str:
        return "No structural change rationale recorded yet."

    @staticmethod
    def _critique_placeholder() -> str:
        return "No prior critique feedback yet; this is the initial attempt."

    @staticmethod
    def _previous_diff_placeholder() -> str:
        return "No previous replacement attempt has been recorded."

    @staticmethod
    def _prior_hypothesis_placeholder() -> str:
        return "No prior hypothesis has been recorded yet."

    @staticmethod
    def _prior_patch_placeholder() -> str:
        return "No prior suggested patch is available yet."

    @staticmethod
    def _history_placeholder() -> str:
        return "No prior iterations have run yet."

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
        diagnosis_text: str,
        before_snippet: str,
        after_snippet: str,
        diff_text: str,
        validation_summary: str,
    ) -> str:
        header = (
            "Critique the replacement block(s) that were successfully applied to this source code."
            if applied
            else "Critique the proposed replacement block(s). The patch diagnostics are provided below."
        )
        checklist = (
            "1) Does it appear to solve and fix the original problem?\n"
            "2) Is it a minimal set of changes to address the problem?\n"
            "3) Is the initial analysis correct or flawed?\n"
            "4) Can the code be simplified to help analysis of the error?"
        )
        sections = [
            header,
            checklist,
            f"Recent iteration history:\n{history_context}",
            f"Original error:\n{error_text}",
            f"Original Diagnosis Summary:\n{diagnosis_text}",
            "Original Code before suggested replacement was applied:\n" + (before_snippet or "Source unavailable."),
            "Replacement block(s) that were applied:\n" + diff_text.strip(),
            "Updated Code after suggested replacement was applied:\n" + (after_snippet or "Source unavailable."),
            f"Validation summary:\n{validation_summary}",
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
        diagnosis_text: str,
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
            diagnosis_text=diagnosis_text,
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