#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def run(cmd, cwd, check=True, text=True):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        rendered = " ".join(cmd)
        raise SystemExit(f"command failed: {rendered}\n{result.stderr.strip()}")
    return result


def command_exists(name):
    return shutil.which(name) is not None


def repo_root():
    result = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    return Path(result.stdout.strip())


def fetch_refs(root, remote, base_ref, pr):
    specs = []
    if base_ref.startswith(f"{remote}/"):
        branch = base_ref.split("/", 1)[1]
        specs.append(f"+{branch}:refs/remotes/{remote}/{branch}")
    if pr:
        specs.append(f"+pull/{pr}/head:refs/remotes/{remote}/pr/{pr}")
    if specs:
        run(["git", "fetch", remote, *specs], root)


def read_lines(path):
    if not path.exists():
        return []
    return [line.rstrip("\n") for line in path.read_text().splitlines()]


def parse_numstat(path):
    rows = []
    for line in read_lines(path):
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add, delete, file_path = parts[0], parts[1], parts[2]
        if add == "-" or delete == "-":
            continue
        rows.append(
            {
                "path": file_path,
                "add": int(add),
                "delete": int(delete),
                "churn": int(add) + int(delete),
            }
        )
    return rows


def is_test_path(path):
    return bool(
        re.search(r"(^|/)(test|tests|integration-tests)(/|$)", path)
        or re.search(r"\.(test|spec)\.", path)
    )


def area_for(path):
    markers = [
        "/external/postgres/",
        "/integration-tests/",
        "/presentation/graphql-schema/",
        "/presentation/",
        "/service/",
        "/adapters/",
        "/graphql-schema/",
        "/stacks/",
        "/libs/",
    ]
    for marker in markers:
        if marker in path:
            return marker.strip("/")
    parts = path.split("/")
    if len(parts) >= 3:
        return "/".join(parts[:3])
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def summarize_rows(rows):
    return {
        "files": len(rows),
        "add": sum(row["add"] for row in rows),
        "delete": sum(row["delete"] for row in rows),
        "churn": sum(row["churn"] for row in rows),
    }


def parse_tokenu_total(stdout):
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None, None
    return payload.get("total"), payload


def tokenu(root, paths, cwd=None):
    if not command_exists("bun"):
        return None, None, "bun not found"
    result = run(["bunx", "tokenu", "-s", "--json", *map(str, paths)], cwd or root, check=False)
    if result.returncode != 0:
        return None, None, result.stderr.strip() or "tokenu failed"
    total, payload = parse_tokenu_total(result.stdout)
    if total is None:
        return None, payload, "tokenu JSON did not contain total"
    return total, payload, None


def materialize_changed_files(root, materialized_dir, head_ref, files_path):
    if materialized_dir.exists():
        shutil.rmtree(materialized_dir)
    materialized_dir.mkdir(parents=True, exist_ok=True)
    materialized = []
    skipped = []
    for file_path in [line for line in read_lines(files_path) if line]:
        entry = run(["git", "ls-tree", head_ref, "--", file_path], root, check=False)
        if entry.returncode != 0 or not entry.stdout.strip():
            skipped.append((file_path, "not present at head"))
            continue
        mode = entry.stdout.split(None, 1)[0]
        if mode == "160000":
            skipped.append((file_path, "submodule gitlink"))
            continue
        blob = run(["git", "show", f"{head_ref}:{file_path}"], root, check=False, text=False)
        if blob.returncode != 0:
            skipped.append((file_path, "not a readable blob"))
            continue
        target = materialized_dir / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob.stdout)
        materialized.append(file_path)
    return materialized, skipped


def maybe_tokei(root, materialized_dir, files):
    if not command_exists("tokei"):
        return None, "tokei not found"
    if not files:
        return None, "no changed files"
    result = run(["tokei", "--output", "json", *files], materialized_dir, check=False)
    if result.returncode != 0:
        return None, result.stderr.strip() or "tokei failed"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, "tokei JSON parse failed"


def tokei_total(payload):
    if not payload:
        return None
    total = payload.get("Total")
    if not total:
        return None
    children = total.get("children", {})
    file_count = 0
    if isinstance(children, dict):
        for reports in children.values():
            if isinstance(reports, list):
                file_count += len(reports)
    return {
        "files": file_count or None,
        "lines": total.get("blanks", 0) + total.get("code", 0) + total.get("comments", 0),
        "code": total.get("code", 0),
        "comments": total.get("comments", 0),
        "blanks": total.get("blanks", 0),
    }


