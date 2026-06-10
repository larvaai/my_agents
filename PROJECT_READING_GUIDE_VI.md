# Huong dan doc project my_agents theo thu tu

Tai lieu nay giai thich project `my_agents` nhu giai thich cho sinh vien nam cuoi: da biet Python, API, Docker, LLM co ban, nhung chua quen doc mot coding-agent co tool loop. Muc tieu la giup ban hieu "luong chay" truoc, roi moi di vao tung module.

## 0. Project nay la gi?

`my_agents` la mot lab coding-agent local. No khong co frontend rieng; no la mot CLI agent:

```text
python main.py <prompt_file>
```

Agent nhan task, goi LLM local, ep LLM tra JSON, goi MCP tools neu can, dua tool result ve LLM, lap lai cho den khi co final.

Hinh dung don gian:

```text
orchestrator = vong lap dieu khien
tool_agent   = LLM + system prompt + skills + tool list
mcp_client   = cong noi den tools
workspace    = sandbox file/code/RAG
```

## 1. Doc tu ngoai vao trong

Dung thu tu nay:

```text
README.md
main.py
orchestrator.py
tools/event_log.py
tools/event_reader.py
agents/tool_agent.py
llm.py
prompts/system_prompt.md
tools/prompt_loader.py
tools/skill_loader.py
tools/mcp_config.py
tools/mcp_client.py
tools/tool_policy.py
mcp_servers/python_sandbox.py
mcp_servers/rag_server.py
inspect_runs.py
run_all_cases.py
skills/*/SKILL.md
```

Sau khi doc xong moi nen doc `workspace/` va `prompts/auto_cases/`, vi do la du lieu test/sandbox, khong phai xuong song cua engine.

## 2. Chang 1: Entry point CLI

Doc:

```text
main.py
```

Can tra loi duoc:

- Prompt mac dinh doc tu dau?
- Neu truyen path thi doc prompt nao?
- Bien `ORCH_MAX_STEPS` anh huong gi?
- Ket qua final duoc in ra ra sao?

Luong chay:

```text
configure_console_encoding()
-> read_user_prompt(prompt_path)
-> run_orchestrator(task, max_steps)
-> print FINAL RESULT
```

Y tuong can nam: `main.py` rat mong. No chi la cong vao CLI.

## 3. Chang 2: Orchestrator loop

Doc:

```text
orchestrator.py
tools/event_log.py
tools/event_reader.py
inspect_runs.py
```

Day la file quan trong nhat cua project.

Doc theo cac ham:

```text
parse_json()
_json_retry_message()
_invalid_action_retry_message()
run_orchestrator()
```

Can tra loi duoc:

- Vi sao agent bi ep tra JSON?
- Khi LLM tra markdown/fenced JSON thi co recover duoc khong?
- Khi parse fail qua nhieu lan thi dung nhu the nao?
- Khi tool call fail hai lan giong nhau thi sao?
- Khi cung mot tool call lap lai qua nguong thi sao?
- Message history duoc append theo thu tu nao?
- Event log duoc ghi vao dau?

Vong lap chinh:

```text
messages = [user task]
for step:
  agent_output = tool_agent(messages)
  action = parse_json(agent_output)
  if action == final:
    return message
  if action == tool:
    tool_result = call_tool(tool, args)
    append assistant raw JSON
    append user tool_result JSON
```

Moi run ghi:

```text
agent_runs/<run_id>/events.jsonl
agent_runs/<run_id>/summary.json
agent_runs/index.jsonl
```

Event types hien co:

```text
MessageEvent       user prompt va assistant raw output
ActionEvent        final action hoac tool action
ObservationEvent   tool result
StateEvent         run_started, step_started, parse_error, stuck, run_finished
```

Y tuong can nam: orchestrator cua ban la "agent runtime nho". No khong thong minh, nhung no giu ky luat va de lai event trail de debug.

`inspect_runs.py` la local event browser:

```powershell
python inspect_runs.py list
python inspect_runs.py summary latest
python inspect_runs.py events latest --kind ActionEvent
python inspect_runs.py events latest --tool rag.rag_search
python inspect_runs.py events latest --text "outside workspace" --json
```

## 4. Chang 3: Tool agent va system prompt

Doc:

