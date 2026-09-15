# Evidence model

## Causal layers

Nx builds an affected set in stages:

1. Git identifies changed files between the merge base and head.
2. Project ownership marks projects containing those files.
3. Implicit workspace inputs can mark additional projects. Nx scans workspace-root inputs from every configured target, not only the target being executed.
4. JavaScript dependency-update logic handles root manifests and lockfiles. Without `projectsAffectedByDependencyUpdates: "auto"`, a changed lockfile marks every project touched.
5. Nx traverses reverse project dependencies from every touched project.
6. `--with-target` retains projects that expose the requested target.

Name the layer that produced the expansion. “The dependency graph did it” is incomplete when a lockfile or broad workspace input created the initial touched projects.

## Rebase claims

A rebase changes commit identities and triggers a new PR workflow after force-push. It does not inherently widen the PR diff when CI compares the new merge base to the new head.

Corroborate a rebase effect only when at least one of these changes:

- the semantic changed-file set;
- lockfile or root-configuration content;
- historical Nx configuration or project graph;
- the base/head selection used by CI;
- the resulting isolated affected scenarios.

Repeated slow runs after force-push are not evidence that main-branch changes leaked into `nx affected`.

## Exactness and caching

The script checks the historical manifest's Nx version against the shared installed version. Matching versions give a fast, high-fidelity replay for nearby history. For long-range analysis with a mismatch, create an isolated frozen dependency install at that commit and rerun; never silently call the mixed-version result exact.

Cache entries are keyed by resolved base, head, target, installed Nx version, and analyzer schema. Git commits are immutable, so a matching cache entry requires no expiration.

## Explanation and intervention evidence

`selection_explanations` are deterministic graph explanations: a seed established by ownership, a matching workspace input, or lockfile policy, followed by a shortest reverse-dependency path to the selected target project. A shortest path is a compact explanation, not proof that it is the only path.

`workspace_input_counterfactuals` temporarily remove only matched project-local workspace-root input declarations, rerun Nx with the same lockfile-free file list, and restore the files exactly. Label the resulting delta `configuration-counterfactual`; it estimates what selection would have been under different configuration and is not an observed historical CI run.
