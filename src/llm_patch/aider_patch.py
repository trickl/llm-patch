"""Aider-inspired patch application helpers.

This module adapts the SEARCH/REPLACE matching logic from
`aider/coders/editblock_coder.py` (see commit
7c9cff2f6ecea9b68cced7d446086a7e79c70c04) so we can score the algorithm against
our corpus of unified diffs. The implementation stays as close to upstream as
possible; any deviations are documented inline."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import math
import re
from typing import Iterable, List, Sequence


@dataclass
class DiffHunk:
    """Simplified representation of a unified-diff hunk."""

    original_lines: List[str]
    updated_lines: List[str]


def _prep(content: str) -> tuple[str, List[str]]:
    if content and not content.endswith("\n"):
        content += "\n"
    return content, content.splitlines(keepends=True)


def _perfect_replace(
    whole_lines: Sequence[str], part_lines: Sequence[str], replace_lines: Sequence[str]
) -> str | None:
    part_tuple = tuple(part_lines)
    part_len = len(part_tuple)
    if part_len == 0:
        return None
    for idx in range(len(whole_lines) - part_len + 1):
        if tuple(whole_lines[idx : idx + part_len]) == part_tuple:
            result = whole_lines[:idx] + list(replace_lines) + list(whole_lines[idx + part_len :])
            return "".join(result)
    return None


def _match_but_for_leading_whitespace(whole_lines: Sequence[str], part_lines: Sequence[str]) -> str | None:
    count = len(whole_lines)
    if count != len(part_lines):
        return None
    if not all(whole_lines[i].lstrip() == part_lines[i].lstrip() for i in range(count)):
        return None
    prefixes = {
        whole_lines[i][: len(whole_lines[i]) - len(part_lines[i])]
        for i in range(count)
        if whole_lines[i].strip()
    }
    if len(prefixes) != 1:
        return None
    return prefixes.pop()


def _replace_part_with_missing_leading_whitespace(
    whole_lines: Sequence[str], part_lines: Sequence[str], replace_lines: Sequence[str]
) -> str | None:
    leading = [len(p) - len(p.lstrip()) for p in part_lines if p.strip()]
    leading += [len(p) - len(p.lstrip()) for p in replace_lines if p.strip()]
    if leading:
        offset = min(leading)
        if offset:
            part_lines = [p[offset:] if p.strip() else p for p in part_lines]
            replace_lines = [p[offset:] if p.strip() else p for p in replace_lines]
    part_len = len(part_lines)
    for idx in range(len(whole_lines) - part_len + 1):
        add_leading = _match_but_for_leading_whitespace(whole_lines[idx : idx + part_len], part_lines)
        if add_leading is None:
            continue
        adjusted_replace = [add_leading + line if line.strip() else line for line in replace_lines]
        combined = list(whole_lines[:idx]) + adjusted_replace + list(whole_lines[idx + part_len :])
        return "".join(combined)
    return None


def _perfect_or_whitespace(
    whole_lines: Sequence[str], part_lines: Sequence[str], replace_lines: Sequence[str]
) -> str | None:
    direct = _perfect_replace(whole_lines, part_lines, replace_lines)
    if direct:
        return direct
    return _replace_part_with_missing_leading_whitespace(whole_lines, part_lines, replace_lines)


_DOTS_RE = re.compile(r"(^\s*\.\.\.\n)", re.MULTILINE | re.DOTALL)


def _try_dotdotdots(whole: str, part: str, replace: str) -> str | None:
    part_pieces = re.split(_DOTS_RE, part)
    replace_pieces = re.split(_DOTS_RE, replace)
    if len(part_pieces) != len(replace_pieces):
        raise ValueError("Unpaired ... in SEARCH/REPLACE block")
    if len(part_pieces) == 1:
        return None
    # Keep only the literal segments (even indices).
    part_literals = [part_pieces[i] for i in range(0, len(part_pieces), 2)]
    replace_literals = [replace_pieces[i] for i in range(0, len(replace_pieces), 2)]
    for literal_part, literal_replace in zip(part_literals, replace_literals, strict=False):
        if not literal_part and not literal_replace:
            continue
        if not literal_part and literal_replace:
            if not whole.endswith("\n"):
                whole += "\n"
            whole += literal_replace
            continue
        occurrences = whole.count(literal_part)
        if occurrences == 0:
            raise ValueError
        if occurrences > 1:
            raise ValueError
        whole = whole.replace(literal_part, literal_replace, 1)
    return whole


def _replace_closest_edit_distance(
    whole_lines: Sequence[str], part: str, part_lines: Sequence[str], replace_lines: Sequence[str]
) -> str | None:
    similarity_thresh = 0.8
    max_similarity = 0.0
    best_start = -1
    best_end = -1
    scale = 0.1
    min_len = max(1, math.floor(len(part_lines) * (1 - scale)))
    max_len = max(min_len, math.ceil(len(part_lines) * (1 + scale)))
    for length in range(min_len, max_len + 1):
        for idx in range(len(whole_lines) - length + 1):
            chunk = "".join(whole_lines[idx : idx + length])
            similarity = SequenceMatcher(None, chunk, part).ratio()
            if similarity > max_similarity:
                max_similarity = similarity
                best_start = idx
                best_end = idx + length
    if max_similarity < similarity_thresh or best_start < 0:
        return None
    combined = list(whole_lines[:best_start]) + list(replace_lines) + list(whole_lines[best_end:])
    return "".join(combined)


def replace_most_similar_chunk(whole: str, part: str, replace: str) -> str | None:
    """Find ``part`` inside ``whole`` and replace it with ``replace``.

    This mirrors ``replace_most_similar_chunk`` from aider, except that we keep
    the edit-distance fallback enabled so the algorithm can still act when the
    context has drifted between the diff and the working tree.
    """

    whole, whole_lines = _prep(whole)
    part, part_lines = _prep(part)
    replace, replace_lines = _prep(replace)

    result = _perfect_or_whitespace(whole_lines, part_lines, replace_lines)
    if result:
        return result

    if len(part_lines) > 2 and not part_lines[0].strip():
        trimmed_part_lines = part_lines[1:]
        result = _perfect_or_whitespace(whole_lines, trimmed_part_lines, replace_lines)
        if result:
            return result

    try:
        result = _try_dotdotdots(whole, part, replace)
        if result:
            return result
    except ValueError:
        # Upstream ignores failures here and falls through to the fuzzy matcher.
        pass

    return _replace_closest_edit_distance(whole_lines, part, part_lines, replace_lines)


def parse_unified_diff_hunks(diff_text: str) -> List[DiffHunk]:
    hunks: List[DiffHunk] = []
    original: List[str] = []
    updated: List[str] = []
    in_hunk = False

    def flush() -> None:
        if not original and not updated:
            return
        hunks.append(DiffHunk(original_lines=list(original), updated_lines=list(updated)))
        original.clear()
        updated.clear()

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("@@"):
            flush()
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue
        if raw_line.startswith("+"):
            updated.append(raw_line[1:])
        elif raw_line.startswith("-"):
            original.append(raw_line[1:])
        elif raw_line.startswith(" "):
            line = raw_line[1:]
            original.append(line)
            updated.append(line)
        elif raw_line.startswith("\\"):
            # ``\ No newline at end of file`` hint – safe to ignore.
            continue
    flush()
    return hunks


def apply_aider_patch(source: str, diff_text: str) -> tuple[str, bool, str]:
    """Apply a unified diff using aider's SEARCH/REPLACE heuristics."""

    hunks = parse_unified_diff_hunks(diff_text)
    if not hunks:
        return source, True, "no hunks"

    updated_text = source
    applied = 0

    for hunk in hunks:
        # When a hunk contains no original lines (pure additions to empty files),
        # append the new content at the end of the file as a best-effort.
        if not hunk.original_lines:
            addition = "\n".join(hunk.updated_lines)
            if addition and not addition.endswith("\n"):
                addition += "\n"
            updated_text = (updated_text or "") + addition
            applied += 1
            continue

        old_block = "\n".join(hunk.original_lines)
        new_block = "\n".join(hunk.updated_lines)
        candidate = replace_most_similar_chunk(updated_text, old_block, new_block)
        if candidate is None:
            return source, False, "aider matcher could not locate context"
        updated_text = candidate
        applied += 1

    return updated_text, True, f"applied {applied} hunks"
