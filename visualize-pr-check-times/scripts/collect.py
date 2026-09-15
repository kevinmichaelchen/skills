#!/usr/bin/env python3
"""Fetch and cache raw GitHub evidence for a pull request's current-head run."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PR_FIELDS = (
    "number,title,url,state,headRefName,headRefOid,baseRefName,createdAt,updatedAt,"
    "mergeable,reviewDecision,statusCheckRollup,commits"
)
RUN_LIST_FIELDS = (
    "databaseId,workflowName,name,event,status,conclusion,createdAt,startedAt,"
    "updatedAt,headSha,url,displayTitle"
)
RUN_FIELDS = (
    "attempt,conclusion,createdAt,databaseId,displayTitle,event,headBranch,headSha,"
    "jobs,name,number,startedAt,status,updatedAt,url,workflowDatabaseId,workflowName"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="GitHub OWNER/REPO")
    parser.add_argument("--pr", required=True, type=int, help="pull request number")
    parser.add_argument("--workflow", default="PR", help="workflow name to profile")
    parser.add_argument("--out", type=Path, help="evidence bundle root")
    parser.add_argument("--include-logs", action="store_true", help="cache logs for jobs over 60 seconds")
    parser.add_argument("--refresh", action="store_true", help="replace immutable cached run data and logs")
    return parser.parse_args()


def gh_json(args: list[str]) -> Any:
    proc = subprocess.run(["gh", *args], check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    return (iso(end) - iso(start)).total_seconds()


def main() -> int:
    args = parse_args()
    root = args.out or Path(f".context/pr-{args.pr}-check-times")
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    pr = gh_json(["pr", "view", str(args.pr), "--repo", args.repo, "--json", PR_FIELDS])
    runs = gh_json([
        "run", "list", "--repo", args.repo, "--branch", pr["headRefName"],
        "--limit", "100", "--json", RUN_LIST_FIELDS,
    ])
    write_json(raw / "pr.json", pr)
    write_json(raw / "branch-runs.json", runs)

    candidates = [
        run for run in runs
        if run["workflowName"] == args.workflow
        and run["headSha"] == pr["headRefOid"]
        and run["status"] == "completed"
    ]
    if not candidates:
        sys.exit(f"no completed {args.workflow!r} run for PR {args.pr} head {pr['headRefOid']}")
    selected = max(candidates, key=lambda run: run["createdAt"])
    run_id = selected["databaseId"]
    run_path = raw / f"run-{run_id}.json"
    if args.refresh or not run_path.exists():
        run = gh_json(["run", "view", str(run_id), "--repo", args.repo, "--json", RUN_FIELDS])
        write_json(run_path, run)
    else:
        run = json.loads(run_path.read_text())

    selection = {
        "repo": args.repo,
        "pr": args.pr,
        "workflow": args.workflow,
        "head_sha": pr["headRefOid"],
        "run_id": run_id,
        "run_file": run_path.name,
        "run_url": run["url"],
    }
    write_json(raw / "selection.json", selection)

    if args.include_logs:
        logs = raw / "logs"
        logs.mkdir(exist_ok=True)
        for job in run["jobs"]:
            job_duration = duration_seconds(job.get("startedAt"), job.get("completedAt"))
            if job.get("conclusion") == "skipped" or job_duration is None or job_duration <= 60:
                continue
            log_path = logs / f"job-{job['databaseId']}.log"
            if log_path.exists() and not args.refresh:
                continue
            proc = subprocess.run(
                ["gh", "run", "view", str(run_id), "--repo", args.repo,
                 "--job", str(job["databaseId"]), "--log"],
                text=True,
                capture_output=True,
            )
            if proc.returncode == 0:
                log_path.write_text(proc.stdout)

    print(json.dumps(selection, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
