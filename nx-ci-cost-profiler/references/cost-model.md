# Cost model

## Evidence levels

1. **Observed task cost**: elapsed time printed for a project target in a named CI run.
2. **Repeated task cost**: a percentile over comparable runs, ideally cache misses on the same runner class.
3. **Static proxy**: source bytes, file count, import count, or test count. Use only when timing is unavailable and label it as a proxy.

Do not silently mix these levels.

## Timing semantics

- `total_seconds` is project-level wall time.
- Vitest component timings may not sum to project wall time. Framework startup, scheduling, reporting, and other unclassified work can account for the remainder.
- Summing project wall times estimates **work exposed**. Parallel execution means it does not estimate workflow duration.
- Workflow latency requires scheduler-aware measurement or simulation with concurrency, ordering, cache, and resource constraints.

## Sampling

- Prefer cache-miss runs when estimating cost avoided by preventing a task from being selected.
- Keep cache-hit and cache-miss cohorts separate.
- Report `samples`; p90 from one sample is only that observation.
- Compare like runner hardware, Node versions, sharding, and test configuration.

## Output schema

The normalizer emits:

- `metadata`: schema version, evidence class and label, source files, input-record count, and immutable provenance (`repository`, `commit`, run IDs, runner, and cache state).
- `projects[]`: project name, samples, and p50/p90/max values for total and available components.
- `missing`: records rejected for missing project names or valid total duration.
