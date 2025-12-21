"""Shared helpers for running LLM-backed phases.

This module is intentionally "migration-only": it contains logic that was
previously embedded (and duplicated) in `controller.py`.

It provides a small runner for the common pattern:
- mark phase RUNNING, emit a start event
- call an LLM completion function
- handle transport exceptions
- store/validate response
- optionally record a machine-check value
- mark phase COMPLETED, emit a completion event

Gather and Critique remain specialized and are handled elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..base import StrategyEvent, StrategyEventKind
from .phases import GuidedIterationArtifact, PhaseArtifact, PhaseStatus


@dataclass(frozen=True, slots=True)
class PhaseRunSpec:
    start_message: str
    completed_message: str
    failed_message: str
    empty_failed_message: str
    exception_human_notes_prefix: str
    empty_human_notes: str
    require_non_empty: bool = True
    machine_check_key: str | None = None
    set_iteration_failure_reason_on_empty: str | None = None


CompleteFn = Callable[[], str]
NowFn = Callable[[], str]
EmitFn = Callable[[StrategyEvent], None]
MakeEventFn = Callable[..., StrategyEvent]
EnsureMachineChecksFn = Callable[[PhaseArtifact], Dict[str, Any]]


def run_phase(
    *,
    artifact: PhaseArtifact,
    iteration: GuidedIterationArtifact | None,
    iteration_index: int,
    complete: CompleteFn,
    spec: PhaseRunSpec,
    now: NowFn,
    make_event: MakeEventFn,
    emit: EmitFn,
    ensure_machine_checks: EnsureMachineChecksFn,
    on_response: Callable[[str], None] | None = None,
) -> Tuple[List[StrategyEvent], Optional[str]]:
    events: List[StrategyEvent] = []
    artifact.status = PhaseStatus.RUNNING
    artifact.started_at = now()
    start_event = make_event(
        kind=StrategyEventKind.PHASE_TRANSITION,
        message=spec.start_message,
        phase=artifact.phase.value,
        iteration=iteration_index,
    )
    emit(start_event)
    events.append(start_event)

    try:
        response_raw = complete()
    except Exception as exc:  # pragma: no cover - transport level failure
        artifact.status = PhaseStatus.FAILED
        artifact.completed_at = now()
        artifact.human_notes = f"{spec.exception_human_notes_prefix}{exc}"
        failure_event = make_event(
            kind=StrategyEventKind.NOTE,
            message=spec.failed_message,
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"error": str(exc)},
        )
        emit(failure_event)
        events.append(failure_event)
        return events, None

    response_text = (response_raw or "").strip()
    artifact.response = response_text

    if spec.require_non_empty and not response_text:
        artifact.status = PhaseStatus.FAILED
        artifact.completed_at = now()
        artifact.human_notes = spec.empty_human_notes
        failure_event = make_event(
            kind=StrategyEventKind.NOTE,
            message=spec.empty_failed_message,
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        if iteration is not None and spec.set_iteration_failure_reason_on_empty:
            iteration.failure_reason = spec.set_iteration_failure_reason_on_empty
        emit(failure_event)
        events.append(failure_event)
        return events, None

    if response_text and on_response is not None:
        on_response(response_text)

    if spec.machine_check_key:
        machine_checks = ensure_machine_checks(artifact)
        machine_checks[spec.machine_check_key] = response_text

    artifact.status = PhaseStatus.COMPLETED
    artifact.completed_at = now()
    completion_event = make_event(
        kind=StrategyEventKind.PHASE_TRANSITION,
        message=spec.completed_message,
        phase=artifact.phase.value,
        iteration=iteration_index,
        data={"characters": len(response_text)},
    )
    emit(completion_event)
    events.append(completion_event)
    return events, response_text
