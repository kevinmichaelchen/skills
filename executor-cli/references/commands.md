# Executor CLI Command Recipes

Use these recipes only after loading live `--help`; Executor's catalog and
schemas are authoritative. Replace placeholders with values from read-only
inspection.

## Preflight and discovery

```sh
command -v executor
executor --version
executor whoami
executor server list
executor tools integrations
executor tools search 'add remote MCP server'
executor call --help
executor call executor --help
```

`executor server list` marks the default profile with `*`. Every command that
talks to a server accepts `--server <profile>` or `--base-url <origin>`; when
neither is given the default profile is used, so confirm which one that is
before reading a catalog or resuming an execution.

## Hosted profile (executor.sh)

Kevin's hosted organization lives at `https://executor.sh` and is normally
saved under the profile name `cloud`. Sign in and verify against that profile
explicitly:

```sh
executor server list
executor login --base-url https://executor.sh --name cloud
executor whoami --server cloud
executor tools integrations --server cloud
executor server list
```

Rules for the hosted profile:

- The organization `/mcp` URL (for example
  `https://executor.sh/<org-slug>/mcp`) is the agent-facing MCP endpoint that
  a harness connects to. It is not the CLI `--base-url`; the CLI origin is
  `https://executor.sh`. Passing the `/mcp` URL as `--base-url` fails or
  targets the wrong surface.
- `executor login` may change the default profile to the one it just saved.
  Run `executor server list` before and after login, and restore the previous
  default with `executor server use <profile>` if it moved. Do not leave the
  default pointing at a different server than the user started with.
- Rediscover full tool paths after an OAuth reauthorization, a connection
  add/remove/refresh, a catalog refresh, or any tool-not-found error.
  Connection name segments can change case or spelling between
  authorizations. Observed: Firecrawl moved from
  `tools.firecrawl_mcp.user.personalfirecrawlmcp.*` to
  `tools.firecrawl_mcp.user.personalFirecrawlMcp.*`. A path that worked
  earlier may still be reused when none of those events happened; on the
  first failure, run `executor tools search --namespace <integration>` and
  use the returned path rather than retrying the old one.
- `executor resume` currently may render an object result as
  `[object Object]`. That is a CLI serialization defect and says nothing
  about whether the object was a success or an error. Treat the outcome as
  indeterminate: verify through observable effects (the created integration
  or connection row, the provider's returned data, or a re-run of the same
  read) before reporting success or failure. Metadata alone does not prove a
  stateless call such as a search completed.

Drill down rather than guessing:

```sh
executor call executor mcp --help
executor call executor mcp addServer --help
executor call executor coreTools oauth --help
executor call executor coreTools connections list --help
```

External integration paths live below the `tools` namespace. Either dotted or
space-separated paths may resolve; confirm with `--help`:

```sh
executor call tools.<integration>.<owner>.<connection>.<tool> --help
executor call tools <integration> <owner> <connection> <tool> --help
```

## Register a remote MCP integration

Probe the endpoint before registration when OAuth or transport is uncertain:

```sh
executor call executor mcp probeEndpoint \
  '{"endpoint":"https://example.com/mcp"}'
```

Register under a distinct, descriptive slug. An OAuth-protected example:

```sh
executor call executor mcp addServer '{
  "transport":"remote",
  "name":"Example MCP Preview",
  "endpoint":"https://example.com/mcp/preview",
  "remoteTransport":"auto",
  "slug":"example_mcp_preview",
  "authenticationTemplate":[{"kind":"oauth2","slug":"oauth2"}]
}'
```

If the call pauses, inspect the returned arguments and execution ID. Resume
only when those arguments are the exact mutation the user authorized:

```sh
executor resume --execution-id <execution-id> \
  --base-url <executor-origin> --action accept --content '{}'
```

Use `decline` or `cancel` when the target differs. Never accept a generic or
unreadable pending mutation. Executor does not currently expose a separate
paused-execution inspection command; if the original output no longer shows
the complete arguments, do not accept it.

## OAuth and Dynamic Client Registration

Discover metadata from the protected resource:

```sh
executor call executor coreTools oauth probe \
  '{"url":"https://example.com/mcp/preview"}'
executor call executor coreTools oauth clients list '{}'
```

Use the probe response to call `oauth.clients.registerDynamic --help`, then
register with the required owner, endpoints, resource, and scopes. Record the
returned client slug; the server may derive a different slug than requested.
Immediately list clients again and compare the before/after resource mapping.
If using a separate `org` or `user` owner to avoid a collision would change
credential ownership semantics and that choice is not already authorized,
stop and ask rather than guessing.

Start OAuth with the exact returned client slug:

```sh
executor call executor coreTools oauth start '{
  "client":"<returned-client-slug>",
  "clientOwner":"org",
  "owner":"org",
  "name":"examplepreview",
  "integration":"example_mcp_preview",
  "template":"oauth2",
  "identityLabel":"Example MCP Preview"
}'
```

Open the returned authorization URL locally and let the browser callback reach
Executor. Do not paste the URL into reports: it contains transient state. Poll
connection metadata without exposing credentials:

```sh
executor call executor coreTools connections list \
  '{"integration":"example_mcp_preview","owner":"org","verbose":true}'
```

Compare `oauthScope` with the intended grant. A connection row proves storage,
not usability; search the integration catalog and invoke one harmless read.
When DCR collision was possible, also invoke one harmless read through the
original integration's full namespace before declaring the setup complete.

## Tool discovery and invocation

```sh
executor tools search 'operation description' --namespace <integration>
executor call tools.<integration>.<owner>.<connection>.<tool> --help
executor call tools.<integration>.<owner>.<connection>.<tool> '<json-input>'
```

When a remote MCP exposes `discover` plus execute-family tools, call `discover`
first and use only its returned operation name, execute tool, and inputs.

## Troubleshooting order

1. Confirm the active server with `executor whoami` and any `--server` or
   `--base-url` flags.
2. List integrations, connections, and OAuth clients.
3. Inspect the integration with `executor mcp getServer --help` and the exact
   call schema.
4. Compare integration endpoint, OAuth resource, owner scope, client slug, and
   granted scopes.
5. Refresh the connection only through the live `connections.refresh` schema.
6. Reauthorize when refresh credentials are expired or bound to a replaced DCR
   client.
7. Invoke one harmless read and report the sanitized failure if it still does
   not work.

Use SQLite only for read-only diagnosis when no supported inspection surface
exists. Never write or migrate Executor state by hand.
