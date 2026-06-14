# Start Here

Tài liệu này dành cho người mới muốn hiểu và chạy project trong khoảng 15 phút.

## Project Này Là Gì?

`my_agents` là một local coding-agent framework. Mục tiêu là tạo agent có thể:

- Nhận prompt từ user.
- Suy nghĩ theo ReAct rõ ràng.
- Gọi MCP tools qua schema cứng.
- Sửa file qua file editor riêng, không sửa bằng terminal tự do.
- Chạy validation/test thật rồi sửa tiếp nếu fail.
- Dùng RAG, search, fetch, document, ledger, browser khi cần.
- Chia vai theo agent phòng ban: Engineering, QA, Review, Ledger/Ops.
- Ghi event log để debug và audit.

Project này lấy nhiều bài học từ OpenHands, nhưng triển khai theo hướng gọn hơn:

- Tool protocol rõ.
- File editor tách khỏi terminal.
- Terminal có metadata rủi ro.
- Agent loop có finish gate.
- Có context condenser.
- Có failed-test repair loop.
- Có JsonGate để sửa và kiểm output JSON trước khi gọi tool.

## Cách Chạy Nhanh

1. Cài dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Mở LM Studio hoặc server OpenAI-compatible:

```text
http://localhost:1234/v1
```

3. Chạy prompt qua orchestrator cũ:

```powershell
python main.py prompts/auto_cases/test_project_00_python_probe.md
```

4. Chạy LangGraph smoke:

```powershell
python run_langgraph_smoke.py
```

5. Chạy JsonGate smoke:

```powershell
python run_json_gate_smoke.py
```

6. Chạy test suite nhóm LangGraph:

```powershell
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
```

7. Nếu muốn chạy RAG, bật Qdrant:

```powershell
docker compose up -d qdrant
```

## User Agent Control

Root `main.py` supports live user directives while the agent is running:

```powershell
python main.py --interactive-user-agent prompts/user_prompt.md
python main.py --user-control-dir var/live_control prompts/user_prompt.md
```

Read:

```text
docs/19_USER_AGENT_CONTROL.md
```

## Process Dashboard UI

Chay UI local de quan ly process, xem agent/state/log, va gui live directive:

```powershell
python run_process_ui.py --port 8765
```

Mo:

```text
http://127.0.0.1:8765
```

Docs:

```text
docs/20_PROCESS_DASHBOARD_UI.md
```

## Đường Đọc Tài Liệu

Nếu bạn là người mới:

1. `docs/00_START_HERE.md`
2. `docs/01_PROJECT_OVERVIEW.md`
3. `docs/03_SETUP_AND_RUN.md`
4. `docs/08_TESTING_GUIDE.md`

Nếu bạn muốn thêm MCP, skill, hoặc agent:

1. `docs/05_MCP_SYSTEM.md`
2. `docs/06_SKILLS_SYSTEM.md`
3. `docs/04_AGENT_PROTOCOL.md`
4. `docs/workflows/add-new-mcp.md`
5. `docs/workflows/add-new-skill.md`
6. `docs/workflows/create-new-agent.md`

Nếu bạn muốn phát triển mini repo/lab:

1. `docs/18_MINI_REPO_DEVELOPMENT.md`
2. `docs/workflows/add-mini-repo-lab.md`
3. `tools/mini_repo_registry.py`
4. `business_prompt_lab/README.md`

Nếu bạn muốn đóng góp kiến trúc:

1. `docs/02_ARCHITECTURE.md`
2. `docs/11_SECURITY_AND_SANDBOX.md`
3. `docs/12_ROADMAP.md`
4. `docs/adr/`
5. `docs/13_IMPLEMENTATION_SUMMARY.md`
6. `docs/17_GENERAL_MULTI_AGENT_ROADMAP.md`

## Các Entry Point Quan Trọng

