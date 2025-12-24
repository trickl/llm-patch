"""Phase definitions for the Guided Convergence Loop strategy."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from .hypothesis import HypothesisSet


class GuidedPhase(str, Enum):
    """Canonical ordered phases described in the pattern documentation."""

    DIAGNOSE = "diagnose"
    PLANNING = "planning"
    GATHER = "gather"
    PROPOSE = "propose"
    GENERATE_PATCH = "generate-patch"
    CRITIQUE = "critique"


class PhaseStatus(str, Enum):
    """Lifecycle indicator for a single Guided Convergence phase."""

    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class PhaseArtifact:
    """Captures the inputs/outputs for a single phase invocation."""

    phase: GuidedPhase
    status: PhaseStatus
    prompt: str
    response: Optional[str] = None
    machine_checks: Mapping[str, Any] = field(default_factory=dict)
    human_notes: Optional[str] = None
    metrics: Mapping[str, float] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "status": self.status.value,
            "prompt": self.prompt,
            "response": self.response,
            "machineChecks": dict(self.machine_checks),
            "humanNotes": self.human_notes,
            "metrics": dict(self.metrics),
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
        }


@dataclass(slots=True)
class GuidedIterationArtifact:
    """One full loop (Diagnose → Critique) worth of artifacts."""

    index: int
    phases: List[PhaseArtifact] = field(default_factory=list)
    accepted: bool = False
    failure_reason: Optional[str] = None
    history_context: Optional[str] = None
    history_entry: Optional[str] = None
    kind: str = "primary"
    label: Optional[str] = None
    hypotheses: "HypothesisSet" | None = None
    selected_hypothesis_id: Optional[str] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)
    pass_index: int = 1
    include_full_critiques: bool = False

    # Optional outcome snapshots for UI inspection. These can be large, so they are
    # not required for the strategy to function, but they are useful for the
    # reviewer UI to switch between iteration outputs.
    patch_applied: Optional[bool] = None
    patched_text: Optional[str] = None
    diff_text: Optional[str] = None
    patch_diagnostics: Optional[str] = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "phases": [phase.to_dict() for phase in self.phases],
            "accepted": self.accepted,
            "failureReason": self.failure_reason,
            "historyContext": self.history_context,
            "historyEntry": self.history_entry,
            "kind": self.kind,
            "label": self.label,
            "hypotheses": self.hypotheses.to_dict() if self.hypotheses else None,
            "selectedHypothesisId": self.selected_hypothesis_id,
            "telemetry": dict(self.telemetry),
            "passIndex": self.pass_index,
            "includeFullCritiques": self.include_full_critiques,

            # Optional outcome snapshot fields.
            "patchApplied": self.patch_applied,
            "patchedText": self.patched_text,
            "diffText": self.diff_text,
            "patchDiagnostics": self.patch_diagnostics,
            "compileReturncode": self.compile_returncode,
            "compileStdout": self.compile_stdout,
            "compileStderr": self.compile_stderr,
        }


@dataclass(slots=True)
class GuidedLoopTrace:
    """Complete execution trace of the Guided Convergence strategy."""

    strategy: str
    iterations: List[GuidedIterationArtifact] = field(default_factory=list)
    target_language: Optional[str] = None
    case_id: Optional[str] = None
    build_command: Optional[str] = None
    notes: Optional[str] = None

    def add_phase(self, iteration: GuidedIterationArtifact, artifact: PhaseArtifact) -> None:
        iteration.phases.append(artifact)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "iterations": [iteration.to_dict() for iteration in self.iterations],
            "targetLanguage": self.target_language,
            "caseId": self.case_id,
            "buildCommand": self.build_command,
            "notes": self.notes,
        }