# MVP Roadmap

## v0.1 - Docs Proposal

Status: done.

Deliverables:

- mini repo folder
- design proposal docs
- data contracts
- agent flow
- roadmap
- test strategy

No runtime.

Exit criteria:

- design is specific enough to implement without re-asking basic architecture
  questions
- scope is intentionally small

## v0.2 - Mock Runner

Status: done.

Deliverables:

- `main.py` with `argparse`
- `--mock`
- tiny fixture repo
- deterministic maps
- transcript output
- observer mock report

Commands:

```powershell
python business_prompt_lab/repo_understanding_lab/main.py --mock baseline
python business_prompt_lab/repo_understanding_lab/main.py --mock ask "Where is the entrypoint?"
```

Exit criteria:

- output artifacts match contracts
- tests do not require LLM
- can be registered in `tools/mini_repo_registry.py`

## v0.3 - Real Scanner And Python Symbol Index

Status: done for Python stdlib MVP.

Deliverables:

- filesystem scanner
- manifest reader
- docs reader
- Python `ast` symbol extractor
- import graph
- simple test map
- runtime command inference

Exit criteria:

- can scan this repo without crashing
- can produce `repo_profile.json`, `file_map.json`, `symbol_map.json`
- can answer simple file/symbol questions from stored maps

## v0.4 - Context Pack And Evidence Answer

Deliverables:

- query classifier
- entity extractor
- symbol search
- graph slice builder
- context packer
- answer writer using local deterministic templates first
- optional LLM answer through `llm.py`

Exit criteria:

- answers cite files/symbols/tests
- unknowns are explicit
- context pack is saved

Current note: deterministic context pack and answer writer are implemented.
Optional LLM answer is still future work.

## v0.5 - No-Leap Guardian And Ledger

Deliverables:

- observer report
- unsupported claim detector
- missed evidence detector
- ledger writer
- run comparison

Exit criteria:

- observer catches intentionally bad answers in fixtures
- ledger can be searched in later runs

## v0.6 - Better Graphs

Candidates:

- Tree-sitter
- LSP references
- SCIP/LSIF import
- route/API map
- config/data flow map
- UI/API surface map

Only add these after v0.3-v0.5 are useful.

## v1.0 - Production Candidate

Production candidate requires:

- deterministic tests
- successful scan of this repo and at least 3 fixture repos
- bounded runtime on large repos
- clear artifact layout
- observer score stable
- no uncontrolled writes to user repos
- clear graduation plan into core tools/orchestration
