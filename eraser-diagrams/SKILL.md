---
name: eraser-diagrams
description: Create, edit, validate, render, or troubleshoot Eraser Diagrams JSON. Use for architecture diagrams, process flows, entity-relationship diagrams, grouped system maps, Eraser component schemas, the eraser-diagrams CLI, PNG or HTML export, and WebP delivery.
---

# Eraser Diagrams

Author explicit diagram JSON and iterate against the renderer's measured output. Treat the source JSON as the maintainable artifact and the image as a generated deliverable.

## Workflow

1. Define the diagram's audience, question, required facts, target dimensions, and output format. Do not invent relationships or cardinalities.
2. Read [`references/authoring.md`](references/authoring.md). Use the split `{ "entities": [...], "connections": [...] }` document form unless existing input uses the interleaved form.
3. Lay out semantic groups and primary flow before decoration. Give every entity a stable, meaningful ID and non-negative integer coordinates.
4. Inspect the live component contract when using an unfamiliar tag:
   - `npx --yes @eraserlabs/diagrams-cli@0.1.0 registry`
   - `npx --yes @eraserlabs/diagrams-cli@0.1.0 schema <tag>`
5. Validate before rendering. Treat warnings as failures unless the user knowingly accepts the degradation:
   - `npx --yes @eraserlabs/diagrams-cli@0.1.0 validate diagram.json --fail-on-warning`
6. Render and inspect the actual artifact. For PNG or HTML, use the upstream CLI. For WebP, use `scripts/render_eraser.sh`, which validates, renders a temporary PNG, and converts it without retaining the intermediate.
7. View raster output after every material layout change. Check clipped text, overlaps, edge crossings, weak hierarchy, excessive canvas size, and readability at the intended display width. Revise and repeat until those checks pass.
8. Deliver the editable JSON beside the requested output and report any accepted warnings, external icon/font dependencies, or compatibility fallbacks.

Completion means the JSON validates, the requested artifact renders, and visual inspection confirms that every required fact and relationship is readable.

## Rendering

Read [`references/cli.md`](references/cli.md) for installation, Chromium discovery, configuration, exit codes, and troubleshooting.

```sh
# Native PNG
npx --yes @eraserlabs/diagrams-cli@0.1.0 render diagram.json \
  --out diagram.png --scale 2 --fail-on-warning

# Optimized WebP through a temporary PNG
scripts/render_eraser.sh diagram.json diagram.webp 2
```

The upstream CLI natively emits PNG and HTML, not SVG or WebP. Never relabel a PNG as WebP; convert it and verify the resulting MIME type.

## Quality Bar

- Keep one reading direction and align peer nodes to a visible grid.
- Use groups for real boundaries, not decorative framing.
- Keep labels short; move explanations into surrounding prose or a legend.
- Use consistent colors to encode meaning and include a legend when color is semantic.
- Prefer `DatabaseRelationship` for ER cardinalities and `Relationship` for ordinary flow.
- Record the actor or direction in edge labels only when the line alone is ambiguous.
- Use stock icons only when network access is acceptable. Unknown icons degrade to placeholders unless configured as errors.
- Prefer `--scale 2` for documentation raster output, then resize at the embedding surface rather than rendering tiny text.

## Source Authority

This skill follows [`eraserlabs/eraser-diagrams`](https://github.com/eraserlabs/eraser-diagrams/tree/6d377f296b94abf63481a07128884066e4930321), MIT licensed. The installed CLI's `registry` and `schema` output remain authoritative when they differ from this skill's concise reference.
