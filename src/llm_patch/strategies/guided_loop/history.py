"""Iteration history helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It centralizes:
- coercing history seed values into strings
- building the initial history log
- formatting history context for prompts
- formatting per-iteration history entries
"""

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Sequence

from .models import GuidedLoopInputs, IterationOutcome


def coerce_history_entries(source: Any) -> List[str]:
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


def initial_history(inputs: GuidedLoopInputs) -> List[str]:
    entries: List[str] = []
    entries.extend(coerce_history_entries(inputs.history_seed))
    additional: Mapping[str, Any] = inputs.additional_context or {}
    entries.extend(coerce_history_entries(additional.get("history_seed")))
    return entries


def format_history(
    entries: Sequence[str],
    *,
    placeholder: str,
    limit: int = 5,
) -> str:
    filtered = [entry for entry in entries if entry]
    if not filtered:
        return placeholder
    tail = filtered[-limit:]
    return "\n".join(f"- {entry}" for entry in tail)


def history_entry(iteration_index: int, outcome: IterationOutcome) -> str:
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
