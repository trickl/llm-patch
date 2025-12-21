"""Post-iteration evaluation helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It handles lightweight post-processing after an iteration produces an outcome:
- detect stalls (repeated diff span + repeated error signature)
- detect unchanged error fingerprints
- record iteration telemetry
- emit informational NOTE events
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..base import StrategyEvent, StrategyEventKind
from .models import IterationOutcome
from .phases import GuidedIterationArtifact


DetectStallFn = Callable[[IterationOutcome | None, IterationOutcome | None], Optional[Dict[str, Any]]]
RecordTelemetryFn = Callable[[GuidedIterationArtifact, str, Any], None]
MakeEventFn = Callable[..., StrategyEvent]
EmitFn = Callable[[StrategyEvent], None]


def post_iteration_evaluation(
    *,
    iteration: GuidedIterationArtifact,
    outcome: IterationOutcome,
    previous_outcome: IterationOutcome | None,
    detect_stall: DetectStallFn,
    record_iteration_telemetry: RecordTelemetryFn,
    make_event: MakeEventFn,
    emit: EmitFn,
) -> List[StrategyEvent]:
    events: List[StrategyEvent] = []
    if not outcome:
        return events

    stall_summary = detect_stall(previous_outcome, outcome)
    if stall_summary:
        iteration.failure_reason = "stall"
        record_iteration_telemetry(iteration, "stall", stall_summary)
        stall_event = make_event(
            kind=StrategyEventKind.NOTE,
            message="Stall detected: diff and error signature repeated",
            iteration=iteration.index,
            data=stall_summary,
        )
        emit(stall_event)
        events.append(stall_event)
        return events

    prev_fp = outcome.previous_error_fingerprint
    curr_fp = outcome.error_fingerprint
    if prev_fp is not None and curr_fp is not None and prev_fp == curr_fp:
        iteration.failure_reason = iteration.failure_reason or "unchanged-error"
        payload = {"previous": prev_fp, "current": curr_fp}
        record_iteration_telemetry(iteration, "unchangedError", payload)
        unchanged_event = make_event(
            kind=StrategyEventKind.NOTE,
            message="Error signature unchanged after patch",
            iteration=iteration.index,
            data=payload,
        )
        emit(unchanged_event)
        events.append(unchanged_event)
        return events

    return events
