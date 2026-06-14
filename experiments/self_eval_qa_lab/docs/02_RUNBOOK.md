# Runbook

## List Assets

```powershell
python main.py lab self_eval_qa_lab --list
```

## Dry Run

```powershell
python main.py lab self_eval_qa_lab --dry-run "Co nen dung multi-agent cho cau hoi nay khong?"
```

## Deterministic Mock Runs

```powershell
python main.py lab self_eval_qa_lab --mock --workflow direct "Fallback la gi?"
python main.py lab self_eval_qa_lab --mock --workflow assisted "JSON agent co nen temp=0 khong?"
python main.py lab self_eval_qa_lab --mock --workflow deep --question-file experiments/self_eval_qa_lab/questions/sample_multi_agent_design.md
python main.py lab self_eval_qa_lab --mock --workflow repo_debug "Repo test fail trong file main.py la gi?"
```

## Real Local LLM

Requires LM Studio or another OpenAI-compatible local server.

```powershell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_API_KEY="lm-studio"
$env:LLM_MODEL="<loaded model name>"
python main.py lab self_eval_qa_lab --llm-provider local --chatgpt-mode local --baseline-mode none "JSON agent co nen temp=0 khong?"
```

## Real Server LLM

```powershell
$env:SELF_EVAL_SERVER_URL="https://your-server.example/v1"
$env:SELF_EVAL_SERVER_API_KEY="..."
$env:SELF_EVAL_SERVER_MODEL="your-model"
python main.py lab self_eval_qa_lab --llm-provider server --chatgpt-mode server "question"
```

## Dataset Benchmark

Run exactly one 20-case batch and review only after case 20:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

Real local model:

```powershell
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 20 --subsets logiqa --review-every 20 --chatgpt-mode mock
```

## Manual ChatGPT Baseline

First run:

```powershell
python main.py lab self_eval_qa_lab --chatgpt-mode manual "question"
```

Then copy `prompts/chatgpt_prompt.md` from the run folder into ChatGPT, save the answer, and rerun:

```powershell
python main.py lab self_eval_qa_lab --chatgpt-answer-file path/to/chatgpt_answer.md "question"
```

## Where To Inspect

- `summary.md`: human-readable run overview.
- `admin/full_trace.json`: no-truncation admin trace.
- `audits/trace_health.json`: mechanical loop/fallback/code checks.
- `audits/critical_audit.json`: critical agent judgment.
- `audits/evolution_decision.json`: proposal-only changes.
- `traces/agent_calls.jsonl`: quick event stream.
