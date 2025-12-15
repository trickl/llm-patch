"""Lifecycle checklist data for the guided loop strategy."""
from __future__ import annotations

import json
from textwrap import indent

GUIDED_LOOP_CHECKLIST = {
    "phases": [
        {
            "step": "diagnose",
            "description": "Map the structural failure to concrete constructs and enumerate competing hypotheses.",
            "rules": [
                "Produce at least two mutually exclusive hypotheses until one is accepted.",
                "Each hypothesis must describe its affected region, expected effect, and structural delta.",
                "Cover both grouping/precedence and token-absence failure modes whenever diagnosing a new issue.",
                "Select exactly one active hypothesis and justify why it best matches the compiler diagnostic.",
            ],
        },
        {
            "step": "propose",
            "description": "Describe the minimal structural adjustment that would satisfy the hypothesis.",
            "rules": [
                "Stay within the active hypothesis region and intent.",
                "Provide a 'structural_change' statement covering grouping, scope, ordering, or ownership.",
                "Write purely in English; no code or pseudo-code.",
            ],
        },
        {
            "step": "generate_patch",
            "description": "Emit a diff that touches only the mandated region and honors constraints.",
            "rules": [
                "Only modify files/lines promised by the hypothesis.",
                "Keep the diff minimal and avoid refactors outside the scope.",
            ],
        },
        {
            "step": "critique",
            "description": "Validate the diff by applying it, running tests, and capturing feedback for refinements.",
            "rules": [
                "Surface compile/test output verbatim when failures persist.",
                "Record any scope violations or application failures as blockers for the next loop.",
            ],
        },
    ],
    "hypothesis": [
        {
            "step": "lifecycle",
            "description": "Hypotheses are expired after two failed attempts or a stall detection.",
            "rules": [
                "Increment retry counts when a patch fails to apply or compile.",
                "Archive the hypothesis when diff + error signatures repeat (stall).",
            ],
        },
    ],
    "validation": [
        {
            "step": "error_fingerprint",
            "description": "Track previous vs current fingerprints to detect unchanged failures.",
            "rules": [
                "If the fingerprint matches, mark the hypothesis rejected and request a new one.",
            ],
        }
    ],
}

GUIDED_LOOP_CHECKLIST_JSON = json.dumps(GUIDED_LOOP_CHECKLIST, indent=2)


def checklist_text() -> str:
    """Return a bullet-list representation for human-readable prompts."""

    lines: list[str] = []
    for category, entries in GUIDED_LOOP_CHECKLIST.items():
        lines.append(f"{category.title()}:")
        for entry in entries:
            lines.append(f"- {entry['step']}: {entry['description']}")
            for rule in entry.get("rules", []):
                lines.append(f"  * {rule}")
    return "\n".join(lines)


GUIDED_LOOP_CHECKLIST_TEXT = checklist_text()