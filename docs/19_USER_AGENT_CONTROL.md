# User Agent Control

User Agent Control lets the human user send live directives while the root
orchestrator is running. The first implementation is wired into the root
single-agent path:

```text
python main.py ...
  -> orchestrator.py
  -> agents/user_agent.py
  -> agents/tool_agent.py
```

## Why This Exists

Normal agent flow starts from one prompt and then continues autonomously. In
real work, the user may need to interrupt:

- Stop optional work and answer now.
- Make the answer shorter.
- Retry the current step.
- Ask for a different tool or skill.
- Ask to add, skip, or remove an agent.
- Correct the task while the model is still running.

The user directive has higher application-level priority than agent suggestions,
default routing, and the previous run plan.

## Authority Order

```text
1. Runtime invariants
2. Latest accepted live user directive
3. Original user prompt
4. Current run plan
5. Agent role/system prompt
6. Agent-to-agent suggestion
7. Heuristics and defaults
```

Runtime invariants cannot be disabled:

- Event log stays on unless the run was started with logging disabled.
- The orchestrator records accepted/rejected directives.
- Agents must not fabricate unavailable tools or skills.
- The system must not claim to expose hidden internal chain-of-thought.
- The root answer loop still follows the JSON action protocol.

## Current Implementation

Implemented files:

```text
agents/user_agent.py
orchestrator.py
main.py
tests/test_user_agent_control.py
```

Current behavior:

- `agents/user_agent.py` parses live user text into structured directives.
- `orchestrator.py` polls directives before agent calls, after agent calls, and
  after tool results.
- If a directive arrives while `tool_agent(...)` is running, the returned output
  is marked stale and not parsed.
- The next agent call receives a high-priority `USER AGENT LIVE DIRECTIVES`
  message.
- `force_final` directives add an explicit instruction to return final JSON now.
- Directives are logged as `UserDirectiveEvent` entries.

This is phase 1: checkpoint interrupt. It does not cancel the in-flight HTTP LLM
request. It accepts the user input while the model runs, then applies it as soon
as the call returns.

## CLI Usage

Interactive stdin mode:

```powershell
python main.py --interactive-user-agent prompts/user_prompt.md
```

While the model is running, type a directive and press Enter:

```text
Dung lai, tra loi ngay va ngan gon.
```

File inbox mode:

```powershell
python main.py --user-control-dir var/live_control prompts/user_prompt.md
```

Append JSONL while the run is active:

```powershell
Add-Content var/live_control/inbox.jsonl '{"text":"Tra loi ngan hon va dung tool search neu co."}'
```

Or write a text file:

```powershell
New-Item -ItemType Directory -Force var/live_control/inbox
Set-Content var/live_control/inbox/001.txt "Dung lai, tra loi ngay."
```

Current-run-only flow change:

```powershell
Add-Content var/live_control/inbox.jsonl '{"text":"Trong lượt chạy này không cần vai trò của critic agent, lượt sau vẫn cần."}'
```

Expected interpretation:

```json
{
  "scope": "current_run",
  "intent": "modify_flow",
  "operations": [
    {
      "op": "remove_or_skip_agent",
      "target": "critic agent",
      "mode": "skip_current_run_only"
    }
  ]
}
```

This does not remove the role from future runs. It only asks the active run to
skip that role if the current runtime supports it; otherwise the agent must say
that the role cannot be removed in this path.

Environment variable mode:

```powershell
$env:ORCH_USER_CONTROL_DIR="var/live_control"
$env:ORCH_USER_AGENT_INTERACTIVE="1"
python main.py prompts/user_prompt.md
```

## Directive Shape

Each live message becomes a directive:

```json
{
  "directive_id": "userdir_0001",
  "raw_text": "Dung lai, tra loi ngay.",
  "source": "control_dir",
  "priority": "user_live",
  "scope": "current_run",
  "intent": "flow_control",
  "operations": [
    {
      "op": "force_final",
      "mode": "synthesize_now"
    }
  ],
  "status": "accepted",
  "notes": []
}
```

Supported operation families:

```text
force_final
retry_step
remove_or_skip_agent
add_agent
request_tool
request_skill
answer_style
answer_instruction
blocked_request
```

## Output And Logs

Normal event logs still live under:

```text
var/agent_runs/<run_id>/
  events.jsonl
  summary.json
  control/
    inbox.jsonl
    user_directives.jsonl
    accepted_directives.jsonl
    rejected_directives.jsonl
    inbox/
```

When a directive arrives during an agent call, events include:

```text
UserDirectiveEvent
StateEvent status=agent_output_marked_stale_by_user_directive
StateEvent status=user_directives_applied
```

Summary metrics include:

```text
user_directives
user_interruptions
stale_agent_outputs
```

## What Is Not Implemented Yet

Not implemented in phase 1:

- Hard cancellation of an in-flight LLM HTTP request.
- Dynamic add/remove of nodes in LangGraph.
- Installing new tools or skills while a run is active.
- Persistent source-code mutation from a live directive.

For now, add/remove agent and tool/skill requests are turned into high-priority
runtime instructions. If the active path cannot actually add that agent/tool, it
must say so instead of pretending.

## Tests

Run the targeted tests:

```powershell
python -m unittest tests.test_user_agent_control
```

Run with the broader root tests:

```powershell
python -m unittest tests.test_user_agent_control tests.test_mini_repo_registry
```

## Next Step

The next implementation should reuse `agents/user_agent.py` inside
`orchestration/langgraph_orchestrator.py` so live directives can skip/retry
department nodes directly:

```text
UserDirectiveEvent
  -> AgentState.active_user_directives
  -> route_next(...)
  -> skip/retry/add approved nodes
```
