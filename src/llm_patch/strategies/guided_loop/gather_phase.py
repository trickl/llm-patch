"""Gather phase executor.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

Gather is specialized compared to other LLM-backed phases:
- requires strict structured JSON output (with retries)
- enforces additional structural requirements based on planning text
- collects extra context snippets from the repository
- records telemetry about gather requests and results
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence

from ..base import StrategyEvent, StrategyEventKind
from . import gathering
from . import error_processing
from .phases import GuidedIterationArtifact, GuidedPhase, PhaseArtifact, PhaseStatus


CompleteFn = Callable[..., str]
NowFn = Callable[[], str]
EmitFn = Callable[[StrategyEvent], None]
MakeEventFn = Callable[..., StrategyEvent]
EnsureMachineChecksFn = Callable[[PhaseArtifact], Dict[str, Any]]
FocusedContextWindowFn = Callable[[], str]
FindPhaseResponseFn = Callable[[GuidedIterationArtifact, GuidedPhase], Optional[str]]
CoerceStringFn = Callable[[Any], Optional[str]]
RecordIterationTelemetryFn = Callable[[GuidedIterationArtifact, str, Dict[str, Any]], None]


def execute_gather(
    *,
    artifact: PhaseArtifact,
    iteration: GuidedIterationArtifact,
    iteration_index: int,
    request: Any,
    complete: CompleteFn,
    temperature: float,
    model: Optional[str],
    allowed_categories: Sequence[str],
    allowed_target_kinds: Sequence[str],
    focused_context_window: FocusedContextWindowFn,
    find_phase_response: FindPhaseResponseFn,
    coerce_string: CoerceStringFn,
    record_iteration_telemetry: RecordIterationTelemetryFn,
    now: NowFn,
    make_event: MakeEventFn,
    emit: EmitFn,
    ensure_machine_checks: EnsureMachineChecksFn,
) -> List[StrategyEvent]:
    """Run the Gather phase.

    Parameters are passed explicitly so this helper is easy to test and so
    `controller.py` can remain mostly orchestration glue.

    `request` is intentionally typed as Any here to avoid a circular import on
    GuidedLoopInputs; the function uses only the attributes required by the
    gathering helpers.
    """

    events: List[StrategyEvent] = []
    artifact.status = PhaseStatus.RUNNING
    artifact.started_at = now()
    start_event = make_event(
        kind=StrategyEventKind.PHASE_TRANSITION,
        message="Starting Gather phase",
        phase=artifact.phase.value,
        iteration=iteration_index,
    )
    emit(start_event)
    events.append(start_event)

    base_prompt = artifact.prompt
    response_text: str = ""
    parsed: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    attempts = 0

    for attempt in range(1, 4):
        attempts = attempt
        try:
            # Gather requires strict structured output; if the client/provider supports it,
            # request native JSON formatting at the API layer (e.g., Ollama "format": "json").
            try:
                response = complete(
                    prompt=artifact.prompt,
                    temperature=temperature,
                    model=model,
                    response_format="json",
                )
            except TypeError:
                response = complete(
                    prompt=artifact.prompt,
                    temperature=temperature,
                    model=model,
                )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = now()
            artifact.human_notes = f"Gather phase failed: {exc}"
            failure_event = make_event(
                kind=StrategyEventKind.NOTE,
                message="Gather phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            emit(failure_event)
            events.append(failure_event)
            return events

        response_text = response.strip()
        try:
            parsed = gathering.parse_gather_response(
                response_text,
                allowed_categories=set(allowed_categories),
                allowed_target_kinds=set(allowed_target_kinds),
            )
            last_error = None
            break
        except ValueError as exc:
            parsed = None
            last_error = str(exc)
            # retry with a stronger constraint suffix
            artifact.prompt = (
                base_prompt
                + "\n\nIMPORTANT: Your previous response was invalid. Output ONLY the JSON object (no prose, no code fences), matching the schema exactly."
            )

    # restore original prompt so the trace remains stable
    artifact.prompt = base_prompt
    artifact.response = response_text
    machine_checks = ensure_machine_checks(artifact)
    machine_checks["gather"] = {
        "attempts": attempts,
        "parseError": last_error,
    }

    if parsed is None:
        parsed = {"needs_more_context": False, "requests": []}
        artifact.human_notes = (
            "Gather stage did not return parseable JSON after 3 attempts; continuing without additional context."
        )

    planning_text = coerce_string(find_phase_response(iteration, GuidedPhase.PLANNING))
    parsed, enforced_reason = gathering.enforce_gather_structural_requirements(
        gather_request=parsed,
        planning_text=planning_text,
        context_window=focused_context_window(),
    )
    machine_checks["gather"]["enforced"] = enforced_reason is not None
    machine_checks["gather"]["enforcementReason"] = enforced_reason

    machine_checks["gather_request"] = parsed
    gathered_text, gathered_details = gathering.collect_gathered_context(
        request,
        parsed,
        detect_error_line=error_processing.detect_error_line,
    )
    machine_checks["gathered_context_text"] = gathered_text
    machine_checks["gathered_context"] = gathered_details
    record_iteration_telemetry(
        iteration,
        "gather",
        {
            "request": parsed,
            "collected": gathered_details,
        },
    )

    artifact.status = PhaseStatus.COMPLETED
    artifact.completed_at = now()
    completion_event = make_event(
        kind=StrategyEventKind.PHASE_TRANSITION,
        message="Gather phase completed",
        phase=artifact.phase.value,
        iteration=iteration_index,
        data={
            "characters": len(artifact.response or ""),
            "gatheredCharacters": len(gathered_text or ""),
        },
    )
    emit(completion_event)
    events.append(completion_event)
    return events
