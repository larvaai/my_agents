# Self Eval QA Lab

Mini repo nay test cau hoi quan trong:

```text
Lens/multi-step answer flow co that su tot hon simple answer khong?
```

v0.3 khong sinh code. No tap trung full trace, ChatGPT baseline, critical audit, va evolution proposal:

```text
Question
  -> Run Planner
  -> Question Classifier
  -> Workflow Router
  -> Simple Answer
  -> Direct / Assisted / Deep / Repo Debug Answer Path
  -> Auto Baseline Answer when route asks for it
  -> ChatGPT Baseline
  -> Blind Evaluator
  -> Error Analyzer
  -> Flow Observer
  -> Lesson Extractor
  -> Critical Auditor
  -> Evolution Decider
  -> Ledger
```

## Chay nhanh

Docs noi bo:

```text
docs/README.md
docs/01_ARCHITECTURE.md
docs/02_RUNBOOK.md
docs/03_TRACE_AND_AUDIT.md
docs/04_REAL_LLM_TESTING.md
docs/05_PRODUCTION_CHECKLIST.md
docs/06_AGENT_CONTRACTS.md
docs/07_DATASET_BENCHMARKS.md
docs/evolution_proposals/README.md
docs/evolution_proposals/EP-0001_XML_FIRST_STRUCTURED_OUTPUT.md
docs/evolution_proposals/EP-0002_GOVERNED_SELF_EVOLUTION.md
docs/evolution_proposals/EP-0003_USER_AGENT_INTERRUPT_CONTROL.md
docs/run_file_map/README.md
docs/run_file_map/00_NEW_CONTRIBUTOR_GUIDE.md
docs/run_file_map/01_RUN_ENTRYPOINTS.md
docs/run_file_map/02_INTERNAL_SOURCE_FILES.md
docs/run_file_map/03_AGENT_PROMPTS_AND_CONTRACTS.md
docs/run_file_map/04_EXTERNAL_PROJECT_FILES.md
docs/run_file_map/05_RUNTIME_DATA_OUTPUTS_AND_TESTS.md
docs/run_file_map/06_DETAILED_PROMPT_FLOW.md
```

List assets:

```powershell
python main.py lab self_eval_qa_lab --list
```

Dry run, khong goi LLM:

```powershell
python main.py lab self_eval_qa_lab --dry-run "Co nen dung multi-agent cho cau hoi nay khong?"
```

Ep workflow de test router:

```powershell
python main.py lab self_eval_qa_lab --mock --workflow direct "Fallback la gi?"
python main.py lab self_eval_qa_lab --mock --workflow assisted "JSON agent co nen temp=0 khong?"
python main.py lab self_eval_qa_lab --mock --workflow deep --question-file experiments/self_eval_qa_lab/questions/sample_multi_agent_design.md
python main.py lab self_eval_qa_lab --mock --workflow repo_debug "Repo test fail trong file main.py la gi?"
```

Mock run, khong goi LLM nhung tao day du output:

```powershell
python main.py lab self_eval_qa_lab --mock --question-file experiments/self_eval_qa_lab/questions/sample_multi_agent_design.md
```

Open CoT Leaderboard-style dataset batch. Review/adjust chi chay sau moi 20 case:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 20 --subsets logiqa --review-every 20 --chatgpt-mode mock
```

ChatGPT baseline:

```powershell
# mock: tu tao ChatGPT-style baseline de test deterministic
python main.py lab self_eval_qa_lab --mock --chatgpt-mode mock "question"

# manual: tao prompts/chatgpt_prompt.md de dan vao ChatGPT, sau do rerun voi file answer
python main.py lab self_eval_qa_lab --chatgpt-mode manual "question"
python main.py lab self_eval_qa_lab --chatgpt-answer-file path/to/chatgpt_answer.md "question"

