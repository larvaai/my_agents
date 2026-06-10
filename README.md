# my_agents

`my_agents` la project thu nghiem coding-agent local. No ket hop:

- LLM local qua LM Studio/OpenAI-compatible API.
- Mot orchestrator ep agent tra JSON-only.
- Tool layer qua MCP servers.
- Skills dang Markdown de dieu khien workflow.
- RAG local bang Qdrant + fastembed.
- Bo test prompt de kiem tra nang luc agent.

Muc tieu cua project khong phai lam chatbot chung chung, ma la xay mot coding-agent co the doc repo, sua file co kiem soat, chay validation, doc loi, dung RAG, va bao cao ro rang.

## Docs chinh thuc

- Bat dau tai `docs/00_START_HERE.md`.
- Muon chay project: `docs/03_SETUP_AND_RUN.md`.
- Muon hieu kien truc: `docs/02_ARCHITECTURE.md`.
- Muon them MCP/skill/agent: `docs/workflows/`.
- Muon debug/test: `docs/08_TESTING_GUIDE.md` va `docs/09_DEBUGGING_GUIDE.md`.
- Muon thu LangGraph role orchestration: `python run_langgraph_smoke.py` de compile smoke nhanh, hoac `python main_langgraph.py prompts/auto_cases/test_langgraph_01_smoke.md` de chay LLM smoke that qua MCP.

## Kien truc ngan gon

```text
User prompt
  -> main.py
  -> orchestrator.run_orchestrator()
  -> agents/tool_agent.py
  -> llm.py -> LM Studio
  -> JSON action
     -> tools/tool_registry.py
     -> tools/mcp_client.py
     -> MCP server
        -> filesystem / git / context7 / python / file_editor / terminal
           / code_index / lint_test / docker / obsidian / issue
           / rag / fetch / search / document / ledger / playwright
  -> tool_result
  -> agent lap lai
  -> JSON final
```

## Thu muc quan trong

```text
agents/              LLM-facing agent wrapper.
tools/               MCP client, MCP config, prompt loader, skill loader.
mcp_servers/         MCP servers noi bo: python, file_editor, terminal, code_index, lint_test, docker, obsidian, issue, RAG, fetch, search, document, ledger, playwright.
skills/              Project skills: plan, edit, debug, test, review.
prompts/             System prompt, user prompt, auto test prompts.
workspace/           Sandbox workspace cho filesystem, python, RAG.
agent_runs/          Event log va summary cua tung lan chay agent.
test_runs/           Log va summary moi lan chay bo test.
qdrant_storage/      Du lieu Qdrant local.
OpenHands/           Repo OpenHands clone de so sanh, khong phai core project.
openhands-workspace/ Workspace copy/trao doi voi OpenHands.
```

## Yeu cau chay

Can co:

- Python 3.11+ khuyen nghi.
- LM Studio dang bat OpenAI-compatible server.
- Node/npx de chay MCP filesystem va Context7.
- Playwright Chromium neu can test UI/rendered web pages.
- Docker neu dung Qdrant.

Cai Python dependencies:

```powershell
cd "D:\Agent PRJ\my_agents"
python -m pip install -r requirements.txt
```

Bat Qdrant:

```powershell
docker compose up -d qdrant
```

Kiem tra Qdrant:

```powershell
Invoke-RestMethod http://localhost:6333/collections
```

Cai browser binary cho Playwright MCP neu can screenshot/doc rendered UI:

```powershell
python -m playwright install chromium
```

## Cau hinh LLM

Mac dinh trong `llm.py`:

```text
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=qwen3.5-9b-claude-4.6-opus-uncensored-distilled
LLM_TIMEOUT=600
LLM_MAX_TOKENS=2048
```

Co the override bang env:

```powershell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_API_KEY="lm-studio"
$env:LLM_MODEL="qwen3.5-9b-claude-4.6-opus-uncensored-distilled"
$env:LLM_MAX_TOKENS="2048"
```

## Chay agent

Chay prompt mac dinh:

```powershell
python main.py
```

Chay mot prompt cu the:

```powershell
python main.py prompts/test_mcp_prompt.md
python main.py prompts/test_rag_02_negative_search.md
```

