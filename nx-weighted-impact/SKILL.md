---
name: nx-weighted-impact
description: Join an Nx dependency graph with measured per-project task costs to quantify weighted reverse-dependency blast radius and counterfactual edge impact, then generate Flint chart specifications. Use when asking which Nx dependencies are most poisonous, where architecture makes affected CI expensive, or which dependency cuts have the highest potential payoff.
---

# Nx Weighted Impact

Measure both breadth and cost. A dependency is consequential when changes flow through it into many downstream test targets, especially expensive ones.

## Workflow

1. Capture a deterministic Nx project graph:

```bash
pnpm nx graph --file=.context/nx-impact/nx-graph.json --open=false --watch=false
git rev-parse HEAD  # record this immutable SHA
```

2. Build measured project costs with `$nx-ci-cost-profiler`. Use static proxies only when runtime evidence is unavailable, and label them.
3. Analyze nodes and edges:

```bash
python3 scripts/analyze_weighted_impact.py \
  --graph .context/nx-impact/nx-graph.json \
  --costs .context/nx-impact/project-costs.json \
  --out .context/nx-impact/results \
  --cost-field p90_total_seconds \
  --graph-commit <full-graph-source-sha>
```

The analyzer fails when the graph commit and timing commit differ. Prefer rebuilding one input. Use `--allow-provenance-mismatch` only when a deliberately mixed-snapshot model is useful; it will be labeled accordingly. Legacy costs without commit provenance require the separate `--allow-unverified-provenance` override.

4. Render the generated `flint-specs/*.json` with `$flint-chart-author` or its rendering helper.
5. Open every WEBP and verify legibility, ordering, units, clipping, and the claim in its title.
6. Report node exposure separately from edge-removal opportunity. Edge impact is marginal: an edge can be broad yet removable with no effect because another path preserves the same reachability.
7. Use `representative-paths.json` for a selective D2 explanation: show only a few high-cost paths, put measured cost on terminal test nodes, and say that the paths are shortest explanations rather than the full graph.

Read [references/metrics.md](references/metrics.md) before interpreting the rankings.

## Outputs

- `summary.json`: coverage and headline statistics.
- `nodes.csv` and `nodes.json`: reverse closure, affected unit targets, and exposed measured work for every project.
- `edges.csv` and `edges.json`: counterfactual reduction after removing each edge.
- `representative-paths.json`: compact high-cost causal paths suitable for a D2 explanatory diagram.
- `flint-specs/weighted-node-impact.json`: top nodes by observed downstream task-minutes.
- `flint-specs/marginal-edge-impact.json`: top edges by aggregate task-minutes avoided under a uniform one-change-per-project model.
- `flint-specs/heavyweight-cost-composition.json`: how the three slowest measured targets amplify the broadest reverse closures.

## Completion criteria

- Graph node, raw edge, and unique project-pair edge counts are recorded. Static and dynamic records for the same project pair are treated as one reachability edge.
- Cost coverage and missing-cost projects are explicit.
- Additive task-work minutes are never called CI latency.
- Edge rankings come from reachability recomputation, not degree alone.
- The uniform-change assumption is disclosed; historical change frequency is added before forecasting ROI.
- Every delivered chart is rendered and visually inspected.
- Every publication caption begins with its evidence class (`Observed`, `Historical replay`, `Configuration counterfactual`, or `Graph-and-cost counterfactual`), identifies the commit/run cohort, and distinguishes task work from CI latency.
