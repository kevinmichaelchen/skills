import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "aggregate_costs.py"
SPEC = importlib.util.spec_from_file_location("nx_cost_aggregate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class AggregateCostsTests(unittest.TestCase):
    def test_emits_required_provenance_and_stable_percentiles(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "costs.json"
            argv = [
                str(SCRIPT),
                "--input", str(ROOT / "tests" / "fixtures" / "timings.json"),
                "--out", str(output),
                "--evidence-kind", "observed-ci",
                "--evidence-label", "fixture run",
                "--repository", "example/repo",
                "--commit", "abcdef1234567890abcdef1234567890abcdef12",
                "--run-id", "run-1",
                "--runner", "fixture-runner",
                "--cache-state", "cold",
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                MODULE.main()
            payload = json.loads(output.read_text())
            self.assertEqual(payload["metadata"]["schema_version"], 2)
            self.assertEqual(payload["metadata"]["provenance"]["commit"], "abcdef1234567890abcdef1234567890abcdef12")
            organization = next(row for row in payload["projects"] if row["project"] == "organization")
            self.assertEqual(organization["p50_total_seconds"], 80.0)
            self.assertEqual(len(payload["missing"]), 1)


if __name__ == "__main__":
    unittest.main()