Gioi han so buoc orchestrator:

```powershell
$env:ORCH_MAX_STEPS="30"
python main.py prompts/test_mcp_prompt.md
```

Moi run se tao event log:

```text
agent_runs/<run_id>/events.jsonl
agent_runs/<run_id>/summary.json
agent_runs/index.jsonl
```

Tat event log neu can:

```powershell
$env:AGENT_EVENT_LOG="0"
```

Gioi han so lan lap lai cung mot tool call:

```powershell
$env:ORCH_MAX_SAME_TOOL_CALLS="3"
```

Inspect run gan nhat:

```powershell
python inspect_runs.py list
python inspect_runs.py summary latest
python inspect_runs.py events latest --limit 20
python inspect_runs.py events latest --kind ObservationEvent
python inspect_runs.py events latest --text "policy_blocked" --json
```

## Tool/MCP hien co

Project expose tools cho agent qua `tools/mcp_config.py` va prompt sinh tu `tools/mcp_client.py`.

### Filesystem MCP

Sandboxed vao:

```text
D:\Agent PRJ\my_agents\workspace
```

Tools chinh:

```text
filesystem.list_directory
filesystem.read_file
filesystem.write_file
filesystem.edit_file
filesystem.search_files
filesystem.directory_tree
```

### Git MCP

Chay tren repo root:

```text
D:\Agent PRJ\my_agents
```

Tools chinh:

```text
git.git_status
git.git_diff
git.git_diff_unstaged
git.git_diff_staged
git.git_log
git.git_show
```

Mutating Git tools hien da bi hard-block trong runtime. Chi bat cho mot run khi user that su yeu cau thay doi Git history/stage/branch:

```powershell
$env:AGENT_ALLOW_GIT_MUTATIONS="1"
python main.py prompts/some_explicit_git_task.md
Remove-Item Env:\AGENT_ALLOW_GIT_MUTATIONS
```

### Context7 MCP

Dung de doc docs thu vien khi can. Neu co API key:

```powershell
$env:CONTEXT7_API_KEY="..."
```

### Python MCP

File:

```text
mcp_servers/python_sandbox.py
```

Chi chay file `.py` trong `workspace`, timeout toi da 30 giay.

Tools:

```text
python.run_python
python.python_probe
```

### File Editor MCP

File:

```text
mcp_servers/file_editor_server.py
```

Dung de view/create/str_replace/insert file trong `workspace`. Day la duong uu tien khi agent can sua file, vi de audit hon terminal.

Tools:

```text
file_editor.file_editor_view
file_editor.file_editor_create
file_editor.file_editor_str_replace
file_editor.file_editor_insert
```

### Terminal MCP

File:

```text
mcp_servers/terminal_server.py
```

Dung de chay command validation/probe nho. Tool nay nhan `argv` list, khong nhan shell string, va moi result co:

```text
command_metadata.summary
command_metadata.security_risk
```

Shell executables nhu `cmd`, `powershell`, `bash`, token dieu khien shell, lenh pha huy, va git mutation bi chan mac dinh.

Tools:

```text
terminal.terminal_run
```

Vi du:

```powershell
@'
from tools.mcp_client import call_mcp_tool
print(call_mcp_tool("terminal.terminal_run", {
    "argv": ["python", "-m", "py_compile", "main.py"],
    "timeout": 10,
    "cwd": ".",
    "purpose": "syntax validation"
}))
'@ | python -
```

### Code Index MCP

File:

```text
mcp_servers/code_index_server.py
```

Read-only project index de agent tim symbol/import/reference ma khong can doc ca repo. Tool nay scan project root nhung exclude thu muc nang nhu `OpenHands`, `qdrant_storage`, `test_runs`, `.git`.

Tools:

```text
code_index.code_index
code_index.code_find_symbol
code_index.code_find_references
code_index.code_dependency_graph
```

### Lint/Test MCP

File:

```text
mcp_servers/lint_test_server.py
```

Duong validation chuan cho coding-agent. Khong chay shell tuy y; chi co compile, ruff check/format check, run Python file, va smoke suite nho.

