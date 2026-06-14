# Data Contracts

All agents and tools should exchange structured objects. Free-form prose is only
allowed in the final user-facing answer and in human-readable report files.

## RepoProfile

```json
{
  "repo_path": "D:/Agent PRJ/my_agents",
  "languages": ["python"],
  "frameworks": ["langgraph"],
  "package_managers": ["pip"],
  "test_runners": ["unittest"],
  "entrypoints": ["main.py"],
  "confidence": 0.82
}
```

## FileNode

```json
{
  "id": "file:orchestrator.py",
  "path": "orchestrator.py",
  "language": "python",
  "role": "runtime_orchestrator",
  "size_bytes": 24893,
  "hash": "sha256:...",
  "is_test": false,
  "is_generated": false
}
```

## SymbolNode

```json
{
  "id": "symbol:orchestrator.run_orchestrator",
  "name": "run_orchestrator",
  "qualified_name": "orchestrator.run_orchestrator",
  "kind": "function",
  "file": "orchestrator.py",
  "line_start": 100,
  "line_end": 260,
  "signature": "run_orchestrator(task: str, ...) -> str",
  "docstring": "",
  "confidence": 0.91
}
```

## GraphEdge

```json
{
  "source": "symbol:main.main",
  "target": "symbol:orchestrator.run_orchestrator",
  "type": "calls",
  "evidence": {
    "file": "main.py",
    "line": 45,
    "snippet": "run_orchestrator(...)"
  },
  "confidence": 0.76
}
```

Allowed edge types:

```text
defines
imports
calls
called_by
tests
documented_by
configures
reads_config
depends_on
mentions
changed_by
learned_from
```

## TestMapItem

```json
{
  "test_id": "tests/test_user_agent_control.py::test_skip_critic_current_run",
  "path": "tests/test_user_agent_control.py",
  "test_type": "unit",
  "target_files": ["agents/user_agent.py", "orchestrator.py"],
  "target_symbols": ["agents.user_agent.UserAgentControl"],
  "last_status": "unknown",
  "reason": "test name and imports mention UserAgentControl"
}
```

## RuntimeCommand

```json
{
  "id": "unit_tests",
  "command": "python -m unittest discover -s tests",
  "purpose": "run unit/integration tests",
  "source": "docs/08_TESTING_GUIDE.md",
  "confidence": 0.88,
  "risk": "medium"
}
```

## ContextPack

```json
{
  "task": {
    "user_request": "Planner Agent works how?",
    "intent": "symbol_question",
    "success_criteria": ["answer cites files", "answer names callers/tests"]
  },
  "entities": ["PlannerAgent"],
  "repo_profile": {},
  "relevant_files": [],
  "relevant_symbols": [],
  "graph_slice": [],
  "docs_context": [],
  "tests": [],
  "runtime_commands": [],
  "ledger_lessons": [],
  "known_risks": [],
  "unknowns": []
}
```

## AgentOutput

Every internal agent should return this shape:

```json
{
  "agent": "ImpactAnalyzerAgent",
  "input_understood": true,
  "evidence": [],
  "decision": "",
  "confidence": 0.0,
  "risks": [],
  "next_actions": []
}
```

## ObserverReport

```json
{
  "agent": "NoLeapGuardian",
  "scores": {
    "context_precision": 0.0,
    "context_recall": 0.0,
    "tool_efficiency": 0.0,
    "patch_minimality": null,
    "test_adequacy": 0.0,
    "no_leap_score": 0.0,
    "ledger_quality": 0.0,
    "overall": 0.0
  },
  "findings": [],
  "unsupported_claims": [],
  "missed_evidence": [],
  "recommended_next_flow": "ask"
}
```

## LedgerEntry

```json
{
  "task": "Explain PlannerAgent",
  "question": "Planner Agent works how?",
  "evidence_used": [],
  "answer_summary": "",
  "observer_findings": [],
  "lesson": "",
  "created_at": "2026-06-14T00:00:00Z"
}
```

## Transcript Event

Runtime should log append-only events:

```json
{
  "run_id": "20260614_001122_abcd",
  "ts": "2026-06-14T00:11:22Z",
  "event": "agent_output",
  "agent": "SymbolIndexerAgent",
  "input_ref": "maps/file_map.json",
  "output_ref": "maps/symbol_map.json",
  "summary": "Extracted 412 symbols from 61 Python files."
}
```

