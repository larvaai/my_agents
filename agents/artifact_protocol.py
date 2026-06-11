from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


FACTORY_VERSION = "v0.7"
DEFAULT_ARTIFACT_ROOT = Path("workspace") / "factory_runs"
MAX_INLINE_FIELD_CHARS = 480


def make_run_id(prefix: str = "factory") -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{prefix}"


def ensure_artifact_dir(
    *,
    artifact_root: str | Path = DEFAULT_ARTIFACT_ROOT,
    run_id: str | None = None,
) -> Path:
    root = Path(artifact_root)
    run_dir = root / (run_id or make_run_id())
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def brief_text(value: Any, *, limit: int = MAX_INLINE_FIELD_CHARS) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    text = "\n".join(line.rstrip() for line in text.splitlines())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def stable_json(data: Any, *, indent: int = 2) -> str:
    return json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=True, default=str)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    kind: str
    producer: str
    title: str
    summary: str
    bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "producer": self.producer,
            "title": self.title,
            "summary": brief_text(self.summary),
            "bytes": self.bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class StageResult:
    agent: str
    department: str
    decision: str
    route_next_agent: str
    artifact_refs: tuple[ArtifactRef, ...] = ()
    missing_inputs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    ok: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "department": self.department,
            "version": FACTORY_VERSION,
            "ok": self.ok,
            "decision": self.decision,
            "artifact_refs": [ref.to_dict() for ref in self.artifact_refs],
            "missing_inputs": list(self.missing_inputs),
            "notes": [brief_text(note) for note in self.notes],
            "route": {
                "next_agent": self.route_next_agent,
                "reason": self.metadata.get("route_reason", self.decision),
            },
            "metadata": _compact_metadata(self.metadata),
        }


def _compact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in metadata.items():
        if key == "route_reason":
            continue
        if isinstance(value, str):
            compacted[key] = brief_text(value)
        elif isinstance(value, list):
            compacted[key] = [
                brief_text(item) if isinstance(item, str) else item
                for item in value[:20]
            ]
            if len(value) > 20:
                compacted[f"{key}_truncated"] = len(value) - 20
        elif isinstance(value, dict):
            compacted[key] = {
                str(item_key): brief_text(item_value) if isinstance(item_value, str) else item_value
                for item_key, item_value in list(value.items())[:20]
            }
            if len(value) > 20:
                compacted[f"{key}_truncated"] = len(value) - 20
        else:
            compacted[key] = value
    return compacted


def write_text_artifact(
    artifact_dir: str | Path,
    filename: str,
    content: str,
    *,
    kind: str,
    producer: str,
    title: str,
    summary: str,
) -> ArtifactRef:
    path = Path(artifact_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return ArtifactRef(
        path=str(path),
        kind=kind,
        producer=producer,
        title=title,
        summary=summary,
        bytes=path.stat().st_size,
        sha256=_sha256(path),
    )


def write_json_artifact(
    artifact_dir: str | Path,
    filename: str,
    data: Any,
    *,
    kind: str,
    producer: str,
    title: str,
    summary: str,
) -> ArtifactRef:
    return write_text_artifact(
        artifact_dir,
        filename,
        stable_json(data),
        kind=kind,
        producer=producer,
        title=title,
        summary=summary,
    )


def read_artifact_text(ref_or_path: ArtifactRef | str | Path) -> str:
    path = Path(ref_or_path.path if isinstance(ref_or_path, ArtifactRef) else ref_or_path)
    return path.read_text(encoding="utf-8")


def stage_blocked(
    *,
    agent: str,
    department: str,
    missing_inputs: list[str],
    route_next_agent: str,
    reason: str,
) -> StageResult:
    return StageResult(
        agent=agent,
        department=department,
        decision="blocked_missing_inputs",
        route_next_agent=route_next_agent,
        missing_inputs=tuple(missing_inputs),
        notes=(reason,),
        ok=False,
        metadata={"route_reason": reason},
    )
