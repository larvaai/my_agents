from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.events import EventBus
from core.registry import CapabilityRegistry
from core.schemas import CapabilityResult, TaskEnvelope, ToolRequest
from core.state import StateStore


@dataclass
class AgentKernel:
    """
    Minimal living core.

    The kernel owns state, events, and capability lookup. Concrete behavior
    lives behind ports/adapters registered in the capability registry.
    """

    registry: CapabilityRegistry
    events: EventBus
    state: StateStore
    config: dict[str, Any] = field(default_factory=dict)

    def accept_task(self, user_request: str, context: dict[str, Any] | None = None) -> TaskEnvelope:
        task = TaskEnvelope(user_request=user_request, context=context or {})
        self.state.set("current_task", task)
        self.events.publish(
            "task.accepted",
            {"task_id": task.task_id, "context_keys": sorted(task.context)},
        )
        return task

    def execute_tool(self, tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        request = ToolRequest(name=tool_name, args=args or {})
        self.events.publish(
            "tool.requested",
            {"tool": request.name, "args": request.args, "request_id": request.request_id},
        )

        resolution = self.registry.resolve_tool(request.name)
        executor = resolution.executor
        try:
            result = executor.execute(request)
        except Exception as exc:
            result = {
                "ok": False,
                "tool": request.name,
                "error": str(exc),
                "kernel_error": True,
            }

        if not isinstance(result, dict):
            result = {
                "ok": False,
                "tool": request.name,
                "error": f"Tool executor returned {type(result).__name__}, expected dict.",
                "kernel_error": True,
            }

        result = CapabilityResult.from_raw(
            capability=request.name,
            feature=resolution.feature,
            result=result,
            metadata={
                "request_id": request.request_id,
                "executor": getattr(executor, "name", executor.__class__.__name__),
            },
        ).as_dict()

        self.events.publish(
            "tool.completed" if result.get("ok") else "tool.failed",
            {
                "tool": request.name,
                "request_id": request.request_id,
                "ok": bool(result.get("ok")),
                "error": result.get("error"),
            },
        )
        return result

    def describe_capabilities(self) -> dict[str, Any]:
        return {
            "features": self.registry.list_features(),
            "tools": self.registry.list_tools(),
        }
