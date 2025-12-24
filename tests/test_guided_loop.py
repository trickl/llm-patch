"""Tests for the Guided Convergence Strategy critique stage."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from llm_patch.strategies.guided_loop import (
    GuidedConvergenceStrategy,
    GuidedLoopConfig,
    GuidedLoopInputs,
    GuidedPhase,
)


class StubLLMClient:
    """Deterministic LLM client for unit tests."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)

    def complete(self, *, prompt: str, temperature: float, model: str | None = None) -> str:  # noqa: D401
        if not self._responses:
            raise RuntimeError("LLM client exhausted responses")
        return self._responses.pop(0)


def diagnosis_payload(label: str, count: int = 2) -> str:
    hypotheses = []
    for idx in range(max(1, count)):
        entry_id = f"{label}-H{idx + 1}"
        kind = "grouping_precedence" if idx % 2 == 0 else "token_absence"
        binding_region = f"{label} binding region {idx + 1}"
        hypotheses.append(
            {
                "id": entry_id,
                "claim": f"{label} hypothesis {idx + 1}",
                "kind": kind,
                "affected_region": f"lines {idx + 1}-{idx + 2}",
                "binding_region": binding_region,
                "expected_effect": f"{label} effect {idx + 1}",
                "structural_change": f"{label} structural change {idx + 1}",
                "confidence": max(0.1, 0.8 - idx * 0.2),
                "explanation": f"{label} evidence {idx + 1}",
            }
        )
    selection_id = hypotheses[0]["id"]
    return json.dumps(
        {
            "diagnosis": f"{label} structural diagnosis",
            "rationale": f"{label} diagnosis rationale",
            "hypotheses": hypotheses,
            "selection": {
                "hypothesis_id": selection_id,
                "rationale": f"{label} selection favors {selection_id}",
                "binding_region": hypotheses[0]["binding_region"],
            },
        },
        indent=2,
    )


