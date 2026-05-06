# Core D2 Syntax

## Shapes, Labels, Containers

- A bare key declares a shape. The default shape is `rectangle`.
- A shape's default label is its key. Assign a value to give it a different label.
- Keys are case-insensitive, so choose stable lowercase IDs.
- Use `shape: <type>` to choose another shape.
- Some shapes keep a 1:1 aspect ratio; long labels can make them both wider and taller.
- Use nested maps for containers. Use `_` inside a container to reference the parent scope.
- Use semicolons for multiple declarations on one line only when readability remains high.

## Strings and Comments

- Prefer unquoted strings when legal.
- Use single or double quotes for reserved characters, reserved words used as keys, or values that contain syntax characters.
- If a string contains both quote types, use double quotes and escape as usual.
- `#` starts a line comment. Block comments use triple double quotes.
- In non-English diagrams, make sure syntax punctuation is ASCII, such as `:` rather than lookalike fullwidth punctuation.

## Connections

- Valid connectors are `--`, `->`, `<-`, and `<->`.
- Referencing undeclared shapes in a connection creates them.
- Connections must reference shape IDs, not labels.
- Repeated connections create multiple connections; they do not override.
- Chaining can be readable for linear flows.
- Cycles are allowed.
- Customize arrowheads with `source-arrowhead` and `target-arrowhead`; keep arrowhead labels short.
- Reference a connection by original ID plus index when you need to style or delete a specific repeated edge.

## Text and Rich Labels

- Standalone text is Markdown.
- Declare a shape explicitly when setting a Markdown label on it.
- Use language tags for code blocks. Common aliases include `md`, `tex`, `js`, `go`, `py`, `rb`, and `ts`.
- Use `latex` or `tex` for mathematical notation; it is MathJax, not full document LaTeX.
- Use `shape: text` for non-Markdown text.
- For block strings that contain `|`, add more delimiter characters or use another non-alphanumeric delimiter.

## Interactivity and Positioning

- `tooltip` adds hover text; it uses HTML `title`, so do not expect Markdown rendering inside it.
- `link` adds clickable links. Quote links containing `#` fragments.
- `near` can position title, legend, text, tooltip, label, or icon near diagram points.
- Common `near` values: `top-left`, `top-center`, `top-right`, `center-left`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`.
- Label/icon positions can use `outside-*` and border positioning.
- Object-relative `near` and `top`/`left` are TALA-only.

## Variables

- Define variables under `vars`.
- Substitute with `${name}` and nested names with `${parent.child}`.
- Variables are scoped like programming-language variables.
- Single quotes bypass substitution.
- Use `...${x}` to spread map or array values.
- Some CLI-like settings can live in `vars.d2-config`, but flags and environment variables take precedence.

## Classes and Globs

- Use classes to reuse attributes and style.
- Object attributes override class attributes.
- Multiple classes apply left-to-right.
- Classes can act as SVG/CSS tags for post-processing.
- Use globs to apply broad changes in one line.
- Globs apply backward and forward in their scope.
- `**` targets recursively; triple globs apply globally across nested layers and imports.
- Use filters with `&`, inverse filters with `!&`, and endpoint filters for connections.
- Use globs to change theme defaults, tag/filter models, and suspend/unsuspend views.

## Overrides and Deletion

- Redeclaring a shape merges with the previous declaration.
- The latest explicit label setting wins.
- Set a shape, connection, or attribute to `null` to delete it.
- Nulling a shape removes endpoint connections and descendants.

## Source Docs

- Strings: https://d2lang.com/tour/strings/
- Shapes: https://d2lang.com/tour/shapes/
- Connections: https://d2lang.com/tour/connections/
- Containers: https://d2lang.com/tour/containers/
- Text: https://d2lang.com/tour/text/
- Interactive: https://d2lang.com/tour/interactive/
- Positions: https://d2lang.com/tour/positions/
- Variables: https://d2lang.com/tour/vars/
- Classes: https://d2lang.com/tour/classes/
- Globs: https://d2lang.com/tour/globs/
- Overrides: https://d2lang.com/tour/overrides/
