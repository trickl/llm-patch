# Hypothesis Lifecycle Design Log

_Last updated: 2025-12-14_

## Context

Guided Loop currently optimizes for internal narrative consistency, which leads to premature convergence on incorrect diagnoses. Once the system forms a belief about the failure, every subsequent phase reinforces it—even when patches fail to apply, leave the failing construct untouched, or when compiler/test feedback remains unchanged. The core issue is not language expertise but a structural search-space collapse caused by unchallenged hypotheses.

## Design Goal

Enforce hypothesis lifecycle discipline that prioritizes falsifiability over narrative elaboration. The upgraded loop must:

- Maintain explicit, isolatable hypotheses
- Demand empirical falsification attempts before patching
- Track observable progress across iterations
- Prevent multi-issue patches and diagnosis drift
- Detect and exit stalled loops proactively

## Structural Improvements

1. **Explicit Hypothesis Objects**
   - Represent each diagnosis as `Hypothesis { id, claim, affected_region, expected_effect }`.
   - Store / compare / retire hypotheses explicitly rather than embedding them in prose strings.

2. **Separate Error Interpretation vs. Explanation**
   - Interpretation answers _what_ structural element failed.
   - Explanation captures _why_ the model believes it failed.
   - Persist only the interpretation between iterations to avoid narrative ossification.

3. **Mandatory Falsification Phase**
   - Before proposing a patch, articulate at least one observable outcome that would contradict the hypothesis.
   - Compare with prior iterations; if contradictions already exist, reject before coding.

4. **One Hypothesis per Patch**
   - Each diff must map to exactly one hypothesis and must touch only the region that hypothesis references.
   - No bundled “shotgun” fixes.

5. **Patch Effect Validation**
   - After applying a diff, compare error messages and locations with the previous iteration.
   - Detect no-op patches and mark their hypotheses as weakened or invalid.

6. **Structural Change Justification**
   - Every patch proposal must describe the structural relationship being altered (grouping, nesting, ordering, scope, ownership).
   - Reject proposals that only cite lexical adjustments (e.g., “adds punctuation”).

7. **Hypothesis Lifetime Limits**
   - Track retry counts; after two failed validations, automatically retire the hypothesis and require a new one.

8. **Competing Hypotheses Early**
   - During initial diagnosis, generate at least two mutually exclusive structural hypotheses and rank their plausibility.
   - Encourages breadth-first exploration before refinement.

9. **No-New-Information Detector**
   - Declare a stall when error message, location, and patch scope remain unchanged.
   - Force hypothesis replacement instead of refining the existing one.

## Next Steps

The implementation plan will map each improvement to concrete code changes within the guided loop controller, phase artifacts, and supporting utilities. This log remains the authoritative reference for the behavioral intent as we iterate.
