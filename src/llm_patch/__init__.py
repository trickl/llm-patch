"""
LLM Patch - A tool for reliably applying LLM-generated unified diffs.

This package provides functionality for applying patches using fuzzy,
context-based matching instead of line numbers.
"""

__version__ = "0.1.0"
__author__ = "trickl"

from .patch_applier import PatchApplier, apply_patch
from .fuzzy_matcher import FuzzyMatcher
from .strategies import (
	PatchRequest,
	PatchResult,
	PatchStrategy,
	StrategyEvent,
	StrategyEventKind,
	StrategyObserver,
)
from .strategies.guided_loop import (
	GuidedConvergenceStrategy,
	GuidedLoopConfig,
	GuidedLoopInputs,
	GuidedLoopResult,
	GuidedLoopTrace,
	GuidedPhase,
)

__all__ = [
	"PatchApplier",
	"apply_patch",
	"FuzzyMatcher",
	"PatchRequest",
	"PatchResult",
	"PatchStrategy",
	"StrategyEvent",
	"StrategyEventKind",
	"StrategyObserver",
	"GuidedConvergenceStrategy",
	"GuidedLoopConfig",
	"GuidedLoopInputs",
	"GuidedLoopResult",
	"GuidedLoopTrace",
	"GuidedPhase",
]
