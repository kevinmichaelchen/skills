#!/usr/bin/env python3
"""Synchronize repo-owned skills into local skill directories as symlinks."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TARGETS = (".agents/skills", ".claude/skills", ".codex/skills")


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--apply", action="store_true",
                        help="create and remove symlinks; default is dry-run")
    return parser.parse_args()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def symlink_target_path(link: Path) -> Path:
    raw_target = Path(link.readlink())
    if raw_target.is_absolute():
        return raw_target
    return link.parent.joinpath(raw_target)


def normalized_symlink_target_path(link: Path) -> Path:
    return Path(os.path.abspath(symlink_target_path(link)))


def describe_destination(path: Path) -> str:
    if path.is_symlink():
        return f"symlink to {symlink_target_path(path)}"
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "file"
    return "path"


def next_backup_path(backup_dir: Path, name: str) -> Path:
    candidate = backup_dir / name
    if not candidate.exists() and not candidate.is_symlink():
        return candidate

    suffix = 1
    while True:
        candidate = backup_dir / f"{name}.{suffix}"
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        suffix += 1


def discover_skills(repo_root: Path) -> list[Skill]:
    try:
        children = sorted(path for path in repo_root.iterdir() if path.is_dir())
    except OSError:
        return []

    return [
        Skill(name=child.name, path=child.resolve())
        for child in children
        if child.joinpath("SKILL.md").is_file()
    ]


def clean_broken_repo_links(target_dir: Path, repo_root: Path, apply: bool) -> list[str]:
    actions: list[str] = []
    if not target_dir.exists():
        return actions

    for entry in sorted(target_dir.iterdir()):
        if not entry.is_symlink():
            continue
        target = symlink_target_path(entry)
        if target.exists():
            continue
        resolved_target = target.resolve(strict=False)
        if not is_relative_to(resolved_target, repo_root):
            continue
        actions.append(f"clean broken {entry} -> {target}")
        if apply:
            entry.unlink()

    return actions


def sync_skill(skill: Skill, target_dir: Path, backup_dir: Path, apply: bool) -> str:
    destination = target_dir / skill.name

    if destination.is_symlink():
        target = normalized_symlink_target_path(destination)
        if target.exists() and target == skill.path:
            return f"ok {destination} -> {skill.path}"

    if destination.exists() or destination.is_symlink():
        backup_path = next_backup_path(backup_dir, destination.name)
        previous = describe_destination(destination)
        if apply:
            target_dir.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)
            destination.rename(backup_path)
            destination.symlink_to(skill.path, target_is_directory=True)
        return (
            f"replace {destination} -> {skill.path} "
            f"(backup: {backup_path}; previous: {previous})"
        )

    if apply:
        target_dir.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(skill.path, target_is_directory=True)
    return f"create {destination} -> {skill.path}"


def is_linked_worktree(repo_root: Path) -> bool:
    # In a linked worktree (e.g. a Conductor workspace) .git is a file whose
    # gitdir points under <primary>/.git/worktrees/; in the primary checkout
    # it is a directory. Walk up so a --repo-root pointed at a subdirectory
    # of a worktree is still caught. Submodules also use a .git file, but
    # their gitdir points under .git/modules/ and the checkout is stable, so
    # only the worktree case is refused. Unreadable .git files are treated
    # as worktrees: a wrongly-refused sync beats symlinks that die with the
    # worktree.
    for candidate in (repo_root, *repo_root.parents):
        git_entry = candidate / ".git"
        if git_entry.is_dir():
            return False
        if git_entry.is_file():
            try:
                gitdir = git_entry.read_text()
            except OSError:
                return True
            return "/worktrees/" in gitdir
    return False


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    home = args.home.expanduser().resolve()
    target_dirs = [home / target for target in DEFAULT_TARGETS]

    if is_linked_worktree(repo_root):
        if args.apply:
            print(
                f"refusing --apply: {repo_root} is a linked git worktree; "
                "symlinks must be anchored to the primary checkout so they "
                "survive worktree deletion. Re-run with "
                "--repo-root <primary checkout>."
            )
            return 1
        print(
            f"warning: {repo_root} is a linked git worktree; --apply will "
            "be refused. Use the primary checkout as --repo-root."
        )

    skills = discover_skills(repo_root)
    mode = "apply" if args.apply else "dry-run"
    print(f"skill symlink sync ({mode})")
    print(f"repo: {repo_root}")

    if not skills:
        print("no skills discovered")

    for target_dir in target_dirs:
        backup_dir = target_dir.parent / ".skill-symlink-sync-backups" / target_dir.name
        print(f"target: {target_dir}")
        for action in clean_broken_repo_links(target_dir, repo_root, args.apply):
            print(f"  {action}")
        for skill in skills:
            print(f"  {sync_skill(skill, target_dir, backup_dir, args.apply)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
