"""Helpers for shaping and extracting compiler error information.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.
"""

from __future__ import annotations

import re
from typing import Mapping, Match, Optional, Sequence


POINTER_SUMMARY_LANGUAGES = {"java", "c"}
ERROR_LINE_PATTERN = re.compile(r"\berror\s*:", re.IGNORECASE)
WARNING_LINE_PATTERN = re.compile(r"\bwarning\s*:", re.IGNORECASE)
NOTE_LINE_PATTERN = re.compile(r"\bnote\s*:", re.IGNORECASE)
POINTER_ALLOWED_CHARS = frozenset({"^", "~", "|", "│"})
TOKEN_PATTERN = re.compile(r"\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|\w+|[^\s\w]", re.UNICODE)


def prepare_compile_error_text(error_text: Optional[str], language: Optional[str]) -> str:
    raw_text = error_text or ""
    text = raw_text.strip()
    if not text:
        return ""
    language_key = (language or "").lower()
    if language_key not in POINTER_SUMMARY_LANGUAGES:
        return raw_text
    block = extract_first_error_block(text)
    lines = block.splitlines() if block else text.splitlines()
    summary = pointer_summary(lines, language_key)
    cleaned_lines = trim_trailing_blanks(lines)
    if summary:
        cleaned_lines = cleaned_lines + ["", summary]
    return "\n".join(cleaned_lines).strip()


def extract_first_error_block(error_text: str) -> str:
    lines = error_text.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if ERROR_LINE_PATTERN.search(line):
            start_idx = idx
            break
    if start_idx is None:
        return error_text.strip()
    end_idx = error_block_end_index(lines, start_idx)
    prefix_lines: list[str] = []
    prefix_idx = start_idx - 1
    while prefix_idx >= 0 and len(prefix_lines) < 3:
        candidate = lines[prefix_idx].strip()
        if not candidate:
            break
        if candidate.endswith(":") or candidate.lower().startswith("in "):
            prefix_lines.insert(0, lines[prefix_idx])
            prefix_idx -= 1
            continue
        break
    block_lines = prefix_lines + lines[start_idx:end_idx]
    trimmed = trim_trailing_blanks(block_lines)
    cleaned = strip_trailing_context_headers(trimmed)
    return "\n".join(cleaned).strip()


def error_block_end_index(lines: Sequence[str], start_idx: int) -> int:
    pointer_relative_idx = find_pointer_line(lines[start_idx:])
    if pointer_relative_idx is not None:
        return start_idx + pointer_relative_idx + 1
    for idx in range(start_idx + 1, len(lines)):
        line = lines[idx]
        if ERROR_LINE_PATTERN.search(line) or is_warning_or_note_line(line):
            return idx
    return len(lines)


