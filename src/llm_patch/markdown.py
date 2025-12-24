"""Markdown parsing helpers.

The project ingests LLM outputs which *may* contain Markdown code fences even when
prompts ask models not to. We therefore centralize fence handling here so every
consumer is tolerant to:

- ```\n ... \n```
- ```lang\n ... \n```
- ~~~\n ... \n~~~
- ~~~lang\n ... \n~~~

These helpers are intentionally permissive: anything that starts with a fence
marker (``` or ~~~) is treated as a fence line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


_FENCE_LINE_RE = re.compile(r"^\s*(?P<fence>```|~~~)(?P<info>.*)$")


def is_fence_line(line: str) -> bool:
    """Return True if the line looks like a Markdown fence line.

    We treat any line that starts with ``` or ~~~ (optionally preceded by
    whitespace) as a fence line, regardless of any trailing language/info text.
    """

    if not line:
        return False
    return _FENCE_LINE_RE.match(line) is not None


def strip_fence_lines(text: str) -> str:
    """Remove all fence lines from text.

    This is best when downstream parsers expect raw patch/diff content and the
    model might have inserted fence lines anywhere.
    """

    if not text:
        return text
    kept: List[str] = []
    for raw_line in text.splitlines():
        if is_fence_line(raw_line.strip()):
            continue
        kept.append(raw_line)
    return "\n".join(kept)


@dataclass(frozen=True, slots=True)
class UnwrappedFence:
    content: str
    fence: str | None = None
    info: str | None = None


def unwrap_fenced_block(text: str, *, fence_markers: Sequence[str] = ("```", "~~~")) -> UnwrappedFence:
    """Unwrap a single top-level fenced block if the text starts with a fence.

    If the text does not begin with a fence line, this returns the original text
    (trimmed of outer whitespace).

    If an opening fence is present but no closing fence is found, we drop the
    opening fence line and return the remainder.

    If multiple closing fences exist, we use the *last* matching fence line.
    """

    if not text:
        return UnwrappedFence(content=text)

    stripped = text.strip()
    if not stripped:
        return UnwrappedFence(content=stripped)

    lines = stripped.splitlines()
    if not lines:
        return UnwrappedFence(content=stripped)

    first = lines[0]
    match = _FENCE_LINE_RE.match(first)
    if not match:
        return UnwrappedFence(content=stripped)

    fence = match.group("fence")
    if fence not in fence_markers:
        return UnwrappedFence(content=stripped)

    info = (match.group("info") or "").strip() or None

    # Find the last line that is a fence line with the same marker.
    closing_idx: Optional[int] = None
    for idx in range(len(lines) - 1, 0, -1):
        m = _FENCE_LINE_RE.match(lines[idx])
        if not m:
            continue
        if m.group("fence") == fence:
            closing_idx = idx
            break

    if closing_idx is None:
        inner_lines = lines[1:]
    else:
        inner_lines = lines[1:closing_idx]

    return UnwrappedFence(content="\n".join(inner_lines).strip(), fence=fence, info=info)
