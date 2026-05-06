# D2 Design Principles

Use this reference before creating or refactoring diagrams.

## Decision Rules

- Prefer readability over terse syntax. D2 intentionally spends a few extra characters when that keeps the source understandable.
- Let D2 defaults carry most aesthetics. Add custom style only after the model is clear.
- Separate the system from the diagram styling. Use imports, classes, and globs so model files do not become scattered style declarations.
- Keep diagrams "whiteboard-fit". Split, filter, or compose large systems rather than forcing hundreds of nodes onto one board.
- Treat D2 as software documentation, not a general visualization or big-data graph tool.
- Let warnings be warnings. D2 often compiles through ignorable issues, so inspect warnings rather than assuming success means perfect intent.
- Prefer desktop/server workflows. D2 has a strong CLI, stdin/stdout support, imports, many export formats, and a Go API.

## Authoring Heuristics

- Start with components, boundaries, and relationships.
- Use containers for ownership, network, deployment, domain, or abstraction boundaries.
- Use labels for human-facing wording and IDs for stable references.
- Keep labels short; put secondary detail in tooltips, markdown text, legends, or nearby notes.
- If a diagram becomes hard to review, split model/style/view into imports.
- If the same model needs multiple audiences, use `suspend`/`unsuspend`, globs, and imports instead of copying the model.

## Source Docs

- D2 design decisions: https://d2lang.com/tour/design/
- D2 FAQ: https://d2lang.com/tour/faq/
- D2 tour intro: https://d2lang.com/tour/intro/
