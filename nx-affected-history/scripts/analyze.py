#!/usr/bin/env python3
"""Replay a historical Nx affected comparison in a cached detached worktree."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
LOCKFILES = {"pnpm-lock.yaml", "pnpm-lock.yml", "package-lock.json", "yarn.lock", "bun.lock", "bun.lockb"}


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def nx_environment() -> dict[str, str]:
    """Return the minimal environment needed by Nx's `env node` launcher."""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node is required to run Nx")
    node_directory = str(Path(node).parent)
    search_path = os.pathsep.join(dict.fromkeys([node_directory, *os.defpath.split(os.pathsep)]))
    return {
        "PATH": search_path,
        "NX_DAEMON": "false",
        "NX_INTERACTIVE": "false",
    }


def git(repo: Path, *args: str) -> str:
    return run(["git", *args], repo)


def parse_json_output(output: str) -> Any:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Nx did not emit JSON:\n{output[-2000:]}")


def nx_projects(worktree: Path, target: str, *, base: str | None = None, head: str | None = None, files: list[str] | None = None) -> list[str]:
    command = [str(worktree / "node_modules/.bin/nx"), "show", "projects", "--affected", f"--with-target={target}", "--json"]
    if files is not None:
        if not files:
            return []
        command.append("--files=" + ",".join(files))
    else:
        command.extend([f"--base={base}", f"--head={head}"])
    payload = parse_json_output(run(command, worktree, nx_environment()))
    return sorted(payload)


def expand_inputs(inputs: list[Any], named_inputs: dict[str, Any]) -> list[str]:
    patterns: list[str] = []
    for item in inputs:
        if isinstance(item, str) and item in named_inputs:
            patterns.extend(expand_inputs(named_inputs[item], named_inputs))
        elif isinstance(item, str) and item.startswith("{workspaceRoot}/"):
            patterns.append(item.removeprefix("{workspaceRoot}/"))
        elif isinstance(item, dict) and isinstance(item.get("fileset"), str) and item["fileset"].startswith("{workspaceRoot}/"):
            patterns.append(item["fileset"].removeprefix("{workspaceRoot}/"))
    return patterns


def implicit_workspace_matches(graph: dict[str, Any], nx_json: dict[str, Any], changed_files: list[str]) -> list[dict[str, Any]]:
    matches = []
    global_named = nx_json.get("namedInputs", {})
    for project, node in graph["nodes"].items():
        named = {**global_named, **node.get("data", {}).get("namedInputs", {})}
        for target, config in node.get("data", {}).get("targets", {}).items():
            for pattern in expand_inputs(config.get("inputs", []), named):
                matching = sorted(file for file in changed_files if fnmatch.fnmatchcase(file, pattern))
                if matching:
                    matches.append({"project": project, "target": target, "pattern": pattern, "matched_files": matching})
    return sorted(matches, key=lambda row: (row["project"], row["target"], row["pattern"]))


