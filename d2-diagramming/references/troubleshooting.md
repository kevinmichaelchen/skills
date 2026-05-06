# Troubleshooting

## Syntax and Labels

- If a label or value will not compile, wrap it in single or double quotes.
- Quote reserved keywords when using them as regular keys.
- Quote links containing `#` URI fragments.
- Use ASCII syntax punctuation in non-ASCII text diagrams.
- If Markdown HTML breaks SVG parsing, use semantic XML-compatible HTML such as `<br/>`.

## Layout and Readability

- If text renders too wide, add explicit newlines.
- If dense connections clutter a short-label shape, increase `width` and `height` to give edge routes more surface area.
- If routes are tangled in Dagre, try ELK.
- If architecture layout fights a hierarchy, try TALA when available.
- Check layout-specific limitations before using object `near`, `top`, `left`, per-container direction, or ancestor-to-descendant connections.

## Export and Embedding

- If SVG interactivity disappears, check embedding mode. `<img>` and CSS backgrounds block links.
- If Markdown SVG looks wrong in design tools, verify whether the viewer supports HTML `foreignObject`.
- If PNG/PDF export fails, check Playwright/headless browser dependencies.
- If PDF lacks animation, that is expected; PDF can preserve links but not SVG animation.
- If PPTX users expect editable shapes/text, clarify that current output is view-only.
- If ASCII output looks poor, simplify shapes, remove styles/icons/rich text, and use ELK/TALA.

## Source Docs

- Troubleshooting: https://d2lang.com/tour/troubleshoot/
- Exports: https://d2lang.com/tour/exports/
- Layouts: https://d2lang.com/tour/layouts/
- ASCII blog: https://d2lang.com/blog/ascii/
