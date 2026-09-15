---
name: birdclaw-x-research
description: Analyze X/Twitter posts, replies, threads, mentions, bookmarks, or account context through Birdclaw or bird CLI. Read-only; preserve raw captures before synthesis.
---

# Birdclaw X Research

Use X as social context, not ground truth. Separate observed posts from
conclusions and preserve the raw capture before synthesis.

## Contract First

When `skillspec` is available, use [`skill.spec.yml`](skill.spec.yml) for route
selection, CLI fallback order, read-only prohibitions, bounded capture rules,
dependency checks, installation approvals, tests, and trace expectations. Start
or resume with `skillspec run-loop skill.spec.yml --input '<task>' --trace-dir
.skillspec/traces --guide agent --json`.

Keep SkillSpec mechanics out of normal user-facing progress. Use
[`deps.toml`](deps.toml) for reviewed dependency evidence. Load
[`references/birdclaw.md`](references/birdclaw.md) only when concrete command,
authentication, pagination, setup, or output-normalization details are needed.
Agent UI metadata lives in [`agents/openai.yaml`](agents/openai.yaml).

## Non-Negotiables

- Stay read-only. Never post, reply, quote, repost, DM, like, bookmark, follow,
  mute, block, delete, edit profile data, or perform another X account write.
- Never expose session cookies, tokens, browser profile paths, or raw auth
  material.
- Do not persist the authenticated account's handle in reusable artifacts
  unless the user explicitly requests that disclosure.
- Preserve raw JSON or Markdown under `.context/x/` before analysis. Use public
  target data in filenames, not authenticated identity.
- Bound every fetch, page count, sync, and timeline scope. Never run a broad
  sync such as `birdclaw sync all` without an explicit bounded-scope decision.
- Prefer `bird` for a specific public post, thread, or replies; prefer
  `birdclaw` for local archive, mentions, and bookmark workflows.
- For live topic search, try the Birdclaw cache first, then use bounded `bird`
  search when the cache is empty and browser-session credentials are usable.
- Group reply themes and disagreements instead of overweighting one viral or
  unusually visible response.
- Try existing commands and `pnpm dlx` before installing. Install globally only
  after the user chooses that persistent setup route.
- Report retrieval scope, source URL, retrieval date, artifact paths, and gaps
  such as rate limits, deleted/private posts, login failures, or incomplete
  pagination.

If a command fails, report its error class instead of silently substituting a
weaker source.
