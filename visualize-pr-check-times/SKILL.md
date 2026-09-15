---
name: visualize-pr-check-times
description: Profile and visualize GitHub pull-request check latency. Use when asked how long PR checks take, which GitHub Actions job gates merging, why unit tests are slow, or to cache GitHub evidence once and repeatedly rebuild Flint-authored WEBP charts offline.
---

# Visualize PR Check Times

Use a three-stage pipeline: **fetch once → build offline → render offline**.
The evidence bundle contains raw GitHub JSON and logs, normalized JSON/CSV,
Flint `ChartAssemblyInput` specs, compiled Vega-Lite, and verified WEBP charts.

## Workflow

1. Resolve the repository and PR number. Check `gh auth status`; stop with the
   observed error if the repository is inaccessible.

2. Fetch the latest completed workflow run for the PR's current head SHA:

   ```bash
   python3 <skill-dir>/scripts/collect.py \
     --repo <owner/repo> \
     --pr <number> \
     --workflow PR \
     --out .context/pr-<number>-check-times \
     --include-logs
   ```

   The collector is the **only** stage that calls GitHub. It refreshes mutable
   PR/run-list metadata, binds the selected run to `headRefOid`, and reuses
   immutable run JSON and logs unless `--refresh` is passed. Run it again only
   when the PR head or desired run changes.

   Completion criterion: `raw/selection.json`, `pr.json`, `branch-runs.json`,
   the selected `run-<id>.json`, and requested job logs exist; the three cached
   head SHAs agree.

3. Rebuild normalized data and Flint specs from the cache:

   ```bash
   python3 <skill-dir>/scripts/build_artifacts.py \
     --bundle .context/pr-<number>-check-times
   ```

   This stage imports no GitHub client and makes no network request. Re-run it
   freely while changing derivation, chart selection, headlines, encodings, or
   sizing. It also parses the cached Unit tests log into exact per-project
   Vitest wall time and component timers when that log is present. It also
   authors a project-level execution timeline and an import-versus-test scatter
   plot from that same cached log; neither chart triggers another GitHub fetch.

   Completion criterion: `derived/summary.json`, `jobs.{json,csv}`,
   `steps.{json,csv}`, `unit-projects.{json,csv}`, and `flint-specs/*.json`
   exist; `summary.json.head_sha` matches `raw/selection.json`; every number is
   traceable to cached timestamps or a Vitest summary.

4. Read the data before charting. Report at least:

   - workflow wall-clock time (`startedAt` to `updatedAt`);
   - the longest job and its share of workflow wall time;
   - the longest step and its share of that job;
   - the next two longest jobs;
   - setup-heavy exceptions where setup/services take more time than the main
     work step.

   Jobs fan out, so never add parallel job durations and call the sum PR latency.
   Use the timeline to identify the gate. Step durations are sequential within
   one job; compare them only to their containing job.

   For Unit tests, prefer Vitest's per-project `Duration` over Nx completion-gap
   estimates. Report the longest project's wall time, start offset, file/test
   count, import time, and test-execution time. Nx projects overlap, and Vitest
   component timers can overlap too; do not sum either as suite wall time.

5. Render the generated Flint specs. Install the pinned runtime into `.context/`
   so dependency files and native modules never enter the skill or target repo:

   ```bash
   npm install --prefix .context/flint-runtime --no-audit --no-fund \
     flint-chart@0.5.1 vega@6 vega-lite@6 sharp@0.34

   node <skill-dir>/scripts/render_flint.mjs \
     --runtime .context/flint-runtime \
     --specs .context/pr-<number>-check-times/flint-specs \
     --out .context/pr-<number>-check-times/charts
   ```

   The specs use registered Flint `Bar Table`, `Grouped Bar Chart`, `Gantt
   Chart`, and `Scatter Plot` types with semantic types. The renderer compiles
   them with `assembleVegaLite`, retains the compiled Vega-Lite JSON, and only
   applies narrow `%H:%M` and UTC-scale axis tweaks to timelines before
   rasterization.

   If changing chart structure, field mappings, or semantic types, use the
   `flint-chart-author` skill and fix the `ChartAssemblyInput`; do not hand-author
   Vega-Lite as a substitute for Flint.

6. Verify every deliverable. Check each image with `file`, inspect its dimensions,
   and view it. Re-render if labels are clipped beyond recognition, ordering is
   misleading, timestamps are unreadable, or the headline does not state the
   finding.

   Completion criterion: every `.webp` is non-empty, decodes as WEBP, has the
   expected headline and readable marks, and agrees with `summary.json`.

## Output contract

Keep the complete evidence bundle under `.context/`; do not commit PR logs or
runtime dependencies. In the final response, link the WEBPs and machine-readable
summary, identify the repository, PR, head SHA, run ID and run URL, and
distinguish observations from recommendations.

Do not claim that a proposed optimization will save a measured amount without a
before/after run. Recommend critical-path work first; faster non-gating jobs do
not shorten the merge wait.
