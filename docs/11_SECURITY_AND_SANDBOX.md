# Security And Sandbox

## Security Model

Prompt rules không phải security boundary. Project dùng nhiều lớp chặn:

```text
role allowlist
  -> JsonGate dry-run
  -> tool schema validation
  -> tool policy
  -> MCP server sandbox
  -> OS/process timeout
```

Không lớp nào hoàn hảo một mình. Các lớp phải cùng tồn tại.

## Workspace Boundary

Agent thao tác file trong:

```text
workspace/
```

Các MCP server local phải resolve path và chặn path escape.

Blocked:

- Absolute path ngoài workspace.
- `..` path traversal.
- Windows drive path như `C:\...`.
- Empty path.

JsonGate cũng dry-run path trước khi tool chạy.

## File Editing

Đường edit chính:

```text
file_editor.file_editor_view
file_editor.file_editor_create
file_editor.file_editor_write_lines
file_editor.file_editor_str_replace
file_editor.file_editor_insert
```

Không edit qua terminal.

Repair mode:

- Nếu có `last_failure`, Code Agent không được rewrite nguyên file đang fail.
- Phải dùng patch nhỏ.
- Whole-file rewrite bị block bằng policy code `repair_requires_patch_tool`.

## Terminal

Terminal MCP chỉ nhận argv list.

Allowed shape:

```json
{
  "argv": ["python", "-m", "py_compile", "main.py"],
  "timeout": 10,
  "cwd": ".",
  "purpose": "validate syntax"
}
```

Blocked by default:

- Shell strings.
- `cmd /c`, `powershell -Command`, `bash -c`.
- Shell control tokens.
- Destructive commands.
- Git mutations.
- Network download commands when unsafe.

High-risk terminal requires:

```powershell
$env:AGENT_ALLOW_HIGH_RISK_TERMINAL="1"
```

## Git

Read-only Git is allowed for Review:

- status
- diff
- log
- show
- branch list

Git mutation blocked by default:

- add
- commit
- reset
- checkout
- create branch

Opt-in only when user explicitly requests:

```powershell
$env:AGENT_ALLOW_GIT_MUTATIONS="1"
```

## Docker

Docker MCP exposes safe inspection by default:

- health
- ps
- compose ps
- compose logs

Compose up/stop are mutation and require:

```powershell
$env:DOCKER_MCP_ALLOW_MUTATION="1"
```

Delete/prune/rm/rmi/volume rm are not exposed.

## JsonGate Dry-Run

JsonGate blocks before execution:

- Unknown tool.
- Missing/wrong tool args.
- Unsafe path.
- Terminal not using argv.
- Git mutation policy.
- Content too large for one call.

This keeps bad JSON from becoming a real tool call.

## Role Boundaries

| Role | Important boundary |
|---|---|
| Code | Edits code, does not validate/approve in LangGraph split |
| Test | Validates, never edits source |
| Review | Reviews, never edits or mutates git |
| Ledger | Records/audits, never edits code or runs terminal |
| Final | Summarizes only |

## Secrets

Do not store secrets in:

- RAG
- Ledger
- Issues
- Obsidian notes
- Documents
- Event logs

Never intentionally ingest:

- `.env`
- API keys
- tokens
- passwords
- private credentials

## Network Tools

Network-capable MCPs:

- `fetch`
- `search`
- `playwright`
- `context7`

Use them for current/external information. Record source URLs when user needs attribution.

## MCP Server Checklist

Every new MCP should have:

- Input schema.
- Output shape.
- Error shape.
- Risk metadata.
- Path sandbox if touching files.
- Timeout if running process/network.
- No arbitrary shell.
- No destructive operation without policy.
- Success test.
- Blocked/failure test.

## Security Smoke Commands

```powershell
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_mcp_chain_smoke.py
```

These catch common regressions in JSON safety, role permission, and tool chain behavior.
