---
name: nx-ci-cost-profiler
description: Measure and normalize per-project Nx unit-test costs from one or more CI runs. Use when diagnosing slow Nx CI, comparing package runtimes, separating import/setup/test costs, or preparing measured cost inputs for dependency-graph impact analysis.
---

# Nx CI Cost Profiler

Produce evidence that distinguishes observed project work from workflow wall-clock latency. Never add parallel project durations and call the result CI duration.

## Workflow

1. Identify the exact repository, workflow run, commit, target, and cache state.
2. Collect per-project task timing. When `$visualize-pr-check-times` produced the evidence bundle, its `derived/unit-projects.json` is accepted directly.
3. Normalize one or more captures:

```bash
python3 scripts/aggregate_costs.py \
  --input run-a/derived/unit-projects.json \
  --input run-b/derived/unit-projects.json \
  --out project-costs.json \
  --evidence-label "cache-miss PR runs" \
  --evidence-kind observed-ci \
  --repository example/example-monorepo \
  --commit <full-source-sha> \
  --run-id <github-run-id> \
  --runner ubuntu-latest \
  --cache-state cold
```

4. Inspect sample counts and missing fields. Prefer several comparable cache-miss runs; treat a one-run profile as a measured example, not a stable forecast.
5. Use `p90_total_seconds` for conservative capacity analysis and `p50_total_seconds` for typical-cost analysis.

Read [references/cost-model.md](references/cost-model.md) before interpreting or publishing results.

## Input expectations

Accept a JSON array of records containing `project` and `total_seconds`. Preserve optional Vitest components such as `import_seconds`, `tests_seconds`, `setup_seconds`, `transform_seconds`, and `environment_seconds`.

## Completion criteria

- Every reported project has an explicit sample count.
- The evidence label identifies the source or cohort.
- Repository, source commit, runner, cache state, evidence kind, and available run IDs are machine-readable in `metadata.provenance`.
- Percentiles are described as project task cost, not workflow latency.
- Missing projects and missing component timings remain visible.
- Any claim based on one run says so.
