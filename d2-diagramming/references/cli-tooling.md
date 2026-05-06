# CLI, Tooling, and API

## Common Commands

- `d2 input.d2`: render `input.svg`.
- `d2 input.d2 output.svg`: render explicit output.
- `d2 - output.svg`: read D2 from stdin.
- `d2 input.d2 -`: write SVG to stdout.
- `d2 fmt file.d2`: format in place.
- `d2 layout`: list available layout engines.
- `d2 layout <engine>`: inspect engine-specific flags.

## Common Flags and Env

- `--layout=<engine>` or `D2_LAYOUT=<engine>`
- `--theme=<id>` and dark-theme equivalents
- `--sketch`
- `--animate-interval=<ms>`
- `--ascii-mode=standard`
- Font flags: `--font-regular`, `--font-italic`, `--font-bold`, `--font-semibold`

Flags and environment variables override `vars.d2-config`.

## Editor and Collaboration Support

D2 has documented support or integrations for VSCode, Vim, Obsidian, Slack, and Discord. Prefer local CLI validation even when editing through an extension.

## D2 Oracle

Use `d2/d2oracle` when programmatically editing diagrams in Go.

- Functions are pure and return a new graph.
- `Create` creates shapes/connections and parent containers as needed.
- `Set` sets attributes or primary values.
- `Delete` deletes shapes/connections; deleting containers deletes children.
- `Rename` renames IDs and references. It is not label editing.
- `Move` moves shapes/connections across containers.
- ID delta helpers track changed IDs after move/delete/rename.

## Source Docs

- Install: https://d2lang.com/tour/install/
- Autoformat: https://d2lang.com/tour/auto-formatter/
- Layouts: https://d2lang.com/tour/layouts/
- D2 Oracle: https://d2lang.com/tour/api/
- Editor support: https://d2lang.com/tour/editor-support/
- VSCode: https://d2lang.com/tour/vscode/
- Vim: https://d2lang.com/tour/vim/
- Obsidian: https://d2lang.com/tour/obsidian/
- Slack: https://d2lang.com/tour/slack/
- Discord: https://d2lang.com/tour/discord/