def git_pr_metadata(root, pr):
    if not pr or not command_exists("gh"):
        return None
    fields = "number,title,author,baseRefName,headRefName,isDraft,state,mergeable,additions,deletions,changedFiles,url,body"
    result = run(["gh", "pr", "view", str(pr), "--json", fields], root, check=False)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def write_artifacts(root, out_dir, label, base_ref, head_ref):
    out_dir.mkdir(parents=True, exist_ok=True)
    diff_path = out_dir / f"{label}.diff"
    numstat_path = out_dir / f"{label}-numstat.tsv"
    files_path = out_dir / f"{label}-files.txt"
    added_path = out_dir / f"{label}-added-lines.txt"
    added_comments_path = out_dir / f"{label}-added-comment-lines.txt"

    diff = run(["git", "diff", "--find-renames", f"{base_ref}...{head_ref}"], root).stdout
    diff_path.write_text(diff)
    numstat_path.write_text(run(["git", "diff", "--numstat", f"{base_ref}...{head_ref}"], root).stdout)
    files_path.write_text(run(["git", "diff", "--name-only", f"{base_ref}...{head_ref}"], root).stdout)
    added_lines = []
    added_comment_lines = []
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            added_lines.append(content)
            if is_comment_line(content):
                added_comment_lines.append(content)
    added_path.write_text("\n".join(added_lines) + ("\n" if added_lines else ""))
    added_comments_path.write_text("\n".join(added_comment_lines) + ("\n" if added_comment_lines else ""))
    return diff_path, numstat_path, files_path, added_path, added_comments_path


