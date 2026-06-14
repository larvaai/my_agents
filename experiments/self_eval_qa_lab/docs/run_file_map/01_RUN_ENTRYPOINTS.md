# 01 Run Entrypoints

This file explains every execution path that can start the mini repo.

## Root Entrypoint

Path:

```text
main.py
```

Role:

- Sets console encoding to UTF-8.
- Detects `lab`, `labs`, `mini`, `mini-repo`, or `mini-repos` as mini-repo mode.
- Delegates mini-repo commands to `tools/mini_repo_registry.py`.
- Runs the older root orchestrator only when no lab entrypoint is used.

Main command:

```powershell
python main.py lab self_eval_qa_lab --mock "question"
```

Dataset command:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20
```

List registered mini repos:

```powershell
python main.py lab list
```

## Mini Repo Registry

Path:

```text
tools/mini_repo_registry.py
```

Role:

- Registers `self_eval_qa_lab`.
- Maps aliases: `self-eval`, `qa-lab`, `selfeval`.
- Maps command `run` to `experiments/self_eval_qa_lab/main.py`.
- Maps command `dataset` to `experiments/self_eval_qa_lab/dataset_runner.py`.
- Uses `runpy.run_path(...)` to execute the target script.
- Temporarily changes cwd to project root so relative imports and output paths
  are stable.

Supported registry syntaxes:

```powershell
python main.py lab self_eval_qa_lab --mock "question"
python main.py lab self-eval --mock "question"
python main.py lab self_eval_qa_lab run --mock "question"
python main.py lab self_eval_qa_lab:run --mock "question"
python main.py lab self_eval_qa_lab dataset --mock --limit 20
python main.py lab self_eval_qa_lab:dataset --mock --limit 20
```

## Direct Single-run Entrypoint

Path:

```text
experiments/self_eval_qa_lab/main.py
```

Role:

- Runs one question through the self-eval QA flow.
- Loads config, prompts, lenses, routing policy, and rubrics.
- Calls the selected LLM provider unless `--mock` or `--dry-run` is used.
- Writes run artifacts under `var/self_eval_qa_lab/<run_id>/` by default.

Direct command:

```powershell
python experiments/self_eval_qa_lab/main.py --mock "question"
```

Important flags:

```text
--question-file <path>          Read question from file.
--mock                          Deterministic run without LLM calls.
--dry-run                       Print selected flow without calling LLM.
--list                          List prompts, lenses, rubrics, sample questions.
--workflow auto|direct|assisted|deep|repo_debug
--baseline-mode auto|none|local
--chatgpt-mode auto|manual|mock|local|server
--chatgpt-answer-file <path>
--force-lenses
--propose-updates               Proposal-only; does not apply changes.
--llm-provider local|server
--model <model>
--server-url <url>
--server-api-key <key>
--server-model <model>
--llm-timeout <seconds>
--max-tokens <int>
--temperature <float>
--out-dir <path>
```

## Dataset Entrypoint

Path:

```text
experiments/self_eval_qa_lab/dataset_runner.py
```

Role:

- Loads Logikon/Open CoT-style cases through `dataset_loader.py`.
- Renders each case into a benchmark multiple-choice question.
- Runs `SelfEvalLab` for each case.
- Parses final `Answer: <letter>`.
- Writes per-case run artifacts and a dataset summary.
- Runs batch review only after `--review-every` completed cases.

Command:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

Important flags:

```text
--dataset logikon-bench
--subsets logiqa,lsat-ar,lsat-lr,lsat-rc,logiqa2
--limit <int>
--offset <int>
--shuffle
--seed <int>
--refresh-dataset
--dataset-cache-dir <path>
--review-every <int>
--target-accuracy <float>
--prompt-style standard|strict_final|deliberate
--mock
--baseline-mode auto|none|local
--llm-provider local|server
--workflow auto|direct|assisted|deep|repo_debug
--chatgpt-mode auto|manual|mock|local|server
--force-lenses
--propose-updates
--model <model>
--server-url <url>
--server-api-key <key>
--server-model <model>
--llm-timeout <seconds>
--max-tokens <int>
--temperature <float>
--out-dir <path>
--fail-fast
```

## LLM Provider Paths

Local provider:

```text
experiments/self_eval_qa_lab/main.py
  -> call_model(...)
  -> llm.py
  -> OpenAI-compatible local server, normally LM Studio
```

Server provider:

```text
experiments/self_eval_qa_lab/main.py
  -> call_model(...)
  -> llm.py with override base_url/api_key/model
  -> OpenAI-compatible remote/server URL
```

Mock provider:

```text
--mock
  -> deterministic fallback functions in experiments/self_eval_qa_lab/main.py
  -> no LLM network calls
```
