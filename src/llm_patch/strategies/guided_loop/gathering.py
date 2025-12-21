"""Gather-phase helpers.

This module is intentionally "migration-only": it contains logic that was
previously embedded in `controller.py`.

The controller remains responsible for orchestration (LLM calls, events), while
this module focuses on:
- parsing strict JSON responses from the Gather phase
- enforcing deterministic-application guardrails (e.g., import/header context)
- collecting additional context snippets from the source tree
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .models import GuidedLoopInputs


def context_looks_like_import_header(context_window: str) -> bool:
    """Best-effort heuristic for whether the current context includes a file header/import area."""

    lowered = (context_window or "").lower()
    return any(
        marker in lowered
        for marker in (
            "import ",
            "#include",
            "using ",
            "package ",
            "module ",
            "require(",
            "from ",
        )
    )


def planning_mentions_import_edit(planning_text: str) -> bool:
    lowered = (planning_text or "").lower()
    return any(
        token in lowered
        for token in (
            " add the import",
            " add an import",
            "missing import",
            "import statement",
            "#include",
            "using ",
        )
    )


def enforce_gather_structural_requirements(
    *,
    gather_request: Dict[str, Any],
    planning_text: str,
    context_window: str,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Apply deterministic-application guardrails when the model under-requests context."""

    if bool(gather_request.get("needs_more_context")):
        return gather_request, None

    if not planning_text:
        return gather_request, None

    planning_mentions_import = planning_mentions_import_edit(planning_text)
    context_has_header = context_looks_like_import_header(context_window)
    if planning_mentions_import and not context_has_header:
        enforced_reason = (
            "Enforced deterministic-application rule: planning indicates an import/header edit, "
            "but the current context window does not include the file header."
        )

        raw_requests = gather_request.get("requests")
        normalized_requests: list[dict[str, Any]] = []
        if isinstance(raw_requests, list):
            normalized_requests = [req for req in raw_requests if isinstance(req, dict)]

        if not any(req.get("category") == "IMPORTS_NAMESPACE" for req in normalized_requests):
            normalized_requests.append(
                {
                    "category": "IMPORTS_NAMESPACE",
                    "target": None,
                    "reason": "Need the file header/imports to apply the planned import edit deterministically.",
                }
            )

        why_text = gather_request.get("why")
        why_text = why_text if isinstance(why_text, str) else ""
        why_text = (why_text or "").strip()
        if why_text:
            why_text = f"{why_text} {enforced_reason}"
        else:
            why_text = enforced_reason

        updated = dict(gather_request)
        updated["needs_more_context"] = True
        updated["why"] = why_text
        updated["requests"] = normalized_requests
        return updated, enforced_reason

    return gather_request, None


def parse_gather_response(
    text: str,
    *,
    allowed_categories: Sequence[str],
    allowed_target_kinds: Sequence[str],
) -> Dict[str, Any]:
    if not text:
        raise ValueError("empty response")

    allowed_categories_set = {str(item) for item in allowed_categories}
    allowed_target_kinds_set = {str(item) for item in allowed_target_kinds}

    def strip_code_fences(raw: str) -> str:
        stripped = raw.strip()
        if not stripped.startswith("```"):
            return stripped
        # Drop the opening fence line (``` or ```json) and the closing fence if present.
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 :]
        stripped = stripped.strip()
        fence_idx = stripped.rfind("```")
        if fence_idx != -1:
            stripped = stripped[:fence_idx]
        return stripped.strip()

    def extract_first_json_object(raw: str) -> str:
        # Best-effort: if the model adds prose before/after, extract the first {...} block.
        candidate = raw.strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return candidate
        return candidate[start : end + 1].strip()

    candidate = strip_code_fences(text)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        candidate = extract_first_json_object(candidate)
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("root must be a JSON object")

    def norm_key(key: str) -> str:
        return re.sub(r"[^a-z0-9]", "", key.lower())

    normalized_payload: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(key, str):
            normalized_payload[norm_key(key)] = value

    needs = normalized_payload.get("needsmorecontext")
    why = normalized_payload.get("why")
    requests = normalized_payload.get("requests")
    if not isinstance(needs, bool):
        raise ValueError("needs_more_context must be boolean")
    if why is None:
        # Backwards compatibility with older traces / models; prompt requires it but we don't hard-fail.
        why = ""
    if not isinstance(why, str):
        raise ValueError("why must be a string")
    if not isinstance(requests, list):
        raise ValueError("requests must be a list")

    cleaned_requests: list[dict[str, Any]] = []
    for idx, item in enumerate(requests):
        if not isinstance(item, dict):
            raise ValueError(f"requests[{idx}] must be an object")
        item_norm: dict[str, Any] = {}
        for key, value in item.items():
            if isinstance(key, str):
                item_norm[norm_key(key)] = value

        category = item_norm.get("category")
        if isinstance(category, str):
            category = category.strip().upper()
        if category not in allowed_categories_set:
            raise ValueError(f"requests[{idx}].category must be one of {sorted(allowed_categories_set)}")

        reason = item_norm.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"requests[{idx}].reason must be a non-empty string")

        target = item_norm.get("target")
        cleaned_target: Optional[dict[str, str]] = None
        if target is not None:
            if not isinstance(target, dict):
                raise ValueError(f"requests[{idx}].target must be object or null")
            target_norm: dict[str, Any] = {}
            for key, value in target.items():
                if isinstance(key, str):
                    target_norm[norm_key(key)] = value
            kind = target_norm.get("kind")
            name = target_norm.get("name")
            if isinstance(kind, str):
                kind = kind.strip().lower()
            if kind not in allowed_target_kinds_set:
                raise ValueError(
                    f"requests[{idx}].target.kind must be one of {sorted(allowed_target_kinds_set)}"
                )
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"requests[{idx}].target.name must be a non-empty string")
            token = name.strip()
            if any(ch.isspace() for ch in token):
                raise ValueError(f"requests[{idx}].target.name must be a single token")
            cleaned_target = {"kind": str(kind), "name": token}

        cleaned_requests.append(
            {
                "category": str(category),
                "target": cleaned_target,
                "reason": reason.strip(),
            }
        )

    return {
        "needs_more_context": needs,
        "why": why.strip(),
        "requests": cleaned_requests,
    }


