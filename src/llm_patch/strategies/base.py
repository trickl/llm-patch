"""Shared abstractions for patching strategies.

The Guided Convergence Loop strategy depends on richer lifecycle tracking than the
existing one-shot patchers. This module provides neutral interfaces so multiple
strategies (git apply, diff-match-patch, aider, guided loop, etc.) can plug into
shared tooling without hard dependencies on each other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Protocol


class StrategyEventKind(str, Enum):
    """Kinds of lifecycle events emitted by patch strategies."""

    PHASE_TRANSITION = "phase-transition"
    ARTIFACT_EMITTED = "artifact-emitted"
    METRIC_RECORDED = "metric-recorded"
    NOTE = "note"


@dataclass(slots=True)
class StrategyEvent:
    """Structured observability payload for strategy orchestration."""

    kind: StrategyEventKind
    strategy: str
    message: str
    data: Mapping[str, Any] = field(default_factory=dict)
    phase: Optional[str] = None
    iteration: Optional[int] = None
    timestamp: Optional[str] = None


class StrategyObserver(Protocol):
    """Observer interface for streaming strategy events to logs, UI, or stores."""

    def notify(self, event: StrategyEvent) -> None:  # pragma: no cover - interface
        """Handle a new strategy event."""


@dataclass(slots=True)
class PatchRequest:
    """Normalized payload handed to every patching strategy."""

    case_id: str
    language: str
    source_path: Path
    source_text: str
    error_text: str
    manifest: Mapping[str, Any]
    extra: MutableMapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PatchResult:
    """Result produced by ``PatchStrategy.run`` calls."""

    applied: bool
    success: bool
    after_text: Optional[str] = None
    diff_text: Optional[str] = None
    notes: str | None = None
    events: List[StrategyEvent] = field(default_factory=list)
    artifacts: List[Mapping[str, Any]] = field(default_factory=list)


class PatchStrategy:
    """Base class for all patching strategies."""

    name: str = "abstract"

    def __init__(self, observer: StrategyObserver | None = None) -> None:
        self._observer = observer

    def set_observer(self, observer: StrategyObserver | None) -> None:
        self._observer = observer

    def run(self, request: PatchRequest) -> PatchResult:  # pragma: no cover - abstract API
        raise NotImplementedError

    # Helper methods -----------------------------------------------------
    def emit(self, event: StrategyEvent) -> None:
        if self._observer is None:
            return
        self._observer.notify(event)

    def _event(
        self,
        *,
        kind: StrategyEventKind,
        message: str,
        phase: str | None = None,
        iteration: int | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> StrategyEvent:
        return StrategyEvent(
            kind=kind,
            strategy=self.name,
            message=message,
            phase=phase,
            iteration=iteration,
            data=data or {},
        )