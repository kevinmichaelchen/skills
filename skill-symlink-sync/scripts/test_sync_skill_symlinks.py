#!/usr/bin/env python3
"""Focused tests for sync_skill_symlinks.py."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("sync_skill_symlinks.py")


def run_sync(repo: Path, home: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--repo-root",
            str(repo),
            "--home",
            str(home),
            *extra,
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write_skill(path: Path) -> None:
    path.mkdir(parents=True)
    path.joinpath("SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")


def test_creates_links_and_replaces_collisions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        home = root / "home"
        source = repo / "demo"
        write_skill(source)

        collision_dir = home / ".claude" / "skills" / "demo"
        collision_dir.mkdir(parents=True)

        result = run_sync(repo, home, "--apply")
        agents_link = home / ".agents" / "skills" / "demo"
        claude_link = home / ".claude" / "skills" / "demo"
        backup_dir = home / ".claude" / ".skill-symlink-sync-backups" / "skills" / "demo"

        assert agents_link.is_symlink()
        assert agents_link.resolve() == source.resolve()
        assert claude_link.is_symlink()
        assert claude_link.resolve() == source.resolve()
        assert backup_dir.is_dir()
        assert "replace" in result.stdout


def test_cleans_broken_repo_links_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        home = root / "home"
        target_dir = home / ".agents" / "skills"
        target_dir.mkdir(parents=True)

        repo_link = target_dir / "removed"
        repo_link.symlink_to(repo / "removed")

        other_link = target_dir / "external"
        other_link.symlink_to(root / "external" / "missing")

        run_sync(repo, home, "--apply")

        assert not repo_link.exists()
        assert not repo_link.is_symlink()
        assert other_link.is_symlink()


def test_replaces_indirect_symlink_collision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        home = root / "home"
        source = repo / "demo"
        write_skill(source)

        agents_dir = home / ".agents" / "skills"
        claude_dir = home / ".claude" / "skills"
        agents_dir.mkdir(parents=True)
        claude_dir.mkdir(parents=True)
        agents_dir.joinpath("demo").symlink_to(source)
        claude_dir.joinpath("demo").symlink_to("../../.agents/skills/demo")

        run_sync(repo, home, "--apply")

        claude_link = claude_dir / "demo"
        backup_link = home / ".claude" / ".skill-symlink-sync-backups" / "skills" / "demo"
        assert claude_link.is_symlink()
        assert claude_link.resolve() == source.resolve()
        assert backup_link.is_symlink()


def test_ignores_nested_skills() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        home = root / "home"
        write_skill(repo / "nested" / "demo")

        result = run_sync(repo, home, "--apply")

        assert "no skills discovered" in result.stdout
        assert not (home / ".agents" / "skills" / "demo").exists()


def main() -> int:
    tests = [
        test_creates_links_and_replaces_collisions,
        test_cleans_broken_repo_links_only,
        test_replaces_indirect_symlink_collision,
        test_ignores_nested_skills,
    ]
    for test in tests:
        test()
        print(f"ok {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
