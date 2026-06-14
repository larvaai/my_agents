# Process Dashboard UI

The Process Dashboard is a local web UI for watching and controlling agent
runs. It is intentionally dependency-light: the backend uses Python stdlib HTTP
server APIs, and the frontend is static HTML/CSS/JS.

## Run It

```powershell
python run_process_ui.py --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

If port `8765` is busy, the server selects another open port and writes it to:

```text
var/process_ui/server.json
```

## What It Can Do

- Start a root orchestrator run with User Agent Control enabled.
- Start a LangGraph run and inspect its event log.
- Send live User Agent directives into a selected run.
- Stop a process that was started by the UI.
- Show active/recent runs from `var/agent_runs/`.
- Show current status, current agent/node, step count, metrics, timeline, stdout,
  and directive history.

## Runtime Paths

UI server:

```text
run_process_ui.py
```

Frontend:

```text
ui/process_dashboard/index.html
ui/process_dashboard/styles.css
ui/process_dashboard/app.js
```

Generated UI state:

```text
var/process_ui/
  server.json
  prompts/
```

Agent logs:

```text
var/agent_runs/<run_id>/
  events.jsonl
  summary.json
  process_stdout.log
  control/
    inbox.jsonl
    ui_directives.jsonl
    user_directives.jsonl
    accepted_directives.jsonl
    rejected_directives.jsonl
```

## User Agent Input

For root orchestrator runs, the UI starts:

```text
python main.py --user-control-dir var/agent_runs/<run_id>/control --max-steps <n> <prompt-file>
```

When you send a directive from the UI, it appends:

```json
{"text": "Trong lượt chạy này không cần vai trò của critic agent, lượt sau vẫn cần.", "source": "process_ui"}
```

to:

```text
var/agent_runs/<run_id>/control/inbox.jsonl
```

The root User Agent consumes that inbox. If a directive arrives while the model
is running, the old model output is marked stale and the next agent step gets a
`USER AGENT LIVE DIRECTIVES` prompt block.

LangGraph runs are observable in this UI. Dynamic LangGraph graph mutation from
live directives is not implemented yet; that is the next integration step.

## API

```text
GET  /api/health
GET  /api/runs
GET  /api/runs/<run_id>
GET  /api/runs/<run_id>/events
POST /api/runs
POST /api/runs/<run_id>/directives
POST /api/runs/<run_id>/stop
```

Start run:

```json
{
  "mode": "root",
  "prompt": "Question...",
  "max_steps": 30
}
```

Supported modes:

```text
root
langgraph
```

## Tests

```powershell
python -m unittest tests.test_process_ui
python -m unittest tests.test_user_agent_control
```

Full test suite:

```powershell
python -m unittest discover -s tests
```
