from __future__ import annotations

import json
import queue
import re
import sys
import threading
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> str:
    return str(value)


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    folded = _fold_text(text)
    return any(marker in folded for marker in markers)


def _extract_target(text: str, markers: tuple[str, ...]) -> str | None:
    folded = _fold_text(text)
    for marker in markers:
        index = folded.find(marker)
        if index < 0:
            continue
        tail = folded[index + len(marker) :].strip(" :.-\t\r\n")
        if not tail:
            return None
        target = re.split(r"[,;\n]", tail, maxsplit=1)[0].strip()
        target = re.sub(r"^(cua|of|role of|vai tro cua)\s+", "", target).strip()
        return target[:120] or None
    return None


@dataclass
class UserDirective:
    directive_id: str
    raw_text: str
    source: str
    received_at: str
    received_monotonic: float
    priority: str = "user_live"
    scope: str = "current_run"
    intent: str = "answer_instruction"
    operations: list[dict[str, Any]] = field(default_factory=list)
    status: str = "accepted"
    notes: list[str] = field(default_factory=list)

    def to_log_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("received_monotonic", None)
        return payload


PROTECTED_MARKERS = (
    "disable trace",
    "turn off trace",
    "tat trace",
    "tat log",
    "xoa log",
    "delete log",
    "hide log",
    "admin trace off",
    "bo admin trace",
    "khong ghi log",
)

HIDDEN_COT_MARKERS = (
    "hidden chain",
    "chain of thought an",
    "hidden cot",
    "reasoning an",
    "suy luan an",
)

FORCE_FINAL_MARKERS = (
    "stop now",
    "finish now",
    "answer now",
    "final now",
    "dung lai",
    "dung ngay",
    "tra loi ngay",
    "chot ngay",
)

RETRY_MARKERS = (
    "retry",
    "rerun",
    "run again",
    "chay lai",
    "lam lai",
    "thu lai",
)

REMOVE_AGENT_MARKERS = (
    "remove agent",
    "skip agent",
    "delete agent",
    "bo agent",
    "bo bot agent",
    "xoa agent",
    "khong can agent",
    "khong can vai tro",
    "khong can role",
)

ADD_AGENT_MARKERS = (
    "add agent",
    "them agent",
    "tao agent",
)

ADD_TOOL_MARKERS = (
    "add tool",
    "them tool",
    "dung tool",
    "use tool",
)

ADD_SKILL_MARKERS = (
    "add skill",
    "them skill",
    "dung skill",
    "use skill",
)

STYLE_SHORT_MARKERS = (
    "shorter",
    "concise",
    "ngan hon",
    "tra loi ngan",
    "bo bot",
    "rut gon",
)

CURRENT_RUN_ONLY_MARKERS = (
    "trong luot chay nay",
    "luot nay",
    "current run",
    "this run",
    "luot sau van can",
    "next run still",
    "future runs still",
)


def parse_user_directive(raw_text: str, directive_id: str, source: str = "manual") -> UserDirective:
    text = raw_text.strip()
    directive = UserDirective(
        directive_id=directive_id,
        raw_text=text,
        source=source,
        received_at=_utc_now(),
        received_monotonic=time.monotonic(),
    )

    if not text:
        directive.status = "rejected"
        directive.intent = "empty"
        directive.notes.append("Empty user directive ignored.")
        return directive

    if _contains_any(text, PROTECTED_MARKERS):
        directive.status = "rejected"
        directive.intent = "blocked_runtime_invariant"
        directive.operations.append({"op": "blocked_request", "target": "trace_logging"})
        directive.notes.append("Trace/admin logging cannot be disabled by a live directive.")
        return directive

    if _contains_any(text, HIDDEN_COT_MARKERS):
        directive.status = "accepted_with_degradation"
        directive.intent = "answer_instruction"
        directive.operations.append(
            {
                "op": "answer_instruction",
                "instruction": "Provide a concise public rationale, not hidden chain-of-thought.",
            }
        )
        directive.notes.append("Hidden internal chain-of-thought is not exposed; public rationale is allowed.")
        return directive

    if _contains_any(text, FORCE_FINAL_MARKERS):
        directive.intent = "flow_control"
        directive.operations.append({"op": "force_final", "mode": "synthesize_now"})

    if _contains_any(text, RETRY_MARKERS):
        directive.intent = "flow_control"
        directive.operations.append({"op": "retry_step", "mode": "next_agent_call"})

    if _contains_any(text, REMOVE_AGENT_MARKERS):
        directive.intent = "modify_flow"
        current_run_only = _contains_any(text, CURRENT_RUN_ONLY_MARKERS)
        directive.operations.append(
            {
                "op": "remove_or_skip_agent",
                "target": _extract_target(text, REMOVE_AGENT_MARKERS) or "unspecified_agent",
                "mode": "skip_current_run_only" if current_run_only else "skip_when_supported",
            }
        )
        if current_run_only:
            directive.notes.append("Skip/remove request applies only to the current run; future runs keep the default role.")

    if _contains_any(text, ADD_AGENT_MARKERS):
        directive.intent = "modify_flow"
        directive.operations.append(
            {
                "op": "add_agent",
                "target": _extract_target(text, ADD_AGENT_MARKERS) or "unspecified_agent",
                "mode": "approved_template_or_runtime_instruction",
            }
        )

    if _contains_any(text, ADD_TOOL_MARKERS):
        directive.intent = "tool_request"
        directive.operations.append(
            {
                "op": "request_tool",
                "target": _extract_target(text, ADD_TOOL_MARKERS) or "unspecified_tool",
                "mode": "use_if_available_otherwise_report",
            }
        )

    if _contains_any(text, ADD_SKILL_MARKERS):
        directive.intent = "skill_request"
        directive.operations.append(
            {
                "op": "request_skill",
                "target": _extract_target(text, ADD_SKILL_MARKERS) or "unspecified_skill",
                "mode": "use_if_available_otherwise_report",
            }
        )

    if _contains_any(text, STYLE_SHORT_MARKERS):
        directive.operations.append({"op": "answer_style", "style": "concise"})

    if not directive.operations:
        directive.intent = "answer_instruction"
        directive.operations.append({"op": "answer_instruction", "instruction": text})

    return directive