def owned_projects(graph: dict[str, Any], changed_files: list[str]) -> dict[str, list[str]]:
    roots = sorted(
        ((node.get("data", {}).get("root", ""), name) for name, node in graph["nodes"].items()),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    result: dict[str, list[str]] = {}
    for file in changed_files:
        owners = [name for root, name in roots if root and (file == root or file.startswith(root + "/"))]
        if owners:
            result[file] = [owners[0]]
    return result


def lockfile_policy(nx_json: dict[str, Any]) -> Any:
    for plugin in nx_json.get("plugins", []):
        if isinstance(plugin, dict) and plugin.get("plugin") in {"@nx/js", "@nx/js/typescript"}:
            if "projectsAffectedByDependencyUpdates" in plugin.get("options", {}):
                return plugin["options"]["projectsAffectedByDependencyUpdates"]
    return "default: all projects"


def project_edges(graph: dict[str, Any]) -> list[tuple[str, str]]:
    return sorted({
        (edge["source"], edge["target"])
        for group in graph.get("dependencies", {}).values()
        for edge in group
        if isinstance(edge.get("source"), str) and isinstance(edge.get("target"), str)
    })


def reverse_adjacency(graph: dict[str, Any]) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {name: [] for name in graph.get("nodes", {})}
    for source, target in project_edges(graph):
        reverse.setdefault(target, []).append(source)
    for dependents in reverse.values():
        dependents.sort()
    return reverse


def shortest_reverse_path(start: str, end: str, reverse: dict[str, list[str]]) -> list[str] | None:
    if start == end:
        return [start]
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        current, path = queue.popleft()
        for dependent in reverse.get(current, []):
            if dependent in seen:
                continue
            next_path = [*path, dependent]
            if dependent == end:
                return next_path
            seen.add(dependent)
            queue.append((dependent, next_path))
    return None


def seed_reasons(
    selected: list[str],
    changed_files: list[str],
    owners: dict[str, list[str]],
    workspace_matches: list[dict[str, Any]],
    policy: Any,
) -> dict[str, list[dict[str, Any]]]:
    reasons: dict[str, list[dict[str, Any]]] = defaultdict(list)
    owned_files: dict[str, list[str]] = defaultdict(list)
    for filename, projects in owners.items():
        for project in projects:
            owned_files[project].append(filename)
    for project, files in sorted(owned_files.items()):
        reasons[project].append({"kind": "project-ownership", "matched_files": sorted(files)})
    for match in workspace_matches:
        reasons[match["project"]].append({
            "kind": "workspace-input",
            "configured_target": match["target"],
            "pattern": match["pattern"],
            "matched_files": match["matched_files"],
        })
    lockfiles = sorted(filename for filename in changed_files if Path(filename).name in LOCKFILES)
    if lockfiles and policy == "default: all projects":
        for project in selected:
            reasons[project].append({
                "kind": "lockfile-default-all",
                "matched_files": lockfiles,
            })
    return dict(reasons)


def explain_selection(
    selected: list[str],
    target: str,
    graph: dict[str, Any],
    changed_files: list[str],
    owners: dict[str, list[str]],
    workspace_matches: list[dict[str, Any]],
    policy: Any,
) -> list[dict[str, Any]]:
    reverse = reverse_adjacency(graph)
    seeds = seed_reasons(selected, changed_files, owners, workspace_matches, policy)
    kind_order = {"project-ownership": 0, "workspace-input": 1, "lockfile-default-all": 2}
    explanations = []
    for project in selected:
        candidates = []
        for seed, reasons in seeds.items():
            path = shortest_reverse_path(seed, project, reverse)
            if path is None:
                continue
            for reason in reasons:
                candidates.append({
                    "seed_project": seed,
                    "seed_reason": reason,
                    "dependency_path": path,
                })
        candidates.sort(key=lambda item: (
            len(item["dependency_path"]),
            kind_order.get(item["seed_reason"]["kind"], 99),
            item["seed_project"],
            item["seed_reason"].get("configured_target", ""),
        ))
        explanations.append({
            "project": project,
            "requested_target": target,
            "primary": candidates[0] if candidates else {
                "seed_project": None,
                "seed_reason": {"kind": "unattributed"},
                "dependency_path": [],
            },
            "alternatives": candidates[1:6],
            "candidate_count": len(candidates),
        })
    return explanations


def project_config_targets(payload: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(payload.get("targets"), dict):
        return payload["targets"]
    if isinstance(payload.get("nx"), dict) and isinstance(payload["nx"].get("targets"), dict):
        return payload["nx"]["targets"]
    return None


def is_direct_workspace_input(item: Any) -> bool:
    return (
        isinstance(item, str) and item.startswith("{workspaceRoot}/")
    ) or (
        isinstance(item, dict)
        and isinstance(item.get("fileset"), str)
        and item["fileset"].startswith("{workspaceRoot}/")
    )


def remove_workspace_inputs(
    worktree: Path,
    graph: dict[str, Any],
    nx_json: dict[str, Any],
    matches: list[dict[str, Any]],
    projects: set[str],
) -> tuple[dict[Path, str], list[dict[str, Any]]]:
    backups: dict[Path, str] = {}
    removals: list[dict[str, Any]] = []
    targets_by_project: dict[str, set[str]] = defaultdict(set)
    for match in matches:
        if match["project"] in projects:
            targets_by_project[match["project"]].add(match["target"])
    for project, target_names in sorted(targets_by_project.items()):
        node = graph["nodes"].get(project, {})
        root = node.get("data", {}).get("root", "")
        candidates = [worktree / root / "project.json", worktree / root / "package.json"]
        config_path = next((path for path in candidates if path.exists()), None)
        if config_path is None:
            continue
        original = config_path.read_text()
        payload = json.loads(original)
        targets = project_config_targets(payload)
        if targets is None:
            continue
        changed = False
        for target in sorted(target_names):
            config = targets.get(target)
            if not isinstance(config, dict) or not isinstance(config.get("inputs"), list):
                continue
            kept = []
            removed = []
            for item in config["inputs"]:
                if is_direct_workspace_input(item):
                    removed.append(item)
                else:
                    kept.append(item)
            if removed:
                config["inputs"] = kept
                removals.append({"project": project, "target": target, "removed_input_items": removed})
                changed = True
        if changed:
            backups[config_path] = original
            config_path.write_text(json.dumps(payload, indent=2) + "\n")
    return backups, removals


def restore_configs(backups: dict[Path, str]) -> None:
    for path, content in backups.items():
        path.write_text(content)


def clear_project_graph_cache(worktree: Path) -> None:
    shutil.rmtree(worktree / ".nx" / "workspace-data", ignore_errors=True)


def workspace_input_counterfactual(
    worktree: Path,
    graph: dict[str, Any],
    nx_json: dict[str, Any],
    matches: list[dict[str, Any]],
    projects: set[str],
    target: str,
    files: list[str],
    baseline_projects: list[str],
) -> dict[str, Any]:
    backups: dict[Path, str] = {}
    try:
        backups, removals = remove_workspace_inputs(worktree, graph, nx_json, matches, projects)
        if not removals:
            return {
                "status": "not-runnable",
                "reason": "No matching project-local target inputs could be removed; the input may come from nx.json targetDefaults.",
                "requested_projects": sorted(projects),
                "removals": [],
            }
        clear_project_graph_cache(worktree)
        selected = nx_projects(worktree, target, files=files)
        return {
            "status": "measured",
            "evidence_class": "configuration-counterfactual",
            "requested_projects": sorted(projects),
            "removals": removals,
            "selected_count": len(selected),
            "selected_projects": selected,
            "projects_removed_from_baseline": sorted(set(baseline_projects) - set(selected)),
            "projects_added_to_baseline": sorted(set(selected) - set(baseline_projects)),
        }
    finally:
        restore_configs(backups)
        clear_project_graph_cache(worktree)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--target", default="test:unit")
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    repo = Path(git(args.repo.resolve(), "rev-parse", "--show-toplevel"))
    base = git(repo, "rev-parse", f"{args.base}^{{commit}}")
    head = git(repo, "rev-parse", f"{args.head}^{{commit}}")
    merge_base = git(repo, "merge-base", base, head)
    installed_manifest = json.loads((repo / "node_modules/nx/package.json").read_text())
    installed_nx = installed_manifest["version"]
    key_source = json.dumps([SCHEMA_VERSION, str(repo), base, head, args.target, installed_nx])
    cache_key = hashlib.sha256(key_source.encode()).hexdigest()[:20]
    cache_path = args.cache_dir / f"{cache_key}.json"
    if cache_path.exists() and not args.no_cache:
        payload = json.loads(cache_path.read_text())
        payload["cache_hit"] = True
        rendered = json.dumps(payload, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered)
        else:
            print(rendered, end="")
        return

    worktree_parent = Path(tempfile.mkdtemp(prefix="nx-affected-history-"))
    worktree = worktree_parent / "tree"
    added = False
    try:
        git(repo, "worktree", "add", "--detach", str(worktree), head)
        added = True
        (worktree / "node_modules").symlink_to(repo / "node_modules", target_is_directory=True)
        historical_package = json.loads((worktree / "package.json").read_text())
        expected_nx = historical_package.get("devDependencies", {}).get("nx") or historical_package.get("dependencies", {}).get("nx")
        version_match = expected_nx == installed_nx
        if not version_match:
            raise RuntimeError(f"historical manifest expects nx {expected_nx}, but shared node_modules has {installed_nx}")

        changed_files = [line for line in git(repo, "diff", "--name-only", "--no-renames", f"{merge_base}...{head}").splitlines() if line]
        graph_path = worktree_parent / "graph.json"
        run(
            [str(worktree / "node_modules/.bin/nx"), "graph", f"--file={graph_path}", "--open=false", "--watch=false"],
            worktree,
            nx_environment(),
        )
        graph = json.loads(graph_path.read_text())["graph"]
        nx_json = json.loads((worktree / "nx.json").read_text())
        policy = lockfile_policy(nx_json)

        groups = {
            "full": None,
            "without_lockfiles": [file for file in changed_files if Path(file).name not in LOCKFILES],
            "lockfiles_only": [file for file in changed_files if Path(file).name in LOCKFILES],
            "typescript_only": [file for file in changed_files if Path(file).suffix in {".ts", ".tsx", ".mts", ".cts"}],
            "graphql_only": [file for file in changed_files if Path(file).suffix in {".gql", ".graphql", ".graphqls"}],
            "manifests_only": [file for file in changed_files if Path(file).name in {"package.json", "project.json"}],
        }
        scenarios = {}
        for name, files in groups.items():
            scenario_files = changed_files if files is None else files
            projects = nx_projects(worktree, args.target, base=merge_base, head=head, files=files)
            scenario_owners = owned_projects(graph, scenario_files)
            scenario_matches = implicit_workspace_matches(graph, nx_json, scenario_files)
            scenarios[name] = {
                "files": scenario_files,
                "count": len(projects),
                "projects": projects,
                "selection_explanations": explain_selection(
                    projects,
                    args.target,
                    graph,
                    scenario_files,
                    scenario_owners,
                    scenario_matches,
                    policy,
                ),
            }

        counterfactual_files = groups["without_lockfiles"]
        counterfactual_matches = implicit_workspace_matches(graph, nx_json, counterfactual_files)
        matched_projects = sorted({match["project"] for match in counterfactual_matches})
        baseline_projects = scenarios["without_lockfiles"]["projects"]
        per_project_counterfactuals = {
            project: workspace_input_counterfactual(
                worktree,
                graph,
                nx_json,
                counterfactual_matches,
                {project},
                args.target,
                counterfactual_files,
                baseline_projects,
            )
            for project in matched_projects
        }
        all_counterfactual = workspace_input_counterfactual(
            worktree,
            graph,
            nx_json,
            counterfactual_matches,
            set(matched_projects),
            args.target,
            counterfactual_files,
            baseline_projects,
        )

        target_projects = sorted(
            name for name, node in graph["nodes"].items()
            if args.target in node.get("data", {}).get("targets", {})
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "evidence_class": "historical-replay",
            "cache_hit": False,
            "cache_key": cache_key,
            "repository": str(repo),
            "base": base,
            "head": head,
            "merge_base": merge_base,
            "target": args.target,
            "installed_nx_version": installed_nx,
            "historical_nx_specifier": expected_nx,
            "runtime_version_match": version_match,
            "runtime_note": "Historical tree with shared matching-version node_modules; no dependency installation performed.",
            "changed_file_count": len(changed_files),
            "changed_files": changed_files,
            "owned_projects_by_file": owned_projects(graph, changed_files),
            "graph_project_count": len(graph["nodes"]),
            "target_project_count": len(target_projects),
            "lockfile_policy": policy,
            "implicit_workspace_matches": implicit_workspace_matches(graph, nx_json, changed_files),
            "workspace_input_counterfactuals": {
                "baseline_scenario": "without_lockfiles",
                "interpretation": "Measured selection after temporarily removing matched workspace-root inputs from project-local target configuration. This is a configuration counterfactual, not observed CI history.",
                "per_project": per_project_counterfactuals,
                "all_matched_projects": all_counterfactual,
            },
            "scenarios": scenarios,
            "provenance": {
                "repository": str(repo),
                "base_commit": base,
                "head_commit": head,
                "merge_base_commit": merge_base,
                "graph_commit": head,
                "nx_version": installed_nx,
                "dependency_state": "shared matching-version node_modules; no historical install",
            },
        }
        args.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, indent=2) + "\n")
        rendered = json.dumps(payload, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered)
        else:
            print(rendered, end="")
    finally:
        if added:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo, capture_output=True)
        shutil.rmtree(worktree_parent, ignore_errors=True)


if __name__ == "__main__":
    main()
