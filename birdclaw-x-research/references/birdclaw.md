# Birdclaw Command Reference

This is a compact reference for agent research workflows. Prefer `--json` for captures and preserve the raw output before analysis.

## Install And Verify

Use an existing install first:

```bash
command -v birdclaw
command -v bird
command -v xurl
```

Not on `PATH` does not mean unavailable. Before installing anything, try the no-install path — these run the published packages without a global install:

```bash
pnpm dlx birdclaw <args>
pnpm dlx @steipete/bird <args>
pnpm dlx @xdevplatform/xurl <args>
```

Install globally only when the user wants a persistent setup:

```bash
pnpm add -g birdclaw @steipete/bird @xdevplatform/xurl
```

Alternative Birdclaw install on macOS:

```bash
brew install steipete/tap/birdclaw
```

Verify auth without persisting account identifiers in artifacts:

```bash
bird check                 # per-browser credential status (Chrome/Safari/Firefox)
bird whoami                # identity — do not persist the handle in artifacts
xurl whoami
birdclaw auth status --json
```

`bird` reads the active Safari, Chrome, or Firefox X browser session. If the user is not signed in, ask them to sign in before retrying. Treat browser cookies as full account credentials.

Safari cookie-read warnings can appear even when Chrome auth succeeds. Treat them as non-fatal warnings: if `bird check` shows any browser's credentials are OK, live reads will work.

## Direct Tweet Reads With bird

Use `bird` for one-off public tweet, thread, and reply capture through the active browser session:

```bash
bird read <tweet-id> --json
bird thread <tweet-id> --json
bird replies <tweet-id> --json
```

If flags or subcommands differ, run:

```bash
bird --help
bird <subcommand> --help
```

Use this path when the user points at a specific X URL and wants the post, its author thread, or replies.

`bird replies` has no `-n`; paginate it with `--all --max-pages`:

```bash
bird replies <tweet-id> --json --all --max-pages 2
```

## Live Topic Search With bird

When Birdclaw's local cache is empty (`birdclaw search tweets "..."` returns `[]`) and `xurl` auth is unavailable, `bird` can run live topic search through the browser session. Keep queries bounded — use `since:`, `min_faves:`, filters, and page caps:

```bash
bird check
bird search '"AGENTS.md" since:2026-03-01 min_faves:10' --json -n 30
bird search '"AGENTS.md" since:2026-03-01 -filter:replies' --json --all --max-pages 3
bird replies <tweet-id> --json --all --max-pages 2
```

Output shapes differ, and downstream analysis must normalize both:

- A simple search returns a plain array: `Tweet[]`.
- A paginated run (`--all --max-pages`) returns an object: `{ tweets: Tweet[], nextCursor: string | null }`.

Read `tweets` when the value is an object, otherwise treat the top-level value as the tweet array.

## Local Birdclaw Reads

Initialize local state only when the user wants Birdclaw as a local archive/cache:

```bash
birdclaw init
birdclaw db stats --json
```

Search local tweets:

```bash
birdclaw search tweets "local-first" --json
birdclaw search tweets "query" --author <public-handle> --limit 20 --json
birdclaw search tweets --liked --limit 20 --json
birdclaw search tweets --bookmarked --limit 20 --json
```

Research bookmarked material:

```bash
birdclaw research "codex" --limit 20 --thread-depth 10 --json
birdclaw research "codex" --limit 20 --thread-depth 10 --out .context/x/codex-research.md
```

Mentions workflow:

```bash
birdclaw sync mentions --mode xurl --limit 100 --max-pages 3 --refresh --json
birdclaw sync mention-threads --mode xurl --limit 30 --json
birdclaw mentions export "agent" --unreplied --limit 10 --json
```

For one-off mention reads, `mentions export --refresh` is acceptable, but repeated workflows should ingest with `sync mentions` first and read from the cache.

## Live Sync Caution

Live sync can spend API reads and broaden the privacy surface. Keep sync commands explicit, bounded, and tied to the user's request.

Useful bounded sync commands:

```bash
birdclaw sync bookmarks --mode auto --limit 100 --refresh --json
birdclaw sync likes --mode auto --limit 100 --refresh --json
birdclaw sync timeline --limit 100 --refresh --json
birdclaw sync mention-threads --mode bird --limit 30 --delay-ms 1500 --timeout-ms 15000 --json
```

Avoid `birdclaw sync all` unless the user explicitly asks for a broad local refresh.

## Writes Are Out Of Scope

This skill is read-only. Do not run write-capable Birdclaw, bird, xurl, or browser commands from this skill, even if the user asks for content creation or account changes.

Out-of-scope actions include creating new tweets, replying to tweets, quoting tweets, retweeting or reposting tweets, sending DMs, liking, bookmarking, following, muting, blocking, deleting content, editing profile data, or any other action that modifies X/Twitter content or account state.

Examples of commands to avoid:

```bash
birdclaw compose post "text"
birdclaw compose reply <tweet-id> "text"
birdclaw compose dm <conversation-id> "text"
birdclaw blocks add <handle-or-id>
birdclaw blocks remove <handle-or-id>
birdclaw mute <handle-or-id>
birdclaw unmute <handle-or-id>
```