class UserDirectiveController:
    """
    Control-plane inbox for live user directives.

    This is intentionally deterministic. The User Agent parses the user's live
    text into directives, persists them, and renders a high-priority prompt
    block for the next agent call. It does not execute tools by itself.
    """

    def __init__(
        self,
        *,
        run_id: str,
        control_dir: str | Path | None = None,
        default_control_dir: str | Path | None = None,
        interactive: bool = False,
        event_logger: Any | None = None,
    ) -> None:
        self.run_id = run_id
        self.interactive = interactive
        self.event_logger = event_logger
        self.control_dir = Path(control_dir or default_control_dir) if (control_dir or default_control_dir) else None
        self.enabled = bool(interactive or control_dir)
        self._queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sequence = 0
        self._inbox_offset = 0
        self._processed_text_files: set[Path] = set()
        self.directives: list[UserDirective] = []

    @property
    def inbox_path(self) -> Path | None:
        if self.control_dir is None:
            return None
        return self.control_dir / "inbox.jsonl"

    def start(self) -> None:
        if not self.enabled:
            return
        if self.control_dir is not None:
            (self.control_dir / "inbox").mkdir(parents=True, exist_ok=True)
            self.inbox_path.touch(exist_ok=True)  # type: ignore[union-attr]
        if self.interactive and self._thread is None:
            self._thread = threading.Thread(target=self._stdin_loop, name="user-agent-stdin", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _stdin_loop(self) -> None:
        while not self._stop.is_set():
            try:
                line = sys.stdin.readline()
            except Exception:
                return
            if line == "":
                return
            text = line.strip()
            if text:
                self._queue.put(("stdin", text))

    def _next_id(self) -> str:
        self._sequence += 1
        return f"userdir_{self._sequence:04d}"

    def _append_jsonl(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, default=_json_default) + "\n")

    def _record_directive(self, raw_text: str, source: str) -> UserDirective:
        directive = parse_user_directive(raw_text, self._next_id(), source=source)
        self.directives.append(directive)
        payload = directive.to_log_dict()
        if self.control_dir is not None:
            if directive.status == "rejected":
                self._append_jsonl(self.control_dir / "rejected_directives.jsonl", payload)
            else:
                self._append_jsonl(self.control_dir / "accepted_directives.jsonl", payload)
            self._append_jsonl(self.control_dir / "user_directives.jsonl", payload)
        if self.event_logger is not None:
            self.event_logger.emit("UserDirectiveEvent", directive=payload)
        return directive

    def _poll_queue(self) -> list[UserDirective]:
        directives: list[UserDirective] = []
        while True:
            try:
                source, text = self._queue.get_nowait()
            except queue.Empty:
                break
            directives.append(self._record_directive(text, source))
        return directives

    def _poll_jsonl_inbox(self) -> list[UserDirective]:
        path = self.inbox_path
        if path is None or not path.exists():
            return []
        directives: list[UserDirective] = []
        with path.open("r", encoding="utf-8") as handle:
            handle.seek(self._inbox_offset)
            lines = handle.readlines()
            self._inbox_offset = handle.tell()
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            source = "control_dir"
            text = stripped
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                source = str(payload.get("source") or source)
                text = str(payload.get("text") or payload.get("prompt") or payload.get("directive") or "")
            if text.strip():
                directives.append(self._record_directive(text, source))
        return directives

    def _poll_text_files(self) -> list[UserDirective]:
        if self.control_dir is None:
            return []
        inbox_dir = self.control_dir / "inbox"
        if not inbox_dir.exists():
            return []
        directives: list[UserDirective] = []
        for path in sorted(inbox_dir.glob("*.txt")):
            resolved = path.resolve()
            if resolved in self._processed_text_files:
                continue
            self._processed_text_files.add(resolved)
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                directives.append(self._record_directive(text, f"file:{path.name}"))
        return directives

    def poll(self) -> list[UserDirective]:
        if not self.enabled:
            return []
        directives: list[UserDirective] = []
        directives.extend(self._poll_queue())
        directives.extend(self._poll_jsonl_inbox())
        directives.extend(self._poll_text_files())
        return directives

    def active_directives(self) -> list[UserDirective]:
        return [
            directive
            for directive in self.directives
            if directive.status in {"accepted", "accepted_with_degradation"}
        ]

    def has_force_final(self, directives: list[UserDirective] | None = None) -> bool:
        selected = directives if directives is not None else self.active_directives()
        return any(
            operation.get("op") == "force_final"
            for directive in selected
            for operation in directive.operations
            if directive.status in {"accepted", "accepted_with_degradation"}
        )

    def render_prompt_block(self, directives: list[UserDirective] | None = None) -> str:
        selected = directives if directives is not None else self.active_directives()
        if not selected:
            return ""
        payload = [directive.to_log_dict() for directive in selected]
        return (
            "USER AGENT LIVE DIRECTIVES\n"
            "These directives were sent by the user while this run was active. "
            "They have higher application-level priority than agent suggestions, "
            "the previous run plan, and default routing. Follow the latest "
            "accepted directive when directives conflict. Do not disable trace "
            "logging, do not fabricate unavailable tools or skills, and keep "
            "the normal JSON action protocol.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)}"
        )
