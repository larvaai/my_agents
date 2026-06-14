# 06 Detailed Prompt Flow

This doc records the real runtime flow, with special focus on how each
file/folder affects system prompt, user prompt, context, code, and flow.

Core idea:

```text
model behavior = model + system_prompt + user_prompt + context + params + repair/gates
```

The folder structure is not magic by itself. It exists to assemble prompts,
inject context, run agents in a controlled order, validate outputs, and record
what happened.

## 1. Prompt Layers

Every model call in this mini repo is built from these layers.

| Layer | Runtime source | What it changes |
|---|---|---|
| Base system prompt | `agents/*.md` | Agent role, rules, output contract, tone, allowed behavior. |
| Dynamic system prompt additions | `main.py` | Benchmark final-answer contract, repair instructions, deterministic system prompts. |
| Lens context | `lenses/*_lens.md` | Extra requirements inserted into `answer_generator.md` for deep flow. |
| Rubric context | `rubrics/*.yaml` | Scoring/flow criteria inserted into evaluator/observer prompts. |
| User prompt | CLI question, question file, dataset rendered question, or JSON payload | The actual task data for this call. |
| Runtime context | Prior agent outputs, classification, workflow trace, evaluation, trace health | Evidence passed to later agents through user prompt payloads. |
| LLM params | CLI/config/env | Provider, model, temperature, max tokens, timeout. |
| Repair/gates | `main.py` | Empty output repair, no-code repair, JSON repair, benchmark `Answer: <letter>` repair. |

## 2. Full Single-run Flow

Entrypoint:

```text
python main.py lab self_eval_qa_lab "question"
```

Actual call path:

```text
root main.py
  -> tools/mini_repo_registry.py
  -> experiments/self_eval_qa_lab/main.py
  -> SelfEvalLab.run()
```

`SelfEvalLab.run()` executes:

```text
1. write prompts/user_prompt.md
2. plan_run()
3. classify()
4. route_workflow()
5. simple_answer()
6. workflow_answer()
   - direct
   - assisted
   - deep
   - repo_debug
7. effective_baseline_mode()
8. baseline_answer()
9. chatgpt_baseline()
10. blind_shuffle()
11. evaluate()
12. reveal_evaluation()
13. deterministic_chatgpt_comparison()
14. error_analysis()
15. observe_flow()
16. extract_lessons()
17. pre-audit analyze_trace_health()
18. critical_audit()
19. evolution_decision()
20. final analyze_trace_health()
21. update_proposal()
22. write_outputs()
```

## 3. Step-by-step Prompt Construction

### 3.1 `plan_run()`

Model call:

```text
No LLM. Deterministic event.
```

System prompt recorded:

```text
Create a no-code auditable answer-flow run plan.
```

User prompt:

```text
Original question.
```

Output:

```text
Fixed JSON-like run plan listing classifier, router, answer path, ChatGPT
baseline, evaluator, analyzer, observer, lessons, critical auditor, and
evolution decider.
```

Prompt influence:

- No `agents/*.md` file is used here.
- This step affects later prompts indirectly because its event is saved into
  trace and later can be reviewed by `critical_auditor`.

### 3.2 `classify()`

For benchmark multiple-choice tasks:

```text
No LLM. Deterministic classification.
```

For normal questions:

System prompt source:

```text
agents/question_classifier.md
```

Dynamic injection:

```text
{{AVAILABLE_LENSES}} -> config.default_lenses
```

User prompt:

```text
Original question.
```

Expected JSON fields:

```text
task_type
complexity
needs_lens_flow
suggested_lenses
```

Prompt influence:

- `agents/question_classifier.md` directly controls how classification is done.
- `config.yaml` indirectly changes classifier system prompt by changing default
  lens names injected into `AVAILABLE_LENSES`.
- `routing_policy.yaml` is not part of this model prompt, but consumes the
  classification immediately after.
- For dataset MCQ tasks, the model classifier is bypassed so prompt drift cannot
  route benchmark cases into the wrong workflow.

### 3.3 `route_workflow()`

Model call:

```text
No LLM. Deterministic router.
```

System prompt recorded:

```text
Route to direct, assisted, deep, or repo_debug using routing_policy.yaml.
```

User prompt:

```json
{
  "question": "...",
  "classification": {...}
}
```

Flow source:

```text
routing_policy.yaml
```

Prompt influence:

