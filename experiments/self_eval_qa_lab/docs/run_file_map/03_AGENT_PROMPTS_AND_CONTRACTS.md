# 03 Agent Prompts And Contracts

This file maps the prompt files, lens files, and rubric files used by the lab.

## Agent Prompt Folder

Path:

```text
experiments/self_eval_qa_lab/agents/
```

Each `.md` file is loaded by `main.py::load_prompt(name)`.

| Prompt | Type | Used for |
|---|---|---|
| `simple_answer.md` | text | Always produces the simple baseline answer. |
| `answer_generator.md` | text | Produces our workflow answer in assisted/deep/repo flows. |
| `baseline_answer.md` | text | Optional local baseline when `--baseline-mode local` or auto baseline is active. |
| `chatgpt_baseline.md` | text | Prompt artifact or local/server ChatGPT-style baseline. |
| `question_classifier.md` | structured JSON | Classifies task type, complexity, and suggested lenses. |
| `blind_evaluator.md` | structured JSON | Scores anonymized answers and selects a winner. |
| `error_analyzer.md` | structured JSON | Explains where our answer won/lost and proposes safe updates. |
| `flow_observer.md` | structured JSON | Reviews whether the selected flow was useful or wasteful. |
| `lesson_extractor.md` | structured JSON | Extracts reusable routing/process lessons. |
| `critical_auditor.md` | structured JSON | Audits the whole agent process for logic, waste, loops, missing agents. |
| `evolution_decider.md` | structured JSON | Proposes add/remove/modify decisions for agents, flows, outputs, skills, or tools. |

## Text Agent Contract

Text agents return normal Markdown/plain text. They are used when the answer is
human-facing.

Runtime protections:

- If output is empty, `call_text_agent()` records the failed call and runs an
  empty-output repair pass.
- If a no-code prompt receives code, `call_text_agent()` can record and repair
  that violation.
- For benchmark MCQ prompts, `call_text_agent()` enforces the last non-empty
  line format:

```text
Answer: <letter>
```

## Structured Agent Contract

Structured agents currently return JSON that must pass schema validation.

Structured agents:

```text
question_classifier
blind_evaluator
error_analyzer
flow_observer
lesson_extractor
critical_auditor
evolution_decider
```

Runtime protections:

- `parse_json_object()` accepts raw JSON or a JSON object inside surrounding
  text/fenced output.
- `validate_json_agent_output()` checks required fields per agent.
- `call_json_agent()` repairs malformed output once.
- If repair fails, the runner records a deterministic fallback event.
- Trace health marks JSON fallback events so we can inspect weak agents later.

Planned proposal:

- `docs/evolution_proposals/EP-0001_XML_FIRST_STRUCTURED_OUTPUT.md` proposes
  XML-first structured output, then internal conversion to JSON.

## Lens Folder

Path:

```text
experiments/self_eval_qa_lab/lenses/
```

Each lens is loaded by `main.py::load_lens(name)` from `*_lens.md`.

| Lens | Role |
|---|---|
| `architecture_lens.md` | Checks structure, components, interfaces, ownership. |
| `critic_lens.md` | Challenges weak assumptions, missing risks, shallow claims. |
| `practical_lens.md` | Forces usable next steps and operational framing. |
| `clarity_lens.md` | Improves readability and answer organization. |
| `no_leap_lens.md` | Prevents unsupported jumps and missing evidence. |

Default lens order is defined in:

```text
experiments/self_eval_qa_lab/config.yaml
```

Default list:

```text
architecture
critic
practical
clarity
no_leap
```

## Rubric Folder

Path:

```text
experiments/self_eval_qa_lab/rubrics/
```

| Rubric | Used by |
|---|---|
| `answer_quality_rubric.yaml` | Blind answer evaluation and deterministic scoring helpers. |
| `flow_quality_rubric.yaml` | Flow observer and trace/process quality review. |

## Public Reasoning Boundary

The lab can store:

- Full prompts.
- Full raw emitted outputs.
- Public rationales.
- Public reasoning summaries.
- Handoffs.
- Trace health findings.

The lab must not claim to expose hidden internal chain-of-thought. When a prompt
asks for reasoning, it should ask for visible/public rationale or concise audit
summary.
