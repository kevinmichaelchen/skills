# Diagram Types

## Sequence Diagrams

- Set `shape: sequence_diagram` on an object.
- Sequence diagrams use normal D2 syntax with two key differences: child actors share scope, and declaration order controls visual order.
- Declare actors early when participant order matters.
- Spans are nested actor objects connected as part of an interaction.
- Groups are containers inside the sequence diagram that are not themselves connected.
- Notes are nested actor objects with no connections.
- Self-messages are actor-to-same-actor connections.
- Style actors and messages as ordinary D2 shapes/connections; lifelines inherit actor stroke and dash.

## SQL Tables and ERDs

- Use `shape: sql_table`.
- Each key defines a row. The row value is the type.
- Constraint values define constraints; recognized values shorten to `PK`, `FK`, and `UNQ`.
- Multiple constraints can be arrays.
- Quote reserved keywords used as row names.
- Use foreign key connections between table rows.
- ELK and TALA route connections to exact rows.

## UML Classes

- Use `shape: class`.
- Each key is a field or method.
- Field values are types.
- Keys containing `(` are methods; values are return types. Missing value means void.
- Visibility prefixes: none or `+` public, `-` private, `#` protected.

## Grid Diagrams

- Use `grid-rows` and `grid-columns`.
- Defining only one dimension lets cells expand in the other direction.
- When both are set, the first one declared is the dominant fill direction.
- Use `width`, `height`, `grid-gap`, `vertical-gap`, and `horizontal-gap` for specific constructions.
- `grid-gap: 0` can build maps or tables, but Markdown tables may be simpler for duplicate-heavy data.
- Connections to grids work normally. Connections between shapes inside a grid are straight center-to-center segments because the grid controls positions.
- Grid diagrams can nest other grid diagrams.
- Use invisible elements to pad and align grids.

## Source Docs

- Sequence diagrams: https://d2lang.com/tour/sequence-diagrams/
- SQL tables: https://d2lang.com/tour/sql-tables/
- UML classes: https://d2lang.com/tour/uml-classes/
- Grid diagrams: https://d2lang.com/tour/grid-diagrams/
- Text and Markdown: https://d2lang.com/tour/text/
