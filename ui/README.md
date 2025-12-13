# llm-patch Reviewer UI

A lightweight React/Vite application for reviewing unified diffs from the llm-patch benchmark corpus. It allows reviewers to inspect each test case, preview the patch effect, and record quality verdicts so low-signal data can be culled quickly.

## Purpose
- **Accelerate manual review** of noisy test cases by presenting before/after/diff views side by side.
- **Capture structured annotations** (source quality, diff quality, final application outcome, reviewer notes) that can be fed back into the benchmark dataset.
- **Provide a launchpad** for future automation (re-running patches, removing bad cases) while remaining easy to set up locally.

## Project layout

```
ui/
├── README.md          # This document
└── reviewer-ui/       # Vite + React workspace for the reviewer app
   ├── src/
   │   ├── components/
   │   ├── server/            # dataset loader + API handler reused by dev/prod servers
   │   ├── store/useReviewStore.ts
   │   └── types.ts
   ├── server/index.ts        # single-process static+API server (sirv + Node http)
   ├── package.json
   └── ...
```

## Getting started

```bash
cd ui/reviewer-ui
npm install            # already run once, repeat after pulling new deps

# Development: Vite dev server + filesystem API (single process)
REVIEWER_DATASET_ROOT=../../benchmarks/generated npm run dev

# Production-like: bundle assets + serve via Node (sirv + same API handler)
REVIEWER_DATASET_ROOT=../../benchmarks/generated npm run serve

# Type-check + production bundle only
npm run build
```

> `REVIEWER_DATASET_ROOT` defaults to `../../benchmarks/generated` (relative to the UI directory). Override it if your benchmark corpus lives elsewhere.

## Core Experience
1. **Test case navigator** (left sidebar) lists all cases with status chips and keyboard navigation.
2. **Dual code viewers** (top split) render the "before" and "after" files with language-aware syntax highlighting.
3. **Diff dock** (bottom pane) pins the unified diff for quick inspection.
4. **Annotation controls** let reviewers mark:
   - Source quality: Good / Poor-Unusable
   - Diff quality: Good / Poor-Unusable
   - Final application: Good / Bad
   - Optional free-form notes
5. **Prev/Next controls** + hotkeys streamline triage across hundreds of cases.

## Architecture Overview
- **Single Node service**
   - During development the dataset API is registered directly on the Vite dev server via a plugin that reuses the same handler as production.
   - For production or local previews `npm run serve` runs `server/index.ts`, which serves the built `dist/` assets with `sirv` and mounts the identical API handler for `/api/*` routes. No extra backend process required.
- **Dataset loader** (`src/server/datasetLoader.ts`)
   - Scans `benchmarks/generated/**/manifest.json` and all result JSON files to enumerate every `(case, model, algorithm, diff)` attempt.
   - Reads the corresponding `before.*`, `diffs/*.diff`, compiler stderr/stdout, and the persisted `after__*.EXT` snapshot recorded during patch evaluation (see `result.after_path`). If the after snapshot is missing it falls back to the before text.
   - Caches summaries in-memory and exposes JSON via `/api/cases` plus `/api/cases/:id`.
- **Frontend**: React + Monaco + Zustand state
   - Monaco renders the before/after panes and the diff viewer; `react-resizable-panels` drives the layout splits.
   - Zustand tracks fetched summaries/details, per-case annotation drafts (source/diff/final verdicts, notes), and the sidebar selection—all persisted client-side for now.
- **Shared schema**: API payload contracts live in `src/types.ts` so both the dataset loader and React components stay in sync.

## Data Model
Each review row represents a single patch attempt (case × model slug × algorithm × diff file):

```text
PatchSummary
├─ id: `${runId}::${caseId}::${modelSlug}::${algorithm}::${diffName}`
├─ caseId / runId / problemId / language
├─ filePath (derived from compile command)
├─ modelSlug / algorithm / diffName
├─ patchApplied (bool)
├─ success (bool)
├─ errorsBefore / errorsAfter / patchDiagnostics

PatchDetail (extends summary)
├─ before: file contents from before.*
├─ diff: unified diff text from `diffs/<model>.diff`
├─ after: persisted patched file from `result.after_path` (falls back to before.* if missing)
├─ errors.stderr / errors.stdout
├─ metadata.manifest / metadata.result (raw JSON payloads)
├─ derived.afterSource (`dataset` vs `missing`)

Each attempt that successfully applies a patch writes its patched source to `after__<modelSlug>__<algorithm>.<ext>` inside the case directory. The relative path is recorded as `after_path` inside the corresponding `results/<model>__<algorithm>.json`, enabling the loader to stream the exact file the compiler saw.
```

Reviewer annotations (source quality, diff quality, final verdict, notes) are stored client-side for now; future work will persist them alongside the dataset.

## Build & enhancement plan
1. **Filesystem API (done)** – share a dataset loader between the Vite dev server and the production Node server so there’s never a second backend process to run.
2. **Reviewer workspace (done)** – sidebar navigation, Monaco-based editors/diff, annotation controls, compiler error panel, optimistic local annotations.
3. **Persistence (next)** – write reviewer annotations + audit logs back to disk (likely JSONL per run directory) and expose POST endpoints for updates.
4. **Filtering & ergonomics** – search/filter by language/model/status, keyboard shortcuts, batching, and a “jump to next unreviewed” action.
5. **Automation hooks** – optional buttons to re-run `llm_patch` on the selected diff, delete low-quality cases, or export CSV/Markdown summaries.
6. **Testing & polish** – add component tests around the dataset loader and a Playwright smoke test that walks a few cases end-to-end.

## Future Enhancements
- Persist annotations + audit logs server-side, then sync them back into the benchmark cleanup pipeline.
- Filtering, keyboard-driven review flow, and batch operations.
- Optional "rerun patch" button that calls the Python `llm_patch` engine to verify the diff directly from the UI.
- CSV/Markdown exports of annotations and quick links to delete or quarantine low-signal cases.

---
This README tracks the UI’s intent, guiding principles, and roadmap. Update it as architecture or scope evolves so new contributors can quickly grok the reviewer tooling.
