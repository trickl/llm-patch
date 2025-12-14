"""Tests for the Guided Convergence Strategy critique stage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from llm_patch.strategies.guided_loop import (
    GuidedConvergenceStrategy,
    GuidedLoopConfig,
    GuidedLoopInputs,
)


class StubLLMClient:
    """Deterministic LLM client for unit tests."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)

    def complete(self, *, prompt: str, temperature: float, model: str | None = None) -> str:  # noqa: D401
        if not self._responses:
            raise RuntimeError("LLM client exhausted responses")
        return self._responses.pop(0)


def interpretation_payload(label: str) -> str:
    return json.dumps(
        {
            "interpretation": f"{label} structural interpretation",
            "explanation": f"{label} interpretation rationale",
        },
        indent=2,
    )


def diagnosis_payload(label: str, count: int = 2) -> str:
    hypotheses = []
    for idx in range(max(1, count)):
        hypotheses.append(
            {
                "claim": f"{label} hypothesis {idx + 1}",
                "affected_region": f"lines {idx + 1}-{idx + 2}",
                "expected_effect": f"{label} effect {idx + 1}",
                "structural_change": f"{label} structural change {idx + 1}",
                "confidence": max(0.1, 0.8 - idx * 0.2),
                "explanation": f"{label} evidence {idx + 1}",
            }
        )
    return json.dumps(
        {
            "interpretation": f"{label} structural diagnosis",
            "explanation": f"{label} diagnosis rationale",
            "hypotheses": hypotheses,
        },
        indent=2,
    )


def diagnosis_payload_without_hypotheses(label: str) -> str:
    return json.dumps(
        {
            "interpretation": f"{label} structural diagnosis",
            "explanation": f"{label} diagnosis rationale",
        },
        indent=2,
    )


def falsify_payload(label: str, *, observed: bool = False) -> str:
    contradictions = []
    if observed:
        contradictions.append(
            {
                "observation": f"{label} observed contradiction",
                "status": "observed",
                "evidence": f"{label} evidence",
            }
        )
    return json.dumps(
        {
            "summary": f"{label} falsification summary",
            "contradictions": contradictions,
        },
        indent=2,
    )


def proposal_payload(label: str) -> str:
    return json.dumps(
        {
            "intent": f"{label} intent",
            "structural_change": f"{label} structural change",
        },
        indent=2,
    )


def compile_command_with_error(message: str) -> list[str]:
    script = "import sys; sys.stderr.write(%r + '\n'); sys.exit(1)" % message
    return [sys.executable, "-c", script]


@pytest.fixture()
def sample_before_file(tmp_path: Path) -> Path:
    before_path = tmp_path / "sample.py"
    before_path.write_text("print('hello')\n", encoding="utf-8")
    return before_path


def build_request(before_path: Path, compile_command: list[str]) -> GuidedLoopInputs:
    return GuidedLoopInputs(
        case_id="sample-case",
        language="python",
        source_path=before_path,
        source_text=before_path.read_text(encoding="utf-8"),
        error_text=f"{before_path.name}:1: error",
        manifest={"compile_command": compile_command},
        compile_command=compile_command,
        extra={},
    )


def test_guided_loop_applies_and_compiles(sample_before_file: Path) -> None:
    diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('hello')\n"
        "+print('patched')\n"
    )
    client = StubLLMClient([
        interpretation_payload("pass-1"),
        diagnosis_payload("pass-1"),
        falsify_payload("pass-1"),
        proposal_payload("pass-1"),
        diff,
        "Critique looks good overall.",
    ])
    compile_command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    request = build_request(sample_before_file, compile_command)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.success is True
    assert result.compile_returncode == 0
    assert result.after_text is not None
    assert "patched" in result.after_text
    assert result.diff_text and result.diff_text.strip() == diff.strip()
    first_iteration = result.trace.iterations[0]
    interpret_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "interpret"
    )
    critique_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "critique"
    )
    propose_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "propose"
    )
    assert critique_phase.status.value == "completed"
    patch_check = critique_phase.machine_checks.get("patchApplication")
    assert patch_check and patch_check["applied"] is True
    assert critique_phase.prompt is not None
    assert critique_phase.prompt.startswith("Critique the following unified diff")
    assert "Original Code before suggested diff was applied" in critique_phase.prompt
    assert "Unified Diff that was applied" in critique_phase.prompt
    assert "Validation summary" in critique_phase.prompt
    assert "Is the initial analysis correct or flawed" in critique_phase.prompt
    assert "Can the code be simplified to help analysis of the error" in critique_phase.prompt
    assert "Critique looks good overall." in critique_phase.response
    assert "Validation summary" in critique_phase.response
    assert "The diff was applied and compile/test succeeded." in critique_phase.response
    assert "No prior iterations have run yet." not in interpret_phase.prompt
    assert "No prior critique feedback yet; this is the initial attempt." not in propose_phase.prompt
    assert "No previous diff attempt has been recorded." not in propose_phase.prompt
    assert first_iteration.history_context is not None
    assert "iterations" in first_iteration.history_context.lower()
    assert first_iteration.history_entry is not None
    telemetry = first_iteration.telemetry
    assert "falsification" in telemetry
    assert telemetry["falsification"][0]["status"] == "viable"


