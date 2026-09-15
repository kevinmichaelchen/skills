---
name: x-post-to-webp
description: Capture public X/Twitter post URLs as tightly cropped WEBP images using X's official embed renderer. Use for tweet screenshots, social-post images, or publication-ready X post cards, including quote posts and link previews.
---

# X Post to WEBP

Render the public post—not a hand-built imitation—then verify every image before delivery.

## Capture

Run the bundled script with one or more status URLs:

```bash
node scripts/capture-x-post.mjs \
  --output-dir .context/x-post-images \
  'https://x.com/example/status/123'
```

Resolve `scripts/capture-x-post.mjs` relative to this `SKILL.md`, not the user's working directory. The script accepts `x.com` and `twitter.com` URLs, renders X's privacy-enhanced official embed, crops to the post, and converts a high-density PNG capture to lossless WEBP with `cwebp`. It does not use browser cookies or write to X.

Useful options:

- `--theme light|dark` selects the embed theme; default to `light` for documents.
- `--scale 1..3` controls Chrome's process-level device-pixel ratio; default to `3` so cross-origin embed content is rendered sharply.
- `--chrome PATH` selects Chrome or Chromium when auto-detection fails.
- `--cwebp PATH` selects the WebP encoder when auto-detection fails. Require `cwebp`; on macOS it is provided by Homebrew's `webp` formula.

Treat a failed or incomplete embed as a retrieval failure. Do not silently replace it with a reconstructed card or a screenshot of the full X page.

## Verify

Open every generated WEBP with the available image-viewing tool. Check that:

- the complete post and any rendered quote card, media, or link preview are present;
- no text, rounded border, or engagement row is clipped;
- no loading placeholder, error notice, cookie dialog, or blank area appears;
- the output is a tightly cropped WEBP with legible text.

Retry once if the embed is incomplete. Report the source URL, output path, pixel dimensions, theme, and any inaccessible or unavailable posts. Completion means every requested URL has either a verified image or an explicit failure.
