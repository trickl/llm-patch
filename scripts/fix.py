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
import difflib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
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
    trace_saved_message: Optional[str]
    cycle_seconds: Optional[float]
    llm_prompt_tokens: Optional[int]
    llm_completion_tokens: Optional[int]
    llm_requests: Optional[int]


def _csv_event(event: str, **fields: object) -> str:
    """Render a compact comma-delimited event line for STDERR.

    Example:
      COMPLETE_SUCCESS,compile_returncode=0,errors_before=9,errors_after=0,cycles=8
    """

    parts = [event]
    for key, value in fields.items():
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return ",".join(parts) + "\n"


def sanitize_model_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the existing guided-loop iteratively until compilation succeeds or progress stops."
        )
    )

    parser.add_argument(
        "case",
        help=(
            "Case identifier. Either the case directory name (e.g. java-qwen2.5-coder:7b-52264466) "
            "or a path to a case directory containing manifest.json and before.*. "
            "If a file path (or a filename under /project) is provided, a temporary case will be generated."
        ),
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("benchmarks/generated"),
        help=(
            "Root directory that contains generated benchmark runs. Required for benchmark-style case IDs; "
            "ignored when <case> is a file path (a temporary case is generated instead)."
        ),
    )

    # Production-style single-file mode helpers.
    parser.add_argument(
        "--compile",
        default=None,
        help=(
            "Compile/check command to run inside a temporary directory, e.g. 'javac ExpressionEvaluator.java' "
            "or 'python -m py_compile main.py'. If omitted for a single-file input, we try a simple default "
            "based on file extension (.py/.java)."
        ),
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language override for single-file mode (otherwise inferred from file extension).",
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
        default=50,
        help=(
            "Maximum number of guided-loop cycles to run. Each cycle attempts to fix the current FIRST error "
            "(based on compiler output) and updates the case inputs for the next cycle."
        ),
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


def resolve_case_dir(dataset_root: Path, case: str) -> Path:
    """Resolve a case either by ID (directory name) or by direct path."""
    candidate = Path(case)
    if candidate.exists() and candidate.is_dir():
        return candidate.resolve()
    return find_case_dir(dataset_root, case)


def _infer_language_from_suffix(suffix: str) -> Optional[str]:
    s = suffix.lower()
    return {
        ".py": "python",
        ".java": "java",
    }.get(s)


def _default_compile_command_for_file(filename: str, language: str) -> Optional[list[str]]:
    # These commands match the guided-loop compilation model: compile in a temp dir with only this file.
    if language == "python":
        return [sys.executable, "-m", "py_compile", filename]
    if language == "java":
        return ["javac", filename]
    return None


def _compile_target_paths(source_name: str, command: list[str]) -> list[Path]:
    """Mirror llm_patch.strategies.guided_loop.compilation.compile_target_paths."""
    source_suffix = Path(source_name).suffix.lower()
    targets: list[Path] = []
    for token in command:
        if not token or token.startswith("-"):
            continue
        candidate = Path(token)
        suffix = candidate.suffix.lower()
        if not suffix or (source_suffix and suffix != source_suffix):
            continue
        relative_candidate = Path(candidate.name) if candidate.is_absolute() else candidate
        if relative_candidate not in targets:
            targets.append(relative_candidate)
    if not targets:
        targets.append(Path(source_name))
    return targets


def _run_initial_compile(*, command: list[str], source_name: str, source_text: str) -> tuple[str, str]:
    """Run the compile command against the *original* source to populate compiler_*.txt."""
    if not command:
        return "", ""
    with tempfile.TemporaryDirectory(prefix="llm_patch_fix_init_") as tmpdir:
        tmp_path = Path(tmpdir)
        for rel_path in _compile_target_paths(source_name, command):
            destination = tmp_path / rel_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source_text, encoding="utf-8")
        proc = subprocess.run(command, cwd=str(tmp_path), capture_output=True, text=True, check=False)
        return proc.stdout or "", proc.stderr or ""


def _resolve_possible_file(case: str) -> Optional[Path]:
    """Resolve a user-provided single-file reference.

    Supports:
      - absolute/relative file paths
      - bare filenames relative to /project (when running inside Docker)
    """
    candidate = Path(case)
    if candidate.exists() and candidate.is_file():
        return candidate.resolve()

    project_root = Path("/project")
    if project_root.exists():
        alt = project_root / case
        if alt.exists() and alt.is_file():
            return alt.resolve()

    return None


def _safe_case_id(prefix: str) -> str:
    # Keep it filesystem-friendly.
    return "".join(ch if (ch.isalnum() or ch in "-_.") else "_" for ch in prefix)