Tools:

```text
lint_test.lint_compile
lint_test.lint_ruff_check
lint_test.lint_ruff_format_check
lint_test.test_python_file
lint_test.test_smoke_suite
```

### Docker MCP

File:

```text
mcp_servers/docker_server.py
```

Docker helper gioi han quyen. Read-only tools doc status/logs; `up/stop` bi chan mac dinh neu chua set `DOCKER_MCP_ALLOW_MUTATION=1`. Khong expose delete/prune/rm/rmi/volume rm.

Tools:

```text
docker.docker_health
docker.docker_ps
docker.docker_compose_ps
docker.docker_compose_logs
docker.docker_compose_up
docker.docker_compose_stop
```

### Obsidian MCP

File:

```text
mcp_servers/obsidian_server.py
```

Vault markdown local. Mac dinh ghi vao `workspace/obsidian_vault`, hoac dat `OBSIDIAN_VAULT_DIR` de tro toi vault rieng. Tool chi lam viec voi `.md` va chan noi dung giong secret/token.

Tools:

```text
obsidian.obsidian_list_notes
obsidian.obsidian_read_note
obsidian.obsidian_write_note
obsidian.obsidian_append_note
obsidian.obsidian_search_notes
obsidian.obsidian_create_daily_note
```

### Issue Tracker MCP

File:

```text
mcp_servers/issue_server.py
```

Issue tracker local bang SQLite trong `workspace/issues/issues.db`, dung cho bug/task/review/risk/blocker va multi-agent handoff.

Tools:

```text
issue.issue_create
issue.issue_update
issue.issue_add_comment
issue.issue_list
issue.issue_get
issue.issue_search
issue.issue_stats
```

### RAG MCP

File:

```text
mcp_servers/rag_server.py
```

Dung:

- `fastembed` de embed text.
- Qdrant tai `http://localhost:6333`.
- Collection mac dinh `my_agents_rag`.
- Chi ingest `.md`, `.txt`, `.py` trong `workspace`.

Tools:

```text
rag.rag_health
rag.rag_ingest
rag.rag_search
```

Env tuy chon:

```powershell
$env:QDRANT_URL="http://localhost:6333"
$env:QDRANT_COLLECTION="my_agents_rag"
$env:EMBEDDING_MODEL="intfloat/multilingual-e5-large"
$env:RAG_CHUNK_SIZE="1200"
$env:RAG_CHUNK_OVERLAP="200"
```

### Fetch MCP

File:

```text
mcp_servers/fetch_server.py
```

Dung de lay noi dung mot URL HTTP/HTTPS va rut ra text doc duoc.

Tools:

```text
fetch.fetch_url
```

### Search MCP

File:

```text
mcp_servers/search_server.py
```

Dung de search web. Provider uu tien:

1. `BRAVE_SEARCH_API_KEY`
2. `TAVILY_API_KEY`
3. DuckDuckGo HTML fallback best-effort, khong can API key

Tools:

```text
search.search_health
search.web_search
```

Env tuy chon:

```powershell
$env:SEARCH_PROVIDER="brave"
$env:BRAVE_SEARCH_API_KEY="..."
$env:TAVILY_API_KEY="..."
```

### Document MCP

File:

```text
mcp_servers/document_server.py
```

Dung de doc/viet tai lieu trong `workspace`. Ho tro text/Markdown/code/json/csv/html; PDF can `pypdf`; DOCX can `python-docx`.

Tools:

```text
document.document_extract_text
document.document_write_markdown
document.document_append_section
document.document_outline
```

### Ledger MCP

File:

```text
mcp_servers/ledger_server.py
```

Append-only JSONL memory/audit log trong `workspace/ledger/ledger.jsonl` mac dinh.

Tools:

```text
ledger.ledger_append
ledger.ledger_tail
ledger.ledger_search
ledger.ledger_get
ledger.ledger_stats
```

Env tuy chon:

```powershell
$env:LEDGER_PATH="D:\Agent PRJ\my_agents\workspace\ledger\ledger.jsonl"
```

### Playwright MCP

File:

```text
mcp_servers/playwright_server.py
```

