---
name: nx-affected-history
description: Replay and explain historical Nx affected selections from arbitrary Git base/head pairs using cached detached worktrees. Use when investigating why unrelated projects ran in a PR, whether rebasing or force-pushing widened CI, how lockfiles or workspace-wide target inputs changed the affected set, or when comparing affected behavior across branch history without pushing or switching the active checkout.
---

# Nx Affected History

Replay first; explain second. Use Nx from the requested historical tree rather than approximating affected behavior from the current graph.

## Replay a comparison

```bash
python3 scripts/analyze.py \
  --repo /path/to/nx-workspace \
  --base <base-sha> \
  --head <head-sha> \
  --target test:unit \
  --cache-dir /path/to/workspace/.context/nx-affected-history/cache \
  --out /path/to/workspace/.context/nx-affected-history/result.json
```

The script creates a temporary detached worktree, shares the caller's `node_modules`, runs Nx with its daemon disabled, and removes the worktree in a `finally` block. It creates no branch and performs no remote operation.

## Interpret the evidence

1. Confirm `runtime_version_match`. Do not present a replay as exact when the installed Nx version differs from the historical manifest.
2. Compare `full` with the trigger-isolation scenarios:
   - `without_lockfiles`
   - `lockfiles_only`
   - `typescript_only`
   - `graphql_only`
   - `manifests_only`
3. Inspect `implicit_workspace_matches`. A workspace-root glob on *any* target can mark its owning project touched before dependency traversal, even when analyzing another target.
4. Inspect each scenario's `selection_explanations`. Each selected project has a primary seed reason and shortest reverse-dependency path; use alternatives when multiple triggers reach it.
5. Inspect `workspace_input_counterfactuals`. These are measured, reversible configuration experiments against the lockfile-free file set—not observed CI history. A `not-runnable` result usually means the input is inherited from `nx.json` rather than project-local configuration.
6. Treat a lockfile-only all-project result as lockfile policy, not architectural coupling.
7. Compare several base/head results before blaming rebase. If the semantic diff and isolated triggers remain stable, force-pushing merely caused another run.

For several completed replays, generate comparative Flint inputs:

```bash
python3 scripts/build_flint_specs.py \
  --result "PR #1104=result-1104.json" \
  --result "PR #1107=result-1107.json" \
  --result "PR #1108=result-1108.json" \
  --out flint-specs
```

Render and inspect the specifications with `$flint-chart-author`.

Read [references/evidence-model.md](references/evidence-model.md) before making causal claims.

## Completion criteria

- Record the exact resolved base, head, merge base, target, Nx version, and changed files.
- Preserve the cached JSON result; immutable comparisons should not call Nx again.
- Separate lockfile, global-input, and dependency-propagation effects.
- Cite the recorded seed and dependency path for claims about why a particular project was selected.
- Leave the caller's branch and worktree list unchanged.
- Label historical replays that reuse current dependencies instead of an exact historical install.
