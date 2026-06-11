from __future__ import annotations

from typing import Any

from core.bootstrap import get_default_kernel
from core.kernel import AgentKernel


def call_tool(
    tool_name: str,
    args: dict[str, Any] | None = None,
    *,
    kernel: AgentKernel | None = None,
) -> dict[str, Any]:
    active_kernel = kernel or get_default_kernel()
    return active_kernel.execute_tool(tool_name, args or {})


def describe_capabilities(*, kernel: AgentKernel | None = None) -> dict[str, Any]:
    active_kernel = kernel or get_default_kernel()
    return active_kernel.describe_capabilities()
