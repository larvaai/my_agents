# Agent Protocol

Protocol này là hợp đồng giữa LLM và orchestrator. Nếu agent phá protocol, JsonGate hoặc tool schema sẽ chặn trước khi tool chạy.

## JSON-only Output

Tool call:

```json
{
  "action": "tool",
  "plan": "short observable plan",
  "tool": "server.tool_name",
  "args": {}
}
```

Final:

```json
{
  "action": "final",
  "finish_reason": "validated|handoff|blocker",
  "message": "final result"
}
```

Rules:

- Không markdown.
- Không text ngoài JSON.
- Không nhiều object.
- JSON boolean phải là `true`/`false`, không phải Python `True`/`False`.
- Tool name nên dùng dạng `server.tool_name`.

## Adaptive Artifact Protocol For Long Analysis

Strict JSON is still the rule for tool calls and final control messages.
However, long business/product/domain analysis should not be stuffed into one
large JSON string.

For Software Factory v0.7, agents write long content into artifacts and return a
small JSON-compatible envelope:

```json
{
  "agent": "Business Logic Model Agent",
  "decision": "artifact_created",
  "artifact_refs": [
    {
      "path": "var/workspace/factory_runs/<run_id>/08_business_logic_model.md",
      "kind": "business_logic_model",
      "sha256": "..."
    }
  ],
  "route": {
    "next_agent": "Business Logic Validator Agent"
  }
}
```

Use this rule:

- Coding/tool actions: strict JSON, short fields, schema validated by JsonGate.
- Business/spec/docs analysis: write Markdown or JSON artifact, then pass only
  references in the control envelope.
- Pattern decisions: allowed only after Domain Analysis has explicit change
  hotspots.
- Final status: may summarize artifacts, but must not inline whole artifacts.

## JsonGate

Mọi output agent đi qua `output_gate.JsonGate`.

Pipeline:

```text
raw output
  -> extract JSON
  -> deterministic repair
  -> action schema check
  -> tool resolve
  -> tool args schema check
  -> dry-run safety check
  -> pass hoặc structured retry error
```

JsonGate sửa deterministic trước:

- Markdown fence.
- Text thừa.
- Trailing comma.
- Python literal.
- Key đơn giản chưa quote.
- Alias an toàn như `tool_name`, `arguments`, `filepath`.

JsonGate không execute tool. Nó chỉ parse, validate và dry-run policy.

Nếu fail:

```text
Failed stage: parse | action_schema | tool_resolve | tool_args | dry_run
Sandbox error: {...}
Return ONLY one corrected JSON object.
```

## Tool Schema

Tool args được validate trong `features/mcp_tools/schemas.py`.

Ví dụ:

```json
{
  "action": "tool",
  "tool": "python.run_python",
  "args": {
    "path": "code/example.py",
    "timeout": 10
  }
}
```

Nếu thiếu `path`, JsonGate hoặc MCP client trả lỗi schema. Agent phải sửa call, không gọi lại y nguyên.

## ReAct Loop

Loop chuẩn:

```text
observe latest state
  -> plan short
  -> tool_call
  -> tool_result
  -> update context
  -> next action
  -> finish
```

`plan` không phải chain-of-thought. Nó là mô tả ngắn để log dễ audit.

## Live User Directive Protocol

Root `orchestrator.py` can receive live user directives through
`agents/user_agent.py`.

Directive rules:

- Latest accepted live user directive has higher priority than agent suggestions.
- Agent must keep returning JSON actions or JSON final messages.
- If a directive asks to stop and answer now, return final JSON unless a
  validation/safety gate requires a blocker.
- If a directive asks for an unavailable tool, skill, or agent, say so clearly
  instead of pretending it exists.
- Directives cannot disable event logging or trace records.
- Directives cannot require exposing hidden internal chain-of-thought.

When a directive arrives during an LLM call, the orchestrator logs the returned
output as stale and retries the next step with a `USER AGENT LIVE DIRECTIVES`
message.

See:

```text
docs/19_USER_AGENT_CONTROL.md
```

## Role Ownership

### Code Agent

Code Agent là Engineering Department:

- Được implement.
- Được sửa file qua File Editor MCP.
- Không tự chạy validation trong LangGraph split.
- Không tự approve.
- Khi có `last_failure`, phải patch nhỏ đúng file fail.

### Test Agent

Test Agent là QA Department:

- Sở hữu validation.
- Chạy test hẹp nhất.
- Phân loại lỗi.
- Nếu lỗi code, route về Code Agent.
- Không sửa source.

### Review Agent

Review Agent là Senior Review Board:

- Review diff, correctness, scope, security, maintainability, release risk.
- Không sửa file.
- Không mutate git.
- Không approve nếu thiếu validation evidence.

### Ledger Agent

Ledger Agent là Secretary / Audit / Operations:

- Ghi sự kiện, task state, decision, incident.
- Audit mâu thuẫn.
- Không sửa code.
- Không chạy terminal.

## Department Lens Pattern

Lens là vai trò tư duy hẹp trong một department.

```text
Lens đề xuất.
Agent lớn quyết định.
Orchestrator điều phối.
Tool executor mới thực thi.
```

Lens không tự chạy tool ở v0.1.

Xem thêm:

```text
docs/agents/department-lenses.md
```

## Failed-Test Repair Protocol

Khi Test Agent chạy validation fail:

```text
tool_result ok=false
  -> extract failure summary
  -> last_failure = file/line/function/error/stderr_tail
  -> repair_attempts += 1
  -> route back to Code
```

Khi Code Agent repair:

- Patch bằng `file_editor.file_editor_str_replace` hoặc `file_editor.file_editor_insert`.
- Không rewrite nguyên file đang fail.
- Nếu cần context, view đúng vùng file fail một lần.
- Sau một patch, handoff lại Test.

## Finish Gate

Không final “đã xong” nếu coding task chưa có validation pass.

Valid validation evidence:

- `python.run_python`
- `python.python_probe`
- `lint_test.lint_compile`
- `lint_test.lint_ruff_check`
- `lint_test.lint_ruff_format_check`
- `lint_test.test_python_file`
- `lint_test.test_smoke_suite`
- Terminal validation hẹp như `py_compile`, `pytest`, `run_all_cases.py`

Nếu không thể validate:

```json
{
  "action": "final",
  "finish_reason": "blocker",
  "message": "Cannot validate because ..."
}
```

## Invalid Tool Or Unsafe Action

Nếu action fail ở `tool_args` hoặc `dry_run`, agent phải sửa đúng lỗi:

- Tool unknown: dùng tool name đúng trong allowlist.
- Missing arg: thêm field bắt buộc.
- Unsafe path: dùng path relative trong workspace.
- Terminal unsafe: chuyển sang MCP validation tool hoặc argv an toàn.
- Git mutation blocked: chỉ thực hiện nếu user yêu cầu rõ và env cho phép.
