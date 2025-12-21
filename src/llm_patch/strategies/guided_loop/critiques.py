"""Critique transcript helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It centralizes:
- recording critique transcripts
- formatting critique history text for prompts
"""

from __future__ import annotations

from typing import List, Optional, Sequence


def record_critique_transcript(transcripts: List[str], transcript: Optional[str]) -> None:
    if transcript:
        transcripts.append(transcript)


def critique_history_text(transcripts: Sequence[str], *, limit: Optional[int] = None) -> Optional[str]:
    if not transcripts:
        return None
    selected = transcripts[-limit:] if limit else list(transcripts)
    separator = "\n\n---\n\n"
    return separator.join(selected)