```text
agents/tool_agent.py
prompts/system_prompt.md
tools/prompt_loader.py
tools/skill_loader.py
```

`tool_agent.py` lam 3 viec:

```text
1. build_tool_prompt()
2. build_skills_prompt()
3. render_system_prompt()
4. call_llm(full_messages)
```

Trong `system_prompt.md`, de y nhung guardrails:

- JSON only.
- Khong invent tools.
- Filesystem nam trong workspace.
- Doc file truoc khi sua.
- Khong commit/reset/checkout neu user khong noi.
- RAG phai `rag_health` truoc.
- Tool failure phai phan loai.

Y tuong can nam: hanh vi agent hien tai phu thuoc rat nhieu vao system prompt. Neu prompt yeu, LLM de pha luat.

## 5. Chang 4: LLM adapter

Doc:

```text
llm.py
```

File nay boc OpenAI client de goi LM Studio.

Can tra loi duoc:

- Default base URL la gi?
- Model mac dinh la gi?
- Env nao override duoc?
- Timeout va max tokens o dau?
- Loi LLM duoc wrap thanh message nao?

Env quan trong:

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
LLM_TIMEOUT
LLM_MAX_TOKENS
```

Y tuong can nam: bat ky model OpenAI-compatible nao cung co the thay vao, mien la chat completions API khop.

## 6. Chang 5: MCP config

Doc:

```text
tools/mcp_config.py
tools/mcp_client.py
tools/tool_registry.py
tools/tool_policy.py
```

`mcp_config.py` dinh nghia:

- Project root.
- Workspace root.
- Danh sach MCP servers.
- Tool names moi server.
- Compatibility aliases.

Hien co 10 server:

```text
filesystem  -> npx @modelcontextprotocol/server-filesystem
git         -> python -m mcp_server_git
context7    -> npx @upstash/context7-mcp
python      -> python -m mcp_servers.python_sandbox
rag         -> python -m mcp_servers.rag_server
fetch       -> python -m mcp_servers.fetch_server
search      -> python -m mcp_servers.search_server
document    -> python -m mcp_servers.document_server
ledger      -> python -m mcp_servers.ledger_server
playwright  -> python -m mcp_servers.playwright_server
```

`mcp_client.py` lam viec nang:

- Resolve alias hoac `server.tool`.
- Check hard policy truoc khi goi MCP.
- Normalize filesystem path vao `workspace`.
- Normalize git args de them `repo_path`.
- Start MCP server qua stdio.
- Call tool.
- Dump result thanh dict co `ok`, `server`, `tool`.

`tool_policy.py` hard-block Git mutation mac dinh:

```text
git_add
git_commit
git_reset
git_checkout
git_create_branch
```

Muon cho phep trong mot run co chu y:

```powershell
$env:AGENT_ALLOW_GIT_MUTATIONS="1"
```

Y tuong can nam: agent khong goi shell truc tiep; agent goi JSON tool request, Python client moi noi sang MCP, va policy layer co quyen chan tool truoc khi no chay.

## 7. Chang 6: Workspace sandbox

Doc:

```text
tools/mcp_client.py
mcp_servers/python_sandbox.py
mcp_servers/rag_server.py
mcp_servers/document_server.py
mcp_servers/ledger_server.py
mcp_servers/playwright_server.py
```

Workspace mac dinh:

```text
D:\Agent PRJ\my_agents\workspace
```

Ba lop path guard:

- Filesystem args duoc resolve trong `mcp_client.py`.
- Python MCP dung `_safe_workspace_path`.
- RAG MCP dung `_safe_workspace_path`.
- Document MCP dung `_safe_workspace_path`.
- Ledger MCP ep ledger nam trong workspace.
- Playwright MCP chi ghi screenshot vao workspace.

Can tra loi duoc:

- Path tuong doi duoc noi voi workspace ra sao?
- Khi path la `../` thi bi chan o dau?
- Python co duoc chay file ngoai workspace khong?
- RAG co ingest file ngoai workspace khong?
- Document/ledger/playwright co ghi ra ngoai workspace duoc khong?

Y tuong can nam: day la boundary an toan quan trong nhat cua project.

## 8. Chang 7: Python MCP

Doc:

```text
mcp_servers/python_sandbox.py
```

Tools:

```text
run_python(path, timeout=10)
python_probe(timeout=10)
```

Dieu kien:

- File phai ton tai.
- Phai la file.
- Phai co suffix `.py`.
- Timeout bi clamp tu 1 den 30 giay.
- CWD la `workspace`.
- `PYTHONPATH` la `workspace`.

Y tuong can nam: day la validation runner nho, khong phai shell tuy y.

## 9. Chang 8: RAG MCP

Doc:

```text
mcp_servers/rag_server.py
docker-compose.yml
```

Qdrant chay bang:

```powershell
docker compose up -d qdrant
```

RAG flow:

```text
rag_health()
  -> kiem tra Qdrant va collection

