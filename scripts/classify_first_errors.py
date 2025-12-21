#!/usr/bin/env python3
"""Classify the first compile/test error for each benchmark case.

This script scans benchmark case directories (e.g. benchmarks/generated/<run>/<lang>/<case>)
for compiler stderr/stdout, extracts the *first* relevant error message, asks a local
Ollama model (default: gpt-oss:20b) to categorize it into one of 7 buckets, and stores
that categorization into the case metadata.

By default we persist classification onto `manifest.json` (non-destructively, by adding
new keys). This makes the data easy to consume later in the Reviewer UI.

Usage:
  python scripts/classify_first_errors.py --run-ids 20251213T225259Z --languages c,java

Prereqs:
  - `ollama` running locally (default http://localhost:11434)
  - model pulled: `ollama pull gpt-oss:20b`
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from llm_patch.clients.ollama import call_ollama


CATEGORY_RUBRIC = """You are classifying the *first* compiler/runtime error message for a single file into exactly one of the categories below.

Return ONLY a single digit: 1, 2, 3, 4, 5, 6, or 7. No other text.

Categories:
1) Purely Syntactic / Localized Structural Errors
- Missing punctuation, malformed constructs, bracket/quote mismatch, incomplete statements.

2) Symbol Resolution / Name Lookup Errors
- Unknown identifiers, missing imports/includes, missing declarations.

3) Type / Signature Mismatch Errors
- Type incompatibility, overload mismatch, generic/template mismatch.

4) Control-Flow / Contract / Invariant Violations
- Must return on all paths, uninitialized variable, unreachable code, async/await misuse, rule violations.

5) File-Level / Configuration / Dependency Errors
- Missing libraries, module resolution, compiler flags/tooling config issues.

6) Cross-File / Cross-Module Semantic Breakages
- API/interface mismatch across files/modules, schema/DTO incompatibilities.

