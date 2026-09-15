---
name: executor-cli
description: Inspect, configure, authorize, call, and troubleshoot Executor integrations through its supported CLI. Use for Executor catalogs, remote MCP registration, OAuth or Dynamic Client Registration, connections, paused approvals, explicit tool calls, or Executor integration health.
---

# Executor CLI

Use Executor's self-management tools instead of editing its storage. Treat the
CLI catalog as the live contract: drill into `--help`, search tools, and use the
exact returned path and schema.

## Contract First

When `skillspec` is available, run [`skill.spec.yml`](skill.spec.yml) with the
task before acting. Use [`deps.toml`](deps.toml) for dependency evidence. Load
[`references/commands.md`](references/commands.md) whenever a concrete command,
remote MCP registration, OAuth flow, or paused execution is needed.

## Procedure

1. **Preflight.** Resolve the active server profile (`executor server list`
   marks the default; pass `--server` or `--base-url` explicitly when the
   target is not the default) and inspect integrations, connections, OAuth
   clients, and relevant tool help before mutation. Completion: the target
   profile, integration, owner, connection, endpoint, and current OAuth client
   resource are known or explicitly absent.
2. **Select the supported surface.** Prefer `executor call executor ...` for
   self-management and `executor call tools.<address> ...` for integration
   tools. Never mutate `~/.executor/data.db` or another backing store.
   Completion: the exact live tool path and input schema are resolved.
3. **Execute the narrow request.** Add, authorize, resume, or call only what the
   user requested. If Executor pauses, accept only when the pending arguments
   exactly match an already authorized action; otherwise show the approval to
   the user. Completion: Executor returned a successful result or a precise
   actionable blocker.
4. **Verify behavior.** Re-list metadata after configuration and invoke one
   harmless target tool. Do not call a connection ready merely because an
   integration row or stored authorization exists. Completion: the intended
   tool works, scope and resource changes are reported, and unrelated
   integrations remain unchanged or any impact is explicit.

## Non-Negotiables

- Never guess a tool address or payload. Use hierarchical `--help` and
  `executor tools search` against the live catalog.
- Never reveal secrets or credential-bearing output, including the private URL
  emitted by `executor open`. Keep sensitive commands in a local pipe and report
  only sanitized results.
- Treat Dynamic Client Registration as resource-sensitive. Before and after
  registration, list OAuth clients and compare owner, returned slug, client ID,
  and resource. Do not assume the requested slug is retained.
- Avoid registering two resources from the same OAuth issuer in the same owner
  scope until collision behavior is understood. A derived client slug may
  replace another resource's metadata; use a separate owner scope or a
  resource-specific client and verify both connections.
- Compare requested OAuth scopes with the final connection grant. Report scope
  expansion instead of describing a broad grant as least privilege.
- Keep parallel versions under distinct integration and connection names and
  call their full namespaces explicitly to avoid cached or overlapping tools.
- Never remove an integration, connection, OAuth client, or server profile
  without an exact user request and a read-only target check.
- The organization `/mcp` URL is the agent-facing MCP endpoint, never the CLI
  `--base-url`. The hosted CLI origin is `https://executor.sh`.
- `executor login` may change the default profile. Record the default before
  login and restore it with `executor server use` if it moved.
- Rediscover full tool paths after OAuth reauthorization, connection or
  catalog changes, or a tool-not-found error; connection name segments can
  change (Firecrawl moved from `personalfirecrawlmcp` to
  `personalFirecrawlMcp`). Do not retry a failed stale path.
- `executor resume` may print an object result as `[object Object]`. That is
  a CLI serialization defect and proves neither success nor failure. Treat
  the outcome as indeterminate and verify it through observable effects or
  provider output before reporting either.

`executor whoami` describes stored CLI authentication; a local daemon may still
serve self-management calls when it reports "not logged in." Test a catalog
read before diagnosing authentication from that line alone.