- `routing_policy.yaml` does not become a model system prompt.
- It changes which future system prompt is used by selecting `direct`,
  `assisted`, `deep`, or `repo_debug`.
- `--workflow` can override it.
- `--force-lenses` maps to `deep` when no forced workflow is set.

### 3.4 `simple_answer()`

System prompt source:

```text
agents/simple_answer.md
```

Dynamic addition:

```text
benchmark_answer_contract(question)
```

If the question is a benchmark MCQ, `main.py` appends a contract requiring:

```text
Answer: <letter>
```

User prompt:

```text
Original question.
```

Prompt influence:

- `agents/simple_answer.md` directly controls the simple baseline style.
- `dataset_loader.py` can strongly influence this call because dataset questions
  already contain passage, options, and final-answer instructions.
- `main.py` adds the benchmark contract again as a system-level constraint.
- This answer becomes runtime context for assisted/repo flows and later
  evaluators.

### 3.5 `workflow_answer()`

Model call:

```text
No direct LLM call. Chooses one answer path.
```

Input:

```text
classification
workflow_decision
simple_answer
```

Prompt influence:

- This method decides which next system prompt is used.
- It can pass the `simple_answer` as user prompt context to later agents.

Branches:

```text
direct      -> no extra model call, final answer = simple_answer
assisted    -> critic review, optional answer_synthesizer rewrite
deep        -> lens_answer using answer_generator + selected lens docs
repo_debug  -> repo_context_router event, debug_reasoner model call
```

## 4. Workflow Branches

### 4.1 Direct Workflow

Model call:

```text
No LLM. Pass-through.
```

System prompt recorded:

```text
Use the simple answer as the final answer for direct workflow.
```

User prompt:

```text
simple_answer
```

Prompt influence:

- The only real model prompt used for final content was `simple_answer()`.
- Direct workflow is sensitive to `agents/simple_answer.md`,
  `dataset_loader.py`, and benchmark contract repair.

### 4.2 Assisted Workflow: Critic

System prompt is built inside `main.py`, not loaded from `agents/*.md`:

```text
You are the Critic Agent. Return public critique only. Do not write code.
Check for overconfident claims, missing caveats, missing validation/fallback
advice, and whether the draft answers the exact question.
```

Dynamic addition for benchmark MCQ:

```text
Also check whether the draft satisfies this contract: Answer: <letter>
```

User prompt:

```text
Question:
<original question>

Draft answer:
<simple_answer>
```

Prompt influence:

- To change this critic behavior today, edit `main.py`.
- A future cleanup could move this inline system prompt into
  `agents/critic.md`.
- The critic output controls whether `answer_synthesizer` runs or is skipped.

### 4.3 Assisted Workflow: Answer Synthesizer

Runs only if critic requests material rewrite or benchmark final line is
missing.

System prompt is built inside `main.py`:

```text
You are the Answer Synthesizer. Rewrite the draft using the critique. Do not
write code. Do not use markdown code fences, JSON blocks, or schema examples
unless the user explicitly asks for an example. Keep important caveats; prefer
accurate uncertainty over confident overclaiming.
```

Dynamic addition for benchmark MCQ:

```text
Answer: <letter>
```

User prompt:

```text
Question:
<original question>

Draft answer:
<simple_answer>

Critique:
<critic output>
```

Prompt influence:

- To make assisted answers closer to expected MCQ answer, strengthen this inline
  system prompt or move it into a file.
- The user prompt includes both original question and critic output, so bad
  critique can steer the final answer badly.
- `benchmark_answer_contract()` and final-answer repair are important gates for
  dataset correctness.

### 4.4 Deep Workflow: Lens Answer

System prompt source:

```text
agents/answer_generator.md
```

Dynamic injections:

```text
{{LENS_DOCS}}       -> selected_lens_docs(selected)
{{SELECTED_LENSES}} -> comma-separated selected lens names
benchmark contract -> appended for MCQ tasks
```

Lens file sources:

```text
lenses/architecture_lens.md
lenses/critic_lens.md
lenses/practical_lens.md
lenses/clarity_lens.md
lenses/no_leap_lens.md
```

User prompt:

```text
Original question.
```

Prompt influence:

- `agents/answer_generator.md` defines the base deep-answer behavior.
- `lenses/*.md` become literal system prompt context inside
  `answer_generator.md`.
- `config.yaml` controls default lens order and fallback lens selection.
- `question_classifier.md` can affect which lens names are selected.
- If no valid selected lenses exist, code falls back to the first 3 default
  lenses.
