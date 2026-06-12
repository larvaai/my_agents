# Repo Layout

Tai lieu nay chi mo ta cach doc repo hien tai. No khong yeu cau xoa, doi ten,
hay rut gon bat ky artifact nao; cac file log, snapshot, workspace output va
external reference deu co gia tri lich su/rag/debug rieng.

## Vung Source Chinh

| Path | Vai tro |
|---|---|
| `core/` | Agent Kernel: state, events, registry, schemas, ports. Day la core boundary moi. |
| `core/ports/` | Stable interfaces cho detachable capabilities: tool, search, memory, browser, code edit, test, issue. |
| `features/` | Removable feature modules. Hien co `features/mcp_tools/` boc MCP layer cu va `features/nulls.py` cho null fallback. |
| `config/features.yaml` | Kernel feature config. Mac dinh bat `mcp_tools`, aliases, va tests bat buoc. |
| `config/agents.yaml` | Agent role registry and aliases. |
| `config/roles/*.yaml` | Role permissions, skills, route permissions, test ownership, and lens group. |
| `agents/` | Agent runtime, department agents, lenses, artifact protocol. |
| `agents/knowledge/` | Read-only Knowledge Department agents. |
| `agents/research_department/` | Research Department search/fetch/PDF/citation wrappers. |
| `agents/safety/` | Safety Department permission/risk/prompt-injection/tool-scope gate. |
| `orchestration/` | Cac runner/orchestrator noi agent theo workflow. |
| `orchestration/global_supervisor.py` | Global Supervisor stage 1-6 wrapper. |
| `orchestration/intent_router.py` | Intent Router stage 1-6. |
| `tools/` | Compatibility helpers: prompt/skill loader, event reader/logger. MCP adapter code lives in `features/mcp_tools/`. |
| `tools/mini_repo_registry.py` | Registry cho mini repo/lab chạy qua `python main.py lab ...`. |
| `mcp_servers/` | MCP servers noi bo cho filesystem-like workflow, validation, RAG, document, ledger, browser, issue, docker. |
| `mcp_servers/pdf_text_extraction_server.py` | Read-only PDF/Text Extraction MCP. |
| `output_gate/` | JsonGate va repair loop cho JSON action/output. |
| `llm.py` | OpenAI-compatible LLM client wrapper. |
| `main.py` | Entry point single-agent/orchestrator cu, dong thoi co mode `lab` cho mini repo. |
| `main_langgraph.py` | Entry point LangGraph role orchestration. |
| `orchestrator.py` | ReAct loop cu van con dung duoc. |
| `business_prompt_lab/` | Mini repo dau tien: prompt benchmark va no-code agent room. |
| `experiments/self_eval_qa_lab/` | Mini repo self-evaluating answer flow v0.2: workflow router, direct/assisted/deep/repo_debug paths, evaluator, flow observer, lessons, ledger. |

## Entry Points Va Smoke Scripts

| Path | Vai tro |
|---|---|
| `run_capability_suite.py` | Smoke tong hop nang luc hien tai cua project. |
| `run_kernel_smoke.py` | Smoke Agent Kernel registry/events/null fallback. |
| `run_feature_tests.py` | Chay tests bat buoc cua cac feature dang bat trong `config/features.yaml`. |
| `run_json_gate_smoke.py` | Smoke JsonGate. |
| `run_agent_role_smoke.py` | Smoke role permission va lenses. |
| `run_langgraph_smoke.py` | Smoke compile/runtime LangGraph nho. |
| `run_mcp_chain_smoke.py` | Smoke MCP chain that khong qua LLM. |
| `run_code_test_agents_smoke.py` | Smoke Code/Test Department. |
| `run_company_agents_smoke.py` | Smoke full Company Agents. |
| `run_software_factory_smoke.py` | Smoke Software Factory artifact pipeline. |
| `run_global_supervisor_smoke.py` | Smoke Global Supervisor stage 1-6 router/knowledge/research/final flow. |
| `run_global_supervisor_demo.py` | Run a task or task file through Global Supervisor and write a JSON log. |
| `run_all_cases.py` | Prompt-based case runner. |
| `inspect_runs.py` | Doc/search event logs trong `var/agent_runs/`. |

## Product Inputs Va Test Prompts

| Path | Vai tro |
|---|---|
| `prompts/system_prompt.md` | System prompt chinh. |
| `prompts/user_prompt.md` | Prompt mac dinh cho `main.py`. |
| `prompts/auto_cases/` | Prompt cases dung bo test tu dong. |
| `prompts/skill_cases/` | Cases de test skills. |
| `prompts/the_sims_prompt.md` | Prompt san pham lon cho demo Software Factory/Company Agents. |
| `prompts/README.md` | Huong dan doc prompts. |

## Documentation

