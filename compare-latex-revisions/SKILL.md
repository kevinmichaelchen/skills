---
name: compare-latex-revisions
description: Compare old and new LaTeX source files without modifying either input, then generate Word-like tracked-change TeX/PDF artifacts or synchronized side-by-side old-left/new-right comparisons with source-line references. Use for `.tex` revision diffs, `latexdiff`-style redlines, highlighted additions/deletions, grant or manuscript revision review, exact line-change reporting, and visually verified comparison PDFs.
---

# Compare LaTeX Revisions

Create review artifacts, never edits to the source pair. Treat the old file as the baseline and the new file as the proposed result.

## Choose the output

- Use **inline** for a compact Word Track Changes analogue: deleted text is red and struck through; added text is blue and underlined.
- Use **side-by-side** for clarity when prose was heavily rewritten: reproduce the old version in the left column and the new version in the right column; color changed old wording red and changed new wording blue.
- Generate **both** when the user wants a complete review package or has not chosen.
- Also offer an editor diff (`code --diff old.tex new.tex`) or terminal word diff when the user only needs source inspection.

Prefer side-by-side for extensive condensation or rewriting. Inline output becomes visually dense when most words in a paragraph changed.

## Workflow

1. Resolve the exact old and new files. Confirm their order.
2. Hash both inputs before work. Never overwrite or format them.
3. Inspect document structure, includes, bibliography commands, custom macros, and preamble differences.
4. Use `scripts/compare_latex.py` for single-file prose documents with parallel body structure:

```bash
python3 scripts/compare_latex.py old.tex new.tex \
  --mode both \
  --output-dir output/pdf \
  --compile
```

5. If the project uses `\input`, `\include`, or many custom commands:
   - Prefer installed `latexdiff --flatten` for the inline artifact.
   - Use the helper for side-by-side only after confirming its logical blocks align.
   - Compile from a copied/generated comparison tree, never by changing the originals.
6. Re-hash both inputs after generation and require identical hashes.
7. Inspect compiler logs for fatal errors, `Overfull`, and `Color stack` warnings.
8. Render every PDF page to PNG and visually inspect it. Do not deliver based on compilation alone.

## LaTeX-safe diff rules

- Diff prose at word/punctuation granularity, not whole source lines.
- Keep complete inline commands such as `\textit{...}` and `\textbf{...}` atomic while matching. Never place diff wrappers across unmatched braces.
- Keep leading and trailing whitespace outside color macros. TeX discards spaces at macro-argument boundaries and can otherwise produce joins such as `miRNAsalso`.
- In inline redlines, remove only the outer `\textbf`/`\textit` wrapper from changed spans when needed. `ulem` can make long styled spans unbreakable and cause large overflows.
- Use the new document's preamble for the inline comparison. Report preamble-only/layout changes separately because they are not naturally visible as body redlines.
- In side-by-side output, synchronize corresponding logical blocks and show subtle `old.tex:N` / `new.tex:N` labels.
- Use a vertical divider, repeated old/new page headers, red only on the old side, blue only on the new side, and black for unchanged text.
- Do not force the new document's own `twocolumn` option into the comparison layout; the comparison columns already represent the two versions. Note the layout change in the legend.

## Compilation

The helper searches for `tectonic`, bundled Codex/ChatGPT Tectonic binaries on macOS, `latexmk`, then `pdflatex`. A first Tectonic run may need package-cache/network approval.

If no compiler is available:

- Generate the `.tex` artifacts.
- Report the missing compiler explicitly.
- Give a local compile command instead of claiming a PDF exists.

For a direct `latexdiff` workflow:

```bash
latexdiff old.tex new.tex > tracked-changes.tex
latexmk -pdf tracked-changes.tex
```

Use `latexdiff --flatten` when the root files include other TeX files.

## Visual QA

Render all pages with the narrowest available tool:

```bash
pdftoppm -png comparison.pdf tmp/pdfs/comparison
```

If Poppler is unavailable, use PyMuPDF in a temporary environment. Inspect:

- margins and column divider;
- paragraph synchronization;
- section transitions and list indentation;
- word spacing at every color boundary;
- line-reference accuracy;
- headers, footers, and page numbers;
- clipping, overlap, malformed glyphs, or color leakage;
- the first and last changed paragraphs.

Extract text as a secondary check for page count, title, final paragraph, and suspicious joined words. Text extraction never replaces page-image review.

## Deliverables

- Write finals under `output/pdf/` unless the user specifies another destination.
- Keep descriptive stable names such as `tracked-changes.pdf` and `side-by-side-changes.pdf`.
- Keep generated `.tex` beside each PDF when it may help later customization.
- Remove temporary renders, package targets, auxiliary files, and logs after QA.
- State which colors mean what, page count, validation performed, and that both source hashes remained unchanged.

## Limits

The bundled side-by-side generator intentionally requires matching logical block kinds and counts. If sections, lists, or paragraphs were inserted, removed, or reordered, do not guess the alignment. Use inline output, manually construct an alignment map in a generated copy, or extend the script for the document's structure.