Dung de lay text/screenshot tu UI local hoac page render bang JavaScript. Truoc khi dung:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Tools:

```text
playwright.playwright_health
playwright.playwright_get_text
playwright.playwright_screenshot
```

## Skills

Skills nam trong `skills/*/SKILL.md`, duoc load boi `tools/skill_loader.py` va chen vao system prompt.

Hien co:

```text
project-plan      Lap ke hoach read-only, khong sua file.
code-edit         Sua code nho, doc file truoc khi edit.
debug-traceback   Debug traceback tu loi cu the.
run-test          Chay validation theo whitelist.
git-review        Review git status/diff, khong commit.
```

Moi skill co YAML frontmatter:

```markdown
---
name: code-edit
description: Make a narrowly scoped code change...
---
```

Co the them metadata UI/agent trong:

```text
skills/<skill-name>/agents/openai.yaml
```

## Test harness

File chinh:

```text
run_all_cases.py
```

Liet ke test cases:

```powershell
python run_all_cases.py --list
```

Chay theo group:

```powershell
python run_all_cases.py --group project
python run_all_cases.py --group rag
python run_all_cases.py --group chain
python run_all_cases.py --group mcp_ext
python run_all_cases.py --group langgraph
python run_all_cases.py --group skill
python run_all_cases.py --group e2e
```

Group `chain` gom cac test nghiem tuc de ep agent dung nhieu MCP theo chuoi:

```text
chain_01_web_fetch_document_ledger
chain_02_document_filesystem_python_ledger
chain_03_playwright_fetch_document_ledger
chain_04_git_document_ledger_readonly
chain_05_rag_health_gate_document_ledger
chain_06_terminal_risk_metadata
chain_07_extended_mcp_core
```

`chain_06_terminal_risk_metadata` xac nhan Terminal MCP chi chay argv khong qua shell va moi ket qua co `command_metadata.summary` + `command_metadata.security_risk`.

`chain_07_extended_mcp_core` xac nhan Code Index, Lint/Test, Docker, Obsidian va Issue Tracker MCP duoc dang ky va chain duoc qua smoke deterministic.

Group `mcp_ext` gom prompt cases qua LLM cho tung MCP moi:

```text
mcp_ext_01_code_index
mcp_ext_02_lint_test
mcp_ext_03_docker
mcp_ext_04_obsidian
mcp_ext_05_issue
```

Chay deterministic MCP chain smoke, khong qua LLM:

```powershell
python run_mcp_chain_smoke.py
```

Runner nay dung de xac minh ban than MCP tools co chain duoc hay khong. Neu runner pass nhung `run_all_cases.py --group chain` fail, loi thuong nam o kha nang model/orchestrator lap ke hoach va goi tool dung thu tu.

Chay mot case:

```powershell
python run_all_cases.py --case rag_02_negative_search
```

Dung fail-fast:

```powershell
python run_all_cases.py --group rag --fail-fast
python run_all_cases.py --group chain --fail-fast
python run_all_cases.py --group mcp_ext --fail-fast
```

Ket qua nam trong:

```text
test_runs/<timestamp>/summary.md
test_runs/<timestamp>/summary.json
test_runs/<timestamp>/<case>.log
```

## Workflow phat trien

### Them MCP tool moi

1. Tao MCP server hoac chon external MCP server.
2. Them vao `MCP_SERVERS` trong `tools/mcp_config.py`.
3. Them tool names vao `MCP_TOOL_NAMES`.
4. Them alias vao `TOOL_ALIASES` neu can.
5. Them schema vao `tools/tool_schemas.py` de client validate input/output/error/metadata.
6. Cap nhat `build_tool_prompt()` neu muon agent thay huong dan ro hon.
7. Tao prompt test trong `prompts/auto_cases`.
8. Them deterministic smoke vao `run_mcp_chain_smoke.py` neu tool la core path.
9. Chay `python run_all_cases.py --case <case_name>`.

### Them skill moi

1. Tao folder `skills/<name>/`.
2. Tao `SKILL.md` co frontmatter `name` va `description`.
3. Them `agents/openai.yaml` neu can metadata.
4. Chay prompt kiem tra skills loaded.
5. Them skill test case neu skill co guardrail quan trong.