- This is the clearest example where a folder changes the system prompt:
  editing a lens changes the system prompt seen by the deep answer model.

### 4.5 Repo Debug Workflow

First step:

```text
repo_context_router
```

No LLM. Deterministic event.

System prompt recorded:

```text
Decide how repo/debug context should be handled without editing code.
```

Then model call:

```text
debug_reasoner
```

System prompt is built inside `main.py`:

```text
You are the Debug Reasoner. Explain repo/debug next checks. Do not write or
edit code. Do not use markdown code fences, JSON blocks, or schema examples
unless the user explicitly asks for an example.
```

Dynamic addition for benchmark MCQ:

```text
Answer: <letter>
```

User prompt:

```text
Question:
<original question>

Draft answer:
<simple_answer>
```

Prompt influence:

- To change repo/debug behavior today, edit `main.py`.
- `routing_policy.yaml` has large influence because it decides whether a
  question gets this prompt path.

## 5. Baselines And Evaluation Flow

### 5.1 `baseline_answer()`

Runs only when effective baseline mode is `local`.

System prompt source:

```text
agents/baseline_answer.md
```

User prompt:

```text
Original question.
```

Prompt influence:

- `routing_policy.yaml` can indirectly trigger this by setting
  `needs_baseline: true` for a workflow.
- `--baseline-mode local` forces it.
- `agents/baseline_answer.md` controls the baseline answer behavior.

### 5.2 `chatgpt_baseline()`

System prompt source:

```text
agents/chatgpt_baseline.md
```

User prompt:

```text
Original question.
```

Modes:

```text
manual -> writes prompts/chatgpt_prompt.md and waits for answer file
mock   -> deterministic heuristic answer
local  -> calls local model with chatgpt_baseline system prompt
server -> calls configured server with chatgpt_baseline system prompt
```

Prompt influence:

- `agents/chatgpt_baseline.md` controls the baseline persona and answer rules.
- `--chatgpt-mode` controls whether this prompt is executed, saved for manual
  use, mocked, or sent to server/local provider.

### 5.3 `evaluate()`

System prompt source:

```text
agents/blind_evaluator.md
```

Dynamic injections:

```text
{{RUBRIC}}        -> rubrics/answer_quality_rubric.yaml as JSON
{{ANSWER_LABELS}} -> answer_a, answer_b, answer_c, ...
```

User prompt:

```json
{
  "question": "...",
  "answers": {
    "answer_a": "...",
    "answer_b": "..."
  }
}
```

Prompt influence:

- `agents/blind_evaluator.md` controls judge behavior.
- `rubrics/answer_quality_rubric.yaml` becomes system prompt context.
- `blind_shuffle()` hides answer source names from the evaluator.
- If you want stricter scoring, usually edit the rubric and evaluator prompt
  together.

### 5.4 `error_analysis()`

System prompt source:

```text
agents/error_analyzer.md
```

User prompt:

```json
{
  "question": "...",
  "classification": {...},
  "answers": {
    "simple": "...",
    "ours": "...",
    "baseline": "...",
    "chatgpt": "..."
  },
  "evaluation": {...}
}
```

Prompt influence:

- `agents/error_analyzer.md` controls how failures are explained.
- It sees revealed source labels, unlike the blind evaluator.
- Its `recommended_update_proposal` can later be recorded if
  `--propose-updates` is used.

### 5.5 `observe_flow()`

System prompt source:

```text
agents/flow_observer.md
```

Dynamic injection:

```text
{{FLOW_RUBRIC}} -> rubrics/flow_quality_rubric.yaml as JSON
```

User prompt:

```json
{
  "question": "...",
  "classification": {...},
  "workflow_decision": {...},
  "workflow_trace": [...],
  "lens_trace": [...],
  "evaluation": {...},
  "error_report": {...},
  "cost_info": {
    "baseline_mode": "...",
    "num_lenses_used": 0,
    "num_workflow_steps": 3
  }
}
```

Prompt influence:

- `agents/flow_observer.md` controls process judging.
- `rubrics/flow_quality_rubric.yaml` becomes system prompt context.
- Actual trace data is user prompt context.
- `sanitize_flow_observation()` can reconcile contradictions after model output.

### 5.6 `extract_lessons()`

System prompt source:

```text
agents/lesson_extractor.md
```

