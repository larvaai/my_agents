# <MCP Name>

## Purpose

MCP này dùng để làm gì?

## Server

- Server name:
- File/package:
- Transport: stdio
- Sandbox:
- Env:

## Tools

| Tool | Args | Output | Notes |
|---|---|---|---|
| `<server>.<tool>` | `{}` | `ok`, ... | ... |

## Input Schema

Định nghĩa trong:

```text
tools/tool_schemas.py
```

## Safety Rules

- ...
- ...

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| ... | ... | ... |

## Tests

```powershell
python -m py_compile mcp_servers\<name>_server.py
python run_all_cases.py --case <case> --fail-fast
```

## When To Use

- ...

## When Not To Use

- ...

