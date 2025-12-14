"""Hypothesis lifecycle primitives for the guided loop strategy."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class HypothesisStatus(str, Enum):
    """Lifecycle states for a single hypothesis."""

    ACTIVE = "active"
    FALSIFIED = "falsified"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    EXPIRED = "expired"


@dataclass(slots=True)
class Hypothesis:
    """Represents a single structural diagnosis within the loop."""

    id: str
    claim: str
    affected_region: str
    expected_effect: str
    interpretation: Optional[str] = None
    explanation: Optional[str] = None
    structural_change: Optional[str] = None
    confidence: Optional[float] = None
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    retry_count: int = 0
    falsification_notes: List[str] = field(default_factory=list)

    def add_falsification_note(self, note: str) -> None:
        note = note.strip()
        if note:
            self.falsification_notes.append(note)

    def clone(self) -> "Hypothesis":
        """Return a shallow copy suitable for snapshots."""

        return Hypothesis(
            id=self.id,
            claim=self.claim,
            affected_region=self.affected_region,
            expected_effect=self.expected_effect,
            interpretation=self.interpretation,
            explanation=self.explanation,
            structural_change=self.structural_change,
            confidence=self.confidence,
            status=self.status,
            retry_count=self.retry_count,
            falsification_notes=list(self.falsification_notes),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "affectedRegion": self.affected_region,
            "expectedEffect": self.expected_effect,
            "interpretation": self.interpretation,
            "explanation": self.explanation,
            "structuralChange": self.structural_change,
            "confidence": self.confidence,
            "status": self.status.value,
            "retryCount": self.retry_count,
            "falsificationNotes": list(self.falsification_notes),
        }


@dataclass(slots=True)
class HypothesisSet:
    """Snapshot of hypothesis buckets for reporting/trace export."""

    active: List[Hypothesis] = field(default_factory=list)
    falsified: List[Hypothesis] = field(default_factory=list)
    rejected: List[Hypothesis] = field(default_factory=list)
    archived: List[Hypothesis] = field(default_factory=list)
    expired: List[Hypothesis] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active": [hyp.to_dict() for hyp in self.active],
            "falsified": [hyp.to_dict() for hyp in self.falsified],
            "rejected": [hyp.to_dict() for hyp in self.rejected],
            "archived": [hyp.to_dict() for hyp in self.archived],
            "expired": [hyp.to_dict() for hyp in self.expired],
        }


class HypothesisManager:
    """Simple lifecycle tracker for hypotheses across iterations."""

    def __init__(self) -> None:
        self._id_counter = itertools.count(1)
        self._active: Dict[str, Hypothesis] = {}
        self._falsified: Dict[str, Hypothesis] = {}
        self._rejected: Dict[str, Hypothesis] = {}
        self._archived: Dict[str, Hypothesis] = {}
        self._expired: Dict[str, Hypothesis] = {}

    def _allocate_id(self) -> str:
        return f"H{next(self._id_counter):03d}"

    def create(
        self,
        *,
        claim: str,
        affected_region: str,
        expected_effect: str,
        interpretation: Optional[str] = None,
        explanation: Optional[str] = None,
        structural_change: Optional[str] = None,
        confidence: Optional[float] = None,
        hypothesis_id: Optional[str] = None,
    ) -> Hypothesis:
        identifier = hypothesis_id or self._allocate_id()
        hypothesis = Hypothesis(
            id=identifier,
            claim=claim,
            affected_region=affected_region,
            expected_effect=expected_effect,
            interpretation=interpretation,
            explanation=explanation,
            structural_change=structural_change,
            confidence=confidence,
        )
        self._active[identifier] = hypothesis
        return hypothesis

    def active(self) -> List[Hypothesis]:
        return list(self._active.values())

    def active_count(self) -> int:
        return len(self._active)

    def get(self, hypothesis_id: str) -> Optional[Hypothesis]:
        return (
            self._active.get(hypothesis_id)
            or self._falsified.get(hypothesis_id)
            or self._rejected.get(hypothesis_id)
            or self._archived.get(hypothesis_id)
            or self._expired.get(hypothesis_id)
        )

    def record(self, hypothesis: Hypothesis) -> None:
        """Register an externally constructed hypothesis."""

        bucket = self._bucket_for_status(hypothesis.status)
        bucket[hypothesis.id] = hypothesis

    def set_status(self, hypothesis_id: str, status: HypothesisStatus) -> Optional[Hypothesis]:
        hypothesis = self.get(hypothesis_id)
        if hypothesis is None:
            return None
        if hypothesis.status == status:
            return hypothesis
        self._remove_from_all(hypothesis_id)
        hypothesis.status = status
        self._bucket_for_status(status)[hypothesis_id] = hypothesis
        return hypothesis

    def increment_retry(self, hypothesis_id: str) -> Optional[int]:
        hypothesis = self.get(hypothesis_id)
        if hypothesis is None:
            return None
        hypothesis.retry_count += 1
        return hypothesis.retry_count

    def add_falsification(self, hypothesis_id: str, note: str) -> None:
        hypothesis = self.get(hypothesis_id)
        if hypothesis is None:
            return
        hypothesis.add_falsification_note(note)

    def snapshot(self) -> HypothesisSet:
        return HypothesisSet(
            active=self._clone_bucket(self._active),
            falsified=self._clone_bucket(self._falsified),
            rejected=self._clone_bucket(self._rejected),
            archived=self._clone_bucket(self._archived),
            expired=self._clone_bucket(self._expired),
        )

    def values(self) -> Iterable[Hypothesis]:
        yield from self._active.values()
        yield from self._falsified.values()
        yield from self._rejected.values()
        yield from self._archived.values()
        yield from self._expired.values()

    def _bucket_for_status(self, status: HypothesisStatus) -> Dict[str, Hypothesis]:
        if status is HypothesisStatus.ACTIVE:
            return self._active
        if status is HypothesisStatus.FALSIFIED:
            return self._falsified
        if status is HypothesisStatus.REJECTED:
            return self._rejected
        if status is HypothesisStatus.ARCHIVED:
            return self._archived
        if status is HypothesisStatus.EXPIRED:
            return self._expired
        return self._active

    def _remove_from_all(self, hypothesis_id: str) -> None:
        for bucket in (
            self._active,
            self._falsified,
            self._rejected,
            self._archived,
            self._expired,
        ):
            bucket.pop(hypothesis_id, None)

    @staticmethod
    def _clone_bucket(bucket: Dict[str, Hypothesis]) -> List[Hypothesis]:
        return [hyp.clone() for hyp in bucket.values()]
