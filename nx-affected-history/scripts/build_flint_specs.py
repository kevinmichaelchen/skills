#!/usr/bin/env python3
"""Build Flint chart inputs from cached Nx affected-history results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", action="append", required=True, help="LABEL=path/to/result.json")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    results = []
    for value in args.result:
        label, separator, filename = value.partition("=")
        if not separator or not label or not filename:
            raise ValueError("--result must be LABEL=path")
        results.append((label, json.loads(Path(filename).read_text())))

    comparison_rows = []
    for label, payload in results:
        comparison_rows.extend([
            {
                "Pull request": label,
                "Scenario": "Actual PR",
                "Affected unit projects": payload["scenarios"]["full"]["count"],
            },
            {
                "Pull request": label,
                "Scenario": "No lockfile",
                "Affected unit projects": payload["scenarios"]["without_lockfiles"]["count"],
            },
        ])
    full_counts = [payload["scenarios"]["full"]["count"] for _, payload in results]
    target_counts = [payload["target_project_count"] for _, payload in results]
    all_full = full_counts == target_counts
    comparison_title = (
        "Every recent payment/order PR selected every unit-test project"
        if all_full
        else "Lockfiles materially widened the recent payment/order PR test sets"
    )
    comparison = {
        "data": {"values": comparison_rows},
        "semantic_types": {
            "Pull request": "Name",
            "Scenario": {"semanticType": "Category", "sortOrder": ["Actual PR", "No lockfile"]},
            "Affected unit projects": {"semanticType": "Count", "intrinsicDomain": [0, max(target_counts)]},
        },
        "chart_spec": {
            "chartType": "Grouped Bar Chart",
            "title": comparison_title,
            "subtitle": "Detached-worktree Nx replays at each PR's exact base/head; actual selection versus the same changed files with lockfiles removed",
            "encodings": {
                "y": {"field": "Pull request"},
                "x": {"field": "Affected unit projects"},
                "group": {"field": "Scenario"},
            },
            "chartProperties": {"showValueLabels": True},
            "baseSize": {"width": 950, "height": 520},
            "canvasSize": {"width": 1250, "height": 760},
        },
        "theme_spec": "mckinsey",
    }

    latest_label, latest = results[-1]
    scenario_labels = [
        ("Lockfile", "lockfiles_only"),
        ("GraphQL", "graphql_only"),
        ("TypeScript", "typescript_only"),
        ("Manifest", "manifests_only"),
    ]
    trigger_rows = [
        {"Trigger": label, "Affected unit projects": latest["scenarios"][key]["count"]}
        for label, key in scenario_labels
    ]
    trigger = {
        "data": {"values": trigger_rows},
        "semantic_types": {
            "Trigger": {"semanticType": "Category", "sortOrder": [label for label, _ in scenario_labels]},
            "Affected unit projects": {"semanticType": "Count", "intrinsicDomain": [0, latest["target_project_count"]]},
        },
        "chart_spec": {
            "chartType": "Bar Chart",
            "title": f"A lockfile change alone selects all {latest['target_project_count']} unit-test projects",
            "subtitle": f"Independent changed-file-class counterfactuals for {latest_label}; GraphQL and TypeScript inputs widen the set before dependency traversal",
            "encodings": {
                "y": {"field": "Trigger"},
                "x": {"field": "Affected unit projects"},
            },
            "chartProperties": {"showValueLabels": True},
            "baseSize": {"width": 900, "height": 430},
            "canvasSize": {"width": 1150, "height": 620},
        },
        "theme_spec": "mckinsey",
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pr-lockfile-counterfactual.json").write_text(json.dumps(comparison, indent=2) + "\n")
    (args.out / "affected-trigger-layers.json").write_text(json.dumps(trigger, indent=2) + "\n")
    print(json.dumps({"results": len(results), "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
