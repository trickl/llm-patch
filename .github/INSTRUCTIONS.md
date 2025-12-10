# GitHub Instructions

Welcome to the **llm-patch** repository! To understand the motivation, architecture, and roadmap of this project, please **start with the [README](../README.md)**. It captures the high-level context you will need before making any changes.

## Python Best Practices for This Repo

To keep contributions consistent and maintainable, please follow these guidelines:

1. **Embrace type safety**
   - Add type hints to all public functions, methods, and return values.
   - Prefer `dataclasses` or typed `NamedTuple`s when passing structured data.

2. **Document intent**
   - Include concise docstrings that explain *why* a function exists, not just what it does.
   - Add in-line comments when implementing heuristics or fuzzy matching logic to explain edge cases.

3. **Keep functions focused**
   - Favor small, composable functions over monolithic ones.
   - When adding a new matching or scoring heuristic, isolate it behind a descriptive helper.

4. **Test first, test often**
   - Cover new behavior with `pytest` cases in `tests/`.
   - Reproduce interesting edge cases with realistic fixture data so regressions are obvious.

5. **Stay lint- and format-friendly**
   - Run `black`, `pylint`, and `mypy` (see the README for commands) before pushing.
   - Respect existing configuration files such as `.pre-commit-config.yaml` and `.pylintrc`.

6. **Prefer clarity over cleverness**
   - Choose explicit variable names and avoid deeply nested conditionals when possible.
   - Use early returns to simplify control flow.

7. **Log, don’t print**
   - Rely on the project’s logging utilities for diagnostics instead of `print` statements.

## Pull Request Checklist

Before opening a PR, make sure you:

- Re-read the [README](../README.md) to ensure your change aligns with the project scope.
- Add or update tests covering your change.
- Run `pytest`, `black`, `pylint`, and `mypy` locally (or via pre-commit) and ensure they pass.
- Provide a concise description that highlights the problem, the solution, and any trade-offs.

Thanks for contributing to llm-patch! 🎉
