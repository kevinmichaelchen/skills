# Metrics and interpretation

Let `R(v)` be project `v` plus every project that transitively depends on it. Let `T` be projects with the selected Nx target, and `c(t)` a measured task cost.

## Node measures

- **Count blast radius**: `B(v) = |R(v) ∩ T|`.
- **Weighted blast radius**: `W(v) = Σ c(t)` for `t ∈ R(v) ∩ T`.
- `W(v)` is exposed task work. It is not CI makespan because tasks can overlap.

High `B` with low `W` means broad but relatively cheap coupling. Low `B` with high `W` means a narrow dependency reaches expensive tests. High values on both dimensions are the strongest architectural targets.

## Edge measures

For edge `e`, remove only `e`, recompute all reverse closures, and compare with the original graph.

The analyzer treats multiple Nx edge records between the same source and target as one project-pair edge. Removing that pair removes every parallel relationship between those projects; raw and unique counts are both reported.

- **Aggregate tests avoided**: sum of reduced selected targets over one hypothetical change to every project.
- **Aggregate work avoided**: sum of reduced task costs under the same uniform-change model.
- **Changed nodes helped**: number of starting projects whose closure becomes smaller.
- **Maximum work avoided**: largest benefit for any single starting project.

These are counterfactual topology measures, not delivery forecasts. Duplicate paths can make a seemingly important edge have zero marginal effect.

The analyzer classifies the join as `snapshot-aligned-counterfactual`, `mixed-snapshot-counterfactual`, or `unverified-counterfactual`. It fails closed on mismatched or missing commit provenance unless the corresponding explicit override is passed.

## Moving from diagnosis to ROI

Replace the uniform-change model with historical change frequency `f(v)` and cache-miss probability `m(v)`:

`Expected avoided work(e) = Σ f(v) × m(v) × [W(v) - W_without_e(v)]`

For latency, simulate or replay the CI scheduler with actual concurrency, task ordering, cache behavior, and runner capacity. Do not convert work minutes directly into wall-clock savings.
