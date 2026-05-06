# C4-Style Diagrams in D2

Use these patterns for C4-like architecture diagrams and other model-view diagram sets.

## Core Pattern

1. Define one model repository: people, systems, containers, components, and relationships.
2. Tag model elements with classes for audience, domain, layer, ownership, or technology.
3. Suspend all model elements with globs.
4. Unsuspend the subset needed for each view with globs and filters.
5. Add view-specific aggregate relationships where the lower-level model is too detailed.

## Useful Features

- `suspend` marks shapes/connections for removal until restored.
- `unsuspend` restores matching shapes/connections.
- Globs and filters slice views from a shared model.
- Markdown labels hold richer names and descriptions.
- `c4-person` supports person-shaped model elements with longer labels.
- The C4 theme gives recognizable C4 styling.
- Classes can function like C4 tags.
- `d2-legend` creates a diagram legend from a variable.
- Layers and `link` support C4-style zooming between abstraction levels.

## Suggested File Split

- `models.d2`: canonical model definitions and relationships.
- `styles.d2`: theme, classes, colors, legend defaults.
- `<audience>-view.d2`: imports models/styles and unsuspends a specific slice.
- `<component>-code.d2`: zoomed-in lower-level diagrams.
- `overview.d2`: composition file linking layers/views together.

## View Heuristics

- Context view: show users, external systems, and the system boundary.
- Container view: show deployable/runtime containers and external dependencies.
- Component view: show important internal components for one container.
- Code view: reserve for a narrow implementation explanation.
- Avoid pretending C4 is strict UML. D2 supports the C4 concepts, but the goal is clarity for the audience.

## Source Docs

- C4 blog: https://d2lang.com/blog/c4/
- Models: https://d2lang.com/tour/models/
- Model-view: https://d2lang.com/tour/model-view/
- Layers: https://d2lang.com/tour/layers/
- Board links: https://d2lang.com/tour/linking/
