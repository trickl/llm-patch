"""Iteration accessors and coercion helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It centralizes:
- finding phase responses/artifacts
- extracting gathered context from the Gather phase artifact
- coercing arbitrary values to a trimmed string
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .phases import GuidedIterationArtifact, GuidedPhase, PhaseArtifact


def find_phase_response(iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[str]:
    for artifact in iteration.phases:
        if artifact.phase == phase and artifact.response:
            return artifact.response
    return None


def find_phase_artifact(iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[PhaseArtifact]:
    for artifact in iteration.phases:
        if artifact.phase == phase:
            return artifact
    return None


def find_gathered_context(iteration: GuidedIterationArtifact) -> Optional[str]:
    artifact = find_phase_artifact(iteration, GuidedPhase.GATHER)
    if not artifact or not isinstance(artifact.machine_checks, Mapping):
        return None
    gathered = artifact.machine_checks.get("gathered_context_text")
    return gathered if isinstance(gathered, str) else None


def coerce_string(value: Any) -> Optional[str]:
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
