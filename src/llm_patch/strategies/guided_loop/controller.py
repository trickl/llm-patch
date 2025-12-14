"""Guided Convergence Loop orchestration scaffolding."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from llm_patch.patch_applier import PatchApplier
PATCH_CONSTRAINTS_TEXT = "\n".join(
    [
        "- Do not reformat unrelated code.",
        "- Do not rename symbols.",
        "- Change only within this method unless strictly necessary.",
        "- Prefer the smallest valid diff.",
    ]
)

PATCH_EXAMPLE_DIFF = (
    "--- lao\t2002-02-21 23:30:39.942229878 -0800\n"
    "+++ tzu\t2002-02-21 23:30:50.442260588 -0800\n"
    "@@ -1,7 +1,6 @@\n"
    "-The Way that can be told of is not the eternal Way;\n"
    "-The name that can be named is not the eternal name.\n"
    " The Nameless is the origin of Heaven and Earth;\n"
    "-The Named is the mother of all things.\n"
    "+The named is the mother of all things.\n"
    "+\n"
    " Therefore let there always be non-being,\n"
    "   so we may see their subtlety,\n"
    " And let there always be being,\n"
    "@@ -9,3 +8,6 @@\n"
    " The two are the same,\n"
    " But after they are produced,\n"
    "   they have different names.\n"
    "+They both may be called deep and profound.\n"
    "+Deeper and more profound,\n"
    "+The door of all subtleties!"
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
    CHECKLIST_FRAGMENT,
    CONSTRAINTS_FRAGMENT,
    CONTEXT_FRAGMENT,
    CRITIQUE_FRAGMENT,
    DIAGNOSE_INSTRUCTIONS_FRAGMENT,
    DIAGNOSE_JSON_SCHEMA_FRAGMENT,
    DIAGNOSIS_RATIONALE_FRAGMENT,
    DIAGNOSIS_SUMMARY_FRAGMENT,
    ERROR_FRAGMENT,
    EXAMPLE_DIFF_FRAGMENT,
    FALSIFY_INSTRUCTIONS_FRAGMENT,
    FALSIFY_JSON_SCHEMA_FRAGMENT,
    GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
    HISTORY_FRAGMENT,
    HYPOTHESIS_CONTEXT_FRAGMENT,
    INTERPRET_JSON_SCHEMA_FRAGMENT,
    INTERPRETATION_RATIONALE_FRAGMENT,
    INTERPRETATION_SUMMARY_FRAGMENT,
    PATCH_DIAGNOSTICS_FRAGMENT,
    PREVIOUS_DIFF_FRAGMENT,
    PROPOSE_INSTRUCTIONS_FRAGMENT,
    PROPOSAL_SUMMARY_FRAGMENT,
    PROPOSE_JSON_SCHEMA_FRAGMENT,
    STRUCTURAL_REASONING_FRAGMENT,
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
    falsification_summary: Optional[str] = None
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
        GuidedPhase.INTERPRET: compose_prompt(
            CHECKLIST_FRAGMENT,
            STRUCTURAL_REASONING_FRAGMENT,
            HISTORY_FRAGMENT,
            ERROR_FRAGMENT,
            CRITIQUE_FRAGMENT,
            INTERPRET_JSON_SCHEMA_FRAGMENT,
        ),
        GuidedPhase.DIAGNOSE: compose_prompt(
            CHECKLIST_FRAGMENT,
            DIAGNOSE_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            CRITIQUE_FRAGMENT,
            ERROR_FRAGMENT,
            INTERPRETATION_SUMMARY_FRAGMENT,
            INTERPRETATION_RATIONALE_FRAGMENT,
            CONTEXT_FRAGMENT,
            DIAGNOSE_JSON_SCHEMA_FRAGMENT,
        ),
        GuidedPhase.PROPOSE: compose_prompt(
            CHECKLIST_FRAGMENT,
            PROPOSE_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PREVIOUS_DIFF_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            HYPOTHESIS_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
            PROPOSE_JSON_SCHEMA_FRAGMENT,
        ),
        GuidedPhase.FALSIFY: compose_prompt(
            CHECKLIST_FRAGMENT,
            FALSIFY_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PATCH_DIAGNOSTICS_FRAGMENT,
            HYPOTHESIS_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
            FALSIFY_JSON_SCHEMA_FRAGMENT,
        ),
        GuidedPhase.GENERATE_PATCH: compose_prompt(
            CHECKLIST_FRAGMENT,
            GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            CRITIQUE_FRAGMENT,
            PREVIOUS_DIFF_FRAGMENT,
            PROPOSAL_SUMMARY_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            HYPOTHESIS_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
            CONSTRAINTS_FRAGMENT,
            EXAMPLE_DIFF_FRAGMENT,
        ),
        GuidedPhase.CRITIQUE: (
            "Critique the diff. Does it respect the constraints? Identify non-minimal or risky edits."
        ),
        GuidedPhase.CONVERGE: (
            "Decide whether to accept the patch. Mention remaining risks or blockers."
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
        if kind == "refine":
            return [
                GuidedPhase.DIAGNOSE,
                GuidedPhase.FALSIFY,
                GuidedPhase.PROPOSE,
                GuidedPhase.GENERATE_PATCH,
                GuidedPhase.CRITIQUE,
            ]
        return [
            GuidedPhase.INTERPRET,
            GuidedPhase.DIAGNOSE,
            GuidedPhase.FALSIFY,
            GuidedPhase.PROPOSE,
            GuidedPhase.GENERATE_PATCH,
            GuidedPhase.CRITIQUE,
            GuidedPhase.CONVERGE,
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
            "interpretation": self._interpretation_placeholder(),
            "interpretation_explanation": self._explanation_placeholder(),
            "diagnosis": self._diagnosis_placeholder(),
            "diagnosis_explanation": self._explanation_placeholder(),
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
            cls._interpretation_placeholder(),
            cls._explanation_placeholder(),
            cls._diagnosis_placeholder(),
            cls._proposal_placeholder(),
            cls._hypothesis_claim_placeholder(),
            cls._hypothesis_region_placeholder(),
            cls._hypothesis_effect_placeholder(),
            cls._hypothesis_structure_placeholder(),
            cls._patch_diagnostics_placeholder(),
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
            if artifact.phase == GuidedPhase.INTERPRET:
                events.extend(self._execute_interpret(artifact, iteration.index, request))
                continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.DIAGNOSE:
                if continue_execution:
                    events.extend(self._execute_diagnose(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.FALSIFY:
                if continue_execution:
                    events.extend(
                        self._execute_falsify(
                            artifact,
                            iteration,
                            iteration.index,
                            request,
                            prior_outcome=prior_outcome,
                        )
                    )
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

    def _execute_interpret(
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
            message="Starting Interpret phase",
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
            artifact.human_notes = f"Interpret phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Interpret phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        self._store_structured_sections(artifact, artifact.response)
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Interpret phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
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
        structured = self._store_structured_sections(artifact, artifact.response)
        hypothesis_events = self._ingest_hypotheses(iteration, structured)
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

    def _execute_falsify(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
        *,
        prior_outcome: IterationOutcome | None,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Falsify phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)

        hypothesis = self._ensure_active_hypothesis(iteration)
        if hypothesis is None:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "No active hypothesis available for falsification."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Falsify phase failed: no active hypothesis",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events

        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Falsify phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Falsify phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events

        artifact.response = response.strip()
        structured = self._store_structured_sections(artifact, artifact.response)
        summary, has_viable, falsify_events = self._apply_falsification_results(
            iteration,
            hypothesis,
            structured,
            prior_outcome=prior_outcome,
        )
        for extra_event in falsify_events:
            self.emit(extra_event)
            events.append(extra_event)
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["falsification"] = summary
        artifact.status = PhaseStatus.COMPLETED if has_viable else PhaseStatus.FAILED
        artifact.completed_at = self._now()
        if not has_viable:
            artifact.human_notes = "All hypotheses were rejected by falsification; regenerate diagnoses."
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Falsify phase completed" if has_viable else "Falsify phase rejected all hypotheses",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"status": summary.get("status"), "remainingHypotheses": summary.get("remaining")},
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
        structured = self._store_structured_sections(artifact, artifact.response)
        intent = self._coerce_string(structured.get("intent") if structured else None)
        structural_change = self._coerce_string(structured.get("structural_change") if structured else None)
        if not intent or not structural_change:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Proposal must return JSON with 'intent' and 'structural_change'."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed: malformed JSON",
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

        diagnosis_struct = self._structured_value(iteration, GuidedPhase.DIAGNOSE, "interpretation")
        diagnosis_fallback = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
        diagnosis_text = diagnosis_struct or diagnosis_fallback or self._diagnosis_placeholder()
        error_text = request.error_text or "(error unavailable)"
        history_context = iteration.history_context or self._history_placeholder()
        pre_span, post_span = self._diff_spans(diff_text)
        before_snippet = self._critique_snippet(
            request.source_text,
            pre_span,
            fallback=self._focused_context_window(request),
        )
        outcome = IterationOutcome(diff_text=diff_text, critique_feedback=artifact.response)
        outcome.diff_span = pre_span

        active_hypothesis = None
        if self._hypothesis_manager and iteration.selected_hypothesis_id:
            active_hypothesis = self._hypothesis_manager.get(iteration.selected_hypothesis_id)
        if not self._validate_patch_scope(pre_span, active_hypothesis):
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Diff edits extend beyond the active hypothesis region."
            iteration.failure_reason = "scope-violation"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: patch violates hypothesis scope",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"hypothesis": active_hypothesis.to_dict() if active_hypothesis else None},
            )
            self.emit(failure_event)
            events.append(failure_event)
            outcome.patch_diagnostics = "Diff edits extend beyond the hypothesis region."
            after_snippet = "Patched output unavailable because the diff violated the hypothesis scope."
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

        if artifact.phase == GuidedPhase.INTERPRET:
            artifact.prompt = self._render_prompt(
                GuidedPhase.INTERPRET,
                request,
                extra={
                    "critique_feedback": critique_feedback,
                    "previous_diff": previous_diff,
                    "patch_diagnostics": prev_diagnostics or "",
                    "history_context": history_context,
                },
            )
        elif artifact.phase == GuidedPhase.DIAGNOSE:
            interpretation_struct = self._structured_value(iteration, GuidedPhase.INTERPRET, "interpretation")
            interpretation_explanation = self._structured_value(iteration, GuidedPhase.INTERPRET, "explanation")
            interpretation_fallback = self._find_phase_response(iteration, GuidedPhase.INTERPRET)
            artifact.prompt = self._render_prompt(
                GuidedPhase.DIAGNOSE,
                request,
                context_override=context_override,
                extra={
                    "interpretation": interpretation_struct
                    or interpretation_fallback
                    or self._interpretation_placeholder(),
                    "interpretation_explanation": interpretation_explanation or self._explanation_placeholder(),
                    "critique_feedback": critique_feedback,
                    "previous_diff": previous_diff,
                    "history_context": history_context,
                },
            )
        elif artifact.phase == GuidedPhase.FALSIFY:
            self._ensure_active_hypothesis(iteration)
            hypothesis_fields = self._hypothesis_prompt_fields()
            artifact.prompt = self._render_prompt(
                GuidedPhase.FALSIFY,
                request,
                context_override=context_override,
                extra={
                    "critique_feedback": critique_feedback,
                    "history_context": history_context,
                    "patch_diagnostics": prev_diagnostics or self._patch_diagnostics_placeholder(),
                    **hypothesis_fields,
                },
            )
        elif artifact.phase == GuidedPhase.PROPOSE:
            diagnosis_struct = self._structured_value(iteration, GuidedPhase.DIAGNOSE, "interpretation")
            diagnosis_explanation = self._structured_value(iteration, GuidedPhase.DIAGNOSE, "explanation")
            diagnosis_fallback = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
            self._ensure_active_hypothesis(iteration)
            hypothesis_fields = self._hypothesis_prompt_fields()
            artifact.prompt = self._render_prompt(
                GuidedPhase.PROPOSE,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": diagnosis_struct or diagnosis_fallback or self._diagnosis_placeholder(),
                    "diagnosis_explanation": diagnosis_explanation or self._explanation_placeholder(),
                    "critique_feedback": critique_feedback,
                    "history_context": history_context,
                    "previous_diff": previous_diff,
                    **hypothesis_fields,
                },
            )
        elif artifact.phase == GuidedPhase.GENERATE_PATCH:
            diagnosis_struct = self._structured_value(iteration, GuidedPhase.DIAGNOSE, "interpretation")
            diagnosis_explanation = self._structured_value(iteration, GuidedPhase.DIAGNOSE, "explanation")
            diagnosis_fallback = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
            proposal_struct = self._structured_value(iteration, GuidedPhase.PROPOSE, "intent")
            proposal_summary = proposal_struct or self._find_phase_response(iteration, GuidedPhase.PROPOSE)
            self._ensure_active_hypothesis(iteration)
            hypothesis_fields = self._hypothesis_prompt_fields()
            artifact.prompt = self._render_prompt(
                GuidedPhase.GENERATE_PATCH,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": diagnosis_struct or diagnosis_fallback or self._diagnosis_placeholder(),
                    "diagnosis_explanation": diagnosis_explanation or self._explanation_placeholder(),
                    "proposal": proposal_summary or self._proposal_placeholder(),
                    "critique_feedback": critique_feedback,
                    "history_context": history_context,
                    "previous_diff": previous_diff,
                    **hypothesis_fields,
                },
            )

    def _find_phase_response(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[str]:
        for artifact in iteration.phases:
            if artifact.phase == phase and artifact.response:
                return artifact.response
        return None

    def _structured_value(self, iteration: GuidedIterationArtifact, phase: GuidedPhase, field: str) -> Optional[str]:
        payload = self._structured_payload(iteration, phase)
        value = payload.get(field)
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None

    def _structured_payload(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Mapping[str, Any]:
        for artifact in iteration.phases:
            if artifact.phase != phase:
                continue
            machine_checks = getattr(artifact, "machine_checks", None)
            if not isinstance(machine_checks, Mapping):
                continue
            payload = machine_checks.get("structured")
            if isinstance(payload, Mapping):
                return payload
        return {}

    def _ingest_hypotheses(
        self,
        iteration: GuidedIterationArtifact,
        structured: Mapping[str, Any],
    ) -> List[StrategyEvent]:
        events: List[StrategyEvent] = []
        if not structured or self._hypothesis_manager is None:
            return events
        raw_entries = structured.get("hypotheses")
        if not isinstance(raw_entries, list):
            return events
        parsed_entries: List[Dict[str, Any]] = []
        for entry in raw_entries:
            normalized = self._normalize_hypothesis_entry(entry)
            if normalized:
                parsed_entries.append(normalized)
        if not parsed_entries:
            return events
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
        interpretation = self._coerce_string(structured.get("interpretation"))
        explanation = self._coerce_string(structured.get("explanation"))
        created_ids: List[str] = []
        for entry in parsed_entries:
            hypothesis = self._hypothesis_manager.create(
                claim=entry["claim"],
                affected_region=entry["affected_region"],
                expected_effect=entry["expected_effect"],
                interpretation=interpretation,
                explanation=entry.get("explanation") or explanation,
                structural_change=entry.get("structural_change"),
                confidence=entry.get("confidence"),
            )
            created_ids.append(hypothesis.id)
        if created_ids:
            events.append(
                self._event(
                    kind=StrategyEventKind.NOTE,
                    message="Recorded structural hypotheses",
                    iteration=iteration.index,
                    data={"hypotheses": created_ids},
                )
            )
            self._record_iteration_telemetry(
                iteration,
                "hypothesesCreated",
                {"ids": created_ids, "count": len(created_ids)},
                append=True,
            )
        iteration.hypotheses = self._hypothesis_manager.snapshot()
        self._select_active_hypothesis(iteration, preferred_ids=created_ids)
        return events

    def _normalize_hypothesis_entry(self, entry: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(entry, Mapping):
            return None
        claim = self._coerce_string(entry.get("claim") or entry.get("hypothesis"))
        if not claim:
            return None
        affected_region = self._coerce_string(
            entry.get("affected_region") or entry.get("region") or entry.get("scope")
        ) or "Unspecified region"
        expected_effect = self._coerce_string(
            entry.get("expected_effect") or entry.get("effect") or entry.get("observable")
        ) or claim
        structural_change = self._coerce_string(entry.get("structural_change") or entry.get("structuralDelta"))
        explanation = self._coerce_string(entry.get("explanation") or entry.get("evidence") or entry.get("rationale"))
        confidence = self._coerce_confidence(entry.get("confidence") or entry.get("plausibility"))
        return {
            "claim": claim,
            "affected_region": affected_region,
            "expected_effect": expected_effect,
            "structural_change": structural_change,
            "explanation": explanation,
            "confidence": confidence,
        }

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
        return {
            "hypothesis_claim": hypothesis.claim or self._hypothesis_claim_placeholder(),
            "hypothesis_region": hypothesis.affected_region or self._hypothesis_region_placeholder(),
            "hypothesis_effect": hypothesis.expected_effect or self._hypothesis_effect_placeholder(),
            "hypothesis_structure": hypothesis.structural_change or self._hypothesis_structure_placeholder(),
        }

    def _apply_falsification_results(
        self,
        iteration: GuidedIterationArtifact,
        hypothesis: Hypothesis,
        structured: Mapping[str, Any],
        *,
        prior_outcome: IterationOutcome | None,
    ) -> tuple[Dict[str, Any], bool, List[StrategyEvent]]:
        contradictions = self._extract_contradictions(structured)
        auto_contradictions = self._auto_contradictions(hypothesis, prior_outcome)
        observed: List[str] = []
        pending: List[str] = []
        for entry in contradictions:
            note = entry.get("observation")
            if not note:
                continue
            status = (entry.get("status") or "pending").lower()
            evidence = entry.get("evidence")
            text = note if not evidence else f"{note} ({evidence})"
            if status == "observed":
                observed.append(text)
            else:
                pending.append(text)
        observed.extend(auto_contradictions.get("observed", []))
        pending.extend(auto_contradictions.get("pending", []))
        summary: Dict[str, Any] = {
            "hypothesisId": hypothesis.id,
            "observed": observed,
            "pending": pending,
            "auto": auto_contradictions,
            "summary": structured.get("summary"),
        }
        for note in observed + pending:
            hypothesis.add_falsification_note(note)

        extra_events: List[StrategyEvent] = []
        if observed:
            rejection_reason = observed[0]
            rejection_event = self._mark_hypothesis_status(
                hypothesis,
                HypothesisStatus.FALSIFIED,
                iteration=iteration,
                reason=f"Falsified: {rejection_reason}",
            )
            if rejection_event:
                extra_events.append(rejection_event)
            summary["status"] = "rejected"
        else:
            summary["status"] = "viable"

        remaining = self._hypothesis_manager.active_count() if self._hypothesis_manager else 0
        summary["remaining"] = remaining
        self._record_iteration_telemetry(iteration, "falsification", summary, append=True)

        if summary["status"] == "rejected":
            # Select a replacement hypothesis immediately, if possible.
            self._select_active_hypothesis(iteration)

        has_viable = self._active_hypothesis() is not None
        return summary, has_viable, extra_events

    def _extract_contradictions(self, structured: Mapping[str, Any]) -> List[Dict[str, str]]:
        raw = structured.get("contradictions") if structured else None
        if not isinstance(raw, list):
            return []
        contradictions: List[Dict[str, str]] = []
        for item in raw:
            if isinstance(item, Mapping):
                observation = self._coerce_string(
                    item.get("observation") or item.get("description") or item.get("statement")
                )
                if not observation:
                    continue
                status = self._coerce_string(item.get("status")) or "pending"
                evidence = self._coerce_string(item.get("evidence") or item.get("proof") or "")
            elif isinstance(item, str):
                observation = item.strip()
                if not observation:
                    continue
                status = "pending"
                evidence = None
            else:
                continue
            contradictions.append(
                {
                    "observation": observation,
                    "status": status.lower(),
                    "evidence": evidence,
                }
            )
        return contradictions

    def _auto_contradictions(
        self,
        hypothesis: Hypothesis,
        prior_outcome: IterationOutcome | None,
    ) -> Dict[str, List[str]]:
        contradictions: Dict[str, List[str]] = {"observed": [], "pending": []}
        if not prior_outcome or prior_outcome.hypothesis_id != hypothesis.id:
            return contradictions
        if not prior_outcome.patch_applied:
            note = prior_outcome.patch_diagnostics or "Patch could not be applied."
            contradictions["pending"].append(f"Previous patch attempt failed: {note}")
        elif prior_outcome.compile_returncode not in (None, 0):
            contradictions["pending"].append(
                "Previous patch applied but compile/test still failed"
            )
        return contradictions

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

    def _store_structured_sections(self, artifact: PhaseArtifact, text: str) -> Mapping[str, Any]:
        structured = self._parse_structured_sections(text)
        if not structured:
            return structured
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["structured"] = structured
        return structured

    @staticmethod
    def _ensure_machine_checks_dict(artifact: PhaseArtifact) -> Dict[str, Any]:
        if isinstance(artifact.machine_checks, dict):
            return artifact.machine_checks
        materialized = dict(artifact.machine_checks or {})
        artifact.machine_checks = materialized
        return materialized

    def _parse_structured_sections(self, text: str) -> Mapping[str, Any]:
        if not text:
            return {}
        candidate = self._extract_json_candidate(text)
        if candidate is None:
            return {}
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, Mapping):
            return {}
        return dict(parsed)

    @staticmethod
    def _extract_json_candidate(text: str) -> Optional[str]:
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        first = text.find("{")
        last = text.rfind("}")
        if first == -1 or last == -1 or last <= first:
            return None
        return text[first : last + 1]

    @staticmethod
    def _error_fingerprint(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return None
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _interpretation_placeholder() -> str:
        return "Interpretation not available yet; run the Interpret phase first."

    @staticmethod
    def _explanation_placeholder() -> str:
        return "Explanation not available yet; capture it during the relevant phase."

    @staticmethod
    def _diagnosis_placeholder() -> str:
        return "Diagnosis not available yet; run the Diagnose phase first."

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
        return "No previous diff attempt has been recorded."

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

    @staticmethod
    def _diff_spans(diff_text: str) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
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

        def _aggregate(spans: List[tuple[int, int]]) -> tuple[int, int] | None:
            if not spans:
                return None
            start = min(span[0] for span in spans)
            end = max(span[1] for span in spans)
            return start, end

        return _aggregate(spans_a), _aggregate(spans_b)

    def _validate_patch_scope(
        self,
        diff_span: tuple[int, int] | None,
        hypothesis: Hypothesis | None,
    ) -> bool:
        if diff_span is None or hypothesis is None:
            return True
        region_span = self._parse_region_span(hypothesis.affected_region)
        if region_span is None:
            return True
        diff_start, diff_end = diff_span
        region_start, region_end = region_span
        return region_start <= diff_start and diff_end <= region_end

    def _parse_region_span(self, descriptor: Optional[str]) -> Optional[tuple[int, int]]:
        if not descriptor:
            return None
        numbers = re.findall(r"\d+", descriptor)
        if not numbers:
            return None
        try:
            values = [int(num) for num in numbers]
        except ValueError:
            return None
        if len(values) == 1:
            value = values[0]
            return value, value
        start, end = values[0], values[1]
        if start > end:
            start, end = end, start
        return start, end

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
            "Critique the following unified diff that was successfully applied to this source code."
            if applied
            else "Critique the following unified diff. The patch diagnostics are provided below."
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
            "Original Code before suggested diff was applied:\n" + (before_snippet or "Source unavailable."),
            "Unified Diff that was applied:\n" + diff_text.strip(),
            "Updated Code after suggested diff was applied:\n" + (after_snippet or "Source unavailable."),
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

    def _run_compile(self, request: GuidedLoopInputs, patched_text: str) -> Dict[str, Any]:
        command = list(request.compile_command or [])
        if not command:
            return {"command": [], "returncode": None, "stdout": "", "stderr": ""}
        try:
            with tempfile.TemporaryDirectory(prefix="llm_patch_guided_") as tmpdir:
                tmp_path = Path(tmpdir)
                source_file = tmp_path / request.source_path.name
                source_file.write_text(patched_text, encoding="utf-8")
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