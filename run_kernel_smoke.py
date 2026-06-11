from __future__ import annotations

import tempfile
from pathlib import Path

from core.bootstrap import create_kernel, get_default_kernel


def _require(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    kernel = get_default_kernel(reload=True)
    capabilities = kernel.describe_capabilities()
    feature_names = {feature["name"] for feature in capabilities["features"]}
    tool_names = {tool["name"] for tool in capabilities["tools"]}

    _require("mcp_tools" in feature_names, capabilities)
    _require("python.python_probe" in tool_names, "MCP tool was not registered")
    _require("run_python" in tool_names, "MCP alias was not registered")

    task = kernel.accept_task("kernel smoke")
    _require(task.user_request == "kernel smoke", task)
    _require(kernel.state.get("current_task") == task, kernel.state.snapshot())

    missing = kernel.execute_tool("unknown.nope", {})
    _require(missing.get("ok") is False, missing)
    _require(missing.get("capability") == "unknown.nope", missing)
    _require(missing.get("feature") == "mcp_tools", missing)
    _require((missing.get("metadata") or {}).get("request_id"), missing)
    _require("Unknown MCP server" in str(missing.get("error")), missing)

    events = [event.event_type for event in kernel.events.history()]
    _require("task.accepted" in events, events)
    _require("tool.requested" in events, events)
    _require("tool.failed" in events, events)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "features.yaml"
        config_path.write_text(
            "features:\n"
            "  mcp_tools:\n"
            "    enabled: false\n",
            encoding="utf-8",
        )
        null_kernel = create_kernel(config_path)
        result = null_kernel.execute_tool("python.python_probe", {"timeout": 1})
        _require(result.get("ok") is False, result)
        _require((result.get("data") or {}).get("missing_capability") is True, result)

    print("KERNEL_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
