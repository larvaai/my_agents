# Self Eval QA Lab

Mini repo nay test cau hoi quan trong:

```text
Lens/multi-step answer flow co that su tot hon simple answer khong?
```

MVP v0.1 khong lam full self-improvement. No chi do:

```text
Question
  -> Question Classifier
  -> Simple Answer
  -> Lens-Based Answer
  -> Optional Baseline Answer
  -> Blind Evaluator
  -> Error Analyzer
  -> Flow Observer
  -> Ledger
```

## Chay nhanh

List assets:

```powershell
python main.py lab self_eval_qa_lab --list
```

Dry run, khong goi LLM:

```powershell
python main.py lab self_eval_qa_lab --dry-run "Co nen dung multi-agent cho cau hoi nay khong?"
```

Mock run, khong goi LLM nhung tao day du output:

```powershell
python main.py lab self_eval_qa_lab --mock --question-file experiments/self_eval_qa_lab/questions/sample_multi_agent_design.md
```

Real run qua `llm.py`, mac dinh khong goi baseline rieng:

```powershell
python main.py lab self_eval_qa_lab "Critical thinking giup toi y tuong self-eval QA lab"
```

Real run co local baseline:

```powershell
python main.py lab self_eval_qa_lab --baseline-mode local "Critical thinking giup toi y tuong self-eval QA lab"
```

Chay truc tiep:

```powershell
python experiments/self_eval_qa_lab/main.py --mock "question"
```

## Output

Moi run ghi vao:

```text
var/self_eval_qa_lab/<run_id>/
  run.json
  summary.md
  answers/simple.md
  answers/ours.md
  answers/baseline.md
```

Ledger append-only:

```text
var/self_eval_qa_lab/ledger/runs.jsonl
var/self_eval_qa_lab/ledger/evaluations.jsonl
var/self_eval_qa_lab/ledger/flow_observations.jsonl
var/self_eval_qa_lab/ledger/update_proposals.jsonl
```

## Design Notes

- Simple answer is always present as a baseline.
- Lens-based answer is only used when classifier says the question is complex enough, unless `--force-lenses` is set.
- Evaluator is blind: it sees `answer_a`, `answer_b`, `answer_c`, not source names.
- Flow Observer evaluates process quality, not answer quality.
- Update proposals are disabled by default and proposal-only when enabled.
- This lab should prove value before any lens becomes a specialist agent.

## Files

```text
agents/      Prompt roles for classifier, answerer, evaluator, analyzer, observer
lenses/      Lens instructions used by lens-based answer generator
rubrics/     Answer and flow quality rubrics
questions/   Sample questions
main.py      CLI runner
config.yaml  Default modes and lens list
```
