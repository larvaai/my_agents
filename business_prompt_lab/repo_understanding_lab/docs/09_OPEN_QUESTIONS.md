# Open Questions

These questions should be answered before implementing beyond v0.2.

## Runtime Scope

Should the first real scanner support only Python, or Python plus JavaScript?

Recommendation: Python only for v0.3, because this repo is Python-heavy and
stdlib `ast` is enough for the first proof.

## Storage

Should maps be stored as flat JSON files or SQLite?

Recommendation:

- JSON for v0.2-v0.3
- SQLite after graph queries become hard

## LLM Dependency

Should the first answer flow call LLM?

Recommendation:

- deterministic templates first
- optional `--llm` later through root `llm.py`

## Vector Search

Should vector search be included early?

Recommendation: no. Build exact symbol search and graph traversal first.
Vector search can help later, but it should not replace symbol/graph evidence.

## Tree-Sitter/LSP

Should v0.3 use Tree-sitter or LSP?

Recommendation: no for the first scanner. Add Tree-sitter after Python AST
proves the artifact contracts.

## Patch Mode

Should the lab propose code changes?

Recommendation: not in early versions. Start with answer and impact analysis.
Patch mode should be proposal-only until the observer and test mapping are good.

## UI Integration

Should this show up in the process dashboard?

Recommendation: yes after v0.3. The dashboard should show:

- current indexing phase
- files scanned
- symbols extracted
- graph edges
- context pack
- observer report

## User Agent Integration

Should live user directives be supported?

Recommendation: yes after the mock runner. User can force evidence, remove an
agent for current run, or ask for a narrower context pack.

