from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from core.events import EventBus
from core.kernel import AgentKernel
from core.registry import CapabilityRegistry
from core.runtime_paths import PROJECT_DIR
from core.state import StateStore


DEFAULT_CONFIG_PATH = PROJECT_DIR / "config" / "features.yaml"

_DEFAULT_KERNEL: AgentKernel | None = None


def _load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return {
            "features": {
                "mcp_tools": {
                    "enabled": True,
                    "module": "features.mcp_tools.feature",
                }
            }
        }

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}

    if not isinstance(loaded, dict):
        raise ValueError(f"Kernel feature config must be a mapping: {path}")

    loaded.setdefault("features", {})
    return loaded


def create_kernel(config_path: str | Path | None = None) -> AgentKernel:
    config = _load_config(config_path)
    registry = CapabilityRegistry()
    kernel = AgentKernel(
        registry=registry,
        events=EventBus(),
        state=StateStore(),
        config=config,
    )

    from features.loader import install_configured_features

    install_configured_features(kernel, config)

    return kernel


def get_default_kernel(*, reload: bool = False) -> AgentKernel:
    global _DEFAULT_KERNEL
    if reload or _DEFAULT_KERNEL is None:
        _DEFAULT_KERNEL = create_kernel()
    return _DEFAULT_KERNEL
