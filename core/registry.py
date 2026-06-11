from __future__ import annotations

from typing import Any, NamedTuple

from core.ports.tool_port import ToolPort
from core.schemas import FeatureDescriptor, ToolRequest


class ToolResolution(NamedTuple):
    executor: ToolPort
    feature: str | None


class NullToolPort:
    name = "null_tool"

    def execute(self, request: ToolRequest) -> dict[str, Any]:
        return {
            "ok": False,
            "tool": request.name,
            "missing_capability": True,
            "error": f"No tool capability is registered for '{request.name}'.",
        }


class CapabilityRegistry:
    """
    Runtime registry for detachable capabilities.

    Exact tool registrations win. If no exact tool is found, the optional
    fallback executor can decide whether it can resolve aliases or dynamic MCP
    tools. If no fallback exists, NullToolPort keeps the kernel alive.
    """

    def __init__(self, *, null_tool: ToolPort | None = None) -> None:
        self._tools: dict[str, ToolPort] = {}
        self._features: dict[str, FeatureDescriptor] = {}
        self._tool_features: dict[str, str] = {}
        self._fallback_tool: ToolPort | None = None
        self._fallback_feature: str | None = None
        self._null_tool = null_tool or NullToolPort()

    def register_feature(self, descriptor: FeatureDescriptor) -> None:
        self._features[descriptor.name] = descriptor

    def register_tool(
        self,
        name: str,
        executor: ToolPort,
        *,
        feature_name: str | None = None,
    ) -> None:
        self._tools[name] = executor
        if feature_name:
            self._tool_features[name] = feature_name

    def register_tools(
        self,
        names: list[str] | tuple[str, ...] | set[str],
        executor: ToolPort,
        *,
        feature_name: str | None = None,
    ) -> None:
        for name in names:
            self.register_tool(name, executor, feature_name=feature_name)

    def set_fallback_tool_executor(self, executor: ToolPort | None, *, feature_name: str | None = None) -> None:
        self._fallback_tool = executor
        self._fallback_feature = feature_name if executor is not None else None

    def get_tool_executor(self, name: str) -> ToolPort:
        return self._tools.get(name) or self._fallback_tool or self._null_tool

    def resolve_tool(self, name: str) -> ToolResolution:
        if name in self._tools:
            return ToolResolution(self._tools[name], self._tool_features.get(name))
        if self._fallback_tool is not None:
            return ToolResolution(self._fallback_tool, self._fallback_feature)
        return ToolResolution(self._null_tool, None)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "feature": self._tool_features.get(name),
                "executor": getattr(executor, "name", executor.__class__.__name__),
            }
            for name, executor in sorted(self._tools.items())
        ]

    def list_features(self) -> list[dict[str, Any]]:
        return [descriptor.as_dict() for descriptor in self._features.values()]
