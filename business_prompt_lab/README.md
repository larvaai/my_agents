# Business Prompt Lab

Mini repo nay co 2 che do rieng, deu nam gon trong `business_prompt_lab` va dung chung `llm.py`:

- `agent_room.py`: cho agent noi chuyen voi nhau, tu giao viec, review, va agent cuoi tong hop cau tra loi. Che do nay khong sinh code.
- `run.py`: prompt benchmark cu de test prompt phan tich business va cham diem JSON output.
- `repo_understanding_lab/`: mini repo doc hieu codebase theo file map, symbol map, graph, test map, context pack, va No-Leap Guardian. Co runner mock/real scanner va da register vao `main.py lab`.

## No-code agent room

Chay mock khong goi LLM, de xem dung luong dieu phoi:

```powershell
python business_prompt_lab/agent_room.py "Toi nen validate y tuong SaaS nay nhu the nao?" --mock
python main.py lab business_prompt_lab --mock "Toi nen validate y tuong SaaS nay nhu the nao?"
```

Chay that qua `llm.py`:

```powershell
python business_prompt_lab/agent_room.py "Toi nen uu tien go-to-market hay product discovery?"
python main.py lab business_prompt_lab "Toi nen uu tien go-to-market hay product discovery?"
```

Chay bang PowerShell wrapper:

```powershell
.\business_prompt_lab\talk.ps1 "Hay dung agent de phan tich co nen launch add-on invoice reconciliation khong"
```

Dung question file:

```powershell
python business_prompt_lab/agent_room.py --question-file business_prompt_lab/questions/sample_strategy_question.md
```

Xem roster va task board fallback, khong goi LLM:

```powershell
python business_prompt_lab/agent_room.py "Thiet ke luong agent tu giao viec" --dry-run
python main.py lab business_prompt_lab:agent-room "Thiet ke luong agent tu giao viec" --dry-run
```

Ket qua nam trong:

```text
var/business_prompt_lab/agent_room/<timestamp>/final.md
var/business_prompt_lab/agent_room/<timestamp>/transcript.md
var/business_prompt_lab/agent_room/<timestamp>/transcript.json
```

Luồng chi tiet nam trong `business_prompt_lab/NO_CODE_AGENT_FLOW.md`.

## Chay nhanh

```powershell
python business_prompt_lab/run.py --dry-run
python business_prompt_lab/run.py
```

Chay mot prompt nhieu lan de xem do on dinh:

```powershell
python business_prompt_lab/run.py --prompt p03 --runs 3 --temperature 0.1
```

Chay tat ca prompt tren tat ca case:

```powershell
python business_prompt_lab/run.py --case all --prompt all --runs 2 --temperature 0.1
```

Ket qua nam trong:

```text
var/business_prompt_lab/<timestamp>/summary.md
var/business_prompt_lab/<timestamp>/summary.json
var/business_prompt_lab/<timestamp>/outputs/*.txt
var/business_prompt_lab/<timestamp>/inputs/*.md
```

## Cach sua

- Them/sua prompt trong `business_prompt_lab/prompts/*.md`.
- Them/sua bai test business trong `business_prompt_lab/cases/*.json`.
- Runner tu import `llm.py`, nen van dung `.env` va cac bien `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_MAX_TOKENS`.

## Cach cham diem

Runner cham diem output theo muc do kiem soat:

- JSON hop le va khong boc markdown.
- Dung top-level schema.
- Co recommendation, confidence, rationale.
- Co business model, market, risks, assumptions, unknowns, next steps.
- Risk va next step du thong tin hanh dong.
- Executive summary ngan gon.

Diem nay do prompt discipline, khong phai chan ly business. Sau khi loc prompt diem cao, van can doc `outputs/*.txt` de danh gia chat luong lap luan.

## Repo Understanding Lab

Doc proposal nam o:

```text
business_prompt_lab/repo_understanding_lab/README.md
business_prompt_lab/repo_understanding_lab/docs/00_START_HERE.md
```

Muc tieu la thiet ke mot lab de agent hieu repo truoc khi tra loi hoac de xuat sua code. Hien da co mock runner va scanner Python stdlib:

```powershell
python main.py lab repo-understanding --mock ask "How does PlannerAgent work?"
python main.py lab repo-understanding baseline --repo .
```
