# Rebuild Playbook

## Cách Dùng

Playbook này là checklist thực thi. Khi bắt đầu repo mới, chỉ làm một tầng tại
một thời điểm. Không kéo code của tầng sau vào tầng trước.

Mỗi tầng có:

- Mục tiêu.
- Files cần tạo.
- Lệnh kiểm tra.
- Điều kiện pass.
- Điều không được làm ở tầng đó.

## Tầng 1 - CLI + Prompt Loader

Mục tiêu:

- Chạy được CLI.
- Đọc prompt file.
- Chưa cần LLM thật.

Files:

```text
main.py
tools/prompt_loader.py
prompts/user_prompt.md
prompts/system_prompt.md
requirements.txt
```

Implementation:

- `main.py` nhận optional `sys.argv[1]`.
- `read_user_prompt(path)` đọc UTF-8.
- Nếu không có path, đọc `prompts/user_prompt.md`.
- In prompt hoặc fake final để xác nhận wiring.

Check:

```powershell
python main.py
python main.py prompts/user_prompt.md
python -m compileall -q main.py tools
```

Pass:

- Không crash.
- Đọc đúng prompt.
- Không có LLM/tool/orchestrator logic phức tạp.

Không làm:

- Không thêm MCP.
- Không thêm multi-agent.
- Không thêm JsonGate.

## Tầng 2 - LLM Adapter + JSON Final

Mục tiêu:

- Gọi LLM OpenAI-compatible.
- Agent trả final JSON.

Files:

```text
llm.py
agents/tool_agent.py
orchestrator.py
```

Implementation:

- `llm.py` chứa `call_llm(messages)`.
- `tool_agent(messages)` render system prompt tối giản.
- `orchestrator.run_orchestrator(task)` gọi agent và parse JSON.
- Chỉ hỗ trợ `action=final` trước.

Check:

```powershell
python main.py prompts/user_prompt.md
```

Pass:

- Valid final JSON được parse.
- Invalid JSON trả lỗi rõ hoặc retry tối giản.

Không làm:

- Chưa gọi tool.
- Chưa cần MCP.

## Tầng 3 - Event Log

Mục tiêu:

- Mỗi run có audit trail.

Files:

```text
core/runtime_paths.py
tools/event_log.py
tools/event_reader.py
inspect_runs.py
```

Implementation:

- Runtime dirs: `var/workspace`, `var/agent_runs`, `var/test_runs`.
- Event types tối thiểu: `MessageEvent`, `ActionEvent`, `StateEvent`.
- Summary chứa status, metrics, final_message.

Check:

```powershell
python main.py prompts/user_prompt.md
python inspect_runs.py list
python inspect_runs.py events latest --limit 20
```

Pass:

- Có `events.jsonl`.
- Có `summary.json`.
- Inspect đọc được.

Không làm:

- Không đưa business logic vào event logger.

## Tầng 4 - Kernel + CapabilityResult

Mục tiêu:

- Tách core khỏi tool backend.

Files:

```text
core/schemas.py
core/events.py
core/state.py
core/ports/tool_port.py
core/registry.py
core/kernel.py
core/bootstrap.py
core/capabilities.py
tests/test_kernel_contracts.py
run_kernel_smoke.py
```

Implementation:

- `CapabilityResult` có envelope ổn định.
- `CapabilityRegistry` resolve exact tool hoặc null tool.
- `AgentKernel.execute_tool()` publish event và wrap result.

Check:

```powershell
python run_kernel_smoke.py
python -m unittest tests.test_kernel_contracts
```

Pass:

- Unknown tool không crash.
- Disabled feature/null tool trả structured failure.

Không làm:

- Core không import MCP/RAG/browser/docker.

## Tầng 5 - Minimal File/Python Tools

Mục tiêu:

- Agent có thể tạo file và chạy file Python trong workspace.

Files:

```text
mcp_servers/file_editor_server.py
mcp_servers/python_sandbox.py
```

Có thể bắt đầu bằng in-process adapter nếu chưa muốn MCP, nhưng contract tool
result phải giữ giống MCP.

Check:

```powershell
python -m compileall -q mcp_servers
```

Manual/smoke:

- Create `var/workspace/code/hello.py`.
- Run `python.run_python` và thấy stdout.
- Thử path `../x.py` phải bị block.

Pass:

- File chỉ nằm trong workspace.
- Chỉ `.py` được chạy.
- Timeout hoạt động.

Không làm:

- Không cho arbitrary shell.

## Tầng 6 - JsonGate + Schemas + Policy

Mục tiêu:

- Không tool nào chạy nếu JSON/action/args không hợp lệ.

Files:

```text
output_gate/json_gate.py
output_gate/repair_rules.py
output_gate/repair_loop.py
features/mcp_tools/schemas.py
features/mcp_tools/policy.py
run_json_gate_smoke.py
```

Check:

```powershell
python run_json_gate_smoke.py
```

Pass:

- Valid tool/final pass.
- Fenced JSON repaired.
- Unsafe path blocked.
- Git mutation blocked.

Không làm:

- JsonGate không execute tool thật.

## Tầng 7 - MCP Adapter Feature

Mục tiêu:

- Tool execution qua feature adapter.

Files:

