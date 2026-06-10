# Base Agent

## Purpose

`BaseAgent` là nền chung cho mọi role agent. Nó không chạy tool trực tiếp; nó build role prompt, gọi LLM, và chặn tool call ngoài allowlist trước khi output quay về orchestrator hoặc scheduler tương lai.

## Implementation

- File: `agents/base_agent.py`
- Registry: `agents/role_agents.py`
- Backward-compatible Tool Agent: `agents/tool_agent.py`

## Interface

```python
BaseAgent(
    name="Code Agent",
    role="Implement narrowly scoped source changes.",
    system_prompt="...",
    allowed_tools=("file_editor.*", "lint_test.*"),
    allowed_skills=("code-edit", "run-test"),
)
```

## Responsibilities

- Build role-specific system prompt.
- Inject allowed tools and allowed skills.
- Call LLM.
- Validate returned tool call against role permission.
- Describe role metadata for smoke tests/docs.

## Non-responsibilities

- Does not execute tools.
- Does not schedule multi-agent work.
- Does not replace MCP runtime policy.

## Tests

```powershell
python run_agent_role_smoke.py
```

