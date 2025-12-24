"""Patch application helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

It supports:
- parsing replacement blocks (ORIGINAL/CHANGED/NEW LINES)
- applying unified diffs / replacement blocks via PatchApplier
- attempting a three-way merge in a focused context fragment, with whole-file
  fallback when the fragment does not contain the ORIGINAL block
- computing approximate before/after spans for critique snippets
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from diff_match_patch import diff_match_patch

from llm_patch.patch_applier import PatchApplier, normalize_replacement_block

from .models import GuidedLoopInputs


REPLACEMENT_BLOCK_PATTERN = re.compile(
    r"ORIGINAL LINES:\s*\n(?P<original>.*?)\n(?:CHANGED|NEW) LINES:\s*\n(?P<updated>.*?)(?=(?:\nORIGINAL LINES:|\Z))",
    re.DOTALL,
)


CODE_FENCE_LINE_RE = re.compile(r"^\s*(?:```|~~~)")


def strip_code_fences(text: str) -> str:
    """Remove Markdown fence lines from an LLM patch response.

    Some models still wrap the patch template in ``` fences despite instructions.
    The patch parser and applier can usually recover, but stripping fences early
    keeps downstream telemetry/diff_text stable and easier to reason about.
    """

    if not text:
        return text
    kept: List[str] = []
    for raw_line in text.splitlines():
        if CODE_FENCE_LINE_RE.match(raw_line.strip()):
            continue
        kept.append(raw_line)
    return "\n".join(kept).strip()


def parse_replacement_blocks(diff_text: str) -> List[tuple[List[str], List[str]]]:
    blocks: List[tuple[List[str], List[str]]] = []
    text = diff_text.strip()
    for match in REPLACEMENT_BLOCK_PATTERN.finditer(text):
        original_lines = split_block_lines(match.group("original"))
        updated_lines = split_block_lines(match.group("updated"))
        blocks.append((original_lines, updated_lines))
    return blocks


def split_block_lines(block: str | None) -> List[str]:
    return normalize_replacement_block(block)


def aggregate_spans(spans: List[tuple[int, int]]) -> tuple[int, int] | None:
    if not spans:
        return None
    start = min(span[0] for span in spans)
    end = max(span[1] for span in spans)
    return start, end


def replacement_diff_spans(
    diff_text: str,
    source_text: str,
    *,
    patch_applier: PatchApplier,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    before_spans: List[tuple[int, int]] = []
    after_spans: List[tuple[int, int]] = []
    source_lines = source_text.splitlines()
    blocks = parse_replacement_blocks(diff_text)
    for original_lines, updated_lines in blocks:
        if not original_lines:
            continue
        index = patch_applier.find_context(source_lines, original_lines)
        if index is None:
            continue
        start_line = index + 1
        before_span = (start_line, start_line + max(len(original_lines), 1) - 1)
        after_span = (start_line, start_line + max(len(updated_lines), 1) - 1)
        before_spans.append(before_span)
        after_spans.append(after_span)
    return aggregate_spans(before_spans), aggregate_spans(after_spans)


def diff_spans(
    diff_text: str,
    *,
    source_text: str | None = None,
    patch_applier: PatchApplier | None = None,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    pattern = re.compile(r"@@ -(?P<start_a>\d+)(?:,(?P<len_a>\d+))? \+(?P<start_b>\d+)(?:,(?P<len_b>\d+))? @@")
    spans_a: List[tuple[int, int]] = []
    spans_b: List[tuple[int, int]] = []
    for line in diff_text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        start_a = int(match.group("start_a"))
        len_a = int(match.group("len_a") or 1)
        start_b = int(match.group("start_b"))
        len_b = int(match.group("len_b") or 1)
        spans_a.append((start_a, start_a + max(len_a, 1) - 1))
        spans_b.append((start_b, start_b + max(len_b, 1) - 1))

    if spans_a or spans_b:
        return aggregate_spans(spans_a), aggregate_spans(spans_b)

    if source_text and "ORIGINAL LINES:" in diff_text and "NEW LINES:" in diff_text:
        if patch_applier is None:
            raise RuntimeError("patch_applier is required to compute replacement diff spans")
        return replacement_diff_spans(diff_text, source_text, patch_applier=patch_applier)

    return None, None


def apply_diff_text(
    request: GuidedLoopInputs,
    diff_text: str,
    replacement_blocks: List[tuple[List[str], List[str]]],
    *,
    patch_applier: PatchApplier,
    dmp: diff_match_patch,
    detect_error_line: Callable[[str, str], Optional[int]],
    context_radius: int,
    suffix_collapse_max_lines: int,
    suffix_collapse_similarity: float,
) -> tuple[Optional[str], bool, str, tuple[tuple[int, int] | None, tuple[int, int] | None] | None]:
    if replacement_blocks and all(original for original, _ in replacement_blocks):
        patched_text, applied, message, spans = apply_three_way_blocks(
            request,
            replacement_blocks,
            patch_applier=patch_applier,
            dmp=dmp,
            detect_error_line=detect_error_line,
            context_radius=context_radius,
            suffix_collapse_max_lines=suffix_collapse_max_lines,
            suffix_collapse_similarity=suffix_collapse_similarity,
        )
        if applied:
            return patched_text, applied, message, spans

        # If the replacement targets lines outside the focused context fragment (for example imports at the
        # top of the file), the three-way merge will fail to locate the ORIGINAL block locally.
        # Fall back to a whole-file patch application so header edits can be applied deterministically.
        patched_text, applied = patch_applier.apply(request.source_text, diff_text)
        if not applied:
            return None, False, message, None
        spans = diff_spans(diff_text, source_text=request.source_text, patch_applier=patch_applier)
        return (
            patched_text,
            True,
            f"Applied patch using whole-file matching after three-way merge failed: {message}",
            spans,
        )

    patched_text, applied = patch_applier.apply(request.source_text, diff_text)
    if not applied:
        return None, False, "Patch applier could not locate context", None
    spans = diff_spans(diff_text, source_text=request.source_text, patch_applier=patch_applier)
    return patched_text, True, "Patch applied successfully", spans


def apply_three_way_blocks(
    request: GuidedLoopInputs,
    replacement_blocks: List[tuple[List[str], List[str]]],
    *,
    patch_applier: PatchApplier,
    dmp: diff_match_patch,
    detect_error_line: Callable[[str, str], Optional[int]],
    context_radius: int,
    suffix_collapse_max_lines: int,
    suffix_collapse_similarity: float,
) -> tuple[Optional[str], bool, str, tuple[tuple[int, int] | None, tuple[int, int] | None] | None]:
    fragment_info = context_fragment_lines(
        request,
        detect_error_line=detect_error_line,
        radius=context_radius,
    )
    if not fragment_info:
        return None, False, "Context fragment unavailable for merge.", None
    start_line, local_fragment = fragment_info
    original_length = len(local_fragment)
    if original_length == 0:
        return None, False, "Context fragment is empty; cannot run merge.", None

    base_fragment = list(local_fragment)
    build_success, target_fragment, build_diag = build_target_fragment(
        base_fragment,
        replacement_blocks,
        patch_applier=patch_applier,
    )
    if not build_success or target_fragment is None:
        message = build_diag or "Unable to construct target fragment for merge."
        return None, False, message, None

    merge_success, merged_fragment, merge_diag = merge_fragment_versions(
        base_fragment,
        local_fragment,
        target_fragment,
    )
    if not merge_success or merged_fragment is None:
        message = merge_diag or "Three-way merge failed while applying patch."
        return None, False, message, None

    source_lines = request.source_text.splitlines()
    start_idx = max(0, start_line - 1)
    end_idx = start_idx + original_length
    trailing_lines = source_lines[end_idx:]
    trailing_lines = collapse_suffix_overlap(
        merged_fragment,
        trailing_lines,
        dmp=dmp,
        suffix_collapse_max_lines=suffix_collapse_max_lines,
        suffix_collapse_similarity=suffix_collapse_similarity,
    )

    updated_source = source_lines[:start_idx] + merged_fragment + trailing_lines
    trailing_newline = request.source_text.endswith("\n")
    patched_text = "\n".join(updated_source)
    if trailing_newline and not patched_text.endswith("\n"):
        patched_text += "\n"

    before_span = (start_line, start_line + original_length - 1) if original_length else None
    after_span = (start_line, start_line + len(merged_fragment) - 1) if merged_fragment else None
    span_tuple: tuple[tuple[int, int] | None, tuple[int, int] | None] = (before_span, after_span)
    return patched_text, True, "Three-way merge applied to context fragment.", span_tuple


def build_target_fragment(
    base_fragment: List[str],
    replacement_blocks: List[tuple[List[str], List[str]]],
    *,
    patch_applier: PatchApplier,
) -> tuple[bool, Optional[List[str]], Optional[str]]:
    working = list(base_fragment)
    for index, (original_lines, updated_lines) in enumerate(replacement_blocks, start=1):
        if not original_lines:
            return False, None, "Replacement block missing ORIGINAL LINES; cannot merge."
        position = patch_applier.find_context(working, list(original_lines))
        if position is None:
            return False, None, f"Could not locate ORIGINAL block {index} within context fragment."
        before = working[:position]
        after = working[position + len(original_lines) :]
        working = before + list(updated_lines) + after
    return True, working, None


def merge_fragment_versions(
    base_fragment: Sequence[str],
    local_fragment: Sequence[str],
    target_fragment: Sequence[str],
) -> tuple[bool, Optional[List[str]], Optional[str]]:
    git_executable = shutil.which("git")
    if not git_executable:
        return False, None, "Git executable not found; cannot perform three-way merge."
    with tempfile.TemporaryDirectory(prefix="llm_patch_merge_") as tmpdir:
        tmp_path = Path(tmpdir)
        base_path = tmp_path / "base.txt"
        local_path = tmp_path / "local.txt"
        target_path = tmp_path / "target.txt"
        base_path.write_text(lines_to_text(base_fragment), encoding="utf-8")
        local_path.write_text(lines_to_text(local_fragment), encoding="utf-8")
        target_path.write_text(lines_to_text(target_fragment), encoding="utf-8")
        try:
            proc = subprocess.run(
                [git_executable, "merge-file", "-p", str(local_path), str(base_path), str(target_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:  # pragma: no cover - defensive
            return False, None, f"git merge-file failed: {exc}"

    merged_output = proc.stdout
    stderr_text = proc.stderr.strip()
    if proc.returncode == 0:
        merged_lines = merged_output.splitlines()
        return True, merged_lines, None
    if proc.returncode == 1:
        diagnostic = stderr_text or "Merge conflict detected while applying patch."
        return False, None, diagnostic
    diagnostic = stderr_text or f"git merge-file exited with {proc.returncode}"
    return False, None, diagnostic


def collapse_suffix_overlap(
    target_fragment: Sequence[str],
    trailing_lines: Sequence[str],
    *,
    dmp: diff_match_patch,
    suffix_collapse_max_lines: int,
    suffix_collapse_similarity: float,
) -> List[str]:
    if not target_fragment or not trailing_lines:
        return list(trailing_lines)
    max_overlap = min(
        suffix_collapse_max_lines,
        len(target_fragment),
        len(trailing_lines),
    )
    for overlap in range(max_overlap, 0, -1):
        suffix = target_fragment[-overlap:]
        prefix = trailing_lines[:overlap]
        if blocks_match(
            suffix,
            prefix,
            dmp=dmp,
            suffix_collapse_similarity=suffix_collapse_similarity,
        ):
            return list(trailing_lines[overlap:])
    return list(trailing_lines)


def blocks_match(
    suffix: Sequence[str],
    prefix: Sequence[str],
    *,
    dmp: diff_match_patch,
    suffix_collapse_similarity: float,
) -> bool:
    if not suffix and not prefix:
        return True
    if len(suffix) != len(prefix):
        return False
    if all(normalize_line(a) == normalize_line(b) for a, b in zip(suffix, prefix)):
        return True

    text_a = "\n".join(suffix)
    text_b = "\n".join(prefix)
    if not text_a and not text_b:
        return True

    diffs = dmp.diff_main(text_a, text_b)
    dmp.diff_cleanupSemantic(diffs)
    equal_chars = sum(len(chunk) for op, chunk in diffs if op == 0)
    denominator = max(len(text_a), len(text_b), 1)
    similarity = equal_chars / denominator
    return similarity >= suffix_collapse_similarity


def normalize_line(line: str) -> str:
    return " ".join(line.strip().split())


def context_fragment_lines(
    request: GuidedLoopInputs,
    *,
    detect_error_line: Callable[[str, str], Optional[int]],
    radius: int,
) -> Optional[tuple[int, List[str]]]:
    source = request.source_text or ""
    if not source:
        return None
    lines = source.splitlines()
    if not lines:
        return None
    filename = request.source_path.name if request.source_path else ""
    error_line = detect_error_line(request.error_text or "", filename)
    if error_line is None:
        start = 1
        end = min(len(lines), start + (radius * 2))
    else:
        center = max(1, min(error_line, len(lines)))
        start = max(1, center - radius)
        end = min(len(lines), center + radius)
    fragment = lines[start - 1 : end]
    return start, fragment


def lines_to_text(lines: Sequence[str]) -> str:
    if not lines:
        return ""
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text