```text
features/loader.py
features/contracts.py
features/mcp_tools/config.py
features/mcp_tools/client.py
features/mcp_tools/adapter.py
features/mcp_tools/feature.py
config/features.yaml
tests/test_feature_contracts.py
tests/test_mcp_tools_feature.py
run_feature_tests.py
```

Check:

```powershell
python run_feature_tests.py
```

Pass:

- Feature registers canonical tools.
- Alias registration can be disabled.
- Tool result wrapped by kernel.

Không làm:

- Không để orchestrator gọi MCP client trực tiếp.

## Tầng 8 - Validation Discipline

Mục tiêu:

- Code edit không được final nếu chưa validate.

Files:

```text
mcp_servers/lint_test_server.py
mcp_servers/terminal_server.py
orchestrator.py
run_mcp_chain_smoke.py
```

Implementation:

- Detect code-change tools.
- Detect validation tools.
- Pending validation flag.
- Repeated tool guard.
- Condense tool result before feeding back to LLM.

Check:

```powershell
python run_mcp_chain_smoke.py
python run_all_cases.py --group project --fail-fast
```

Pass:

- Code change requires validation.
- Terminal blocks shell.
- Tool failure repeated stops.

Không làm:

- Không dùng terminal để edit.

## Tầng 9 - Skills

Mục tiêu:

- Workflow instructions có thể gắn vào system prompt.

Files:

```text
skills/project-plan/SKILL.md
skills/code-edit/SKILL.md
skills/debug-traceback/SKILL.md
skills/run-test/SKILL.md
skills/git-review/SKILL.md
tools/skill_loader.py
```

Check:

```powershell
python run_all_cases.py --group skill --fail-fast
```

Pass:

- Project-plan không edit.
- Git-review không mutate git.

Không làm:

- Skill không phải tool; không đặt skill name vào `tool`.

## Tầng 10 - Role Agents

Mục tiêu:

- Tách quyền theo role.

Files:

```text
agents/base_agent.py
agents/role_agents.py
agents/lenses/
run_agent_role_smoke.py
```

Check:

```powershell
python run_agent_role_smoke.py
```

Pass:

- Role gọi forbidden tool bị block.
- Role allowlist expand đúng.

Không làm:

- Chưa cần LangGraph nếu role smoke chưa ổn.

## Tầng 11 - LangGraph Pipeline

Mục tiêu:

- Multi-agent state machine cho coding task.

Files:

```text
orchestration/agent_state.py
orchestration/langgraph_orchestrator.py
main_langgraph.py
run_langgraph_smoke.py
```

Check:

```powershell
python run_langgraph_smoke.py
```

Pass:

- Graph compile.
- Failure summary capture.
- Repair guard hoạt động.
- Finish gate hoạt động.

Không làm:

- Không cho từng role tự execute tool ngoài tool node.

## Tầng 12 - Company Agents v0.5

Mục tiêu:

- Department contract deterministic.

Files:

```text
agents/department_v05.py
agents/*_agent.py
orchestration/code_test_orchestrator.py
orchestration/company_orchestrator.py
run_code_test_agents_smoke.py
run_company_agents_smoke.py
```

Check:

```powershell
python run_code_test_agents_smoke.py
python run_company_agents_smoke.py
```

Pass:

- Code writes scoped file.
- Test runs validation.
- Review approves only after pass.
- Ledger records.
- Final routes done.

Không làm:

- Không thay thế LangGraph real runtime vội; dùng làm contract target.

## Tầng 13 - Software Factory

Mục tiêu:

- Product prompt dài sinh spec artifacts trước coding.

Files:

```text
agents/artifact_protocol.py
agents/software_factory_agents.py
orchestration/software_factory_orchestrator.py
run_software_factory_smoke.py
run_software_factory_demo.py
```

Check:

```powershell
python run_software_factory_smoke.py
```

Pass:

- Đủ Vision/BRD/PRD/Stories/AC/Domain/Logic/Technical/Pattern/Spec/Handoff/Docs artifacts.
- Pattern decision có hotspot evidence.
- Implementation spec có requested files.

Không làm:

- Software Factory không claim đã implement source code.

## Tầng 14 - Global Supervisor

Mục tiêu:

- Route đúng request ngoài coding.

Files:

```text
orchestration/intent_router.py
orchestration/global_supervisor.py
agents/knowledge/
agents/research_department/
agents/safety/
agents/final_synthesis_agent.py
run_global_supervisor_smoke.py
```

Check:

```powershell
python run_global_supervisor_smoke.py
python run_capability_suite.py
```

Pass:

- Knowledge không dùng repo write tools.
- Research no-network mặc định.
- Product build route Software Factory.
- Safety blocks prompt injection.

Không làm:

- Không bật real coding/network mặc định nếu chưa cần.

## Tầng 15 - Hardening Before Daily Use

Mục tiêu:

- Làm repo mới đủ ổn để dùng hằng ngày.

Checklist:

- Fix encoding docs/prompts.
- Add docs index.
- Add traceability matrix.
- Add ADRs.
- Add dev quick/full checks.
- Add cleanup policy cho runtime artifacts.
- Decide MCP process pooling.

Check:

```powershell
python run_dev_checks.py --quick
python run_dev_checks.py --full
```

Pass:

- Quick pass trước mỗi change.
- Full pass trước milestone lớn.

