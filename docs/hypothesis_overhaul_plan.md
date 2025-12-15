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

## Phase 1 – Diagnosis Summary & Rationale

1. **Prompt & response schema**
   - Simplify `PROMPT_TEMPLATES` so the loop opens with `DIAGNOSE` (the Interpret phase was removed entirely).
   - Require Diagnose responses to emit both a `diagnosis` field (structural summary) and a `rationale` field (evidence).
   - Update post-processing to parse those fields into `Hypothesis` objects so downstream prompts can reference them directly.
   - Enforce the rule in prompts, schema validation, and telemetry so Diagnose stays structural—ownership, scope, ordering, and dependency vocabulary only.

2. **Persistence rules**
   - When preparing prompts for later phases, carry forward the diagnosis summary but keep the rationale scoped to the current iteration to reduce narrative ossification.

Deliverable: deterministic storage of structural diagnoses detached from descriptive rationale.

---

## Phase 2 – Competing Hypotheses & Generation Workflow

1. **Multi-hypothesis generation**
   - During the first `DIAGNOSE` run (and whenever a stall is detected), require the model to output at least two mutually exclusive hypotheses.
   - Parse and rank them; create `Hypothesis` entries with `expected_effect` descriptions.

2. **Hypothesis selection gate**
   - Before `PROPOSE`, select the highest-ranked active hypothesis and inject only its data into downstream prompts.
   - Track which hypothesis each patch attempt references.

3. **Diagnose commitment contract**
   - Update the `DIAGNOSE` prompt/schema so it always emits both a grouping/precedence hypothesis and a missing-token hypothesis before any have been accepted.
   - Require the model to select exactly one of those hypotheses (with rationale and an expanded binding region) so that `FALSIFY` never runs without a committed framing.
   - Persist the selected hypothesis ID + rationale into the iteration telemetry so downstream enforcement (scope validation, retries) can cite the same commitment.

4. **Feasibility gate**
   - After enumerating hypotheses inside `DIAGNOSE`, require an explicit feasibility verdict for each one answering, “Can this structural change be applied entirely within the affected_region?”
   - Record the verdict alongside the hypothesis so telemetry can prove whether a later patch overran the region.
   - Hypotheses that require edits outside their declared region are immediately marked non-selectable; only region-contained options (e.g., grouping) can advance while spillover candidates (e.g., token_absence) are disqualified automatically.
   - Selection logic in the controller MUST refuse to activate any hypothesis that fails this check; enforcement cannot rely on prompt compliance alone. This ensures Diagnose automatically lands on the grouping hypothesis in the motivating case.

Deliverable: explicit hypothesis list plus selection controls per iteration.

---

## Phase 3 – Validation Mechanics (Deferred Falsification)

1. **Future falsification hook**
   - Document the contradiction-checking heuristics we eventually want, but keep the dedicated `GuidedPhase.FALSIFY` removed until the telemetry is ready.
   - In the interim, rely on deterministic signals (patch apply failures, unchanged error fingerprints, compile diagnostics) to reject or archive hypotheses.

2. **Patch effect validation**
   - Extend `IterationOutcome` to store previous vs. current error fingerprints (message, location, classification).
   - After compile/test, compute diff; if unchanged, downgrade the hypothesis reliability or reject after threshold.

Deliverable: loop refuses to proceed with hypotheses that fail deterministic validation, with a placeholder for future falsification prompts.

---

## Phase 4 – Patch Constraints & Structural Justification

1. **Structured affected regions**
   - Replace string-based regions with a fixed enum: `lambda_body`, `conditional_expression`, `enclosing_call_expression`, or `statement_boundary`.
   - Store both the region kind and referenced node span so downstream validators can reason about AST structure, not raw text snippets.
   - Enforce invariants: `grouping_precedence` hypotheses must bind at least a `conditional_expression`, and `token_absence` hypotheses must bind a `statement_boundary`, preventing impossible bindings.

2. **One hypothesis per patch**
   - During `PROPOSE`/`GENERATE_PATCH`, validate that the diff only touches lines inside `hypothesis.affected_region`.
   - If multiple regions are touched, reject the patch and request a narrowed proposal.

3. **Structural change justification**
    - Replace the free-text “structural delta” with a structured payload:
       ```json
       {
         "structural_change": {
           "type": "grouping",
           "operation": "introduce_parentheses"
         }
       }
       ```
    - Define the enum so `type ∈ {grouping, scope, ordering, ownership}` and each type has a tightly scoped `operation` list (e.g., grouping → `{introduce_parentheses, remove_parentheses, rebind_operator}`).
    - Enforce the invariant that grouping changes MUST NOT introduce or remove statement terminators; schema validation should reject any attempt to smuggle token edits under a grouping claim.
    - Persist the structured justification next to the hypothesis attempt; highlight in critique events if missing.

Deliverable: concrete enforcement that diffs are scoped and explained structurally.

---

## Phase 5 – Hypothesis Lifetime & Stall Detection

1. **Retry counters**
   - Increment `hypothesis.retry_count` whenever a patch attempt tied to it fails (no apply, compile failure, or unchanged error).
   - When the count ≥ 2, auto-archive the hypothesis and trigger generation of a fresh alternative.

2. **No-new-information detector**
   - Compare `(error_message, error_location, diff_span)` with the previous iteration.
   - If identical, emit a stall event, mark the hypothesis as invalid, and branch back to Phase 2 logic to create competing hypotheses.

3. **Feasibility auto flip**
   - If a hypothesis clears `DIAGNOSE` but `GENERATE_PATCH` fails solely because the patch would exceed the allowed scope, archive the hypothesis immediately as “structurally infeasible.”
   - Automatically select the next highest-ranked feasible hypothesis (or trigger new generation) so the loop cannot oscillate on a repeatedly disqualified idea.
   - Record the flip in telemetry to explain why scope violations end a hypothesis’ lifetime.

4. **Scope violation kill switch**
   - Treat every scope violation reported by `GENERATE_PATCH` as definitive evidence that the active hypothesis cannot be fulfilled; immediately archive it and force `DIAGNOSE` to select a different, feasible hypothesis within the same loop.
   - Reset retries and log the eviction reason so future analytics can trace how often hypotheses die due to region overshoots.
   - Re-enter the Diagnose phase with the remaining hypothesis list (or trigger regeneration if empty) so the loop never stalls on a dead hypothesis.
   - This prevents oscillation when the model keeps proposing out-of-bounds edits.

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

Status: ✅ Implemented via `prompt_fragments.py` (shared sections + JSON schema reminders) and `docs/guided_loop_checklist.json`; as of 2025-12-15 the checklist remains documented but is no longer embedded verbatim in every prompt to avoid unnecessary token overhead.

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