User prompt:

```json
{
  "workflow_decision": {...},
  "flow_observation": {...},
  "error_report": {...}
}
```

Prompt influence:

- `agents/lesson_extractor.md` controls what becomes a reusable lesson.
- It does not see full raw trace; it sees distilled workflow/error context.

### 5.7 `critical_audit()`

System prompt source:

```text
agents/critical_auditor.md
```

User prompt:

```json
{
  "workflow_decision": {...},
  "workflow_trace": [...],
  "flow_observation": {...},
  "chatgpt_comparison": {...},
  "trace_health": {...},
  "agent_call_events": [...]
}
```

Prompt influence:

- `agents/critical_auditor.md` controls how hard the system criticizes itself.
- It receives full recorded event metadata as user prompt context.
- `trace_health` is computed before audit and strongly influences what the
  auditor can notice.
- `sanitize_critical_audit()` reconciles hallucinated findings against observed
  trace facts.

### 5.8 `evolution_decision()`

System prompt source:

```text
agents/evolution_decider.md
```

User prompt:

```json
{
  "critical_audit": {...},
  "flow_observation": {...},
  "lesson_report": {...},
  "chatgpt_comparison": {...}
}
```

Prompt influence:

- `agents/evolution_decider.md` controls add/remove/modify proposals for agents,
  flows, skills, tools, and outputs.
- In v0.3 this remains proposal-only. It does not apply file edits.
- Future governed self-evolution is described in
  `docs/evolution_proposals/EP-0002_GOVERNED_SELF_EVOLUTION.md`.

## 6. Dataset Flow

Entrypoint:

```text
python main.py lab self_eval_qa_lab dataset --limit 20 --subsets logiqa
```

Actual call path:

```text
root main.py
  -> tools/mini_repo_registry.py
  -> experiments/self_eval_qa_lab/dataset_runner.py
  -> dataset_loader.load_logikon_cases()
  -> dataset_loader.render_case_question()
  -> SelfEvalLab.run() once per case
```

Dataset question construction:

```text
Dataset metadata
Passage
Question
Options
Instructions
```

Prompt styles:

```text
standard
strict_final
deliberate
```

How dataset files affect prompts:

- `datasets/logikon_bench_manifest.json` chooses which raw cases are loaded.
- `dataset_loader.py` renders each case into the user prompt.
- `--prompt-style` changes the instruction block inside the user prompt.
- `main.py` detects benchmark MCQ prompts and appends final-answer contracts to
  relevant system prompts.
- `dataset_runner.py` can change runtime policy after each review batch, but
  only after `--review-every` completed cases.

## 7. File/folder Impact Matrix

