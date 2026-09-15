---
name: github-pr-creator
description: Create or draft GitHub pull requests with Conventional Commit titles, focused visual summaries, and evidence-backed validation. Use when the user asks to open, create, draft, publish, update, or write a PR.
---

# GitHub PR Creator

Draft or create GitHub pull requests with a strict title gate and a
two-audience body: visual and concise for humans, exhaustive for reviewing
agents.

## Intent And Authorization

- "Write" or "draft" a PR means return proposed title and body text unless the
  user explicitly asks to create a draft PR on GitHub.
- "Create," "open," or "publish" a PR authorizes GitHub PR creation.
- Do not push commits or branches unless the user requests it or publishing the
  authorized PR requires it. State when a push is required before doing it.
- Preserve the requested draft or ready-for-review state when creating or
  updating a PR.

## Hard Gates

All fenced blocks in this file are format templates and reference material,
not executable code.

Every PR title must be a Conventional Commit title:

```text
<type>: <summary>
```

Examples:

- `feat(cli): add profile selection`
- `fix: handle expired session refresh`
- `docs: clarify PR title requirements`

Rules:

- Use a Conventional Commit type: `feat`, `fix`, `docs`, `refactor`, `test`,
  `chore`, `ci`, `build`, `perf`, `style`, or `revert`.
- The summary should be concise, imperative, lowercase unless a proper noun
  requires capitalization, and have no trailing period.

## Workflow

1. Read repository context:
   - Read applicable `AGENTS.md`, workspace instructions, and PR templates.
     Treat their title, body, base-branch, and publishing rules as additional
     constraints.
2. Resolve the PR coordinates and idempotency state:
   - Identify the repository, head repository, local head branch, upstream,
     remote head branch, and whether the branch is in a fork.
   - Resolve the target branch from workspace instructions, an existing PR, or
     the repository default, in that order.
   - Check whether the current remote head branch already has an open PR. If it
     does, update or report that PR as the request requires; do not create a
     duplicate.
   - Confirm the head repository, head branch, base branch, and requested draft
     state before any mutation.
3. Inspect committed and uncommitted state separately:
   - Read `git status --short --branch`, `git log <base>..HEAD`,
     `git diff --stat <base>...HEAD`, and `git diff <base>...HEAD`.
   - Inspect staged and unstaged diffs separately. State whether uncommitted
     changes will be excluded from the PR.
   - Identify the primary user-visible or maintainer-visible goal.
4. Apply any issue or ticket requirements from repository instructions. Never
   invent a ticket, infer that one exists from a branch name alone, or add an
   issue-closing link unless the closing behavior is known and intended.
5. Choose the Conventional Commit type from the actual change:
   - `feat` for new user-visible behavior.
   - `fix` for bug fixes.
   - `refactor` for behavior-preserving restructuring.
   - `docs`, `test`, `ci`, `build`, `perf`, `style`, `chore`, or `revert` when
     those are the main change.
6. Draft the body using the Two-Audience Body Contract below:
   - Every body has exactly two H2 headings: `## For humans` and
     `## For machines`, in that order. Do not use any other H2 headings.
   - Keep the complete `For humans` section under 300 words. It must stand on
     its own and surface the goal, impact, material risk or breaking behavior,
     and validation state.
   - Put `## For machines` inside a closed `<details>` element. Make it an
     exhaustive review dossier rather than a restatement of the human summary.
     It may contain H3 headings and nested `<details>` elements.
   - Give every `For humans` section one change-shaped visual, following the
     [show-me skill](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md):
     choose the smallest diff, pseudocode, tree, or Mermaid diagram that makes
     the change easier to understand. Place it beside the text it supports.
   - Keep visuals selective and factual. Show only the files, calls, states,
     components, and boundaries needed to review this change; never add a
     decorative diagram merely to satisfy the format.
   - Honor explicit presentation requests inside this envelope; they never
     remove either audience section or relax the human word limit.
   - Use at most two or three GitHub alerts per body.
   - Use reference-style links when official API, class, or field documentation
     materially helps review.
   - Separate observed facts, implementation decisions, and genuine open
     questions. Do not present unresolved behavior as settled intent.
   - Use `Closes` or `Fixes` only when the integration's closing behavior is
     known and intended. Otherwise use a plain issue or ticket reference.
