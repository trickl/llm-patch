"""Iteration evaluation + telemetry helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It centralizes:
- compile error fingerprinting
- stall detection (repeated diff span + repeated normalized error signature)
- iteration telemetry recording
- PhaseArtifact machine_checks materialization
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Optional, Tuple

from .models import IterationOutcome
from .phases import GuidedIterationArtifact, PhaseArtifact


def ensure_machine_checks_dict(artifact: PhaseArtifact) -> Dict[str, Any]:
    if isinstance(artifact.machine_checks, dict):
        return artifact.machine_checks
    materialized = dict(artifact.machine_checks or {})
    artifact.machine_checks = materialized
    return materialized


def record_iteration_telemetry(
    iteration: GuidedIterationArtifact | None,
    key: str,
    payload: Any,
    *,
    append: bool = False,
) -> None:
    if not iteration:
        return
    if iteration.telemetry is None:
        iteration.telemetry = {}
    if append:
        bucket = iteration.telemetry.setdefault(key, [])
        bucket.append(payload)
    else:
        iteration.telemetry[key] = payload


def error_fingerprint(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def stall_signature(outcome: IterationOutcome | None) -> Optional[Tuple[str, Optional[int], Tuple[int, int]]]:
    if not outcome or not outcome.patch_applied:
        return None
    if outcome.compile_returncode in (None, 0):
        return None
    if not outcome.diff_span:
        return None
    message = outcome.error_message or outcome.compile_stderr or outcome.compile_stdout or outcome.error_fingerprint
    if not message:
        return None
    normalized_message = re.sub(r"\s+", " ", message.strip())
    if not normalized_message:
        return None
    return normalized_message, outcome.error_location, outcome.diff_span


def detect_stall(
    previous_outcome: IterationOutcome | None,
    current_outcome: IterationOutcome | None,
) -> Optional[Dict[str, Any]]:
    prev_signature = stall_signature(previous_outcome)
    curr_signature = stall_signature(current_outcome)
    if not prev_signature or not curr_signature:
        return None
    if prev_signature != curr_signature:
        return None
    message, location, diff_span = curr_signature
    return {
        "errorMessage": message,
        "errorLocation": location,
        "diffSpan": list(diff_span),
    }
