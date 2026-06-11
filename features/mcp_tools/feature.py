from __future__ import annotations

from typing import Any

from core.kernel import AgentKernel
from core.schemas import FeatureDescriptor
from features.mcp_tools.adapter import MCPToolAdapter
from features.mcp_tools.config import MCP_TOOL_NAMES, TOOL_ALIASES


def _canonical_mcp_tool_names() -> tuple[str, ...]:
    return tuple(
        f"{server_name}.{tool_name}"
        for server_name, tool_names in MCP_TOOL_NAMES.items()
        for tool_name in tool_names
    )


DESCRIPTOR = FeatureDescriptor(
    name="mcp_tools",
    version="1.0",
    category="tool_adapter",
    capabilities=(),
    tests=(
        "tests.test_feature_contracts",
        "tests.test_mcp_tools_feature",
    ),
    description="Routes kernel tool requests to configured MCP servers.",
    dependencies=("features.mcp_tools.client", "features.mcp_tools.config"),
)


def install(kernel: AgentKernel, settings: dict[str, Any]) -> None:
    adapter = MCPToolAdapter()
    canonical_names = _canonical_mcp_tool_names()
    register_aliases = bool(settings.get("register_aliases", True))
    alias_names = tuple(TOOL_ALIASES) if register_aliases else ()
    capability_names = canonical_names + alias_names

    descriptor = FeatureDescriptor(
        name=DESCRIPTOR.name,
        version=DESCRIPTOR.version,
        category=DESCRIPTOR.category,
        capabilities=capability_names,
        tests=DESCRIPTOR.tests,
        enabled=True,
        removable=True,
        description=DESCRIPTOR.description,
        dependencies=DESCRIPTOR.dependencies,
    )
    kernel.registry.register_feature(descriptor)
    kernel.registry.register_tools(capability_names, adapter, feature_name=DESCRIPTOR.name)

    if settings.get("fallback_for_unregistered", True):
        kernel.registry.set_fallback_tool_executor(adapter, feature_name=DESCRIPTOR.name)
