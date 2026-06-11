from __future__ import annotations

import importlib
import unittest

from core.bootstrap import create_kernel
from features.loader import configured_feature_tests


class FeatureContractTests(unittest.TestCase):
    def test_enabled_features_declare_importable_tests(self) -> None:
        kernel = create_kernel()
        features = kernel.describe_capabilities()["features"]
        self.assertTrue(features)

        for feature in features:
            with self.subTest(feature=feature["name"]):
                self.assertTrue(feature["removable"])
                self.assertTrue(feature["tests"])
                for module_name in feature["tests"]:
                    importlib.import_module(module_name)

    def test_configured_feature_tests_are_discoverable(self) -> None:
        kernel = create_kernel()
        tests = configured_feature_tests(kernel.config)
        self.assertIn("tests.test_feature_contracts", tests)
        self.assertIn("tests.test_mcp_tools_feature", tests)

    def test_every_tool_reports_feature_owner(self) -> None:
        kernel = create_kernel()
        tools = kernel.describe_capabilities()["tools"]
        self.assertTrue(tools)
        missing_owner = [tool["name"] for tool in tools if not tool.get("feature")]
        self.assertEqual(missing_owner, [])


if __name__ == "__main__":
    unittest.main()
