# Two-audience PR body reference

[two-audience-body.md](two-audience-body.md) demonstrates the mandatory body
contract with a generic CLI change:

- `## For humans` starts the body, stands alone, and stays under 300 words.
- `## For machines` is hidden in a closed `<details>` element and supplies the
  exhaustive context a reviewing agent needs.
- H3 headings and nested `<details>` organize machine detail without creating
  more H2 sections.
- Material risk remains visible in the human section even when the machine
  section expands on it.

[show-me-pr-visuals.md](show-me-pr-visuals.md) adapts HumanLayer's
[show-me skill](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md)
for GitHub PR bodies: select one compact, change-shaped visual that makes the
human summary faster to understand without turning the body into a diagram
gallery.
