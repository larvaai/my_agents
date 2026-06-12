# Self Eval QA Lab

Mini repo nay test cau hoi quan trong:

```text
Lens/multi-step answer flow co that su tot hon simple answer khong?
```

v0.2 khong lam full self-improvement va khong sinh code. No tap trung do routing:

```text
Question
  -> Question Classifier
  -> Workflow Router
  -> Simple Answer
  -> Direct / Assisted / Deep / Repo Debug Answer Path
  -> Auto Baseline Answer when route asks for it
  -> Blind Evaluator
  -> Error Analyzer
  -> Flow Observer
  -> Lesson Extractor
  -> Ledger
```

## Chay nhanh

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
  answers/simple.md
  answers/ours.md
  answers/baseline.md
```

Ledger append-only:

```text
var/self_eval_qa_lab/ledger/runs.jsonl
var/self_eval_qa_lab/ledger/evaluations.jsonl
var/self_eval_qa_lab/ledger/flow_observations.jsonl
var/self_eval_qa_lab/ledger/lessons.jsonl
var/self_eval_qa_lab/ledger/update_proposals.jsonl
```

## Design Notes

- Simple answer is always present as a baseline.
- Workflow Router chooses `direct`, `assisted`, `deep`, or `repo_debug`.
- Lens-based answer is now the `deep` path; `--force-lenses` maps to `deep`.
- `--baseline-mode auto` runs baseline only when the selected workflow requests it.
- Evaluator is blind: it sees `answer_a`, `answer_b`, `answer_c`, not source names.
- Flow Observer evaluates process quality, not answer quality.
- Lesson Extractor records routing lessons before any prompt/lens update proposal.
- Update proposals are disabled by default and proposal-only when enabled.
- This lab should prove value before any lens becomes a specialist agent.

## Files

```text
agents/      Prompt roles for classifier, answerer, evaluator, analyzer, observer
lenses/      Lens instructions used by lens-based answer generator
rubrics/     Answer and flow quality rubrics
questions/   Sample questions
main.py      CLI runner
config.yaml  Default modes and lens list
routing_policy.yaml  v0.2 deterministic workflow routing policy
```
