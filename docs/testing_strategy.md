# Testing Strategy & Benchmark Pipeline

This document explains how llm-patch will build, maintain, and evaluate a large-scale corpus of real LLM-generated diffs. The goal is to benchmark patching algorithms quantitatively and repeatably on realistic failures rather than synthetic noise.

## Guiding Principles

1. **Reality over theory** – Every test case must originate from real LLM output (code + diffs). No random corruption or artificial noise.
2. **Ground-truth anchored** – Each case stores the original broken code, the compiler/interpreter diagnostics, the diffs proposed by multiple LLMs, and an accepted truth version for validation.
3. **Transparent metrics** – Success is measured per algorithm, per language, per model, so regressions are obvious.
4. **Reproducible pipelines** – Scripts can regenerate datasets at will, parametrised by language, model, prompt set, and failure filters.

## Dataset Layout

```
benchmarks/
  metadata.json                # High-level info (languages, versions, compiler flags)
  cases/
    <language>/<context>/<case_id>/
      before.<ext>             # Broken code emitted by generator
      compile_error.txt        # Captured stderr/stdout from compiler
      diffs/
        <model_name>.diff      # Unified diff produced by each LLM
      truth/<source>.patched   # Agreed "after" file (consensus or curation)
      manifest.json            # Machine-readable metadata (prompt hash, timestamps, tags)
```

- `<language>` – `java`, `c`, `cpp`, `typescript` initially.
- `<context>` – optional bucket such as `api-client`, `algorithms`, `config-parser`.
- `<case_id>` – deterministic UUID or hash (e.g., `modelName_promptHash_retryIndex`).
- `manifest.json` contains: generator prompt ID, model/config used, compiler versions, detected failure class, truth provenance (consensus, manual, etc.).

## Test Case Generation Pipeline

### 1. Prompt Library
- Maintain `prompts/<language>/*.md` describing desired programs ("Implement Dijkstra", "REST client", etc.).
- Track metadata (complexity, required APIs, allowed libraries) to ensure coverage variety.

### 2. Candidate Generation Script
- CLI: `python -m scripts.generate_failures --language java --count 100 --provider openai --model gpt-4o-mini --prompt-set prompts/java`
- Supports providers `ollama`, `openai`, and future third-parties via a pluggable adapter layer.
- Provider config order of precedence:
  1. CLI flags (e.g., `--openai-api-key`)
  2. Environment variables loaded from `.env` (`OPENAI_API_KEY`, optional `ANTHROPIC_API_KEY`)
  3. Provider-specific defaults (e.g., `OLLAMA_HOST=http://localhost:11434`).
- Emits provisional files into `artifacts/tmp/<language>/<run_id>/candidate_<n>.<ext>` with embedded metadata.

### 3. Syntactic Validation & Filtering
- For each candidate, run the appropriate compiler/tooling:
  - Java → `javac`
  - C → `gcc`
  - C++ → `g++`
  - TypeScript → `tsc --noEmit`
- Capture command, exit code, stdout, stderr, and compiler version.
- If compilation **succeeds**, discard the candidate.
- If compilation **fails**, snapshot:
  - Original source (`before.<ext>`)
  - `compile_error.txt`
  - `manifest.json` (prompt hash, seed, model, compiler command, timestamp).
- Continue until each language accumulates ≥100 failure cases.

### 4. Truth File Derivation
- Collect diffs or complete files from multiple "fixer" models (can reuse generation script with different prompts instructing a fix).
- Accept a truth file when both conditions hold:
  1. At least two independent models produce identical patched files **or** a human reviewer signs off.
  2. The file compiles successfully with the same toolchain used for failure detection.
- Store truth files under `truth/<source>.patched` and record provenance (`consensus`, `manual_review`) inside `manifest.json`.

### 5. Diff Harvesting
- For each failing case, prompt each model under test to provide a unified diff relative to `before.<ext>`.
- Validate response format: ensure hunks start with `@@`, summarise missing context, and normalise whitespace.
- Save each diff separately under `diffs/<model_name>.diff` along with generation metadata (`temperature`, `max_tokens`, prompt ID).

