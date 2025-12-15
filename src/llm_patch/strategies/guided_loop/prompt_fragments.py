"""Reusable prompt fragments for the guided loop strategy."""
from __future__ import annotations

from textwrap import dedent



def compose_prompt(*segments: str) -> str:
    """Join non-empty prompt segments with blank lines."""

    normalized: list[str] = []
    for segment in segments:
        if not segment:
            continue
        stripped = segment.strip()
        if stripped:
            normalized.append(stripped)
    return "\n\n".join(normalized)


DIAGNOSE_INSTRUCTIONS_FRAGMENT = dedent(
    """
    Given the compiler/test output and the focused code window, identify the precise construct causing the failure. Cite the
    relevant line numbers from the snippet and explain why the construct is invalid in {language}. Do not propose fixes or emit new code—focus solely on diagnosis.

    Enumerate at least three mutually exclusive hypotheses that could explain the observed failure. Treat the compiler message as potentially incomplete or misleading.
    For each hypothesis, respond in plain English (paragraphs or bullet points) and include:
      • A stable label such as "H1" / "H2".
      • A structural claim describing the suspected issue.
      • Evidence from the snippet or diagnostics supporting the claim.
      • The code region or construct affected if the hypothesis holds.

    After listing the hypotheses, clearly name the single active hypothesis you want to pursue next and justify why it best fits the evidence compared to the alternatives.
    Do not return JSON, code fences, or tables—use prose and simple bullet lists only.
    """
)

PROPOSE_INSTRUCTIONS_FRAGMENT = (
    "Propose the cleanest, simplest fix that might resolve the diagnosed issue, assuming the active hypothesis is correct and taking into account prior attempts and diagnoses."
    " Respond with a few sentences in plain English describing the intent and the structural change, where the change should be made and how the change should fix the issue; respond in plain English without code or pseudo-code, but" \
    " with enough detail that a competent engineer could implement the change precisely. Consider any effects on surrounding code and constraints from prior attempts."
)

GENERATE_PATCH_INSTRUCTIONS_FRAGMENT = dedent(
    """
    Produce the patch as plain text using the following template for each edit. Do not add code fences, commentary, or diagnostics outside
    the template, and keep every block as small as possible so fuzzy matching stays accurate.

    ORIGINAL LINES:
    <verbatim snippet exactly as it appears now>

    NEW LINES:
    <replacement snippet>

    If multiple replacements are required, repeat the template with a blank line between blocks. The applier will locate ORIGINAL LINES via
    diff-match-patch style search, so only include the lines that truly need to change.
    """
)

HISTORY_FRAGMENT = "Recent iteration history:\n{history_context}"
PRIOR_HYPOTHESIS_FRAGMENT = "Prior hypothesis (if any):\n{prior_hypothesis}"
PRIOR_PATCH_FRAGMENT = "Prior suggested patch (if any):\n{prior_patch_summary}"
CRITIQUE_FRAGMENT = "Prior critique insights (if any):\n{critique_feedback}"
ERROR_FRAGMENT = "Compiler error:\n{error}"
DIAGNOSIS_SUMMARY_FRAGMENT = "Diagnosis summary (structural only):\n{diagnosis}"
DIAGNOSIS_RATIONALE_FRAGMENT = "Diagnosis rationale (discard after this iteration):\n{diagnosis_explanation}"
PATCH_DIAGNOSTICS_FRAGMENT = "Latest patch diagnostics or replacement outcome:\n{patch_diagnostics}"
PREVIOUS_DIFF_FRAGMENT = "Most recent replacement attempt:\n{previous_diff}"
PROPOSAL_SUMMARY_FRAGMENT = "Proposal summary:\n{proposal}"
CONTEXT_FRAGMENT = "Context:\n{context}"

HYPOTHESIS_CONTEXT_FRAGMENT = (
    "Active hypothesis claim (must remain isolated):\n{hypothesis_claim}\n\n"
    "Affected region mandated by this hypothesis:\n{hypothesis_region}\n\n"
    "Expected observable effect if successful:\n{hypothesis_effect}\n\n"
    "Previously recorded structural change (if any):\n{hypothesis_structure}"
)

CONSTRAINTS_FRAGMENT = "Constraints:\n{constraints}"
EXAMPLE_REPLACEMENT_FRAGMENT = "Example replacement block:\n{example_diff}"

__all__ = [
    "DIAGNOSE_INSTRUCTIONS_FRAGMENT",
    "PROPOSE_INSTRUCTIONS_FRAGMENT",
    "GENERATE_PATCH_INSTRUCTIONS_FRAGMENT",
    "HISTORY_FRAGMENT",
    "PRIOR_HYPOTHESIS_FRAGMENT",
    "PRIOR_PATCH_FRAGMENT",
    "CRITIQUE_FRAGMENT",
    "ERROR_FRAGMENT",
    "DIAGNOSIS_SUMMARY_FRAGMENT",
    "DIAGNOSIS_RATIONALE_FRAGMENT",
    "PATCH_DIAGNOSTICS_FRAGMENT",
    "PREVIOUS_DIFF_FRAGMENT",
    "PROPOSAL_SUMMARY_FRAGMENT",
    "CONTEXT_FRAGMENT",
    "HYPOTHESIS_CONTEXT_FRAGMENT",
    "CONSTRAINTS_FRAGMENT",
    "EXAMPLE_REPLACEMENT_FRAGMENT",
    "compose_prompt",
]