| File/folder | System prompt impact | User prompt/context impact | Flow/code impact |
|---|---|---|---|
| `agents/*.md` | Direct. These are base system prompts for named agents. | None by itself. | Loaded by `load_prompt()`. |
| `agents/simple_answer.md` | Direct for `simple_answer()`. | Simple answer becomes context for later agents. | Always used before selected workflow. |
| `agents/answer_generator.md` | Direct for deep/lens answer. Receives lens docs via placeholders. | Original question only. | Used only in deep workflow. |
| `agents/question_classifier.md` | Direct for normal classification. Receives available lenses. | Original question. | Output affects routing and selected lenses. |
| `agents/blind_evaluator.md` | Direct evaluator system prompt. Receives answer rubric. | Blind answer pack. | Output decides winner/scores. |
| `agents/error_analyzer.md` | Direct error analyzer system prompt. | Revealed scores and all answers. | Can create update proposal. |
| `agents/flow_observer.md` | Direct flow observer system prompt. Receives flow rubric. | Workflow trace, lens trace, cost info. | Output feeds lessons and audit. |
| `agents/lesson_extractor.md` | Direct lesson extractor system prompt. | Workflow/error summaries. | Output feeds evolution decision. |
| `agents/critical_auditor.md` | Direct critical audit system prompt. | Trace health and agent events. | Output feeds evolution decision. |
| `agents/evolution_decider.md` | Direct evolution system prompt. | Audit, flow, lessons, ChatGPT comparison. | Proposal-only decision. |
| `agents/baseline_answer.md` | Direct when local baseline runs. | Original question. | Adds baseline answer to blind evaluation. |
| `agents/chatgpt_baseline.md` | Direct for ChatGPT-style baseline modes. | Original question. | Adds or saves ChatGPT baseline. |
| `lenses/*.md` | Directly inserted into deep answer system prompt through `{{LENS_DOCS}}`. | None by itself. | Changes deep answer behavior without editing Python. |
| `rubrics/answer_quality_rubric.yaml` | Inserted into blind evaluator system prompt. | None by itself. | Changes scoring criteria. |
| `rubrics/flow_quality_rubric.yaml` | Inserted into flow observer system prompt. | None by itself. | Changes process scoring. |
| `questions/*.md` | No direct system prompt impact. | Supplies user prompt when `--question-file` is used. | Useful for repeatable tests. |
| `datasets/logikon_bench_manifest.json` | No direct system prompt impact. | Chooses raw dataset cases that become user prompts. | Controls available benchmark subsets. |
| `dataset_loader.py` | Indirect. Its benchmark prompt shape triggers system contract additions in `main.py`. | Direct. Renders dataset user prompt. | Parses final answer letters. |
| `dataset_runner.py` | Indirect. Batch policy can force workflow or prompt style. | Runs rendered case prompt per case. | Controls review cadence and batch adjustment. |
| `config.yaml` | Indirect. Default lenses are injected into classifier and deep prompts. | None directly. | Sets provider/baseline/default lens/update policy. |
| `routing_policy.yaml` | No direct model system prompt, except recorded deterministic router prompt. | Router sees classification and question. | Chooses future prompt path. |
| `main.py` | Direct and indirect. Builds inline system prompts, appends benchmark contracts, creates repair prompts, injects lenses/rubrics. | Builds JSON payloads for later agents. | Core orchestration, parsing, validation, trace. |
| `llm.py` | No prompt wording impact. | Sends messages to model. | Provider/model/timeout/max-token behavior. |
| `tools/mini_repo_registry.py` | No prompt wording impact. | None. | Dispatches root CLI to mini repo scripts. |
| `.env` | No prompt wording impact. | None. | Selects model/server defaults used by `llm.py`. |
| `var/self_eval_qa_lab/*` | No direct prompt impact during current run. | Stores traces and ledgers for later analysis. | Evidence source for future evolution work. |

## 8. Where To Edit For Specific Behavior

### Make answers closer to benchmark answer key

Edit first:

```text
dataset_loader.py              -> clearer user prompt and final-answer instruction
agents/simple_answer.md        -> stronger direct answer behavior
main.py benchmark contract     -> stricter system-level `Answer: <letter>` rule
agents/answer_generator.md     -> better deep answer behavior if using deep flow
```

Then validate with:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

For real model validation:

```powershell
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 20 --subsets logiqa --review-every 20 --chatgpt-mode mock --baseline-mode none --prompt-style strict_final
```

### Make critic/rewrite smarter

Edit:

```text
main.py assisted_answer() inline critic prompt
main.py assisted_answer() inline answer_synthesizer prompt
```

Possible future cleanup:

```text
agents/critic.md
agents/answer_synthesizer.md
```

### Make deep flow more useful

Edit:

```text
agents/answer_generator.md
lenses/*.md
config.yaml default lenses
agents/question_classifier.md suggested lens behavior
```

### Make evaluator stricter

Edit:

```text
agents/blind_evaluator.md
rubrics/answer_quality_rubric.yaml
```

### Make process audit stricter

Edit:

```text
agents/flow_observer.md
rubrics/flow_quality_rubric.yaml
agents/critical_auditor.md
agents/evolution_decider.md
```

### Change which prompt path runs

Edit:

```text
routing_policy.yaml
agents/question_classifier.md
main.py route_workflow_deterministic()
```

## 9. Important Distinction

Some files change the system prompt directly:

```text
agents/*.md
lenses/*.md
rubrics/*.yaml
main.py inline system prompts
main.py repair prompts
```

Some files change user prompt/context:

```text
questions/*.md
dataset_loader.py
dataset cases loaded from manifest/cache
prior agent outputs assembled by main.py
trace_health and workflow_trace payloads
```

Some files change flow, which indirectly changes which system prompt is used:

```text
routing_policy.yaml
config.yaml
dataset_runner.py runtime policy
main.py workflow methods
```

That means improving answer quality is usually not only "edit one system
prompt". The shortest path is often:

```text
1. improve user prompt contract
2. improve relevant agent system prompt
3. ensure routing picks that agent
4. add repair/parse gate if format matters
5. run batch eval before accepting the change
```