rag_ingest(path)
  -> resolve path trong workspace
  -> collect .md/.txt/.py
  -> chunk text
  -> embed bang fastembed
  -> delete old chunks by source
  -> upsert vao Qdrant

rag_search(query)
  -> embed query
  -> query Qdrant
  -> loc score_threshold
  -> tra hits
```

Can tra loi duoc:

- Collection mac dinh ten gi?
- Embedding model mac dinh ten gi?
- File extensions nao duoc ingest?
- Re-ingest cung source co xoa du lieu cu khong?
- Score threshold anh huong false positive ra sao?

Y tuong can nam: RAG la memory/search ngoai prompt. Dung dung se giam context rac.

## 10. Chang 9: Web, document, ledger, UI MCP

Doc:

```text
mcp_servers/fetch_server.py
mcp_servers/search_server.py
mcp_servers/document_server.py
mcp_servers/ledger_server.py
mcp_servers/playwright_server.py
```

Vai tro:

```text
fetch      -> lay text tu mot URL HTTP/HTTPS
search     -> tim web qua Brave/Tavily hoac DuckDuckGo fallback
document   -> doc/viet/outline tai lieu trong workspace
ledger     -> append-only memory/audit JSONL
playwright -> doc text va chup screenshot tu page render bang browser
```

Can tra loi duoc:

- Search khac fetch o diem nao?
- Khi nao page can Playwright thay vi fetch?
- Document MCP khac filesystem MCP o diem nao?
- Ledger luu tri dang gi va o dau?
- Nhung dependency nao la optional: `pypdf`, `python-docx`, `playwright`, Chromium browser binary?

Y tuong can nam: day la nhom tool dua project gan hon coding-agent thuc dung, vi agent co the research web, doc artifact, ghi lai quyet dinh, va nhin UI thay vi chi sua file.

## 11. Chang 10: Skills

Doc:

```text
skills/project-plan/SKILL.md
skills/code-edit/SKILL.md
skills/debug-traceback/SKILL.md
skills/run-test/SKILL.md
skills/git-review/SKILL.md
tools/skill_loader.py
```

Skill format:

```markdown
---
name: project-plan
description: ...
---

