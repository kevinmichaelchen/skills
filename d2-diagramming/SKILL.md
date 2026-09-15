---
name: d2-diagramming
description: Create, edit, validate, or export D2 diagrams. Use for `.d2` files, architecture diagrams, C4, sequence, ERD, UML, grid, animated, or multi-board diagrams, D2 styling/layout, exports, and rendering or CLI troubleshooting.
---

# D2 Diagramming

Use D2 as a software-documentation language, not a generic charting language. Prefer diagrams that fit on a whiteboard, describe systems clearly, and remain readable as text.

## Workflow

1. Clarify the diagram job: architecture overview, C4 view, sequence diagram, ERD, UML class diagram, grid/table-like diagram, animation/steps, presentation, embedded doc asset, or existing `.d2` maintenance.
2. Pick the structure before styling:
   - Use one file for small diagrams.
   - Use imports for shared models, classes, themes, templates, or domain-owned components.
   - Use composition when the user needs abstraction layers, scenarios, steps, zooming, or presentation output.
3. Write readable D2 first. Use meaningful IDs, concise labels, containers for architecture boundaries, and manual dimensions only to solve layout or readability problems.
4. Add styling through themes, classes, and globs. Keep one-off inline style for real local exceptions.
5. Select the layout engine deliberately. Use Dagre for quick hierarchical diagrams, ELK for orthogonal routing and SQL row routing, and TALA when available for software-architecture layouts, symmetry, per-container direction, locked positions, and object-near hints.
6. Validate and render. Run `d2 fmt` or compile when available; export to the target format and inspect the output type's limitations.

## Load References

Always start with:

- `references/diagram-design.md`
- `references/syntax-core.md`

Then load only the relevant detail:

- Layout choice: `references/layout-engines.md`
- Styling, themes, icons, fonts, or sketch mode: `references/styling-themes.md`
- Imports, shared files, templates, or refactors: `references/modularity-imports.md`
- Layers, scenarios, steps, board links, animation, or presentations: `references/composition-animation.md`
- Sequence, ERD, UML class, grid, or markdown/text diagrams: `references/diagram-types.md`
- C4-style architecture: `references/c4-model.md`
- SVG, PNG, PDF, PPTX, GIF, ASCII, or embedding: `references/exports-embedding.md`
- CLI, editor support, or D2 Oracle: `references/cli-tooling.md`
- Render failures or confusing output: `references/troubleshooting.md`
- Original docs inventory: `references/source-doc-map.md`

You can run `scripts/d2_bundle_refs.sh <intent>` to list a minimal reference bundle.

## Export Guidance

- For web/docs, prefer SVG for vector diagrams unless the destination rejects SVG or renders `foreignObject` incorrectly.
- When the destination requires a raster image, deliver WEBP. Render through a temporary PNG with `scripts/d2_render.sh input.d2 output.webp`; do not retain or publish the PNG unless compatibility explicitly requires it.
- PNG/PDF and WEBP's intermediate render depend on Playwright/headless browser support; WEBP conversion additionally requires `cwebp` or ImageMagick.
- For multi-board diagrams, choose multiple SVGs, PDF, PPTX, GIF, or animated SVG based on audience and diagram size.
- For source code comments or terminal docs, export ASCII and keep the diagram simple: boxes/arrows, ELK/TALA, minimal shapes, no rich text/icons/styles.
- For presentations, use PPTX for view-only slides; do not imply PowerPoint objects are editable.

## Quality Bar

- Prefer model-first diagrams: nodes and relationships first, visual style second.
- Use imports to separate reusable model, view, style, and template files.
- Use globs/classes for consistent defaults, tags, and view filtering.
- Use `suspend`/`unsuspend` plus globs for model-view and C4-style subsets.
- Keep labels short; move secondary context to tooltips, markdown text blocks, legends, or adjacent notes.
- Quote labels/keys with reserved characters, URI fragments containing `#`, or reserved keywords used as normal keys.
- Add newlines or explicit width/height when text or dense connections hurt readability.
- Test the export in the same embedding mode the user will use.

## Helper Scripts

- `scripts/d2_check.sh <file.d2>...` verifies the CLI, formats files with `d2 fmt`, and compiles SVGs in a temp directory.
- `scripts/d2_render.sh [options] input.d2 output.ext` renders one diagram with common layout/theme/sketch/animation/ASCII flags and supports optimized WEBP delivery through a temporary PNG.
- `scripts/d2_bundle_refs.sh <intent>` prints the recommended reference files for a task.
