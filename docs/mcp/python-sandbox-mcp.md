# Python Sandbox MCP

## Purpose

Python Sandbox MCP chạy file `.py` trong workspace với timeout và stdout/stderr rõ ràng.

## Server

- Server name: `python`
- File: `mcp_servers/python_sandbox.py`
- Transport: stdio
- Sandbox: `var/workspace/`

## Tools

| Tool | Args | Output chính |
|---|---|---|
| `python.run_python` | `path`, `timeout` | `ok`, `stdout`, `stderr`, `returncode` |
| `python.python_probe` | `timeout` | kiểm subprocess Python |

## Safety

- Chỉ chạy `.py`.
- Chỉ path trong workspace.
- Timeout tối đa trong server.
- `stdin=subprocess.DEVNULL` để tránh chờ input.

## Test

```powershell
python run_all_cases.py --case project_00_python_probe --fail-fast
python run_all_cases.py --case project_01_filesystem_python --fail-fast
```

## Common Errors

| Error | Nguyên nhân | Fix |
|---|---|---|
| File does not exist | Path sai hoặc ngoài workspace | Dùng path workspace-relative |
| Only .py files can be executed | File không phải Python | Chạy tool khác |
| timed out | Script treo/chờ input | Dùng probe hoặc test hẹp hơn |
