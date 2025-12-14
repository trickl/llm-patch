"""Strategy interfaces for LLM-guided patching."""
from .base import (
    PatchRequest,
    PatchResult,
    PatchStrategy,
    StrategyEvent,
    StrategyEventKind,
    StrategyObserver,
)

__all__ = [
    "PatchRequest",
    "PatchResult",
    "PatchStrategy",
    "StrategyEvent",
    "StrategyEventKind",
    "StrategyObserver",
]
