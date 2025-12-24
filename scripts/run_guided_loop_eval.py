#!/usr/bin/env python3
"""Run the guided-loop strategy across all stored benchmark cases.

This is intentionally a harness script (not library code). It:
- iterates benchmark case directories under benchmarks/generated/<run>/<lang>/<case>
- runs GuidedConvergenceStrategy ("guided-loop") for each case
- writes per-case result payloads next to the case (same format as scripts/run_guided_loop.py)
- emits a summary at the end grouped by language and first_error_category

Notes:
- This script requires the relevant toolchains (gcc/javac/tsc/python) to be installed,
  because guided-loop validates fixes by re-running the compile/test command.
- It also requires a running Ollama instance if using OllamaLLMClient.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from llm_patch.clients import OllamaLLMClient
from llm_patch.strategies.guided_loop import GuidedConvergenceStrategy, GuidedLoopConfig, GuidedLoopInputs


def _ensure_repo_root_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_ensure_repo_root_on_path()

from scripts.run_guided_loop import (  # noqa: E402
    extract_first_error,
    find_before_file,
    resolve_source_path,
    sanitize_model_name,
    write_after_artifact,
    write_diff_artifact,
    write_result_payload,
)


CATEGORY_LABELS: dict[int, str] = {
    1: "Purely Syntactic / Localized Structural",
    2: "Symbol Resolution / Name Lookup",
    3: "Type / Signature Mismatch",
    4: "Control-Flow / Contract / Invariant",
    5: "File-Level / Configuration / Dependency",
    6: "Cross-File / Cross-Module Semantic",
    7: "Lint / Style / Best Practice",
}


@dataclass(frozen=True)
class CaseRef:
    run_id: str
    language: str
    case_dir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run guided-loop across stored benchmark cases")
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
        help="Comma-separated run IDs to include (default: all runs)",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="",
        help="Comma-separated languages to include (default: all languages)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("LLM_PATCH_GUIDED_MODEL", "qwen2.5-coder:7b"),
        help="Ollama model identifier (default: qwen2.5-coder:7b)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature passed to Ollama",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=1,
        help="Number of primary guided-loop iterations",
    )
    parser.add_argument(
        "--refine-iterations",
        type=int,
        default=3,
        help="Additional refinement iterations",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing guided-loop results for a case",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional cap on number of cases to run (0 = no limit)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Optional delay (seconds) between cases",
    )
    return parser.parse_args()


def iter_run_ids(dataset_root: Path, run_ids_csv: str) -> list[str]:
    if run_ids_csv.strip():
        return [part.strip() for part in run_ids_csv.split(",") if part.strip()]
    return sorted([p.name for p in dataset_root.iterdir() if p.is_dir()])


def iter_cases(
    dataset_root: Path,
    run_ids: Sequence[str],
    languages: set[str] | None,
) -> Iterator[CaseRef]:
    for run_id in run_ids:
        run_dir = dataset_root / run_id
        if not run_dir.exists():
            continue
        for lang_dir in sorted([p for p in run_dir.iterdir() if p.is_dir()]):
            language = lang_dir.name
            if languages is not None and language not in languages:
                continue
            for case_dir in sorted([p for p in lang_dir.iterdir() if p.is_dir()]):
                if (case_dir / "manifest.json").exists():
                    yield CaseRef(run_id=run_id, language=language, case_dir=case_dir)


def result_path_for(case_dir: Path, model: str) -> Path:
    slug = sanitize_model_name(model)
    results_dir = case_dir / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir / f"{slug}__guided-loop.json"


def run_one_case(
    *,
    case: CaseRef,
    model: str,
    temperature: float,
    max_iterations: int,
    refine_iterations: int,
    overwrite: bool,
) -> dict:
    case_dir = case.case_dir
    manifest = json.loads((case_dir / "manifest.json").read_text(encoding="utf-8"))

    out_path = result_path_for(case_dir, model)
    if out_path.exists() and not overwrite:
        return json.loads(out_path.read_text(encoding="utf-8"))

    before_path = find_before_file(case_dir)
    before_text = before_path.read_text(encoding="utf-8")
    source_path = resolve_source_path(case_dir, before_path, manifest.get("compile_command"))
    error_text = extract_first_error(case_dir)

    request = GuidedLoopInputs(
        case_id=manifest["case_id"],
        language=manifest.get("language") or case.language,
        source_path=source_path,
        source_text=before_text,
        error_text=error_text,
        manifest=manifest,
        extra={"run_id": case.run_id},
        compile_command=manifest.get("compile_command"),
    )

    client = OllamaLLMClient(model=model, temperature=temperature)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            max_iterations=max_iterations,
            refine_sub_iterations=refine_iterations,
            interpreter_model=model,
            patch_model=model,
            temperature=temperature,
        ),
    )

    result = strategy.run(request)

    diff_path = write_diff_artifact(case_dir, source_path.name, model, result.diff_text)
    after_path = None
    if result.after_text:
        after_path = write_after_artifact(case_dir, source_path.name, model, result.after_text)
    payload_path = write_result_payload(case_dir, diff_path, after_path, model, manifest, result)
    return json.loads(payload_path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()

    dataset_root: Path = args.dataset_root
    run_ids = iter_run_ids(dataset_root, args.run_ids)
    languages = None
    if args.languages.strip():
        languages = {part.strip() for part in args.languages.split(",") if part.strip()}

    cases = list(iter_cases(dataset_root, run_ids, languages))
    if args.limit and args.limit > 0:
        cases = cases[: args.limit]

    # Aggregation
    by_lang = Counter()
    by_lang_pass = Counter()

    by_cat = Counter()
    by_cat_pass = Counter()

    by_lang_cat = defaultdict(Counter)
    by_lang_cat_pass = defaultdict(Counter)

    failures: list[dict] = []

    start = time.time()
    for idx, case in enumerate(cases, start=1):
        print(f"[{idx}/{len(cases)}] {case.run_id}/{case.language}/{case.case_dir.name}", flush=True)
        manifest_path = case.case_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        lang = manifest.get("language") or case.language
        cat = manifest.get("first_error_category")
        if not isinstance(cat, int):
            cat = 0

        try:
            payload = run_one_case(
                case=case,
                model=args.model,
                temperature=args.temperature,
                max_iterations=args.max_iterations,
                refine_iterations=args.refine_iterations,
                overwrite=args.overwrite,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  -> ERROR: {exc!r}", flush=True)
            failures.append(
                {
                    "case_id": manifest.get("case_id") or case.case_dir.name,
                    "run_id": case.run_id,
                    "language": lang,
                    "category": cat,
                    "problem_id": manifest.get("problem_id"),
                    "error": repr(exc),
                }
            )
            # Count as attempted but not passed.
            by_lang[lang] += 1
            by_cat[cat] += 1
            by_lang_cat[lang][cat] += 1
            continue

        by_lang[lang] += 1
        by_cat[cat] += 1
        by_lang_cat[lang][cat] += 1

        if payload.get("success") is True:
            print("  -> PASS", flush=True)
            by_lang_pass[lang] += 1
            by_cat_pass[cat] += 1
            by_lang_cat_pass[lang][cat] += 1
        else:
            print("  -> FAIL", flush=True)
            failures.append(
                {
                    "case_id": payload.get("case_id"),
                    "language": lang,
                    "category": cat,
                    "problem_id": payload.get("problem_id"),
                    "compile_returncode": payload.get("compile_returncode"),
                    "patch_applied": payload.get("patch_applied"),
                }
            )

        if args.sleep:
            time.sleep(args.sleep)

    elapsed = time.time() - start

    summary = {
        "model": args.model,
        "model_slug": sanitize_model_name(args.model),
        "temperature": args.temperature,
        "max_iterations": args.max_iterations,
        "refine_iterations": args.refine_iterations,
        "cases": len(cases),
        "elapsed_seconds": elapsed,
        "by_language": {
            lang: {"passed": by_lang_pass[lang], "total": by_lang[lang]} for lang in sorted(by_lang)
        },
        "by_category": {
            str(cat): {
                "label": CATEGORY_LABELS.get(cat, "Unclassified" if cat == 0 else "Unknown"),
                "passed": by_cat_pass[cat],
                "total": by_cat[cat],
            }
            for cat in sorted(by_cat)
        },
        "by_language_category": {
            lang: {
                str(cat): {
                    "label": CATEGORY_LABELS.get(cat, "Unclassified" if cat == 0 else "Unknown"),
                    "passed": by_lang_cat_pass[lang][cat],
                    "total": by_lang_cat[lang][cat],
                }
                for cat in sorted(by_lang_cat[lang])
            }
            for lang in sorted(by_lang_cat)
        },
        "failures_sample": failures[:50],
    }

    # Write a single summary file at dataset root for convenience.
    summary_dir = dataset_root / "guided_loop_summaries"
    summary_dir.mkdir(exist_ok=True)
    out_path = summary_dir / f"{sanitize_model_name(args.model)}__guided-loop__summary.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== Guided-loop summary ===")
    print(f"Model: {args.model}")
    print(f"Cases: {len(cases)}  Elapsed: {elapsed:.1f}s")

    print("\nBy language:")
    for lang in sorted(by_lang):
        total = by_lang[lang]
        passed = by_lang_pass[lang]
        print(f"  {lang:12s} {passed:4d}/{total:4d}  ({(passed/total*100.0 if total else 0.0):5.1f}%)")

    print("\nBy first_error_category:")
    for cat in sorted(by_cat):
        total = by_cat[cat]
        passed = by_cat_pass[cat]
        label = CATEGORY_LABELS.get(cat, "Unclassified" if cat == 0 else "Unknown")
        print(f"  {cat:>2} {label:45s} {passed:4d}/{total:4d}  ({(passed/total*100.0 if total else 0.0):5.1f}%)")

    print(f"\nWrote summary: {out_path}")


if __name__ == "__main__":
    main()
