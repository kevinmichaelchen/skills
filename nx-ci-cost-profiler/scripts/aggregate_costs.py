#!/usr/bin/env python3
"""Aggregate one or more per-project timing captures into a stable cost profile."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

COMPONENTS = (
    "total_seconds",
    "import_seconds",
    "tests_seconds",
    "setup_seconds",
    "transform_seconds",
    "environment_seconds",
)


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 3)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 3)


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return None


def load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    raise ValueError(f"{path} must contain a JSON array of unsummarized timing records")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--evidence-label", default="unspecified timing captures")
    parser.add_argument("--evidence-kind", required=True, choices=("observed-ci", "local-replay", "static-estimate"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True, help="Full source commit SHA used by every timing capture")
    parser.add_argument("--run-id", action="append", default=[], help="CI run ID or local capture ID; repeat as needed")
    parser.add_argument("--runner", required=True, help="Runner class or machine description")
    parser.add_argument("--cache-state", required=True, choices=("cold", "warm", "mixed", "unknown"))
    args = parser.parse_args()

    if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", args.commit):
        parser.error("--commit must be a full 40- or 64-character hexadecimal Git commit SHA")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rejected: list[dict[str, Any]] = []
    input_count = 0
    for path in args.input:
        for row in load_records(path):
            input_count += 1
            project = row.get("project")
            total = numeric(row.get("total_seconds"))
            if not isinstance(project, str) or not project.strip() or total is None:
                rejected.append({"source": str(path), "project": project, "reason": "missing project or total_seconds"})
                continue
            grouped[project].append(row)

    projects = []
    for project, rows in sorted(grouped.items()):
        result: dict[str, Any] = {"project": project, "samples": len(rows)}
        for field in COMPONENTS:
            values = [value for row in rows if (value := numeric(row.get(field))) is not None]
            stem = field.removesuffix("_seconds")
            result[f"{stem}_samples"] = len(values)
            result[f"p50_{field}"] = percentile(values, 0.5)
            result[f"p90_{field}"] = percentile(values, 0.9)
            result[f"max_{field}"] = round(max(values), 3) if values else None
        projects.append(result)

    output = {
        "metadata": {
            "schema_version": 2,
            "evidence_label": args.evidence_label,
            "evidence_kind": args.evidence_kind,
            "provenance": {
                "repository": args.repository,
                "commit": args.commit.lower(),
                "run_ids": args.run_id,
                "runner": args.runner,
                "cache_state": args.cache_state,
            },
            "sources": [str(path) for path in args.input],
            "input_records": input_count,
            "accepted_records": sum(len(rows) for rows in grouped.values()),
            "project_count": len(projects),
        },
        "projects": projects,
        "missing": rejected,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["metadata"], indent=2))


if __name__ == "__main__":
    main()
