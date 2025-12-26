from __future__ import annotations

import sys
from pathlib import Path


def test_create_case_from_single_file_python_syntax_error(tmp_path: Path) -> None:
    # Import from scripts/ (it's a package).
    from scripts.fix import create_case_from_single_file

    source_file = tmp_path / "bad.py"
    source_text = "def f():\n    return (\n"
    source_file.write_text(source_text, encoding="utf-8")

    dataset_root = tmp_path / "dataset"
    dataset_root.mkdir()

    case_dir, case_id = create_case_from_single_file(
        scratch_dataset_root=dataset_root,
        source_file=source_file,
        language="python",
        compile_command=[sys.executable, "-m", "py_compile", source_file.name],
    )

    assert case_dir.exists()
    assert case_dir.name == case_id
    assert (case_dir / "manifest.json").exists()
    assert (case_dir / "before.py").read_text(encoding="utf-8") == source_text

    # The initial compiler stderr should contain a syntax error.
    stderr = (case_dir / "compiler_stderr.txt").read_text(encoding="utf-8")
    assert stderr.strip() != ""
    assert "SyntaxError" in stderr


def test_create_case_from_single_file_includes_source_filename(tmp_path: Path) -> None:
    from scripts.fix import create_case_from_single_file

    source_file = tmp_path / "Hello.java"
    source_text = "public class Hello { public static void main(String[] a){ } }\n"
    source_file.write_text(source_text, encoding="utf-8")

    dataset_root = tmp_path / "dataset"
    dataset_root.mkdir()

    case_dir, _case_id = create_case_from_single_file(
        scratch_dataset_root=dataset_root,
        source_file=source_file,
        language="java",
        compile_command=["javac", source_file.name],
    )

    # We also write the source filename itself to make resolve_source_path work.
    assert (case_dir / "Hello.java").read_text(encoding="utf-8") == source_text


def test_copy_benchmark_seed_dir_excludes_prior_artifacts(tmp_path: Path) -> None:
    from scripts.fix import copy_benchmark_seed_dir

    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()

    # Minimal required inputs.
    (src / "manifest.json").write_text("{}", encoding="utf-8")
    (src / "before.java").write_text("class X {}\n", encoding="utf-8")
    (src / "compiler_stderr.txt").write_text("1 error\n", encoding="utf-8")

    # Pre-existing artifacts that should NOT be copied.
    (src / "results").mkdir()
    (src / "results" / "something.json").write_text("{}", encoding="utf-8")
    (src / "diffs").mkdir()
    (src / "diffs" / "old.diff").write_text("diff", encoding="utf-8")
    (src / "after").mkdir()
    (src / "after" / "old.java").write_text("class Y {}\n", encoding="utf-8")

    copy_benchmark_seed_dir(src, dest)

    assert (dest / "manifest.json").exists()
    assert (dest / "before.java").exists()
    assert (dest / "compiler_stderr.txt").exists()

    assert not (dest / "results").exists()
    assert not (dest / "diffs").exists()
    assert not (dest / "after").exists()
