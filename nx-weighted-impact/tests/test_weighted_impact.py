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
SCRIPT = ROOT / "scripts" / "analyze_weighted_impact.py"
SPEC = importlib.util.spec_from_file_location("nx_weighted_impact", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class WeightedImpactTests(unittest.TestCase):
    def run_analysis(self, commit: str, *extra: str):
        temporary = tempfile.TemporaryDirectory()
        output = Path(temporary.name) / "output"
        argv = [
            str(SCRIPT),
            "--graph", str(ROOT / "tests" / "fixtures" / "graph.json"),
            "--costs", str(ROOT / "tests" / "fixtures" / "costs.json"),
            "--out", str(output),
            "--graph-commit", commit,
            *extra,
        ]
        error = None
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            try:
                MODULE.main()
            except ValueError as exc:
                error = exc
        return temporary, output, error

    def test_aligned_snapshots_emit_paths_and_counterfactual_label(self):
        temporary, output, error = self.run_analysis("abcdef1234567890abcdef1234567890abcdef12")
        with temporary:
            self.assertIsNone(error)
            summary = json.loads((output / "summary.json").read_text())
            paths = json.loads((output / "representative-paths.json").read_text())["paths"]
            self.assertEqual(summary["analysis_class"], "snapshot-aligned-counterfactual")
            organization_to_api = next(row for row in paths if row["changed_project"] == "organization" and row["selected_test_project"] == "api")
            self.assertEqual(organization_to_api["dependency_path"], ["organization", "cart", "api"])

    def test_mismatched_snapshots_fail_without_explicit_override(self):
        temporary, _output, error = self.run_analysis("1111111111111111111111111111111111111111")
        with temporary:
            self.assertIsInstance(error, ValueError)
            self.assertIn("does not match cost commit", str(error))


if __name__ == "__main__":
    unittest.main()
