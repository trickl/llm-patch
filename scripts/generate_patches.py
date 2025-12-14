#!/usr/bin/env python3
"""Harvest unified diff patches for existing failing cases using Ollama models.

This script reads previously captured compiler/runtime errors under `benchmarks/generated/*`,
extracts only the first reported error per case, and asks each configured LLM to emit a
minimal unified diff that fixes that specific error. The diffs are stored alongside the
original test case under `diffs/<model>.diff`.
"""
from __future__ import annotations

import argparse
import logging
import os
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from llm_patch.clients import call_ollama
from scripts.generate_failures import LANGUAGE_CONFIGS

LOGGER = logging.getLogger(__name__)


@dataclass
class CaseInfo:
    case_dir: Path
    language: str
    before_path: Path
    first_error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate unified diffs for failing cases")
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("benchmarks/generated"),
        help="Root directory containing generation runs",
    )
    parser.add_argument(
        "--run-ids",
        type=str,
        help="Comma-separated subset of run directory names to process (default: all)",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="java,c,python,typescript",
        help="Comma-separated languages to include",
    )
    parser.add_argument(
        "--models",
        type=str,
        default="qwen2.5-coder:7b,llama3.2:3b,phi3:mini",
        help="Comma-separated Ollama models that should emit patches",
    )
    parser.add_argument(
        "--limit-per-language",
        type=int,
        default=0,
        help="Optional cap on number of cases per language (0 = no limit)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for Ollama requests",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate diffs even if a file already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List targeted cases without contacting any models",
    )
    return parser.parse_args()


def sanitize_model_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def discover_cases(
    input_root: Path,
    languages: Iterable[str],
    run_ids: Optional[Iterable[str]] = None,
) -> Dict[str, List[CaseInfo]]:
    lang_filter = {lang.strip(): True for lang in languages if lang.strip()}
    run_filter = {run.strip(): True for run in run_ids} if run_ids else None
    cases: Dict[str, List[CaseInfo]] = {lang: [] for lang in lang_filter}

    if not input_root.exists():
        raise FileNotFoundError(f"Input root {input_root} does not exist")

    for run_dir in sorted(input_root.iterdir()):
        if not run_dir.is_dir():
            continue
        if run_filter and run_dir.name not in run_filter:
            continue
        for lang_dir in sorted(run_dir.iterdir()):
            if not lang_dir.is_dir():
                continue
            lang_name = lang_dir.name
            if lang_name not in lang_filter:
                continue
            for case_dir in sorted(lang_dir.iterdir()):
                if not case_dir.is_dir():
                    continue
                before_candidates = list(case_dir.glob("before.*"))
                if not before_candidates:
                    LOGGER.warning("Skipping %s (missing before.*)", case_dir)
                    continue
                before_path = before_candidates[0]
                try:
                    first_error = extract_first_error(case_dir)
                except ValueError as exc:
                    LOGGER.warning("Skipping %s: %s", case_dir, exc)
                    continue
                cases.setdefault(lang_name, []).append(
                    CaseInfo(
                        case_dir=case_dir,
                        language=lang_name,
                        before_path=before_path,
                        first_error=first_error,
                    )
                )
    return cases


def extract_first_error(case_dir: Path) -> str:
    for filename in ("compiler_stderr.txt", "compiler_stdout.txt"):
        path = case_dir / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = [line.rstrip("\n") for line in text.splitlines()]
        chunk: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not chunk:
                if not stripped:
                    continue
                chunk.append(line)
            else:
                if not stripped:
                    break
                chunk.append(line)
        if chunk:
            return "\n".join(chunk).strip()
    raise ValueError("no compiler output found")


