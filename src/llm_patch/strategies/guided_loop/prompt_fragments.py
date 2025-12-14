"""Reusable prompt fragments for the guided loop strategy."""
from __future__ import annotations

from textwrap import dedent

from .checklist import GUIDED_LOOP_CHECKLIST_JSON


def _escape_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")


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


CHECKLIST_FRAGMENT = (
    "Guided loop lifecycle checklist (JSON — never violate these rules when responding):\n"
    f"{_escape_braces(GUIDED_LOOP_CHECKLIST_JSON)}"
)

STRUCTURAL_REASONING_FRAGMENT = (
    "Explain what the following compiler/test error means in {language} using structural language only."
    " Reference only scopes, ownership, ordering, or dependency relationships."
)

DIAGNOSE_INSTRUCTIONS_FRAGMENT = dedent(
    """
    Given the compiler output, prior interpretation, and the focused code window, identify the precise construct causing the
    failure. Cite the relevant line numbers from the snippet and explain why the construct is invalid in {language}. Do not
    propose fixes or emit new code; focus solely on diagnosis.

    Enumerate hypothesis *types*, not paraphrases. Always include at least one hypothesis that attributes the failure to
    incorrect expression grouping or operator precedence, and at least one that attributes it to missing or misplaced tokens
    (terminators, delimiters, keywords). After enumerating, explicitly choose exactly one active hypothesis and explain why
    the compiler diagnostic favors it over the alternatives.
    """
)

PROPOSE_INSTRUCTIONS_FRAGMENT = (
    "Propose the cleanest, simplest fix that resolves the diagnosed issue, taking into account prior attempts and diagnoses."
    " Respond with intent and structural justification only."
)

FALSIFY_INSTRUCTIONS_FRAGMENT = (
    "Before proposing code, stress-test the active hypothesis by attempting to falsify it."
    " List observable outcomes that would prove it wrong and mark whether each has already occurred."
)

GENERATE_PATCH_INSTRUCTIONS_FRAGMENT = (
    "Produce a unified diff implementing exactly the approved proposal while honoring every constraint."
)

HISTORY_FRAGMENT = "Recent iteration history:\n{history_context}"
CRITIQUE_FRAGMENT = "Prior critique insights (if any):\n{critique_feedback}"
ERROR_FRAGMENT = "Compiler error:\n{error}"
INTERPRETATION_SUMMARY_FRAGMENT = "Interpretation summary (structural only):\n{interpretation}"
INTERPRETATION_RATIONALE_FRAGMENT = "Interpretation rationale (discard after this iteration):\n{interpretation_explanation}"
DIAGNOSIS_SUMMARY_FRAGMENT = "Diagnosis summary (structural only):\n{diagnosis}"
DIAGNOSIS_RATIONALE_FRAGMENT = "Diagnosis rationale (discard after this iteration):\n{diagnosis_explanation}"
PATCH_DIAGNOSTICS_FRAGMENT = "Latest patch diagnostics or diff outcome:\n{patch_diagnostics}"
PREVIOUS_DIFF_FRAGMENT = "Most recent diff attempt:\n{previous_diff}"
PROPOSAL_SUMMARY_FRAGMENT = "Proposal summary:\n{proposal}"
CONTEXT_FRAGMENT = "Context:\n{context}"

HYPOTHESIS_CONTEXT_FRAGMENT = (
    "Active hypothesis claim (must remain isolated):\n{hypothesis_claim}\n\n"
    "Affected region mandated by this hypothesis:\n{hypothesis_region}\n\n"
    "Expected observable effect if successful:\n{hypothesis_effect}\n\n"
    "Previously recorded structural change (if any):\n{hypothesis_structure}"
)

CONSTRAINTS_FRAGMENT = "Constraints:\n{constraints}"
EXAMPLE_DIFF_FRAGMENT = "Example unified diff:\n{example_diff}"

INTERPRET_JSON_SCHEMA_FRAGMENT = dedent(
    """
    Return a JSON object with exactly two fields:
    - "interpretation": describe the structural element or relationship that is failing (no fixes, no narration).
    - "explanation": cite the evidence or reasoning that supports this interpretation.
    Interpretation must stay minimal—reference only observable structure or regions.
    """
)

DIAGNOSE_JSON_SCHEMA_FRAGMENT = dedent(
    """
    Respond using JSON with the following fields:
    - "interpretation" and "explanation" (as before).
    - "hypotheses": an array where each entry has:
        * "id": stable identifier (e.g., "H1").
        * "claim": structural statement of the hypothesis.
        * "kind": one of "grouping_precedence", "token_absence", or "other".
        * "affected_region": span or construct the hypothesis binds to.
        * "expected_effect": what will change observably if the hypothesis holds.
        * "structural_change" (if known).
        * "confidence" between 0 and 1.
        * short "explanation" referencing the snippet.
    - "selection": object with:
        * "hypothesis_id": the "id" of the chosen hypothesis (must match one entry above).
        * "rationale": why this hypothesis best fits the diagnostic compared to the others.
        * optional "binding_region" describing the expanded structural span the loop must respect.
    Output at least two mutually exclusive hypotheses when none have been accepted yet, covering both grouping/precedence
    and token-absence categories.
    """
)

PROPOSE_JSON_SCHEMA_FRAGMENT = dedent(
    """
    Respond with a JSON object containing two fields:
    - "intent": 1-2 sentences describing the change.
    - "structural_change": a short phrase describing the structural relationship being modified (grouping, nesting,
      ordering, scope, or ownership).
    Do not emit code, diffs, or pseudo-code.
    """
)

FALSIFY_JSON_SCHEMA_FRAGMENT = dedent(
    """
    Respond with JSON containing:
    - "hypothesis_id" (default to the active hypothesis if omitted)
    - "contradictions": an array where each item has "observation", "status" (observed|pending), and optional "evidence"
    - optional "summary" string describing remaining validation steps
    """
)

__all__ = [
    "CHECKLIST_FRAGMENT",
    "STRUCTURAL_REASONING_FRAGMENT",
    "DIAGNOSE_INSTRUCTIONS_FRAGMENT",
    "PROPOSE_INSTRUCTIONS_FRAGMENT",
    "FALSIFY_INSTRUCTIONS_FRAGMENT",
    "GENERATE_PATCH_INSTRUCTIONS_FRAGMENT",
    "HISTORY_FRAGMENT",
    "CRITIQUE_FRAGMENT",
    "ERROR_FRAGMENT",
    "INTERPRETATION_SUMMARY_FRAGMENT",
    "INTERPRETATION_RATIONALE_FRAGMENT",
    "DIAGNOSIS_SUMMARY_FRAGMENT",
    "DIAGNOSIS_RATIONALE_FRAGMENT",
    "PATCH_DIAGNOSTICS_FRAGMENT",
    "PREVIOUS_DIFF_FRAGMENT",
    "PROPOSAL_SUMMARY_FRAGMENT",
    "CONTEXT_FRAGMENT",
    "HYPOTHESIS_CONTEXT_FRAGMENT",
    "CONSTRAINTS_FRAGMENT",
    "EXAMPLE_DIFF_FRAGMENT",
    "INTERPRET_JSON_SCHEMA_FRAGMENT",
    "DIAGNOSE_JSON_SCHEMA_FRAGMENT",
    "PROPOSE_JSON_SCHEMA_FRAGMENT",
    "FALSIFY_JSON_SCHEMA_FRAGMENT",
    "compose_prompt",
]
