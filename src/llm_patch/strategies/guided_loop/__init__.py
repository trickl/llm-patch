"""Guided Convergence Loop strategy scaffolding."""
from .checklist import GUIDED_LOOP_CHECKLIST, GUIDED_LOOP_CHECKLIST_JSON, GUIDED_LOOP_CHECKLIST_TEXT
from .controller import GuidedConvergenceStrategy, GuidedLoopConfig, GuidedLoopInputs, GuidedLoopResult
from .hypothesis import Hypothesis, HypothesisManager, HypothesisSet, HypothesisStatus
from .phases import GuidedLoopTrace, GuidedPhase, GuidedIterationArtifact, PhaseArtifact, PhaseStatus

__all__ = [
    "GuidedConvergenceStrategy",
    "GuidedLoopConfig",
    "GuidedLoopInputs",
    "GuidedLoopResult",
    "Hypothesis",
    "HypothesisManager",
    "HypothesisSet",
    "HypothesisStatus",
    "GuidedLoopTrace",
    "GuidedPhase",
    "GuidedIterationArtifact",
    "PhaseArtifact",
    "PhaseStatus",
    "GUIDED_LOOP_CHECKLIST",
    "GUIDED_LOOP_CHECKLIST_JSON",
    "GUIDED_LOOP_CHECKLIST_TEXT",
]
