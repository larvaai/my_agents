# 05 Runtime Data Outputs And Tests

This file explains generated files and how to verify the mini repo.

## Default Output Root

Default single-run output:

```text
var/self_eval_qa_lab/<run_id>/
```

Default dataset-run output:

```text
var/self_eval_qa_lab/dataset_runs/<dataset_run_id>/
```

Default dataset cache:

```text
var/self_eval_qa_lab/datasets/
```

Override single-run output:

```powershell
python main.py lab self_eval_qa_lab --mock --out-dir var/tmp_self_eval "question"
```

Override dataset-run output:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --out-dir var/tmp_self_eval_dataset --limit 20
```

## Single-run Output Tree

Each run writes:

```text
var/self_eval_qa_lab/<run_id>/
  run.json
  summary.md
  admin/
    full_trace.json
  answers/
    simple.md
    ours.md
    final.md
    chatgpt.md or chatgpt_pending.md
    baseline.md
  audits/
    chatgpt_comparison.json
    critical_audit.json
    evolution_decision.json
    trace_health.json
  proposals/
    evolution_decision.json
  prompts/
    user_prompt.md
    *.system.md
    *.user.md
    chatgpt_prompt.md
  outputs/
    *.md
  traces/
    events.jsonl
    agent_calls.jsonl
    handoffs.jsonl
```

Important files:

| File | Meaning |
|---|---|
| `run.json` | Full structured result for the run. |
| `summary.md` | Human-readable run summary. |
| `admin/full_trace.json` | No-truncation admin trace with prompts, outputs, rationales, handoffs. |
| `answers/simple.md` | Simple single-agent answer baseline. |
| `answers/ours.md` | Selected workflow answer. |
| `answers/final.md` | Current final answer alias; same as our answer. |
| `answers/chatgpt.md` | ChatGPT baseline answer when available. |
| `answers/chatgpt_pending.md` | Manual baseline placeholder when ChatGPT answer is pending. |
| `answers/baseline.md` | Optional local external baseline. |
| `audits/critical_audit.json` | Critical self-audit of the agent process. |
| `audits/evolution_decision.json` | Proposal-only evolution decision. |
| `audits/trace_health.json` | Loop/repetition/fallback/tiny-output/code-violation health report. |
| `traces/events.jsonl` | Compact event stream. |
| `traces/agent_calls.jsonl` | Compact agent-call stream. |
| `traces/handoffs.jsonl` | Agent handoff stream. |

## Single-run Ledger

Append-only ledger files live under:

```text
var/self_eval_qa_lab/ledger/
```

Files:

```text
runs.jsonl
evaluations.jsonl
flow_observations.jsonl
lessons.jsonl
critical_audits.jsonl
evolution_decisions.jsonl
trace_health.jsonl
update_proposals.jsonl
```

These are useful for later cross-run analysis and evolution proposals.

## Dataset-run Output Tree

Each dataset run writes:

```text
var/self_eval_qa_lab/dataset_runs/<dataset_run_id>/
  dataset_manifest.json
  case_results.jsonl
  runtime_policy.json
  summary.md
  cases/
    00001_*.json
    00002_*.json
  case_runs/
    <run_id>/
      run.json
      summary.md
      admin/full_trace.json
      ...
  batch_reviews/
    batch_0001_review.json
```

Important files:

| File | Meaning |
|---|---|
| `dataset_manifest.json` | Dataset source, subsets, case list, seed, review cadence. |
| `case_results.jsonl` | One compact result per case. |
| `cases/*.json` | Per-case expanded result. |
| `case_runs/<run_id>/` | Full normal single-run output for each dataset case. |
| `batch_reviews/*.json` | Batch review after every `--review-every` cases. |
| `runtime_policy.json` | Current dataset runtime policy after batch adjustments. |
| `summary.md` | Dataset-level metrics and recommendations. |

## Dataset Cache

Downloaded JSONL files are cached under:

```text
var/self_eval_qa_lab/datasets/logikon-bench/
```

The loader uses the manifest paths, for example:

```text
data/AGIEval/logiqa-en.jsonl
data/AGIEval/lsat-ar.jsonl
data/AGIEval/lsat-lr.jsonl
data/AGIEval/lsat-rc.jsonl
data/LogiQA20/logiqa_20_en.jsonl
```

Refresh cache:

```powershell
python main.py lab self_eval_qa_lab dataset --refresh-dataset --limit 20
```

## Fast Verification

Mock single run:

```powershell
python main.py lab self_eval_qa_lab --mock "JSON agent co nen temp=0 khong?"
```

Mock dataset batch:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

Unit tests:

```powershell
python -m unittest tests.test_self_eval_qa_lab tests.test_self_eval_qa_lab_dataset tests.test_mini_repo_registry
```

All tests:

```powershell
python -m unittest discover -s tests
```

Opt-in real LLM test:

```powershell
$env:RUN_SELF_EVAL_REAL_LLM="1"
python -m unittest tests.test_self_eval_qa_lab_real_llm
```

## Real Local LLM Smoke

Start LM Studio OpenAI-compatible server, then:

```powershell
python main.py lab self_eval_qa_lab --llm-provider local --chatgpt-mode mock --baseline-mode none "JSON agent co nen temp=0 khong?"
```

Real dataset smoke:

```powershell
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 3 --subsets logiqa --review-every 20 --chatgpt-mode mock --baseline-mode none --prompt-style strict_final
```

## Server LLM Smoke

```powershell
python main.py lab self_eval_qa_lab --llm-provider server --server-url "https://your-server.example/v1" --server-model "your-model" --server-api-key "..." "question"
```

Or set env first:

```powershell
$env:SELF_EVAL_SERVER_URL="https://your-server.example/v1"
$env:SELF_EVAL_SERVER_API_KEY="..."
$env:SELF_EVAL_SERVER_MODEL="your-model"
python main.py lab self_eval_qa_lab --llm-provider server "question"
```

## Production-readiness Check

Before treating a change as stable:

```powershell
python -m unittest discover -s tests
python main.py lab self_eval_qa_lab --mock "smoke question"
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

For model-specific changes, add:

```powershell
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 20 --subsets logiqa --review-every 20 --chatgpt-mode mock --baseline-mode none --prompt-style strict_final
```
