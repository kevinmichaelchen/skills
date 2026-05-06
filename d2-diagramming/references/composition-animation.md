# Composition and Animation

Use composition when a single static board cannot carry the story.

## Board Types

| Keyword | Meaning | Use For |
| --- | --- | --- |
| `layers` | New blank boards with no inheritance | Different abstraction levels or zoom targets |
| `scenarios` | Boards that inherit from the base layer | Alternate views of the same system |
| `steps` | Boards that inherit from the previous step | Sequences, build-ups, and animations |

## Links

- `link` can target external URLs or internal boards.
- Quote board names that contain `.`.
- In link values, `_` refers to parent boards, not parent containers.
- Backlinks/navigation can make multi-board diagrams usable when exported.

## Export Choices

- Multiple SVGs: default for many boards; internal links are rewritten to file paths.
- Animated SVG: use `--animate-interval=<ms>` for small compositions or short step loops.
- Animated GIF: useful where SVG animation is not supported.
- PDF: good for layers and multi-page review; links can be clickable.
- PPTX: useful for presentations and Google Slides sharing; output is view-only.

## Animation Patterns

- Show change by overlaying versions in place instead of side-by-side.
- Show deployment or user-flow steps with `steps`.
- Build up a diagram from small pieces to a final view.
- Keep animated loops short enough for the audience to understand without waiting.

## Source Docs

- Composition intro: https://d2lang.com/tour/composition/
- Composition formats: https://d2lang.com/tour/composition-formats/
- Layers: https://d2lang.com/tour/layers/
- Scenarios: https://d2lang.com/tour/scenarios/
- Steps: https://d2lang.com/tour/steps/
- Board links: https://d2lang.com/tour/linking/
- Animation blog: https://d2lang.com/blog/animation/