## Evaluation Harness

1. **Inputs** – For every `<language>/<context>/<case_id>`, load `before`, `truth`, compiler diagnostics, and the set of diffs.
2. **Engines Under Test** – Include:
   - Baseline `patch`/`git apply` for reference.
   - Existing llm-patch algorithms and experimental variants.
3. **Execution** – For each diff:
   - Run the engine with `before` + diff → produce `candidate_after`.
   - Compare against `truth` (byte-for-byte match, optionally AST-aware checks later).
   - Record status (`success`, `partial`, `failed`), match confidence, and diagnostics (where did fuzzy matching land?).
4. **Metrics** – Emit aggregated CSV/JSON: success rate per engine per language, failure taxonomy, mean similarity score, percentage requiring fuzzy fallback.
5. **Regression Gate** – Integrate with CI to fail if a change reduces success rate beyond configurable tolerance (e.g., −1% absolute).

## Automation & Tooling

- **Scripts directory** – `scripts/` will host
  - `generate_failures.py` (Stage 1–3)
  - `harvest_diffs.py` (Stage 5)
  - `derive_truth.py` (Stage 4 workflow aid)
  - `run_benchmark.py` (Evaluation harness)
- **Metadata helpers** – Provide `llm_patch.dataset.schema` for loading/saving manifest objects with type hints and validation.
- **Caching** – When using remote APIs, cache prompts/responses under `artifacts/cache/` keyed by hash to avoid duplicate spend.
- **Compiler availability** – At startup, scripts verify toolchain presence and version; missing dependencies should raise actionable errors.
- **Secrets management** – `.env` (already added to repo root) defines placeholders for `OPENAI_API_KEY` and optional provider secrets. Runtime scripts should respect `.gitignore` so secrets never commit.

## Implementation Plan (Assuming Baseline Patch Tool Exists)

1. **Define schemas (Week 1)**
   - Create Pydantic/dataclass schema for `TestCaseManifest` and `DiffMetadata`.
   - Build helper to materialise directory layout per case.

2. **Implement failure generator (Week 1–2)**
   - Adapter layer for OpenAI + Ollama clients with streaming logs.
   - Prompt selection + templating engine.
   - Compiler executor + log capture; ensures 100 failing samples per language before exit.

3. **Truth aggregation workflow (Week 2)**
   - CLI to request fix attempts from configured models.
   - Auto-consensus detection + optional manual approval CLI.
   - Re-run compilers/tests on accepted truth artifacts.

4. **Diff harvesting CLI (Week 2–3)**
   - For each failing case, request diffs from LLM set, validate format, store under `diffs/`.
   - Normalise line endings, deduplicate identical diffs.

5. **Evaluation runner (Week 3)**
   - Build `benchmarks/run_benchmark.py` that loads cases, executes:
     - Baseline GNU `patch`
     - llm-patch core algorithm (`PatchApplier`)
     - Experimental strategies (future modules)
   - Output JSON/CSV summary + Markdown report for CI badges.

6. **Continuous integration (Week 3)**
   - GitHub Action to run `run_benchmark.py --smoke` on pull requests (sample subset).
   - Nightly job to run full suite and push metrics artifact.

7. **Documentation & onboarding (ongoing)**
   - Keep this document updated.
   - Provide quickstart guides inside `docs/` for running generators and benchmarks locally.

With this pipeline in place, llm-patch gains an ever-growing, real-world benchmark suite that keeps the patching algorithms honest and quantifiably robust.

## Initial Generation Campaign (Ollama-only)

To bootstrap the dataset we will focus on one well-understood problem—`expr_eval_v1`, the **Expression Evaluator** described in `docs/test_cases.md`. The first large batch will:

- **Languages**: Java, C, Python, and TypeScript.
- **Models (Ollama provider)**: `qwen2.5-coder:7b`, `llama3.2:3b`, and `phi3:mini`.
- **Target**: ≥100 failing samples per language (compile errors, runtime exceptions surfaced by unit smoke tests, or lint/type failures for TypeScript).

The script introduced in this change (`scripts/generate_failures.py`) orchestrates the process end-to-end:

1. Builds prompts from the canonical problem description (problem ID remains configurable so future problem sets can reuse the pipeline).
2. Calls the requested Ollama models sequentially, capturing raw code outputs.
3. Writes temporary sources and runs the appropriate toolchain checks (see `docs/toolchains.md`).
4. Discards successful executions; persists failure artifacts (source, stdout/stderr logs, manifest metadata) under `benchmarks/generated/<run_id>/...`.

Future iterations can point the same CLI at OpenAI/Anthropic adapters and additional problem IDs without rewiring the workflow.

## Automated First-Error Patch Harvesting

Once failing samples exist, we request *targeted* diffs that only address the very first compiler/interpreter error. This keeps the dataset granular and makes it easier to study partial-application behavior in llm-patch.

- **Script**: `scripts/generate_patches.py`
- **Inputs**: existing case directories (default `benchmarks/generated/*`), compiler output, and the raw `before.<ext>` file.
- **Process**:
   1. Parse the first non-empty line(s) of `compiler_stderr.txt` (falling back to `compiler_stdout.txt`) to capture the first error message verbatim.
   2. Prompt each configured model independently with `(a) the first error, (b) the original source code)` and instructions to emit the smallest possible unified diff that fixes *only* that error.
   3. Store each response under `diffs/<model>.diff`, using a sanitized model slug (e.g., `qwen2.5-coder_7b.diff`).
   4. Skip already-generated diffs unless `--overwrite` is provided; resumable runs let us accumulate patches as new cases land in the corpus.
- **Usage example**:

   ```bash
   python3 -m scripts.generate_patches \
         --run-ids 20251210T162236Z \
         --languages java,c,python,typescript \
         --models qwen2.5-coder:7b,llama3.2:3b,phi3:mini \
         --limit-per-language 25
   ```

The resulting diffs give the patching engine realistic, model-specific guidance for each failure mode without conflating multiple fixes into a single sample. Later stages (truth derivation) can combine these diffs to reach consensus “after” files.

## Patch Application & Scoring (Steps 4–7)

With failures + diffs in place, we execute the remainder of the user-defined strategy as follows:

1. **Apply diffs via multiple algorithms.** Each LLM-generated patch is attempted with three engines: the strict `git apply` flow, Google Diff Match Patch, and an Aider-inspired search/replace matcher (ported from `aider/coders/editblock_coder.py`). This gives us comparable baselines for line-number, text-diff, and semantic block matching.
2. **Recompile / relint the patched code.** We rerun the original `compile_command` captured in every `manifest.json`, mirroring the exact toolchain invocation that produced the failure diagnostics in the first place.
3. **Judge patch validity.** A patch registers as successful only when:
   - the original first error string is absent from the new compiler output,
   - the total number of error diagnostics decreases relative to the stored baseline,
   - and the diff does more than delete code (at least one addition is required).
4. **Record per-attempt telemetry.** For every `(case, model, algorithm)` tuple we emit a JSON artifact noting whether the patch applied, compiler return codes, before/after error counts, hunk statistics, and the final success verdict. Aggregations roll up to per-algorithm success rates.

### Automation Script: `scripts/run_patch_eval.py`

Run the entire sequence across one or more generation runs:

```bash
python -m scripts.run_patch_eval \
   --run-ids 20251210T162236Z \  # optional, defaults to all runs
   --algorithms git,diff-match-patch \
   --languages java,c,python,typescript
```

Key behaviours:

- Results land under each case directory inside `results/<model_slug>__<algorithm>.json`.
- Summaries print to stdout (attempts/applied/success per algorithm).
- Use `--limit-per-language` for smoke tests and `--overwrite` to recompute existing verdicts.
- Add `--markdown-report <path>` to emit a README-ready HTML table (complete with grouped columns per algorithm and a red→green heatmap) that breaks down applied %, fixed %, and compound success % for every `problem_id × language` suite, along with the git commit hash used for that evaluation.

These artifacts satisfy steps 4–7 of the broad testing strategy: patch attempts, recompilation, validation, and scoring for every algorithm under evaluation.
