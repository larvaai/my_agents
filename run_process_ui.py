from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from core.runtime_paths import AGENT_RUNS_DIR, PROJECT_DIR, VAR_DIR
from tools.event_reader import load_runs


STATIC_DIR = PROJECT_DIR / "ui" / "process_dashboard"
UI_STATE_DIR = VAR_DIR / "process_ui"
PROMPT_DIR = UI_STATE_DIR / "prompts"
SERVER_INFO_PATH = UI_STATE_DIR / "server.json"
RUN_MODES = {"root", "langgraph"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_default(value: Any) -> str:
    return str(value)


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def read_jsonl(path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if limit is not None:
        lines = lines[-limit:]
    records: list[dict[str, Any]] = []
    offset = max(0, (len(path.read_text(encoding="utf-8", errors="replace").splitlines()) - len(lines)))
    for index, line in enumerate(lines, start=offset + 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            records.append(
                {
                    "kind": "InvalidEvent",
                    "line_number": index,
                    "error": str(exc),
                    "raw": line,
                }
            )
    return records


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, default=json_default) + "\n")


def tail_text(path: Path, *, max_chars: int = 24000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    return f"[tail {max_chars} of {len(text)} chars]\n{text[-max_chars:]}"


def safe_run_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)


def build_run_id(mode: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"ui_{mode}_{timestamp}_{uuid.uuid4().hex[:6]}"


def find_open_port(preferred: int) -> int:
    if preferred == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def build_command(mode: str, prompt_path: Path, run_id: str, max_steps: int) -> list[str]:
    if mode == "root":
        return [
            sys.executable,
            "main.py",
            "--user-control-dir",
            str(AGENT_RUNS_DIR / run_id / "control"),
            "--max-steps",
            str(max_steps),
            str(prompt_path),
        ]
    if mode == "langgraph":
        return [sys.executable, "main_langgraph.py", str(prompt_path)]
    raise ValueError(f"Unsupported mode: {mode}")


def summarize_event(event: dict[str, Any]) -> str:
    kind = event.get("kind", "?")
    sequence = event.get("sequence", "?")
    prefix = f"#{sequence} {kind}"
    if event.get("node"):
        prefix += f" node={event.get('node')}"
    if event.get("step") is not None:
        prefix += f" step={event.get('step')}"
    if kind == "StateEvent":
        return f"{prefix} status={event.get('status', '?')}"
    if kind == "ActionEvent":
        tool = event.get("tool")
        return f"{prefix} action={event.get('action', '?')}" + (f" tool={tool}" if tool else "")
    if kind == "ObservationEvent":
        result = event.get("result") if isinstance(event.get("result"), dict) else {}
        return f"{prefix} tool={event.get('tool', '?')} ok={result.get('ok')}"
    if kind == "MessageEvent":
        content = str(event.get("content", "")).replace("\n", " ")
        return f"{prefix} role={event.get('role', '?')} {content[:180]}"
    if kind == "UserDirectiveEvent":
        directive = event.get("directive") if isinstance(event.get("directive"), dict) else {}
        return f"{prefix} directive={directive.get('intent')} status={directive.get('status')}"
    return prefix


def derive_run_state(
    run_id: str,
    events: list[dict[str, Any]],
    summary: dict[str, Any] | None = None,
    process: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agents: dict[str, dict[str, Any]] = {}
    status_counts: dict[str, int] = {}
    directives: list[dict[str, Any]] = []
    current_agent = None
    current_status = None
    current_step = 0
    last_tool = None
    last_action = None
    last_error = None

    def touch_agent(name: str, *, event: dict[str, Any], status: str | None = None) -> None:
        item = agents.setdefault(
            name,
            {
                "name": name,
                "events": 0,
                "actions": 0,
                "tools": 0,
                "errors": 0,
                "last_status": None,
                "last_seen": None,
                "active": False,
            },
        )
        item["events"] += 1
        if event.get("kind") == "ActionEvent":
            item["actions"] += 1
        if event.get("kind") == "ObservationEvent" or event.get("tool"):
            item["tools"] += 1
        if event.get("kind") == "ErrorEvent":
            item["errors"] += 1
        if status:
            item["last_status"] = status
        item["last_seen"] = event.get("timestamp")

    for event in events:
        kind = event.get("kind")
        if isinstance(event.get("step"), int):
            current_step = max(current_step, int(event["step"]))

        status = event.get("status")
        if isinstance(status, str):
            current_status = status
            status_counts[status] = status_counts.get(status, 0) + 1

        node = event.get("node")
        agent = event.get("agent")
        if isinstance(node, str):
            current_agent = node
            touch_agent(node, event=event, status=status if isinstance(status, str) else None)
        elif isinstance(agent, str):
            current_agent = agent
            touch_agent(agent, event=event, status=status if isinstance(status, str) else None)
        elif kind == "MessageEvent" and event.get("role") == "assistant":
            current_agent = current_agent or "tool_agent"
            touch_agent("tool_agent", event=event)

        if kind == "ActionEvent":
            last_action = event.get("action")
            if event.get("tool"):
                last_tool = event.get("tool")
        if kind == "ObservationEvent":
            last_tool = event.get("tool")
        if kind == "ErrorEvent":
            last_error = event
        if kind == "UserDirectiveEvent" and isinstance(event.get("directive"), dict):
            directives.append(event["directive"])

    if process and process.get("status") == "running":
        current_status = "running"
    elif summary and summary.get("status"):
        current_status = str(summary.get("status"))
    elif current_status is None:
        current_status = "waiting_for_events" if not events else "active"

    if current_agent and current_agent in agents:
        agents[current_agent]["active"] = bool(process and process.get("status") == "running")

    metrics = dict((summary or {}).get("metrics") or {})
    if process:
        metrics.setdefault("process_status", process.get("status"))
        metrics.setdefault("returncode", process.get("returncode"))

    return {
        "run_id": run_id,
        "status": current_status,
        "current_agent": current_agent,
        "step": current_step or metrics.get("steps"),
        "last_action": last_action,
        "last_tool": last_tool,
        "last_error": last_error,
        "agents": list(agents.values()),
        "status_counts": status_counts,
        "directives": directives,
        "metrics": metrics,
        "event_count": len(events),
        "latest_event": events[-1] if events else None,
        "timeline": [
            {
                "sequence": event.get("sequence"),
                "timestamp": event.get("timestamp"),
                "kind": event.get("kind"),
                "status": event.get("status"),
                "node": event.get("node"),
                "tool": event.get("tool"),
                "summary": summarize_event(event),
            }
            for event in events[-200:]
        ],
    }


@dataclass
class ManagedProcess:
    run_id: str
    mode: str
    prompt_path: Path
    command: list[str]
    control_dir: Path
    stdout_path: Path
    process: subprocess.Popen[str]
    started_at: str = field(default_factory=utc_now)
    stdout_tail: deque[str] = field(default_factory=lambda: deque(maxlen=600))
    finished_at: str | None = None

    def status(self) -> str:
        return "running" if self.process.poll() is None else "finished"

    def returncode(self) -> int | None:
        return self.process.poll()

    def snapshot(self) -> dict[str, Any]:
        if self.finished_at is None and self.process.poll() is not None:
            self.finished_at = utc_now()
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "status": self.status(),
            "returncode": self.returncode(),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "prompt_path": str(self.prompt_path),
            "control_dir": str(self.control_dir),
            "stdout_path": str(self.stdout_path),
            "command": self.command,
            "stdout_tail": list(self.stdout_tail)[-160:],
        }


class ProcessManager:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.processes: dict[str, ManagedProcess] = {}

    def start_run(self, *, mode: str, prompt: str, max_steps: int = 30) -> dict[str, Any]:
        if mode not in RUN_MODES:
            raise ValueError(f"Unsupported mode {mode!r}. Supported: {sorted(RUN_MODES)}")
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt is required.")
        run_id = build_run_id(mode)
        run_dir = AGENT_RUNS_DIR / run_id
        control_dir = run_dir / "control"
        stdout_path = run_dir / "process_stdout.log"
        PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        control_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = PROMPT_DIR / f"{run_id}.md"
        prompt_path.write_text(prompt + "\n", encoding="utf-8")
        command = build_command(mode, prompt_path, run_id, max_steps)
        env = os.environ.copy()
        env.update(
            {
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8",
                "AGENT_RUN_ID": run_id,
                "AGENT_RUNS_DIR": str(AGENT_RUNS_DIR),
                "ORCH_USER_CONTROL_DIR": str(control_dir),
                "LANGGRAPH_MAX_STEPS": str(max_steps),
            }
        )
        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        managed = ManagedProcess(
            run_id=run_id,
            mode=mode,
            prompt_path=prompt_path,
            command=command,
            control_dir=control_dir,
            stdout_path=stdout_path,
            process=process,
        )
        with self.lock:
            self.processes[run_id] = managed
        threading.Thread(target=self._read_stdout, args=(managed,), daemon=True).start()
        return managed.snapshot()

    def _read_stdout(self, managed: ManagedProcess) -> None:
        managed.stdout_path.parent.mkdir(parents=True, exist_ok=True)
        with managed.stdout_path.open("a", encoding="utf-8") as handle:
            if managed.process.stdout is not None:
                for line in managed.process.stdout:
                    managed.stdout_tail.append(line.rstrip("\n"))
                    handle.write(line)
                    handle.flush()
        managed.process.wait()
        managed.finished_at = utc_now()

    def get(self, run_id: str) -> ManagedProcess | None:
        with self.lock:
            return self.processes.get(run_id)

    def snapshots(self) -> list[dict[str, Any]]:
        with self.lock:
            items = [process.snapshot() for process in self.processes.values()]
        return sorted(items, key=lambda item: str(item.get("started_at", "")), reverse=True)

    def stop(self, run_id: str) -> dict[str, Any]:
        process = self.get(run_id)
        if process is None:
            raise KeyError(f"Run is not managed by this UI server: {run_id}")
        if process.process.poll() is None:
            process.process.terminate()
            try:
                process.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.process.kill()
                process.process.wait(timeout=5)
        process.finished_at = utc_now()
        return process.snapshot()


MANAGER = ProcessManager()


class ProcessDashboardHandler(BaseHTTPRequestHandler):
    server_version = "ProcessDashboard/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _send_json(self, value: Any, status: int = 200) -> None:
        payload = json.dumps(value, ensure_ascii=False, indent=2, default=json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, value: str, *, content_type: str = "text/plain; charset=utf-8", status: int = 200) -> None:
        payload = value.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")
        return payload

    def _serve_static(self, path: str) -> None:
        if path == "/":
            target = STATIC_DIR / "index.html"
        else:
            relative = unquote(path.lstrip("/"))
            target = (STATIC_DIR / relative).resolve()
            if not str(target).startswith(str(STATIC_DIR.resolve())):
                self._send_json({"error": "Invalid static path."}, status=HTTPStatus.FORBIDDEN)
                return
        if not target.exists() or not target.is_file():
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            return
        suffix = target.suffix.lower()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
        }.get(suffix, "application/octet-stream")
        self._send_text(target.read_text(encoding="utf-8"), content_type=content_type)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/health":
                self._send_json(
                    {
                        "ok": True,
                        "project_dir": str(PROJECT_DIR),
                        "runs_dir": str(AGENT_RUNS_DIR),
                        "modes": sorted(RUN_MODES),
                        "processes": MANAGER.snapshots(),
                    }
                )
                return
            if parsed.path == "/api/runs":
                query = parse_qs(parsed.query)
                limit = int((query.get("limit") or ["50"])[0])
                runs = load_runs(str(AGENT_RUNS_DIR))[:limit]
                managed = {item["run_id"]: item for item in MANAGER.snapshots()}
                for run in runs:
                    if run.get("run_id") in managed:
                        run["process"] = managed[run["run_id"]]
                for run_id, process in managed.items():
                    if not any(run.get("run_id") == run_id for run in runs):
                        runs.insert(
                            0,
                            {
                                "run_id": run_id,
                                "status": process.get("status"),
                                "metrics": {},
                                "events_path": str(AGENT_RUNS_DIR / run_id / "events.jsonl"),
                                "summary_path": str(AGENT_RUNS_DIR / run_id / "summary.json"),
                                "process": process,
                            },
                        )
                self._send_json({"runs": runs[:limit], "processes": MANAGER.snapshots()})
                return
            if parsed.path.startswith("/api/runs/"):
                parts = [part for part in parsed.path.split("/") if part]
                if len(parts) == 3:
                    self._send_json(self._run_payload(parts[2]))
                    return
                if len(parts) == 4 and parts[3] == "events":
                    query = parse_qs(parsed.query)
                    limit = int((query.get("limit") or ["400"])[0])
                    events = read_jsonl(AGENT_RUNS_DIR / safe_run_id(parts[2]) / "events.jsonl", limit=limit)
                    self._send_json({"events": events})
                    return
            self._serve_static(parsed.path)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/runs":
                body = self._read_body()
                max_steps = max(1, min(300, int(body.get("max_steps") or 30)))
                process = MANAGER.start_run(
                    mode=str(body.get("mode") or "root"),
                    prompt=str(body.get("prompt") or ""),
                    max_steps=max_steps,
                )
                self._send_json({"process": process}, status=HTTPStatus.CREATED)
                return
            if parsed.path.startswith("/api/runs/"):
                parts = [part for part in parsed.path.split("/") if part]
                if len(parts) == 4 and parts[3] == "directives":
                    run_id = safe_run_id(parts[2])
                    body = self._read_body()
                    text = str(body.get("text") or "").strip()
                    if not text:
                        raise ValueError("Directive text is required.")
                    control_dir = AGENT_RUNS_DIR / run_id / "control"
                    payload = {
                        "text": text,
                        "source": "process_ui",
                        "sent_at": utc_now(),
                    }
                    append_jsonl(control_dir / "inbox.jsonl", payload)
                    append_jsonl(control_dir / "ui_directives.jsonl", payload)
                    self._send_json({"ok": True, "run_id": run_id, "directive": payload})
                    return
                if len(parts) == 4 and parts[3] == "stop":
                    self._send_json({"process": MANAGER.stop(safe_run_id(parts[2]))})
                    return
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except KeyError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _run_payload(self, raw_run_id: str) -> dict[str, Any]:
        run_id = safe_run_id(raw_run_id)
        run_dir = AGENT_RUNS_DIR / run_id
        events = read_jsonl(run_dir / "events.jsonl", limit=1000)
        summary = read_json(run_dir / "summary.json")
        process = MANAGER.get(run_id)
        process_snapshot = process.snapshot() if process else None
        control_dir = run_dir / "control"
        directives = read_jsonl(control_dir / "user_directives.jsonl", limit=200)
        ui_directives = read_jsonl(control_dir / "ui_directives.jsonl", limit=200)
        state = derive_run_state(run_id, events, summary, process_snapshot)
        state["directives_from_files"] = directives
        state["ui_directives"] = ui_directives
        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "summary": summary,
            "process": process_snapshot,
            "state": state,
            "events": events[-400:],
            "stdout": tail_text(run_dir / "process_stdout.log"),
            "control": {
                "control_dir": str(control_dir),
                "inbox_path": str(control_dir / "inbox.jsonl"),
            },
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local process dashboard UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Print browser URL only; opening is handled by the caller.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    UI_STATE_DIR.mkdir(parents=True, exist_ok=True)
    port = find_open_port(args.port)
    server = ThreadingHTTPServer((args.host, port), ProcessDashboardHandler)
    SERVER_INFO_PATH.write_text(
        json.dumps(
            {
                "url": f"http://{args.host}:{port}",
                "host": args.host,
                "port": port,
                "pid": os.getpid(),
                "started_at": utc_now(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Process dashboard: http://{args.host}:{port}", flush=True)

    def shutdown(signum: int, frame: Any) -> None:
        raise KeyboardInterrupt

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