def trim_trailing_blanks(lines: Sequence[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    while trimmed and not trimmed[0].strip():
        trimmed.pop(0)
    return trimmed


def strip_trailing_context_headers(lines: Sequence[str]) -> list[str]:
    cleaned = list(lines)
    while cleaned and cleaned[-1].strip().endswith(":") and "error" not in cleaned[-1].lower():
        cleaned.pop()
    return cleaned


def is_warning_or_note_line(line: str) -> bool:
    return bool(WARNING_LINE_PATTERN.search(line) or NOTE_LINE_PATTERN.search(line))


def pointer_summary(lines: Sequence[str], language: Optional[str]) -> Optional[str]:
    if not language or language.lower() not in POINTER_SUMMARY_LANGUAGES:
        return None
    pointer_index = find_pointer_line(lines)
    if pointer_index is None or pointer_index == 0:
        return None
    code_line = lines[pointer_index - 1]
    pointer_line = lines[pointer_index]
    return describe_pointer_context(code_line, pointer_line)


def find_pointer_line(lines: Sequence[str]) -> Optional[int]:
    allowed = POINTER_ALLOWED_CHARS
    for idx, line in enumerate(lines):
        if "^" not in line:
            continue
        normalized = line.replace("│", "|")
        stripped = normalized.strip()
        if not stripped:
            continue
        filtered = "".join(ch for ch in stripped if not ch.isspace())
        remainder = "".join(ch for ch in filtered if ch not in allowed)
        if not remainder:
            return idx
    return None


def describe_pointer_context(code_line: str, pointer_line: str) -> Optional[str]:
    pointer_expanded = pointer_line.expandtabs(4)
    caret_index = pointer_expanded.find("^")
    if caret_index == -1:
        return None
    code_expanded = code_line.expandtabs(4)
    context = token_context_descriptions(code_expanded, caret_index)
    prev_desc = context["previous"]
    current_desc = context["current"]
    summary = f"Position of error on line - previous token: {prev_desc}; current token: {current_desc}."
    marked_line = line_with_marker(code_line, caret_index)
    if not marked_line:
        return summary
    snippet_lines = [
        summary,
        "In the following snippet, the position of the error is denoted by  <ERROR> ",
        marked_line,
    ]
    return "\n".join(snippet_lines)


def line_with_marker(code_line: str, caret_index: int, marker: str = " <ERROR> ") -> str:
    tab_size = 4
    column = 0
    for idx, char in enumerate(code_line):
        if char == "\t":
            remainder = column % tab_size
            step = tab_size - remainder if remainder else tab_size
        else:
            step = 1
        if caret_index < column + step:
            return f"{code_line[:idx]}{marker}{code_line[idx:]}"
        column += step
    return f"{code_line}{marker}"


def token_context_descriptions(code_line: str, caret_index: int) -> Mapping[str, str]:
    tokens = list(TOKEN_PATTERN.finditer(code_line))
    prev_match = None
    current_match = None
    next_match = None
    for match in tokens:
        start, end = match.span()
        if end <= caret_index:
            prev_match = match
            continue
        if start <= caret_index < end:
            current_match = match
            continue
        if start > caret_index:
            next_match = match
            break
    current_desc = describe_token(current_match, default="a whitespace column")
    prev_desc = describe_token(prev_match, default="start of line")
    next_desc = describe_token(next_match, default="end of line")
    return {"current": current_desc, "previous": prev_desc, "next": next_desc}


def describe_token(match: Match[str] | None, *, default: str) -> str:
    if match is None:
        return default
    token = match.group()
    if not token:
        return default
    if token.isidentifier():
        return f"identifier {token!r}"
    if token.replace("_", "").isdigit():
        return f"number {token!r}"
    if token.startswith(("\"", "'")):
        return f"literal {token}"
    return f"symbol {token!r}"


def symbol_label(symbol: Optional[str], *, default: str) -> str:
    if symbol is None:
        return default
    if symbol == " ":
        return "a space"
    if symbol == "\t":
        return "a tab"
    if symbol == "\n":
        return "a newline"
    if symbol.isprintable():
        return repr(symbol)
    return f"U+{ord(symbol):04X}"


def detect_error_line(error_text: str, filename: str) -> Optional[int]:
    if not error_text:
        return None
    filename_pattern = re.compile(rf"{re.escape(filename)}:(\d+)") if filename else None
    generic_pattern = re.compile(r":(\d+):")
    keyword_pattern = re.compile(r"line\s+(\d+)", re.IGNORECASE)

    def extract_number(line: str) -> Optional[int]:
        match = filename_pattern.search(line) if filename_pattern else None
        if match:
            try:
                return int(match.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        match = generic_pattern.search(line)
        if match:
            try:
                return int(match.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        match = keyword_pattern.search(line)
        if match:
            try:
                return int(match.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        return None

    lines = error_text.splitlines()
    priority_lines = [
        line for line in lines if ERROR_LINE_PATTERN.search(line) or WARNING_LINE_PATTERN.search(line)
    ]
    for line in priority_lines:
        extracted = extract_number(line)
        if extracted is not None:
            return extracted

    match = filename_pattern.search(error_text) if filename_pattern else None
    if match:
        try:
            return int(match.group(1))
        except ValueError:  # pragma: no cover - defensive
            return None
    generic = generic_pattern.search(error_text)
    if generic:
        try:
            return int(generic.group(1))
        except ValueError:  # pragma: no cover - defensive
            return None
    fallback = keyword_pattern.search(error_text)
    if fallback:
        try:
            return int(fallback.group(1))
        except ValueError:  # pragma: no cover - defensive
            return None
    return None
