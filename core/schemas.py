from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskEnvelope:
    user_request: str
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass(frozen=True)
class ToolRequest:
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass(frozen=True)
class CapabilityResult:
    ok: bool
    capability: str
    feature: str | None
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(
        cls,
        *,
        capability: str,
        feature: str | None,
        result: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> "CapabilityResult":
        if is_capability_result(result):
            data = dict(result.get("data") or {})
            result_metadata = dict(result.get("metadata") or {})
            if metadata:
                result_metadata.update(metadata)
            return cls(
                ok=bool(result.get("ok")),
                capability=str(result.get("capability") or capability),
                feature=result.get("feature") if result.get("feature") is not None else feature,
                data=data,
                error=result.get("error"),
                metadata=result_metadata,
            )

        ok = bool(result.get("ok", False))
        error = None if ok else str(result.get("error") or "Capability execution failed.")
        data = {
            key: value
            for key, value in result.items()
            if key not in {"ok", "error", "metadata"}
        }
        result_metadata = dict(result.get("metadata") or {})
        tool_metadata = result.get("tool_metadata")
        if isinstance(tool_metadata, dict):
            result_metadata.setdefault("tool_metadata", tool_metadata)
        if metadata:
            result_metadata.update(metadata)
        result_metadata.setdefault("raw_keys", sorted(result))

        return cls(
            ok=ok,
            capability=capability,
            feature=feature,
            data=data,
            error=error,
            metadata=result_metadata,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability": self.capability,
            "feature": self.feature,
            "data": dict(self.data),
            "error": self.error,
            "metadata": dict(self.metadata),
        }


def is_capability_result(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    required = {"ok", "capability", "feature", "data", "error", "metadata"}
    return required <= set(result)


def capability_data(result: dict[str, Any]) -> dict[str, Any]:
    if is_capability_result(result):
        data = result.get("data")
        return data if isinstance(data, dict) else {}
    return result


def capability_metadata(result: dict[str, Any]) -> dict[str, Any]:
    if is_capability_result(result):
        metadata = result.get("metadata")
        return metadata if isinstance(metadata, dict) else {}
    metadata = result.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def capability_get(result: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in {"ok", "capability", "feature", "data", "error", "metadata"}:
        return result.get(key, default)
    return capability_data(result).get(key, default)


@dataclass(frozen=True)
class FeatureDescriptor:
    name: str
    version: str
    category: str
    capabilities: tuple[str, ...]
    tests: tuple[str, ...]
    enabled: bool = True
    removable: bool = True
    description: str = ""
    dependencies: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "capabilities": list(self.capabilities),
            "tests": list(self.tests),
            "enabled": self.enabled,
            "removable": self.removable,
            "description": self.description,
            "dependencies": list(self.dependencies),
        }
