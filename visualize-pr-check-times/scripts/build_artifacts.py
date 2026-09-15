#!/usr/bin/env python3
"""Build normalized timing data and Flint specs entirely from cached evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ANSI = re.compile(r"(?:\x1b\[[0-9;?]*[ -/]*[@-~]|\^\[\[[0-9;?]*[ -/]*[@-~])")
LOG_TIMESTAMP = re.compile(r"\t(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\s")
NX_UNIT = re.compile(r'nx run\s+([^:\s]+):"?test:unit"?')
VITEST_DURATION = re.compile(
    r"Duration\s+(\d+(?:\.\d+)?(?:ms|s|m))\s+"
    r"\(transform\s+(\d+(?:\.\d+)?(?:ms|s|m)),\s+"
    r"setup\s+(\d+(?:\.\d+)?(?:ms|s|m)),\s+"
    r"import\s+(\d+(?:\.\d+)?(?:ms|s|m)),\s+"
    r"tests\s+(\d+(?:\.\d+)?(?:ms|s|m)),\s+"
    r"environment\s+(\d+(?:\.\d+)?(?:ms|s|m))\)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path, help="evidence bundle containing raw/")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    if not path.exists():
        sys.exit(f"missing cached evidence: {path}")
    return json.loads(path.read_text())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    return (iso(end) - iso(start)).total_seconds()


def value_seconds(value: str) -> float:
    if value.endswith("ms"):
        return float(value[:-2]) / 1000
    if value.endswith("s"):
        return float(value[:-1])
    if value.endswith("m"):
        return float(value[:-1]) * 60
    raise ValueError(f"unsupported duration: {value}")


def phase(name: str) -> str:
    if "Prepare" in name:
        return "Prepare"
    if "Merge Gate" in name or name == "deploy":
        return "Gate"
    if name.startswith("annotate /"):
        return "Annotation"
    return "Parallel checks"


def short_name(name: str) -> str:
    shortened = name.removeprefix("checks / ").removeprefix("annotate / ")
    shortened = re.sub(r"^[^\w]+", "", shortened).strip()
    return re.sub(r"^Seed validation \(([^)]+)\)$", r"Seed validation — \1", shortened)


def parse_unit_projects(log_path: Path, unit_step_start: str | None) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    projects: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in log_path.read_text(errors="replace").splitlines():
        line = ANSI.sub("", raw_line)
        nx_match = NX_UNIT.search(line) if "##[group]" in line else None
        if nx_match:
            timestamp = LOG_TIMESTAMP.search(line)
            current = {
                "project": nx_match.group(1),
                "completed_at": timestamp.group(1) if timestamp else None,
                "test_files": None,
                "tests_passed": None,
                "tests_skipped": 0,
                "vitest_start_time": None,
            }
            continue
        if current is None:
            continue
        files_match = re.search(r"Test Files\s+(\d+) passed", line)
        if files_match:
            current["test_files"] = int(files_match.group(1))
        tests_match = re.search(r"Tests\s+(\d+) passed(?:\s+\|\s+(\d+) skipped)?", line)
        if tests_match:
            current["tests_passed"] = int(tests_match.group(1))
            current["tests_skipped"] = int(tests_match.group(2) or 0)
        start_match = re.search(r"Start at\s+(\d{2}:\d{2}:\d{2})", line)
        if start_match:
            current["vitest_start_time"] = start_match.group(1)
        duration_match = VITEST_DURATION.search(line)
        if not duration_match:
            continue
        names = ["total", "transform", "setup", "import", "tests", "environment"]
        for name, value in zip(names, duration_match.groups()):
            current[f"{name}_seconds"] = round(value_seconds(value), 3)
        component_sum = sum(current[f"{name}_seconds"] for name in names[1:])
        current["component_sum_seconds"] = round(component_sum, 3)
        current["components_overlap_wall_clock"] = component_sum > current["total_seconds"]
        if current["completed_at"] and current["vitest_start_time"]:
            day = current["completed_at"][:10]
            current["vitest_started_at"] = f"{day}T{current['vitest_start_time']}Z"
            if unit_step_start:
                current["start_offset_seconds"] = seconds(unit_step_start, current["vitest_started_at"])
        else:
            current["vitest_started_at"] = None
            current["start_offset_seconds"] = None
        projects.append(current)
        current = None
    projects.sort(key=lambda row: row["total_seconds"], reverse=True)
    return projects


def chart_specs(
    jobs: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    unit_projects: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    job_rows = [
        {"Job": row["job"], "Minutes": row["duration_minutes"]}
        for row in jobs if row["phase"] != "Annotation"
    ]
    timeline_rows = [
        {"Job": row["job"], "Start": row["started_at"], "Finish": row["completed_at"], "Phase": row["phase"]}
        for row in jobs
    ]
    top_steps = steps[:15]
    step_rows = [
        {"Step": f"{row['step']} — {row['job']}", "Minutes": row["duration_minutes"]}
        for row in top_steps
    ]
    slow_job = summary["critical_job"]
    slow_step = top_steps[0]
    duration = summary["workflow_duration_seconds"]
    has_prepare_phase = any(row["phase"] == "Prepare" for row in jobs)
    timeline_title = (
        f"Prepare fans out; the slowest job is {slow_job}"
        if has_prepare_phase
        else f"The slowest job is {slow_job}"
    )
    common = {"theme_spec": "economist", "options": {"addTooltips": True}}
    specs = {
        "job-durations": {
            **common,
            "data": {"values": job_rows},
            "semantic_types": {"Job": "Category", "Minutes": {"semanticType": "Duration", "unit": "minutes"}},
            "chart_spec": {
                "chartType": "Bar Table",
                "title": f"{slow_job} take {summary['critical_job_duration_seconds'] / 60:.1f} of {duration / 60:.1f} minutes",
                "subtitle": f"Non-skipped jobs in {summary['workflow']} run {summary['run_id']}; bars are each job's wall-clock duration",
                "encodings": {"y": {"field": "Job", "sortBy": "x", "sortOrder": "descending"}, "x": {"field": "Minutes"}},
                "baseSize": {"width": 1200, "height": 760},
                "canvasSize": {"width": 1500, "height": 1000},
            },
        },
        "job-timeline": {
            **common,
            "data": {"values": timeline_rows},
            "semantic_types": {"Job": "Category", "Start": "DateTime", "Finish": "DateTime", "Phase": "Category"},
            "chart_spec": {
                "chartType": "Gantt Chart",
                "title": timeline_title,
                "subtitle": f"Actual job start and finish times for {summary['workflow']} run {summary['run_id']} (UTC)",
                "encodings": {"y": {"field": "Job"}, "x": {"field": "Start"}, "x2": {"field": "Finish"}, "color": {"field": "Phase"}},
                "baseSize": {"width": 1300, "height": 850},
                "canvasSize": {"width": 1600, "height": 1100},
            },
        },
        "slowest-steps": {
            **common,
            "data": {"values": step_rows},
            "semantic_types": {"Step": "Category", "Minutes": {"semanticType": "Duration", "unit": "minutes"}},
            "chart_spec": {
                "chartType": "Bar Table",
                "title": f"{slow_step['step']} alone burns {slow_step['duration_seconds'] / 60:.1f} minutes",
                "subtitle": f"The 15 longest individual steps in {summary['workflow']} run {summary['run_id']}",
                "encodings": {"y": {"field": "Step", "sortBy": "x", "sortOrder": "descending"}, "x": {"field": "Minutes"}},
                "baseSize": {"width": 1300, "height": 800},
                "canvasSize": {"width": 1650, "height": 1050},
            },
        },
    }
    if unit_projects:
        top_projects = unit_projects[:10]
        metric_names = [
            ("Total wall", "total_seconds"),
            ("Import", "import_seconds"),
            ("Tests", "tests_seconds"),
            ("Transform", "transform_seconds"),
        ]
        unit_rows = [
            {"Project": row["project"], "Metric": label, "Minutes": round(row[field] / 60, 3)}
            for row in top_projects
            for label, field in metric_names
        ]
        longest = top_projects[0]
        specs["unit-project-breakdown"] = {
            **common,
            "data": {"values": unit_rows},
            "semantic_types": {
                "Project": "Category",
                "Metric": "Category",
                "Minutes": {"semanticType": "Duration", "unit": "minutes"},
            },
            "chart_spec": {
                "chartType": "Grouped Bar Chart",
                "title": f"The {longest['project']} project spends {longest['import_seconds'] / 60:.1f} minutes importing code",
                "subtitle": "Top 10 exact per-project Vitest wall times and components; Nx projects overlap in parallel and component timers can overlap",
                "encodings": {
                    "x": {"field": "Project", "sortBy": "y", "sortOrder": "descending"},
                    "y": {"field": "Minutes"},
                    "group": {"field": "Metric"},
                },
                "baseSize": {"width": 1500, "height": 800},
                "canvasSize": {"width": 1800, "height": 1000},
                "chartProperties": {"dodge": "global"},
            },
        }
        scheduled_projects = sorted(
            (row for row in unit_projects if row.get("vitest_started_at") and row.get("completed_at")),
            key=lambda row: row["vitest_started_at"],
        )
        schedule_rows = [
            {
                "Project": row["project"],
                "Start": row["vitest_started_at"],
                "Finish": row["completed_at"],
                "Profile": "Import > tests" if row["import_seconds"] > row["tests_seconds"] else "Tests ≥ import",
            }
            for row in scheduled_projects
        ]
        specs["unit-project-timeline"] = {
            **common,
            "data": {"values": schedule_rows},
            "semantic_types": {
                "Project": "Category",
                "Start": "DateTime",
                "Finish": "DateTime",
                "Profile": "Category",
            },
            "chart_spec": {
                "chartType": "Gantt Chart",
                "title": f"{longest['project']} runs for {longest['total_seconds'] / 60:.1f} minutes and reaches the tail",
                "subtitle": "Exact Vitest project start and completion times (UTC); projects overlap, and color only compares import with test execution",
                "encodings": {
                    "y": {"field": "Project"},
                    "x": {"field": "Start"},
                    "x2": {"field": "Finish"},
                    "color": {"field": "Profile"},
                },
                "baseSize": {"width": 1400, "height": 1200},
                "canvasSize": {"width": 1700, "height": 1500},
            },
        }
        scatter_projects = top_projects[:10]
        scatter_rows = [
            {
                "Project": row["project"],
                "Import minutes": round(row["import_seconds"] / 60, 3),
                "Test minutes": round(row["tests_seconds"] / 60, 3),
                "Wall minutes": round(row["total_seconds"] / 60, 3),
            }
            for row in scatter_projects
        ]
        import_ratio = longest["import_seconds"] / longest["tests_seconds"]
        specs["unit-import-vs-tests"] = {
            **common,
            "data": {"values": scatter_rows},
            "semantic_types": {
                "Project": "Category",
                "Import minutes": {"semanticType": "Duration", "unit": "minutes"},
                "Test minutes": {"semanticType": "Duration", "unit": "minutes"},
                "Wall minutes": {"semanticType": "Duration", "unit": "minutes"},
            },
            "chart_spec": {
                "chartType": "Scatter Plot",
                "title": f"For {longest['project']}, importing takes {import_ratio:.1f}× longer than tests",
                "subtitle": "Top 10 projects by exact Vitest wall time; bubble area is project wall time and colors identify projects",
                "encodings": {
                    "x": {"field": "Test minutes"},
                    "y": {"field": "Import minutes"},
                    "size": {"field": "Wall minutes"},
                    "color": {"field": "Project"},
                },
                "baseSize": {"width": 1200, "height": 800},
                "canvasSize": {"width": 1500, "height": 1000},
            },
        }
    return specs


def main() -> int:
    args = parse_args()
    root = args.bundle
    raw = root / "raw"
    derived = root / "derived"
    specs_dir = root / "flint-specs"
    selection = read_json(raw / "selection.json")
    pr = read_json(raw / "pr.json")
    run = read_json(raw / selection["run_file"])
    if selection["head_sha"] != pr["headRefOid"] or run["headSha"] != selection["head_sha"]:
        sys.exit("cached selection, PR head, and run head SHA do not match")

    run_start = iso(run["startedAt"])
    jobs: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    for job in run["jobs"]:
        job_duration = seconds(job.get("startedAt"), job.get("completedAt"))
        if job["conclusion"] == "skipped" or job_duration is None:
            continue
        job_name = short_name(job["name"])
        jobs.append({
            "job": job_name,
            "full_job_name": job["name"],
            "phase": phase(job["name"]),
            "conclusion": job["conclusion"],
            "started_at": job["startedAt"],
            "completed_at": job["completedAt"],
            "relative_start_seconds": (iso(job["startedAt"]) - run_start).total_seconds(),
            "relative_end_seconds": (iso(job["completedAt"]) - run_start).total_seconds(),
            "duration_seconds": job_duration,
            "duration_minutes": round(job_duration / 60, 3),
            "job_id": job["databaseId"],
            "url": job.get("url", ""),
        })
        for step in job.get("steps", []):
            step_duration = seconds(step.get("startedAt"), step.get("completedAt"))
            if step_duration is None or step_duration <= 0:
                continue
            steps.append({
                "job": job_name,
                "step": step["name"],
                "step_label": f"{step['name']} — {job_name}",
                "conclusion": step["conclusion"],
                "started_at": step["startedAt"],
                "completed_at": step["completedAt"],
                "duration_seconds": step_duration,
                "duration_minutes": round(step_duration / 60, 3),
                "job_id": job["databaseId"],
            })
    jobs.sort(key=lambda row: row["duration_seconds"], reverse=True)
    steps.sort(key=lambda row: row["duration_seconds"], reverse=True)

    unit_job = next((row for row in jobs if row["job"] == "Unit tests"), None)
    unit_step = next((row for row in steps if row["job"] == "Unit tests" and row["step"] == "Run unit tests"), None)
    unit_log = raw / "logs" / f"job-{unit_job['job_id']}.log" if unit_job else Path("/nonexistent")
    unit_projects = parse_unit_projects(unit_log, unit_step["started_at"] if unit_step else None)

    checks: list[dict[str, Any]] = []
    for check in pr.get("statusCheckRollup", []):
        check_duration = seconds(check.get("startedAt"), check.get("completedAt"))
        if check.get("__typename") != "CheckRun" or check.get("conclusion") == "SKIPPED" or check_duration is None:
            continue
        checks.append({
            "workflow": check.get("workflowName") or "External checks",
            "check": check["name"],
            "conclusion": check["conclusion"],
            "started_at": check["startedAt"],
            "completed_at": check["completedAt"],
            "duration_seconds": check_duration,
            "duration_minutes": round(check_duration / 60, 3),
            "url": check.get("detailsUrl", ""),
        })
    checks.sort(key=lambda row: row["duration_seconds"], reverse=True)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for check in checks:
        if check["workflow"] != "External checks":
            grouped.setdefault(check["workflow"], []).append(check)
    workflow_spans = []
    for workflow, workflow_checks in grouped.items():
        start = min(row["started_at"] for row in workflow_checks)
        end = max(row["completed_at"] for row in workflow_checks)
        span = seconds(start, end)
        workflow_spans.append({
            "workflow": workflow,
            "started_at": start,
            "completed_at": end,
            "duration_seconds": span,
            "duration_minutes": round(span / 60, 3),
            "check_count": len(workflow_checks),
        })
    workflow_spans.sort(key=lambda row: row["duration_seconds"], reverse=True)

    critical = jobs[0]
    workflow_duration = seconds(run["startedAt"], run["updatedAt"])
    summary = {
        "repo": selection["repo"],
        "pr": selection["pr"],
        "pr_url": pr["url"],
        "pr_title": pr["title"],
        "head_sha": selection["head_sha"],
        "workflow": run["workflowName"],
        "run_id": selection["run_id"],
        "run_url": run["url"],
        "run_conclusion": run["conclusion"],
        "run_started_at": run["startedAt"],
        "run_updated_at": run["updatedAt"],
        "workflow_duration_seconds": workflow_duration,
        "critical_job": critical["job"],
        "critical_job_duration_seconds": critical["duration_seconds"],
        "critical_job_share_of_workflow": round(critical["duration_seconds"] / workflow_duration, 4),
        "slowest_step": steps[0]["step"],
        "slowest_step_job": steps[0]["job"],
        "slowest_step_duration_seconds": steps[0]["duration_seconds"],
        "slowest_step_share_of_critical_job": round(steps[0]["duration_seconds"] / critical["duration_seconds"], 4),
        "job_count": len(jobs),
        "step_count": len(steps),
        "top_jobs": [{"job": row["job"], "duration_seconds": row["duration_seconds"]} for row in jobs[:5]],
        "top_steps": [
            {"job": row["job"], "step": row["step"], "duration_seconds": row["duration_seconds"]}
            for row in steps[:5]
        ],
        "workflow_spans": workflow_spans,
    }
    if unit_projects:
        longest = unit_projects[0]
        summary["unit_test_analysis"] = {
            "source_log": str(unit_log.relative_to(root)),
            "project_count": len(unit_projects),
            "longest_project": longest["project"],
            "longest_project_total_seconds": longest["total_seconds"],
            "longest_project_start_offset_seconds": longest.get("start_offset_seconds"),
            "longest_project_started_at": longest.get("vitest_started_at"),
            "longest_project_completed_at": longest.get("completed_at"),
            "longest_project_test_files": longest.get("test_files"),
            "longest_project_tests_passed": longest.get("tests_passed"),
            "longest_project_tests_skipped": longest.get("tests_skipped"),
            "longest_project_import_seconds": longest["import_seconds"],
            "longest_project_test_execution_seconds": longest["tests_seconds"],
            "longest_project_import_share_of_wall": round(longest["import_seconds"] / longest["total_seconds"], 4),
            "longest_project_test_share_of_wall": round(longest["tests_seconds"] / longest["total_seconds"], 4),
            "timing_caveat": "Nx projects overlap in parallel; Vitest component timers can overlap and must not be summed as suite wall time.",
        }

    write_json(derived / "summary.json", summary)
    for name, rows in {
        "jobs": jobs,
        "steps": steps,
        "checks": checks,
        "workflow-spans": workflow_spans,
        "unit-projects": unit_projects,
    }.items():
        write_json(derived / f"{name}.json", rows)
        write_csv(derived / f"{name}.csv", rows)
    specs = chart_specs(jobs, steps, unit_projects, summary)
    specs_dir.mkdir(parents=True, exist_ok=True)
    for existing in specs_dir.glob("*.json"):
        if existing.stem not in specs:
            existing.unlink()
    for name, spec in specs.items():
        write_json(specs_dir / f"{name}.json", spec)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
