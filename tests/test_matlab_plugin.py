from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPOSITORY_ROOT / "plugins" / "matlab-r2026a"
SERVER_PATH = PLUGIN_ROOT / "scripts" / "matlab_mcp_server.py"

spec = importlib.util.spec_from_file_location("matlab_mcp_server", SERVER_PATH)
assert spec is not None and spec.loader is not None
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class ServerUnitTests(unittest.TestCase):
    def test_tool_names_are_unique_and_annotated(self) -> None:
        names = [tool["name"] for tool in server.TOOLS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            names,
            [
                "matlab_info",
                "list_matlab_products",
                "get_matlab_help",
                "run_matlab_code",
                "run_matlab_script",
            ],
        )
        for tool in server.TOOLS:
            annotations = tool["annotations"]
            self.assertIn("readOnlyHint", annotations)
            self.assertIn("destructiveHint", annotations)
            self.assertIn("openWorldHint", annotations)
        by_name = {tool["name"]: tool for tool in server.TOOLS}
        for name in ("matlab_info", "list_matlab_products", "get_matlab_help"):
            self.assertTrue(by_name[name]["annotations"]["readOnlyHint"])
            self.assertFalse(by_name[name]["annotations"]["openWorldHint"])
        for name in ("run_matlab_code", "run_matlab_script"):
            self.assertFalse(by_name[name]["annotations"]["readOnlyHint"])
            self.assertTrue(by_name[name]["annotations"]["destructiveHint"])
            self.assertTrue(by_name[name]["annotations"]["openWorldHint"])

    def test_release_guard_runs_before_requested_code(self) -> None:
        guarded = server.release_guarded_statement("disp(55);")
        self.assertIn("version('-release')", guarded)
        self.assertIn("2026a", guarded)
        self.assertTrue(guarded.endswith("disp(55);"))

    def test_environment_override_is_first_candidate(self) -> None:
        override = str(REPOSITORY_ROOT / "fake" / "matlab.exe")
        with mock.patch.dict(os.environ, {"MATLAB_R2026A_EXE": override}):
            candidates = server.matlab_executable_candidates()
        self.assertEqual(candidates[0], Path(override))

    def test_matlab_string_quoting(self) -> None:
        self.assertEqual(server.matlab_quote("O'Brien"), "'O''Brien'")

    def test_timeout_rejects_boolean_and_out_of_range_values(self) -> None:
        with self.assertRaises(ValueError):
            server.parse_timeout(True, 10)
        with self.assertRaises(ValueError):
            server.parse_timeout(0, 10)
        with self.assertRaises(ValueError):
            server.parse_timeout(server.MAX_TIMEOUT_SECONDS + 1, 10)

    def test_output_truncation_preserves_both_ends(self) -> None:
        value = "A" * (server.MAX_OUTPUT_CHARS + 100)
        truncated, was_truncated = server.truncate_output(value)
        self.assertTrue(was_truncated)
        self.assertTrue(truncated.startswith("A"))
        self.assertTrue(truncated.endswith("A"))
        self.assertIn("characters omitted", truncated)


class RepositoryContractTests(unittest.TestCase):
    def test_manifest_and_marketplace_contract(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["name"], PLUGIN_ROOT.name)
        self.assertEqual(manifest["version"], server.SERVER_VERSION)
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertEqual(marketplace["name"], "matlab-tools")
        self.assertEqual(marketplace["plugins"][0]["name"], manifest["name"])
        self.assertEqual(
            marketplace["plugins"][0]["source"]["path"],
            "./plugins/matlab-r2026a",
        )

    def test_mcp_server_uses_a_repo_relative_script(self) -> None:
        mcp = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
        config = mcp["mcpServers"]["matlab-r2026a"]
        self.assertEqual(config["cwd"], ".")
        self.assertEqual(config["command"], "python")
        self.assertEqual(config["args"], ["./scripts/matlab_mcp_server.py"])
        self.assertNotIn("env", config)


if __name__ == "__main__":
    unittest.main()
