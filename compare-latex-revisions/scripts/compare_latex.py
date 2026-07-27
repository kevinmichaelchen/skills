#!/usr/bin/env python3
"""Generate inline and side-by-side LaTeX revision comparisons.

This helper is intentionally conservative: it never modifies its inputs and
requires matching logical block structure for side-by-side output.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(
    r"(\\(?:textit|textbf|emph)\{[^{}]*\}"
    r"|\\&"
    r"|\$[^$]*\$"
    r"|[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*"
    r"|\\[A-Za-z@]+"
    r"|[{}]"
    r"|[^\w\s]"
    r"|\s+)"
)

STRUCTURAL_RE = re.compile(
    r"\\(?:section|subsection|subsubsection)\*?\{(.*)\}"
)


@dataclass(frozen=True)
class SourceLine:
    number: int
    text: str
    kind: str


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def document_bounds(lines: list[str]) -> tuple[int, int]:
    try:
        begin = lines.index(r"\begin{document}")
        end = lines.index(r"\end{document}")
    except ValueError as error:
        raise ValueError("expected \\begin{document} and \\end{document}") from error
    return begin, end


def comparison_split(lines: list[str]) -> tuple[list[str], list[str]]:
    begin, end = document_bounds(lines)
    try:
        maketitle = lines.index(r"\maketitle", begin + 1, end)
    except ValueError:
        maketitle = begin
    return lines[: maketitle + 1], lines[maketitle + 1 : end]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def boundary_safe_markup(command: str, text: str, *, strip_style: bool) -> str:
    match = re.fullmatch(r"(\s*)(.*?)(\s*)", text, flags=re.DOTALL)
    assert match
    leading, core, trailing = match.groups()
    if not core:
        return text
    if strip_style:
        core = re.sub(r"\\(?:textbf|textit|emph)\{([^{}]*)\}", r"\1", core)
    return leading + command + "{" + core + "}" + trailing


def inline_pair(old: str, new: str) -> str:
    old_tokens = tokenize(old)
    new_tokens = tokenize(new)
    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
    pieces: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_text = "".join(old_tokens[i1:i2])
        new_text = "".join(new_tokens[j1:j2])
        if tag == "equal":
            pieces.append(new_text)
        elif tag == "delete":
            pieces.append(
                boundary_safe_markup(r"\DIFdel", old_text, strip_style=True)
            )
        elif tag == "insert":
            pieces.append(
                boundary_safe_markup(r"\DIFadd", new_text, strip_style=True)
            )
        else:
            pieces.append(
                boundary_safe_markup(r"\DIFdel", old_text, strip_style=True)
            )
            pieces.append(
                boundary_safe_markup(r"\DIFadd", new_text, strip_style=True)
            )
    return "".join(pieces)


def inline_body(old: list[str], new: list[str]) -> list[str]:
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    result: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_block = old[i1:i2]
        new_block = new[j1:j2]
        if tag == "equal":
            result.extend(new_block)
        elif tag == "replace":
            paired = min(len(old_block), len(new_block))
            result.extend(
                inline_pair(old_block[index], new_block[index])
                for index in range(paired)
            )
            result.extend(
                boundary_safe_markup(r"\DIFdel", line, strip_style=True)
                for line in old_block[paired:]
                if line
            )
            result.extend(
                boundary_safe_markup(r"\DIFadd", line, strip_style=True)
                for line in new_block[paired:]
                if line
            )
        elif tag == "delete":
            result.extend(
                boundary_safe_markup(r"\DIFdel", line, strip_style=True)
                for line in old_block
                if line
            )
        elif tag == "insert":
            result.extend(
                boundary_safe_markup(r"\DIFadd", line, strip_style=True)
                for line in new_block
                if line
            )
    return result


def inject_inline_packages(preamble: list[str]) -> list[str]:
    package_lines = [
        r"\usepackage[normalem]{ulem}",
        r"\usepackage{xcolor}",
        r"\definecolor{DIFaddcolor}{RGB}{0,76,178}",
        r"\definecolor{DIFdelcolor}{RGB}{190,30,45}",
        r"\definecolor{DIFnotebg}{RGB}{255,248,220}",
        r"\newcommand{\DIFadd}[1]{{\color{DIFaddcolor}\uline{#1}}}",
        r"\newcommand{\DIFdel}[1]{{\color{DIFdelcolor}\sout{#1}}}",
    ]
    insertion = next(
        (
            index
            for index, line in enumerate(preamble)
            if line == r"\begin{document}"
        ),
        len(preamble),
    )
    return preamble[:insertion] + package_lines + preamble[insertion:]


def preamble_comments(old: list[str], new: list[str]) -> list[str]:
    diff = list(
        difflib.unified_diff(
            old,
            new,
            fromfile="old preamble",
            tofile="new preamble",
            lineterm="",
        )
    )
    if not diff:
        return ["% No preamble changes detected."]
    return ["% PREAMBLE CHANGE: " + line for line in diff]


def build_inline(old_path: Path, new_path: Path, output: Path) -> None:
    old_lines = read_lines(old_path)
    new_lines = read_lines(new_path)
    old_preamble, old_body = comparison_split(old_lines)
    new_preamble, new_body = comparison_split(new_lines)
    preamble = inject_inline_packages(new_preamble)
    changed_preamble = old_preamble != new_preamble
    note = [
        "",
        r"\noindent\fcolorbox{gray}{DIFnotebg}{%",
        r"\parbox{\dimexpr\columnwidth-2\fboxsep-2\fboxrule\relax}{%",
        r"\small\textbf{Tracked changes:} "
        r"\textcolor{DIFaddcolor}{\uline{blue underline = added}}; "
        r"\textcolor{DIFdelcolor}{\sout{red strike-through = deleted}}."
        + (
            r" \textbf{Preamble/layout changes were also detected; "
            r"see comments at the top of this generated source.}"
            if changed_preamble
            else ""
        )
        + "}}",
        "",
    ]
    output_lines = (
        preamble_comments(old_preamble, new_preamble)
        + preamble
        + note
        + inline_body(old_body, new_body)
        + [r"\end{document}", ""]
    )
    output.write_text("\n".join(output_lines), encoding="utf-8")


def source_blocks(path: Path) -> list[SourceLine]:
    lines = read_lines(path)
    begin, end = document_bounds(lines)
    result: list[SourceLine] = []
    for index in range(begin + 1, end):
        text = lines[index].strip()
        if not text or text == r"\maketitle":
            continue
        if text in {r"\begin{itemize}", r"\end{itemize}"}:
            continue
        if text.startswith(r"\section"):
            kind = "section"
        elif text.startswith(r"\subsection"):
            kind = "subsection"
        elif text.startswith(r"\item"):
            kind = "item"
            text = text.removeprefix(r"\item").lstrip()
        else:
            kind = "paragraph"
        result.append(SourceLine(index + 1, text, kind))
    return result


def colored_pair(old: str, new: str) -> tuple[str, str]:
    old_tokens = tokenize(old)
    new_tokens = tokenize(new)
    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
    old_parts: list[str] = []
    new_parts: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_text = "".join(old_tokens[i1:i2])
        new_text = "".join(new_tokens[j1:j2])
        if tag == "equal":
            old_parts.append(old_text)
            new_parts.append(new_text)
        elif tag == "delete":
            old_parts.append(
                boundary_safe_markup(r"\OLDCHANGE", old_text, strip_style=False)
            )
        elif tag == "insert":
            new_parts.append(
                boundary_safe_markup(r"\NEWCHANGE", new_text, strip_style=False)
            )
        else:
            old_parts.append(
                boundary_safe_markup(r"\OLDCHANGE", old_text, strip_style=False)
            )
            new_parts.append(
                boundary_safe_markup(r"\NEWCHANGE", new_text, strip_style=False)
            )
    return "".join(old_parts), "".join(new_parts)


def extract_title(path: Path) -> str:
    for line in read_lines(path):
        match = re.fullmatch(r"\\title\{(.*)\}", line.strip())
        if match:
            return match.group(1)
    return "LaTeX Revision Comparison"


def render_content(kind: str, text: str) -> str:
    if kind in {"section", "subsection"}:
        match = STRUCTURAL_RE.fullmatch(text)
        if not match:
            raise ValueError(f"unsupported heading syntax: {text}")
        command = "section" if kind == "section" else "subsection"
        return rf"\{command}*{{{match.group(1)}}}"
    if kind == "item":
        return r"\CompareItem{" + text + "}"
    return text + r"\par"


def render_side_block(side: str, source: SourceLine, content: str) -> list[str]:
    return [
        rf"\LineRef{{{side}.tex:{source.number}}}",
        render_content(source.kind, content),
    ]


def build_side_by_side(
    old_path: Path, new_path: Path, output: Path, title: str
) -> None:
    old = source_blocks(old_path)
    new = source_blocks(new_path)
    if len(old) != len(new):
        raise ValueError(
            "side-by-side mode requires matching logical block counts "
            f"({len(old)} old, {len(new)} new)"
        )
    mismatches = [
        (left, right)
        for left, right in zip(old, new, strict=True)
        if left.kind != right.kind
    ]
    if mismatches:
        left, right = mismatches[0]
        raise ValueError(
            "side-by-side structure mismatch: "
            f"old line {left.number} is {left.kind}, "
            f"new line {right.number} is {right.kind}"
        )

    document = [
        r"\documentclass[10pt]{article}",
        r"\usepackage[margin=0.65in,top=0.72in,bottom=0.65in]{geometry}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{microtype}",
        r"\usepackage{xcolor}",
        r"\usepackage{paracol}",
        r"\usepackage{fancyhdr}",
        r"\definecolor{OldRed}{RGB}{190,30,45}",
        r"\definecolor{NewBlue}{RGB}{0,76,178}",
        r"\definecolor{OldBg}{RGB}{255,235,238}",
        r"\definecolor{NewBg}{RGB}{232,240,254}",
        r"\definecolor{NoteBg}{RGB}{255,248,220}",
        r"\newcommand{\OLDCHANGE}[1]{{\color{OldRed}#1}}",
        r"\newcommand{\NEWCHANGE}[1]{{\color{NewBlue}#1}}",
        r"\newcommand{\LineRef}[1]{\par\noindent{\color{gray}\fontsize{7}{8}\selectfont #1}\par\nobreak}",
        r"\newcommand{\CompareItem}[1]{\par\noindent\hangindent=1.25em\hangafter=1\makebox[1.1em][l]{\textbullet}#1\par}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{0.5\baselineskip}",
        r"\setlength{\emergencystretch}{2em}",
        r"\setlength{\columnsep}{0.34in}",
        r"\setlength{\columnseprule}{0.4pt}",
        r"\setlength{\headheight}{14pt}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\fancyhead[L]{\color{OldRed}\bfseries OLD VERSION}",
        r"\fancyhead[R]{\color{NewBlue}\bfseries NEW VERSION}",
        r"\fancyfoot[C]{\thepage}",
        r"\begin{document}",
        r"\begin{center}",
        r"{\LARGE " + title + r"}\\[0.25em]",
        r"{\large Side-by-Side Tracked Changes}",
        r"\end{center}",
        r"\noindent\fcolorbox{gray}{NoteBg}{\parbox{\dimexpr\textwidth-2\fboxsep-2\fboxrule\relax}{%",
        r"\small The left column reproduces the old file; removed or replaced wording is "
        r"\textcolor{OldRed}{red}. The right column reproduces the new file; added or "
        r"replaced wording is \textcolor{NewBlue}{blue}. Black text is unchanged. "
        r"Source-line references appear above each synchronized block. Preamble and "
        r"layout changes must be reviewed separately.}}",
        r"\vspace{0.8em}",
        r"\begin{paracol}{2}",
        r"\noindent\colorbox{OldBg}{\parbox{\dimexpr\columnwidth-2\fboxsep\relax}{\centering\bfseries\color{OldRed}OLD VERSION}}",
        r"\switchcolumn",
        r"\noindent\colorbox{NewBg}{\parbox{\dimexpr\columnwidth-2\fboxsep\relax}{\centering\bfseries\color{NewBlue}NEW VERSION}}",
        r"\switchcolumn*",
    ]
    for old_line, new_line in zip(old, new, strict=True):
        old_text, new_text = colored_pair(old_line.text, new_line.text)
        document.extend(render_side_block("old", old_line, old_text))
        document.append(r"\switchcolumn")
        document.extend(render_side_block("new", new_line, new_text))
        document.append(r"\switchcolumn*")
    document.extend([r"\end{paracol}", r"\end{document}", ""])
    output.write_text("\n".join(document), encoding="utf-8")


def tectonic_candidates() -> Iterable[Path]:
    for path in (
        Path("/Applications/Codex.app/Contents/Resources/plugins/"
             "openai-bundled/plugins/latex/bin/tectonic"),
        Path("/Applications/ChatGPT.app/Contents/Resources/plugins/"
             "openai-bundled/plugins/latex/bin/tectonic"),
    ):
        if path.is_file():
            yield path


def find_compiler(explicit: str | None) -> tuple[str, str] | None:
    if explicit:
        path = shutil.which(explicit) or explicit
        name = Path(path).name
        return name, str(path)
    tectonic = shutil.which("tectonic")
    if tectonic:
        return "tectonic", tectonic
    for path in tectonic_candidates():
        return "tectonic", str(path)
    for name in ("latexmk", "pdflatex"):
        executable = shutil.which(name)
        if executable:
            return name, executable
    return None


def compile_tex(tex_path: Path, compiler: tuple[str, str]) -> None:
    name, executable = compiler
    output_dir = tex_path.parent
    if name == "tectonic":
        command = [
            executable,
            "--keep-logs",
            "--outdir",
            str(output_dir),
            str(tex_path),
        ]
    elif name == "latexmk":
        command = [
            executable,
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-outdir={output_dir}",
            str(tex_path),
        ]
    else:
        command = [
            executable,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={output_dir}",
            str(tex_path),
        ]
    subprocess.run(command, check=True)
    log_path = tex_path.with_suffix(".log")
    if log_path.exists():
        log = log_path.read_text(encoding="utf-8", errors="replace")
        fatal_patterns = (r"^!", r"Color stack (?:over|under)flow")
        if any(re.search(pattern, log, flags=re.MULTILINE) for pattern in fatal_patterns):
            raise RuntimeError(f"unsafe compiler warnings in {log_path}")
        overfull = re.findall(r"Overfull \\[hv]box.*", log)
        if overfull:
            print(
                f"warning: {len(overfull)} overfull boxes in {log_path}; "
                "inspect and fix before delivery",
                file=sys.stderr,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument(
        "--mode",
        choices=("inline", "side-by-side", "both"),
        default="both",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("output/pdf"))
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--compiler", help="compiler executable or name")
    parser.add_argument("--title", help="raw LaTeX title for side-by-side output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    old_path = args.old.resolve()
    new_path = args.new.resolve()
    if old_path == new_path:
        raise ValueError("old and new paths must differ")
    for path in (old_path, new_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    before = {old_path: digest(old_path), new_path: digest(new_path)}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    if args.mode in {"inline", "both"}:
        inline_path = args.output_dir / "tracked-changes.tex"
        build_inline(old_path, new_path, inline_path)
        outputs.append(inline_path)
    if args.mode in {"side-by-side", "both"}:
        side_path = args.output_dir / "side-by-side-changes.tex"
        build_side_by_side(
            old_path,
            new_path,
            side_path,
            args.title or extract_title(new_path),
        )
        outputs.append(side_path)

    if args.compile:
        compiler = find_compiler(args.compiler)
        if compiler is None:
            raise RuntimeError(
                "no LaTeX compiler found; generated TeX files but no PDFs"
            )
        for output in outputs:
            compile_tex(output, compiler)

    after = {old_path: digest(old_path), new_path: digest(new_path)}
    if before != after:
        raise RuntimeError("an input file changed during comparison generation")

    for output in outputs:
        print(output)
        pdf = output.with_suffix(".pdf")
        if pdf.exists():
            print(pdf)
    print(f"old sha256: {before[old_path]}")
    print(f"new sha256: {before[new_path]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
