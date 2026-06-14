# Real LLM Testing

The real LLM test is intentionally opt-in because it calls an external/local model and can be slow.

## Enable

```powershell
$env:RUN_SELF_EVAL_REAL_LLM="1"
```

## Local LM Studio

```powershell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_API_KEY="lm-studio"
$env:LLM_MODEL="<loaded model name>"
$env:SELF_EVAL_REAL_LLM_PROVIDER="local"
$env:SELF_EVAL_REAL_CHATGPT_MODE="local"
python -m unittest tests.test_self_eval_qa_lab_real_llm
```

## Server

```powershell
$env:RUN_SELF_EVAL_REAL_LLM="1"
$env:SELF_EVAL_REAL_LLM_PROVIDER="server"
$env:SELF_EVAL_SERVER_URL="https://your-server.example/v1"
$env:SELF_EVAL_SERVER_API_KEY="..."
$env:SELF_EVAL_SERVER_MODEL="your-model"
$env:SELF_EVAL_REAL_CHATGPT_MODE="server"
python -m unittest tests.test_self_eval_qa_lab_real_llm
```

## Tunables

```text
SELF_EVAL_REAL_LLM_TIMEOUT=60
SELF_EVAL_REAL_LLM_MAX_TOKENS=768
SELF_EVAL_REAL_LLM_MODEL=<override model>
SELF_EVAL_REAL_LLM_QUESTION=<override question>
```

## Pass Criteria

The test fails if:

- trace health status is not clean
- any JSON agent falls back because output is invalid JSON
- any handoff loop is detected
- any no-code agent emits code
- repeated outputs suggest agents are parroting each other
- critical audit logic score is below 6

## Debug Procedure

1. Open `summary.md`.
2. Open `audits/trace_health.json`.
3. Open `audits/critical_audit.json`.
4. Open `admin/full_trace.json`.
5. Inspect the exact agent output in `outputs/*.md`.
6. Check whether a repair or sanitizer event already corrected the raw output.
7. Fix the smallest responsible prompt, schema, routing rule, or guard.
8. Rerun the same real LLM test.

Do not add a new agent until the trace proves an existing agent cannot be gated or prompted into doing the job.
