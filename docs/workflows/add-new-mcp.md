# Workflow: Add New MCP

## Goal

Thêm một MCP mới mà không phá protocol, sandbox, test runner.

## Steps

1. Xác định purpose và risk.
2. Tạo server nhỏ trong `mcp_servers/<name>_server.py`.
3. Mỗi tool trả dict có `ok`, `tool`, và `error` khi fail.
4. Thêm server vào `MCP_SERVERS` trong `tools/mcp_config.py`.
5. Thêm tool names vào `MCP_TOOL_NAMES`.
6. Thêm alias vào `TOOL_ALIASES` nếu cần.
7. Thêm schema vào `tools/tool_schemas.py`.
8. Thêm examples vào `tools/mcp_client.build_tool_prompt()`.
9. Thêm prompt case vào `run_all_cases.py`.
10. Nếu là core path, thêm deterministic smoke vào `run_mcp_chain_smoke.py`.
11. Viết docs trong `docs/mcp/` hoặc `future-mcps.md`.
12. Chạy validation.

## Validation

```powershell
python -m py_compile mcp_servers\<name>_server.py tools\mcp_config.py tools\tool_schemas.py tools\mcp_client.py
python run_mcp_chain_smoke.py
python run_all_cases.py --case <new_case> --fail-fast
```

## Safety Checklist

- Path sandbox rõ.
- Timeout rõ.
- Max output/input size.
- Không shell tự do.
- Không destructive actions không có opt-in.
- Schema guard pass.
- Blocked/failure path có test.

## Template

Xem:

```text
docs/templates/mcp-server-template.md
```

