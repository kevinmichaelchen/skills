# Layout Engines

## Selection Matrix

| Engine | Use For | Watch For |
| --- | --- | --- |
| Dagre | Fast default hierarchical diagrams and quick drafts | Unmaintained upstream, curved multi-segment routes, weaker container routing |
| ELK | Orthogonal routing, fewer crossings, container-to-container routing, SQL table row routing | Still hierarchical, can add unnecessary bends, limited symmetry |
| TALA | Software architecture, non-hierarchical whiteboard-like layout, symmetry, first-class containers, exact row routing | Proprietary separate install, newer, small changes can alter layout more |

## Feature Support Notes

- Choose the layout with `--layout=<engine>` or `D2_LAYOUT=<engine>`.
- List available layouts with `d2 layout`.
- Use `d2 layout <engine>` for engine-specific flags.
- `near` to constants works generally; `near` to another object is TALA-only.
- `top` and `left` to lock positions are TALA-only.
- Per-container `direction` is TALA-only.
- Container `width` and `height` are documented as ELK-only in the pulled docs; non-container dimensions work generally.
- Ancestor-to-descendant connections do not work in Dagre.
- SQL table connections point to exact rows in ELK and TALA.

## Practical Defaults

- Start with Dagre for simple top-down dependency flows.
- Try ELK when edges look tangled, when diagrams have important containers, or when ERD row routing matters.
- Use TALA when the user explicitly has it installed or needs software-architecture polish that hierarchical layout fights.

## Source Docs

- Layout overview: https://d2lang.com/tour/layouts/
- Dagre: https://d2lang.com/tour/dagre/
- ELK: https://d2lang.com/tour/elk/
- TALA: https://d2lang.com/tour/tala/
