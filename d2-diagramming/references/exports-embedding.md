# Exports and Embedding

## Export Formats

| Format | Use For | Notes |
| --- | --- | --- |
| SVG | Web docs, wikis, default CLI output | Uses CSS and `foreignObject`; best viewed in browser/web context |
| PNG | Static images | Rendered by Playwright/headless browser from SVG |
| PDF | Multi-page review, clickable links | Built from PNG pages; links may work, animation does not |
| PPTX | Presentations from compositions | View-only output, not editable native PowerPoint shapes/text |
| GIF | Short animated compositions | Good where animated SVG is not supported |
| TXT | ASCII diagrams | Best for comments, terminals, and plain-text docs |

## SVG Embedding

SVG links and tooltips depend on embedding mode:

- Inline SVG: links work.
- `<object>`, `<iframe>`, and `<embed>`: links work.
- `<img>` and CSS background image: links do not work.
- Markdown labels rely on XHTML `foreignObject`; pure SVG editors may render them incorrectly.

## ASCII Output

- D2 detects `.txt` and renders ASCII.
- Use `--ascii-mode=standard` for true ASCII instead of Unicode box-drawing characters.
- ASCII renders only with ELK and TALA; Dagre or unspecified layout falls back to ELK.
- Keep ASCII diagrams simple: boxes and arrows, little styling, no icons, no rich Markdown/LaTeX/code, avoid special shapes when possible.
- Many styles are moot in ASCII.

## Multi-Board Output

- Multiple SVGs are the default for many-board compositions.
- `--animate-interval=<ms>` creates animated SVG when appropriate.
- PDF and PPTX are often better than animation for large compositions.

## Source Docs

- Exports: https://d2lang.com/tour/exports/
- FAQ export notes: https://d2lang.com/tour/faq/
- ASCII blog: https://d2lang.com/blog/ascii/
- PowerPoint blog: https://d2lang.com/blog/powerpoint/