7. Include evidence-backed validation:
   - List only checks observed in command output or explicitly supplied by the
     user. Do not infer validation from changed test files.
   - Distinguish passed, failed, skipped, and not-run checks. If a relevant
     check was not run, say so briefly and why.
8. Re-check before mutation:
   - Validate the title against the hard gates and confirm branch coordinates,
     repository-specific requirements, draft state, existing-PR handling, and
     authorization to create, update, or push. Fix violations or ask for
     missing context.
9. Create or update the PR as authorized.
10. Fetch the PR after mutation and verify its URL and number, title, base and
    head branches, draft state, and rendered body. Correct any mismatch that
    remains within the user's authorization.

## Two-Audience Body Contract

The body begins with `## For humans`; nothing precedes it. Put relevant issue
or ticket links in this section. Put `AI-assisted.` here when the PR was
substantially agent-authored. All of this counts toward the strict 300-word
limit.

The human section should be plainspoken and scannable. It states what changed
and why, user or operator impact, material risk or breaking behavior, rollout
or migration requirements when applicable, and the observed validation state.
It includes one compact, change-shaped visual and may otherwise use prose,
bullets, or a compact table, but no additional H2 headings. Prefer a diff for a
before/after change, pseudocode for logic, a call or component tree for
ownership and flow, a file tree for structural changes, and Mermaid for
multi-component interaction. A tiny configuration or dependency change can use
a two-line text or diff sketch. GitHub-renderable text is the default; a linked
HTML artifact may supplement but never replace the in-body visual. See
[show-me PR visual guidance](references/show-me-pr-visuals.md) for the upstream
reference and PR-specific adaptation.

Immediately after it, use this machine section shape:

```markdown
<details>
<summary>For machines: exhaustive review context</summary>

## For machines

### Objective and context
<the prior behavior, problem, intended outcome, and scope boundaries>

### Implementation map
<every material file/component changed and how the pieces interact>

### Decisions and alternatives
<important choices, constraints, tradeoffs, rejected alternatives, assumptions>

### Behavioral and data impact
<before/after semantics, APIs, schemas, compatibility, side effects, edge cases>

### Risk, rollout, and rollback
<failure modes, security/performance/operational concerns, deployment order,
rollback mechanics; repeat material risk from For humans with more detail>

### Validation evidence
<exact checks and observed results; distinguish passed, failed, skipped,
and not run; connect evidence to claims>

### Review guide
<recommended review order, high-value lines/decisions, generated or noisy files>

### References and open questions
<tickets, docs, prior art, follow-ups, unresolved questions; omit only when empty>

</details>
```

The machine section has no word limit. Be super detailed: supply enough
self-contained context that a reviewing agent can evaluate intent,
implementation, correctness, risk, and validation without reconstructing the
change from scratch. Tailor the H3 subsections to the change, add nested
`<details>` for long logs or per-file notes, and omit categories only when they
are genuinely inapplicable. Never conceal uncertainty: label observed facts,
implementation decisions, assumptions, and open questions distinctly.

See [the canonical example](references/two-audience-body.md) when calibrating
coverage or nesting.

## Body Principles

- Make the human section concise enough to read quickly and the machine section
  complete enough to support an independent agent review.
- Use one focused visual to compress explanation, not to decorate the body.
  Add another visual only when it answers a distinct review question.
- Keep material risk and breaking behavior in the human section; expand on it
  in the machine section instead of hiding it there.
- Avoid long issue backstory unless it changes review strategy.
- Account for every material changed component in the machine section.
- Do not pad the body with generic checklist text.