# Project Plan
...
```

Skill loader:

- Tim `skills/*/SKILL.md`.
- Parse YAML frontmatter don gian.
- Doc optional `agents/openai.yaml`.
- Render vao system prompt.

Can phan biet:

- Skill khong phai tool.
- Skill la instruction/workflow.
- Tool moi thuc thi hanh dong.

Y tuong can nam: skills la cach dat "thoi quen lam viec" cho agent.

## 12. Chang 11: Prompts

Doc:

```text
prompts/system_prompt.md
prompts/user_prompt.md
prompts/test_mcp_prompt.md
prompts/test_rag_*.md
prompts/auto_cases/
prompts/skill_cases/
```

Can biet:

- `system_prompt.md` la prompt runtime that.
- `user_prompt.md` la task mac dinh khi chay `python main.py`.
- `auto_cases` va `skill_cases` la prompt test.
- Mot so file tieng Viet dang bi mojibake; nen sua encoding sau neu muon dung lam tai lieu nguoi doc.

Y tuong can nam: prompt la test fixture va policy layer, khong chi la van ban mau.

## 13. Chang 12: Test harness

Doc:

```text
run_all_cases.py
write_skill_cases.py
test_runs/
```

`run_all_cases.py` lam:

- Dinh nghia `TestCase`.
- Ghi prompt ra `prompts/auto_cases`.
- Chay `python main.py <prompt>`.
- Bat timeout.
- Check output co/khong co substring.
- Ghi log va summary.

Lenh quan trong:

```powershell
python run_all_cases.py --list
python run_all_cases.py --group project
python run_all_cases.py --group rag --fail-fast
python run_all_cases.py --case rag_02_negative_search
```

Can tra loi duoc:

- Test case pass/fail dua tren dieu kien nao?
- Log nam o dau?
- Khi timeout thi ghi gi?
- Co group nao: `rag`, `project`, `agent`, `skill`, `e2e`, `orchestrator`.

Y tuong can nam: day la bo regression test cho hanh vi agent, khong phai unit test truyen thong.

## 13. Luong end-to-end can ve lai bang tay

Hay tu ve 14 buoc:

```text
1. User chay python main.py prompts/x.md
2. main.py doc prompt
3. orchestrator tao messages
4. tool_agent render system prompt
5. skill_loader chen skills
6. mcp_client chen tool list
7. llm.py goi LM Studio
8. LLM tra JSON action
9. orchestrator parse JSON
10. Neu action=tool, tool_registry goi mcp_client
11. mcp_client goi MCP server
12. Tool result quay ve orchestrator
13. Tool result duoc append vao messages
14. Lap lai den action=final
```

Neu ban noi duoc file/function cho tung buoc, ban da hieu project.

## 14. Nen hoc gi tu OpenHands de nang project nay

Project nay da co:

- JSON discipline.
- MCP tool boundary.
- Workspace sandbox.
- RAG local.
- Skills.
- Test harness.
- OpenHands-style event log nho gon.
- Local event search/list qua `inspect_runs.py`.
- Runtime policy block cho Git mutation.
- Stuck detection cho repeated tool calls.

Tu OpenHands nen hoc them:

- Persistent conversation history.
- Runtime sandbox lifecycle ro hon.
- UI/log viewer hoac API event search.
- Metrics token/step/tool.
- Multi-agent orchestration ben ngoai.

## 15. Known risks nen sua sau

### 1. Encoding mojibake

Nhieu prompt/test file tieng Viet dang hien sai encoding. Nen rewrite UTF-8 sach, vi prompt loi co the lam model hieu kem.

### 2. MCP stdio moi call khoi dong server moi

Don gian va de debug, nhung cham. Sau nay co the tao persistent MCP sessions.

### 3. JSON schema con long

Nen validate:

- `action` bat buoc.
- `tool` bat buoc neu action tool.
- `args` phai la object.
- tool name nam trong allowlist.
- final message co kieu mong doi.

### 4. RAG chua co source line ranges

Hits co `source` va `chunk_index`, nhung chua co line start/end. Neu dung de sua code, line ranges se huu ich hon.

### 5. Event log chua co viewer/API

Hien da co event JSONL va CLI inspect/search, nhung chua co viewer web/API. Co the xay tiep:

```text
agent_runs/<run_id>/events.jsonl -> local viewer web / API search
```

Day la cau noi de sau nay lam UI hoac multi-agent.

## 16. Checklist khi sua project

Truoc khi sua:

- Xac dinh task thuoc core, tool, skill, RAG hay test harness.
- Doc file lien quan.
- Kiem tra worktree neu lien quan git.

Khi sua:

- Sua nho.
- Khong dung vao `OpenHands/` neu task khong lien quan.
- Khong sua file trong `workspace/` neu do chi la test fixture, tru khi task yeu cau.
- Khong xoa `qdrant_storage/` neu khong co ly do.

Sau khi sua:

- Chay validation hep nhat.
- Neu lien quan RAG: chay `rag_health`/case RAG.
- Neu lien quan skill: chay skill case.
- Neu lien quan orchestrator: chay project/orchestrator case.

## 17. Ket luan

`my_agents` hien la mot coding-agent lab rat tot de hoc va tien hoa dan: nho hon OpenHands nen de nam, nhung da co cac thanh phan quan trong cua mot agent that: LLM adapter, orchestrator loop, tools, sandbox, RAG, skills, va regression prompts.

Doc theo thu tu nay se giup ban thay ro moi thay doi nen nam o dau. Khi muon nang cap, hay uu tien hard policy, event log, workspace lifecycle, va multi-agent orchestrator.
