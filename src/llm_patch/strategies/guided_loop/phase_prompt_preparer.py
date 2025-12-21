"""Phase prompt preparation helper.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

The controller remains responsible for owning state (e.g. latest diagnosis
output) and providing prompt rendering utilities. This module centralizes the
conditional logic that wires phase-specific prompt variables.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from .phases import GuidedIterationArtifact, GuidedPhase, PhaseArtifact
from .models import GuidedLoopInputs, IterationOutcome


RenderPromptFn = Callable[..., str]
FocusedContextWindowFn = Callable[[GuidedLoopInputs], str]
FormatPriorPatchSummaryFn = Callable[[IterationOutcome | None], str]
BuildRefinementContextFn = Callable[[IterationOutcome | None], str]
CritiqueHistoryTextFn = Callable[[], Optional[str]]
FindPhaseResponseFn = Callable[[GuidedIterationArtifact, GuidedPhase], Optional[str]]
FindGatheredContextFn = Callable[[GuidedIterationArtifact], Optional[str]]
CoerceStringFn = Callable[[Any], Optional[str]]


def prepare_phase_prompt(
    *,
    artifact: PhaseArtifact,
    iteration: GuidedIterationArtifact,
    request: GuidedLoopInputs,
    prior_outcome: IterationOutcome | None,
    history_context: str,
    render_prompt: RenderPromptFn,
    focused_context_window: FocusedContextWindowFn,
    format_prior_patch_summary: FormatPriorPatchSummaryFn,
    build_refinement_context: BuildRefinementContextFn,
    critique_history_text: CritiqueHistoryTextFn,
    find_phase_response: FindPhaseResponseFn,
    find_gathered_context: FindGatheredContextFn,
    coerce_string: CoerceStringFn,
    latest_diagnosis_output: str | None,
    critique_placeholder: Callable[[], str],
    previous_diff_placeholder: Callable[[], str],
    experiment_summary_placeholder: Callable[[], str],
    diagnosis_output_placeholder: Callable[[], str],
    critique_output_placeholder: Callable[[], str],
    proposal_placeholder: Callable[[], str],
    gathered_context_placeholder: Callable[[], str],
    history_placeholder: Callable[[], str],
    refinement_context_placeholder: Callable[[], str],
) -> None:
    critique_feedback = prior_outcome.critique_feedback if prior_outcome else critique_placeholder()
    previous_diff = prior_outcome.diff_text if (prior_outcome and prior_outcome.diff_text) else previous_diff_placeholder()
    context_override = focused_context_window(request)
    prior_patch_summary = format_prior_patch_summary(prior_outcome)

    is_refine_iteration = iteration.kind == "refine"
    refinement_context_text = refinement_context_placeholder()
    if is_refine_iteration:
        refinement_context_text = build_refinement_context(prior_outcome)

    if getattr(iteration, "include_full_critiques", False):
        full_transcript = critique_history_text()
        if full_transcript:
            critique_feedback = full_transcript

    phase_history_context = history_context
    phase_previous_diff = previous_diff
    phase_critique_feedback = critique_feedback
    phase_prior_patch_summary = prior_patch_summary

    if artifact.phase == GuidedPhase.DIAGNOSE:
        artifact.prompt = render_prompt(
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
        return

    if artifact.phase == GuidedPhase.PLANNING:
        diagnosis_output = find_phase_response(iteration, GuidedPhase.DIAGNOSE)
        if not diagnosis_output:
            diagnosis_output = latest_diagnosis_output
        critique_transcript = critique_history_text()
        artifact.prompt = render_prompt(
            GuidedPhase.PLANNING,
            request,
            context_override=context_override,
            extra={
                "diagnosis_output": (diagnosis_output or diagnosis_output_placeholder()),
                "critique_output": (critique_transcript or critique_output_placeholder()),
            },
        )
        return

    if artifact.phase == GuidedPhase.PROPOSE:
        experiment_result = coerce_string(find_phase_response(iteration, GuidedPhase.PLANNING))
        gathered_context = coerce_string(find_gathered_context(iteration))
        artifact.prompt = render_prompt(
            GuidedPhase.PROPOSE,
            request,
            context_override=context_override,
            extra={
                "experiment_summary": experiment_result or experiment_summary_placeholder(),
                "gathered_context": gathered_context or gathered_context_placeholder(),
                "critique_feedback": phase_critique_feedback,
                "history_context": phase_history_context,
                "previous_diff": phase_previous_diff,
                "prior_patch_summary": phase_prior_patch_summary,
                "refinement_context": refinement_context_text,
            },
        )
        return

    if artifact.phase == GuidedPhase.GATHER:
        experiment_result = coerce_string(find_phase_response(iteration, GuidedPhase.PLANNING))
        artifact.prompt = render_prompt(
            GuidedPhase.GATHER,
            request,
            context_override=context_override,
            extra={
                "experiment_summary": experiment_result or experiment_summary_placeholder(),
            },
        )
        return

    if artifact.phase == GuidedPhase.GENERATE_PATCH:
        planning_result = coerce_string(find_phase_response(iteration, GuidedPhase.PLANNING))
        active_hypothesis_text = planning_result or experiment_summary_placeholder()
        proposal_summary = coerce_string(find_phase_response(iteration, GuidedPhase.PROPOSE))
        gathered_context = coerce_string(find_gathered_context(iteration))
        artifact.prompt = render_prompt(
            GuidedPhase.GENERATE_PATCH,
            request,
            context_override=context_override,
            extra={
                "diagnosis": active_hypothesis_text,
                "diagnosis_explanation": active_hypothesis_text,
                "proposal": proposal_summary or proposal_placeholder(),
                "gathered_context": gathered_context or gathered_context_placeholder(),
                "previous_diff": phase_previous_diff,
                "prior_patch_summary": phase_prior_patch_summary,
                "refinement_context": refinement_context_text,
            },
        )
        return
