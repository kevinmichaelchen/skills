---
name: crawl-docs
description: Mirror official documentation sites into the shared local cache at $HOME/.cache/crawl/ using `pnx @mdream/crawl`. Use when asked to pull, mirror, or grab docs for a tool or library, when a task needs offline/official reference material, or before evaluating a new dependency.
---

# Crawl Docs

We keep local markdown mirrors of official documentation so agents can read
authoritative references without fetching the web mid-task. The mirroring tool
is [`@mdream/crawl`](https://github.com/harlan-zw/mdream).

## Conventions

- All mirrors live under `$HOME/.cache/crawl/<hostname>/`, one directory per
  documentation site, named exactly by hostname (e.g. `knip.dev`, `oxc.rs`,
  `vitest.dev`, `maple.dev`).
- The cache is user-global, shared across projects, and lives outside every
  repository — nothing to git-ignore and no per-project copies.
- `pnx` is the user's shell alias for `pnpm dlx`. In non-interactive shells run
  `pnpm dlx` directly.

## Pulling a site

```sh
pnpm dlx @mdream/crawl -u <url> -o ~/.cache/crawl/<hostname> \
  --artifacts "markdown,llms.txt" --max-pages 500
```

Example:

```sh
pnpm dlx @mdream/crawl -u https://oxc.rs -o ~/.cache/crawl/oxc.rs \
  --artifacts "markdown,llms.txt" --max-pages 500
```

The tool discovers pages via sitemap.xml when one exists and falls back to a
recursive same-domain crawl (default depth 3, `--depth <n>` to change). It
writes one markdown file per page preserving URL paths, plus an `llms.txt`
index. A 150-page site takes a few seconds.

Useful flags:

- `--max-pages <n>` — hard page cap; always set it so a crawl can never run
  unbounded. If the tool reports exactly the cap, the crawl was cut short —
  re-run with a higher cap (each run takes seconds) until the reported count
  comes in under it.
- `-u "<host>/docs/**"` — scope the crawl to one section.
- `--exclude "<pattern>"` — skip URLs. Patterns must include the domain
  (`"example.com/api/**"`); bare file globs like `"**/*.html"` are rejected.
- `--driver playwright` — only for JS-rendered sites that come back empty with
  the default HTTP driver.

Known quirk: sites that link every page in two URL forms (`/page` and
`/page.html`) get mirrored twice, as `page.md` and `page-html.md` with the
same content. Don't try to exclude one form — deep pages are often linked in
only one of them — just accept the duplicates; disk is cheap and reads still
find the content.

## After pulling

- Verify content landed: `find ~/.cache/crawl/<hostname> -type f | head`,
  and sanity-check the page count against the site's apparent size.
- Re-pulling into the same directory refreshes pages but does not delete
  removed ones; for a clean refresh, delete the hostname directory first.

## Using mirrors

- Check `ls ~/.cache/crawl/` first — the mirror may already exist from
  another project.
- Prefer reading the mirror over live web fetches when the mirror exists.
- Delegate large doc-digestion jobs to subagents and point them at the mirror
  directory; tell them not to fetch the web.
- Mirrors are reference material, not project content: never import from,
  link to, or commit anything under `~/.cache/crawl/`.