def test_guided_loop_compile_failure(sample_before_file: Path) -> None:
    diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('hello')\n"
        "+print('patched')\n"
    )
    client = StubLLMClient([
        interpretation_payload("compile-fail"),
        diagnosis_payload("compile-fail"),
        falsify_payload("compile-fail"),
        proposal_payload("compile-fail"),
        diff,
        "Compile still failing after patch.",
    ])
    compile_command = [sys.executable, "-c", "import sys; sys.exit(1)"]
    request = build_request(sample_before_file, compile_command)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.success is False
    assert result.compile_returncode == 1
    first_iteration = result.trace.iterations[0]
    critique_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "critique"
    )
    assert critique_phase.status.value == "failed"
    compile_check = critique_phase.machine_checks.get("compile")
    assert compile_check and compile_check["returncode"] == 1
    assert critique_phase.prompt is not None
    assert "Validation summary" in critique_phase.prompt
    assert "compile/test exited with return code 1" in critique_phase.prompt
    assert "Compile still failing" in critique_phase.response
    assert "Validation summary" in critique_phase.response
    assert "compile/test exited with return code 1" in critique_phase.response
    assert first_iteration.history_entry is not None
    assert "compile/test failed" in first_iteration.history_entry


def test_guided_loop_multiple_iterations_succeed(sample_before_file: Path) -> None:
    bad_diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('nonexistent')\n"
        "+print('still wrong')\n"
    )
    good_diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('hello')\n"
        "+print('refined')\n"
    )
    client = StubLLMClient(
        [
            interpretation_payload("loop1"),
            diagnosis_payload("loop1"),
            falsify_payload("loop1"),
            proposal_payload("propose-pass-1"),
            bad_diff,
            "critique-pass-1",
            diagnosis_payload("loop2"),
            falsify_payload("loop2"),
            proposal_payload("propose-pass-2"),
            good_diff,
            "critique-pass-2",
        ]
    )
    compile_command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    request = build_request(sample_before_file, compile_command)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=2,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.success is True
    assert result.diff_text and result.diff_text.strip() == good_diff.strip()
    second_iteration = result.trace.iterations[1]
    critique_phase = next(phase for phase in second_iteration.phases if phase.phase.value == "critique")
    assert critique_phase.status.value == "completed"
    assert second_iteration.kind == "refine"
    assert second_iteration.phases[0].phase.value == "diagnose"
    assert second_iteration.history_context is not None
    assert second_iteration.history_entry is not None


def test_guided_loop_history_seed_in_prompts(sample_before_file: Path) -> None:
    diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('hello')\n"
        "+print('seeded')\n"
    )
    client = StubLLMClient([
        interpretation_payload("seeded"),
        diagnosis_payload("seeded"),
        falsify_payload("seeded"),
        proposal_payload("seeded"),
        diff,
        "Critique for seeded history.",
    ])
    compile_command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    request = GuidedLoopInputs(
        case_id="sample-case",
        language="python",
        source_path=sample_before_file,
        source_text=sample_before_file.read_text(encoding="utf-8"),
        error_text=f"{sample_before_file.name}:1: error",
        manifest={"compile_command": compile_command},
        compile_command=compile_command,
        history_seed=("Loop 0: manual attempt failed.",),
    )
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
        ),
    )

    result = strategy.run(request)

    history_context = result.trace.iterations[0].history_context
    assert history_context is not None
    assert "manual attempt" in history_context
    assert result.trace.iterations[0].history_entry is not None


def test_hypothesis_expires_after_two_retries(sample_before_file: Path) -> None:
    bad_diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('missing context')\n"
        "+print('still missing')\n"
    )
    client = StubLLMClient(
        [
            interpretation_payload("retry-1"),
            diagnosis_payload("retry-1"),
            falsify_payload("retry-1"),
            proposal_payload("retry-1"),
            bad_diff,
            "critique-retry-1",
            diagnosis_payload_without_hypotheses("retry-2"),
            falsify_payload("retry-2"),
            proposal_payload("retry-2"),
            bad_diff,
            "critique-retry-2",
        ]
    )
    request = build_request(sample_before_file, [])
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=1,
        ),
    )

    result = strategy.run(request)

    second_iteration = result.trace.iterations[1]
    hypotheses = second_iteration.hypotheses
    assert hypotheses is not None
    assert len(hypotheses.expired) >= 1
    assert any(h.retry_count >= 2 for h in hypotheses.expired)
    telemetry = second_iteration.telemetry
    assert "retries" in telemetry
    assert any(entry["retryCount"] >= 2 for entry in telemetry["retries"])


def test_stall_detection_archives_hypothesis(sample_before_file: Path) -> None:
    repeated_diff = (
        "--- sample.py\n"
        "+++ sample.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-print('hello')\n"
        "+print('looped change')\n"
    )
    compile_command = compile_command_with_error(f"{sample_before_file.name}:1: boom")
    client = StubLLMClient(
        [
            interpretation_payload("stall-1"),
            diagnosis_payload("stall-1"),
            falsify_payload("stall-1"),
            proposal_payload("stall-1"),
            repeated_diff,
            "critique-stall-1",
            diagnosis_payload_without_hypotheses("stall-2"),
            falsify_payload("stall-2"),
            proposal_payload("stall-2"),
            repeated_diff,
            "critique-stall-2",
        ]
    )
    request = build_request(sample_before_file, compile_command)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=1,
        ),
    )

    result = strategy.run(request)

    second_iteration = result.trace.iterations[1]
    assert second_iteration.failure_reason == "stall"
    hypotheses = second_iteration.hypotheses
    assert hypotheses is not None
    inactive = list(hypotheses.archived) + list(hypotheses.expired)
    assert inactive, "expected hypothesis to be removed from active pool"
    assert any(h.retry_count >= 2 for h in inactive)
    telemetry = second_iteration.telemetry
    assert "stall" in telemetry
    assert telemetry["stall"][0]["errorLocation"] == 1
    assert any(event.message.startswith("Stall detected") for event in result.events)