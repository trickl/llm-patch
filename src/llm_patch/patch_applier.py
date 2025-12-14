"""Core functionality for applying unified diffs using fuzzy matching."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional, Sequence, Tuple

from .fuzzy_matcher import FuzzyMatcher


HUNK_HEADER_RE = re.compile(r"@@ -(?P<orig_start>\d+)(?:,(?P<orig_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@")


@dataclass(slots=True)
class ParsedHunk:
    """Lightweight representation of a unified diff hunk."""

    original_lines: List[str]
    updated_lines: List[str]
    original_start: int | None = None
    new_start: int | None = None


class PatchApplier:
    """Apply unified diff hunks against a source string using fuzzy matching."""

    def __init__(self, similarity_threshold: float = 0.8):
        if not 0 <= similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        self.similarity_threshold = similarity_threshold
        self.fuzzy_matcher = FuzzyMatcher(threshold=similarity_threshold)

    # ------------------------------------------------------------------
    def apply(self, source: str, patch: str) -> Tuple[str, bool]:
        """Apply ``patch`` (unified diff or replacement text) to ``source``."""

        if not patch:
            return source, True

        # Maintain backwards compatibility with legacy callers that pass the
        # "after" text instead of a diff by returning the patch verbatim when no
        # diff markers are detected.
        if not self._looks_like_unified_diff(patch):
            return patch, True

        hunks = self._parse_unified_diff(patch)
        if not hunks:
            return source, False

        normalized_source = self._split_preserving_trailing_newline(source)
        result_lines = list(normalized_source[0])
        had_trailing_newline = normalized_source[1]

        for hunk in hunks:
            success, result_lines = self._apply_hunk(result_lines, hunk)
            if not success:
                return source, False

        result_text = "\n".join(result_lines)
        if had_trailing_newline and not result_text.endswith("\n"):
            result_text += "\n"
        return result_text, True

    # ------------------------------------------------------------------
    def find_context(self, source_lines: List[str], context_lines: List[str]) -> Optional[int]:
        return self.fuzzy_matcher.find_best_match(source_lines, context_lines)

    # ------------------------------------------------------------------
    @staticmethod
    def _looks_like_unified_diff(patch: str) -> bool:
        markers = ("\n@@", "@@ ", "\n+", "\n-", "--- ", "+++ ")
        return any(marker in patch for marker in markers)

    @staticmethod
    def _split_preserving_trailing_newline(source: str) -> tuple[List[str], bool]:
        if not source:
            return [], False
        trailing_newline = source.endswith("\n")
        return source.splitlines(), trailing_newline

    # ------------------------------------------------------------------
    def _apply_hunk(self, lines: List[str], hunk: ParsedHunk) -> Tuple[bool, List[str]]:
        if not hunk.original_lines:
            insert_at = self._insertion_index(lines, hunk)
            updated = lines[:insert_at] + list(hunk.updated_lines) + lines[insert_at:]
            return True, updated

        index = self.find_context(lines, hunk.original_lines)
        if index is None:
            return False, lines
        if index < 0 or index > len(lines):
            return False, lines

        updated_lines = list(lines[:index])
        updated_lines.extend(hunk.updated_lines)
        updated_lines.extend(lines[index + len(hunk.original_lines) :])
        return True, updated_lines

    def _insertion_index(self, lines: Sequence[str], hunk: ParsedHunk) -> int:
        hint = self._line_number_hint(hunk, len(lines))
        if hint is not None:
            return max(0, min(hint, len(lines)))
        return len(lines)

    @staticmethod
    def _line_number_hint(hunk: ParsedHunk, line_count: int) -> Optional[int]:
        if hunk.original_start is None:
            return None
        zero_indexed = max(0, hunk.original_start - 1)
        return min(zero_indexed, line_count)

    # ------------------------------------------------------------------
    def _parse_unified_diff(self, patch: str) -> List[ParsedHunk]:
        hunks: List[ParsedHunk] = []
        current_original: List[str] = []
        current_updated: List[str] = []
        current_header: Optional[dict[str, int]] = None
        in_hunk = False

        def flush() -> None:
            nonlocal current_original, current_updated, current_header, in_hunk
            if not in_hunk:
                return
            hunks.append(
                ParsedHunk(
                    original_lines=list(current_original),
                    updated_lines=list(current_updated),
                    original_start=(current_header or {}).get("orig_start"),
                    new_start=(current_header or {}).get("new_start"),
                )
            )
            current_original = []
            current_updated = []
            current_header = None
            in_hunk = False

        for raw_line in patch.splitlines():
            if raw_line.startswith("@@"):
                flush()
                header = HUNK_HEADER_RE.match(raw_line)
                if header:
                    current_header = {
                        "orig_start": int(header.group("orig_start")),
                        "new_start": int(header.group("new_start")),
                    }
                else:
                    current_header = None
                in_hunk = True
                continue
            if not in_hunk:
                continue
            if raw_line.startswith("---") or raw_line.startswith("+++"):
                continue
            if raw_line.startswith("+" ):
                current_updated.append(raw_line[1:])
                continue
            if raw_line.startswith("-"):
                current_original.append(raw_line[1:])
                continue
            if raw_line.startswith(" "):
                text = raw_line[1:]
                current_original.append(text)
                current_updated.append(text)
                continue
            if raw_line.startswith("\\"):
                continue
        flush()
        return hunks


def apply_patch(source: str, patch: str, similarity_threshold: float = 0.8) -> Tuple[str, bool]:
    """
    Convenience function to apply a patch to source code.

    Args:
        source: The original source code as a string.
        patch: The unified diff patch as a string.
        similarity_threshold: Minimum similarity ratio (0-1) for matching contexts.

    Returns:
        A tuple of (modified_source, success) where modified_source is the
        patched code and success indicates if the patch was applied successfully.
    """
    applier = PatchApplier(similarity_threshold)
    return applier.apply(source, patch)
