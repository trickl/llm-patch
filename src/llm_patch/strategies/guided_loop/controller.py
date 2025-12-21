"""Guided Convergence Loop orchestration scaffolding."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from textwrap import dedent
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Match, Optional, Protocol, Sequence, Tuple

from diff_match_patch import diff_match_patch

from llm_patch.patch_applier import PatchApplier, normalize_replacement_block
from .compilation import run_compile
from . import error_processing
from . import gathering
from . import patching
from . import prompting
from . import evaluation
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
    "CHANGED LINES:\n"
    "return tokens.stream()\n"
    "        .map(token -> token.equals(\"-\") && inPrefixContext(previous)\n"
    "                ? \"0-\" : token)\n"
    "        .collect(Collectors.toList());\n"
)

REPLACEMENT_BLOCK_PATTERN = re.compile(
    r"ORIGINAL LINES:\s*\n(?P<original>.*?)\n(?:CHANGED|NEW) LINES:\s*\n(?P<updated>.*?)(?=(?:\nORIGINAL LINES:|\Z))",
    re.DOTALL,
)

from ..base import PatchRequest, PatchStrategy, StrategyEvent, StrategyEventKind
from .models import GuidedLoopConfig, GuidedLoopInputs, GuidedLoopResult, IterationOutcome
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
    GATHERED_CONTEXT_FRAGMENT,
    GATHER_INSTRUCTIONS_FRAGMENT,
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
        GuidedPhase.GATHER: compose_prompt(
            GATHER_INSTRUCTIONS_FRAGMENT,
            ERROR_FRAGMENT,
            EXPERIMENT_SUMMARY_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.PROPOSE: compose_prompt(
            PROPOSE_INSTRUCTIONS_FRAGMENT,
            REFINEMENT_CONTEXT_FRAGMENT,
            ERROR_FRAGMENT,
            EXPERIMENT_SUMMARY_FRAGMENT,
            GATHERED_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.GENERATE_PATCH: compose_prompt(
            GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
            PROPOSAL_SUMMARY_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            GATHERED_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
            CONSTRAINTS_FRAGMENT,
            EXAMPLE_REPLACEMENT_FRAGMENT,
        ),
        GuidedPhase.CRITIQUE: dedent(
            """
            Begin with a Markdown heading that states the hypothesis label and its description (for example: "### H2 – Missing comma in enum").
            Critique the replacement block(s). Do they respect the constraints? Identify non-minimal or risky edits.
            Tie your observations back to the named hypothesis so later phases can cite this critique verbatim.
            """
        ),
    }

    POINTER_SUMMARY_LANGUAGES = error_processing.POINTER_SUMMARY_LANGUAGES
    ERROR_LINE_PATTERN = error_processing.ERROR_LINE_PATTERN
    WARNING_LINE_PATTERN = error_processing.WARNING_LINE_PATTERN
    NOTE_LINE_PATTERN = error_processing.NOTE_LINE_PATTERN
    POINTER_ALLOWED_CHARS = error_processing.POINTER_ALLOWED_CHARS
    TOKEN_PATTERN = error_processing.TOKEN_PATTERN
    CONTEXT_RADIUS = 5
    SUFFIX_COLLAPSE_MAX_LINES = 8
    SUFFIX_COLLAPSE_SIMILARITY = 0.97
    GATHER_ALLOWED_CATEGORIES = {
        "ENCLOSING_SCOPE",
        "DECLARATION",
        "IMPORTS_NAMESPACE",
        "TYPE_CONTEXT",
        "FILE_CONTEXT",
        "USAGE_CONTEXT",
    }
    GATHER_ALLOWED_TARGET_KINDS = {"symbol", "type", "module", "unknown"}

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
        self._dmp = diff_match_patch()
        self._baseline_error_fingerprint: Optional[str] = None
        self._latest_diagnosis_output: Optional[str] = None
        self._critique_transcripts: list[str] = []

    def run(self, request: PatchRequest) -> GuidedLoopResult:
        inputs = self._ensure_inputs(request)
        self._latest_diagnosis_output = None
        self._critique_transcripts = []
        baseline_source = inputs.raw_error_text or inputs.error_text
        self._baseline_error_fingerprint = self._error_fingerprint(baseline_source)
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
            processed_error = self._prepare_compile_error_text(
                request.raw_error_text or request.error_text,
                request.language,
            )
            request.error_text = processed_error
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
        processed_error = self._prepare_compile_error_text(request.error_text, request.language)
        return GuidedLoopInputs(
            case_id=request.case_id,
            language=request.language,
            source_path=request.source_path,
            source_text=request.source_text,
            error_text=processed_error,
            manifest=request.manifest,
            extra=request.extra,
            raw_error_text=request.error_text,
            additional_context=extra_context,
            history_seed=history_seed,
            initial_outcome=initial_outcome,
        )

    def _prepare_compile_error_text(self, error_text: Optional[str], language: Optional[str]) -> str:
        return error_processing.prepare_compile_error_text(error_text, language)

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
        passes = max(1, self._config.main_loop_passes)
        iteration_counter = 0
        loop_counter = 0
        refine_counter = 0

        for pass_index in range(1, passes + 1):
            include_full_critiques = pass_index > 1
            for _ in range(primary_iterations):
                iteration_counter += 1
                loop_counter += 1
                label = f"Loop {loop_counter}"
                iteration = GuidedIterationArtifact(
                    index=iteration_counter,
                    kind="primary",
                    label=label,
                    pass_index=pass_index,
                    include_full_critiques=include_full_critiques,
                )
                for phase in self._phase_order(kind="primary"):
                    prompt = self._render_prompt(phase, request)
                    artifact = PhaseArtifact(phase=phase, status=PhaseStatus.PLANNED, prompt=prompt)
                    trace.add_phase(iteration, artifact)
                trace.iterations.append(iteration)

            for _ in range(refine_iterations):
                iteration_counter += 1
                refine_counter += 1
                label = f"Refine {refine_counter}"
                iteration = GuidedIterationArtifact(
                    index=iteration_counter,
                    kind="refine",
                    label=label,
                    pass_index=pass_index,
                    include_full_critiques=include_full_critiques,
                )
                for phase in self._phase_order(kind="refine"):
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
                GuidedPhase.GATHER,
                GuidedPhase.PROPOSE,
                GuidedPhase.GENERATE_PATCH,
                GuidedPhase.CRITIQUE,
            ]
        return [
            GuidedPhase.DIAGNOSE,
            GuidedPhase.PLANNING,
            GuidedPhase.GATHER,
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
        return prompting.render_prompt(
            templates=self.PROMPT_TEMPLATES,
            phase=phase,
            request=request,
            detect_error_line=error_processing.detect_error_line,
            constraints=PATCH_CONSTRAINTS_TEXT,
            example_diff=PATCH_EXAMPLE_DIFF,
            context_override=context_override,
            extra=extra,
        )

    @classmethod
    def _placeholder_texts(cls) -> set[str]:
        return prompting.placeholder_texts()

    def _strip_placeholder_sections(self, text: str) -> str:
        return prompting.strip_placeholder_sections(text)

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
            elif artifact.phase == GuidedPhase.GATHER:
                if continue_execution:
                    events.extend(self._execute_gather(artifact, iteration, iteration.index, request))
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

    def _execute_gather(
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
            message="Starting Gather phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)

        base_prompt = artifact.prompt
        response_text: str = ""
        parsed: Optional[Dict[str, Any]] = None
        last_error: Optional[str] = None
        attempts = 0
        for attempt in range(1, 4):
            attempts = attempt
            try:
                # Gather requires strict structured output; if the client/provider supports it,
                # request native JSON formatting at the API layer (e.g., Ollama "format": "json").
                try:
                    response = self._client.complete(
                        prompt=artifact.prompt,
                        temperature=self._config.temperature,
                        model=self._config.interpreter_model,
                        response_format="json",
                    )
                except TypeError:
                    response = self._client.complete(
                        prompt=artifact.prompt,
                        temperature=self._config.temperature,
                        model=self._config.interpreter_model,
                    )
            except Exception as exc:  # pragma: no cover - transport level failure
                artifact.status = PhaseStatus.FAILED
                artifact.completed_at = self._now()
                artifact.human_notes = f"Gather phase failed: {exc}"
                failure_event = self._event(
                    kind=StrategyEventKind.NOTE,
                    message="Gather phase failed",
                    phase=artifact.phase.value,
                    iteration=iteration_index,
                    data={"error": str(exc)},
                )
                self.emit(failure_event)
                events.append(failure_event)
                return events

            response_text = response.strip()
            try:
                parsed = gathering.parse_gather_response(
                    response_text,
                    allowed_categories=self.GATHER_ALLOWED_CATEGORIES,
                    allowed_target_kinds=self.GATHER_ALLOWED_TARGET_KINDS,
                )
                last_error = None
                break
            except ValueError as exc:
                parsed = None
                last_error = str(exc)
                # retry with a stronger constraint suffix
                artifact.prompt = (
                    base_prompt
                    + "\n\nIMPORTANT: Your previous response was invalid. Output ONLY the JSON object (no prose, no code fences), matching the schema exactly."
                )

        # restore original prompt so the trace remains stable
        artifact.prompt = base_prompt
        artifact.response = response_text
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["gather"] = {
            "attempts": attempts,
            "parseError": last_error,
        }

        if parsed is None:
            parsed = {"needs_more_context": False, "requests": []}
            artifact.human_notes = (
                "Gather stage did not return parseable JSON after 3 attempts; continuing without additional context."
            )

        planning_text = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
        enforced_reason: Optional[str]
        parsed, enforced_reason = gathering.enforce_gather_structural_requirements(
            gather_request=parsed,
            planning_text=planning_text,
            context_window=self._focused_context_window(request),
        )
        machine_checks["gather"]["enforced"] = enforced_reason is not None
        machine_checks["gather"]["enforcementReason"] = enforced_reason

        machine_checks["gather_request"] = parsed
        gathered_text, gathered_details = gathering.collect_gathered_context(
            request,
            parsed,
            detect_error_line=error_processing.detect_error_line,
        )
        machine_checks["gathered_context_text"] = gathered_text
        machine_checks["gathered_context"] = gathered_details
        self._record_iteration_telemetry(
            iteration,
            "gather",
            {
                "request": parsed,
                "collected": gathered_details,
            },
            append=True,
        )

        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Gather phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={
                "characters": len(artifact.response or ""),
                "gatheredCharacters": len(gathered_text or ""),
            },
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
        replacement_blocks = patching.parse_replacement_blocks(diff_text)
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
        pre_span, post_span = patching.diff_spans(
            diff_text,
            source_text=request.source_text,
            patch_applier=self._patch_applier,
        )
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
            artifact.human_notes = "Diff template invalid: no ORIGINAL/CHANGED blocks or @@ hunks were found."
            iteration.failure_reason = "empty-diff"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: malformed diff template",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"diff_excerpt": diff_text[:200]},
            )
            self.emit(failure_event)
            events.append(failure_event)
            outcome.patch_diagnostics = "Diff template missing ORIGINAL/CHANGED blocks"
            after_snippet = "Patched output unavailable because the diff template had no ORIGINAL/CHANGED blocks."
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

        patched_text, applied, patch_message, span_override = patching.apply_diff_text(
            request,
            diff_text,
            replacement_blocks,
            patch_applier=self._patch_applier,
            dmp=self._dmp,
            detect_error_line=error_processing.detect_error_line,
            context_radius=self.CONTEXT_RADIUS,
            suffix_collapse_max_lines=self.SUFFIX_COLLAPSE_MAX_LINES,
            suffix_collapse_similarity=self.SUFFIX_COLLAPSE_SIMILARITY,
        )
        if span_override:
            pre_span, post_span = span_override
            outcome.diff_span = pre_span
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
            compile_result = run_compile(request, patched_text)
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

        if getattr(iteration, "include_full_critiques", False):
            full_transcript = self._critique_history_text()
            if full_transcript:
                critique_feedback = full_transcript

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
            gathered_context = self._coerce_string(self._find_gathered_context(iteration))
            artifact.prompt = self._render_prompt(
                GuidedPhase.PROPOSE,
                request,
                context_override=context_override,
                extra={
                    "experiment_summary": experiment_result or self._experiment_summary_placeholder(),
                    "gathered_context": gathered_context or self._gathered_context_placeholder(),
                    "critique_feedback": phase_critique_feedback,
                    "history_context": phase_history_context,
                    "previous_diff": phase_previous_diff,
                    "prior_patch_summary": phase_prior_patch_summary,
                    "refinement_context": refinement_context_text,
                },
            )
        elif artifact.phase == GuidedPhase.GATHER:
            experiment_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            artifact.prompt = self._render_prompt(
                GuidedPhase.GATHER,
                request,
                context_override=context_override,
                extra={
                    "experiment_summary": experiment_result or self._experiment_summary_placeholder(),
                },
            )
        elif artifact.phase == GuidedPhase.GENERATE_PATCH:
            planning_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            active_hypothesis_text = planning_result or self._experiment_summary_placeholder()
            proposal_summary = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PROPOSE))
            gathered_context = self._coerce_string(self._find_gathered_context(iteration))
            artifact.prompt = self._render_prompt(
                GuidedPhase.GENERATE_PATCH,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": active_hypothesis_text,
                    "diagnosis_explanation": active_hypothesis_text,
                    "proposal": proposal_summary or self._proposal_placeholder(),
                    "gathered_context": gathered_context or self._gathered_context_placeholder(),
                    "previous_diff": phase_previous_diff,
                    "prior_patch_summary": phase_prior_patch_summary,
                    "refinement_context": refinement_context_text,
                },
            )

    def _format_prior_patch_summary(self, prior_outcome: IterationOutcome | None, *, max_chars: int = 4000) -> str:
        return prompting.format_prior_patch_summary(prior_outcome, max_chars=max_chars)

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

    def _find_phase_artifact(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[PhaseArtifact]:
        for artifact in iteration.phases:
            if artifact.phase == phase:
                return artifact
        return None

    def _find_gathered_context(self, iteration: GuidedIterationArtifact) -> Optional[str]:
        artifact = self._find_phase_artifact(iteration, GuidedPhase.GATHER)
        if not artifact or not isinstance(artifact.machine_checks, Mapping):
            return None
        gathered = artifact.machine_checks.get("gathered_context_text")
        return gathered if isinstance(gathered, str) else None

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
        evaluation.record_iteration_telemetry(iteration, key, payload, append=append)

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
        return evaluation.detect_stall(previous_outcome, current_outcome)

    def _stall_signature(self, outcome: IterationOutcome | None) -> Optional[Tuple[str, Optional[int], Tuple[int, int]]]:
        return evaluation.stall_signature(outcome)

    @staticmethod
    def _ensure_machine_checks_dict(artifact: PhaseArtifact) -> Dict[str, Any]:
        return evaluation.ensure_machine_checks_dict(artifact)


    @staticmethod
    def _error_fingerprint(text: Optional[str]) -> Optional[str]:
        return evaluation.error_fingerprint(text)

    @staticmethod
    def _diagnosis_placeholder() -> str:
        return prompting.diagnosis_placeholder()

    @staticmethod
    def _diagnosis_explanation_placeholder() -> str:
        return prompting.diagnosis_explanation_placeholder()

    @staticmethod
    def _diagnosis_output_placeholder() -> str:
        return prompting.diagnosis_output_placeholder()

    @staticmethod
    def _proposal_placeholder() -> str:
        return prompting.proposal_placeholder()

    @staticmethod
    def _experiment_summary_placeholder() -> str:
        return prompting.experiment_summary_placeholder()

    @staticmethod
    def _critique_output_placeholder() -> str:
        return prompting.critique_output_placeholder()

    @staticmethod
    def _patch_diagnostics_placeholder() -> str:
        return prompting.patch_diagnostics_placeholder()

    @staticmethod
    def _critique_placeholder() -> str:
        return prompting.critique_placeholder()

    @staticmethod
    def _previous_diff_placeholder() -> str:
        return prompting.previous_diff_placeholder()

    @staticmethod
    def _prior_patch_placeholder() -> str:
        return prompting.prior_patch_placeholder()

    @staticmethod
    def _gathered_context_placeholder() -> str:
        return prompting.gathered_context_placeholder()

    @staticmethod
    def _history_placeholder() -> str:
        return prompting.history_placeholder()

    @staticmethod
    def _refinement_context_placeholder() -> str:
        return prompting.refinement_context_placeholder()

    def _context_for_phase(self, phase: GuidedPhase, request: GuidedLoopInputs) -> str:
        return prompting.context_for_phase(
            phase,
            request,
            detect_error_line=error_processing.detect_error_line,
        )

    def _default_context_slice(self, request: GuidedLoopInputs, limit: int = 2000) -> str:
        return prompting.default_context_slice(request, limit=limit)

    def _focused_context_window(self, request: GuidedLoopInputs, radius: int = 5) -> str:
        return prompting.focused_context_window(
            request,
            detect_error_line=error_processing.detect_error_line,
            radius=radius,
        )

    @staticmethod
    def _format_numbered_block(lines: Sequence[str], starting_line: int) -> str:
        return prompting.format_numbered_block(lines, starting_line)

    def _critique_snippet(
        self,
        text: Optional[str],
        span: tuple[int, int] | None,
        *,
        radius: int = 5,
        fallback: str,
    ) -> str:
        return prompting.critique_snippet(text, span, radius=radius, fallback=fallback)

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
        return prompting.build_critique_prompt(
            applied=applied,
            history_context=history_context,
            error_text=error_text,
            active_hypothesis_text=active_hypothesis_text,
            before_snippet=before_snippet,
            after_snippet=after_snippet,
            diff_text=diff_text,
            validation_summary=validation_summary,
        )

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
        return error_processing.detect_error_line(error_text, filename)

    # ------------------------------------------------------------------
    # Compatibility shims for tests / migration-only refactor.
    def _parse_replacement_blocks(self, diff_text: str) -> List[tuple[List[str], List[str]]]:
        return patching.parse_replacement_blocks(diff_text)

    def _apply_three_way_blocks(
        self,
        request: GuidedLoopInputs,
        replacement_blocks: List[tuple[List[str], List[str]]],
    ) -> tuple[Optional[str], bool, str, tuple[tuple[int, int] | None, tuple[int, int] | None] | None]:
        return patching.apply_three_way_blocks(
            request,
            replacement_blocks,
            patch_applier=self._patch_applier,
            dmp=self._dmp,
            detect_error_line=error_processing.detect_error_line,
            context_radius=self.CONTEXT_RADIUS,
            suffix_collapse_max_lines=self.SUFFIX_COLLAPSE_MAX_LINES,
            suffix_collapse_similarity=self.SUFFIX_COLLAPSE_SIMILARITY,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _summarize_diff(diff_text: str) -> Dict[str, Any]:
        if "ORIGINAL LINES:" in diff_text and (
            "NEW LINES:" in diff_text or "CHANGED LINES:" in diff_text
        ):
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
        blocks = patching.parse_replacement_blocks(diff_text)
        hunks = len(blocks)
        added = sum(len(updated) for _, updated in blocks)
        removed = sum(len(original) for original, _ in blocks)
        return {
            "added_lines": added,
            "removed_lines": removed,
            "hunks": hunks,
            "delete_only": added == 0 and removed > 0,
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