def create_case_from_single_file(
    *,
    scratch_dataset_root: Path,
    source_file: Path,
    language: str,
    compile_command: list[str],
) -> tuple[Path, str]:
    """Create a case directory under scratch_dataset_root for a single-file fix run."""

    source_text = source_file.read_text(encoding="utf-8")
    filename = source_file.name
    before_name = f"before{source_file.suffix}"

    # Generate a unique-ish case id for display/artifacts.
    stamp = os.environ.get("LLM_PATCH_RUN_ID") or "prod"
    case_id = _safe_case_id(f"{language}-prod-{filename}-{stamp}")

    case_dir = scratch_dataset_root / "production" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / before_name).write_text(source_text, encoding="utf-8")

    # Helpful to also store the canonical filename if the compile command references it.
    (case_dir / filename).write_text(source_text, encoding="utf-8")

    stdout, stderr = _run_initial_compile(command=compile_command, source_name=filename, source_text=source_text)
    (case_dir / "compiler_stdout.txt").write_text(stdout, encoding="utf-8")
    (case_dir / "compiler_stderr.txt").write_text(stderr, encoding="utf-8")

    manifest = {
        "case_id": case_id,
        "language": language,
        "problem_id": "production-single-file",
        "compile_command": compile_command,
        "notes": {
            "source_file": str(source_file),
        },
    }
    (case_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return case_dir, case_id


def find_before_file(case_dir: Path) -> Path:
    for candidate in case_dir.glob("before.*"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Missing before.* file in {case_dir}")


_BENCHMARK_ARTIFACT_DIRS = (
    "results",
    "diffs",
    "after",
)


def copy_benchmark_seed_dir(src: Path, dest: Path) -> None:
    """Copy only the inputs needed to run guided-loop.

    Benchmark directories often already contain `results/`, `diffs/`, and `after/` artifacts from
    other algorithms (git/aider/diff-match-patch, previous guided-loop runs, etc.). When we preserve
    the workdir and open the reviewer UI, those unrelated artifacts get indexed and show up as if
    they were part of the current run.

    To keep inspection focused, we intentionally do NOT copy those artifact directories into the
    scratch dataset. The guided-loop runner and this wrapper will generate fresh `results/` / `diffs/`
    / `after/` for the current run.
    """

    ignore = shutil.ignore_patterns(*_BENCHMARK_ARTIFACT_DIRS)
    shutil.copytree(src, dest, ignore=ignore)

    # Defensive cleanup in case the source uses unexpected nesting or naming.
    for dirname in _BENCHMARK_ARTIFACT_DIRS:
        shutil.rmtree(dest / dirname, ignore_errors=True)


def _write_text(path: Path, text: str | None) -> None:
    if text is None:
        return
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _unified_diff_text(*, before: str, after: str, file_path: str) -> str:
    """Return a git-style unified diff between before and after.

    Notes:
      - We keep output deterministic (no timestamps).
      - We intentionally do NOT preserve line endings when feeding difflib.
        (If we pass lines with trailing newlines and then join with "\n", we end up
        with double-newlines and a diff that looks like it has blank lines between
        every line.)
    """

    before_lines = before.splitlines()
    after_lines = after.splitlines()

    diff_iter = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=3,
        lineterm="",
    )
    diff_lines = list(diff_iter)
    if not diff_lines:
        return ""
    return "\n".join(diff_lines) + "\n"


def _file_path_for_unified_diff(*, case_dir: Path, resolved_file: Optional[Path]) -> str:
    """Best-effort path label for unified diff headers.

    - For single-file runs: prefer a path relative to /project when available.
    - For benchmark runs: derive the compile target path from manifest compile_command.
    """

    if resolved_file is not None:
        try:
            project_root = Path("/project")
            if project_root.exists() and resolved_file.is_relative_to(project_root):
                return resolved_file.relative_to(project_root).as_posix()
        except Exception:
            # is_relative_to may raise in older path forms; fall back to name.
            pass
        return resolved_file.name

    manifest_path = case_dir / "manifest.json"
    if manifest_path.exists():
        manifest = _read_json(manifest_path)
        compile_command = manifest.get("compile_command") or []
        before_path = find_before_file(case_dir)
        targets = _compile_target_paths(before_path.name, list(compile_command) if isinstance(compile_command, list) else [])
        if targets:
            return targets[0].as_posix()

    # Fallback to before.* filename.
    return find_before_file(case_dir).name


def _latest_guided_loop_result(case_dir: Path, model: str) -> Path:
    slug = sanitize_model_name(model)
    candidate = case_dir / "results" / f"{slug}__guided-loop.json"
    if not candidate.exists():
        raise FileNotFoundError(f"Expected guided-loop result not found: {candidate}")
    return candidate


def _cycle_tag(cycle: int) -> str:
    return f"cycle_{cycle:03d}"


def snapshot_cycle_artifacts(*, outcome: CycleOutcome, model: str, cycle: int) -> None:
    """Persist a copy of each cycle's artifacts for UI inspection.

    The guided-loop runner overwrites its canonical artifacts each run. For inspect mode we want
    a stable per-cycle history. We do this purely in the wrapper, leaving guided-loop unchanged.

    Snapshot strategy:
      - Copy diff/after artifacts to cycle-specific filenames.
      - Copy the result JSON to a cycle-specific filename and tweak:
          - algorithm: unique per cycle (so the UI lists each cycle separately)
          - diff_path/after_path: point to the copied artifacts
          - outer_cycle: cycle number
    """

    payload = _read_json(outcome.result_path)
    slug = sanitize_model_name(model)
    tag = _cycle_tag(cycle)

    new_diff_rel: str | None = None
    if outcome.diff_path and outcome.diff_path.exists():
        diff_dir = outcome.diff_path.parent
        new_diff_path = diff_dir / f"{slug}__guided-loop__{tag}.diff"
        shutil.copyfile(outcome.diff_path, new_diff_path)
        new_diff_rel = new_diff_path.relative_to(outcome.case_dir).as_posix()

    new_after_rel: str | None = None
    if outcome.after_path and outcome.after_path.exists():
        after_dir = outcome.after_path.parent
        # Preserve original filename suffix (usually the source filename).
        suffix = outcome.after_path.name
        # Convert: <slug>__guided-loop__<file> -> <slug>__guided-loop__cycle_XXX__<file>
        marker = f"{slug}__guided-loop__"
        if suffix.startswith(marker):
            suffix = suffix[len(marker) :]
        new_after_path = after_dir / f"{slug}__guided-loop__{tag}__{suffix}"
        shutil.copyfile(outcome.after_path, new_after_path)
        new_after_rel = new_after_path.relative_to(outcome.case_dir).as_posix()

    # Write a cycle-specific result JSON.
    results_dir = outcome.case_dir / "results"
    results_dir.mkdir(exist_ok=True)
    result_copy_path = results_dir / f"{slug}__guided-loop__{tag}.json"

    # Ensure the UI treats each cycle as a distinct record.
    payload["algorithm"] = f"guided-loop-cycle-{cycle:03d}"
    payload["outer_cycle"] = cycle
    if new_diff_rel is not None:
        payload["diff_path"] = new_diff_rel
    if new_after_rel is not None:
        payload["after_path"] = new_after_rel

    result_copy_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_last_dataset_pointer(*, workdir: Path, dataset_root: Path) -> None:
    """Write a stable pointer that inspect mode can use to find the most recent run."""
    try:
        root = workdir / "llm-patch"
        root.mkdir(parents=True, exist_ok=True)
        (root / "last_dataset_root.txt").write_text(str(dataset_root) + "\n", encoding="utf-8")
    except Exception:
        # Never fail the main fix flow due to inspection convenience.
        return


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

    # The guided-loop runner prints a repetitive "Guided loop trace saved to ..." line.
    # For outer-cycle runs, that's noisy; we emit it only once at the end.
    trace_saved_message: Optional[str] = None

    if proc.stdout:
        out_lines = proc.stdout.splitlines()
        forwarded: list[str] = []
        for line in out_lines:
            if line.startswith("Guided loop trace saved to "):
                trace_saved_message = line
                continue
            forwarded.append(line)
        if forwarded:
            sys.stderr.write("\n".join(forwarded))
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
        trace_saved_message=trace_saved_message,
        cycle_seconds=payload.get("cycle_seconds"),
        llm_prompt_tokens=(payload.get("llm_usage") or {}).get("prompt_tokens") if isinstance(payload.get("llm_usage"), dict) else None,
        llm_completion_tokens=(payload.get("llm_usage") or {}).get("completion_tokens") if isinstance(payload.get("llm_usage"), dict) else None,
        llm_requests=(payload.get("llm_usage") or {}).get("requests") if isinstance(payload.get("llm_usage"), dict) else None,
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

    # Create a scratch dataset root and populate it either by copying a benchmark case directory
    # or by generating a temporary single-file case.
    dataset_root_resolved = args.dataset_root.resolve()
    resolved_file = _resolve_possible_file(args.case)

    if not args.workdir.exists():
        raise FileNotFoundError(f"workdir does not exist: {args.workdir}")

    scratch_parent = args.workdir / "llm-patch"
    scratch_parent.mkdir(parents=True, exist_ok=True)

    scratch_root = Path(tempfile.mkdtemp(prefix="fix-", dir=str(scratch_parent)))
    scratch_dataset_root = scratch_root / "dataset"
    scratch_dataset_root.mkdir(parents=True, exist_ok=True)

    if resolved_file is not None:
        # Single-file "production" mode.
        language = args.language or _infer_language_from_suffix(resolved_file.suffix)
        if not language:
            raise ValueError(
                f"Could not infer language from file extension '{resolved_file.suffix}'. "
                "Provide --language or use a benchmark case directory."
            )

        if args.compile is not None:
            compile_command = shlex.split(args.compile)
        else:
            compile_command = _default_compile_command_for_file(resolved_file.name, language) or []
        if not compile_command:
            raise ValueError(
                "No compile command available for this file type. "
                "Provide --compile, e.g. --compile 'javac MyFile.java'."
            )

        scratch_case_dir, case_id = create_case_from_single_file(
            scratch_dataset_root=scratch_dataset_root,
            source_file=resolved_file,
            language=language,
            compile_command=compile_command,
        )
    else:
        # Benchmark case mode.
        case_dir = resolve_case_dir(dataset_root_resolved, args.case)
        case_id = case_dir.name

        # Preserve the on-disk dataset structure when the case lives under dataset-root.
        # Otherwise, place it under a stable "custom/" prefix.
        try:
            rel_case_dir = case_dir.relative_to(dataset_root_resolved)
        except ValueError:
            rel_case_dir = Path("custom") / case_dir.name

        scratch_case_dir = scratch_dataset_root / rel_case_dir
        scratch_case_dir.parent.mkdir(parents=True, exist_ok=True)
        copy_benchmark_seed_dir(case_dir, scratch_case_dir)

    # Capture the original inputs once; the scratch before.* is mutated each cycle.
    original_before_path: Optional[Path] = None
    original_source_text: Optional[str] = None
    unified_diff_path_label: Optional[str] = None

    last_errors_after: Optional[int] = None
    final_outcome: Optional[CycleOutcome] = None
    diff_text: Optional[str] = None
    baseline_errors: Optional[int] = None
    best_errors_after: Optional[int] = None
    improved_once = False
    removed_once = False
    executed_cycles = 0
    last_trace_saved_message: Optional[str] = None
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_llm_requests = 0
    total_cycle_seconds = 0.0
    run_start = time.perf_counter()

    try:
        # Capture the original source for final unified diff output.
        original_before_path = find_before_file(scratch_case_dir)
        original_source_text = original_before_path.read_text(encoding="utf-8")
        unified_diff_path_label = _file_path_for_unified_diff(case_dir=scratch_case_dir, resolved_file=resolved_file)

        for cycle in range(1, args.outer_cycles + 1):
            executed_cycles = cycle
            final_outcome = run_guided_loop_once(
                app_root=app_root,
                scratch_dataset_root=scratch_dataset_root,
                case_id=case_id,
                model=args.model,
                temperature=args.temperature,
                max_iterations=args.max_iterations,
                refine_iterations=args.refine_iterations,
            )

            if baseline_errors is None and final_outcome.errors_before is not None:
                baseline_errors = final_outcome.errors_before

            if final_outcome.errors_after is not None:
                if best_errors_after is None or final_outcome.errors_after < best_errors_after:
                    best_errors_after = final_outcome.errors_after

            if final_outcome.first_error_removed is True:
                removed_once = True

            if final_outcome.trace_saved_message:
                last_trace_saved_message = final_outcome.trace_saved_message

            if isinstance(final_outcome.llm_prompt_tokens, int):
                total_prompt_tokens += final_outcome.llm_prompt_tokens
            if isinstance(final_outcome.llm_completion_tokens, int):
                total_completion_tokens += final_outcome.llm_completion_tokens
            if isinstance(final_outcome.llm_requests, int):
                total_llm_requests += final_outcome.llm_requests
            if isinstance(final_outcome.cycle_seconds, (int, float)):
                total_cycle_seconds += float(final_outcome.cycle_seconds)

            # Per-cycle progress signal (stderr only; diff stays clean on stdout).
            if final_outcome.errors_before is not None and final_outcome.errors_after is not None:
                event = "ERROR_FIXED" if final_outcome.errors_after < final_outcome.errors_before else "CYCLE_FAILURE"
            else:
                event = "CYCLE_FAILURE"
            sys.stderr.write(
                _csv_event(
                    event,
                    cycle=cycle,
                    compile_returncode=final_outcome.compile_returncode,
                    errors_before=final_outcome.errors_before,
                    errors_after=final_outcome.errors_after,
                    cycle_seconds=(round(float(final_outcome.cycle_seconds), 3) if isinstance(final_outcome.cycle_seconds, (int, float)) else None),
                    llm_prompt_tokens=final_outcome.llm_prompt_tokens,
                    llm_completion_tokens=final_outcome.llm_completion_tokens,
                    llm_requests=final_outcome.llm_requests,
                )
            )

            # Persist a stable per-cycle history for the reviewer UI.
            snapshot_cycle_artifacts(outcome=final_outcome, model=args.model, cycle=cycle)

            # Success condition: compilation succeeds.
            if final_outcome.compile_returncode == 0:
                break

            # No-progress condition: errors_after did not decrease.
            if final_outcome.errors_after is not None:
                # If error count didn't decrease and the *first error* wasn't removed, we're stuck.
                if (
                    last_errors_after is not None
                    and final_outcome.errors_after >= last_errors_after
                    and final_outcome.first_error_removed is not True
                ):
                    break
                if last_errors_after is not None and final_outcome.errors_after < last_errors_after:
                    improved_once = True
                last_errors_after = final_outcome.errors_after

            # Prepare inputs for next cycle.
            apply_cycle_state_update(case_dir=final_outcome.case_dir, outcome=final_outcome)

        if not final_outcome:
            sys.stderr.write("No guided-loop cycles were executed.\n")
            return 1

        if original_source_text is None or unified_diff_path_label is None:
            sys.stderr.write("Missing original source snapshot for unified diff output.\n")
            return 1

        # Determine the final source text to diff against.
        if final_outcome.after_path and final_outcome.after_path.exists():
            final_source_text = final_outcome.after_path.read_text(encoding="utf-8")
        else:
            # If the last cycle failed to apply a patch, the scratch before.* still reflects
            # the latest successfully applied state.
            final_source_text = find_before_file(final_outcome.case_dir).read_text(encoding="utf-8")

        # Generate unified diff before cleanup.
        diff_text = _unified_diff_text(
            before=original_source_text,
            after=final_source_text,
            file_path=unified_diff_path_label,
        )
    finally:
        run_seconds = time.perf_counter() - run_start
        if args.keep_workdir:
            sys.stderr.write(f"Scratch dataset preserved at: {scratch_dataset_root}\n")
            write_last_dataset_pointer(workdir=args.workdir, dataset_root=scratch_dataset_root)
        else:
            shutil.rmtree(scratch_root, ignore_errors=True)

    if diff_text is None:
        return 1

    # Summarize outcome on STDERR without affecting diff-only STDOUT.
    if final_outcome.compile_returncode == 0:
        sys.stderr.write(
            _csv_event(
                "COMPLETE_SUCCESS",
                compile_returncode=0,
                errors_before=baseline_errors,
                errors_after=final_outcome.errors_after,
                cycles=executed_cycles,
                run_seconds=round(float(run_seconds), 3),
                cycle_seconds=round(float(total_cycle_seconds), 3),
                llm_prompt_tokens=total_prompt_tokens,
                llm_completion_tokens=total_completion_tokens,
                llm_requests=total_llm_requests,
            )
        )
    else:
        # If we saw any decrease in error count at any point, call it partial success.
        partial = improved_once or removed_once
        if baseline_errors is not None and best_errors_after is not None and best_errors_after < baseline_errors:
            partial = True
        label = "PARTIAL_SUCCESS" if partial else "FAILURE"
        sys.stderr.write(
            _csv_event(
                label,
                errors_before=baseline_errors,
                best_errors_after=best_errors_after,
                final_errors_after=final_outcome.errors_after,
                compile_returncode=final_outcome.compile_returncode,
                cycles=executed_cycles,
                run_seconds=round(float(run_seconds), 3),
                cycle_seconds=round(float(total_cycle_seconds), 3),
                llm_prompt_tokens=total_prompt_tokens,
                llm_completion_tokens=total_completion_tokens,
                llm_requests=total_llm_requests,
            )
        )

    if last_trace_saved_message:
        sys.stderr.write(last_trace_saved_message)
        if not last_trace_saved_message.endswith("\n"):
            sys.stderr.write("\n")

    # Output: unified diff only.
    sys.stdout.write(diff_text)

    # Exit code convention:
    #  - 0: complete success (compile passed)
    #  - 1: failure (no progress)
    #  - 3: partial success (some progress but compile still failing)
    if final_outcome.compile_returncode == 0:
        return 0
    if improved_once or removed_once or (
        baseline_errors is not None and best_errors_after is not None and best_errors_after < baseline_errors
    ):
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
