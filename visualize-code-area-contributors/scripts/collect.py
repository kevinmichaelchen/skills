#!/usr/bin/env python3
"""Cache path-scoped Git history without interpreting contributor identities."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path, help="local Git repository")
    parser.add_argument("--path", required=True, help="repository-relative directory or file")
    parser.add_argument("--ref", default="HEAD", help="Git revision to analyze")
    parser.add_argument("--out", required=True, type=Path, help="evidence bundle")
    parser.add_argument("--include-merges", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        sys.exit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def parse_log(raw_log: str) -> list[dict[str, Any]]:
    commits: list[dict[str, Any]] = []
    for block in raw_log.split("\x1e"):
        if not block.strip():
            continue
        header, *numstat_lines = block.strip("\n").splitlines()
        fields = header.split("\x1f", 4)
        if len(fields) != 5:
            sys.exit(f"unexpected git log header: {header!r}")
        sha, authored_at, author_name, author_email, subject = fields
        changes = []
        for line in numstat_lines:
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            additions, deletions = parts[:2]
            changes.append({
                "path": "\t".join(parts[2:]),
                "additions": int(additions) if additions.isdigit() else None,
                "deletions": int(deletions) if deletions.isdigit() else None,
            })
        commits.append({
            "sha": sha,
            "authored_at": authored_at,
            "author_name": author_name,
            "author_email": author_email,
            "subject": subject,
            "changes": changes,
        })
    return commits


def main() -> int:
    args = parse_args()
    repo = Path(git(args.repo, "rev-parse", "--show-toplevel").strip())
    head_sha = git(repo, "rev-parse", args.ref).strip()
    path = args.path.strip("/")
    existence = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{head_sha}:{path}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if existence.returncode:
        sys.exit(f"path does not exist at {args.ref}: {path}")

    raw_dir = args.out / "raw"
    selection_path = raw_dir / "selection.json"
    commits_path = raw_dir / "commits.json"
    selection = {
        "repo_root": str(repo),
        "path": path,
        "requested_ref": args.ref,
        "head_sha": head_sha,
        "include_merges": args.include_merges,
    }
    if not args.refresh and selection_path.exists() and commits_path.exists():
        if json.loads(selection_path.read_text()) == selection:
            cached = json.loads(commits_path.read_text())
            print(json.dumps({**selection, "commit_count": len(cached), "cache": "reused"}, indent=2))
            return 0

    log_args = [
        "log",
        head_sha,
        "--numstat",
        "--format=%x1e%H%x1f%aI%x1f%aN%x1f%aE%x1f%s",
    ]
    if not args.include_merges:
        log_args.append("--no-merges")
    log_args.extend(["--", path])
    commits = parse_log(git(repo, *log_args))
    if not commits:
        sys.exit(f"no commits found for {path} at {args.ref}")
    write_json(selection_path, selection)
    write_json(commits_path, commits)
    print(json.dumps({**selection, "commit_count": len(commits), "cache": "written"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
