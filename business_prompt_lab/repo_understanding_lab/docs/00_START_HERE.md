# Start Here

This mini repo designs a code-understanding agent lab.

The goal is to make an agent understand a repo like an engineer:

1. See the project shape.
2. Read manifests and docs.
3. Build file, symbol, dependency, runtime, test, and memory maps.
4. Answer questions from evidence.
5. Refuse to jump from weak evidence to confident conclusions.

## Problem

Many code agents fail because they do this:

```text
user request
  -> grep one keyword
  -> open one file
  -> guess root cause
  -> patch
```

This creates predictable mistakes:

- changing the wrong module
- missing callers and tests
- ignoring config and runtime setup
- over-trusting stale docs
- treating import graph as behavior graph
- forgetting previous failures

## Lab Hypothesis

An agent gets meaningfully better if the repo is represented as a small
knowledge system:

```text
Code understanding
  = filesystem map
  + manifest/runtime map
  + documentation grounding
  + symbol index
  + dependency graph
  + call graph
  + test map
  + git/history map
  + ledger memory
  + no-leap observer
```

## What This Lab Will Produce

The proposed runtime will produce artifacts like:

```text
var/repo_understanding_lab/<run_id>/
  repo_profile.json
  file_map.json
  symbol_map.json
  dependency_graph.json
  call_graph.json
  test_map.json
  runtime_map.json
  context_pack.json
  observer_report.json
  final_answer.md
  transcript.jsonl
```

## What To Read Next

Read in this order:

1. `01_DESIGN_PROPOSAL.md`
2. `02_ARCHITECTURE.md`
3. `03_DATA_CONTRACTS.md`
4. `04_AGENT_FLOW.md`
5. `05_MVP_ROADMAP.md`

