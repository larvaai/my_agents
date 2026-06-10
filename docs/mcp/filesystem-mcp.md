# Filesystem MCP

## Purpose

Filesystem MCP đọc/ghi/list/search file trong workspace sandbox.

## Server

- Server name: `filesystem`
- Package: `@modelcontextprotocol/server-filesystem`
- Transport: stdio
- Sandbox: `workspace/`
- Config: `tools/mcp_config.py`

## Common Tools

| Tool | Dùng để |
|---|---|
| `filesystem.read_file` | Đọc file |
| `filesystem.write_file` | Ghi file |
| `filesystem.list_directory` | List folder |
| `filesystem.search_files` | Tìm file |
| `filesystem.directory_tree` | Cây thư mục |

## Safety

- Path được normalize về `workspace/`.
- Không dùng Filesystem MCP cho edit tinh vi nếu có thể dùng File Editor MCP.
- Khi sửa code, ưu tiên `file_editor.*` để audit rõ hơn.

## Test

```powershell
python run_all_cases.py --case project_01_filesystem_python --fail-fast
python run_mcp_chain_smoke.py
```

## Khi Không Dùng

- Không dùng để chạy command.
- Không dùng để đọc ngoài workspace.
- Không dùng thay Git MCP để xem diff.

