from __future__ import annotations

from typing import Any

from core.schemas import CapabilityResult, ToolRequest
from features.mcp_tools.client import call_mcp_tool


class MCPToolAdapter:
    name = "mcp_tool_adapter"

    def execute(self, request: ToolRequest) -> dict[str, Any]:
        result = call_mcp_tool(request.name, request.args)
        return CapabilityResult.from_raw(
            capability=request.name,
            feature="mcp_tools",
            result=result,
            metadata={"adapter": self.name},
        ).as_dict()
