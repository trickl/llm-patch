"""Trace planning helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It centralizes:
- planning the iteration/phase skeleton (`GuidedLoopTrace`)
- the phase ordering for primary vs refine loops

The actual prompt rendering remains delegated to the controller via a callback.
"""

from __future__ import annotations

from typing import Callable, List

from .models import GuidedLoopConfig, GuidedLoopInputs
from .phases import GuidedIterationArtifact, GuidedLoopTrace, GuidedPhase, PhaseArtifact, PhaseStatus


def phase_order(*, kind: str = "primary") -> List[GuidedPhase]:
    if kind == "refine":
        return [
            GuidedPhase.PLANNING,
            GuidedPhase.GATHER,
            GuidedPhase.PROPOSE,
            GuidedPhase.GENERATE_PATCH,
            GuidedPhase.CRITIQUE,
        ]
    return [
        GuidedPhase.DIAGNOSE,
        GuidedPhase.PLANNING,
        GuidedPhase.GATHER,
        GuidedPhase.PROPOSE,
        GuidedPhase.GENERATE_PATCH,
        GuidedPhase.CRITIQUE,
    ]


def plan_trace(
    *,
    strategy_name: str,
    config: GuidedLoopConfig,
    request: GuidedLoopInputs,
    render_prompt: Callable[[GuidedPhase, GuidedLoopInputs], str],
) -> GuidedLoopTrace:
    trace = GuidedLoopTrace(
        strategy=strategy_name,
        target_language=request.language,
        case_id=request.case_id,
        build_command=" ".join(request.compile_command or []) or None,
    )
    primary_iterations = max(1, config.max_iterations)
    refine_iterations = max(0, config.refine_sub_iterations)
    passes = max(1, config.main_loop_passes)
    iteration_counter = 0
    loop_counter = 0
    refine_counter = 0

    for pass_index in range(1, passes + 1):
        include_full_critiques = pass_index > 1
        for _ in range(primary_iterations):
            iteration_counter += 1
            loop_counter += 1
            label = f"Loop {loop_counter}"
            iteration = GuidedIterationArtifact(
                index=iteration_counter,
                kind="primary",
                label=label,
                pass_index=pass_index,
                include_full_critiques=include_full_critiques,
            )
            for phase in phase_order(kind="primary"):
                prompt = render_prompt(phase, request)
                artifact = PhaseArtifact(phase=phase, status=PhaseStatus.PLANNED, prompt=prompt)
                trace.add_phase(iteration, artifact)
            trace.iterations.append(iteration)

        for _ in range(refine_iterations):
            iteration_counter += 1
            refine_counter += 1
            label = f"Refine {refine_counter}"
            iteration = GuidedIterationArtifact(
                index=iteration_counter,
                kind="refine",
                label=label,
                pass_index=pass_index,
                include_full_critiques=include_full_critiques,
            )
            for phase in phase_order(kind="refine"):
                prompt = render_prompt(phase, request)
                artifact = PhaseArtifact(phase=phase, status=PhaseStatus.PLANNED, prompt=prompt)
                trace.add_phase(iteration, artifact)
            trace.iterations.append(iteration)

    trace.notes = (
        "Trace contains prompt templates only. Actual execution will attach responses, checks, "
        "and iteration history entries for each loop."
    )
    return trace
