# Setup And Run

## Requirements

- Windows PowerShell hoặc terminal tương đương.
- Python 3.11+.
- Node.js/npx cho Filesystem MCP và Context7 MCP.
- Docker Desktop nếu dùng Qdrant/RAG hoặc Docker MCP.
- LM Studio hoặc endpoint OpenAI-compatible.

## Install

```powershell
python -m pip install -r requirements.txt
```

Nếu dùng Playwright screenshot/browser:

```powershell
python -m playwright install chromium
```

## LLM Configuration

Project dùng `llm.py` để gọi LM Studio/OpenAI-compatible API.

Env thường dùng:

```powershell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_API_KEY="lm-studio"
$env:LLM_MODEL="ten-model-trong-lm-studio"
```

LM Studio thường không cần API key thật. `lm-studio` chỉ là placeholder để client OpenAI-compatible chấp nhận.

## Run Single-Agent Orchestrator

Prompt mặc định:

```powershell
python main.py
```

Prompt file:

```powershell
python main.py prompts/auto_cases/test_project_00_python_probe.md
```

## Run LangGraph Orchestrator

```powershell
python main_langgraph.py prompts/the_sims_prompt.md
```

Giới hạn step:

```powershell
$env:LANGGRAPH_MAX_STEPS="80"
python main_langgraph.py prompts/the_sims_prompt.md
```

## Run Qdrant For RAG

```powershell
docker compose up -d qdrant
```

Health check:

```powershell
Invoke-RestMethod http://localhost:6333/collections
```

RAG MCP cũng có tool health:

```text
rag.rag_health
```

## Smoke Checks

Chạy sau khi setup:

```powershell
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_langgraph_smoke.py
python run_mcp_chain_smoke.py
```

Chạy group LangGraph:

```powershell
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
```

Chạy một case:

```powershell
python run_all_cases.py --case agent_01_fix_small_bug --fail-fast
```

List case:

```powershell
python run_all_cases.py --list
```

## Important Env Vars

| Env | Ý nghĩa |
|---|---|
| `ORCH_MAX_STEPS` | Max step cho single-agent orchestrator |
| `LANGGRAPH_MAX_STEPS` | Max step cho LangGraph orchestrator |
| `ORCH_MAX_OBSERVATION_CHARS` | Giới hạn condenser tool result |
| `AGENT_ALLOW_GIT_MUTATIONS` | Cho phép Git mutation khi user yêu cầu rõ |
| `AGENT_ALLOW_HIGH_RISK_TERMINAL` | Cho phép terminal high-risk command |
| `DOCKER_MCP_ALLOW_MUTATION` | Cho Docker compose up/stop |
| `OBSIDIAN_VAULT_DIR` | Vault Obsidian local |
| `ISSUE_DB_PATH` | SQLite issue DB path |
| `QDRANT_URL` | Qdrant URL |
| `QDRANT_COLLECTION` | Qdrant collection |
| `SEARCH_PROVIDER` | `brave`, `tavily`, hoặc fallback |
| `BRAVE_SEARCH_API_KEY` | Brave Search key |
| `TAVILY_API_KEY` | Tavily key |

## Generated Data

| Path | Nội dung |
|---|---|
| `var/agent_runs/` | Event logs và summary của agent runs |
| `var/test_runs/` | Logs và summary của test runner |
| `var/workspace/` | Workspace sandbox cho agent |
| `var/workspace/ledger/` | Append-only ledger |
| `var/workspace/issues/` | Issue tracker local |
| `var/workspace/obsidian_vault/` | Markdown vault |
| `var/qdrant_storage/` | Qdrant local data |

## Clean Mental Model

Không cần chạy tất cả ngay. Thứ tự tốt nhất:

1. LM Studio lên.
2. `python run_json_gate_smoke.py`.
3. `python run_agent_role_smoke.py`.
4. `python run_langgraph_smoke.py`.
5. Một prompt nhỏ qua `main.py`.
6. Một prompt role-based qua `main_langgraph.py`.

## Run Code/Test Department v0.5

The direct v0.5 Code/Test runner is deterministic by default and does not need
LLM unless `--use-llm` is provided.

```powershell
python run_code_test_agents_smoke.py
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --max-cycles 2
```

For model-backed lens experimentation:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --use-llm
```
