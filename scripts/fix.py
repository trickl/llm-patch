#!/usr/bin/env python3
"""Outer-loop fixer that repeatedly invokes the existing guided-loop runner.

This module is intentionally a thin orchestrator:
- It does not change guided-loop prompts/stages.
- It repeatedly runs the existing scripts/run_guided_loop.py, updating the
  case workspace between cycles.

STDOUT: final unified diff only
STDERR: diagnostics / per-cycle runner output
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CycleOutcome:
    case_dir: Path
    result_path: Path
    diff_path: Optional[Path]
    after_path: Optional[Path]
    errors_before: Optional[int]
    errors_after: Optional[int]
    compile_returncode: Optional[int]
    patch_applied: Optional[bool]
    first_error_removed: Optional[bool]


def sanitize_model_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the existing guided-loop iteratively until compilation succeeds or progress stops."
        )
    )

    parser.add_argument(
        "case_id",
        help="Case directory name, e.g. java-qwen2.5-coder:7b-52264466",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
        help="Root directory that contains generated benchmark runs",
    )

    # Guided-loop parameters (optional; default values match scripts/run_guided_loop.py).
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-iterations", type=int, default=1)
    parser.add_argument("--refine-iterations", type=int, default=3)

    # Outer loop control.
    parser.add_argument(
        "--outer-cycles",
        type=int,
        default=10,
        help="Maximum number of guided-loop cycles to run",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path("/workspace"),
        help="Writable directory used for scratch copies (inside Docker: /workspace)",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the scratch directory for inspection",
    )

    return parser.parse_args(argv)


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


def _write_text(path: Path, text: str | None) -> None:
    if text is None:
        return
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_guided_loop_result(case_dir: Path, model: str) -> Path:
    slug = sanitize_model_name(model)
    candidate = case_dir / "results" / f"{slug}__guided-loop.json"
    if not candidate.exists():
        raise FileNotFoundError(f"Expected guided-loop result not found: {candidate}")
    return candidate


def run_guided_loop_once(
    *,
    app_root: Path,
    scratch_dataset_root: Path,
    case_id: str,
    model: str,
    temperature: float,
    max_iterations: int,
    refine_iterations: int,
) -> CycleOutcome:
    # Run the existing script. Capture its stdout to avoid contaminating our stdout.
    cmd = [
        sys.executable,
        str(app_root / "scripts" / "run_guided_loop.py"),
        case_id,
        "--dataset-root",
        str(scratch_dataset_root),
        "--model",
        model,
        "--temperature",
        str(temperature),
        "--max-iterations",
        str(max_iterations),
        "--refine-iterations",
        str(refine_iterations),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    # Forward guided-loop runner output to STDERR for inspection.
    if proc.stdout:
        sys.stderr.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stderr.write("\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")

    if proc.returncode != 0:
        raise RuntimeError(f"guided-loop runner failed with exit code {proc.returncode}")

    # Locate the case directory inside the scratch dataset and parse the result payload.
    case_dir = find_case_dir(scratch_dataset_root, case_id)
    result_path = _latest_guided_loop_result(case_dir, model)
    payload = _read_json(result_path)

    diff_path = payload.get("diff_path")
    after_path = payload.get("after_path")

    diff_abs = (case_dir / diff_path) if diff_path else None
    after_abs = (case_dir / after_path) if after_path else None

    return CycleOutcome(
        case_dir=case_dir,
        result_path=result_path,
        diff_path=diff_abs,
        after_path=after_abs,
        errors_before=payload.get("errors_before"),
        errors_after=payload.get("errors_after"),
        compile_returncode=payload.get("compile_returncode"),
        patch_applied=payload.get("patch_applied"),
        first_error_removed=payload.get("first_error_removed"),
    )


def apply_cycle_state_update(*, case_dir: Path, outcome: CycleOutcome) -> None:
    """Update the scratch case inputs so the next cycle targets the next error.

    - Replace before.* with after text from this cycle (if available).
    - Replace compiler_stderr.txt/compiler_stdout.txt with the recorded post-compile streams.

    This keeps behavior aligned with scripts/run_guided_loop.py which always reads
    before.* and the first error chunk from compiler_*.txt.
    """

    payload = _read_json(outcome.result_path)

    if outcome.after_path and outcome.after_path.exists():
        before_path = find_before_file(case_dir)
        before_path.write_text(outcome.after_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Update error streams for next iteration's "first error" extraction.
    _write_text(case_dir / "compiler_stderr.txt", payload.get("stderr_after"))
    _write_text(case_dir / "compiler_stdout.txt", payload.get("stdout_after"))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv) if argv is not None else sys.argv[1:])

    app_root = Path(__file__).resolve().parents[1]

    # Create a scratch dataset root and copy the case directory into it.
    case_dir = find_case_dir(args.dataset_root, args.case_id)
    rel_case_dir = case_dir.relative_to(args.dataset_root)

    if not args.workdir.exists():
        raise FileNotFoundError(f"workdir does not exist: {args.workdir}")

    scratch_parent = args.workdir / "llm-patch"
    scratch_parent.mkdir(parents=True, exist_ok=True)

    tmpdir_obj = tempfile.TemporaryDirectory(prefix="fix-", dir=str(scratch_parent))
    scratch_dataset_root = Path(tmpdir_obj.name) / "dataset"
    scratch_dataset_root.mkdir(parents=True, exist_ok=True)

    scratch_case_dir = scratch_dataset_root / rel_case_dir
    scratch_case_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(case_dir, scratch_case_dir)

    last_errors_after: Optional[int] = None
    final_outcome: Optional[CycleOutcome] = None
    diff_text: Optional[str] = None

    try:
        for cycle in range(1, args.outer_cycles + 1):
            final_outcome = run_guided_loop_once(
                app_root=app_root,
                scratch_dataset_root=scratch_dataset_root,
                case_id=args.case_id,
                model=args.model,
                temperature=args.temperature,
                max_iterations=args.max_iterations,
                refine_iterations=args.refine_iterations,
            )

            # Success condition: compilation succeeds.
            if final_outcome.compile_returncode == 0:
                break

            # No-progress condition: errors_after did not decrease.
            if final_outcome.errors_after is not None:
                if last_errors_after is not None and final_outcome.errors_after >= last_errors_after:
                    break
                last_errors_after = final_outcome.errors_after

            # Prepare inputs for next cycle.
            apply_cycle_state_update(case_dir=final_outcome.case_dir, outcome=final_outcome)

        if not final_outcome:
            sys.stderr.write("No guided-loop cycles were executed.\n")
            return 1

        if not final_outcome.diff_path or not final_outcome.diff_path.exists():
            sys.stderr.write("Final diff artifact not found.\n")
            return 1

        # Read diff before cleanup.
        diff_text = final_outcome.diff_path.read_text(encoding="utf-8")
    finally:
        if args.keep_workdir:
            sys.stderr.write(f"Scratch dataset preserved at: {scratch_dataset_root}\n")
        else:
            tmpdir_obj.cleanup()

    if diff_text is None:
        return 1

    # Output: unified diff only.
    sys.stdout.write(diff_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
