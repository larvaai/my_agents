# MCP System

## MCP Trong Project Này

MCP là lớp tool runtime. Agent không gọi Python function trực tiếp. Agent chỉ trả JSON action, orchestrator route qua MCP client.

```text
agent JSON action
  -> JsonGate
  -> tools/tool_registry.call_tool()
  -> tools/mcp_client.call_mcp_tool()
  -> resolve tool
  -> validate schema
  -> policy check
  -> MCP stdio server
  -> normalized tool result
```

## Files

| File | Vai trò |
|---|---|
| `tools/mcp_config.py` | MCP server config, tool names, aliases |
| `tools/mcp_client.py` | Resolve, validate, start stdio, call tool |
| `tools/tool_registry.py` | Orchestrator-facing call interface |
| `tools/tool_schemas.py` | Hard schema, output, error, metadata |
| `tools/tool_policy.py` | Hard policy như block git mutation |
| `mcp_servers/*.py` | Local MCP server implementations |

## Tool Protocol

Tool call luôn là:

```json
{
  "action": "tool",
  "tool": "server.tool_name",
  "args": {}
}
```

Tool result luôn cố gắng có:

```json
{
  "ok": true,
  "server": "server",
  "tool": "tool_name"
}
```

Nếu lỗi:

```json
{
  "ok": false,
  "error": "...",
  "schema_error": true,
  "policy_blocked": true,
  "policy_code": "..."
}
```

## MCP Servers Hiện Có

| Server | Nhóm chức năng | Ghi chú |
|---|---|---|
| `filesystem` | Read/write/list/search workspace | External MCP, sandbox theo workspace |
| `file_editor` | View/create/write_lines/str_replace/insert | Đường edit chính, dễ audit |
| `python` | Run Python file | Workspace-only, timeout |
| `lint_test` | Compile, ruff, Python test, smoke suite | Preferred validation |
| `terminal` | Safe argv command runner | Có security_risk metadata |
| `git` | Status/diff/log/show/branch | Mutation bị policy block mặc định |
| `code_index` | Symbol/reference/dependency graph | Read-only code understanding |
| `rag` | Qdrant ingest/search | Workspace knowledge |
| `fetch` | Fetch URL | Một URL mỗi call |
| `search` | Web search | Brave/Tavily/fallback |
| `document` | Extract/write/append/outline docs | Workspace documents |
| `pdf_text_extraction` | Extract PDF/text content | Read-only, workspace-bound |
| `ledger` | Append-only run memory | Audit and decisions |
| `playwright` | Browser text/screenshot | UI/browser verification |
| `docker` | Docker ps/logs/compose gated ops | Mutations opt-in |
| `obsidian` | Local markdown vault | Notes/knowledge |
| `issue` | Local SQLite issue tracker | Bugs, tasks, risks |
| `context7` | Library docs lookup | External docs |

## File Editor MCP

File editing nên đi qua:

- `file_editor.file_editor_view`
- `file_editor.file_editor_create`
- `file_editor.file_editor_write_lines`
- `file_editor.file_editor_str_replace`
- `file_editor.file_editor_insert`

`file_editor_write_lines` được thêm để tránh JSON string dài dễ vỡ khi tạo file lớn.

Rule:

- Tạo file mới: `file_editor_create` hoặc `file_editor_write_lines`.
- Sửa file đang fail test: `file_editor_str_replace` hoặc `file_editor_insert`.
- Không dùng terminal để edit file.

## Terminal MCP

Terminal chỉ nhận argv list:

```json
{
  "tool": "terminal.terminal_run",
  "args": {
    "argv": ["python", "-m", "py_compile", "main.py"],
    "timeout": 10,
    "cwd": ".",
    "purpose": "validate syntax"
  }
}
```

Không dùng shell string. Không dùng `cmd /c`, `powershell -Command`, `bash -c` qua agent.

Terminal result có metadata:

- summary
- security_risk
- blocked reason nếu có

## Schema

Mọi tool quan trọng có schema trong `tools/tool_schemas.py`.

Schema gồm:

- `name`
- input args
- output shape
- errors
- metadata

Metadata nên có:

- `category`
- `risk`
- `read_only`
- `changes_file`
- `validation`
- `sandbox`

## Policy

`tools/tool_policy.py` là hard boundary.

Hiện có:

- Git mutation blocked mặc định.
- Terminal high-risk controlled by env.
- Docker mutation controlled by env.
- Path safety trong MCP server và JsonGate dry-run.

## Add New MCP Checklist

1. Tạo server trong `mcp_servers/` hoặc external MCP config.
2. Thêm `MCP_SERVERS` trong `tools/mcp_config.py`.
3. Thêm tool names vào `MCP_TOOL_NAMES`.
4. Thêm alias nếu cần vào `TOOL_ALIASES`.
5. Thêm schema vào `tools/tool_schemas.py`.
6. Thêm examples/prompt trong `tools/mcp_client.py`.
7. Thêm role allowlist trong `agents/role_agents.py`.
8. Thêm smoke deterministic nếu core.
9. Thêm prompt case trong `run_all_cases.py`.
10. Cập nhật docs `docs/mcp/`.

## Current Design Rule

MCP là capability. Skill là workflow instruction. Agent role là permission boundary. JsonGate là output contract. Không trộn bốn thứ này.
