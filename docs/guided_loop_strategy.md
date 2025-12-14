# Guided Convergence Loop Strategy

The [Guided Convergence Loop](https://github.com/trickl/llm-guided-convergence-loop) replaces one-shot
patch generation with explicit, inspectable phases (Interpret → Diagnose → Propose → Constrain → Patch →
Critique → Refine → Converge). This document captures how the pattern will be implemented within
`llm-patch`, how we will visualise it in the reviewer UI, and how observability remains consistent with
existing strategies.

## Objectives

1. **Implementation scaffolding** – codify the loop as a first-class strategy so we can orchestrate phases,
   retry logic, and machine checks in code rather than prompt spaghetti.
2. **UI introspection** – surface per-phase prompts, responses, checks, and verdicts inside the reviewer so
   humans can trace convergence history.
3. **Observability + compatibility** – emit uniform events/metrics that coexist with git/diff-match-patch/
aider results without breaking historical datasets.

## Implementation roadmap

### 1. Strategy abstractions

- `src/llm_patch/strategies/base.py` now defines `PatchRequest`, `PatchResult`, `PatchStrategy`, and
  streaming `StrategyEvent`s. All algorithms (existing and future) can implement the same contract, which
  keeps `run_patch_eval.py` agnostic to the actual approach.
- Observers can subscribe to events (e.g., JSONL logs, websocket feeds, metrics), unlocking runtime
  visibility without tight coupling.

### 2. Guided loop scaffolding

- `src/llm_patch/strategies/guided_loop/phases.py` enumerates the canonical phases plus per-iteration
  artifacts. Every iteration stores prompts, raw model output, machine checks, and optional reviewer notes.
- `GuidedConvergenceStrategy` (controller module) currently generates a **plan trace** – the ordered prompts
  that will be issued for each phase/iteration. This is intentionally executable-agnostic so we can plug in
  different LLM backends.
- Next implementation steps:
  1. Inject an `LLMClient` adapter and implement `_execute_phase` that (a) renders the template,
     (b) calls the appropriate model, (c) normalises the response, and (d) records artifacts/events.
  2. Add deterministic machine checkpoints between Critique and Refine (patch apply + compile).
  3. When a compile passes, mark the iteration as `accepted` and exit; otherwise record critique findings
     and continue.
  4. Persist each iteration trace under `benchmarks/.../results/<model>__guided-loop.json` so historical
     runs remain intact.

### 3. CLI + dataset integration

- Extend `scripts/generate_patches.py` with a `--strategy=guided-loop` flag that instantiates
  `GuidedConvergenceStrategy`, feeds it the case metadata, and writes:
  - `diffs/<model>.diff` (latest accepted diff)
  - `results/<model>__guided-loop.json` (full trace + machine checks)
  - `artifacts/<model>__guided-loop/iteration-*/phase-*.md` (optional human-readable exports)
- Update `scripts/run_patch_eval.py` so `ALGORITHM_LABELS` includes `guided-loop` and the evaluator can read
  the trace file to derive metrics (e.g., "iterations until success"). Because guided loop emits events,
  `run_patch_eval` can remain simple: it only needs to know whether the patch applied and tests passed.

## Reviewer UI visualisation plan

1. **Data contract**
   - `CaseDetail` will gain an optional `strategyTrace` field (see `ui/reviewer-ui/src/types.ts`). Each
     trace contains iterations, and each iteration contains ordered phase artifacts.
   - Backend endpoints should include the trace for guided-loop generated patches, but may omit it for
     legacy strategies (field stays `null`).

2. **Timeline panel**
   - Add a vertical timeline dock below the diff panel that lists `Iteration N` + phase chips. Hover/click
     reveals prompt/responses rendered in formatted cards.
   - Badge colours mirror `PhaseStatus` (planned, running, completed, failed). Machine checks display as
     pill indicators (e.g., ✅ compile, ⚠ lint).

3. **Phase detail drawer**
   - Selecting a phase opens a drawer showing:
     - Prompt + response text
     - Structured critique checklist (constraints satisfied, lines touched, etc.)
     - Relevant artifacts (diff preview for Generate/Refine, stderr snippet for Critique)
   - Drawer also exposes "copy prompt" actions for reproducing runs manually.

4. **Fallback behaviour**
   - If `strategyTrace` is missing, the UI defaults to today’s layout (Before/After + Diff/Error panels),
     so git/aider outputs still render without change.

## Observability + metrics

- Every phase transition emits a `StrategyEvent` that can be streamed to disk or telemetry sinks. Event
  schema: `{kind, strategy, phase, iteration, timestamp, data}`.
- Deterministic machine checks (patch apply, compile, tests) attach their raw stdout/stderr to the phase’s
  `machine_checks` map plus event payloads.
- Summary metrics to capture per iteration: lines touched, number of critiques raised, compile runtime.
- For UI debugging we will persist the trace JSON next to existing `results/*.json` so both human reviewers
  and automated tooling share a single source of truth.

## Compatibility considerations

- Existing CLI workflows keep their behaviour: unless `--strategy=guided-loop` is passed, git/dmp/aider
  pipelines remain untouched.
- Data formats are strictly additive (new JSON blobs + optional UI fields), so previous datasets continue to
  load.
- Observability hooks are optional; strategies that do not emit events will simply operate silently.

By landing the scaffolding + plan above we have a clear path to a fully instrumented, UI-friendly Guided
Convergence Loop that coexists with our current patching algorithms.
