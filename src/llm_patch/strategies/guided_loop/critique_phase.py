"""Critique phase executor.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

Critique is the most specialized phase:
- validates the diff template / replacement blocks
- applies the patch (with guided-loop patch application fallbacks)
- optionally runs compile/test and fingerprints failures
- asks a critique model to review the patch + validation summary

The controller remains responsible for prompt rendering details and critique
model invocation; those are injected as callbacks.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from ..base import StrategyEvent, StrategyEventKind
from .compilation import run_compile
from . import patching
from .phases import GuidedIterationArtifact, GuidedPhase, PhaseArtifact, PhaseStatus
from .models import IterationOutcome


NowFn = Callable[[], str]
EmitFn = Callable[[StrategyEvent], None]
MakeEventFn = Callable[..., StrategyEvent]
SummarizeDiffFn = Callable[[str], Dict[str, Any]]
CritiqueSnippetFn = Callable[[Optional[str], Tuple[int, int] | None, Any], str]
FocusedContextWindowFn = Callable[[Any], str]
FindPhaseResponseFn = Callable[[GuidedIterationArtifact, GuidedPhase], Optional[str]]
CoerceStringFn = Callable[[Any], Optional[str]]
DetectErrorLineFn = Callable[[str, str], Optional[int]]
ErrorFingerprintFn = Callable[[Optional[str]], Optional[str]]

FinalizeCritiqueResponseFn = Callable[
    [
        PhaseArtifact,
        int,
        List[StrategyEvent],
    ],
    None,
]


def execute_critique(
    *,
    artifact: PhaseArtifact,
    iteration: GuidedIterationArtifact,
    iteration_index: int,
    request: Any,
    compile_check: bool,
    now: NowFn,
    make_event: MakeEventFn,
    emit: EmitFn,
    summarize_diff: SummarizeDiffFn,
    critique_snippet: CritiqueSnippetFn,
    focused_context_window: FocusedContextWindowFn,
    find_phase_response: FindPhaseResponseFn,
    coerce_string: CoerceStringFn,
    detect_error_line: DetectErrorLineFn,
    error_fingerprint: ErrorFingerprintFn,
    finalize_critique_response: Callable[..., None],
    history_placeholder: Callable[[], str],
    experiment_summary_placeholder: Callable[[], str],
    config_compile_command: Optional[List[str]] = None,
    patch_applier: Any = None,
    dmp: Any = None,
    context_radius: int = 5,
    suffix_collapse_max_lines: int = 8,
    suffix_collapse_similarity: float = 0.97,
) -> tuple[List[StrategyEvent], IterationOutcome | None]:
    """Run the Critique phase.

    `request` is intentionally typed as Any here to avoid circular imports; it
    must provide the attributes used (source_text, source_path, language,
    compile_command, etc.).

    `finalize_critique_response` is a controller callback that is responsible for
    building the critique prompt, invoking the critique model, and recording the
    critique transcript.
    """

    events: List[StrategyEvent] = []
    artifact.status = PhaseStatus.RUNNING
    artifact.started_at = now()
    start_event = make_event(
        kind=StrategyEventKind.PHASE_TRANSITION,
        message="Starting Critique checks",
        phase=artifact.phase.value,
        iteration=iteration_index,
    )
    emit(start_event)
    events.append(start_event)

    diff_text = find_phase_response(iteration, GuidedPhase.GENERATE_PATCH)
    if not diff_text:
        artifact.status = PhaseStatus.FAILED
        artifact.completed_at = now()
        artifact.human_notes = "Generate Patch did not produce a diff to critique."
        failure_event = make_event(
            kind=StrategyEventKind.NOTE,
            message="Critique skipped: missing diff",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        iteration.failure_reason = "missing-diff"
        emit(failure_event)
        events.append(failure_event)
        return events, IterationOutcome(
            diff_text=None,
            patch_applied=False,
            patch_diagnostics="No diff available",
            critique_feedback=artifact.response or artifact.human_notes,
        )

    diff_stats = summarize_diff(diff_text)
    replacement_blocks = patching.parse_replacement_blocks(diff_text)
    artifact.machine_checks = {
        "diffStats": diff_stats,
    }
    artifact.metrics = {
        "diff_added": float(diff_stats["added_lines"]),
        "diff_removed": float(diff_stats["removed_lines"]),
        "diff_hunks": float(diff_stats["hunks"]),
    }

    experiment_summary = coerce_string(find_phase_response(iteration, GuidedPhase.PLANNING))
    active_hypothesis_text = experiment_summary or experiment_summary_placeholder()
    error_text = getattr(request, "error_text", None) or "(error unavailable)"
    history_context = iteration.history_context or history_placeholder()

    pre_span, post_span = patching.diff_spans(
        diff_text,
        source_text=request.source_text,
        patch_applier=patch_applier,
    )
    before_snippet = critique_snippet(
        request.source_text,
        pre_span,
        fallback=focused_context_window(request),
    )

    outcome = IterationOutcome(diff_text=diff_text, critique_feedback=artifact.response)
    outcome.diff_span = pre_span

    if diff_stats["hunks"] == 0:
        artifact.status = PhaseStatus.FAILED
        artifact.completed_at = now()
        artifact.human_notes = "Diff template invalid: no ORIGINAL/CHANGED blocks or @@ hunks were found."
        iteration.failure_reason = "empty-diff"
        failure_event = make_event(
            kind=StrategyEventKind.NOTE,
            message="Critique failed: malformed diff template",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"diff_excerpt": diff_text[:200]},
        )
        emit(failure_event)
        events.append(failure_event)
        outcome.patch_diagnostics = "Diff template missing ORIGINAL/CHANGED blocks"
        after_snippet = "Patched output unavailable because the diff template had no ORIGINAL/CHANGED blocks."
        finalize_critique_response(
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
        patch_applier=patch_applier,
        dmp=dmp,
        detect_error_line=detect_error_line,
        context_radius=context_radius,
        suffix_collapse_max_lines=suffix_collapse_max_lines,
        suffix_collapse_similarity=suffix_collapse_similarity,
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
        artifact.completed_at = now()
        artifact.human_notes = "Patch application failed; queue another guided loop iteration to retry."
        iteration.failure_reason = "patch-apply"
        failure_event = make_event(
            kind=StrategyEventKind.NOTE,
            message="Critique failed: patch application",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"diagnostics": patch_message},
        )
        emit(failure_event)
        events.append(failure_event)
        after_snippet = "Patched output unavailable because the diff could not be applied."
        finalize_critique_response(
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
    compile_command = getattr(request, "compile_command", None) or config_compile_command
    if compile_check and compile_command:
        compile_result = run_compile(request, patched_text)
        artifact.machine_checks["compile"] = dict(compile_result)
        outcome.compile_returncode = compile_result.get("returncode")
        outcome.compile_stdout = compile_result.get("stdout")
        outcome.compile_stderr = compile_result.get("stderr")

        compile_event = make_event(
            kind=StrategyEventKind.NOTE,
            message="Compile command completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={
                "command": compile_result.get("command"),
                "returncode": compile_result.get("returncode"),
            },
        )
        emit(compile_event)
        events.append(compile_event)

        fingerprint_source: Optional[str]
        if compile_result.get("returncode") == 0:
            fingerprint_source = None
        else:
            fingerprint_source = compile_result.get("stderr") or compile_result.get("stdout")
            error_message = (fingerprint_source or "").strip()
            outcome.error_message = error_message or None
            if error_message:
                outcome.error_location = detect_error_line(error_message, request.source_path.name)

        outcome.error_fingerprint = error_fingerprint(fingerprint_source)
        if compile_result.get("returncode") != 0:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = now()
            artifact.human_notes = (
                "Compile/Test command failed; provide diagnostics to the next guided loop iteration."
            )
            iteration.failure_reason = f"compile-{compile_result.get('returncode')}"
            failure_event = make_event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: compile",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={
                    "returncode": compile_result.get("returncode"),
                    "stderr": compile_result.get("stderr", "")[:500],
                },
            )
            emit(failure_event)
            events.append(failure_event)

            after_snippet = critique_snippet(
                patched_text,
                post_span,
                fallback="Patched output unavailable.",
            )
            finalize_critique_response(
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
    artifact.completed_at = now()
    after_snippet = critique_snippet(
        patched_text,
        post_span,
        fallback="Patched output unavailable.",
    )
    finalize_critique_response(
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
        not compile_check or not compile_command or outcome.compile_success
    )
    completion_event = make_event(
        kind=StrategyEventKind.PHASE_TRANSITION,
        message="Critique checks completed",
        phase=artifact.phase.value,
        iteration=iteration_index,
        data={
            "patch_applied": outcome.patch_applied,
            "compile_success": outcome.compile_success,
        },
    )
    emit(completion_event)
    events.append(completion_event)

    if not outcome.critique_feedback:
        outcome.critique_feedback = artifact.response or artifact.human_notes

    return events, outcome
