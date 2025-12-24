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
from . import history
from . import trace_planning
from . import iteration_utils
from . import critiques
from . import phase_runner
from . import gather_phase
from . import critique_phase
from . import phase_prompt_preparer
from . import post_iteration
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
    "for (int i = 0; i < 10; ++i) {\n"
    "    items.insert(item);\n"
    "}\n"
    "CHANGED LINES:\n"
    "for (int i = 0; i < 10; ++i) {\n"
    "    items.add(item);\n"
    "}\n"
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
        return history.initial_history(inputs)

    def _format_history(self, entries: Sequence[str], limit: int = 5) -> str:
        return history.format_history(entries, placeholder=self._history_placeholder(), limit=limit)

    def _history_entry(self, iteration_index: int, outcome: IterationOutcome) -> str:
        return history.history_entry(iteration_index, outcome)

    @staticmethod
    def _coerce_history_entries(source: Any) -> List[str]:
        return history.coerce_history_entries(source)

    def _plan_trace(self, request: GuidedLoopInputs) -> GuidedLoopTrace:
        return trace_planning.plan_trace(
            strategy_name=self.name,
            config=self._config,
            request=request,
            render_prompt=lambda phase, req: self._render_prompt(phase, req),
        )

    def _phase_order(self, *, kind: str = "primary") -> List[GuidedPhase]:
        return trace_planning.phase_order(kind=kind)

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
        spec = phase_runner.PhaseRunSpec(
            start_message="Starting Diagnose phase",
            completed_message="Diagnose phase completed",
            failed_message="Diagnose phase failed",
            empty_failed_message="Diagnose phase failed: empty response",
            exception_human_notes_prefix="Diagnose phase failed: ",
            empty_human_notes="Diagnose phase returned an empty response.",
            require_non_empty=True,
            machine_check_key="diagnosis_text",
        )
        events, response_text = phase_runner.run_phase(
            artifact=artifact,
            iteration=iteration,
            iteration_index=iteration_index,
            complete=lambda: self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            ),
            spec=spec,
            now=self._now,
            make_event=self._event,
            emit=self.emit,
            ensure_machine_checks=self._ensure_machine_checks_dict,
            on_response=lambda text: setattr(self, "_latest_diagnosis_output", text),
        )
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
        spec = phase_runner.PhaseRunSpec(
            start_message="Starting Planning phase",
            completed_message="Planning phase completed",
            failed_message="Planning phase failed",
            empty_failed_message="Planning phase failed: empty response",
            exception_human_notes_prefix="Planning phase failed: ",
            empty_human_notes="Planning phase returned an empty response.",
            require_non_empty=True,
            machine_check_key="planning_notes",
            set_iteration_failure_reason_on_empty="empty-response",
        )
        events, _ = phase_runner.run_phase(
            artifact=artifact,
            iteration=iteration,
            iteration_index=iteration_index,
            complete=lambda: self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            ),
            spec=spec,
            now=self._now,
            make_event=self._event,
            emit=self.emit,
            ensure_machine_checks=self._ensure_machine_checks_dict,
        )
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
        return gather_phase.execute_gather(
            artifact=artifact,
            iteration=iteration,
            iteration_index=iteration_index,
            request=request,
            complete=self._client.complete,
            temperature=self._config.temperature,
            model=self._config.interpreter_model,
            allowed_categories=sorted(self.GATHER_ALLOWED_CATEGORIES),
            allowed_target_kinds=sorted(self.GATHER_ALLOWED_TARGET_KINDS),
            focused_context_window=lambda: self._focused_context_window(request),
            find_phase_response=self._find_phase_response,
            coerce_string=self._coerce_string,
            record_iteration_telemetry=lambda iter_art, key, payload: self._record_iteration_telemetry(
                iter_art,
                key,
                payload,
                append=True,
            ),
            now=self._now,
            make_event=self._event,
            emit=self.emit,
            ensure_machine_checks=self._ensure_machine_checks_dict,
        )


    def _execute_propose(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        spec = phase_runner.PhaseRunSpec(
            start_message="Starting Propose phase",
            completed_message="Propose phase completed",
            failed_message="Propose phase failed",
            empty_failed_message="Propose phase failed: empty response",
            exception_human_notes_prefix="Propose phase failed: ",
            empty_human_notes="Proposal response was empty.",
            require_non_empty=True,
            machine_check_key="proposal",
        )
        events, _ = phase_runner.run_phase(
            artifact=artifact,
            iteration=iteration,
            iteration_index=iteration_index,
            complete=lambda: self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.patch_model,
            ),
            spec=spec,
            now=self._now,
            make_event=self._event,
            emit=self.emit,
            ensure_machine_checks=self._ensure_machine_checks_dict,
        )
        return events

    def _execute_generate_patch(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        spec = phase_runner.PhaseRunSpec(
            start_message="Starting Generate Patch phase",
            completed_message="Generate Patch phase completed",
            failed_message="Generate Patch phase failed",
            empty_failed_message="Generate Patch phase failed: empty response",
            exception_human_notes_prefix="Generate Patch phase failed: ",
            empty_human_notes="Generate Patch phase returned an empty response.",
            require_non_empty=False,
            machine_check_key=None,
        )
        events, response_text = phase_runner.run_phase(
            artifact=artifact,
            iteration=None,
            iteration_index=iteration_index,
            complete=lambda: self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.patch_model,
            ),
            spec=spec,
            now=self._now,
            make_event=self._event,
            emit=self.emit,
            ensure_machine_checks=self._ensure_machine_checks_dict,
        )
        if response_text:
            artifact.response = patching.strip_code_fences(response_text)
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
        return critique_phase.execute_critique(
            artifact=artifact,
            iteration=iteration,
            iteration_index=iteration_index,
            request=request,
            compile_check=self._config.compile_check,
            now=self._now,
            make_event=self._event,
            emit=self.emit,
            summarize_diff=self._summarize_diff,
            critique_snippet=lambda text, span, **kwargs: self._critique_snippet(text, span, **kwargs),
            focused_context_window=lambda req: self._focused_context_window(req),
            find_phase_response=self._find_phase_response,
            coerce_string=self._coerce_string,
            detect_error_line=self._detect_error_line,
            error_fingerprint=self._error_fingerprint,
            finalize_critique_response=self._finalize_critique_response,
            history_placeholder=self._history_placeholder,
            experiment_summary_placeholder=self._experiment_summary_placeholder,
            patch_applier=self._patch_applier,
            dmp=self._dmp,
            context_radius=self.CONTEXT_RADIUS,
            suffix_collapse_max_lines=self.SUFFIX_COLLAPSE_MAX_LINES,
            suffix_collapse_similarity=self.SUFFIX_COLLAPSE_SIMILARITY,
        )

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
        phase_prompt_preparer.prepare_phase_prompt(
            artifact=artifact,
            iteration=iteration,
            request=request,
            prior_outcome=prior_outcome,
            history_context=history_context,
            render_prompt=lambda phase, req, **kwargs: self._render_prompt(phase, req, **kwargs),
            focused_context_window=self._focused_context_window,
            format_prior_patch_summary=lambda outcome: self._format_prior_patch_summary(outcome),
            build_refinement_context=self._build_refinement_context,
            critique_history_text=lambda: self._critique_history_text(),
            find_phase_response=self._find_phase_response,
            find_gathered_context=self._find_gathered_context,
            coerce_string=self._coerce_string,
            latest_diagnosis_output=self._latest_diagnosis_output,
            critique_placeholder=self._critique_placeholder,
            previous_diff_placeholder=self._previous_diff_placeholder,
            experiment_summary_placeholder=self._experiment_summary_placeholder,
            diagnosis_output_placeholder=self._diagnosis_output_placeholder,
            critique_output_placeholder=self._critique_output_placeholder,
            proposal_placeholder=self._proposal_placeholder,
            gathered_context_placeholder=self._gathered_context_placeholder,
            history_placeholder=self._history_placeholder,
            refinement_context_placeholder=self._refinement_context_placeholder,
        )

    def _format_prior_patch_summary(self, prior_outcome: IterationOutcome | None, *, max_chars: int = 4000) -> str:
        return prompting.format_prior_patch_summary(prior_outcome, max_chars=max_chars)

    def _build_refinement_context(self, prior_outcome: IterationOutcome | None) -> str:
        return "Refinement iterations reuse the most recent Diagnose output; do not rerun Diagnose."

    def _critique_history_text(self, limit: Optional[int] = None) -> Optional[str]:
        return critiques.critique_history_text(self._critique_transcripts, limit=limit)

    def _find_phase_response(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[str]:
        return iteration_utils.find_phase_response(iteration, phase)

    def _find_phase_artifact(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[PhaseArtifact]:
        return iteration_utils.find_phase_artifact(iteration, phase)

    def _find_gathered_context(self, iteration: GuidedIterationArtifact) -> Optional[str]:
        return iteration_utils.find_gathered_context(iteration)

    @staticmethod
    def _coerce_string(value: Any) -> Optional[str]:
        return iteration_utils.coerce_string(value)

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
        critiques.record_critique_transcript(self._critique_transcripts, transcript)
    def _post_iteration_evaluation(
        self,
        iteration: GuidedIterationArtifact,
        outcome: IterationOutcome,
        previous_outcome: IterationOutcome | None,
    ) -> List[StrategyEvent]:
        return post_iteration.post_iteration_evaluation(
            iteration=iteration,
            outcome=outcome,
            previous_outcome=previous_outcome,
            detect_stall=self._detect_stall,
            record_iteration_telemetry=lambda iter_art, key, payload: self._record_iteration_telemetry(
                iter_art,
                key,
                payload,
                append=True,
            ),
            make_event=self._event,
            emit=self.emit,
        )

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
