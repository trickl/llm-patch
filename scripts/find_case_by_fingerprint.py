#!/usr/bin/env python3
"""Locate benchmark cases by their fingerprint identifier."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find a benchmark case by fingerprint")
    parser.add_argument("fingerprint", help="Fingerprint to match (prefix ok)")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("benchmarks/generated"),
        help="Dataset root (defaults to benchmarks/generated)",
    )
    parser.add_argument(
        "--languages",
        type=str,
        help="Optional comma-separated language filter",
    )
    return parser.parse_args()


def iter_case_dirs(root: Path, languages: Iterable[str] | None) -> Iterable[Path]:
    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir():
            continue
        for lang_dir in sorted(run_dir.iterdir()):
            if not lang_dir.is_dir():
                continue
            if languages and lang_dir.name not in languages:
                continue
            for case_dir in sorted(lang_dir.iterdir()):
                if case_dir.is_dir():
                    yield case_dir


def compute_fingerprint(run_id: str, case_id: str, before_path: Path) -> str:
    try:
        text = before_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    digest = hashlib.sha256()
    digest.update(run_id.encode())
    digest.update(b":")
    digest.update(case_id.encode())
    digest.update(b":")
    digest.update(text.encode())
    return digest.hexdigest()[:12]


def main() -> None:
    args = parse_args()
    prefix = args.fingerprint.lower()
    languages = None
    if args.languages:
        languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]

    matches: list[tuple[str, Path]] = []
    for case_dir in iter_case_dirs(args.root, languages):
        try:
            before_path = next(case_dir.glob("before.*"))
        except StopIteration:
            continue
        run_id = case_dir.parents[1].name  # /generated/<run>/<lang>/<case>
        case_id = case_dir.name
        fingerprint = compute_fingerprint(run_id, case_id, before_path)
        if fingerprint.startswith(prefix):
            matches.append((fingerprint, case_dir))

    if not matches:
        print("No cases matched fingerprint", prefix)
        sys.exit(1)

    for fingerprint, case_dir in matches:
        lang = case_dir.parent.name
        run_id = case_dir.parents[1].name
        print(f"{fingerprint}\t{run_id}\t{lang}\t{case_dir}")
    sys.exit(0)


if __name__ == "__main__":
    main()
