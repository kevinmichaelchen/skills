---
name: visualize-code-area-contributors
description: Analyze and visualize who has contributed most to a repository directory or file over time. Use for code-area ownership, prolific contributor rankings, author/email deduplication, contribution recency, monthly activity heatmaps, or Flint WEBP charts derived from local Git history.
---

# Visualize Code Area Contributors

Use a local, reproducible pipeline: **collect Git once → resolve identities and
build offline → render offline**. Treat commit counts and churn as contribution
signals, never as measures of quality, difficulty, or individual performance.

## Workflow

1. Resolve the repository, path, and ref. Default to the checked-out `HEAD`; do
   not use `--all`, because tool-created refs can contain synthetic commits.

2. Cache path-scoped, non-merge history:

   ```bash
   python3 <skill-dir>/scripts/collect.py \
     --repo <repo-root> \
     --path <repo-relative-path> \
     --ref HEAD \
     --out .context/contributors-<path-slug>
   ```

   The collector records raw commit identity, timestamp, subject, paths, and
   numstat. It reuses the cache when the resolved SHA and options match.

   Completion criterion: `raw/selection.json` pins the repository, path, and
   head SHA, and `raw/commits.json` contains at least one commit.

3. Choose an identity alias file when the repository needs one. Use a file
   supplied by the user or maintained alongside the target repository; do not
   invent identities. Add aliases only with evidence from the user, matching
   email addresses, or an unambiguous repository identity. Email aliases take
   precedence over name aliases; this prevents a malformed author name from
   stealing another person's email identity. Exact unmatched names merge
   across emails.

4. Build normalized evidence and Flint specs without querying Git:

   ```bash
   python3 <skill-dir>/scripts/build_artifacts.py \
     --bundle .context/contributors-<path-slug> \
     --aliases <path-to-reviewed-aliases.json> \
     --top 12
   ```

   Use `--exclude-churn-commit <sha>` for a known bootstrap, generated-code, or
   directory-migration commit when its numstat would distort churn. This never
   removes the commit from contribution counts; disclose every exclusion.

   Inspect `derived/identity-review.json` before naming people. Resolve or
   explicitly report relevant `emails_with_multiple_names`,
   `names_with_multiple_emails`, and `unmapped_identities` instead of silently
   guessing.

   Completion criterion: contributor totals reconcile to the attributed raw
   commit count, alias provenance has a SHA-256 digest, and every material
   identity conflict is resolved or disclosed.

5. Read both views:

   - `contributor-scale-recency`: bar length is commit volume; color is the
     author's last contribution date.
   - `contributor-activity-heatmap`: cell intensity and labels are monthly
     commit counts, preserving activity shape through time.

   Use commits as the primary prolificness ranking. Report churn and unique
   paths as context, since large migrations or generated files can dominate
   line counts. Path history starts when that path appears; Git does not follow
   a directory rename automatically, so disclose known predecessor paths.

6. Render the Flint inputs with a runtime stored under `.context/`:

   ```bash
   npm install --prefix .context/flint-runtime --no-audit --no-fund \
     flint-chart@0.5.1 vega@6 vega-lite@6 sharp@0.34

   node <skill-dir>/scripts/render_flint.mjs \
     --runtime .context/flint-runtime \
     --specs .context/contributors-<path-slug>/flint-specs \
     --out .context/contributors-<path-slug>/charts
   ```

   The scripts author registered Flint `Bar Table` and `Heatmap` inputs and
   retain compiled Vega-Lite provenance. If chart structure or encodings need
   to change, use `flint-chart-author` and fix the Flint input rather than
   hand-authoring backend JSON.

   If the user requests machine-readable evidence without images, stop after
   step 5 and report that rendering was intentionally not run.

7. Verify every WEBP with `file`, dimensions, and visual inspection. Confirm
   author ordering, date direction, heatmap labels, and headline values against
   `derived/contributors.json` and `derived/monthly.json`.

## Output contract

Report the repository, path, ref SHA, history scope, alias source, exclusions,
top contributors, and identity caveats. Link the scale/recency WEBP, activity
heatmap, contributor JSON/CSV, monthly JSON/CSV, and identity review. Keep all
generated evidence under `.context/`; do not commit repository history bundles.
