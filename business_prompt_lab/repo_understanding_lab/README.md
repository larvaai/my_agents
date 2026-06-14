# Repo Understanding Lab

Docs-first mini repo for designing an agent system that reads and understands a
code project before it answers questions or proposes changes.

This lab is registered in `python main.py lab ...` and now has a stdlib-first
runtime: mock fixture runs, real repo scanning, Python AST symbol extraction,
simple graph/test maps, context packs, and a deterministic No-Leap Guardian.

## Purpose

The lab tests one core idea:

```text
Good code-agent behavior is not "grep, guess, patch".
Good code-agent behavior is "map, index, retrieve evidence, reason with graph,
verify with tests, then answer or patch".
```

The target system should build these layers:

- repo map
- manifest/runtime map
- documentation map
- symbol map
- dependency and call graph
- behavior/test map
- ledger/memory map
- no-leap observer

## Current Status

Status: `implemented-v0.3`

Created files:

```text
business_prompt_lab/repo_understanding_lab/
  README.md
  docs/
    00_START_HERE.md
    01_DESIGN_PROPOSAL.md
    02_ARCHITECTURE.md
    03_DATA_CONTRACTS.md
    04_AGENT_FLOW.md
    05_MVP_ROADMAP.md
    06_TEST_AND_EVALUATION.md
    07_IMPLEMENTATION_PLAN.md
    08_NO_LEAP_GUARDIAN.md
    09_OPEN_QUESTIONS.md
  fixtures/
    tiny_python_repo/
  repo_understanding/
    scanner.py
    manifests.py
    docs_reader.py
    symbols.py
    graphs.py
    runtime.py
    context_pack.py
    observer.py
  main.py
```

Runtime output stays under `var/repo_understanding_lab/<run_id>/`.

## Run

Mock fixture:

```powershell
python business_prompt_lab/repo_understanding_lab/main.py --mock baseline
python business_prompt_lab/repo_understanding_lab/main.py --mock ask "How does PlannerAgent work?"
python main.py lab repo-understanding --mock ask "How does PlannerAgent work?"
```

Real repo:

```powershell
python business_prompt_lab/repo_understanding_lab/main.py baseline --repo .
python business_prompt_lab/repo_understanding_lab/main.py ask --repo . "How does main.py call orchestrator?"
python business_prompt_lab/repo_understanding_lab/main.py impact --repo . orchestrator.run_orchestrator
```

Artifacts:

```text
maps/file_map.json
maps/repo_profile.json
maps/docs_map.json
maps/symbol_map.json
maps/dependency_graph.json
maps/test_map.json
maps/runtime_map.json
context/context_pack.json
reports/observer_report.json
reports/understanding_report.json
final_answer.md
summary.json
summary.md
transcript.jsonl
```

## Read First

Start here:

```text
docs/00_START_HERE.md
```

Then read:

```text
docs/01_DESIGN_PROPOSAL.md
docs/02_ARCHITECTURE.md
docs/03_DATA_CONTRACTS.md
docs/04_AGENT_FLOW.md
```

## Proposed Phases

1. `v0.1-docs`
   Design proposal only. Done.

2. `v0.2-mock`
   Deterministic mock runner that scans a tiny fixture repo and emits fake but
   structured maps. Done.

3. `v0.3-index`
   Real filesystem scan, manifest reader, Python AST symbol extractor, import
   graph, and test map. Done for Python stdlib MVP.

4. `v0.4-context-pack`
   Query flow that turns a user question into an evidence-backed context pack.
   Done: v0.4 adds repo-flow synthesis, external workspace test mapping, and
   `reports/understanding_report.json`.

5. `v0.5-observer`
   No-Leap Guardian checks whether the agent jumped to conclusions, skipped
   tests, or used weak evidence.

## Design Constraint

This lab must stay read-first. It may later include a patch proposal flow, but
the early versions must focus on understanding, evidence, and diagnostics before
editing code.