def collect_gathered_context(
    request: GuidedLoopInputs,
    gather_request: Mapping[str, Any],
    *,
    detect_error_line: Callable[[str, str], Optional[int]],
    header_lines: int = 20,
    usage_radius: int = 3,
    scope_radius: int = 20,
    max_hits: int = 5,
    max_other_files: int = 3,
    max_file_chars: int = 120_000,
) -> tuple[str, Dict[str, Any]]:
    needs = gather_request.get("needs_more_context") is True
    why = gather_request.get("why") if isinstance(gather_request.get("why"), str) else ""
    requests = gather_request.get("requests") if isinstance(gather_request.get("requests"), list) else []
    if not needs or not requests:
        details: Dict[str, Any] = {"note": "no additional context requested"}
        if why.strip():
            details["why"] = why.strip()
        return "", details

    error_line = detect_error_line(request.error_text or "", request.source_path.name)
    all_lines = request.source_text.splitlines()
    total_lines = len(all_lines)

    def numbered_window(start_line: int, end_line: int) -> str:
        start = max(1, start_line)
        end = min(total_lines, end_line)
        window = []
        for lineno in range(start, end + 1):
            raw = all_lines[lineno - 1]
            window.append(f"{lineno:4d} | {raw}")
        return "\n".join(window).rstrip()

    # Best-effort read of neighboring files for cross-file name resolution.
    other_files: list[tuple[str, str]] = []
    if request.source_path and request.source_path.exists():
        parent = request.source_path.parent
        ext = request.source_path.suffix.lower()
        candidates: list[Path] = []
        if ext in {".c", ".cc", ".cpp", ".cxx"}:
            candidates.extend(sorted(parent.glob("*.h")))
            candidates.extend(sorted(parent.glob(f"*{ext}")))
        elif ext in {".py"}:
            candidates.extend(sorted(parent.glob("*.py")))
        elif ext in {".ts", ".tsx", ".js", ".jsx"}:
            candidates.extend(sorted(parent.glob("*.ts")))
            candidates.extend(sorted(parent.glob("*.tsx")))
            candidates.extend(sorted(parent.glob("*.js")))
            candidates.extend(sorted(parent.glob("*.jsx")))
        elif ext in {".java"}:
            candidates.extend(sorted(parent.glob("*.java")))
        else:
            candidates.extend(sorted(parent.iterdir()))

        seen = set()
        for path in candidates:
            if len(other_files) >= max_other_files:
                break
            if not path.is_file() or path == request.source_path:
                continue
            if path.name in seen:
                continue
            seen.add(path.name)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not text.strip():
                continue
            other_files.append((path.name, text[:max_file_chars]))

    details: Dict[str, Any] = {
        "errorLine": error_line,
        "totalLines": total_lines,
        "why": why.strip(),
        "requested": [
            {
                "category": item.get("category"),
                "target": item.get("target"),
                "reason": item.get("reason"),
            }
            for item in requests
            if isinstance(item, Mapping)
        ],
        "scannedOtherFiles": [name for name, _ in other_files],
    }

    sections: list[str] = []

    def infer_token_from_error_text() -> Optional[str]:
        # Prefer the enriched pointer summary inserted by prepare_compile_error_text().
        text = request.error_text or ""
        if not text:
            return None
        match = re.search(r"current token:\s*identifier\s+'([^']+)'", text)
        if match:
            candidate = match.group(1).strip()
            if candidate and not any(ch.isspace() for ch in candidate):
                return candidate
        match = re.search(r"current token:\s*identifier\s+\"([^\"]+)\"", text)
        if match:
            candidate = match.group(1).strip()
            if candidate and not any(ch.isspace() for ch in candidate):
                return candidate
        return None

    # Determine token of interest (single token supported for now).
    token: Optional[str] = None
    for item in requests:
        if not isinstance(item, Mapping):
            continue
        target = item.get("target")
        if isinstance(target, Mapping):
            name = target.get("name")
            if isinstance(name, str) and name.strip():
                token = name.strip()
                break

    if token is None:
        token = infer_token_from_error_text()

    requested_categories = {
        item.get("category")
        for item in requests
        if isinstance(item, Mapping) and isinstance(item.get("category"), str)
    }

    if "FILE_CONTEXT" in requested_categories:
        sections.append(
            "FILE_CONTEXT:\n" + f"file={request.source_path.name}\n" + f"lines={total_lines}\n"
        )

    if "IMPORTS_NAMESPACE" in requested_categories:
        header_end = min(header_lines, total_lines)
        sections.append("IMPORTS_NAMESPACE (file header):\n" + numbered_window(1, header_end))

    if "ENCLOSING_SCOPE" in requested_categories and error_line:
        sections.append(
            "ENCLOSING_SCOPE (around error line):\n"
            + numbered_window(error_line - scope_radius, error_line + scope_radius)
        )

    def find_usages_in_text(text: str, *, file_label: str) -> list[str]:
        if not token:
            return []
        lines = text.splitlines()
        hits: list[str] = []
        for idx, line in enumerate(lines, start=1):
            if token in line:
                start = max(1, idx - usage_radius)
                end = min(len(lines), idx + usage_radius)
                excerpt = []
                excerpt.append(f"{file_label}:{idx}:")
                for lineno in range(start, end + 1):
                    excerpt.append(f"{lineno:4d} | {lines[lineno - 1]}")
                hits.append("\n".join(excerpt))
                if len(hits) >= max_hits:
                    break
        return hits

    if token and "USAGE_CONTEXT" in requested_categories:
        hits = find_usages_in_text(request.source_text, file_label=request.source_path.name)
        for name, text in other_files:
            if len(hits) >= max_hits:
                break
            hits.extend(find_usages_in_text(text, file_label=name))
            hits = hits[:max_hits]
        if hits:
            sections.append("USAGE_CONTEXT:\n" + "\n\n".join(hits))
        else:
            sections.append(f"USAGE_CONTEXT:\n(no occurrences of '{token}' found)")

    def find_declarations_in_text(text: str, *, file_label: str) -> list[str]:
        if not token:
            return []
        patterns = [
            re.compile(rf"\b(class|struct|enum|interface)\s+{re.escape(token)}\b"),
            re.compile(rf"\bdef\s+{re.escape(token)}\b"),
            re.compile(rf"\bfunction\s+{re.escape(token)}\b"),
            re.compile(rf"\btypedef\b.*\b{re.escape(token)}\b"),
            re.compile(rf"\b{re.escape(token)}\s*\("),
        ]
        lines = text.splitlines()
        hits: list[str] = []
        for idx, line in enumerate(lines, start=1):
            if any(p.search(line) for p in patterns):
                hits.append(f"{file_label}:{idx}: {line.strip()}")
                if len(hits) >= max_hits:
                    break
        return hits

    if token and "DECLARATION" in requested_categories:
        hits = find_declarations_in_text(request.source_text, file_label=request.source_path.name)
        for name, text in other_files:
            if len(hits) >= max_hits:
                break
            hits.extend(find_declarations_in_text(text, file_label=name))
            hits = hits[:max_hits]
        if hits:
            sections.append("DECLARATION:\n" + "\n".join(hits))
        else:
            sections.append(f"DECLARATION:\n(no likely declarations of '{token}' found)")

    if token and "TYPE_CONTEXT" in requested_categories:
        # For now, reuse declaration heuristics; refine later per-language.
        hits = find_declarations_in_text(request.source_text, file_label=request.source_path.name)
        for name, text in other_files:
            if len(hits) >= max_hits:
                break
            hits.extend(find_declarations_in_text(text, file_label=name))
            hits = hits[:max_hits]
        if hits:
            sections.append("TYPE_CONTEXT:\n" + "\n".join(hits))
        else:
            sections.append(f"TYPE_CONTEXT:\n(no type context found for '{token}')")

    combined = "\n\n".join(section for section in sections if section.strip()).strip()
    details["token"] = token
    details["sections"] = [section.split("\n", 1)[0] for section in sections]
    return combined, details
