#!/usr/bin/env python3
"""Join an Nx graph to task costs and rank node exposure and marginal edge impact."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import deque
from pathlib import Path
from typing import Any


def load_costs(path: Path, field: str) -> tuple[dict[str, float], str, dict[str, Any]]:
    payload = json.loads(path.read_text())
    rows = payload if isinstance(payload, list) else payload.get("projects", [])
    label = payload.get("metadata", {}).get("evidence_label", path.name) if isinstance(payload, dict) else path.name
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    costs: dict[str, float] = {}
    for row in rows:
        value = row.get(field)
        if value is None and field == "p90_total_seconds":
            value = row.get("total_seconds")
        if isinstance(row.get("project"), str) and isinstance(value, (int, float)) and value >= 0:
            costs[row["project"]] = float(value)
    return costs, label, metadata


def reverse_adjacency(projects: list[str], edges: list[tuple[str, str]], omitted: tuple[str, str] | None = None):
    reverse = {project: [] for project in projects}
    for edge in edges:
        if edge == omitted:
            continue
        source, target = edge
        reverse.setdefault(target, []).append(source)
    return reverse


def closure(start: str, reverse: dict[str, list[str]]) -> set[str]:
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for dependent in reverse.get(current, []):
            if dependent not in seen:
                seen.add(dependent)
                queue.append(dependent)
    return seen


def shortest_path(start: str, end: str, reverse: dict[str, list[str]]) -> list[str] | None:
    if start == end:
        return [start]
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        current, path = queue.popleft()
        for dependent in sorted(reverse.get(current, [])):
            if dependent in seen:
                continue
            candidate = [*path, dependent]
            if dependent == end:
                return candidate
            seen.add(dependent)
            queue.append((dependent, candidate))
    return None


def impact(start: str, reverse: dict[str, list[str]], targets: set[str], costs: dict[str, float]):
    affected = closure(start, reverse) & targets
    measured = affected & costs.keys()
    return affected, round(sum(costs[name] for name in measured), 3)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def chart_specs(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    target_count: int,
    evidence: str,
    baseline: dict[str, tuple[set[str], float]],
    costs: dict[str, float],
    analysis_class: str,
):
    top_nodes = nodes[:20]
    node_values = [
        {
            "Project": row["project"],
            "Exposed task minutes": round(row["exposed_work_seconds"] / 60, 2),
            "Affected unit projects": row["affected_target_count"],
            "Coverage": row["cost_coverage"],
        }
        for row in top_nodes
    ]
    top_node = node_values[0] if node_values else {"Project": "No project", "Exposed task minutes": 0}
    all_measured_minutes = sum(costs.values()) / 60
    top_share = round(100 * top_node["Exposed task minutes"] / all_measured_minutes) if all_measured_minutes else 0
    node_spec = {
        "data": {"values": node_values},
        "semantic_types": {
            "Project": "Name",
            "Exposed task minutes": {"semanticType": "Duration", "unit": "minutes"},
            "Affected unit projects": {"semanticType": "Count", "intrinsicDomain": [0, target_count]},
            "Coverage": {"semanticType": "Percentage", "intrinsicDomain": [0, 1]},
        },
        "chart_spec": {
            "chartType": "Bar Chart",
            "title": f"Modeled: {top_node['Project']} exposes {top_share}% of measured unit-test work",
            "subtitle": f"{analysis_class}; graph reachability joined to project timings ({evidence}); additive task work, not CI latency",
            "encodings": {
                "y": {"field": "Project", "sortBy": "x", "sortOrder": "descending"},
                "x": {"field": "Exposed task minutes"},
                "color": {"field": "Affected unit projects"},
            },
            "chartProperties": {"showValueLabels": True},
            "baseSize": {"width": 1100, "height": 900},
            "canvasSize": {"width": 1320, "height": 1100},
        },
        "theme_spec": "mckinsey",
    }

    top_edges = [row for row in edges if row["aggregate_work_saved_seconds"] > 0][:20]
    edge_values = [
        {
            "Dependency edge": f"{row['source']} → {row['target']}",
            "Aggregate task minutes avoided": round(row["aggregate_work_saved_seconds"] / 60, 2),
            "Starting projects helped": row["changed_nodes_helped"],
        }
        for row in top_edges
    ]
    top_edge = edge_values[0] if edge_values else {"Dependency edge": "No single edge", "Aggregate task minutes avoided": 0}
    edge_spec = {
        "data": {"values": edge_values},
        "semantic_types": {
            "Dependency edge": "Name",
            "Aggregate task minutes avoided": {"semanticType": "Duration", "unit": "minutes"},
            "Starting projects helped": "Count",
        },
        "chart_spec": {
            "chartType": "Bar Chart",
            "title": f"Counterfactual: removing {top_edge['Dependency edge']} has the largest modeled impact",
            "subtitle": f"{analysis_class}; summed over one hypothetical change to every project; alternate graph paths remain; task work, not latency",
            "encodings": {
                "y": {"field": "Dependency edge", "sortBy": "x", "sortOrder": "descending"},
                "x": {"field": "Aggregate task minutes avoided"},
                "color": {"field": "Starting projects helped"},
            },
            "chartProperties": {"showValueLabels": True},
            "baseSize": {"width": 1100, "height": 900},
            "canvasSize": {"width": 1400, "height": 1120},
        },
        "theme_spec": "mckinsey",
    }
    heavyweight_projects = [name for name, _ in sorted(costs.items(), key=lambda item: -item[1])[:3]]
    composition_values = []
    for row in nodes[:12]:
        affected = baseline[row["project"]][0]
        other_seconds = 0.0
        for target in affected:
            seconds = costs.get(target, 0.0)
            if target in heavyweight_projects:
                composition_values.append({
                    "Project": row["project"],
                    "Cost source": target,
                    "Task minutes": round(seconds / 60, 3),
                })
            else:
                other_seconds += seconds
        composition_values.append({
            "Project": row["project"],
            "Cost source": "other projects",
            "Task minutes": round(other_seconds / 60, 3),
        })
    top_affected = baseline[nodes[0]["project"]][0] if nodes else set()
    heavy_seconds = sum(costs.get(name, 0.0) for name in heavyweight_projects if name in top_affected)
    top_seconds = nodes[0]["exposed_work_seconds"] if nodes else 0
    heavy_share = round(100 * heavy_seconds / top_seconds) if top_seconds else 0
    composition_spec = {
        "data": {"values": composition_values},
        "semantic_types": {
            "Project": {
                "semanticType": "Category",
                "sortOrder": [row["project"] for row in nodes[:12]],
            },
            "Cost source": {
                "semanticType": "Category",
                "sortOrder": [*heavyweight_projects, "other projects"],
            },
            "Task minutes": {"semanticType": "Duration", "unit": "minutes"},
        },
        "chart_spec": {
            "chartType": "Stacked Bar Chart",
            "title": f"Modeled: the three heaviest suites contribute {heavy_share}% of the broadest closure's work",
            "subtitle": f"{analysis_class}; measured timing composition for the 12 highest-cost reverse closures ({evidence}); task work, not CI latency",
            "encodings": {
                "y": {"field": "Project"},
                "x": {"field": "Task minutes"},
                "color": {"field": "Cost source"},
            },
            "chartProperties": {"stackMode": "stacked"},
            "baseSize": {"width": 1100, "height": 720},
            "canvasSize": {"width": 1400, "height": 930},
        },
        "theme_spec": "mckinsey",
    }
    return node_spec, edge_spec, composition_spec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--costs", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--cost-field", default="p90_total_seconds")
    parser.add_argument("--graph-commit", required=True, help="Full commit SHA from which the Nx graph was generated")
    parser.add_argument("--allow-provenance-mismatch", action="store_true", help="Produce an explicitly mixed-snapshot model instead of failing")
    parser.add_argument("--allow-unverified-provenance", action="store_true", help="Allow costs without a commit, labeled unverified")
    args = parser.parse_args()

    if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", args.graph_commit):
        parser.error("--graph-commit must be a full 40- or 64-character hexadecimal Git commit SHA")

    graph_payload = json.loads(args.graph.read_text())
    graph = graph_payload.get("graph", graph_payload)
    projects = sorted(graph["nodes"])
    targets = {
        name for name, node in graph["nodes"].items()
        if "test:unit" in node.get("data", {}).get("targets", {})
    }
    raw_edges = [edge for group in graph["dependencies"].values() for edge in group]
    edges = sorted({(edge["source"], edge["target"]) for edge in raw_edges})
    costs, evidence, cost_metadata = load_costs(args.costs, args.cost_field)
    cost_commit = cost_metadata.get("provenance", {}).get("commit")
    graph_commit = args.graph_commit.lower()
    if not cost_commit:
        if not args.allow_unverified_provenance:
            raise ValueError("cost profile has no metadata.provenance.commit; rerun the cost profiler or pass --allow-unverified-provenance")
        analysis_class = "unverified-counterfactual"
    elif cost_commit.lower() != graph_commit:
        if not args.allow_provenance_mismatch:
            raise ValueError(
                f"graph commit {graph_commit} does not match cost commit {cost_commit}; "
                "use matching inputs or pass --allow-provenance-mismatch"
            )
        analysis_class = "mixed-snapshot-counterfactual"
    else:
        analysis_class = "snapshot-aligned-counterfactual"
    reverse = reverse_adjacency(projects, edges)

    baseline: dict[str, tuple[set[str], float]] = {}
    nodes = []
    for project in projects:
        affected, work = impact(project, reverse, targets, costs)
        baseline[project] = (affected, work)
        measured_count = len(affected & costs.keys())
        nodes.append({
            "project": project,
            "affected_target_count": len(affected),
            "measured_target_count": measured_count,
            "cost_coverage": round(measured_count / len(affected), 4) if affected else 1.0,
            "exposed_work_seconds": work,
            "direct_dependents": len(reverse.get(project, [])),
        })
    nodes.sort(key=lambda row: (-row["exposed_work_seconds"], -row["affected_target_count"], row["project"]))

    edge_rows = []
    for source, target in edges:
        altered = reverse_adjacency(projects, edges, (source, target))
        aggregate_tests = 0
        aggregate_work = 0.0
        changed_nodes = 0
        maximum_work = 0.0
        for project in projects:
            affected_after, work_after = impact(project, altered, targets, costs)
            affected_before, work_before = baseline[project]
            tests_saved = len(affected_before) - len(affected_after)
            work_saved = max(0.0, work_before - work_after)
            if tests_saved or work_saved > 0.0005:
                changed_nodes += 1
            aggregate_tests += tests_saved
            aggregate_work += work_saved
            maximum_work = max(maximum_work, work_saved)
        edge_rows.append({
            "source": source,
            "target": target,
            "changed_nodes_helped": changed_nodes,
            "aggregate_test_tasks_saved": aggregate_tests,
            "aggregate_work_saved_seconds": round(aggregate_work, 3),
            "max_single_change_work_saved_seconds": round(maximum_work, 3),
        })
    edge_rows.sort(key=lambda row: (-row["aggregate_work_saved_seconds"], -row["aggregate_test_tasks_saved"], row["source"], row["target"]))

    measured_targets = targets & costs.keys()
    representative_paths = []
    for row in nodes[:10]:
        start = row["project"]
        expensive_targets = sorted(
            baseline[start][0] & costs.keys(),
            key=lambda project: (-costs[project], project),
        )[:5]
        for selected_target in expensive_targets:
            path = shortest_path(start, selected_target, reverse)
            representative_paths.append({
                "changed_project": start,
                "selected_test_project": selected_target,
                "test_cost_seconds": round(costs[selected_target], 3),
                "dependency_path": path,
                "path_hops": len(path or []) - 1,
                "edge_meaning": "Each arrow means the project on the right directly depends on the project on the left.",
            })
    summary = {
        "schema_version": 2,
        "analysis_class": analysis_class,
        "interpretation": "A deterministic graph-and-cost counterfactual. It estimates selected task work; it does not reproduce observed CI wall-clock latency.",
        "provenance": {
            "graph_commit": graph_commit,
            "cost_commit": cost_commit,
            "cost_evidence_kind": cost_metadata.get("evidence_kind"),
            "cost_provenance": cost_metadata.get("provenance"),
        },
        "graph_projects": len(projects),
        "raw_graph_edges": len(raw_edges),
        "unique_project_edges": len(edges),
        "parallel_edge_records": len(raw_edges) - len(edges),
        "unit_target_projects": len(targets),
        "measured_unit_projects": len(measured_targets),
        "missing_cost_projects": sorted(targets - costs.keys()),
        "cost_field": args.cost_field,
        "evidence_label": evidence,
        "zero_marginal_edges": sum(row["aggregate_work_saved_seconds"] == 0 for row in edge_rows),
        "top_nodes": nodes[:10],
        "top_edges": edge_rows[:10],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "flint-specs").mkdir(exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.out / "nodes.json").write_text(json.dumps(nodes, indent=2) + "\n")
    (args.out / "edges.json").write_text(json.dumps(edge_rows, indent=2) + "\n")
    (args.out / "representative-paths.json").write_text(json.dumps({
        "schema_version": 1,
        "analysis_class": analysis_class,
        "diagram_guidance": "Use selectively: show a small number of high-cost causal paths, label test cost at terminal nodes, and state that paths are shortest explanations rather than the full graph.",
        "paths": representative_paths,
    }, indent=2) + "\n")
    write_csv(args.out / "nodes.csv", nodes)
    write_csv(args.out / "edges.csv", edge_rows)
    node_spec, edge_spec, composition_spec = chart_specs(
        nodes, edge_rows, len(targets), evidence, baseline, costs, analysis_class
    )
    (args.out / "flint-specs" / "weighted-node-impact.json").write_text(json.dumps(node_spec, indent=2) + "\n")
    (args.out / "flint-specs" / "marginal-edge-impact.json").write_text(json.dumps(edge_spec, indent=2) + "\n")
    (args.out / "flint-specs" / "heavyweight-cost-composition.json").write_text(json.dumps(composition_spec, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