# server: goi OpenAI-compatible server lam ChatGPT baseline
python main.py lab self_eval_qa_lab --chatgpt-mode server --server-url "https://your-server.example/v1" --server-model "your-model" "question"
```

Real run qua `llm.py`, mac dinh khong goi baseline rieng:

```powershell
python main.py lab self_eval_qa_lab --llm-provider local "Critical thinking giup toi y tuong self-eval QA lab"
```

Real run co local baseline. Mac dinh `--baseline-mode auto`: chi route `deep` moi goi baseline; `direct`, `assisted`, `repo_debug` se skip baseline.

```powershell
python main.py lab self_eval_qa_lab --llm-provider local --baseline-mode local "Critical thinking giup toi y tuong self-eval QA lab"
```

## LLM Provider

Option 1: local model qua `llm.py` va LM Studio. Day la default.

```powershell
python main.py lab self_eval_qa_lab --llm-provider local "question"
```

Local provider dung cac bien co san cua `llm.py`:

```text
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=<local model name>
```

Option 2: server OpenAI-compatible. URL co the set sau bang CLI hoac env.

```powershell
python main.py lab self_eval_qa_lab --llm-provider server --server-url "https://your-server.example/v1" --server-model "your-model" "question"
```

Hoac set env:

```powershell
$env:SELF_EVAL_SERVER_URL="https://your-server.example/v1"
$env:SELF_EVAL_SERVER_API_KEY="..."
$env:SELF_EVAL_SERVER_MODEL="your-model"
python main.py lab self_eval_qa_lab --llm-provider server "question"
```

Chay truc tiep:

```powershell
python experiments/self_eval_qa_lab/main.py --mock "question"
```

## Output

Moi run ghi vao:

```text
var/self_eval_qa_lab/<run_id>/
  run.json
  summary.md
  admin/full_trace.json
  answers/simple.md
  answers/ours.md
  answers/final.md
  answers/chatgpt.md
  answers/baseline.md
  audits/chatgpt_comparison.json
  audits/critical_audit.json
  audits/evolution_decision.json
  audits/trace_health.json
  prompts/*.md
  outputs/*.md
  traces/events.jsonl
  traces/agent_calls.jsonl
  traces/handoffs.jsonl
```

Ledger append-only:

```text
var/self_eval_qa_lab/ledger/runs.jsonl
var/self_eval_qa_lab/ledger/evaluations.jsonl
var/self_eval_qa_lab/ledger/flow_observations.jsonl
var/self_eval_qa_lab/ledger/lessons.jsonl
var/self_eval_qa_lab/ledger/critical_audits.jsonl
var/self_eval_qa_lab/ledger/evolution_decisions.jsonl
var/self_eval_qa_lab/ledger/trace_health.jsonl
var/self_eval_qa_lab/ledger/update_proposals.jsonl
```

Dataset runs ghi vao:

```text
var/self_eval_qa_lab/dataset_runs/<dataset_run_id>/
  dataset_manifest.json
  case_results.jsonl
  cases/*.json
  case_runs/<run_id>/
  batch_reviews/batch_0001_review.json
  runtime_policy.json
  summary.md
```

## Design Notes

- Simple answer is always present as a baseline.
- Workflow Router chooses `direct`, `assisted`, `deep`, or `repo_debug`.
- Lens-based answer is now the `deep` path; `--force-lenses` maps to `deep`.
- `--baseline-mode auto` runs baseline only when the selected workflow requests it.
- Evaluator is blind: it sees `answer_a`, `answer_b`, `answer_c`, not source names.
- Flow Observer evaluates process quality, not answer quality.
- Lesson Extractor records routing lessons before any prompt/lens update proposal.
- Critical Auditor checks whether the flow was logical, wasteful, missing agents, or multi-agent theater.
- Evolution Decider can propose adding/removing/modifying agents, flow, outputs, skills, or tools, but never applies changes automatically.
- Admin full trace stores prompts, inputs, raw outputs, public rationales, and handoffs without truncation.
- Trace Health detects repeated outputs, JSON fallback, tiny outputs, code violations, duplicate agent steps, and handoff loops.
- Update proposals are disabled by default and proposal-only when enabled.
- This lab should prove value before any lens becomes a specialist agent.

## Files

```text
agents/      Prompt roles for classifier, answerer, evaluator, analyzer, observer
lenses/      Lens instructions used by lens-based answer generator
rubrics/     Answer and flow quality rubrics
questions/   Sample questions
main.py      CLI runner
dataset_loader.py   Logikon Bench loader, cache, answer parser
dataset_runner.py   Batched dataset runner with review every 20 cases
config.yaml  Default modes and lens list
routing_policy.yaml  deterministic workflow routing policy
```