def build_prompt(case: CaseInfo) -> str:
    source = case.before_path.read_text(encoding="utf-8")
    error_block = case.first_error
    filename = case.before_path.name
    return textwrap.dedent(
        f"""
        You are an expert software engineer fixing a single compiler error.

        The compiler reported the first error below:
        ```text
        {error_block}
        ```

        Apply the smallest possible edit to the file `{filename}` to resolve this exact error.
        Do not attempt to fix any additional issues.

        Current file contents:
        ```
        {source}
        ```

        Respond with a valid unified diff (GNU format) that patches `{filename}`.
        The diff must include the `---` and `+++` headers and should include only a few unchanged lines for context.
        Do not add explanations or additional files.
        """
    ).strip()


def extract_diff_text(response: str) -> str:
    if "```" not in response:
        return response.strip()
    blocks: List[str] = []
    collecting = False
    buffer: List[str] = []
    for line in response.splitlines():
        marker = line.strip().startswith("```")
        if marker:
            if collecting:
                blocks.append("\n".join(buffer))
                buffer.clear()
                collecting = False
            else:
                collecting = True
            continue
        if collecting:
            buffer.append(line)
    if collecting and buffer:
        blocks.append("\n".join(buffer))
    for block in blocks:
        trimmed = block.strip()
        if trimmed.startswith("diff ") or trimmed.startswith("---") or "@@" in trimmed:
            return trimmed
    return blocks[0].strip() if blocks else response.strip()


def ensure_diffs_dir(case_dir: Path) -> Path:
    diff_dir = case_dir / "diffs"
    diff_dir.mkdir(exist_ok=True)
    return diff_dir


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]
    models = [model.strip() for model in args.models.split(",") if model.strip()]

    missing = [lang for lang in languages if lang not in LANGUAGE_CONFIGS]
    if missing:
        raise ValueError(f"Unsupported languages requested: {missing}")

    run_ids = [run.strip() for run in args.run_ids.split(",")] if args.run_ids else None
    cases = discover_cases(args.input_root, languages, run_ids)

    if args.dry_run:
        for lang, case_list in cases.items():
            limit = args.limit_per_language or len(case_list)
            LOGGER.info("[DRY RUN] %s -> %s cases", lang, min(len(case_list), limit))
            for case in case_list[:limit]:
                LOGGER.info("  %s", case.case_dir)
        return

    summary = {lang: {"processed": 0, "diffs": {model: 0 for model in models}} for lang in languages}

    for lang in languages:
        case_list = cases.get(lang, [])
        if not case_list:
            LOGGER.warning("No cases found for language %s", lang)
            continue
        limit = args.limit_per_language or len(case_list)
        LOGGER.info("=== Language %s (processing %s cases) ===", lang, min(limit, len(case_list)))
        for case in case_list[:limit]:
            summary[lang]["processed"] += 1
            prompt = build_prompt(case)
            diff_dir = ensure_diffs_dir(case.case_dir)
            for model in models:
                model_slug = sanitize_model_name(model)
                diff_path = diff_dir / f"{model_slug}.diff"
                if diff_path.exists() and not args.overwrite:
                    LOGGER.info("Skipping %s for model %s (exists)", case.case_dir.name, model)
                    continue
                LOGGER.info("Requesting patch: lang=%s case=%s model=%s", lang, case.case_dir.name, model)
                try:
                    response = call_ollama(model, prompt, temperature=args.temperature)
                except Exception as exc:  # noqa: BLE001
                    LOGGER.error("Model call failed (%s): %s", model, exc)
                    continue
                diff_text = extract_diff_text(response)
                if not diff_text:
                    LOGGER.error("Empty diff for %s via %s", case.case_dir.name, model)
                    continue
                diff_path.write_text(diff_text + "\n", encoding="utf-8")
                summary[lang]["diffs"][model] += 1

    LOGGER.info("Summary:")
    for lang, stats in summary.items():
        LOGGER.info("%s: processed %s cases", lang, stats["processed"])
        for model, count in stats["diffs"].items():
            LOGGER.info("  %s -> %s diffs", model, count)


if __name__ == "__main__":
    main()
