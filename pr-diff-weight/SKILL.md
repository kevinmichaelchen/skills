---
name: pr-diff-weight
description: Measure the review weight of a GitHub pull request diff. Use when a user asks to grab a PR, size a PR, estimate diff weight, compare a PR against main, count changed files/lines/tokens, run tokei or tokenu on a PR diff, or produce a concise review-weight summary before reviewing code.
---

# PR Diff Weight

## Overview

Measure a PR without switching the user's current branch. Fetch the PR into a remote ref, diff it against the base branch, compute line churn, token counts, touched-file size, prose/comment weight, test versus production split, area hotspots, and a short review-weight read.

Prefer `scripts/measure-pr-diff.py` for repeatable measurements. Use manual commands only when the script cannot run in the local repository.

## Quick Start

From the repository root:

```bash
python3 .context/skills/pr-diff-weight/scripts/measure-pr-diff.py --pr 729
```

Useful options:

```bash
python3 .context/skills/pr-diff-weight/scripts/measure-pr-diff.py --pr 729 --base origin/main
python3 .context/skills/pr-diff-weight/scripts/measure-pr-diff.py --head origin/some-branch --base origin/main
python3 .context/skills/pr-diff-weight/scripts/measure-pr-diff.py --pr 729 --out-dir .context/pr729-analysis
```

The script writes scratch artifacts under `.context/pr-diff-weight/` by default and prints the summary to stdout. It materializes only changed files for touched-file measurements; it does not clone, rename or switch the current branch, or initialize submodules.

## Workflow

1. Confirm the repo context with `git status --short --branch` and `git remote -v`.
2. Run the script with `--pr <number>` when the user gives a GitHub PR number. Use `--head <ref>` only when the PR ref already exists or the user gives a branch/ref.
3. If the user asked to "grab" a PR, include PR metadata from `gh pr view <number>` when `gh` is available.
4. Report the essentials:
   - PR title/state/base/head when available
   - files changed, insertions, deletions, total churn
   - full patch lines/bytes/tokens
   - added-lines-only tokens
   - touched-file `tokei` total and changed-file token total
   - PR description lines/words/tokens when GitHub metadata is available
   - added comment-line count and token count
   - test versus production split
   - largest areas and top churn files
   - a short judgment of review weight and where the reviewer should focus
5. Mention skipped measurements if `tokei`, `bun`, `tokenu`, or `gh` are unavailable.

## Checkout And Submodule Policy

Avoid full checkouts for measurement-only work. The script fetches refs into the existing repository, writes patch artifacts, and materializes changed files with `git show <head>:<path>` into `.context/pr-diff-weight/<label>-files/`.

This intentionally avoids:

- cloning the repository
- switching the user's working branch
- running `git submodule update`
- recursively cloning nested submodules
- materializing unchanged files

If a changed path is a submodule gitlink, skip touched-file token and `tokei` analysis for that path and mention it in notes. The diff still captures the submodule pointer change.

Do not add `--recurse-submodules` to fetch, checkout, clone, or worktree commands for this skill unless the user explicitly asks to include submodule contents in the weight calculation.

## Prose Weight

Include prose metrics in the same report, not a separate skill, when the user asks about PR weight, PR verbosity, overly descriptive PR descriptions, or code comment pollution. These metrics are part of review burden.

Measure:

- PR body lines, words, and tokens from `gh pr view --json body`
- added comment lines from the diff
- added comment-line tokens with `tokenu`
- touched-file total comment lines from `tokei` when available

Interpret prose weight conservatively. High PR-body tokens are not automatically bad, but flag when the body is long relative to the code diff or repeats information already obvious from changed files/tests. For code comments, flag comments that explain provenance, historical process, or how a decision was made when that context does not need to live permanently beside the code. Prefer comments that explain durable invariants, surprising constraints, public contract behavior, or non-obvious safety requirements.

## Interpretation

Use these rough labels, but let architectural breadth override raw size:

- Small: under 300 changed lines or under 8k patch tokens, narrow surface.
- Medium-small: 300-900 changed lines or 8k-20k patch tokens, especially if mostly tests.
- Medium: 900-2,000 changed lines or 20k-45k patch tokens, multiple areas or contracts.
- Large: over 2,000 changed lines, over 45k patch tokens, generated files, migrations, broad domain changes, or multiple packages.

Call out whether the churn is test-heavy. A PR with high test churn but modest production churn is usually lighter than its raw insertion count suggests, unless it changes schemas, persistence behavior, auth, migrations, or public API contracts.

## Manual Fallback

When the script cannot run, use this pattern:

```bash
git fetch origin +main:refs/remotes/origin/main +pull/PR_NUMBER/head:refs/remotes/origin/pr/PR_NUMBER
mkdir -p .context/prPR_NUMBER-analysis
git diff --find-renames origin/main...origin/pr/PR_NUMBER > .context/prPR_NUMBER-analysis/prPR_NUMBER.diff
git diff --numstat origin/main...origin/pr/PR_NUMBER > .context/prPR_NUMBER-analysis/prPR_NUMBER-numstat.tsv
git diff --name-only origin/main...origin/pr/PR_NUMBER > .context/prPR_NUMBER-analysis/prPR_NUMBER-files.txt
awk '/^\+/ && !/^\+\+\+/ { sub(/^\+/, ""); print }' .context/prPR_NUMBER-analysis/prPR_NUMBER.diff > .context/prPR_NUMBER-analysis/prPR_NUMBER-added-lines.txt
wc -l -c .context/prPR_NUMBER-analysis/prPR_NUMBER.diff .context/prPR_NUMBER-analysis/prPR_NUMBER-added-lines.txt
bunx tokenu -s --json .context/prPR_NUMBER-analysis/prPR_NUMBER.diff .context/prPR_NUMBER-analysis/prPR_NUMBER-added-lines.txt
mkdir -p .context/prPR_NUMBER-files
while IFS= read -r file; do mkdir -p ".context/prPR_NUMBER-files/$(dirname "$file")"; git show "origin/pr/PR_NUMBER:$file" > ".context/prPR_NUMBER-files/$file" 2>/dev/null || true; done < .context/prPR_NUMBER-analysis/prPR_NUMBER-files.txt
cd .context/prPR_NUMBER-files && xargs tokei --num-format commas < ../prPR_NUMBER-analysis/prPR_NUMBER-files.txt
```

Keep generated artifacts in `.context/` so they remain gitignored collaboration scratch space.
