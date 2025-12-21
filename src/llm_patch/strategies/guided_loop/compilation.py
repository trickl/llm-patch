"""Compile/test execution helpers for the guided-loop strategy.

This module intentionally contains the subprocess + temp-dir logic used during the
Critique phase so the main controller can focus on orchestration.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .models import GuidedLoopInputs


def run_compile(request: GuidedLoopInputs, patched_text: str) -> Dict[str, Any]:
    command = list(request.compile_command or [])
    if not command:
        return {"command": [], "returncode": None, "stdout": "", "stderr": ""}
    try:
        with tempfile.TemporaryDirectory(prefix="llm_patch_guided_") as tmpdir:
            tmp_path = Path(tmpdir)
            for rel_path in compile_target_paths(request, command):
                destination = tmp_path / rel_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(patched_text, encoding="utf-8")
            proc = subprocess.run(
                command,
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                check=False,
            )
            return {
                "command": command,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
    except OSError as exc:  # pragma: no cover - defensive
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def compile_target_paths(request: GuidedLoopInputs, command: Sequence[str]) -> List[Path]:
    """Return the relative file paths that should contain the patched source."""

    source_suffix = Path(request.source_path.name).suffix.lower()
    targets: List[Path] = []
    for token in command:
        if not token or token.startswith("-"):
            continue
        candidate = Path(token)
        suffix = candidate.suffix.lower()
        if not suffix or (source_suffix and suffix != source_suffix):
            continue
        if candidate.is_absolute():
            relative_candidate = Path(candidate.name)
        else:
            relative_candidate = candidate
        if relative_candidate not in targets:
            targets.append(relative_candidate)
    if not targets:
        targets.append(Path(request.source_path.name))
    return targets
