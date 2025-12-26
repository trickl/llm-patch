from __future__ import annotations

import json
from pathlib import Path


class _ResultStub:
    def __init__(
        self,
        *,
        applied: bool = True,
        compile_returncode: int | None = 1,
        compile_stderr: str = "",
        compile_stdout: str = "",
        success: bool = False,
        notes: str = "",
        patch_diagnostics: str = "",
        diff_text: str | None = None,
        after_text: str | None = None,
    ) -> None:
        self.applied = applied
        self.compile_returncode = compile_returncode
        self.compile_stderr = compile_stderr
        self.compile_stdout = compile_stdout
        self.success = success
        self.notes = notes
        self.patch_diagnostics = patch_diagnostics
        self.diff_text = diff_text
        self.after_text = after_text
        self.trace = None


def test_write_result_payload_includes_before_stdout_stderr(tmp_path: Path) -> None:
    from scripts.run_guided_loop import write_result_payload

    case_dir = tmp_path / "case"
    case_dir.mkdir(parents=True)

    (case_dir / "compiler_stderr.txt").write_text("file.java:1: error: boom\n1 error\n", encoding="utf-8")
    (case_dir / "compiler_stdout.txt").write_text("some stdout\n", encoding="utf-8")

    manifest = {"case_id": "java-foo", "language": "java"}
    result = _ResultStub(compile_stderr="file.java:1: error: boom\n1 error\n")

    payload_path = write_result_payload(
        case_dir=case_dir,
        diff_path=None,
        after_path=None,
        model="qwen2.5-coder:7b",
        manifest=manifest,
        result=result,
    )

    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    assert payload["stderr_before"] == "file.java:1: error: boom\n1 error\n"
    assert payload["stdout_before"] == "some stdout\n"

    # Ensure the numeric counts still reflect the compiler stderr before/after.
    assert payload["errors_before"] == 1
    assert payload["errors_after"] == 1