### Them tri thuc RAG

1. Dat file `.md`, `.txt`, hoac `.py` vao `workspace`.
2. Goi `rag.rag_health`.
3. Goi `rag.rag_ingest` voi path file/folder.
4. Goi `rag.rag_search` voi query va threshold phu hop.

## Guardrails hien co

- Agent phai tra JSON object duy nhat.
- Tool call phai dung protocol `{"action":"tool","tool":"server.tool","args":{...}}`; nhieu local tool co schema input/output/error/metadata trong `tools/tool_schemas.py`.
- Orchestrator retry khi JSON invalid.
- Neu cung mot tool call fail 2 lan, orchestrator ep agent final va phan loai loi.
- Neu cung mot tool call lap lai qua `ORCH_MAX_SAME_TOOL_CALLS`, orchestrator chan tiep de tranh loop.
- Filesystem/Python/RAG deu chan path ngoai `workspace`.
- File edit nen di qua `file_editor.*`; terminal chi dung cho validation/probe.
- Terminal MCP khong chay shell string, chi chay `argv`; moi result co `command_metadata.summary` va `command_metadata.security_risk`.
- Code Index MCP read-only va exclude thu muc lon de giu toc do.
- Lint/Test MCP la validation path uu tien sau code edit.
- Docker MCP khong expose delete/prune/rm; `up/stop` can env opt-in.
- Obsidian MCP sandbox vault local va chan noi dung giong secret/token.
- Issue Tracker MCP luu SQLite trong workspace cho bug/task/review/risk/blocker.
- Python MCP chi chay `.py`, co timeout.
- System prompt yeu cau doc file truoc khi sua file ton tai.
- Orchestrator co context condenser cho tool result truoc khi dua lai vao LLM, giup giam prompt growth.
- Finish gate chan final neu da sua code ma chua co validation pass sau do, tru khi agent bao ro blocker/dependency failure.
- Runtime hard-block Git mutation tru khi `AGENT_ALLOW_GIT_MUTATIONS=1`.
- Moi run co event log `MessageEvent`, `ActionEvent`, `ObservationEvent`, va `StateEvent`.
- `inspect_runs.py` cho phep list/search events tu local run logs, gan voi tinh than `/events/search` cua OpenHands.

## Known issues

- Mot so prompt/test case tieng Viet dang bi mojibake encoding. Nen rewrite lai UTF-8 sach neu muon doc/bao cao dep.
- Moi tool call MCP dang khoi dong stdio server moi, don gian nhung ton overhead.
- Schema validation da co cho cac local/custom MCP; external MCP van dua them vao schema cua server goc.
- RAG chi dung vector search, chua co reranker, metadata filter nang cao, hay source line ranges.
- Event log da co CLI inspect/search, nhung chua co viewer web/API.
- `OpenHands/` la repo clone lon, nen loai khoi nhieu thao tac search/test neu chi lam core project.

## Troubleshooting

### LLM request failed

Kiem tra LM Studio dang chay server tai `LLM_BASE_URL`, model da load dung ten, va API path `/v1/models` tra ket qua.

### Qdrant/RAG loi dependency

Chay:

```powershell
docker ps | Select-String qdrant
Invoke-RestMethod http://localhost:6333/collections
```

Sau do test:

```powershell
python main.py prompts/test_rag_02_negative_search.md
```

### Python MCP timeout

Kiem tra subprocess:

```powershell
python main.py prompts/auto_cases/test_project_00_python_probe.md
```

### MCP filesystem/context7 loi npx

Kiem tra Node/npx:

```powershell
npx --version
```

### Agent bi invalid JSON lien tuc

Giam task do phuc tap, giam output mong doi, hoac tang chat luong model. Orchestrator se stop sau `max_parse_errors`.

## Tai lieu doc tiep

Doc file nay de hieu repo theo thu tu:

```text
PROJECT_READING_GUIDE_VI.md
```

Doc OpenHands theo thu tu:

```text
OpenHands/OPENHANDS_READING_GUIDE_VI.md
```
