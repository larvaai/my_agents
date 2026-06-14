# 00 New Contributor Guide

This guide is for contributors who are new to this mini repo, new to
multi-agent prompting, or not yet comfortable reading the Python flow.

Read this before the deeper file map.

## One-sentence Mental Model

The mini repo is a machine that builds prompts, sends them to agents, checks the
outputs, saves every step, and then asks critic/evolution agents what should be
improved next.

The most important idea:

```text
agents/*.md define how an agent should behave
main.py decides when that agent runs and what context it receives
dataset_loader.py or the user's question provides the actual task
rubrics/ and lenses/ add extra instructions into some system prompts
var/ stores what really happened
```

## System Prompt, User Prompt, Context, Flow

When the model is called, it usually receives two main pieces:

```text
system prompt = rules for the agent
user prompt   = the concrete task/data for this call
```

In this repo:

| Term | Easy meaning | Typical file |
|---|---|---|
| System prompt | "You are this agent. Follow these rules." | `agents/*.md` |
| User prompt | "Here is the actual question/case/data." | CLI question, `questions/*.md`, `dataset_loader.py`, JSON payloads in `main.py` |
| Context | Extra information added to help the model decide. | `lenses/*.md`, `rubrics/*.yaml`, prior agent outputs |
| Flow | Which agent runs first, second, third. | `main.py`, `routing_policy.yaml` |
| Repair | A second chance when output is empty/wrong format. | `main.py` |
| Trace | The saved evidence of what happened. | `var/self_eval_qa_lab/...` |

## Where To Start

If you only have 10 minutes, read these in order:

```text
1. README.md
2. docs/run_file_map/00_NEW_CONTRIBUTOR_GUIDE.md
3. docs/run_file_map/06_DETAILED_PROMPT_FLOW.md
4. experiments/self_eval_qa_lab/main.py only after you know what you are looking for
```

If you want to change answer quality, start here:

```text
agents/simple_answer.md
agents/answer_generator.md
dataset_loader.py
lenses/*.md
rubrics/*.yaml
routing_policy.yaml
```

Do not start by editing every file. Pick one behavior, one file, one test run.

## The Normal Run In Plain Language

When you run:

```powershell
python main.py lab self_eval_qa_lab --mock "question"
```

the repo does this:

```text
1. Save the original question.
2. Make a run plan.
3. Classify the question.
4. Pick a workflow.
5. Always create a simple answer.
6. Depending on workflow:
   - direct: use simple answer
   - assisted: critic checks simple answer, synthesizer may rewrite
   - deep: answer_generator uses selected lenses
   - repo_debug: debug_reasoner gives no-code repo/debug advice
7. Optionally create local baseline.
8. Create or save ChatGPT-style baseline.
9. Shuffle answers so evaluator does not know source names.
10. Blind evaluator scores answers.
11. Error analyzer explains win/loss.
12. Flow observer checks whether the agent process was worth it.
13. Lesson extractor records reusable lessons.
14. Critical auditor looks at the whole trace.
15. Evolution decider proposes future changes.
16. Everything is saved under var/self_eval_qa_lab/<run_id>/.
```

## The Same Run As Prompt Movement

The question moves through the system like this:

```text
Original question
  -> user prompt for question_classifier
  -> routing decision
  -> user prompt for simple_answer
  -> maybe context for critic / answer_synthesizer / lens_answer
  -> answer candidates
  -> JSON payload for blind_evaluator
  -> JSON payload for error_analyzer
  -> JSON payload for flow_observer
  -> JSON payload for critical_auditor
  -> JSON payload for evolution_decider
```

Notice: later agents usually do not receive only the original question. They
receive JSON payloads built by `main.py` that include earlier outputs.

## File Groups For Beginners

### `agents/`

This is the first place to look when an agent says the wrong kind of thing.

Example:

```text
Problem: simple answer is too long.
Likely file: agents/simple_answer.md
```

```text
Problem: evaluator scores too generously.
Likely file: agents/blind_evaluator.md and rubrics/answer_quality_rubric.yaml
```

```text
Problem: critical auditor misses obvious repeated-agent behavior.
Likely file: agents/critical_auditor.md
```

### `lenses/`

These are extra instructions inserted into the deep answer system prompt.

Example:

```text
Problem: deep answer lacks practical next steps.
Likely file: lenses/practical_lens.md
```

```text
Problem: deep answer jumps to conclusions.
Likely file: lenses/no_leap_lens.md
```

Editing a lens changes the system prompt for deep workflow, because
`answer_generator.md` receives the rendered lens docs.

### `rubrics/`

These are judge criteria.

Example:

```text
Problem: answers with weak evidence still score high.
Likely file: rubrics/answer_quality_rubric.yaml
Also check: agents/blind_evaluator.md
```

```text
Problem: flow observer does not punish unnecessary agents.
Likely file: rubrics/flow_quality_rubric.yaml
Also check: agents/flow_observer.md
```

### `dataset_loader.py`

This file turns dataset rows into user prompts.

Example:

```text
Problem: model does not end with Answer: A/B/C/D.
Likely file: dataset_loader.py prompt_style text
Also check: main.py benchmark_answer_contract()
```

### `routing_policy.yaml`

This file helps decide which workflow runs.

Example:

```text
Problem: simple benchmark MCQ is routed to deep flow.
Likely file: routing_policy.yaml or main.py benchmark classification/routing logic
```

### `main.py`

This is the engine.

Edit it only when the behavior is truly about orchestration, not just wording.

Examples:

```text
Problem: wrong agent order.
Likely file: main.py
```

```text
Problem: need a new repair pass.
Likely file: main.py
```