7) Lint / Style / Best Practice Violations
- Unused imports, formatting, naming conventions, warnings-only policy violations.
""".strip()


ERROR_PATTERNS = [
    # gcc/clang
    re.compile(r"^.+?:\d+:\d+:\s+error:\s+.+$"),
    re.compile(r"^.+?:\d+:\d+:\s+fatal\s+error:\s+.+$"),
    # javac
    re.compile(r"^.+?:\d+:\s+error:\s+.+$"),
    re.compile(r"^error:\s+.+$"),
    # tsc
    re.compile(r"^.+\(\d+,\d+\):\s+error\s+TS\d+:\s+.+$"),
    re.compile(r"^error\s+TS\d+:\s+.+$"),
]

PYTHON_EXCEPTION_RE = re.compile(
    r"^(SyntaxError|IndentationError|TabError|TypeError|NameError|ImportError|ModuleNotFoundError|AttributeError|ValueError|RuntimeError|Exception):\s+.+$"
)


@dataclass(frozen=True)
class ClassificationResult:
    category: int
    raw_response: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify first errors in benchmark cases using an Ollama model")
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("benchmarks/generated"),
        help="Dataset root containing run folders (default: benchmarks/generated)",
    )
    parser.add_argument(
        "--run-ids",
        type=str,
        default="",
        help="Comma-separated run IDs to include (default: all runs under dataset-root)",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="",
        help="Comma-separated language filter (default: all languages)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("LLM_PATCH_CLASSIFIER_MODEL", "gpt-oss:20b"),
        help="Ollama model to use (default: gpt-oss:20b)",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        help="Ollama host URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing classification fields in manifest.json",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional cap on number of cases to classify (0 = no limit)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and extract first errors but do not call the LLM or write files",
    )
    return parser.parse_args()


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def iter_case_dirs(dataset_root: Path, run_ids: list[str] | None, languages: list[str] | None) -> Iterable[Path]:
    run_dirs = [dataset_root / run_id for run_id in run_ids] if run_ids else sorted(p for p in dataset_root.iterdir() if p.is_dir())
    for run_dir in run_dirs:
        if not run_dir.exists() or not run_dir.is_dir():
            continue
        for lang_dir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
            if languages and lang_dir.name not in languages:
                continue
            for case_dir in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
                yield case_dir


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def extract_first_error(stderr_text: str, stdout_text: str, language: str | None = None) -> str:
    # Prefer stderr; then stdout.
    blobs = [stderr_text, stdout_text]

    # 1) Pattern-based extraction for common compiler formats.
    for blob in blobs:
        for line in blob.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            for pattern in ERROR_PATTERNS:
                if pattern.match(stripped):
                    return stripped

    # 2) Python tracebacks: the last non-empty line that looks like an exception.
    if language == "python":
        lines = [ln.strip() for ln in (stderr_text + "\n" + stdout_text).splitlines() if ln.strip()]
        for line in reversed(lines):
            if PYTHON_EXCEPTION_RE.match(line):
                return line

    # 3) General heuristic: first line containing 'error'/'exception' keywords.
    keywords = ("error", "exception", "traceback", "fatal", "syntaxerror", "indentationerror")
    for blob in blobs:
        for line in blob.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if any(k in lower for k in keywords):
                return stripped

    # 4) Fallback: first non-empty line.
    for blob in blobs:
        for line in blob.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped

    return ""


def build_prompt(*, language: str, error_message: str) -> str:
    return (
        f"{CATEGORY_RUBRIC}\n\n"
        f"Language: {language}\n"
        f"First error message:\n{error_message}\n"
    )


def parse_category(response_text: str) -> Optional[int]:
    text = response_text.strip()
    # Allow the model to accidentally include whitespace/newlines.
    match = re.search(r"\b([1-7])\b", text)
    if not match:
        return None
    value = int(match.group(1))
    if 1 <= value <= 7:
        return value
    return None


def classify_error(*, model: str, host: str, language: str, error_message: str) -> ClassificationResult:
    prompt = build_prompt(language=language, error_message=error_message)
    raw = call_ollama(model, prompt, temperature=0.0, host=host)
    category = parse_category(raw)
    if category is not None:
        return ClassificationResult(category=category, raw_response=raw)

    # One retry with an even stricter instruction.
    retry_prompt = (
        f"Return ONLY one character: 1,2,3,4,5,6,or 7. No punctuation, no words.\n\n"
        f"Error message:\n{error_message}\n\n"
        f"Rubric (choose exactly one):\n{CATEGORY_RUBRIC}\n"
    )
    raw2 = call_ollama(model, retry_prompt, temperature=0.0, host=host)
    category2 = parse_category(raw2)
    if category2 is None:
        raise ValueError(f"Classifier did not return a category digit. Response was: {raw2!r}")
    return ClassificationResult(category=category2, raw_response=raw2)


def update_manifest(
    manifest_path: Path,
    *,
    error_message: str,
    category: int,
    model: str,
    overwrite: bool,
) -> bool:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    key_category = "first_error_category"
    key_message = "first_error_message"

    if not overwrite and (key_category in manifest or key_message in manifest):
        return False

    manifest[key_message] = error_message
    manifest[key_category] = int(category)
    manifest["first_error_category_model"] = model
    manifest["first_error_category_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["first_error_category_version"] = "v1"

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def main() -> None:
    args = parse_args()

    run_ids = parse_csv(args.run_ids) if args.run_ids else None
    languages = parse_csv(args.languages) if args.languages else None

    total = 0
    skipped = 0
    updated = 0
    failed = 0

    for case_dir in iter_case_dirs(args.dataset_root, run_ids, languages):
        if args.limit and total >= args.limit:
            break

        manifest_path = case_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        language = str(manifest.get("language") or case_dir.parent.name)
        stderr_text = load_text(case_dir / "compiler_stderr.txt")
        stdout_text = load_text(case_dir / "compiler_stdout.txt")
        first_error = extract_first_error(stderr_text, stdout_text, language=language)
        if not first_error:
            continue

        total += 1

        # Skip if already classified.
        if not args.overwrite and (
            "first_error_category" in manifest or "first_error_message" in manifest
        ):
            skipped += 1
            continue

        if args.dry_run:
            print(f"[dry-run] {case_dir}: {language} :: {first_error}")
            continue

        try:
            result = classify_error(
                model=args.model,
                host=args.ollama_host,
                language=language,
                error_message=first_error,
            )
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"[fail] {case_dir.name}: {exc}")
            continue

        wrote = update_manifest(
            manifest_path,
            error_message=first_error,
            category=result.category,
            model=args.model,
            overwrite=args.overwrite,
        )
        if wrote:
            updated += 1
            print(f"[ok] {case_dir.name}: category={result.category} :: {first_error}")
        else:
            skipped += 1

    print(
        "\n".join(
            [
                "=== First-error classification summary ===",
                f"dataset_root: {args.dataset_root}",
                f"model: {args.model}",
                f"total_seen: {total}",
                f"updated: {updated}",
                f"skipped: {skipped}",
                f"failed: {failed}",
            ]
        )
    )


if __name__ == "__main__":
    main()