def diagnosis_payload_without_hypotheses(label: str) -> str:
    return json.dumps(
        {
            "diagnosis": f"{label} structural diagnosis",
            "rationale": f"{label} diagnosis rationale",
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


def planning_payload(label: str, reason: str | None = None) -> str:
    justification = reason or f"Continuing with {label}."
    return f"Active hypothesis: {label}\nJustification: {justification}"

def gather_payload(*, needs_more_context: bool = False, token: str | None = None) -> str:
    request: dict[str, object] = {
        "needs_more_context": needs_more_context,
        "why": "Need more context to validate the active hypothesis safely." if needs_more_context else "Existing context is sufficient.",
        "requests": [],
    }
    if needs_more_context and token:
        request["requests"] = [
            {
                "category": "USAGE_CONTEXT",
                "target": {"kind": "symbol", "name": token},
                "reason": "Need to see how this symbol is used elsewhere.",
            }
        ]
    return json.dumps(request)


def fenced_gather_payload(*, needs_more_context: bool = False, category: str = "IMPORTS_NAMESPACE") -> str:
    payload = {
        "needs_more_context": needs_more_context,
        "why": "Need import header to confirm symbol availability." if needs_more_context else "No extra context needed.",
        "requests": [
            {
                "category": category,
                "target": None,
                "reason": "Need to confirm imports/namespace context.",
            }
        ]
        if needs_more_context
        else [],
    }
    return "```json\n" + json.dumps(payload, indent=2) + "\n```"


def tilde_fenced_gather_payload(*, needs_more_context: bool = False, category: str = "IMPORTS_NAMESPACE") -> str:
    payload = {
        "needs_more_context": needs_more_context,
        "why": "Need import header to confirm symbol availability." if needs_more_context else "No extra context needed.",
        "requests": [
            {
                "category": category,
                "target": None,
                "reason": "Need to confirm imports/namespace context.",
            }
        ]
        if needs_more_context
        else [],
    }
    return "~~~json\n" + json.dumps(payload, indent=2) + "\n~~~"

def replacement_block(original: str, new: str) -> str:
    return (
        "ORIGINAL LINES:\n"
        f"{original.rstrip()}\n"
        "NEW LINES:\n"
        f"{new.rstrip()}\n"
    )


def compile_command_with_error(message: str) -> list[str]:
    script = "import sys; sys.stderr.write(%r + '\n'); sys.exit(1)" % message
    return [sys.executable, "-c", script]


def test_compile_error_preprocessing_java_pointer_summary() -> None:
    raw_error = """HelloWorld.java:10: error: ';' expected
        return value
               ^
HelloWorld.java:11: error: not a statement
    return 42
           ^
"""
    strategy = GuidedConvergenceStrategy(client=None, config=GuidedLoopConfig())

    processed = strategy._prepare_compile_error_text(raw_error, "java")

    assert "HelloWorld.java:10: error" in processed
    assert "HelloWorld.java:11" not in processed
    assert "Position of error on line" in processed
    assert "previous token" in processed
    assert "current token" in processed
    assert "<ERROR>" not in processed
    assert "In the following snippet" not in processed


def test_compile_error_preprocessing_c_trims_warnings_and_adds_pointer_summary() -> None:
    raw_error = """In file included from expression_evaluator.c:1:
expression_evaluator.c:8:63: error: expected identifier before '(' token
    8 | typedef enum { NUMBER, PLUS, MINUS, MUL } TokenType;
      |                                             ^~~
expression_evaluator.c: In function 'getNextToken':
expression_evaluator.c:29:9: warning: missing initializer for field 'value' of 'Token' [-Wmissing-field-initializers]
   29 |         return (Token){EOF};
      |         ^~~~~~
"""
    strategy = GuidedConvergenceStrategy(client=None, config=GuidedLoopConfig())

    processed = strategy._prepare_compile_error_text(raw_error, "c")

    assert "warning" not in processed
    assert "Position of error on line" in processed
    assert "expression_evaluator.c:29" not in processed
    assert "<ERROR>" not in processed
    assert "In the following snippet" not in processed


def test_compile_error_preprocessing_non_target_language_is_noop() -> None:
    raw_error = "sample.py:1: error: boom\nsecond line"
    strategy = GuidedConvergenceStrategy(client=None, config=GuidedLoopConfig())

    processed = strategy._prepare_compile_error_text(raw_error, "python")

    assert processed == raw_error


def test_detect_error_line_prioritizes_error_lines_over_prefix_lines() -> None:
    error_text = """In file included from expression_evaluator.c:1:\nexpression_evaluator.c:8:63: error: expected identifier before '(' token\n    8 | typedef enum { NUMBER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF } TokenType;\n      |                                                               ^~~\n"""

    line = GuidedConvergenceStrategy._detect_error_line(error_text, "expression_evaluator.c")

    assert line == 8


def test_detect_error_line_falls_back_when_no_error_or_warning_lines() -> None:
    error_text = """In file included from expression_evaluator.c:1:\ncompilation terminated.\n"""

    line = GuidedConvergenceStrategy._detect_error_line(error_text, "expression_evaluator.c")

    assert line == 1


def test_ensure_inputs_reprocesses_error_text_for_guided_inputs(tmp_path: Path) -> None:
    raw_error = """ExpressionEvaluator.java:41: error: ';' expected
                        ? \"0-\" : token)
                                      ^
1 error
"""
    source_path = tmp_path / "ExpressionEvaluator.java"
    source_path.write_text("class ExpressionEvaluator {}\n", encoding="utf-8")
    request = GuidedLoopInputs(
        case_id="java-case",
        language="java",
        source_path=source_path,
        source_text=source_path.read_text(encoding="utf-8"),
        error_text=raw_error,
        manifest={},
    )
    strategy = GuidedConvergenceStrategy(client=None, config=GuidedLoopConfig())

    processed_inputs = strategy._ensure_inputs(request)

    assert processed_inputs is request
    assert processed_inputs.error_text != raw_error
    assert "Position of error on line" in processed_inputs.error_text
    assert processed_inputs.raw_error_text == raw_error
    assert "<ERROR>" not in processed_inputs.error_text
    assert "In the following snippet" not in processed_inputs.error_text


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
    diff = replacement_block("print('hello')", "print('patched')")
    client = StubLLMClient([
        diagnosis_payload("pass-1"),
        planning_payload("pass-1-H1"),
        gather_payload(),
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
            main_loop_passes=1,
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
    planning_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "planning"
    )
    critique_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "critique"
    )
    generate_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase == GuidedPhase.GENERATE_PATCH
    )
    propose_phase = next(
        phase
        for phase in first_iteration.phases
        if phase.phase.value == "propose"
    )
    assert planning_phase.prompt.startswith(
        "You are at the experiment-planning stage. Use the most recent Diagnose narrative"
    )
    assert '"diagnosis": "pass-1 structural diagnosis"' in planning_phase.prompt
    assert critique_phase.status.value == "completed"
    patch_check = critique_phase.machine_checks.get("patchApplication")
    assert patch_check and patch_check["applied"] is True
    assert critique_phase.prompt is not None
    assert critique_phase.prompt.startswith(
        "Summarize the critique of the applied patch"
    )
    assert "Active hypothesis summary:" in critique_phase.prompt
    assert "Original Code before suggested replacement was applied" in critique_phase.prompt
    assert "Replacement block(s) that were applied" in critique_phase.prompt
    assert "pass-1 structural diagnosis" not in critique_phase.prompt
    assert "Active hypothesis: pass-1-H1" in critique_phase.prompt
    assert "Validation summary" in critique_phase.prompt
    assert "Active hypothesis: pass-1-H1" in generate_phase.prompt
    assert "pass-1 structural diagnosis" not in generate_phase.prompt
    assert "Critique looks good overall." in critique_phase.response
    assert "Validation summary" in critique_phase.response
    assert "The diff was applied and compile/test succeeded." in critique_phase.response
    assert "No prior critique feedback yet; this is the initial attempt." not in propose_phase.prompt
    assert "No previous diff attempt has been recorded." not in propose_phase.prompt
    assert "Latest experiment notes:" in propose_phase.prompt
    assert "Active hypothesis: pass-1-H1" in propose_phase.prompt
    assert "pass-1 structural diagnosis" not in propose_phase.prompt
    assert first_iteration.history_context is not None
    assert "iterations" in first_iteration.history_context.lower()
    assert first_iteration.history_entry is not None
    assert isinstance(first_iteration.telemetry, dict)


def test_generate_patch_strips_code_fences(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('patched')")
    fenced_diff = "```python\n" + diff + "```\n"
    client = StubLLMClient([
        diagnosis_payload("pass-1"),
        planning_payload("pass-1-H1"),
        gather_payload(),
        proposal_payload("pass-1"),
        fenced_diff,
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.success is True
    assert result.diff_text is not None
    assert result.diff_text.strip() == diff.strip()
    assert "```" not in result.diff_text


def test_gather_parses_json_code_fences_and_injects_context(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('patched')")
    client = StubLLMClient([
        diagnosis_payload("pass-1"),
        planning_payload("pass-1-H1"),
        fenced_gather_payload(needs_more_context=True, category="IMPORTS_NAMESPACE"),
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    first_iteration = result.trace.iterations[0]
    gather_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "gather")
    propose_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "propose")
    generate_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "generate-patch")

    gather_request = gather_phase.machine_checks.get("gather_request")
    assert gather_request is not None
    assert gather_request["needs_more_context"] is True
    assert isinstance(gather_request.get("why"), str)
    assert gather_request["requests"][0]["category"] == "IMPORTS_NAMESPACE"

    assert "Additional gathered context:" in propose_phase.prompt
    assert "IMPORTS_NAMESPACE (file header):" in propose_phase.prompt
    assert "|" in propose_phase.prompt

    assert "Additional gathered context:" in generate_phase.prompt
    assert "IMPORTS_NAMESPACE (file header):" in generate_phase.prompt


def test_gather_injects_declaration_context_window(tmp_path: Path) -> None:
    before_path = tmp_path / "sample.py"
    before_path.write_text(
        dedent(
            """\
            def use():
                return Token()


            class Token:
                def __init__(self):
                    pass
            """
        ),
        encoding="utf-8",
    )
    diff = replacement_block("pass", "self.value = 0")
    gather = json.dumps(
        {
            "needs_more_context": True,
            "why": "Need the declaration context for this symbol.",
            "requests": [
                {
                    "category": "DECLARATION",
                    "target": {"kind": "symbol", "name": "Token"},
                    "reason": "Need to confirm where Token is declared.",
                }
            ],
        }
    )
    client = StubLLMClient(
        [
            diagnosis_payload("pass-1"),
            planning_payload("pass-1-H1"),
            gather,
            proposal_payload("pass-1"),
            diff,
            "Critique looks good overall.",
        ]
    )
    compile_command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    request = build_request(before_path, compile_command)
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    first_iteration = result.trace.iterations[0]
    propose_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "propose")
    assert "Additional gathered context:" in propose_phase.prompt
    assert "DECLARATION CONTEXT:" in propose_phase.prompt
    assert "sample.py (around line" in propose_phase.prompt
    assert "|" in propose_phase.prompt
    assert "class Token" in propose_phase.prompt


def test_gather_parses_tilde_json_code_fences(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('patched')")
    client = StubLLMClient([
        diagnosis_payload("pass-1"),
        planning_payload("pass-1-H1"),
        tilde_fenced_gather_payload(needs_more_context=True, category="IMPORTS_NAMESPACE"),
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    first_iteration = result.trace.iterations[0]
    gather_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "gather")
    gather_request = gather_phase.machine_checks.get("gather_request")
    assert gather_request is not None
    assert gather_request["needs_more_context"] is True
    assert gather_request["requests"][0]["category"] == "IMPORTS_NAMESPACE"


def test_gather_parses_case_insensitive_keys(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('patched')")
    # Intentionally mixed casing and camelCase keys; target is null.
    gather = json.dumps(
        {
            "NeedsMoreContext": True,
            "WHY": "Need to confirm imports.",
            "REQUESTS": [
                {
                    "Category": "imports_namespace",
                    "Target": None,
                    "Reason": "Need to confirm imports.",
                }
            ],
        }
    )
    client = StubLLMClient([
        diagnosis_payload("pass-1"),
        planning_payload("pass-1-H1"),
        gather,
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    first_iteration = result.trace.iterations[0]
    gather_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "gather")
    propose_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "propose")

    gather_request = gather_phase.machine_checks.get("gather_request")
    assert gather_request is not None
    assert gather_request["needs_more_context"] is True
    assert gather_request["why"] == "Need to confirm imports."
    assert gather_request["requests"][0]["category"] == "IMPORTS_NAMESPACE"
    assert "Additional gathered context:" in propose_phase.prompt
    assert "|" in propose_phase.prompt


def test_gather_enforces_import_header_when_plan_mentions_import(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('patched')")
    # Planning explicitly mentions adding an import, but Gather (incorrectly) claims no extra context is needed.
    planning_text = "Active hypothesis: H2\nJustification: Add the import statement for Foo at the top of the file."
    client = StubLLMClient(
        [
            diagnosis_payload("pass-1"),
            planning_text,
            gather_payload(needs_more_context=False),
            proposal_payload("pass-1"),
            diff,
            "Critique looks good overall.",
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
            refine_sub_iterations=0,
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    first_iteration = result.trace.iterations[0]
    gather_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "gather")
    propose_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "propose")

    gather_request = gather_phase.machine_checks.get("gather_request")
    assert gather_request is not None
    assert gather_request["needs_more_context"] is True
    assert gather_request["requests"][0]["category"] == "IMPORTS_NAMESPACE"
    assert "Additional gathered context:" in propose_phase.prompt
    assert "IMPORTS_NAMESPACE (file header):" in propose_phase.prompt


def test_three_way_merge_preserves_duplicate_lines(tmp_path: Path) -> None:
    before_path = tmp_path / "dup.py"
    before_path.write_text(
        "def greet():\n    print('hello')\n    print('hello')\n    return True\n",
        encoding="utf-8",
    )
    diff = replacement_block(
        "    print('hello')\n    print('hello')",
        "    print('hi')\n    print('hi')",
    )
    client = StubLLMClient([
        diagnosis_payload("dupe"),
        planning_payload("dupe-H1"),
        gather_payload(),
        proposal_payload("dupe"),
        diff,
        "Duplicate lines preserved.",
    ])
    compile_command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    request = GuidedLoopInputs(
        case_id="duplicate-case",
        language="python",
        source_path=before_path,
        source_text=before_path.read_text(encoding="utf-8"),
        error_text=f"{before_path.name}:2: error",
        manifest={"compile_command": compile_command},
        compile_command=compile_command,
        extra={},
    )
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.after_text is not None


def test_replacement_block_can_edit_outside_context_fragment(tmp_path: Path) -> None:
    before_path = tmp_path / "far_edit.py"
    before_path.write_text(
        "import os\nimport sys\n\n" + "x = 1\n" * 80 + "print('hello')\n",
        encoding="utf-8",
    )
    # Focused context will be near the end of the file; the patch edits the header imports.
    error_text = f"{before_path.name}:75: error"
    diff = replacement_block(
        "import os\nimport sys",
        "import os\nimport sys\nimport json",
    )
    client = StubLLMClient(
        [
            diagnosis_payload("header"),
            planning_payload("header-H1"),
            gather_payload(),
            proposal_payload("header"),
            diff,
            "Header edit applied.",
        ]
    )
    compile_command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    request = GuidedLoopInputs(
        case_id="header-edit",
        language="python",
        source_path=before_path,
        source_text=before_path.read_text(encoding="utf-8"),
        error_text=error_text,
        manifest={"compile_command": compile_command},
        compile_command=compile_command,
        extra={},
    )
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.after_text is not None
    assert "import json" in result.after_text
    first_iteration = result.trace.iterations[0]
    critique_phase = next(phase for phase in first_iteration.phases if phase.phase.value == "critique")
    patch_diagnostics = critique_phase.machine_checks.get("patchApplication")
    assert patch_diagnostics and patch_diagnostics["applied"] is True
    assert "whole-file matching" in (patch_diagnostics.get("message") or "")


def test_successful_compile_does_not_mark_unchanged_error(tmp_path: Path) -> None:
    before_path = tmp_path / "sample.py"
    before_path.write_text(
        "def main():\n    print(\"hi\"\n",
        encoding="utf-8",
    )

    diff = replacement_block(
        '    print("hi"',
        '    print("hi")',
    )
    client = StubLLMClient(
        [
            diagnosis_payload("syntax"),
            planning_payload("syntax-H1"),
            gather_payload(),
            proposal_payload("syntax"),
            diff,
            "Syntax fix applied.",
        ]
    )
    compile_command = [sys.executable, "-m", "py_compile", before_path.name]
    request = GuidedLoopInputs(
        case_id="syntax-success",
        language="python",
        source_path=before_path,
        source_text=before_path.read_text(encoding="utf-8"),
        error_text=f"{before_path.name}:2: error: syntax error",
        manifest={"compile_command": compile_command},
        compile_command=compile_command,
        extra={},
    )
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    assert result.applied is True
    assert result.success is True
    assert result.trace is not None

    first_iteration = result.trace.iterations[0]
    assert first_iteration.accepted is True
    assert first_iteration.failure_reason is None
    assert "unchangedError" not in (first_iteration.telemetry or {})


def test_three_way_merge_collapses_suffix_duplicates(tmp_path: Path) -> None:
    before_text = dedent(
        r"""
        // header 1
        // header 2
        // header 3
        // header 4
        // header 5
        // header 6
        // header 7
        // header 8
        // header 9
        // header 10
        class ExpressionEvaluator {
                List<String> normalize(List<String> tokens) {
                return tokens.stream()
                    .map(token -> token.equals("-") && (tokens.isEmpty() || tokens.get(tokens.size() - 1).matches("[\\(+-]")))
                        ? "0-" : token)
                    .collect(Collectors.toList());
            }
        }
        """
    ).lstrip("\n")
    before_path = tmp_path / "ExpressionEvaluator.java"
    before_path.write_text(before_text, encoding="utf-8")

    original_lines = before_text.splitlines()
    start_idx = next(
        idx for idx, line in enumerate(original_lines) if line.strip().startswith("return tokens.stream()")
    )
    original_block = "\n".join(original_lines[start_idx : start_idx + 3])
    new_block = "\n".join(
        [
            "                return tokens.stream()",
            "                        .map(token -> {",
            r'                            if (token.equals("-") && (tokens.isEmpty() || tokens.get(tokens.size() - 1).matches("[\(+-]"))) {',
            '                                return "0-";',
            '                            }',
            '                            return token;',
            '                        })',
            '                        .collect(Collectors.toList());',
        ]
    )
    diff = replacement_block(original_block, new_block)

    request = GuidedLoopInputs(
        case_id="java-duplicate-collapse",
        language="java",
        source_path=before_path,
        source_text=before_text,
        error_text="ExpressionEvaluator.java:10: error",
        manifest={},
    )
    strategy = GuidedConvergenceStrategy(client=None, config=GuidedLoopConfig())
    replacement_blocks = strategy._parse_replacement_blocks(diff)

    patched_text, applied, _, _ = strategy._apply_three_way_blocks(request, replacement_blocks)

    assert applied is True
    assert patched_text.count(".collect(Collectors.toList());") == 1
    assert "return token" in patched_text


def test_changed_lines_replacement_blocks_are_summarized() -> None:
    diff_text = (
        "ORIGINAL LINES:\n"
        "print('hello')\n"
        "CHANGED LINES:\n"
        "print('goodbye')\n"
    )

    stats = GuidedConvergenceStrategy._summarize_diff(diff_text)

    assert stats["hunks"] == 1
    assert stats["added_lines"] == 1
    assert stats["removed_lines"] == 1
    assert stats["delete_only"] is False


def test_guided_loop_compile_failure(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('patched')")
    client = StubLLMClient([
        diagnosis_payload("compile-fail"),
        planning_payload("compile-fail-H1"),
        gather_payload(),
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
            main_loop_passes=1,
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
    bad_diff = replacement_block("print('nonexistent')", "print('still wrong')")
    good_diff = replacement_block("print('hello')", "print('refined')")
    client = StubLLMClient(
        [
            diagnosis_payload("loop1"),
            planning_payload("loop1-H1"),
            gather_payload(),
            proposal_payload("propose-pass-1"),
            bad_diff,
            "critique-pass-1",
            planning_payload("loop1-H2", "Trying the remaining hypothesis."),
            gather_payload(),
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
            refine_sub_iterations=1,
            main_loop_passes=1,
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
    assert second_iteration.phases[0].phase.value == "planning"
    assert second_iteration.history_context is not None
    assert second_iteration.history_entry is not None
    planning_phase = second_iteration.phases[0]
    assert '"diagnosis": "loop1 structural diagnosis"' in planning_phase.prompt
    assert "critique-pass-1" in planning_phase.prompt
    assert "Validation summary" in planning_phase.prompt


def test_guided_loop_history_seed_in_prompts(sample_before_file: Path) -> None:
    diff = replacement_block("print('hello')", "print('seeded')")
    client = StubLLMClient([
        diagnosis_payload("seeded"),
        planning_payload("seeded-H1"),
        gather_payload(),
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    history_context = result.trace.iterations[0].history_context
    assert history_context is not None
    assert "manual attempt" in history_context
    assert result.trace.iterations[0].history_entry is not None


def test_hypothesis_reset_before_refinement(sample_before_file: Path) -> None:
    bad_diff = replacement_block("print('missing context')", "print('still missing')")
    client = StubLLMClient(
        [
            diagnosis_payload("retry-1"),
            planning_payload("retry-1-H1"),
            gather_payload(),
            proposal_payload("retry-1"),
            bad_diff,
            "critique-retry-1",
            planning_payload("retry-1-H2", "Switching hypotheses for refinement."),
            gather_payload(),
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    second_iteration = result.trace.iterations[1]
    assert second_iteration.kind == "refine"
    assert second_iteration.hypotheses is None
    planning_phase = second_iteration.phases[0]
    assert planning_phase.phase.value == "planning"
    assert '"diagnosis": "retry-1 structural diagnosis"' in planning_phase.prompt
    assert "critique-retry-1" in planning_phase.prompt
    assert any(
        event.message.startswith("Refinement iteration skipping Diagnose")
        for event in result.events
        if event.iteration == second_iteration.index
    )


def test_stall_detection_archives_hypothesis(sample_before_file: Path) -> None:
    repeated_diff = replacement_block("print('hello')", "print('looped change')")
    compile_command = compile_command_with_error(f"{sample_before_file.name}:1: boom")
    client = StubLLMClient(
        [
            diagnosis_payload("stall-1"),
            planning_payload("stall-1-H1"),
            gather_payload(),
            proposal_payload("stall-1"),
            repeated_diff,
            "critique-stall-1",
            planning_payload("stall-1-H2", "Retrying with the alternate hypothesis."),
            gather_payload(),
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
            main_loop_passes=1,
        ),
    )

    result = strategy.run(request)

    second_iteration = result.trace.iterations[1]
    assert second_iteration.failure_reason == "stall"
    assert second_iteration.hypotheses is None
    telemetry = second_iteration.telemetry
    assert "stall" in telemetry
    assert telemetry["stall"][0]["errorLocation"] == 1
    assert any(event.message.startswith("Stall detected") for event in result.events)


def test_second_main_loop_uses_full_critique_history(sample_before_file: Path) -> None:
    missing_diff = replacement_block("print('unavailable context')", "print('still missing')")
    first_critique = "First loop critique transcript."
    client = StubLLMClient(
        [
            diagnosis_payload("primary-1"),
            planning_payload("primary-1-H1"),
            gather_payload(),
            proposal_payload("primary-1"),
            missing_diff,
            first_critique,
            diagnosis_payload("primary-2"),
            planning_payload("primary-2-H1"),
            gather_payload(),
            proposal_payload("primary-2"),
            missing_diff,
            "Second loop critique transcript.",
        ]
    )
    request = build_request(sample_before_file, [])
    strategy = GuidedConvergenceStrategy(
        client=client,
        config=GuidedLoopConfig(
            interpreter_model="test",
            patch_model="test",
            max_iterations=1,
            refine_sub_iterations=0,
            main_loop_passes=2,
        ),
    )

    result = strategy.run(request)

    assert len(result.trace.iterations) == 2
    second_loop = result.trace.iterations[1]
    assert second_loop.pass_index == 2
    assert second_loop.include_full_critiques is True
    diagnose_phase = next(
        phase for phase in second_loop.phases if phase.phase == GuidedPhase.DIAGNOSE
    )
    assert first_critique in diagnose_phase.prompt