```text
Problem: need to pass extra context to critical auditor.
Likely file: main.py
```

## Common Change Recipes

### Recipe 1: Make MCQ Benchmark Answers Easier To Parse

Goal:

```text
The model should end with exactly: Answer: <letter>
```

Check/edit in this order:

```text
1. dataset_loader.py
   - Does the rendered question clearly demand the final answer line?

2. main.py benchmark_answer_contract()
   - Does the system prompt reinforce the same contract?

3. main.py repair_benchmark_answer_contract()
   - Does repair force one valid letter?

4. tests/test_self_eval_qa_lab_dataset.py
   - Does parser test cover this format?
```

Verify:

```powershell
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
```

### Recipe 2: Make Deep Flow More Useful

Goal:

```text
Deep flow should add useful structure, not just repeat simple_answer.
```

Check/edit:

```text
1. agents/answer_generator.md
2. lenses/architecture_lens.md
3. lenses/critic_lens.md
4. lenses/practical_lens.md
5. lenses/clarity_lens.md
6. lenses/no_leap_lens.md
7. config.yaml default lens order
```

Verify:

```powershell
python main.py lab self_eval_qa_lab --mock --workflow deep --question-file experiments/self_eval_qa_lab/questions/sample_multi_agent_design.md
```

### Recipe 3: Make Assisted Flow Less Wasteful

Goal:

```text
Only rewrite when critique finds a material issue.
```

Check/edit:

```text
1. main.py assisted_answer() critic prompt
2. main.py critique_requests_material_rewrite()
3. main.py assisted_answer() rewrite skip logic
4. tests/test_self_eval_qa_lab.py
```

Reason:

The critic and synthesizer prompts are currently inline in `main.py`, not in
`agents/*.md`.

### Recipe 4: Make Self-audit More Useful

Goal:

```text
Critical auditor should notice loops, weak handoffs, wasted agents, and missing context.
```

Check/edit:

```text
1. agents/critical_auditor.md
2. main.py critical_audit() payload
3. main.py analyze_trace_health()
4. agents/evolution_decider.md
5. docs/evolution_proposals/
```

Verify by reading:

```text
var/self_eval_qa_lab/<run_id>/audits/critical_audit.json
var/self_eval_qa_lab/<run_id>/audits/evolution_decision.json
var/self_eval_qa_lab/<run_id>/admin/full_trace.json
```

## How To Read A Run Output

After a run, open:

```text
var/self_eval_qa_lab/<run_id>/summary.md
```

Then inspect:

```text
answers/final.md
audits/trace_health.json
audits/critical_audit.json
audits/evolution_decision.json
admin/full_trace.json
```

If output was bad, ask in this order:

```text
1. Did the user prompt contain enough information?
2. Did the correct workflow run?
3. Did the relevant system prompt say the right rule?
4. Did context from earlier agents confuse the later agent?
5. Did parser/repair hide the original model failure?
6. Did trace_health catch the issue?
7. Did critical_auditor notice it?
```

## Simple Debug Map

| Symptom | Start here |
|---|---|
| Wrong final answer format | `dataset_loader.py`, `main.py benchmark_answer_contract()` |
| Agent is verbose | Relevant `agents/*.md` or inline prompt in `main.py` |
| Deep flow repeats simple answer | `agents/answer_generator.md`, `lenses/*.md`, `trace_health` |
| Evaluator is unfair | `agents/blind_evaluator.md`, `rubrics/answer_quality_rubric.yaml` |
| Wrong workflow selected | `routing_policy.yaml`, `question_classifier.md`, `route_workflow_deterministic()` |
| JSON parse fallback | Relevant structured agent prompt, `call_json_agent()` |
| Empty output | `call_text_agent()`, model max tokens, provider config |
| ChatGPT comparison missing | `--chatgpt-mode`, `agents/chatgpt_baseline.md`, answer file |
| Dataset cases not loading | `datasets/logikon_bench_manifest.json`, cache path, network |
| Real LLM not responding | `.env`, `llm.py`, LM Studio/server URL |

## Contribution Checklist

Before changing anything:

```text
1. Name the symptom.
2. Find the run artifact that proves the symptom.
3. Decide whether this is system prompt, user prompt, context, flow, parser, or provider.
4. Change the smallest file that can fix it.
5. Run a mock check.
6. If prompt/model behavior matters, run a small real LLM smoke.
7. Record what improved and what got worse.
```

Fast check:

```powershell
python -m unittest tests.test_self_eval_qa_lab tests.test_self_eval_qa_lab_dataset tests.test_mini_repo_registry
```

Full check:

```powershell
python -m unittest discover -s tests
```

## What Not To Do First

Avoid these as first moves:

```text
1. Do not rewrite main.py just because an answer is weak.
2. Do not add a new agent until a trace proves an existing agent cannot do it.
3. Do not change routing after only one lucky or unlucky case.
4. Do not optimize for one dataset case without checking a batch.
5. Do not disable trace, audit, repair, or baseline comparison to make output look cleaner.
```

Most first fixes should be prompt or context fixes, not architecture rewrites.

## Tiny Example

Suppose the dataset output says:

```text
The answer is probably C because the passage rules out the other choices.
```

But parser fails because the final line is missing.

This is probably not a deep architecture problem. It is likely:

```text
user prompt contract too weak
or system prompt contract too weak
or repair did not trigger
```

Check:

```text
dataset_loader.py render_case_question()
main.py benchmark_answer_contract()
main.py repair_benchmark_answer_contract()
traces/agent_calls.jsonl
admin/full_trace.json
```

The desired model-visible instruction should be explicit:

```text
The last non-empty line must be exactly: Answer: <letter>
```

Then verify across a batch, not one case.