| File | Vai trò |
|---|---|
| `main.py` | Chạy single-agent orchestrator |
| `main.py --interactive-user-agent ...` | Chạy single-agent orchestrator với live User Agent directives |
| `main.py lab ...` | Chạy mini repo/lab qua registry chung |
| `main_langgraph.py` | Chạy LangGraph multi-agent pipeline |
| `orchestrator.py` | ReAct loop cũ, vẫn còn dùng được |
| `orchestration/langgraph_orchestrator.py` | Role pipeline mới |
| `orchestration/global_supervisor.py` | Global Supervisor stage 1-6 wrapper |
| `orchestration/intent_router.py` | Intent Router stage 1-6 |
| `orchestration/company_orchestrator.py` | Full Company Agents v0.5 runner |
| `orchestration/software_factory_orchestrator.py` | Software Factory v0.7 artifact-first spec runner |
| `docs/17_GENERAL_MULTI_AGENT_ROADMAP.md` | Global Supervisor / Intent Router roadmap |
| `docs/18_MINI_REPO_DEVELOPMENT.md` | Guide phát triển nhiều mini repo/lab |
| `docs/19_USER_AGENT_CONTROL.md` | Live user directives cho root orchestrator |
| `docs/20_PROCESS_DASHBOARD_UI.md` | UI quan ly process, agent state, LangGraph logs, User Agent input |
| `agents/role_agents.py` | Khai báo role agents và quyền tool |
| `agents/business_analyst_agent.py` | Business Analyst gate trước Planner |
| `agents/lenses/` | Department lens specs |
| `output_gate/` | JsonGate và JSON repair sandbox |
| `features/mcp_tools/client.py` | MCP client/router |
| `features/mcp_tools/schemas.py` | Tool schema cứng |
| `mcp_servers/` | MCP servers nội bộ |
| `run_all_cases.py` | Prompt-based test runner |

## Khi Có Lỗi

Đọc theo thứ tự:

1. Terminal output của lệnh vừa chạy.
2. `var/test_runs/<timestamp>/<case>.log`.
3. `var/agent_runs/<run_id>/events.jsonl`.
4. `docs/09_DEBUGGING_GUIDE.md`.

Lệnh hữu ích:

```powershell
python inspect_runs.py list
python inspect_runs.py events latest --limit 20
python run_json_gate_smoke.py
python run_ba_agent_smoke.py
python run_agent_role_smoke.py
```

## Code/Test v0.5 Quick Start

Project now has a direct Code/Test Department v0.5 runner. It is separate from
`main_langgraph.py` and is safe to test independently.

```powershell
python run_code_test_agents_smoke.py
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --max-cycles 2
```

Read the full guide:

```text
docs/14_CODE_TEST_V05.md
```

## Full Company Agents v0.5 Quick Start

Project also has a direct full-company v0.5 runner:

```text
Research -> Business Analyst -> Planner -> Architect -> Code -> Test -> Review -> Ledger -> Final
```

Run the deterministic smoke:

```powershell
python run_company_agents_smoke.py
```

Run the demo and inspect JSON:

```powershell
python run_company_agents_demo.py --version v0.5 --max-cycles 2
```

Read the full guide:

```text
docs/15_COMPANY_AGENTS_V05.md
```

## Software Factory v0.7 Quick Start

Use this path before real coding when the prompt is a product/business problem,
not just a direct code edit.

```text
Intake Protocol -> Vision -> BRD -> PRD -> Story -> AC -> Domain -> Business Logic -> Technical -> Pattern -> Implementation Spec -> Code Handoff -> Docs Verification
```

Run the smoke:

```powershell
python run_software_factory_smoke.py
```

Run it on a prompt file:

```powershell
python run_software_factory_demo.py --task-file prompts/the_sims_prompt.md
```

Then hand the generated implementation spec to the real company runner:

```powershell
python run_company_agents_demo.py --real --task-file var/workspace/factory_runs/<run_id>/10_implementation_spec.md --real-max-steps 260
```

Read the full guide:

```text
docs/16_SOFTWARE_FACTORY_V06.md
```
