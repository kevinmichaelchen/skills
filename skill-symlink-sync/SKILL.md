---
name: skill-symlink-sync
description: Symlink Kevin's repo-owned skills into local agent skill directories. Use to install, relink, audit, or clean up skills under `$HOME/.agents/skills`, `$HOME/.claude/skills`, or `$HOME/.codex/skills`.
---

# Skill Symlink Sync

Keep Kevin's skills installed from this repository without maintaining a
manual list.

## Workflow

1. Confirm the repository root.
   - A skill source is any direct child directory containing `SKILL.md`.
2. Preview the sync:
   ```bash
   python3 skill-symlink-sync/scripts/sync_skill_symlinks.py --repo-root .
   ```
3. If the preview matches the requested scope, apply it:
   ```bash
   python3 skill-symlink-sync/scripts/sync_skill_symlinks.py \
     --repo-root . \
     --apply
   ```
4. Report every created, already-correct, replaced, skipped, and cleaned
   entry. If a destination was replaced, include the backup path that now holds
   the previous file, directory, or symlink.

## Sync Rules

- Link discovered skills into `$HOME/.agents/skills/<skill-name>`,
  `$HOME/.claude/skills/<skill-name>`, and `$HOME/.codex/skills/<skill-name>`.
- `--apply` is refused when `--repo-root` is a linked git worktree (for
  example a Conductor workspace): symlinks anchored there break when the
  worktree is deleted. Always sync from the primary checkout.
- Repo skills take precedence over destination collisions. A collision is any
  destination that already exists and is not a symlink to the discovered source,
  including files, directories, and symlinks to another target. Preserve the
  displaced path under `.skill-symlink-sync-backups` beside the target skill
  directory, then create the repo symlink.
- Broken symlinks may be removed only when their resolved target is inside the
  current repository root. This lets removed repo skills be cleaned up without
  touching unrelated local skill links.
- The script defaults to dry-run mode. Use `--apply` only after the preview is
  consistent with the user's request.
