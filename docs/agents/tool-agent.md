# Tool Agent

## Role

Tool Agent là agent đang chạy thật trong project. Nó nhận message history, system prompt, danh sách MCP tools, skills, rồi trả JSON action.

## Implementation

- File: `agents/tool_agent.py`
- Base class: `agents/base_agent.py`
- Registry key: `tool` in `agents/role_agents.py`
- LLM call: `llm.call_llm()`
- System prompt: `prompts/system_prompt.md`
- Tool prompt: `features/mcp_tools/client.py`
- Skills prompt: `tools/skill_loader.build_skills_prompt()`

## Allowed Output

Tool:

```json
{
  "action": "tool",
  "plan": "brief observable plan",
  "tool": "server.tool_name",
  "args": {}
}
```

Final:

```json
{
  "action": "final",
  "finish_reason": "validated",
  "message": "..."
}
```

## Responsibilities

- Hiểu request.
- Chọn tool đúng.
- Đọc tool result.
- Sửa call khi schema/tool lỗi.
- Chạy validation sau code edit.
- Final rõ ràng, không bịa.
- Giữ backward compatibility cho orchestrator hiện tại.

## Non-responsibilities

- Không trực tiếp chạy shell.
- Không tự bypass MCP.
- Không commit/push trừ khi user yêu cầu và policy cho phép.
- Không giữ memory ngoài logs/ledger/issue/RAG.

## Tests

```powershell
python run_all_cases.py --case orchestrator_01_json_only --fail-fast
python run_all_cases.py --case agent_01_fix_small_bug --fail-fast
```
