# Safety Department

Phase 6 adds a deterministic Safety Department for Global Supervisor plans.

Current files:

```text
agents/safety/permission_agent.py
agents/safety/risk_agent.py
agents/safety/prompt_injection_agent.py
agents/safety/tool_scope_agent.py
agents/safety/department.py
```

Responsibilities:

- Permission Agent: reports when code execution or network research is being
  delegated because the current supervisor mode has not enabled those actions.
- Risk Agent: classifies route risk from repo, code, network, and agent-factory
  needs.
- Prompt Injection Agent: blocks obvious instruction override or secret
  exfiltration language before dispatch.
- Tool Scope Agent: validates department-level boundaries in the execution plan.

Current hard rules:

- Knowledge Department cannot write files.
- Research Department cannot modify repo files.
- Coding Department is delegated unless `run_coding=True`.
- Network research stays deterministic unless `research_use_tools=True`.
- Unknown departments in an execution plan are blocked.

Smoke:

```powershell
python run_global_supervisor_smoke.py
```

Expected marker:

```text
GLOBAL_SUPERVISOR_STAGE_1_6_SMOKE_OK
```
