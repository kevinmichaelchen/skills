# Modularity and Imports

## Import Forms

- Regular import treats the imported file as a map value.
- Spread import inserts imported contents into the current map.
- Spread imports only work inside maps.
- Omit the `.d2` extension; the formatter normalizes it.
- D2 imports only `.d2` files.
- Use partial imports to import one object or subtree.
- Quote imported file names containing `.` because dot also targets nested fields.
- Relative imports are relative to the importing file, not the process working directory.
- Absolute imports are supported, but relative imports are more portable.

## Patterns

- Model-view: define reusable models once, import them into view files, and show subsets with globs.
- Modular classes: keep classes in a shared style file, mirroring HTML/CSS separation.
- Nested composition: keep each board flat and readable, then import them into higher-level compositions.
- Imported template: wrap diagrams in a shared branded or documentation template.

## Organizational Uses

- Compliance: keep canonical architecture or policy diagrams in files that rarely change.
- Domain ownership: let teams maintain their own domain files and compose them.
- Code reviews: isolate model, view, and style changes so diffs are easier to review.
- Reuse: centralize color classes, shapes, legends, and domain models.
- DRY: update shared objects once and import them across diagrams.

## Source Docs

- Import syntax: https://d2lang.com/tour/imports/
- Import use cases: https://d2lang.com/tour/imports-use-cases/
- Model-view: https://d2lang.com/tour/model-view/
- Modular classes: https://d2lang.com/tour/modular-classes/
- Nested composition: https://d2lang.com/tour/nested-composition/
- Imported template: https://d2lang.com/tour/imported-template/
