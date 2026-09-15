---
name: confluence-pages
description: Search, read, summarize, create, update, comment on, or attach files and images to Confluence through Executor's Atlassian MCP integrations. Use for Confluence URLs, pages, blog posts, attachments, inline images, comments, freshness checks, or Confluence context.
---

# Confluence Pages

Treat Confluence as field notes, not gospel. It is useful context, especially
recent ADRs and active comment threads, but may be stale, incomplete,
contradictory, or unsettled.

## Contract First

When `skillspec` is available, use [`skill.spec.yml`](skill.spec.yml) for route
selection, write prohibitions, ownership checks, bounded approvals, dependency
requirements, tests, and trace expectations. Start or resume with
`skillspec run-loop skill.spec.yml --input '<task>' --trace-dir
.skillspec/traces --guide agent --json`.

Keep SkillSpec mechanics out of normal user-facing progress. Use
[`deps.toml`](deps.toml) for reviewed dependency evidence. Load
[`reference/operations.md`](reference/operations.md) only when concrete
Executor or Atlassian MCP calls are needed. Agent UI metadata lives in
[`agents/openai.yaml`](agents/openai.yaml).

## Non-Negotiables

- Read through Executor's authenticated Atlassian integration. Re-resolve a
  missing tool address with live discovery rather than guessing it.
- For local attachments or inline images, use an independently named Atlassian
  Rovo MCP v2 connection. Discover `createConfluenceAttachment` live, prepare
  the upload, run its short-lived command locally, and embed the returned
  `fileId` with collection `contentId-<content-id>`.
- Never declare attachment upload unavailable from the v1 catalog alone. If v2
  is missing or unauthenticated, load `$executor-cli` and configure or repair it
  through supported CLI tools; never edit Executor's database directly.
- Never print, persist, or repeat upload bearer tokens. Do not confuse an
  attachment ID (`att...`) with the media `fileId` required by the page body.
- Prefer SVG for vector diagrams when Confluence accepts and renders the asset
  correctly. For raster charts and diagrams, upload WEBP; treat PNG/JPEG as
  intermediate or explicit compatibility formats, not the default deliverable.
  Before embedding, verify the actual MIME type, pixel dimensions, and byte
  size rather than trusting the filename extension.
- When inline placement was requested, do not stop after upload. Fetch the
  current HTML body, preserve unrelated content, dry-run the update, publish,
  and read it back to verify the expected media nodes.
- Every HTML body sent to Confluence must be independently valid. Never leave
  raw template markers, bare text, or Markdown image syntax at the document
  root; wrap temporary attachment slots in valid block elements, then replace
  those fetched blocks with media nodes after upload.
- For prose-heavy pages and blog posts, prefer Confluence's native
  `contentWidth: "narrow"`; use `wide` for content whose tables or diagrams need
  it and `max` only when the user or artifact requires it. Never simulate a
  reading-width constraint with inline CSS. Preserve the fetched body and
  verify the published width plus existing media after a width-only update.
- For summaries, report the page title and URL or ID, author/owner, created and
  latest-version times, whether comments were checked, and confidence.
- Treat active comments as evidence that can materially change a page's
  meaning. Prefer current, corroborated material and preserve disagreements.
- Never present Confluence alone as final authority for consequential product,
  policy, security, or compliance claims; verify against code, Jira, PRs,
  owners, or live behavior.
- Write only when the user explicitly requests an exact write and the contract's
  ownership route allows it. Pages owned by the user are the only normal write
  surface.
- Treat an explicit imperative as approval only when the current context also
  fixes the destination, files, and intended placement. Otherwise elicit the
  missing details or bounded write approval.
- Never modify team-owned pages, governed records such as ADRs, or another
  author's page. Never archive, delete, move, reorganize, or bulk-edit pages.
- Default comments on another person's page to a draft in the response. An
  exact-page, exact-comment override must be explicit and pass the contract.
- Fetch the current page immediately before any allowed update, verify
  author/owner and destination, and preserve unrelated content.

If live Atlassian behavior contradicts the contract or operations reference,
use the live result only for the safe part of the current task, then report the
drift instead of silently adapting.
