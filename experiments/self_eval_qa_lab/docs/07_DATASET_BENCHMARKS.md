# Dataset Benchmarks

This mini repo can run Open CoT Leaderboard-style benchmark cases as batched QA jobs.

## Source

Default source:

- Hugging Face dataset: `logikon/logikon-bench`
- Dataset page: https://huggingface.co/datasets/logikon/logikon-bench
- Local manifest: `experiments/self_eval_qa_lab/datasets/logikon_bench_manifest.json`

The manifest points to these subsets:

- `logiqa`
- `logiqa2`
- `lsat-ar`
- `lsat-lr`
- `lsat-rc`

The runner caches downloaded JSONL files under `var/self_eval_qa_lab/datasets/`.
Do not vendor the full dataset into the repo unless the license and distribution plan are reviewed.

## Run 20 Cases

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

Real local model:

```powershell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_API_KEY="lm-studio"
$env:LLM_MODEL="<loaded model name>"
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 20 --subsets logiqa --review-every 20 --chatgpt-mode mock
```

Real server model:

```powershell
$env:SELF_EVAL_SERVER_URL="https://your-server.example/v1"
$env:SELF_EVAL_SERVER_API_KEY="..."
$env:SELF_EVAL_SERVER_MODEL="<model>"
python main.py lab self_eval_qa_lab dataset --llm-provider server --limit 20 --subsets logiqa --review-every 20 --chatgpt-mode mock
```

## Batch Rule

The runner does not review or adjust after every case.
It only runs `batch_critical_review` when completed case count is exactly divisible by `--review-every`.
Default cadence is 20:

- cases 1-19: run and log only
- case 20: review cases 1-20, then adjust runtime policy for the next batch
- cases 21-39: run with the updated policy
- case 40: review cases 21-40, then adjust again

This forces evidence-based changes instead of reacting to a single noisy case.

## Accuracy Gate

The runner does not change workflow based on low accuracy until the final-answer parser is reliable.
If fewer than 95% of cases are parseable, the batch review may tighten `prompt_style`, but it must not treat `0/N` as reasoning failure yet.
Once parse success is reliable, low accuracy can move the next batch from router-selected flow to `assisted`, then to `deep` if repeated evidence supports it.

## What Gets Logged

Each dataset run creates:

```text
var/self_eval_qa_lab/dataset_runs/<dataset_run_id>/
  dataset_manifest.json
  case_results.jsonl
  cases/<case>.json
  case_runs/<normal_lab_run_id>/
  batch_reviews/batch_0001_review.json
  runtime_policy.json
  summary.md
```

Each normal lab run still writes its own `admin/full_trace.json`, prompts, outputs, handoffs, audits, and trace health.

## Answer Scoring

Cases are rendered as multiple-choice tasks and tell the final agent to end with:

```text
Answer: <letter>
```

The benchmark parser accepts common variants like `Final answer: A`, `option A`, or an exact unique option text.
The score compares only the final option letter against the answer key.

## CoT Boundary

The dataset runner uses questions, options, and final answer keys.
It does not feed or expose reference chain-of-thought fields.
Admin logs include full prompts, raw emitted outputs, public rationales, trace events, and handoffs, but not fabricated hidden reasoning.