def is_comment_line(content):
    stripped = content.strip()
    if not stripped:
        return False
    return bool(
        stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped.startswith("*")
        or stripped.startswith("*/")
        or stripped.startswith("#")
        or stripped.startswith("<!--")
        or stripped.startswith("--")
        or stripped.startswith('"""')
        or stripped.startswith("'''")
    )


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9_]+(?:[-'][A-Za-z0-9_]+)?", text))


def write_pr_body(out_dir, label, metadata):
    if not metadata:
        return None
    body = metadata.get("body") or ""
    body_path = out_dir / f"{label}-pr-body.md"
    body_path.write_text(body)
    return body_path


def body_metrics(body_path):
    if not body_path or not body_path.exists():
        return None
    text = body_path.read_text()
    return {
        "lines": len(text.splitlines()),
        "words": word_count(text),
        "bytes": len(text.encode()),
    }


def fmt_int(value):
    if value is None:
        return "n/a"
    return f"{value:,}"


def markdown(args, metadata, stats, rows, area_rows, top_files, prose_stats, notes):
    lines = []
    title = f"PR {args.pr}" if args.pr else args.head
    lines.append(f"# Diff Weight: {title}")
    lines.append("")
    if metadata:
        lines.append(f"- Title: {metadata.get('title')}")
        lines.append(f"- State: {metadata.get('state')}, draft: {metadata.get('isDraft')}, mergeable: {metadata.get('mergeable')}")
        lines.append(f"- Base/head: {metadata.get('baseRefName')} <- {metadata.get('headRefName')}")
        lines.append(f"- URL: {metadata.get('url')}")
        lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    for key, value in stats:
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("## Churn Split")
    lines.append("")
    lines.append("| Category | Files | Add | Delete | Churn |")
    lines.append("|---|---:|---:|---:|---:|")
    for label, summary in rows:
        lines.append(
            f"| {label} | {fmt_int(summary['files'])} | +{fmt_int(summary['add'])} | -{fmt_int(summary['delete'])} | {fmt_int(summary['churn'])} |"
        )
    lines.append("")
    lines.append("## Areas")
    lines.append("")
    lines.append("| Area | Files | Add | Delete | Churn |")
    lines.append("|---|---:|---:|---:|---:|")
    for area, summary in area_rows:
        lines.append(
            f"| `{area}` | {fmt_int(summary['files'])} | +{fmt_int(summary['add'])} | -{fmt_int(summary['delete'])} | {fmt_int(summary['churn'])} |"
        )
    lines.append("")
    lines.append("## Top Files")
    lines.append("")
    lines.append("| Churn | Add | Delete | File |")
    lines.append("|---:|---:|---:|---|")
    for row in top_files:
        lines.append(f"| {fmt_int(row['churn'])} | +{fmt_int(row['add'])} | -{fmt_int(row['delete'])} | `{row['path']}` |")
    if prose_stats:
        lines.append("")
        lines.append("## Prose Weight")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---:|")
        for key, value in prose_stats:
            lines.append(f"| {key} | {value} |")
    if notes:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Measure GitHub PR diff weight without switching branches.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--pr", type=int, help="GitHub PR number to fetch as origin/pr/<number>")
    target.add_argument("--head", help="Existing git ref to compare against the base")
    parser.add_argument("--base", default="origin/main", help="Base ref for three-dot diff")
    parser.add_argument("--remote", default="origin", help="Git remote for PR fetches")
    parser.add_argument("--out-dir", help="Directory for generated diff artifacts")
    parser.add_argument("--materialized-dir", help="Directory for materialized changed files")
    args = parser.parse_args()

    root = repo_root()
    label = f"pr{args.pr}" if args.pr else re.sub(r"[^A-Za-z0-9_.-]+", "-", args.head).strip("-")
    out_dir = Path(args.out_dir) if args.out_dir else root / ".context" / "pr-diff-weight" / label
    materialized_dir = (
        Path(args.materialized_dir)
        if args.materialized_dir
        else root / ".context" / "pr-diff-weight" / f"{label}-files"
    )
    head_ref = f"{args.remote}/pr/{args.pr}" if args.pr else args.head

    fetch_refs(root, args.remote, args.base, args.pr)
    metadata = git_pr_metadata(root, args.pr)
    diff_path, numstat_path, files_path, added_path, added_comments_path = write_artifacts(
        root, out_dir, label, args.base, head_ref
    )
    body_path = write_pr_body(out_dir, label, metadata)

    rows = parse_numstat(numstat_path)
    total = summarize_rows(rows)
    test_rows = [row for row in rows if is_test_path(row["path"])]
    prod_rows = [row for row in rows if not is_test_path(row["path"])]
    tests = summarize_rows(test_rows)
    prod = summarize_rows(prod_rows)

    areas = {}
    for row in rows:
        area = area_for(row["path"])
        areas.setdefault(area, []).append(row)
    area_rows = sorted(
        ((area, summarize_rows(area_rows)) for area, area_rows in areas.items()),
        key=lambda item: item[1]["churn"],
        reverse=True,
    )
    top_files = sorted(rows, key=lambda row: row["churn"], reverse=True)[:10]

    notes = []
    patch_tokens, _, err = tokenu(root, [diff_path])
    if err:
        notes.append(f"Patch token count skipped: {err}.")
    added_tokens, _, err = tokenu(root, [added_path])
    if err:
        notes.append(f"Added-lines token count skipped: {err}.")
    added_comment_tokens, _, err = tokenu(root, [added_comments_path])
    if err:
        notes.append(f"Added-comment token count skipped: {err}.")
    pr_body_tokens = None
    if body_path:
        pr_body_tokens, _, err = tokenu(root, [body_path])
        if err:
            notes.append(f"PR-body token count skipped: {err}.")

    touched_file_tokens = None
    tokei_summary = None
    try:
        files, skipped = materialize_changed_files(root, materialized_dir, head_ref, files_path)
        for file_path, reason in skipped:
            notes.append(f"Skipped touched-file materialization for `{file_path}`: {reason}.")
        if files:
            touched_file_tokens, _, err = tokenu(root, files, cwd=materialized_dir)
            if err:
                notes.append(f"Touched-file token count skipped: {err}.")
        tokei_payload, err = maybe_tokei(root, materialized_dir, files)
        if err:
            notes.append(f"Tokei touched-file count skipped: {err}.")
        else:
            tokei_summary = tokei_total(tokei_payload)
    except SystemExit as exc:
        notes.append(f"Touched-file materialization skipped: {exc}.")

    diff_bytes = diff_path.stat().st_size
    diff_lines = len(read_lines(diff_path))
    added_lines = len(read_lines(added_path))
    added_comment_lines = len(read_lines(added_comments_path))
    pr_body = body_metrics(body_path)

    summary_metrics = [
        ("Files changed", fmt_int(total["files"])),
        ("Insertions / deletions", f"+{fmt_int(total['add'])} / -{fmt_int(total['delete'])}"),
        ("Total churn", fmt_int(total["churn"])),
        ("Full patch size", f"{fmt_int(diff_lines)} lines, {fmt_int(diff_bytes)} bytes"),
        ("Full patch tokens", fmt_int(patch_tokens)),
        ("Added-lines-only", f"{fmt_int(added_lines)} lines, {fmt_int(added_tokens)} tokens"),
        ("Changed-file tokens", fmt_int(touched_file_tokens)),
    ]
    if tokei_summary:
        summary_metrics.append(
            (
                "Touched-file tokei total",
                f"{fmt_int(tokei_summary['lines'])} lines, {fmt_int(tokei_summary['code'])} code, {fmt_int(tokei_summary['comments'])} comments",
            )
        )

    split_rows = [("All", total), ("Tests", tests), ("Production/schema", prod)]
    prose_stats = [
        ("Added comment lines", fmt_int(added_comment_lines)),
        ("Added comment tokens", fmt_int(added_comment_tokens)),
    ]
    if pr_body:
        prose_stats.extend(
            [
                ("PR description lines", fmt_int(pr_body["lines"])),
                ("PR description words", fmt_int(pr_body["words"])),
                ("PR description tokens", fmt_int(pr_body_tokens)),
            ]
        )
    report = markdown(args, metadata, summary_metrics, split_rows, area_rows, top_files, prose_stats, notes)
    report_path = out_dir / f"{label}-report.md"
    report_path.write_text(report)
    print(report)
    print(f"Artifacts: {out_dir}")


if __name__ == "__main__":
    main()
