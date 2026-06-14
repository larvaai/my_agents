# Production Checklist

## Before Enabling For Real Users

- [ ] `python -m unittest discover -s tests` passes.
- [ ] `RUN_SELF_EVAL_REAL_LLM=1 python -m unittest tests.test_self_eval_qa_lab_real_llm` passes against the intended model.
- [ ] Real run creates `admin/full_trace.json`.
- [ ] `audits/trace_health.json` has `status: clean`.
- [ ] `audits/trace_health.json` has `severe_count: 0`.
- [ ] `trace_health.looping_detected` is false.
- [ ] No JSON fallback is present.
- [ ] No no-code agent emits code.
- [ ] Critical audit score is at least 6.
- [ ] Flow/Critical sanitizer notes, if present, are explainable and not hiding real loops.
- [ ] ChatGPT baseline is present through mock, local, server, or manual answer.
- [ ] Evolution decisions remain proposal-only.
- [ ] Dataset batch smoke passes: `python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20`.
- [ ] Dataset run has exactly one `batch_reviews/batch_0001_review.json` after 20 cases.
- [ ] Dataset `case_results.jsonl` has parse success for most cases before judging accuracy.

## Red Flags

- ChatGPT wins repeatedly on simple questions.
- Critic output repeats the draft instead of naming failure modes.
- Answer Synthesizer copies Critic instead of rewriting.
- JSON agents return prose or fenced JSON when strict JSON is requested.
- Flow Observer defends the selected flow despite clear over-routing.
- Evolution Decider proposes adding agents before fixing routing/prompt/schema.

## Fix Order

1. Routing policy.
2. Output schema and JSON repair.
3. Prompt wording.
4. Agent gating/removal.
5. Skill/tool proposal.
6. New agent.

## Release Gate

A run is acceptable for production only if the full trace can explain:

- why each agent ran
- what new signal it added
- why the final answer beat or lost to ChatGPT
- what should change next, if anything
