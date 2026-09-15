# Eraser JSON authoring

## Document form

Prefer the split form because it makes missing relationships explicit and permits the default relationship tag:

```json
{
  "entities": [
    {
      "tag": "Shape",
      "id": "api",
      "x": 40,
      "y": 40,
      "width": 180,
      "texts": [{ "text": "API", "fontSize": 18 }],
      "color": "blue"
    },
    {
      "tag": "Shape",
      "id": "database",
      "x": 320,
      "y": 40,
      "shape": "cylinder",
      "texts": [{ "text": "Orders" }],
      "color": "purple"
    }
  ],
  "connections": [
    { "from": "api", "to": "database", "label": "SQL" }
  ]
}
```

Both `entities` and `connections` are required, including an empty connections array. The alternative `{ "elements": [...] }` form requires `tag` on every item. Do not submit a bare array.

Entities require `tag`, `id`, `x`, and `y`. Coordinates are non-negative integer pixels from the top-left. Authored width and height are minimums; measured text can enlarge an element. Connections require `from` and `to` IDs. In the split form, an omitted connection tag means `Relationship`.

## Stock vocabulary

| Tag | Use |
|---|---|
| `Shape` | General nodes and geometric symbols |
| `Icon` | Catalog icon with caption |
| `Textbox` | Standalone Markdown text |
| `Group` | Structural container with a horizontal title |
| `Lane`, `Pool` | BPMN-style swimlanes |
| `Activity`, `Event`, `Gateway` | BPMN process elements |
| `DatabaseTable` | Table with named, typed fields |
| `Legend` | Explicit visual key |
| `Divider` | Section separator |
| `Relationship` | Ordinary directed or undirected edge |
| `DatabaseRelationship` | Crow's-foot database cardinality |

Run `eraser-diagrams schema <tag>` before using detailed properties that are not shown here.

## Relationships

`Relationship` supports `label`, `fromPort`, `toPort`, `connectorStyle`, `cornerStyle`, `lineStyle`, `lineWidth`, `color`, `startArrowhead`, and `endArrowhead`. Common ports are `top`, `right`, `bottom`, and `left`; common arrowheads include `arrow`, `bar`, `dot`, `triangle`, `crowFootSingle`, and `crowFootMany`.

Use `DatabaseRelationship.relType` with `one-to-one`, `one-to-many`, `many-to-one`, or `many-to-many` rather than manually approximating database cardinality.

## Containment

Create a `Group`, `Lane`, or `Pool`, then set each child's `containerId` to the container's ID. Size and position the container to leave clear internal padding. Containment is semantic and affects routing; do not simulate it by drawing a box behind unrelated nodes.

## Styling

Use a small semantic palette: `white`, `yellow`, `green`, `blue`, `purple`, `red`, `orange`, or `black`, or explicit CSS colors. Use `bgColor` and `borderColor` only for targeted surface overrides. Keep `styleMode` consistent among peers (`plain`, `shadow`, or `watercolor`).

Text runs support Markdown plus `fontSize`, `color`, `hAlign`, and `typeface`. Prefer a shared typeface and no more than three meaningful text sizes. For `Shape`, typeface belongs on each text run; other tags may accept it at the root.

## Iteration loop

1. Validate with warnings treated as failures.
2. Render at the intended aspect ratio and `--scale 2` for raster documentation.
3. Inspect the rendered image, not just the JSON.
4. Adjust coordinates, minimum dimensions, ports, or labels.
5. Repeat until labels are unclipped, connections are traceable, and the composition remains readable at final display size.

Rendered JSON from the Node API can include measured entity boxes and routed connection points. Use it for geometry diagnosis; keep the authored source as the canonical editable document.
