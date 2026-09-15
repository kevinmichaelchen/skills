# Show-me visuals for PR bodies

Use HumanLayer's
[show-me skill](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md)
as the visual-language source. Adapt it to GitHub review by placing one compact,
change-shaped visual in `## For humans`, next to the explanation it supports.

Choose the smallest truthful view:

- `diff` for before/after behavior, configuration, component shape, or file layout.
- Pseudocode for a logic or state transition.
- A call tree, component tree, or shallow file tree for ownership and structure.
- Mermaid for interaction among multiple components or steps.

Keep only the calls, files, props, states, and boundaries a reviewer needs. A
small dependency bump can show `old version -> new version`; a broad refactor
can show a shallow file-tree diff. Do not add a visual that merely repeats the
prose or implies behavior the diff does not establish.

Prefer fenced text, diff, or Mermaid that GitHub renders in the body. A focused
HTML artifact can be useful during discussion, but GitHub does not render it
inline; link it only as supplemental evidence and retain an in-body visual.
