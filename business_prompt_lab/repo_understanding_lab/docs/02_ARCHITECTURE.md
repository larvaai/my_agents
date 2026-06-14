# Architecture

## High-Level Shape

```text
User Question or Repo Path
  -> Task Analyzer
  -> Repo Scanner
  -> Manifest Reader
  -> Docs Reader
  -> Symbol Indexer
  -> Graph Builder
  -> Test Mapper
  -> Runtime Investigator
  -> Context Packer
  -> Answer or Impact Agent
  -> No-Leap Guardian
  -> Ledger Writer
```

## Proposed Folder Layout

Future runtime layout:

```text
business_prompt_lab/repo_understanding_lab/
  README.md
  main.py
  config/
    default.json
  docs/
  fixtures/
    tiny_python_repo/
  prompts/
    answer_agent.md
    observer_agent.md
  repo_understanding/
    scanner.py
    manifests.py
    docs_reader.py
    symbols.py
    graphs.py
    tests.py
    runtime.py
    context_pack.py
    observer.py
    ledger.py
    schemas.py
  tests/
    test_scanner.py
    test_symbols.py
    test_context_pack.py
```

Runtime output should stay outside source:

```text
var/repo_understanding_lab/<run_id>/
  inputs/
  maps/
  context/
  reports/
  transcript.jsonl
```

## Components

### Task Analyzer

Classifies user request:

- repo baseline
- architecture question
- symbol question
- behavior question
- impact analysis
- test selection
- patch proposal later

### Repo Scanner

Builds file inventory:

- path
- extension
- language guess
- size
- hash
- role guess
- ignored/generated flag

### Manifest Reader

Reads dependency/runtime declarations:

- `pyproject.toml`
- `requirements.txt`
- `package.json`
- `go.mod`
- `Cargo.toml`
- `Dockerfile`
- CI workflows

### Docs Reader

Reads high-value docs first:

- `README.md`
- `docs/**`
- `ADR/**`
- `CONTRIBUTING.md`
- `CHANGELOG.md`

Docs are evidence, not truth.

### Symbol Indexer

V0 should support Python with stdlib `ast`:

- function
- class
- method
- import
- assignment constants

Later versions can add Tree-sitter or LSP.

### Graph Builder

Builds simple graph edges:

- file defines symbol
- file imports file/package
- symbol calls symbol-like name
- test file tests source file
- docs mention symbol/file
- config read by source

### Runtime Investigator

Infers commands:

- run command
- test command
- lint command
- typecheck command
- build command

It should separate high-confidence commands from guessed commands.

### Context Packer

Turns many maps into one bounded context object for answer agents.

The pack should be small enough to feed to an LLM, but structured enough to
audit later.

### No-Leap Guardian

Reviews process quality:

- Did the flow read the right evidence?
- Did it skip tests?
- Did it over-trust docs?
- Did it confuse import with runtime behavior?
- Did it answer beyond evidence?

### Ledger Writer

Stores lessons:

- task
- evidence used
- mistakes found by observer
- tests suggested/run
- final answer summary
- reusable lesson

## Data Flow

```text
RepoPath
  -> FileMap
  -> SourceSet
  -> SymbolMap
  -> ImportGraph
  -> CallGraph
  -> TestMap
  -> RuntimeMap
  -> RepoKnowledgeGraph
  -> ContextPack
  -> FinalAnswer
  -> ObserverReport
  -> LedgerEntry
```

## Runtime Modes

### `--dry-run`

Show planned scan/index flow without reading all source.

### `--mock`

Use fixture repo and deterministic fake LLM outputs.

### `baseline`

Build maps for a repo and save artifacts.

### `ask`

Answer a question from an existing or freshly built index.

### `impact`

Analyze likely blast radius for a file/symbol.

### `observe`

Review a previous run transcript.

