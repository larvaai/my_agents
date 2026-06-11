from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from core.bootstrap import create_kernel
from tests.test_kernel_contracts import assert_capability_envelope


class MCPToolsFeatureTests(unittest.TestCase):
    def test_feature_registers_canonical_tools_and_aliases(self) -> None:
        kernel = create_kernel()
        capabilities = kernel.describe_capabilities()
        features = {feature["name"]: feature for feature in capabilities["features"]}
        tool_names = {tool["name"] for tool in capabilities["tools"]}

        self.assertIn("mcp_tools", features)
        self.assertIn("python.python_probe", tool_names)
        self.assertIn("run_python", tool_names)
        self.assertIn("tests.test_mcp_tools_feature", features["mcp_tools"]["tests"])

    def test_adapter_execution_is_called_through_kernel(self) -> None:
        kernel = create_kernel()
        with patch(
            "features.mcp_tools.adapter.call_mcp_tool",
            return_value={"ok": True, "tool": "python_probe", "server": "python"},
        ) as call:
            result = kernel.execute_tool("python.python_probe", {"timeout": 1})

        assert_capability_envelope(self, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["capability"], "python.python_probe")
        self.assertEqual(result["feature"], "mcp_tools")
        self.assertEqual(result["data"]["server"], "python")
        self.assertTrue(result["metadata"]["request_id"])
        call.assert_called_once_with("python.python_probe", {"timeout": 1})

    def test_feature_can_disable_alias_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "features.yaml"
            config_path.write_text(
                "features:\n"
                "  mcp_tools:\n"
                "    enabled: true\n"
                "    module: features.mcp_tools.feature\n"
                "    register_aliases: false\n"
                "    fallback_for_unregistered: false\n",
                encoding="utf-8",
            )
            kernel = create_kernel(config_path)

        tool_names = {tool["name"] for tool in kernel.describe_capabilities()["tools"]}
        self.assertIn("python.run_python", tool_names)
        self.assertNotIn("run_python", tool_names)


if __name__ == "__main__":
    unittest.main()
