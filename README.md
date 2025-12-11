# llm-patch

<p align="center">
  <img src="llm-patch-logo.png" alt="llm-patch logo" width="220" />
</p>

> ⚙️ **Context-aware patch application for imperfect LLM diffs.** llm-patch aligns unified diffs without depending on fragile line numbers so your agent workflows keep moving.

llm-patch absorbs the noisy diffs emitted by code LLMs, finds where each hunk *should* land, and applies it the way a human would—matching on meaning and context instead of brittle coordinates.

---

## Table of Contents

- [Quickstart](#quickstart)
- [Why use llm-patch?](#why-use-llm-patch)
- [Problem → Solution → Benefit](#problem--solution--benefit)
- [Example LLM pipeline](#example-llm-pipeline)
- [How it works](#how-it-works)
- [Landscape of approaches](#landscape-of-approaches)
- [Benchmarks at a glance](#benchmarks-at-a-glance)
- [Installation & compatibility](#installation--compatibility)
- [Usage reference](#usage-reference)
- [Development & testing](#development--testing)
- [Contributing & community](#contributing--community)
- [License & acknowledgments](#license--acknowledgments)
- [Benchmark dataset quickstart](#benchmark-dataset-quickstart)
  - [Patch evaluation scoreboard](#patch-evaluation-scoreboard)

---

## Quickstart

### Getting started in 3 steps

1. **Install**
   ```bash
   pip install llm-patch
   ```
2. **Ask your LLM for a unified diff** that fixes the first compiler error it sees.
3. **Apply the diff** with llm-patch and print the result:
   ```python
   from llm_patch import apply_patch

   patched_text, success = apply_patch(before_code, llm_diff)
   if success:
       print(patched_text)
   else:
       print("Patch did not apply cleanly")
   ```

> ℹ️ Today llm-patch ships as a Python library. A CLI wrapper is on the roadmap—contributions welcome!

### Minimal Python example

```python
from llm_patch import apply_patch

source_code = """
def hello():
    print("Hello, World!")
"""

diff = """@@
 def hello():
-    print("Hello, World!")
+    print("Hello, Universe!")
"""

result, success = apply_patch(source_code, diff)
if success:
    print(result)
```

---

## Why use llm-patch?

- ✅ **Applies diffs when `git apply` and `patch` choke** on stale line numbers or missing context.
- ⏱️ **Cuts manual babysitting** in LLM coding pipelines—no more hand-editing files to match a diff.
- 🧪 **Powers reproducible experiments** thanks to an evaluation harness plus a curated corpus of real failed patches.
- 🔌 **Language agnostic:** works on any text file—code, config, docs.
- 📈 **Demonstrably better** than strict patchers (see benchmarks below).

---

## Problem → Solution → Benefit

### Problem

- LLMs emit unified diffs that rarely match the current file version.
- Traditional patch tools assume perfect line numbers, leading to "patch does not apply" failures.
- Broken diffs stall automated agents and burn operator time.

### Solution

- Ignore line numbers entirely and locate each hunk using surrounding context plus fuzzy matching.
- Apply multiple fallbacks (exact match, whitespace-tolerant, diff-match-patch heuristics, and an Aider-inspired search/replace strategy).
- Recompile / rerun checks automatically to verify that the patch actually fixed the error it targeted.

### Benefit

- Dramatically **higher application rates** on noisy diffs.
- **Less human intervention** in CI/CD loops or autonomous agent workflows.
- **Observable metrics** so improvements can be measured, not guessed.

---

## Example LLM pipeline

```
LLM generates code  ──▶  compilation fails  ──▶  LLM emits unified diff
                                           │
                                           ▼
                                    llm-patch aligns diff
                                           │
                                           ▼
                                Patched file recompiled/tests
```

1. Capture the first compiler error and feed it (plus the broken file) to an LLM.
2. LLM returns a diff that *should* fix just that error.
3. llm-patch applies the diff despite drifting context and hands the updated file back to your build/test step.

---

## How it works

1. **Parse diffs** into hunks while ignoring line numbers.
2. **Match hunks** using layered strategies (exact, relaxed, fuzzy, best-effort search via the Aider algorithm).
3. **Apply edits** only after confidence thresholds are met; delete-only diffs are flagged.
4. **Recompile/retest** with the original command to see if the first error disappeared and overall diagnostics dropped.
5. **Record telemetry** (attempt/applied/success counts, diagnostics) for benchmarking and regression detection.

---

## Landscape of approaches

A growing ecosystem is exploring resilient patching:

- **Aider** pioneered fuzzy chunk replacement for imperfect LLM diffs.
- **Cursor** leans on semantic context when aligning edits.
- **GitHub Copilot Agents** mix structural heuristics with text-based fixes.
- **Google's diff-match-patch** offers approximate text matching but lacks unified-diff parsing out of the box.

llm-patch focuses on being a *standalone*, language-agnostic library dedicated solely to making LLM diff application reliable.

---

## Benchmarks at a glance

- ⚠️ **Git apply** succeeds on only **0.3 %** of the real-world diffs in our corpus.
- 📏 **diff-match-patch** lifts that to **4.9 %**.
- 🚀 **llm-patch's Aider-style strategy** currently lands **10.2 %** end-to-end successes and applies 86 % of diffs—*verified* by recompiling every case.

The full heatmap (per language × problem suite) is included below and regenerated via `scripts/run_patch_eval.py --markdown-report docs/patch_eval_results.md`.

---

## Installation & compatibility

| Component | Support |
| --- | --- |
| Python | 3.9, 3.10, 3.11, 3.12+ |
| Operating Systems | Linux, macOS, Windows |
| Packaging | `pip install llm-patch` (supports virtualenv/conda) |

### Recommended environment setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip
pip install llm-patch
```

> Need fully reproducible runs? Wrap the repo in Docker or use the provided `requirements*.txt` files for dev installs.

---

## Usage reference

### Basic API

```python
from llm_patch import apply_patch

patched_text, success = apply_patch(before_text, unified_diff)
```

### PatchApplier class

```python
from llm_patch import PatchApplier

applier = PatchApplier(similarity_threshold=0.8)
patched_text, success = applier.apply(before_text, diff)
```

### FuzzyMatcher helper

```python
from llm_patch import FuzzyMatcher

matcher = FuzzyMatcher(threshold=0.7)
match_index = matcher.find_best_match(source_lines, pattern_lines)
if match_index is not None:
    print(f"Pattern found at line {match_index}")
```

### Typical workflow tips

1. Store compiler stderr/stdout for each failing file.
2. Capture the *first* error message and feed it to your LLM along with the source file.
3. Apply the resulting diff via llm-patch.
4. Re-run the same compile/test command to verify the fix.

---

## Development & testing

```bash
pip install -r requirements-dev.txt
pytest -v --cov=llm_patch
```

Other helpful commands:

- `pylint src/llm_patch`
- `black src/ tests/`
- `mypy src/llm_patch`
- `pre-commit run --all-files`

New contributions should include unit tests (or evaluation harness updates) that cover the change. Aim to keep or raise coverage for touched modules.

---

## Contributing & community

We welcome issues, benchmarks, and PRs!

**Contribution checklist**

1. Fork & branch (`git checkout -b feature/amazing-feature`).
2. Implement the change plus tests/benchmarks.
3. Run `pytest` and linting before opening the PR.
4. Document user-facing changes in the README or docs.

We follow the [Contributor Covenant](CODE_OF_CONDUCT.md).

---

## License & acknowledgments

- Licensed under the MIT License – see [LICENSE](LICENSE).
- Inspired by the need to reliably apply LLM-generated code patches and the pioneering work from Aider, Cursor, and others.

---

## Benchmark dataset quickstart

- Problem catalog: start with the Expression Evaluator spec in `docs/test_cases.md`.
- Toolchains: install compilers/interpreters as listed in `docs/toolchains.md` (Java, C, Python, TypeScript, plus Ollama models `qwen2.5-coder:7b`, `llama3.2:3b`, and `phi3:mini`).
- Failure harvesting: run `python -m scripts.generate_failures --target-per-language 100` to collect non-compiling samples (`benchmarks/generated/<run_id>/...`).
- First-error diffs: run `python -m scripts.generate_patches --models qwen2.5-coder:7b,llama3.2:3b,phi3:mini` to get minimal diffs per case.
- Patch evaluation: run `python -m scripts.run_patch_eval --algorithms git,diff-match-patch,aider --markdown-report docs/patch_eval_results.md --log-level WARNING` to apply every diff using git apply, diff-match-patch, and the Aider-style matcher.

These artifacts keep the benchmark reproducible so improvements can be measured quantitatively.

### Patch evaluation scoreboard

<!-- Auto-generated by scripts/run_patch_eval.py. Run with --markdown-report to refresh. -->

Results generated from commit `3222602` (3222602f238794d3f7d939f64b6fdd71a36c6e0c).

<table>
  <thead>
    <tr>
      <th rowspan="2">Test Suite</th>
      <th colspan="3">Git patch</th>
      <th colspan="3">diff-match-patch</th>
      <th colspan="3">Aider</th>
    </tr>
    <tr>
      <th>Applied %</th>
      <th>Fixed %</th>
      <th>Compound %</th>
      <th>Applied %</th>
      <th>Fixed %</th>
      <th>Compound %</th>
      <th>Applied %</th>
      <th>Fixed %</th>
      <th>Compound %</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>expr_eval_v1</code> · c</td>
      <td style="background-color:#eadddb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 34.9% (104/298)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.0% (0/104)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.0% (0/298)</td>
      <td style="background-color:#eadddb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 36.2% (108/298)</td>
      <td style="background-color:#f0dadb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 19.4% (21/108)</td>
      <td style="background-color:#f5d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  7.0% (21/298)</td>
      <td style="background-color:#d6e5dd; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 88.3% (263/298)</td>
      <td style="background-color:#f6d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  5.7% (15/263)</td>
      <td style="background-color:#f6d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  5.0% (15/298)</td>
    </tr>
    <tr>
      <td><code>expr_eval_v1</code> · java</td>
      <td style="background-color:#eadddb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 35.4% (105/297)</td>
      <td style="background-color:#f7d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  2.9% (3/105)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  1.0% (3/297)</td>
      <td style="background-color:#f2d9da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 14.5% (43/297)</td>
      <td style="background-color:#ebdcdb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 32.6% (14/43)</td>
      <td style="background-color:#f6d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  4.7% (14/297)</td>
      <td style="background-color:#dae3dc; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 76.8% (228/297)</td>
      <td style="background-color:#f1dadb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 18.9% (43/228)</td>
      <td style="background-color:#f2d9da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 14.5% (43/297)</td>
    </tr>
    <tr>
      <td><code>expr_eval_v1</code> · python</td>
      <td style="background-color:#e9dddb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 38.0% (115/303)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.9% (1/115)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.3% (1/303)</td>
      <td style="background-color:#e6dedb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 46.5% (141/303)</td>
      <td style="background-color:#f5d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  7.1% (10/141)</td>
      <td style="background-color:#f7d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  3.3% (10/303)</td>
      <td style="background-color:#d5e5dd; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 90.1% (273/303)</td>
      <td style="background-color:#f4d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  9.2% (25/273)</td>
      <td style="background-color:#f5d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  8.3% (25/303)</td>
    </tr>
    <tr>
      <td><code>expr_eval_v1</code> · typescript</td>
      <td style="background-color:#e6dfdb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 47.4% (143/302)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.0% (0/143)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.0% (0/302)</td>
      <td style="background-color:#f0dadb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 20.9% (63/302)</td>
      <td style="background-color:#efdbdb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 22.2% (14/63)</td>
      <td style="background-color:#f6d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  4.6% (14/302)</td>
      <td style="background-color:#d5e5dd; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 88.7% (268/302)</td>
      <td style="background-color:#f2d9da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 14.6% (39/268)</td>
      <td style="background-color:#f3d9da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 12.9% (39/302)</td>
    </tr>
    <tr>
      <td><strong>Average</strong></td>
      <td style="background-color:#e9dddb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 38.9% (467/1200)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.9% (4/467)</td>
      <td style="background-color:#f8d7da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  0.3% (4/1200)</td>
      <td style="background-color:#ecdcdb; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 29.6% (355/1200)</td>
      <td style="background-color:#f2dada; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 16.6% (59/355)</td>
      <td style="background-color:#f6d8da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); ">  4.9% (59/1200)</td>
      <td style="background-color:#d6e5dd; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 86.0% (1032/1200)</td>
      <td style="background-color:#f3d9da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 11.8% (122/1032)</td>
      <td style="background-color:#f4d9da; text-align:center; white-space:nowrap; font-family:var(--font-mono,monospace); "> 10.2% (122/1200)</td>
    </tr>
  </tbody>
</table>