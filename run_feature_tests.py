from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

from core.bootstrap import DEFAULT_CONFIG_PATH, create_kernel
from features.loader import configured_feature_tests


BASE_TEST_MODULES = [
    "tests.test_kernel_contracts",
]


def _configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _suite_from_modules(module_names: list[str]) -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for module_name in module_names:
        suite.addTests(loader.loadTestsFromName(module_name))
    return suite


def main() -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Run tests required by enabled features.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Feature config path")
    args = parser.parse_args()

    kernel = create_kernel(Path(args.config))
    feature_tests = configured_feature_tests(kernel.config)
    module_names = sorted(set(BASE_TEST_MODULES + feature_tests))
    if not module_names:
        print("No feature tests configured.")
        return 1

    suite = _suite_from_modules(module_names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    print("FEATURE_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
