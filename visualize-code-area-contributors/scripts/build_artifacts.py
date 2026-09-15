#!/usr/bin/env python3
"""Deduplicate cached Git authors and author Flint contributor-history specs."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--aliases", type=Path)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--exclude-churn-commit", action="append", default=[])
    return parser.parse_args()


def read_json(path: Path) -> Any:
    if not path.exists():
        sys.exit(f"missing cached input: {path}")
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


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def month_start(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return f"{parsed.year:04d}-{parsed.month:02d}-01"


def month_range(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    finish = date.fromisoformat(end)
    values = []
    while current <= finish:
        values.append(current.isoformat())
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
    return values


def load_aliases(path: Path | None) -> tuple[dict[str, str], dict[str, str], dict[str, str], set[str], dict[str, Any]]:
    if path is None:
        return {}, {}, {}, set(), {"source": None, "sha256": None, "canonical_authors": 0}
    data = read_json(path)
    email_to_key: dict[str, str] = {}
    name_to_key: dict[str, str] = {}
    key_to_name: dict[str, str] = {}
    for index, author in enumerate(data.get("canonical_authors", [])):
        canonical = author["name"].strip()
        key = f"explicit:{index}:{normalize_name(canonical)}"
        key_to_name[key] = canonical
        for email in author.get("emails", []):
            normalized = email.strip().casefold()
            if normalized in email_to_key and email_to_key[normalized] != key:
                sys.exit(f"email appears in multiple aliases: {email}")
            email_to_key[normalized] = key
        for name in author.get("names", []):
            normalized = normalize_name(name)
            if normalized in name_to_key and name_to_key[normalized] != key:
                sys.exit(f"name appears in multiple aliases: {name}")
            name_to_key[normalized] = key
    ignored = {email.strip().casefold() for email in data.get("ignored_emails", [])}
    provenance = {
        "source": str(path.resolve()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canonical_authors": len(key_to_name),
    }
    return email_to_key, name_to_key, key_to_name, ignored, provenance


def main() -> int:
    args = parse_args()
    if args.top < 1:
        sys.exit("--top must be positive")
    raw = args.bundle / "raw"
    derived = args.bundle / "derived"
    specs_dir = args.bundle / "flint-specs"
    selection = read_json(raw / "selection.json")
    commits = read_json(raw / "commits.json")
    email_aliases, name_aliases, explicit_names, ignored_emails, alias_provenance = load_aliases(args.aliases)
    excluded_churn = set(args.exclude_churn_commit)

    email_names: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    name_emails: dict[str, set[str]] = collections.defaultdict(set)
    aggregates: dict[str, dict[str, Any]] = {}
    monthly: dict[tuple[str, str], dict[str, int]] = collections.defaultdict(lambda: {"commits": 0, "churn": 0})
    unmapped: set[tuple[str, str]] = set()

    for commit in commits:
        raw_name = commit["author_name"].strip()
        email = commit["author_email"].strip().casefold()
        normalized_name = normalize_name(raw_name)
        email_names[email][raw_name] += 1
        name_emails[normalized_name].add(email)
        if email in ignored_emails:
            continue
        if email in email_aliases:
            key = email_aliases[email]
        elif normalized_name in name_aliases:
            key = name_aliases[normalized_name]
        else:
            # Exact author names merge across emails; non-exact aliases require
            # an explicit configuration entry and remain visible for review.
            key = f"auto:{normalized_name or email}"
            unmapped.add((raw_name, email))
        display_name = explicit_names.get(key, raw_name or email)
        aggregate = aggregates.setdefault(key, {
            "author": display_name,
            "emails": set(),
            "raw_names": set(),
            "commits": set(),
            "paths": set(),
            "dates": [],
            "active_months": set(),
            "additions": 0,
            "deletions": 0,
        })
        aggregate["emails"].add(email)
        aggregate["raw_names"].add(raw_name)
        aggregate["commits"].add(commit["sha"])
        aggregate["dates"].append(commit["authored_at"])
        month = month_start(commit["authored_at"])
        aggregate["active_months"].add(month)
        additions = 0
        deletions = 0
        for change in commit["changes"]:
            aggregate["paths"].add(change["path"])
            if change["additions"] is not None and change["deletions"] is not None:
                additions += change["additions"]
                deletions += change["deletions"]
        if commit["sha"] not in excluded_churn:
            aggregate["additions"] += additions
            aggregate["deletions"] += deletions
            monthly[(key, month)]["churn"] += additions + deletions
        monthly[(key, month)]["commits"] += 1

    contributor_rows = []
    for key, aggregate in aggregates.items():
        commit_count = len(aggregate["commits"])
        contributor_rows.append({
            "identity_key": key,
            "author": aggregate["author"],
            "commits": commit_count,
            "commit_share": 0.0,
            "additions": aggregate["additions"],
            "deletions": aggregate["deletions"],
            "churn": aggregate["additions"] + aggregate["deletions"],
            "unique_paths_touched": len(aggregate["paths"]),
            "active_months": len(aggregate["active_months"]),
            "first_authored_at": min(aggregate["dates"]),
            "last_authored_at": max(aggregate["dates"]),
            "emails": sorted(aggregate["emails"]),
            "raw_names": sorted(aggregate["raw_names"]),
        })
    contributor_rows.sort(key=lambda row: (-row["commits"], -row["churn"], row["author"].casefold()))
    total_commits = sum(row["commits"] for row in contributor_rows)
    for row in contributor_rows:
        row["commit_share"] = round(row["commits"] / total_commits, 4)

    top_rows = contributor_rows[: args.top]
    all_months = month_range(
        min(month_start(commit["authored_at"]) for commit in commits),
        max(month_start(commit["authored_at"]) for commit in commits),
    )
    author_by_key = {row["identity_key"]: row["author"] for row in top_rows}
    monthly_rows = []
    for row in top_rows:
        key = row["identity_key"]
        for month in all_months:
            values = monthly[(key, month)]
            monthly_rows.append({
                "author": author_by_key[key],
                "month": month,
                "commits": values["commits"],
                "churn": values["churn"],
            })

    conflicts = {
        "emails_with_multiple_names": [
            {"email": email, "names": dict(names)}
            for email, names in sorted(email_names.items()) if len(names) > 1
        ],
        "names_with_multiple_emails": [
            {"name": name, "emails": sorted(emails)}
            for name, emails in sorted(name_emails.items()) if len(emails) > 1
        ],
        "unmapped_identities": [
            {"name": name, "email": email} for name, email in sorted(unmapped)
        ],
    }

    area = selection["path"]
    top = top_rows[0]
    top_two_share = sum(row["commits"] for row in top_rows[:2]) / total_commits
    recency_reference = max(commit["authored_at"][:10] for commit in commits)
    recency_reference_date = date.fromisoformat(recency_reference)
    bar_values = [{
        "Author": row["author"],
        "Commits": row["commits"],
        "Last activity": row["last_authored_at"][:10],
        "Recency days": (recency_reference_date - date.fromisoformat(row["last_authored_at"][:10])).days,
        "Churn": row["churn"],
        "Paths touched": row["unique_paths_touched"],
    } for row in top_rows]
    heatmap_values = [{
        "Author": row["author"],
        "Month": row["month"],
        "Commits": row["commits"],
    } for row in monthly_rows]
    common = {"theme_spec": "economist", "options": {"addTooltips": True}}
    specs = {
        "contributor-scale-recency": {
            **common,
            "data": {"values": bar_values},
            "semantic_types": {
                "Author": "Category",
                "Commits": "Quantity",
                "Last activity": "Date",
                "Recency days": {"semanticType": "Duration", "unit": "days"},
                "Churn": "Quantity",
                "Paths touched": "Quantity",
            },
            "chart_spec": {
                "chartType": "Bar Table",
                "title": f"{top['author']} leads {area} with {top['commits']} commits",
                "subtitle": f"Top {len(top_rows)} authors; bar length is non-merge commits, and darker means less recent as of {recency_reference}",
                "encodings": {
                    "y": {"field": "Author", "sortBy": "x", "sortOrder": "descending"},
                    "x": {"field": "Commits"},
                    "color": {"field": "Recency days"},
                },
                "baseSize": {"width": 1250, "height": 760},
                "canvasSize": {"width": 1550, "height": 1000},
            },
        },
        "contributor-activity-heatmap": {
            **common,
            "data": {"values": heatmap_values},
            "semantic_types": {"Author": "Category", "Month": "Date", "Commits": "Quantity"},
            "chart_spec": {
                "chartType": "Heatmap",
                "title": f"The top two authors account for {top_two_share:.0%} of {area} commits",
                "subtitle": f"Monthly non-merge commits for the top {len(top_rows)} authors; darker cells mean more commits",
                "encodings": {
                    "x": {"field": "Month"},
                    "y": {"field": "Author"},
                    "color": {"field": "Commits"},
                },
                "chartProperties": {"showValueLabels": True},
                "baseSize": {"width": 1350, "height": 760},
                "canvasSize": {"width": 1650, "height": 1000},
            },
        },
    }
    summary = {
        **selection,
        "history": "path-scoped Git history",
        "merge_commits_included": selection["include_merges"],
        "raw_commit_count": len(commits),
        "attributed_commit_count": total_commits,
        "contributor_count": len(contributor_rows),
        "top_author": top["author"],
        "top_author_commits": top["commits"],
        "top_two_commit_share": round(top_two_share, 4),
        "alias_provenance": alias_provenance,
        "excluded_churn_commits": sorted(excluded_churn),
    }
    write_json(derived / "summary.json", summary)
    write_json(derived / "contributors.json", contributor_rows)
    write_csv(derived / "contributors.csv", [
        {key: value for key, value in row.items() if key not in {"emails", "raw_names"}}
        for row in contributor_rows
    ])
    write_json(derived / "monthly.json", monthly_rows)
    write_csv(derived / "monthly.csv", monthly_rows)
    write_json(derived / "identity-review.json", conflicts)
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
