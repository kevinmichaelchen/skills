import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze.py"
SPEC = importlib.util.spec_from_file_location("nx_affected_analyze", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class AnalyzeTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "nodes": {
                "organization": {"data": {"root": "packages/organization"}},
                "cart": {"data": {"root": "packages/cart"}},
                "api": {"data": {"root": "apps/api"}},
            },
            "dependencies": {
                "cart": [{"source": "cart", "target": "organization"}],
                "api": [{"source": "api", "target": "cart"}],
            },
        }

    def test_explains_transitive_selection_from_owned_file(self):
        explanations = MODULE.explain_selection(
            ["organization", "cart", "api"],
            "test:unit",
            self.graph,
            ["packages/organization/src/index.ts"],
            {"packages/organization/src/index.ts": ["organization"]},
            [],
            "default: all projects",
        )
        api = next(row for row in explanations if row["project"] == "api")
        self.assertEqual(api["primary"]["seed_reason"]["kind"], "project-ownership")
        self.assertEqual(api["primary"]["dependency_path"], ["organization", "cart", "api"])

    @mock.patch.object(MODULE.shutil, "which", return_value="/toolchain/bin/node")
    def test_nx_environment_does_not_copy_ambient_variables(self, _which):
        self.assertEqual(MODULE.nx_environment(), {
            "PATH": f"/toolchain/bin{MODULE.os.pathsep}{MODULE.os.defpath}",
            "NX_DAEMON": "false",
            "NX_INTERACTIVE": "false",
        })

    def test_removes_only_workspace_root_inputs_and_restores_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_dir = root / "packages" / "organization"
            project_dir.mkdir(parents=True)
            config = project_dir / "project.json"
            original = '{"targets":{"build":{"inputs":["default","{workspaceRoot}/packages/**/*.ts"]}}}\n'
            config.write_text(original)
            graph = {"nodes": {"organization": {"data": {"root": "packages/organization"}}}}
            matches = [{"project": "organization", "target": "build", "pattern": "packages/**/*.ts", "matched_files": ["packages/x.ts"]}]
            backups, removals = MODULE.remove_workspace_inputs(root, graph, {}, matches, {"organization"})
            self.assertEqual(len(removals), 1)
            self.assertEqual(json.loads(config.read_text())["targets"]["build"]["inputs"], ["default"])
            MODULE.restore_configs(backups)
            self.assertEqual(config.read_text(), original)

    def test_does_not_remove_entire_named_input_to_eliminate_one_global_member(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_dir = root / "packages" / "organization"
            project_dir.mkdir(parents=True)
            config = project_dir / "project.json"
            original = '{"targets":{"build":{"inputs":["default"]}}}\n'
            config.write_text(original)
            graph = {"nodes": {"organization": {"data": {"root": "packages/organization"}}}}
            nx_json = {"namedInputs": {"default": ["{projectRoot}/**/*", "{workspaceRoot}/packages/**/*.ts"]}}
            matches = [{"project": "organization", "target": "build", "pattern": "packages/**/*.ts", "matched_files": ["packages/x.ts"]}]
            backups, removals = MODULE.remove_workspace_inputs(root, graph, nx_json, matches, {"organization"})
            self.assertEqual(removals, [])
            self.assertEqual(backups, {})
            self.assertEqual(config.read_text(), original)


if __name__ == "__main__":
    unittest.main()
