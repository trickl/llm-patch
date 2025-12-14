# Hypothesis Lifecycle Overhaul – Implementation Plan

_Last updated: 2025-12-14_

This document lays out a language-agnostic roadmap for weaving the nine structural improvements into the Guided Loop strategy. It highlights the primary touch points inside `src/llm_patch/strategies/guided_loop/` and supporting modules.

---

## Phase 0 – Scaffolding & Data Model

1. **Introduce Hypothesis primitives**
   - File: `src/llm_patch/strategies/guided_loop/phases.py` (or a new `hypothesis.py`).
   - Add dataclasses for `Hypothesis`, `HypothesisSet`, and lightweight state tracking (status, retries, falsification evidence).
   - Extend `GuidedIterationArtifact` to reference the hypotheses considered during that loop.

2. **Augment controller state**
   - File: `controller.py`.
   - Maintain a `HypothesisManager` that stores active, rejected, and archived hypotheses across iterations.
   - Ensure every phase prompt can reference explicit hypothesis IDs rather than prose.

Deliverable: new data structures wired into trace artifacts (no behavior change yet).

---

## Phase 1 – Diagnosis Split (Interpretation vs Explanation)

1. **Prompt & response schema**
   - Modify `PROMPT_TEMPLATES` for `INTERPRET` and `DIAGNOSE` to solicit separate `interpretation` (structural element) and `explanation` (reasoning) sections.
   - Update post-processing to parse outputs into structured fields stored on `Hypothesis` objects.

2. **Persistence rules**
   - When preparing prompts for later phases, carry forward only the interpretation field; explanations stay within the current iteration.

Deliverable: deterministic storage of structural interpretations detached from narrative rationale.

---

## Phase 2 – Competing Hypotheses & Generation Workflow

1. **Multi-hypothesis generation**
   - During the first `DIAGNOSE` run (and whenever a stall is detected), require the model to output at least two mutually exclusive hypotheses.
   - Parse and rank them; create `Hypothesis` entries with `expected_effect` descriptions.

2. **Hypothesis selection gate**
   - Before `PROPOSE`, select the highest-ranked non-falsified hypothesis and inject only its data into downstream prompts.
   - Track which hypothesis each patch attempt references.

Deliverable: explicit hypothesis list plus selection controls per iteration.

---

## Phase 3 – Falsification & Validation Mechanics

1. **Add falsification phase**
   - Insert a new phase `GuidedPhase.FALSIFY` (between `DIAGNOSE` and `PROPOSE`).
   - Prompt the model to enumerate observable contradictions for the active hypothesis.
   - Auto-check against prior iteration history (compile results, patch application failures). If any listed contradiction already occurred, mark hypothesis `rejected`.

2. **Patch effect validation**
   - Extend `IterationOutcome` to store previous vs. current error fingerprints (message, location, classification).
   - After compile/test, compute diff; if unchanged, downgrade the hypothesis reliability or reject after threshold.

Deliverable: loop refuses to proceed with hypotheses that fail their own falsification criteria.

---

## Phase 4 – Patch Constraints & Structural Justification

1. **One hypothesis per patch**
   - During `PROPOSE`/`GENERATE_PATCH`, validate that the diff only touches lines inside `hypothesis.affected_region`.
   - If multiple regions are touched, reject the patch and request a narrowed proposal.

2. **Structural change justification**
   - Update `PROPOSE` prompt to ask for a concise “structural delta” statement (grouping/nesting/order/scope/ownership).
   - Persist the justification next to the hypothesis attempt; highlight in critique events if missing.

Deliverable: concrete enforcement that diffs are scoped and explained structurally.

---

## Phase 5 – Hypothesis Lifetime & Stall Detection

1. **Retry counters**
   - Increment `hypothesis.retry_count` whenever a patch attempt tied to it fails (no apply, compile failure, or unchanged error).
   - When the count ≥ 2, auto-archive the hypothesis and trigger generation of a fresh alternative.

2. **No-new-information detector**
   - Compare `(error_message, error_location, diff_span)` with the previous iteration.
   - If identical, emit a stall event, mark the hypothesis as invalid, and branch back to Phase 2 logic to create competing hypotheses.

Deliverable: enforced exploration when progress metrics flatline.

---

## Phase 6 – Trace & Telemetry Updates

1. **Trace artifacts**
   - Extend `GuidedLoopTrace` exports to include hypothesis lifecycle summaries, falsification evidence, and stall signals per iteration.

2. **Observer events**
   - Emit structured `StrategyEvent` payloads whenever a hypothesis is created, falsified, weakened, or archived. This allows downstream tooling to visualize the search dynamics.

Deliverable: transparency hooks for downstream analytics and UI.

---

## Phase 7 – Prompt Library & Checklist Integration

1. **Reusable prompt fragments**
   - Encapsulate hypothesis-specific instructions into helper templates to keep `PROMPT_TEMPLATES` readable.

2. **Inline checklist**
   - Provide a machine-readable checklist (YAML/JSON) that Copilot/LLMs can ingest to remember the lifecycle rules, enabling future automation and tests.

Deliverable: maintainable prompt codebase and lightweight checklists for future agents.

Status: ✅ Implemented via `prompt_fragments.py` (shared sections + JSON schema reminders) and `docs/guided_loop_checklist.json`, which is also embedded directly into each prompt to keep lifecycle rules front and center.

---

## Validation Strategy

- Unit tests: extend `tests/test_guided_loop.py` to simulate hypothesis creation, falsification, and stall detection without invoking real models.
- Integration harness: add scenarios under `scripts/run_guided_loop.py` to ensure logs show hypothesis turnover.
- Regression metric: fail fast if any iteration ends without recording at least one hypothesis ID.

---

## Open Questions

- Should hypotheses persist across cases (global memory) or remain per case execution? (default: per case)
- How should we encode error fingerprints (hash vs. structured fields) for the no-new-information detector?
- Where do we surface user-facing messaging when the system intentionally abandons a hypothesis?

This plan should be revisited after Phase 3 to ensure validation complexity is manageable before layering on telemetry and checklist work.
