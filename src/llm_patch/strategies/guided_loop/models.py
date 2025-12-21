"""Shared dataclasses for the Guided Convergence Loop.

This module intentionally contains *only* data containers and lightweight computed
properties so the rest of the guided-loop implementation can be split into
smaller, testable modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence, Tuple

from ..base import PatchRequest, PatchResult
from .phases import GuidedLoopTrace


@dataclass(slots=True)
class GuidedLoopConfig:
    """Runtime configuration for the guided loop strategy."""

    max_iterations: int = 1
    refine_sub_iterations: int = 3
    main_loop_passes: int = 2
    interpreter_model: str = "planner"
    patch_model: str = "patcher"
    critique_model: Optional[str] = None
    temperature: float = 0.0
    auto_constraints: bool = True
    compile_check: bool = True

    def total_iterations(self) -> int:
        base = max(1, self.max_iterations)
        refinements = max(0, self.refine_sub_iterations)
        passes = max(1, self.main_loop_passes)
        return (base + refinements) * passes


@dataclass(slots=True)
class GuidedLoopInputs(PatchRequest):
    """Adds guided-loop specific context to the base patch request."""

    compile_command: Optional[Sequence[str]] = None
    additional_context: Mapping[str, Any] = field(default_factory=dict)
    history_seed: Sequence[str] = field(default_factory=tuple)
    initial_outcome: Optional[Mapping[str, Any]] = None
    raw_error_text: Optional[str] = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial wiring
        if self.raw_error_text is None:
            self.raw_error_text = self.error_text


@dataclass(slots=True)
class GuidedLoopResult(PatchResult):
    """Extends the base ``PatchResult`` with a structured trace."""

    trace: GuidedLoopTrace | None = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None
    patch_diagnostics: Optional[str] = None


@dataclass(slots=True)
class IterationOutcome:
    """Container for deterministic critique + compile results."""

    diff_text: Optional[str] = None
    patched_text: Optional[str] = None
    patch_applied: bool = False
    patch_diagnostics: Optional[str] = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None
    critique_feedback: Optional[str] = None
    hypothesis_id: Optional[str] = None
    error_fingerprint: Optional[str] = None
    previous_error_fingerprint: Optional[str] = None
    diff_span: Optional[Tuple[int, int]] = None
    error_message: Optional[str] = None
    error_location: Optional[int] = None

    @property
    def compile_success(self) -> bool:
        return self.compile_returncode == 0 if self.compile_returncode is not None else False
