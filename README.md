# llm-patch

<p align="center">
  <img src="llm-patch-logo.png" alt="llm-patch logo" width="220" />
</p>

> ⚙️ **Guided, small-model-friendly patching.** llm-patch orchestrates an iterative diagnose→plan→patch loop so even mid-tier models can land reliable fixes.

llm-patch is a **staged repair workflow** plus a **robust patch applier**. Given a failing compile/test and the first error, it runs a tight loop: generate multiple hypotheses (to avoid lock-in), pick one to test, describe the intended fix in English, emit a minimal edit, apply it with fuzzy/intent matching, then recompile and critique. This makes the process more reliable with smaller models and more transparent for humans—each step is inspectable, and failures become actionable rather than mysterious.

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

### Docker sandbox (fix + inspect UI)

This repo also includes a **Docker execution envelope** that can run the existing guided-loop workflow safely (read-only `/project`, writable `/workspace`) and optionally expose the **reviewer UI** to inspect results.

#### Recommended: pull the official image

Most users should **pull** the prebuilt image rather than building locally:

```bash
docker pull docker.io/trickl/llm-patch:latest
```

You can also pin to a specific version tag (recommended for reproducibility):

```bash
docker pull docker.io/trickl/llm-patch:0.1.0
```

#### Build the image

```bash
docker build -t llm-patch:local .
```

#### Run `fix` and preserve artifacts

Run against a single file and keep the scratch dataset so it can be inspected later:

```bash
WORKDIR=/tmp/llm-patch

docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v "$WORKDIR":/workspace \
  -e OLLAMA_HOST="http://127.0.0.1:11434" \
  docker.io/trickl/llm-patch:latest \
  fix MyFile.java \
    --model qwen2.5-coder:7b \
    --keep-workdir
```

Notes:

- `--keep-workdir` is required for inspection.
- By default, STDOUT is **diff-only**; progress/diagnostics go to STDERR.
- If you want to **see progress live** *and* save both the diff and the log, use `tee`:

  ```bash
  WORKDIR=/tmp/llm-patch

  docker run --rm \
    --network host \
    --user "$(id -u):$(id -g)" \
    -v "$(pwd)":/project:ro \
    -v "$WORKDIR":/workspace \
    -e OLLAMA_HOST="http://127.0.0.1:11434" \
    docker.io/trickl/llm-patch:latest \
    fix MyFile.java --keep-workdir \
    1> "$WORKDIR/final.diff" \
    2> >(tee "$WORKDIR/run.log" >&2)
  ```

  (This uses Bash process substitution; if your shell doesn’t support it, you can still redirect `2> "$WORKDIR/run.log"` and tail it in another terminal.)
- The wrapper snapshots each outer cycle as its own record (e.g. `guided-loop-cycle-001`, `guided-loop-cycle-002`, …) so you can review every cycle in the UI.
- The input can be either:
  - a single source file path (or just a filename under `/project` in Docker), or
  - a benchmark run directory (advanced / benchmarking only) via `--dataset-root`.
- `--outer-cycles` is optional: it’s a safety cap on how many “first-error” fix attempts to try. The run still stops early if it stops making progress.

#### Production-style single file usage

For “real” use, you typically want to point at **your file**, not the benchmark dataset.

In Docker, if your repo is mounted at `/project:ro`, you can pass just the filename:

```bash
docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v /tmp/llm-patch:/workspace \
  -e OLLAMA_HOST="http://127.0.0.1:11434" \
  docker.io/trickl/llm-patch:latest \
  fix MyFile.java --keep-workdir
```

The wrapper will generate a temporary run directory under `/workspace` automatically.

If the tool cannot infer the compile command for your file type, provide one explicitly:

```bash
docker.io/trickl/llm-patch:latest fix MyFile.java \
  --compile "javac MyFile.java" \
  --keep-workdir
```

#### Run `inspect` (starts the UI web service)

Using the **same** `/workspace` mount as above:

```bash
docker run --rm \
  -p 4173:4173 \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v /tmp/llm-patch:/workspace \
  docker.io/trickl/llm-patch:latest \
  inspect
```

Open:

- `http://127.0.0.1:4173`

If you want to inspect a specific preserved dataset root, you can override auto-discovery:

