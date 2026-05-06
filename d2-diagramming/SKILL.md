---
name: d2-diagramming
description: Create, edit, refactor, validate, and export D2 diagrams for software architecture and documentation. Use when Codex needs to work with `.d2` files or D2 syntax; generate architecture diagrams, C4-style views, sequence diagrams, ERDs, UML class diagrams, grid diagrams, multi-board compositions, animated diagrams, SVG/PNG/PDF/PPTX/GIF/ASCII exports; choose D2 layout engines, themes, classes, globs, imports, variables, icons, tooltips, links, or troubleshoot D2 rendering and CLI issues.
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

## Output Rules

- For web/docs, prefer SVG unless the target strips interactivity or cannot render SVG `foreignObject`.
- For static images, use PNG; remember PNG/PDF depend on Playwright/headless browser support.
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
- `scripts/d2_render.sh [options] input.d2 output.ext` renders one diagram with common layout/theme/sketch/animation/ASCII flags.
- `scripts/d2_bundle_refs.sh <intent>` prints the recommended reference files for a task.
