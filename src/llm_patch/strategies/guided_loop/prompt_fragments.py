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

    The diagnosis must not imply a specific edit (for example: "add", "remove", or "move" code). Describe observations and structural defects only.

    If a compiler message mentions a token, do not interpret the token literally unless you can name the concrete grammar rule being violated. When you believe the message is referencing a strict grammar construct, state the exact construct and why the compiler would flag the error at that reported location, even if you suspect the root cause lives earlier in the file.

    Enumerate at least three mutually exclusive hypotheses that could explain the observed failure. Treat the compiler message as potentially incomplete or misleading.
    For each hypothesis, respond in plain English (paragraphs or bullet points) and include:
        • A stable label such as "H1" / "H2".
        • A structural claim describing the suspected issue.
        • Evidence from the snippet or diagnostics supporting the claim.
        • The code region or construct affected if the hypothesis holds.
        * Do not write any code or diffs.
        * Do not propose any possible fix or solution in words or pseudo-code.
        * Do not propose any actions or structural changes, such as "add", "remove", or "move" code.
        * Only describe a root cause that may manifest the observed failure.

    Do not return JSON, code fences, or tables—use prose and simple bullet lists only.
    """
)

PROPOSE_INSTRUCTIONS_FRAGMENT = (
    "Propose the cleanest, simplest fix that might resolve the diagnosed issue, incorporating lessons from prior attempts and critiques."
    " Respond with a few sentences in plain English describing the intent and the structural change, where the change should be made, and how the change should fix the issue; respond in plain English without code or pseudo-code, but"
    " with enough detail that a competent engineer could implement the change precisely. Consider any effects on surrounding code and constraints from prior attempts."
)

EXPERIMENT_SUMMARY_FRAGMENT = "Latest experiment notes:\n{experiment_summary}"
CRITIQUE_OUTPUT_FRAGMENT = "Recent critique transcript:\n{critique_output}"

EXPERIMENT_INSTRUCTIONS_FRAGMENT = dedent(
    """
    You are at the experiment-planning stage. Use the most recent Diagnose narrative, critique feedback, and history log to outline the next concrete experiment.

    Rules:
        • Focus on the freshest evidence from Diagnose; do not invent new structured fields or catalogs.
        • Reference the critique feedback or iteration history when explaining why this experiment might succeed.
        * Do not repeat any experiments that have already been attempted in prior iterations.
        • If there is insufficient information to proceed, explicitly request a new Diagnose phase rather than guessing.
        * Do not propose code changes or patches at this stage—focus solely on which hypothesis to test next.
        * Do not write any code or diffs.
        * Do not propose any possible fix or solution in words or pseudo-code.
        * Do not propose any actions or structural changes, such as "add", "remove", or "move" code.
        * Only propose which hypothesis to test next based on existing diagnoses.


    Respond in prose (no tables or JSON) and include these elements:
        • The active hypothesis to test, citing its stable label from Diagnose along with it's complete description.
    """
)

DIAGNOSIS_OUTPUT_FRAGMENT = "{diagnosis_output}"

REFINEMENT_CONTEXT_FRAGMENT = "Refinement guidance:\n{refinement_context}"

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
PRIOR_PATCH_FRAGMENT = "Prior suggested patch (if any):\n{prior_patch_summary}"
CRITIQUE_FRAGMENT = "Prior critique insights (if any):\n{critique_feedback}"
ERROR_FRAGMENT = "Compiler error:\n{error}"
DIAGNOSIS_SUMMARY_FRAGMENT = "Diagnosis summary (structural only):\n{diagnosis}"
DIAGNOSIS_RATIONALE_FRAGMENT = "Diagnosis rationale (discard after this iteration):\n{diagnosis_explanation}"
PATCH_DIAGNOSTICS_FRAGMENT = "Latest patch diagnostics or replacement outcome:\n{patch_diagnostics}"
PREVIOUS_DIFF_FRAGMENT = "Most recent replacement attempt:\n{previous_diff}"
PROPOSAL_SUMMARY_FRAGMENT = "Proposal summary:\n{proposal}"
CONTEXT_FRAGMENT = "Context:\n{context}"

CONSTRAINTS_FRAGMENT = "Constraints:\n{constraints}"
EXAMPLE_REPLACEMENT_FRAGMENT = "Example replacement block:\n{example_diff}"

__all__ = [
    "DIAGNOSE_INSTRUCTIONS_FRAGMENT",
    "PROPOSE_INSTRUCTIONS_FRAGMENT",
    "EXPERIMENT_SUMMARY_FRAGMENT",
    "CRITIQUE_OUTPUT_FRAGMENT",
    "EXPERIMENT_INSTRUCTIONS_FRAGMENT",
    "DIAGNOSIS_OUTPUT_FRAGMENT",
    "REFINEMENT_CONTEXT_FRAGMENT",
    "GENERATE_PATCH_INSTRUCTIONS_FRAGMENT",
    "HISTORY_FRAGMENT",
    "PRIOR_PATCH_FRAGMENT",
    "CRITIQUE_FRAGMENT",
    "ERROR_FRAGMENT",
    "DIAGNOSIS_SUMMARY_FRAGMENT",
    "DIAGNOSIS_RATIONALE_FRAGMENT",
    "PATCH_DIAGNOSTICS_FRAGMENT",
    "PREVIOUS_DIFF_FRAGMENT",
    "PROPOSAL_SUMMARY_FRAGMENT",
    "CONTEXT_FRAGMENT",
    "CONSTRAINTS_FRAGMENT",
    "EXAMPLE_REPLACEMENT_FRAGMENT",
    "compose_prompt",
]