```bash
docker.io/trickl/llm-patch:latest inspect --dataset-root /workspace/llm-patch/fix-*/dataset
```

Tip: if you built locally, you can replace `docker.io/trickl/llm-patch:latest` with `llm-patch:local`.

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

- ✅ **Built for smaller LLMs.** By splitting diagnosis, planning, patching, and critique into separate prompts, the system avoids the “one big leap” that mid-tier models routinely fumble.
- 🔍 **Hypothesis tracking = debuggability.** Each loop emits human-readable hypotheses, decisions, and critiques so engineers can see *why* a run failed instead of guessing.
- 🧠 **Intent before syntax.** The model returns “before/after” snippets, and llm-patch infers the change with fuzzy, line-number-aware alignment—perfect diffs are optional.
- 🧪 **Benchmark-backed.** Every strategy is evaluated against real, compiler-busted programs generated by actual models across C, Java, Python, and TypeScript.
- 🔌 **Language agnostic & parser-free.** Because the pipeline works in text space (with optional token cues), it survives syntax errors and applies equally to config files, code, or docs.
- ♻️ **Single-error focus.** Fixing the top-most error prevents cascading confusion and keeps loops short, cheap, and easy to rerun.

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

That diagram *was* effectively describing a “one-shot” workflow (ask for a diff, try to apply it, recompile). It’s a common baseline, but it undersells the actual innovation here.

llm-patch’s core contribution is a **staged repair loop** (internally referred to as the `guided-loop` strategy) that turns patching into an iterative, observable procedure.

### One-shot baseline (what many tools do)

```
compile fails  ──▶  LLM asked for diagnosis+fix+diff in one step  ──▶  attempt apply  ──▶  recompile
```

This can work with frontier models, but smaller models often:
- lock onto the wrong root cause (compiler errors are frequently downstream symptoms)
- emit syntactically broken or misaligned diffs

### llm-patch staged repair loop (the project’s focus)

```
compile fails
  │
  ▼
extract first error + focused, line-numbered code window
  │
  ▼
DIAGNOSE: generate multiple mutually exclusive hypotheses (English only)
  │
  ▼
PLAN/PROPOSE: pick a hypothesis + describe the intended change (English only)
  │
  ▼
GENERATE PATCH: produce “before/after” snippets (not a perfect unified diff)
  │
  ▼
APPLY: fuzzy/intent-based alignment lands the change in the right place
  │
  ▼
RECOMPILE/TEST + CRITIQUE
  ├─ success: stop
  └─ failure: reject hypothesis → try next → (optionally) re-diagnose with new evidence
```

The key utility is that each step is small and inspectable, which makes mid-tier models far more reliable and makes failures actionable for humans.

---

## How it works

The staged repair loop (internally: `guided-loop`) breaks patching into small, testable steps so mid-tier models can iterate without getting stuck.

1. **Diagnose (English-only).** Feed the compiler stderr plus a focused code window; the model produces multiple mutually exclusive hypotheses, preventing lock-in on a single (possibly wrong) explanation.
2. **Plan & propose.** The loop selects the most promising hypothesis, then asks for a plain-English intervention plan. Keeping this step non-code preserves observability and makes failure modes obvious.
3. **Generate patch.** Only after the intent is clear do we request code edits. The prompt includes numbered context, caret-token annotations, and precise error-position metadata so the model never has to infer line numbers.
4. **Apply with intent matching.** Instead of trusting raw diffs, llm-patch compares “before” and “after” snippets, uses fuzzy/Aider-style alignment to locate the intended region, and applies the change—even when whitespace or surrounding code drifted.
5. **Compile/test & critique.** The system rebuilds with the original command, checks whether the targeted error vanished, and records a critique entry. Failed hypotheses are retired; the loop either tries the next hypothesis or restarts Diagnose with the new evidence.
6. **Benchmark + telemetry.** Every run logs strategy traces, success/failure reasons, and per-sample metrics, feeding the included harness so improvements are measurable across languages and models.

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
- 🚀 **llm-patch's Aider-style strategy** currently lands **10.2 %** end-to-end successes and applies 86 % of diffs—*verified* by recompiling every benchmark program.

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
- First-error diffs: run `python -m scripts.generate_patches --models qwen2.5-coder:7b,llama3.2:3b,phi3:mini` to get minimal diffs per benchmark program.
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