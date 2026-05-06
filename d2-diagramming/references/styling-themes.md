# Styling, Themes, Icons, and Fonts

## Style Keywords

Use `style` for local visual attributes:

- `opacity`: float `0` to `1`
- `stroke`, `fill`, `font-color`: CSS color name, hex, or supported gradient string
- `fill-pattern`: `dots`, `lines`, `grain`, or `none`
- `stroke-width`: integer `1` to `15`
- `stroke-dash`: integer `0` to `10`
- `border-radius`: integer `0` to `20`
- `shadow`, `3d`, `multiple`, `double-border`, `animated`, `bold`, `italic`, `underline`: booleans
- `font`: currently `mono`
- `font-size`: integer `8` to `100`
- `text-transform`: `uppercase`, `lowercase`, `title`, or `none`

Root-level styles can set diagram background/frame: `fill`, `fill-pattern`, `stroke`, `stroke-width`, `stroke-dash`, and `double-border`.

For `sql_table` and `class`, `fill`, `stroke`, and `font-color` apply to header/body differently than ordinary shapes. Verify the rendered result.

## Themes

- Use `--theme` or the related environment variable to select a light theme.
- Use dark-theme settings when the exported SVG should adapt to user light/dark mode preferences.
- Special themes may set defaults beyond color, such as caps, mono font, border radius, fill patterns, or double borders.
- Use `theme-overrides` and `dark-theme-overrides` under config variables to customize theme color codes.
- Prefer themes, classes, and globs over repeating inline style.

## Icons and Images

- Use `icon: <url-or-path>` for icons/images on shapes.
- Local CLI renders can use local image paths.
- Icon placement is automatic and depends on labels, containers, and layout engine.
- Use `near` under `icon` to position icons when needed.
- Use `shape: image` for standalone icon/image shapes.
- D2 hosts common architecture icons at https://icons.terrastruct.com/.

## Fonts and Sketch Mode

- Defaults are Source Sans Pro for labels/Markdown and Source Code Pro for code/class text.
- CLI font flags include `--font-regular`, `--font-italic`, `--font-bold`, and `--font-semibold`.
- Supply all fonts when possible; missing styles fall back to defaults.
- Sketch mode uses hand-drawn fonts; provided fonts replace that sketch font family.
- Enable hand-drawn output with `--sketch`.

## Source Docs

- Styles: https://d2lang.com/tour/style/
- Themes: https://d2lang.com/tour/themes/
- Icons: https://d2lang.com/tour/icons/
- Fonts: https://d2lang.com/tour/fonts/
- Sketch mode: https://d2lang.com/tour/sketch/
- Dark mode blog: https://d2lang.com/blog/dark-mode/
- Hand-drawn blog: https://d2lang.com/blog/hand-drawn-diagrams/
