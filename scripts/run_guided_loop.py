#!/usr/bin/env python3
"""Execute the Guided Convergence Loop strategy for a single failure case."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Optional, Sequence
from llm_patch.clients import OllamaLLMClient
from llm_patch.strategies.guided_loop import GuidedConvergenceStrategy, GuidedLoopConfig, GuidedLoopInputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Guided Loop strategy for a stored failure case")
    parser.add_argument("case_id", help="Case directory name, e.g. java-qwen2.5-coder:7b-1d980869")
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("benchmarks/generated"),
        help="Root directory that contains generated benchmark runs",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-coder:7b",
        help="Ollama model identifier for the Interpret phase",
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
        help="Number of primary guided-loop iterations to plan up front",
    )
    parser.add_argument(
        "--refine-iterations",
        type=int,
        default=3,
        help="Additional refinement iterations to allow after each critique",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_dir = find_case_dir(args.dataset_root, args.case_id)
    manifest = json.loads((case_dir / "manifest.json").read_text(encoding="utf-8"))
    before_path = find_before_file(case_dir)
    before_text = before_path.read_text(encoding="utf-8")
    source_path = resolve_source_path(case_dir, before_path, manifest.get("compile_command"))
    error_text = extract_first_error(case_dir)

    request = GuidedLoopInputs(
        case_id=manifest["case_id"],
        language=manifest["language"],
        source_path=source_path,
        source_text=before_text,
        error_text=error_text,
        manifest=manifest,
        extra={"run_id": case_dir.parents[2].name if len(case_dir.parents) >= 2 else "unknown"},
        compile_command=manifest.get("compile_command"),
    )
    client = OllamaLLMClient(model=args.model, temperature=args.temperature)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            max_iterations=args.max_iterations,
            refine_sub_iterations=args.refine_iterations,
            interpreter_model=args.model,
            patch_model=args.model,
            temperature=args.temperature,
        ),
    )
    result = strategy.run(request)
    if not result.trace:
        raise RuntimeError("Guided loop did not return a trace")

    diff_path = write_diff_artifact(case_dir, source_path.name, args.model, result.diff_text)
    after_path = None
    if result.after_text:
        after_path = write_after_artifact(case_dir, source_path.name, args.model, result.after_text)
    result_path = write_result_payload(case_dir, diff_path, after_path, args.model, manifest, result)
    print(f"Guided loop trace saved to {result_path}")


def find_case_dir(dataset_root: Path, case_id: str) -> Path:
    matches = sorted(dataset_root.glob(f"**/{case_id}"))
    for candidate in matches:
        if candidate.is_dir() and candidate.name == case_id:
            return candidate
    raise FileNotFoundError(f"Could not locate case directory for {case_id} under {dataset_root}")


def find_before_file(case_dir: Path) -> Path:
    for candidate in case_dir.glob("before.*"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Missing before.* file in {case_dir}")


def resolve_source_path(case_dir: Path, before_path: Path, compile_command: Sequence[str] | None) -> Path:
    candidate = _select_manifest_source_name(compile_command, before_path.suffix)
    if not candidate:
        return before_path
    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        candidate_path = Path(candidate_path.name)
    return case_dir / candidate_path


def _select_manifest_source_name(compile_command: Sequence[str] | None, default_suffix: str) -> Optional[str]:
    if not compile_command:
        return None
    expected_suffix = default_suffix.lower()
    for token in compile_command:
        if not token or token.startswith("-"):
            continue
        candidate_suffix = Path(token).suffix.lower()
        if expected_suffix and candidate_suffix != expected_suffix:
            continue
        if not candidate_suffix and expected_suffix:
            continue
        return token
    return None


def extract_first_error(case_dir: Path) -> str:
    for filename in ("compiler_stderr.txt", "compiler_stdout.txt"):
        path = case_dir / filename
        if not path.exists():
            continue
        lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
        chunk: list[str] = []
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
    return ""


def sanitize_model_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def write_diff_artifact(case_dir: Path, filename: str, model: str, diff_text: str | None) -> Path:
    diff_dir = case_dir / "diffs"
    diff_dir.mkdir(exist_ok=True)
    slug = sanitize_model_name(model)
    diff_path = diff_dir / f"{slug}__guided-loop.diff"
    if diff_text:
        payload = diff_text.rstrip("\n") + "\n"
    else:
        payload = (
            f"diff --git a/{filename} b/{filename}\n"
            f"--- a/{filename}\n"
            f"+++ b/{filename}\n"
            "@@\n"
            "-// guided loop placeholder\n"
            "+// guided loop placeholder\n"
        )
    diff_path.write_text(payload, encoding="utf-8")
    return diff_path


def write_after_artifact(case_dir: Path, filename: str, model: str, after_text: str) -> Path:
    after_dir = case_dir / "after"
    after_dir.mkdir(exist_ok=True)
    slug = sanitize_model_name(model)
    after_path = after_dir / f"{slug}__guided-loop__{filename}"
    after_path.write_text(after_text, encoding="utf-8")
    return after_path


def write_result_payload(
    case_dir: Path,
    diff_path: Path | None,
    after_path: Path | None,
    model: str,
    manifest: dict,
    result,
) -> Path:
    slug = sanitize_model_name(model)
    results_dir = case_dir / "results"
    results_dir.mkdir(exist_ok=True)
    payload_path = results_dir / f"{slug}__guided-loop.json"
    trace_dict = result.trace.to_dict() if result.trace else None
    diff_stats = summarize_diff_text(result.diff_text)

    compiler_stderr_before_path = case_dir / "compiler_stderr.txt"
    compiler_stdout_before_path = case_dir / "compiler_stdout.txt"

    stderr_before = (
        compiler_stderr_before_path.read_text(encoding="utf-8")
        if compiler_stderr_before_path.exists()
        else ""
    )
    stdout_before = (
        compiler_stdout_before_path.read_text(encoding="utf-8")
        if compiler_stdout_before_path.exists()
        else ""
    )

    errors_before = count_compiler_errors(stderr_before)
    errors_after = count_compiler_errors(result.compile_stderr)
    first_error_removed = bool(errors_before) and errors_after == 0 if errors_after is not None else False
    payload = {
        "case_id": manifest["case_id"],
        "language": manifest["language"],
        "model_slug": slug,
        "algorithm": "guided-loop",
        "diff_path": diff_path.relative_to(case_dir).as_posix() if diff_path else None,
        "after_path": after_path.relative_to(case_dir).as_posix() if after_path else None,
        "patch_applied": result.applied,
        "patch_diagnostics": result.patch_diagnostics or "",
        "compile_returncode": result.compile_returncode,
        "errors_before": errors_before,
        "errors_after": errors_after,
        "first_error_removed": first_error_removed,
        "added_lines": diff_stats["added_lines"],
        "removed_lines": diff_stats["removed_lines"],
        "hunks": diff_stats["hunks"],
        "delete_only": diff_stats["delete_only"],
        "success": result.success,
        "notes": result.notes,
        "stderr_before": stderr_before,
        "stdout_before": stdout_before,
        "stderr_after": result.compile_stderr,
        "stdout_after": result.compile_stdout,
        "strategy_trace": trace_dict,
    }
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload_path


_JAVAC_SUMMARY_RE = re.compile(r"(?m)^\s*(?P<count>\d+)\s+errors?\s*$")
_FILELINE_ERROR_RE = re.compile(r"(?m)^.+?:\d+?:\s+error:\s+")


def count_compiler_errors(text: str | None) -> int | None:
    """Best-effort count of compiler errors.

    Historically we counted non-empty stderr lines, which inflates counts for compilers
    that emit multi-line diagnostics per error (e.g. javac).

    This function prefers:
      1) javac-style summary line: "N errors" / "1 error"
      2) file:line: error: ... style lines

    Falls back to counting non-empty lines if we cannot infer an error count.
    """

    if text is None:
        return None

    if not text.strip():
        return 0

    summary = _JAVAC_SUMMARY_RE.search(text)
    if summary:
        try:
            return int(summary.group("count"))
        except ValueError:
            pass

    matches = list(_FILELINE_ERROR_RE.finditer(text))
    if matches:
        return len(matches)

    # Conservative fallback: count non-empty lines.
    return sum(1 for line in text.splitlines() if line.strip())


def summarize_diff_text(diff_text: str | None) -> dict:
    if not diff_text:
        return {"added_lines": 0, "removed_lines": 0, "hunks": 0, "delete_only": False}
    added = removed = hunks = 0
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            hunks += 1
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return {
        "added_lines": added,
        "removed_lines": removed,
        "hunks": hunks,
        "delete_only": added == 0 and removed > 0,
    }


if __name__ == "__main__":
    main()
