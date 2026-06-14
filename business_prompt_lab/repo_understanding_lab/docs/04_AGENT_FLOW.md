# Agent Flow

## Proposed Agent Roster

### Task Analyzer

Turns the user request into a route:

- baseline
- ask
- impact
- test-selection
- observe-run
- patch-proposal later

### Repo Cartographer

Builds the first map:

- root files
- folders
- source/test/docs/config grouping
- likely entrypoints
- large/generated/vendor exclusions

### Manifest Reader

Understands what the repo lives on:

- language
- package manager
- dependencies
- scripts
- build/test/lint commands

### Docs Grounder

Reads docs as intent and links docs to code symbols/files.

### Symbol Indexer

Extracts code symbols and signatures.

### Dependency Analyst

Builds import and package dependency maps.

### Runtime Investigator

Finds run/test/build commands and ranks confidence.

### Test Intelligence Agent

Maps tests to files and symbols, and suggests targeted tests.

### Behavior Analyst

Builds input-to-output flow from entrypoints, handlers, and common data objects.

### Context Packer

Selects bounded evidence for answer/impact agents.

### Answer Agent

Answers the user with evidence. It cannot invent facts outside the context pack.

### Impact Analyzer

Predicts blast radius for a file/symbol/config change.

### No-Leap Guardian

Reviews whether the run followed evidence and did not jump to conclusions.

### Ledger Agent

Saves reusable lessons.

## First-Run Flow

```text
User provides repo path
  -> Repo Cartographer
  -> Manifest Reader
  -> Docs Grounder
  -> Symbol Indexer
  -> Dependency Analyst
  -> Runtime Investigator
  -> Test Intelligence
  -> Behavior Analyst
  -> baseline summary
  -> No-Leap Guardian
  -> Ledger Agent
```

## Question Flow

```text
User question
  -> Task Analyzer
  -> entity extraction
  -> symbol search
  -> graph traversal depth 1-2
  -> docs/test/ledger lookup
  -> Context Packer
  -> Answer Agent
  -> No-Leap Guardian
  -> Final Answer
  -> Ledger Agent
```

## Impact Flow

```text
Target file/symbol
  -> locate node
  -> callers/callees
  -> tests
  -> configs/runtime commands
  -> recent git changes
  -> risk list
  -> suggested validation commands
  -> No-Leap Guardian
```

## Patch Proposal Flow Later

Patch mode must not be in v0.1/v0.2.

Later:

```text
User change request
  -> Task Analyzer
  -> Context Packer
  -> Impact Analyzer
  -> Patch Planner
  -> Patch Proposal
  -> Test Intelligence
  -> Review Agent
  -> No-Leap Guardian
  -> Ledger Agent
```

The first patch version should produce a proposed diff or plan, not apply it
automatically.

## Human/User Agent Override

This lab should eventually support a User Agent channel:

- user can add evidence requirements
- user can force a specific file/symbol into context
- user can mark an agent as unnecessary for the current run
- user can request a narrower or broader graph slice
- user instructions override internal agent preferences

The User Agent should be logged as a first-class event.

## Flow Quality Checks

The observer checks:

- Did the run start from repo shape?
- Did it read manifest before runtime guesses?
- Did it read docs as intent, not truth?
- Did it build symbol or graph evidence?
- Did it map tests?
- Did it state unknowns?
- Did it avoid patching before impact analysis?

