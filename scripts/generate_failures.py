#!/usr/bin/env python3
"""Generate failing code samples from Ollama models for benchmarking.

Usage example:
    python -m scripts.generate_failures \
        --languages java,c,python,typescript \
        --models qwen2.5-coder:7b,llama3.2:3b,phi3:mini \
        --target-per-language 100
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, Sequence
from llm_patch.clients import call_ollama

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class LanguageConfig:
    name: str
    extension: str
    filename: str
    prompt_guidance: str
    compile_command_builder: Callable[[Path], Sequence[str]]


@dataclass(frozen=True)
class ProblemSpec:
    problem_id: str
    title: str
    description: str
    requirements: Sequence[str]
    sample_tests: Sequence[tuple[str, str]]


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str


PROBLEMS: Dict[str, ProblemSpec] = {
    "expr_eval_v1": ProblemSpec(
        problem_id="expr_eval_v1",
        title="Expression Evaluator",
        description=(
            "Implement a mini calculator that tokenizes, parses, and evaluates infix "
            "arithmetic expressions with parentheses, unary minus, and integer semantics."
        ),
        requirements=[
            "Accept strings such as \"3 + 4 * (2 - 1)\" and return an integer result.",
            "Respect operator precedence (* and / before + and -).",
            "Support parentheses and nested expressions.",
            "Handle unary minus (e.g., -3 + 5).",
            "Split responsibilities across tokenizer, parser, and evaluator utilities.",
            "Provide minimal error handling for malformed expressions.",
        ],
        sample_tests=[
            ("1 + 2", "3"),
            ("2 * 3 + 4", "10"),
            ("2 * (3 + 4)", "14"),
            ("8 / 2 * (2 + 2)", "16"),
        ],
    ),
}


def _build_java_command(source_path: Path) -> Sequence[str]:
    return ["javac", source_path.name]


def _build_c_command(source_path: Path) -> Sequence[str]:
    return [
        "gcc",
        source_path.name,
        "-std=c17",
        "-Wall",
        "-Wextra",
        "-O0",
        "-o",
        "expr_eval.out",
    ]


def _build_python_command(source_path: Path) -> Sequence[str]:
    python = os.environ.get("PYTHON", sys.executable or "python3")
    return [python, "-m", "py_compile", source_path.name]


def _build_typescript_command(source_path: Path) -> Sequence[str]:
    return [
        "tsc",
        "--strict",
        "--target",
        "ES2020",
        "--module",
        "commonjs",
        "--noEmit",
        source_path.name,
    ]


LANGUAGE_CONFIGS: Dict[str, LanguageConfig] = {
    "java": LanguageConfig(
        name="java",
        extension="java",
        filename="ExpressionEvaluator.java",
        prompt_guidance=textwrap.dedent(
            """
            - Use a public class named ExpressionEvaluator as the entry point (with main method for smoke tests).
            - Additional helpers can be static inner classes or package-private classes within the same file.
            - Target Java 21, no external libraries beyond the standard library.
            """
        ).strip(),
        compile_command_builder=_build_java_command,
    ),
    "c": LanguageConfig(
        name="c",
        extension="c",
        filename="expression_evaluator.c",
        prompt_guidance=textwrap.dedent(
            """
            - Produce a single C17 source file named expression_evaluator.c.
            - Include tokenizer, parser, and evaluator helpers as separate functions.
            - Provide a simple CLI in main that runs a few sample expressions.
            """
        ).strip(),
        compile_command_builder=_build_c_command,
    ),
    "python": LanguageConfig(
        name="python",
        extension="py",
        filename="expression_evaluator.py",
        prompt_guidance=textwrap.dedent(
            """
            - Target Python 3.11+ with standard library only.
            - Structure code into classes or functions (Tokenizer, Parser, Evaluator) rather than a single function.
            - Add an `if __name__ == '__main__'` block that demonstrates a few sample evaluations.
            """
        ).strip(),
        compile_command_builder=_build_python_command,
    ),
    "typescript": LanguageConfig(
        name="typescript",
        extension="ts",
        filename="expression_evaluator.ts",
        prompt_guidance=textwrap.dedent(
            """
            - Write idiomatic TypeScript that can be compiled with `tsc --strict` targeting Node 18 (CommonJS modules).
            - Export a function evaluateExpression(input: string): number and provide a simple CLI example at the bottom.
            - Avoid external dependencies.
            """
        ).strip(),
        compile_command_builder=_build_typescript_command,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate failing samples from Ollama models")
    parser.add_argument(
        "--languages",
        default="java,c,python,typescript",
        help="Comma-separated languages to target (subset of: %s)" % ", ".join(sorted(LANGUAGE_CONFIGS)),
    )
    parser.add_argument(
        "--models",
        default="qwen2.5-coder:7b,llama3.2:3b,phi3:mini",
        help="Comma-separated Ollama models",
    )
    parser.add_argument(
        "--problem-id",
        default="expr_eval_v1",
        choices=sorted(PROBLEMS.keys()),
        help="Problem definition to use",
    )
    parser.add_argument(
        "--target-per-language",
        type=int,
        default=100,
        help="Number of failing samples to collect per language",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks/generated"),
        help="Base directory for persisted failures",
    )
    parser.add_argument(
        "--max-attempts-per-language",
        type=int,
        default=1000,
        help="Safety cap on total generations per language to avoid infinite loops",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for Ollama models",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate prompts but skip model + compiler calls (debugging)",
    )
    return parser.parse_args()


def ensure_tool_available(command: str) -> None:
    if shutil.which(command) is None:
        raise FileNotFoundError(
            f"Required tool '{command}' is not available on PATH. Install it (see docs/toolchains.md)."
        )


def validate_environment(languages: Iterable[str]) -> None:
    ensure_tool_available("ollama")
    for lang in languages:
        cfg = LANGUAGE_CONFIGS[lang]
        compiler_binary = cfg.compile_command_builder(Path(cfg.filename))[0]
        if shutil.which(compiler_binary) is None:
            raise FileNotFoundError(
                f"Compiler '{compiler_binary}' required for language '{lang}' not found."
            )


def render_prompt(problem: ProblemSpec, language: LanguageConfig) -> str:
    requirements = "\n".join(f"- {item}" for item in problem.requirements)
    tests = "\n".join(f"{expr} => {expected}" for expr, expected in problem.sample_tests)
    guidance = language.prompt_guidance
    return textwrap.dedent(
        f"""
        You are a professional software engineer. Write a complete {language.name} program.

        Problem: {problem.title}
        Description: {problem.description}

        Functional requirements:
        {requirements}

        Sample evaluations (write automated tests or a CLI snippet that demonstrates these):
        {tests}

        Language-specific guidance:
        {guidance}

        Output only the final source code for {language.filename}. Avoid commentary outside of code blocks.
        """
    ).strip()



def extract_code(generation: str) -> str:
    if "```" not in generation:
        return generation.strip()
    blocks: list[str] = []
    collecting = False
    buffer: list[str] = []
    for line in generation.splitlines():
        if line.strip().startswith("```"):
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
    return "\n\n".join(blocks).strip()


def run_command(cmd: Sequence[str], cwd: Path) -> RunResult:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return RunResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def save_failure(
    base_dir: Path,
    language: LanguageConfig,
    model: str,
    problem_id: str,
    prompt: str,
    generation_raw: str,
    source_code: str,
    compile_cmd: Sequence[str],
    run_result: RunResult,
) -> None:
    case_id = f"{language.name}-{model}-{uuid.uuid4().hex[:8]}"
    case_dir = base_dir / language.name / case_id
    case_dir.mkdir(parents=True, exist_ok=False)

    (case_dir / f"before.{language.extension}").write_text(source_code, encoding="utf-8")
    (case_dir / "model_response.txt").write_text(generation_raw, encoding="utf-8")
    (case_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (case_dir / "compiler_stdout.txt").write_text(run_result.stdout, encoding="utf-8")
    (case_dir / "compiler_stderr.txt").write_text(run_result.stderr, encoding="utf-8")

    manifest = {
        "case_id": case_id,
        "language": language.name,
        "problem_id": problem_id,
        "model": model,
        "provider": "ollama",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "compile_command": compile_cmd,
        "return_code": run_result.returncode,
    }
    (case_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    LOGGER.info("Saved failure case %s", case_id)


def main() -> None:
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]
    models = [model.strip() for model in args.models.split(",") if model.strip()]

    for lang in languages:
        if lang not in LANGUAGE_CONFIGS:
            raise ValueError(f"Unsupported language '{lang}'. Supported: {sorted(LANGUAGE_CONFIGS)}")

    problem = PROBLEMS[args.problem_id]

    if not args.dry_run:
        validate_environment(languages)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    overall_stats = {}

    for language_name in languages:
        cfg = LANGUAGE_CONFIGS[language_name]
        prompt = render_prompt(problem, cfg)
        failures = 0
        attempts = 0
        LOGGER.info("=== Language %s ===", language_name)
        while failures < args.target_per_language and attempts < args.max_attempts_per_language:
            for model in models:
                if failures >= args.target_per_language:
                    break
                attempts += 1
                LOGGER.info(
                    "Generating sample %s (attempt %s/%s) with model %s",
                    language_name,
                    attempts,
                    args.max_attempts_per_language,
                    model,
                )
                if args.dry_run:
                    LOGGER.info("Dry run: would have prompted model %s", model)
                    failures += 1
                    continue
                try:
                    generation_raw = call_ollama(model, prompt, temperature=args.temperature)
                except Exception as exc:  # noqa: BLE001
                    LOGGER.error("Generation failed: %s", exc)
                    continue
                source_code = extract_code(generation_raw)
                if not source_code.strip():
                    LOGGER.warning("Empty generation from model %s", model)
                    continue
                with tempfile.TemporaryDirectory(prefix="llm_patch_gen_") as tmpdir:
                    tmp_path = Path(tmpdir)
                    source_path = tmp_path / cfg.filename
                    source_path.write_text(source_code, encoding="utf-8")
                    compile_cmd = list(cfg.compile_command_builder(source_path))
                    result = run_command(compile_cmd, cwd=tmp_path)
                if result.returncode == 0:
                    LOGGER.info("Sample compiled/executed successfully; discarding (need failures).")
                    continue
                save_failure(
                    base_dir=output_dir,
                    language=cfg,
                    model=model,
                    problem_id=problem.problem_id,
                    prompt=prompt,
                    generation_raw=generation_raw,
                    source_code=source_code,
                    compile_cmd=compile_cmd,
                    run_result=result,
                )
                failures += 1
                time.sleep(0.1)
                if attempts >= args.max_attempts_per_language:
                    break
        overall_stats[language_name] = {
            "failures_collected": failures,
            "attempts": attempts,
        }
        if failures < args.target_per_language:
            LOGGER.warning(
                "Language %s reached only %s/%s failures (increase max attempts or adjust prompts).",
                language_name,
                failures,
                args.target_per_language,
            )

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(overall_stats, indent=2), encoding="utf-8")
    LOGGER.info("Wrote summary to %s", summary_path)


if __name__ == "__main__":
    main()
