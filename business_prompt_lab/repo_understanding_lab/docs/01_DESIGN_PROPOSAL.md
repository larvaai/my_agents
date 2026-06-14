# Design Proposal

## Name

`repo_understanding_lab`

## Mission

Build a mini repo that lets us test whether an agent can understand a codebase
before it answers questions or proposes edits.

The first successful version should answer questions like:

- "Planner Agent works how?"
- "Which tests cover this module?"
- "If I change this function, what may break?"
- "Where does this config value flow?"
- "Why did this area fail before?"

The answer must cite evidence from the maps it built.

## Scope

In scope:

- read repo structure
- read dependency manifests
- read docs
- detect entrypoints
- extract symbols
- build import graph
- build simple call graph
- map tests to files/symbols
- infer runtime commands
- assemble context packs
- run observer critique
- write ledger entries

Out of scope for the first implementation:

- automatic patching
- self-modifying skills
- full multi-language LSP integration
- vector DB dependency
- changing the main project orchestration

Patch proposal can appear later, but only after the read/understand loop is
measured.

## Design Principles

### 1. Docs Are Intent, Code Is Current State

The system should classify evidence:

```text
docs      = intended design
code      = current implementation
tests     = behavior contract
logs      = failure trace
git       = evolution history
ledger    = learned memory
```

The final answer must not treat docs as absolute truth if code disagrees.

### 2. Graph Before Guess

The agent should not jump from a keyword search to an answer. It should build a
small graph slice:

```text
symbol
  -> defined_in file
  -> called_by callers
  -> calls callees
  -> tested_by tests
  -> documented_by docs
  -> touched_by recent commits
```

### 3. Evidence Pack Before Answer

Each answer should come from a `ContextPack`, not from loose text snippets.

The pack includes:

- user question
- detected intent
- entities
- relevant files
- relevant symbols
- graph slice
- docs references
- test references
- git/ledger references
- risks and unknowns

### 4. No-Leap Rule

The observer must flag statements that move too fast:

```text
Weak: "Planner is broken."
Better: "The failing test asserts Planner output. Planner receives TaskContext
from QuestionAnalyzer. The trace shows intent is missing before Planner runs.
The likely root cause is upstream of Planner."
```

### 5. Minimal Runtime First

Do not start with Tree-sitter, LSP, SCIP, vector DB, and a UI at once.

Start with deterministic Python stdlib indexing:

- filesystem scan
- manifest reader
- Python `ast`
- regex fallback for docs/routes
- JSON artifacts
- mock fixtures

Then graduate to richer tools only when the simple path proves useful.

## Proposed User Flows

### Flow A: First Repo Baseline

```text
repo path
  -> scan root
  -> detect profile
  -> read manifests
  -> read docs
  -> parse source
  -> build maps
  -> save baseline
  -> summarize architecture
```

### Flow B: Ask A Repo Question

```text
question
  -> classify intent
  -> extract entities
  -> retrieve graph slice
  -> read relevant files
  -> read related docs/tests/ledger
  -> build context pack
  -> answer with evidence
  -> observer critique
```

### Flow C: Impact Analysis

```text
target file/symbol
  -> caller/callee graph
  -> test map
  -> config/runtime map
  -> recent git changes
  -> risk summary
  -> suggested tests
```

### Flow D: Patch Proposal Later

```text
bug/task
  -> context pack
  -> impact analysis
  -> patch plan
  -> proposed diff
  -> targeted tests
  -> review
  -> ledger
```

Patch proposal is later because the first value is repo understanding.

## Success Criteria

The lab is useful when:

- it can explain repo structure without reading random files
- it can find relevant symbols from a natural question
- it can show caller/callee/test evidence
- it can tell when evidence is missing
- it can recommend targeted tests
- observer can catch unsupported conclusions
- outputs are saved in stable JSON/Markdown artifacts

