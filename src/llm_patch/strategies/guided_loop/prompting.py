"""Prompt assembly helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It centralizes:
- prompt rendering + placeholder stripping
- placeholder text defaults
- context window selection / formatting helpers
- critique prompt assembly
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from .models import GuidedLoopInputs, IterationOutcome
from .phases import GuidedPhase


def diagnosis_placeholder() -> str:
    return "Diagnosis not available yet; run the Diagnose phase first."


def diagnosis_explanation_placeholder() -> str:
    return "Diagnosis rationale not available yet; run the Diagnose phase first."


def diagnosis_output_placeholder() -> str:
    return "Diagnose phase output unavailable yet."


def proposal_placeholder() -> str:
    return "Proposal not available yet; run the Propose phase first."


def experiment_summary_placeholder() -> str:
    return "Experiment phase output unavailable yet."


def critique_output_placeholder() -> str:
    return "No critique transcripts are available yet."


def patch_diagnostics_placeholder() -> str:
    return "No patch diagnostics available yet."


def critique_placeholder() -> str:
    return "No prior critique feedback yet; this is the initial attempt."


def previous_diff_placeholder() -> str:
    return "No previous replacement attempt has been recorded."


def prior_patch_placeholder() -> str:
    return "No prior suggested patch is available yet."


def gathered_context_placeholder() -> str:
    return "No additional context gathered."


def history_placeholder() -> str:
    return "No prior iterations have run yet."


def refinement_context_placeholder() -> str:
    return "No refinement guidance for this iteration."


def placeholder_texts() -> set[str]:
    return {
        history_placeholder(),
        critique_placeholder(),
        previous_diff_placeholder(),
        diagnosis_placeholder(),
        diagnosis_explanation_placeholder(),
        proposal_placeholder(),
        patch_diagnostics_placeholder(),
        prior_patch_placeholder(),
        refinement_context_placeholder(),
        diagnosis_output_placeholder(),
        experiment_summary_placeholder(),
        critique_output_placeholder(),
        gathered_context_placeholder(),
    }


def strip_placeholder_sections(text: str) -> str:
    placeholders = placeholder_texts()
    lines = text.splitlines()
    cleaned: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.rstrip().endswith(":") and i + 1 < len(lines):
            placeholder_candidate = lines[i + 1].strip()
            if placeholder_candidate in placeholders:
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


def context_for_phase(
    phase: GuidedPhase,
    request: GuidedLoopInputs,
    *,
    detect_error_line,
) -> str:
    if phase in (GuidedPhase.DIAGNOSE, GuidedPhase.PROPOSE, GuidedPhase.GENERATE_PATCH):
        return focused_context_window(request, detect_error_line=detect_error_line)
    return default_context_slice(request)


def default_context_slice(request: GuidedLoopInputs, limit: int = 2000) -> str:
    source = (request.source_text or "").strip()
    if not source:
        return "Source unavailable."
    if len(source) <= limit:
        return source
    return source[:limit].rstrip() + "\n…"


def focused_context_window(
    request: GuidedLoopInputs,
    *,
    detect_error_line,
    radius: int = 5,
) -> str:
    source = request.source_text
    if not source:
        return "Source unavailable."
    lines = source.splitlines()
    if not lines:
        return "Source unavailable."
    filename = request.source_path.name if request.source_path else ""
    error_line = detect_error_line(request.error_text or "", filename)
    if error_line is None:
        start = 1
        end = min(len(lines), start + (radius * 2))
    else:
        center = max(1, min(error_line, len(lines)))
        start = max(1, center - radius)
        end = min(len(lines), center + radius)
    snippet = lines[start - 1 : end]
    return format_numbered_block(snippet, start)


def format_numbered_block(lines: Sequence[str], starting_line: int) -> str:
    formatted: List[str] = []
    line_no = starting_line
    for line in lines:
        formatted.append(f"{line_no:>4} | {line}")
        line_no += 1
    return "\n".join(formatted) if formatted else "Source unavailable."


def critique_snippet(
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
    return format_numbered_block(excerpt, start)


def build_critique_prompt(
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
        "Start with a header stating the hypothesis label identifier and descriptive title. Take care to state the current, latest hypothesis identifier and title and not that from prior iterations.\n"
        "Then address each item in order:\n"
        "1) Outcome summary — Did the patch resolve the issue? Mention compile/test status.\n"
        "2) Could the patch be applied? — If not, explain why.\n"
        "3) In one word was the outcome successful? If not, declare the hypothesis to be 'REJECTED' ."
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


def format_prior_patch_summary(
    prior_outcome: IterationOutcome | None,
    *,
    max_chars: int = 4000,
) -> str:
    placeholder = prior_patch_placeholder()
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


def render_prompt(
    *,
    templates: Mapping[GuidedPhase, str],
    phase: GuidedPhase,
    request: GuidedLoopInputs,
    detect_error_line,
    constraints: str,
    example_diff: str,
    context_override: Optional[str] = None,
    extra: Optional[Mapping[str, str]] = None,
) -> str:
    template = templates[phase]
    filename = request.source_path.name if request.source_path else ""
    context = context_override if context_override is not None else context_for_phase(
        phase,
        request,
        detect_error_line=detect_error_line,
    )
    data: Dict[str, str] = {
        "language": request.language or "",
        "error": request.error_text or "(error unavailable)",
        "context": context,
        "filename": filename,
        "diagnosis": diagnosis_placeholder(),
        "diagnosis_explanation": diagnosis_explanation_placeholder(),
        "proposal": proposal_placeholder(),
        "constraints": constraints,
        "example_diff": example_diff,
        "critique_feedback": critique_placeholder(),
        "previous_diff": previous_diff_placeholder(),
        "patch_diagnostics": "",
        "history_context": history_placeholder(),
        "prior_patch_summary": prior_patch_placeholder(),
        "refinement_context": refinement_context_placeholder(),
        "diagnosis_output": diagnosis_output_placeholder(),
        "experiment_summary": experiment_summary_placeholder(),
        "critique_output": critique_output_placeholder(),
        "gathered_context": gathered_context_placeholder(),
    }
    if extra:
        data.update({key: value for key, value in extra.items() if value is not None})
    populated = template.format(**data)
    return strip_placeholder_sections(populated)