| Path | Vai tro |
|---|---|
| `docs/00_START_HERE.md` | Diem vao cho nguoi moi. |
| `docs/01_PROJECT_OVERVIEW.md` | Tong quan project. |
| `docs/02_ARCHITECTURE.md` | Kien truc runtime va boundaries. |
| `docs/03_SETUP_AND_RUN.md` | Cai dat va chay local. |
| `docs/04_AGENT_PROTOCOL.md` | Protocol agent/tool/action. |
| `docs/05_MCP_SYSTEM.md` | MCP system. |
| `docs/06_SKILLS_SYSTEM.md` | Skill system. |
| `docs/07_RAG_SYSTEM.md` | RAG local. |
| `docs/08_TESTING_GUIDE.md` | Validation/test strategy. |
| `docs/09_DEBUGGING_GUIDE.md` | Debug failed runs. |
| `docs/10_CONTRIBUTING.md` | Quy trinh dong gop. |
| `docs/11_SECURITY_AND_SANDBOX.md` | Guardrails va sandbox. |
| `docs/12_ROADMAP.md` | Huong phat trien. |
| `docs/13_IMPLEMENTATION_SUMMARY.md` | Tong ket implementation lich su. |
| `docs/14_CODE_TEST_V05.md` | Code/Test Department v0.5. |
| `docs/15_COMPANY_AGENTS_V05.md` | Company Agents v0.5. |
| `docs/16_SOFTWARE_FACTORY_V06.md` | Software Factory v0.7. |
| `docs/17_GENERAL_MULTI_AGENT_ROADMAP.md` | Global Supervisor / Intent Router roadmap; stage 1-6 implemented. |
| `docs/18_MINI_REPO_DEVELOPMENT.md` | Guide phat trien mini repo/lab va tich hop qua `main.py lab`. |
| `docs/adr/` | Architecture Decision Records. |
| `docs/agents/` | Tai lieu tung agent/lens. |
| `docs/mcp/` | Tai lieu tung MCP. |
| `docs/workflows/` | Workflow them MCP/skill/agent/debug. |
| `docs/templates/` | Templates cho ADR, agent, MCP, skill, test case. |

## Runtime, Artifact, Va Historical Data

Khong coi cac vung nay la rac. Chung la du lieu phuc vu debug, RAG, audit,
so sanh output va khoi phuc ket qua.

| Path | Vai tro |
|---|---|
| `var/workspace/` | Sandbox chinh cho filesystem/python/RAG/document/ledger/issue artifacts. Runtime boundary duoc dinh nghia trong `core/runtime_paths.py`. |
| `var/workspace/factory_runs/` | Software Factory artifacts theo tung run. |
| `var/workspace/society_sim*` | Generated product/output/backups tu prompt simulation. |
| `var/workspace/code/` | Workspace code fixtures, smoke files, generated test artifacts. |
| `var/workspace/notes/` | Notes/RAG sample knowledge. |
| `var/workspace/ledger/` | Append-only ledger output. |
| `var/workspace/issues/` | SQLite issue tracker local. |
| `var/workspace/obsidian_vault/` | Local markdown vault sample/output. |
| `var/agent_runs/` | Event log va summary cua agent runs. |
| `var/test_runs/` | Logs va summaries cua prompt/smoke test runs. |
| `var/qdrant_storage/` | Local Qdrant data. |
| `project_context.txt` | Snapshot context lon cua repo tai mot thoi diem. |
| `skills_test_logs.txt` | Historical skill/test logs. |
| `savegame.json`, `test_save.json`, `test_savegame.json` | Historical/generated save artifacts. |

## External Reference

| Path | Vai tro |
|---|---|
| `OpenHands/` | External reference repo de hoc/so sanh, khong phai core runtime. |
| `openhands-workspace/` | Workspace trao doi/copy voi OpenHands. |
| `PROJECT_READING_GUIDE_VI.md` | Huong dan doc reference/context tieng Viet. |

## Quy Uoc Khi Phat Trien Tiep

- Khi sua code runtime, bat dau tu `core/`, `agents/`, `orchestration/`,
  `tools/`, `mcp_servers/`, hoac `output_gate/`.
- Khi them integration moi, uu tien tao port/contract trong `core/ports/`,
  feature trong `features/`, va tests trong `tests/` thay vi cho orchestrator
  goi tool cu the truc tiep.
- Khi them behavior moi, cap nhat docs tuong ung trong `docs/` va prompt/test
  case lien quan trong `prompts/`.
- Khi can inspect lich su hay output cu, doc `var/agent_runs/`, `var/test_runs/`,
  `var/workspace/`, `var/qdrant_storage/`, `project_context.txt`, va
  `skills_test_logs.txt` thay vi xoa chung.
- Khong hard-code `workspace/`, `agent_runs/`, `test_runs/`, hoac
  `qdrant_storage/`; dung `core.runtime_paths`.
