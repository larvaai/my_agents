from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.bootstrap import create_kernel


ENVELOPE_KEYS = {"ok", "capability", "feature", "data", "error", "metadata"}


def assert_capability_envelope(testcase: unittest.TestCase, result: dict) -> None:
    testcase.assertTrue(ENVELOPE_KEYS <= set(result))
    testcase.assertIsInstance(result["ok"], bool)
    testcase.assertIsInstance(result["capability"], str)
    testcase.assertTrue(result["feature"] is None or isinstance(result["feature"], str))
    testcase.assertIsInstance(result["data"], dict)
    testcase.assertTrue(result["error"] is None or isinstance(result["error"], str))
    testcase.assertIsInstance(result["metadata"], dict)


class KernelContractTests(unittest.TestCase):
    def test_kernel_accepts_task_and_records_events(self) -> None:
        kernel = create_kernel()
        task = kernel.accept_task("test task", {"source": "unit"})

        self.assertEqual(task.user_request, "test task")
        self.assertEqual(kernel.state.get("current_task"), task)
        self.assertIn("task.accepted", [event.event_type for event in kernel.events.history()])

    def test_disabled_feature_uses_null_tool_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "features.yaml"
            config_path.write_text(
                "features:\n"
                "  mcp_tools:\n"
                "    enabled: false\n",
                encoding="utf-8",
            )
            kernel = create_kernel(config_path)

        result = kernel.execute_tool("python.python_probe", {"timeout": 1})
        assert_capability_envelope(self, result)
        self.assertFalse(result["ok"])
        self.assertTrue(result["data"]["missing_capability"])
        self.assertEqual(result["capability"], "python.python_probe")
        self.assertIsNone(result["feature"])

    def test_unknown_tool_uses_capability_result_envelope(self) -> None:
        kernel = create_kernel()

        result = kernel.execute_tool("unknown.nope", {})

        assert_capability_envelope(self, result)
        self.assertFalse(result["ok"])
        self.assertEqual(result["capability"], "unknown.nope")
        self.assertEqual(result["feature"], "mcp_tools")
        self.assertIn("Unknown MCP server", result["error"] or "")
        self.assertTrue(result["metadata"]["request_id"])

    def test_unknown_feature_module_fails_at_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "features.yaml"
            config_path.write_text(
                "features:\n"
                "  missing:\n"
                "    enabled: true\n"
                "    module: features.does_not_exist\n",
                encoding="utf-8",
            )
            with self.assertRaises(ModuleNotFoundError):
                create_kernel(config_path)


if __name__ == "__main__":
    unittest.main()
