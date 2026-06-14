# Test And Evaluation

## Test Levels

### Unit Tests

Test pure functions:

- file role detection
- manifest parsing
- Python symbol extraction
- import graph extraction
- test-to-source mapping
- context pack size limits
- observer score calculation

### Fixture Tests

Use tiny repos:

```text
fixtures/
  tiny_python_repo/
    README.md
    pyproject.toml
    src/app.py
    src/planner.py
    tests/test_planner.py
```

Golden outputs:

```text
fixtures/expected/
  tiny_python_repo_file_map.json
  tiny_python_repo_symbol_map.json
  tiny_python_repo_graph.json
```

### Smoke Tests

Proposed commands:

```powershell
python business_prompt_lab/repo_understanding_lab/main.py --mock baseline
python business_prompt_lab/repo_understanding_lab/main.py --mock ask "How does Planner work?"
python -m unittest discover -s business_prompt_lab/repo_understanding_lab/tests
```

### Repo-Level Smoke

After v0.3:

```powershell
python business_prompt_lab/repo_understanding_lab/main.py baseline --repo .
python business_prompt_lab/repo_understanding_lab/main.py ask --repo . "How does main.py call the orchestrator?"
```

## Evaluation Rubric

### Context Precision

Did the pack include mostly relevant files/symbols?

### Context Recall

Did the pack miss important caller/callee/test/docs evidence?

### Evidence Quality

Are claims backed by file/symbol/test/doc/git evidence?

### No-Leap Score

Did the final answer distinguish observation, inference, and uncertainty?

### Test Adequacy

Did it identify the right tests or admit no tests exist?

### Runtime Safety

Did it avoid writes and dangerous commands during read-only analysis?

### Artifact Quality

Can an admin inspect the run later from JSON/Markdown files?

## Negative Test Cases

The fixture suite should include traps:

- stale docs disagree with code
- test name points to one module but imports another
- import exists but function is never called
- config flag disables a path
- wrapper function hides the real caller
- two symbols share the same short name

The observer should catch bad answers that ignore these traps.

## Required Admin Artifacts

Each run should save:

```text
transcript.jsonl
context_pack.json
observer_report.json
final_answer.md
summary.json
```

If LLM is used, save model-visible prompts and raw model outputs. Do not claim to
store private hidden reasoning; store only the text actually emitted by the model
or deterministic tool outputs.

