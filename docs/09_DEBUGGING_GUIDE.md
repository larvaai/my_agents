# Debugging Guide

## Debug Order

Khi một run lỗi, đọc theo thứ tự:

1. Terminal output.
2. `var/test_runs/<timestamp>/<case>.log`.
3. `var/agent_runs/<run_id>/events.jsonl`.
4. `var/agent_runs/<run_id>/summary.json`.
5. Source code của tool/orchestrator liên quan.

Useful commands:

```powershell
python inspect_runs.py list
python inspect_runs.py events latest --limit 50
python inspect_runs.py summary latest
```

## JsonGate Error

Triệu chứng:

```text
json_gate_error
JSON_GATE_FAILED
Failed stage: parse | action_schema | tool_resolve | tool_args | dry_run
```

Cách đọc:

- `parse`: raw output không thành JSON sau repair.
- `action_schema`: thiếu `action`, `tool`, `args`, hoặc `message`.
- `tool_resolve`: tool không tồn tại hoặc ambiguous.
- `tool_args`: args sai schema.
- `dry_run`: path/command/policy unsafe.

Cách xử lý:

1. Xem `AGENT RAW OUTPUT`.
2. Xem `Sandbox error`.
3. Nếu lỗi do schema thiếu, sửa prompt/tool example.
4. Nếu lỗi do tool unknown, thêm tool vào `features/mcp_tools/config.py` hoặc sửa agent prompt.
5. Nếu lỗi do dry-run, kiểm tra path, terminal argv, git policy.

Smoke:

```powershell
python run_json_gate_smoke.py
```

## Tool Args Sai Schema

Triệu chứng:

```text
schema_error: true
Missing required argument
Invalid type for server.tool.arg
Unexpected argument
```

Cách xử lý:

- Đọc schema trong `features/mcp_tools/schemas.py`.
- Đọc examples trong `features/mcp_tools/client.py`.
- Đảm bảo agent dùng `server.tool_name`.
- Nếu MCP mới chưa có schema, thêm schema.

## Role Tool Blocked

Triệu chứng:

```text
policy_code: role_tool_not_allowed
is not allowed to call ...
```

Cách xử lý:

- Kiểm tra `agents/role_agents.py`.
- Xác định đúng role nào nên sở hữu tool.
- Không mở quyền rộng nếu task chỉ cần handoff role.
- Chạy:

```powershell
python run_agent_role_smoke.py
```

## Failed-Test Repair Loop

Triệu chứng:

```text
last_failure
repair_attempts
repair_requires_patch_tool
```

Ý nghĩa:

- Test Agent chạy validation fail.
- Orchestrator tóm tắt failure.
- Code Agent phải patch nhỏ đúng file fail.
- Whole-file rewrite bị block nếu đang repair.

Cách xử lý:

1. Xem `last_failure.file`, `line`, `error`.
2. View vùng file fail.
3. Patch bằng `file_editor_str_replace` hoặc `file_editor_insert`.
4. Handoff lại Test.

## Finish Gate Blocked

Triệu chứng:

```text
finish_gate_blocked
Blocked by finish gate
Validation is required
```

Ý nghĩa:

- Agent đã sửa code hoặc prompt yêu cầu validation.
- Chưa có test pass thật trong `tests_run`.

Cách xử lý:

- Test Agent chạy validation hẹp:

```text
python.run_python
lint_test.test_python_file
lint_test.lint_compile
```

- Nếu dependency lỗi, final phải là blocker rõ.

## Repeated Tool Call

Triệu chứng:

```text
agent_stuck
Same tool call repeated too many times
```

Cách xử lý:

- Đọc tool result lần đầu.
- Không retry cùng args.
- Đổi giả thuyết hoặc báo blocker.
- Nếu schema/tool bug thật, sửa MCP hoặc prompt examples.

## Python MCP Timeout

Triệu chứng:

```text
Python execution timed out after ...
```

Nguyên nhân thường gặp:

- Script loop vô hạn.
- Test chờ input.
- Import side effect treo.
- Test quá rộng.

Cách xử lý:

- Chạy `lint_test.lint_compile` trước.
- Tạo probe nhỏ.
- Chạy file hẹp nhất.
- Giảm timeout chỉ khi đã hiểu vì sao.

## RAG Lỗi

Triệu chứng:

- `rag.rag_health` fail.
- Search không có hit.
- Hit sai source.

Cách xử lý:

1. Bật Qdrant.
2. Gọi `rag.rag_health`.
3. Ingest file/folder cụ thể.
4. Kiểm tra source file có nội dung.
5. Điều chỉnh `score_threshold`.

## Docker/Playwright Dependency Failure

Triệu chứng:

```text
dependency_failure: true
Command not found
browser not installed
```

Cách xử lý:

- Docker: mở Docker Desktop.
- Playwright:

```powershell
python -m playwright install chromium
```

- Nếu task không bắt buộc, báo dependency blocker thay vì sửa code.

## LM Studio Lỗi

Triệu chứng:

```text
LLM request failed
connection refused
model not found
```

Cách xử lý:

1. Mở LM Studio.
2. Load model.
3. Bật OpenAI-compatible server.
4. Kiểm tra env:

```powershell
$env:LLM_BASE_URL
$env:LLM_MODEL
```

## Debug Checklist

Trước khi sửa code:

- Lỗi nằm ở agent output, tool schema, policy, dependency, hay code logic?
- Có event log không?
- Có tool result đầy đủ không?
- Có reproduction hẹp không?
- Có validation pass/fail thật không?

Sau khi sửa:

```powershell
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_langgraph_smoke.py
```
