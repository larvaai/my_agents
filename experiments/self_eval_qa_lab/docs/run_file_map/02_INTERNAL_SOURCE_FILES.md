# 02 Internal Source Files

This file maps all source/config/data files inside:

```text
experiments/self_eval_qa_lab/
```

Generated `__pycache__/` files are ignored; they are Python runtime cache and
are not needed for understanding or running the lab.

## Top-level Files

| Path | Role |
|---|---|
| `README.md` | Quick start, design notes, output layout, provider options. |
| `__init__.py` | Makes the folder importable as `experiments.self_eval_qa_lab`. |
| `main.py` | Main single-question runner and core agent orchestration. |
| `dataset_runner.py` | Batch runner for Open CoT/Logikon-style dataset cases. |
| `dataset_loader.py` | Dataset manifest loader, downloader, case renderer, answer parser. |
| `config.yaml` | Lab version, default LLM provider, baseline modes, default lenses, update policy. |
| `routing_policy.yaml` | Deterministic workflow descriptions and keyword routing rules. |

## `main.py`

Core responsibilities:

- Defines runtime paths:
  - `LAB_DIR`
  - `ROOT_DIR`
  - `PROMPT_DIR`
  - `LENS_DIR`
  - `RUBRIC_DIR`
  - `QUESTION_DIR`
  - `DEFAULT_OUT_DIR`
- Defines dataclasses:
  - `LabConfig`
  - `LLMOptions`
  - `AnswerItem`
  - `WorkflowDecision`
  - `LabResult`
- Loads config, routing policy, prompts, lenses, and rubrics.
- Classifies question type and complexity.
- Routes workflow to `direct`, `assisted`, `deep`, or `repo_debug`.
- Calls text agents and JSON agents.
- Repairs empty text outputs and malformed JSON outputs.
- Enforces benchmark `Answer: <letter>` contract when needed.
- Compares simple answer, our answer, optional local baseline, and ChatGPT baseline.
- Runs blind evaluation, error analysis, flow observation, lessons, critical audit,
  evolution decision, and trace health.
- Writes full artifacts, ledgers, and admin trace.

Important class:

```text
SelfEvalLab
```

Important methods:

```text
run()
call_text_agent()
call_json_agent()
workflow_answer()
simple_answer()
baseline_answer()
chatgpt_baseline()
evaluate()
error_analysis()
observe_flow()
extract_lessons()
critical_audit()
evolution_decision()
write_outputs()
```

Important deterministic helpers:

```text
classify_question_deterministic()
route_workflow_deterministic()
deterministic_evaluation()
deterministic_error_report()
deterministic_flow_observation()
deterministic_lesson_report()
deterministic_critical_audit()
deterministic_evolution_decision()
analyze_trace_health()
```

## `dataset_runner.py`

Core responsibilities:

- Loads cases from `dataset_loader.py`.
- Runs `SelfEvalLab` once per case.
- Writes a dataset run folder.
- Stores per-case records as JSON and JSONL.
- Reviews only at the configured cadence, default 20 cases.
- Adjusts runtime policy conservatively after batch review.

Important functions:

```text
run_benchmark()
review_batch()
decide_batch_adjustment()
summarize_lab_result()
summarize_error()
build_summary_markdown()
should_review_case()
```

Important dataclass:

```text
RuntimePolicy
```

## `dataset_loader.py`

Core responsibilities:

- Reads `datasets/logikon_bench_manifest.json`.
- Downloads dataset JSONL files from Hugging Face raw URLs.
- Caches downloaded files under `var/self_eval_qa_lab/datasets/`.
- Converts JSONL rows to `DatasetCase`.
- Renders each case into a benchmark prompt.
- Parses model output back into a multiple-choice answer letter.

Important functions:

```text
load_manifest()
available_subsets()
resolve_subset_specs()
download_logikon_subset()
load_cases_from_jsonl()
load_logikon_cases()
render_case_question()
parse_multiple_choice_answer()
```

Important dataclass:

```text
DatasetCase
```

## Config Files

### `config.yaml`

Controls:

- Lab name and version.
- Default LLM provider: `local`.
- Server provider env var names.
- Baseline default mode: `auto`.
- ChatGPT baseline supported modes.
- Default lens list.
- Self-update policy: disabled and proposal-only by default.

Runtime effect:

- Loaded by `main.py::load_config()`.
- Used by `dataset_runner.py` before constructing each `SelfEvalLab`.

### `routing_policy.yaml`

Controls:

- Workflow descriptions.
- Whether a workflow needs baseline and evaluation.
- Max step hints.
- Keyword rules for definition, repo debug, deep, and assisted tasks.

Runtime effect:

- Loaded by `main.py::load_routing_policy()`.
- Used by `route_workflow_deterministic()`.

## Data Files

### `datasets/logikon_bench_manifest.json`

Defines:

- Dataset id: `logikon/logikon-bench`.
- Raw base URL on Hugging Face.
- Supported subsets:
  - `logiqa`
  - `lsat-ar`
  - `lsat-lr`
  - `lsat-rc`
  - `logiqa2`
- Split, path, license, and origin for each subset.

Runtime effect:

- `dataset_loader.py` uses it to resolve and download JSONL files.

### `questions/sample_multi_agent_design.md`

Sample question for mock or real single-run testing:

```powershell
python main.py lab self_eval_qa_lab --mock --question-file experiments/self_eval_qa_lab/questions/sample_multi_agent_design.md
```

## Docs Files

Existing docs:

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
docs/run_file_map/README.md
docs/run_file_map/01_RUN_ENTRYPOINTS.md
docs/run_file_map/02_INTERNAL_SOURCE_FILES.md
docs/run_file_map/03_AGENT_PROMPTS_AND_CONTRACTS.md
docs/run_file_map/04_EXTERNAL_PROJECT_FILES.md
docs/run_file_map/05_RUNTIME_DATA_OUTPUTS_AND_TESTS.md
```

Docs are not runtime dependencies, but they are part of the mini repo operating
manual.
