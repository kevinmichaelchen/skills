# Eraser Diagrams CLI

## Requirements and version

- Node.js 22.12 or newer.
- A local Chromium-family browser for rendering; validation does not need a browser.
- `@eraserlabs/diagrams-cli@0.1.0`, reviewed from upstream commit `6d377f296b94abf63481a07128884066e4930321`.
- `cwebp` or ImageMagick only when producing WebP through the bundled wrapper.

Install locally with `npm install -D @eraserlabs/diagrams-cli`, or use the pinned package through `npx --yes @eraserlabs/diagrams-cli@0.1.0`.

## Commands

```sh
eraser-diagrams validate diagram.json --fail-on-warning
eraser-diagrams render diagram.json --out diagram.png --scale 2 --fail-on-warning
eraser-diagrams render diagram.json --out diagram.html --format html --fail-on-warning
eraser-diagrams registry
eraser-diagrams schema Shape
eraser-diagrams init
```

Multiple render inputs share one warm browser. Use `--out-dir` for batches and `--pages` for controlled concurrency. Use `--json` for machine-readable reports; status and issues otherwise go to stderr.

## Chromium discovery

Resolution order is `--chromium-path`, `CHROMIUM_PATH`, `chromiumPath` in `eraser-diagrams.config.json`, then automatic detection. Run `eraser-diagrams init` to pin the detected path in a project config.

The CLI discovers `eraser-diagrams.config.json` by walking upward until the first Git root. Explicit `--config` or `ERASER_DIAGRAMS_CONFIG` takes precedence. Relative paths resolve from the config file's directory.

## Strict rendering

Use `--fail-on-warning` for publication artifacts. Typical warnings include unknown icon names and degraded fonts. Use `--unknown-icon error` when placeholders would mislead. Stock icons are fetched from Eraser's public asset catalog and therefore require network access unless a cache or custom base URL is configured.

Exit codes are:

- `0`: all inputs succeeded.
- `1`: an input failed validation or rendering, or warnings were promoted to errors.
- `2`: invocation/configuration failure, such as a bad flag or missing Chromium.

## WebP

The CLI emits PNG and HTML. Run:

```sh
scripts/render_eraser.sh input.json output.webp 2
```

The wrapper validates strictly, renders to a private temporary directory, converts with `cwebp` first or ImageMagick as a fallback, and removes the temporary PNG. If neither converter exists, install one or deliver the native PNG with an explicit compatibility explanation.
