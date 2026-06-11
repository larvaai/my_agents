from __future__ import annotations

import importlib
from typing import Any

from core.kernel import AgentKernel


DEFAULT_FEATURE_MODULES: dict[str, str] = {
    "mcp_tools": "features.mcp_tools.feature",
}


def _feature_items(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_features = config.get("features", {})
    if raw_features is None:
        return {}
    if not isinstance(raw_features, dict):
        raise ValueError("Kernel feature config must contain a 'features' mapping.")

    features: dict[str, dict[str, Any]] = {}
    for name, settings in raw_features.items():
        if settings is None:
            settings = {}
        if not isinstance(settings, dict):
            raise ValueError(f"Feature config for {name!r} must be a mapping.")
        features[name] = settings
    return features


def install_configured_features(kernel: AgentKernel, config: dict[str, Any]) -> None:
    for feature_name, settings in _feature_items(config).items():
        if settings.get("enabled", True) is False:
            continue

        module_name = settings.get("module") or DEFAULT_FEATURE_MODULES.get(feature_name)
        if not module_name:
            raise ValueError(f"No module configured for feature {feature_name!r}.")

        module = importlib.import_module(str(module_name))
        install = getattr(module, "install", None)
        if not callable(install):
            raise ValueError(f"Feature module {module_name!r} has no install(kernel, settings).")

        install(kernel, settings)


def configured_feature_tests(config: dict[str, Any]) -> list[str]:
    tests: list[str] = []
    for feature_name, settings in _feature_items(config).items():
        if settings.get("enabled", True) is False:
            continue

        explicit_tests = settings.get("tests")
        if explicit_tests is not None:
            if not isinstance(explicit_tests, list) or not all(isinstance(item, str) for item in explicit_tests):
                raise ValueError(f"tests for feature {feature_name!r} must be a list of module names.")
            tests.extend(explicit_tests)
            continue

        module_name = settings.get("module") or DEFAULT_FEATURE_MODULES.get(feature_name)
        if not module_name:
            continue
        module = importlib.import_module(str(module_name))
        descriptor = getattr(module, "DESCRIPTOR", None)
        descriptor_tests = getattr(descriptor, "tests", ())
        tests.extend(str(item) for item in descriptor_tests)
    return sorted(set(tests))
