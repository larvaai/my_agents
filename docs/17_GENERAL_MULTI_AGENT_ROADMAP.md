# General Multi-Agent Roadmap

This document is a design agreement checkpoint. It describes the phases, file
structure, routing flow, and contracts for upgrading `my_agents` from a
coding-first agent system into a general multi-agent system where the Coding
Department runs only when the request needs code or repo work.

Status: phases 1-6 are implemented as a low-risk deterministic wrapper.
Product-build prompts now route through Software Factory before coding handoff.

## Goal

Move from:

```text
User request -> coding-oriented graph -> code/repo tools -> final answer
```

to:

```text
User request
  -> Global Supervisor / Intent Router
  -> selected department or execution plan
  -> Final Synthesis Agent
  -> final answer
```

The existing coding system remains intact. It becomes the Coding Department
subgraph behind the router.

## Non-Goals For This Roadmap

- Do not rewrite the existing LangGraph, Company Agents, or Software Factory
  flows in phase 1.
- Do not move existing agent files into a new directory tree yet.
- Do not give knowledge/research agents write access to repo files.
- Do not let each department produce the final user answer independently.
- Do not add broad new tools before a safety gate exists.

## Phase 1: Simple Router

Status: implemented in `orchestration/intent_router.py` and
`orchestration/global_supervisor.py`.

Add a thin supervisor layer with three route types first:

```text
GENERAL_KNOWLEDGE
CODE_TASK
AGENT_CREATION
```

Proposed files:

```text
orchestration/
  intent_router.py
  global_supervisor.py
run_global_supervisor_smoke.py
prompts/auto_cases/test_global_router_01_smoke.md
```

`orchestration/intent_router.py` owns:

- `IntentType` enum or string constants.
- `RouteDecision` dict/dataclass schema.
- Deterministic keyword classifier first.
- Optional LLM classifier later, behind the same output schema.

Minimal route decision shape:

```json
{
  "intent": "GENERAL_KNOWLEDGE | CODE_TASK | AGENT_CREATION",
  "confidence": 0.0,
  "needs_repo": false,
  "needs_code": false,
  "needs_web": false,
  "needs_memory": false,
  "target_department": "knowledge | coding | agent_factory",
  "reason": "short routing reason"
}
```

`orchestration/global_supervisor.py` owns:

- entrypoint function for the new global flow
- router invocation
- department dispatch
- collection of department output
- call to Final Synthesis Agent

Phase 1 flow:

```text
User
  -> Global Supervisor
  -> Intent Router
     -> GENERAL_KNOWLEDGE -> General Knowledge Agent placeholder
     -> CODE_TASK -> existing Company/LangGraph coding path
     -> AGENT_CREATION -> Agent Factory placeholder or Software Factory spec path
  -> Final Synthesis Agent placeholder
```

Acceptance checks:

- A general knowledge prompt must not call repo write tools.
- A code prompt still reaches the existing coding path.
- An agent creation prompt routes away from general knowledge.
- The router output is compact JSON and easy to test.

## Phase 2: Knowledge Agent

Status: implemented in `agents/knowledge/`.

Add the first read-only Knowledge Department. It should answer stable conceptual
questions without triggering code tools.

Proposed files:

```text
agents/
  knowledge/
    __init__.py
    general_knowledge_agent/
      __init__.py
      agent.py
      prompt.md
    philosophy_agent/
      __init__.py
      agent.py
      prompt.md
docs/agents/knowledge-department.md
```

Initial allowed capabilities:

- no file writes
- no terminal execution
- no Python execution
- optional RAG later
- optional citation only when the answer depends on external sources

Phase 2 flow:

```text
GENERAL_KNOWLEDGE
  -> Knowledge Department
  -> General Knowledge Agent or Philosophy Agent
  -> department output
  -> Final Synthesis Agent
```

Knowledge output shape:

```json
{
  "department": "knowledge",
  "agent": "general_knowledge_agent",
  "answer_draft": "short or medium answer",
  "confidence": "low | medium | high",
  "needs_research": false,
  "sources": [],
  "limits": []
}
```

Acceptance checks:

- Philosophy questions route to `philosophy_agent`.
- Generic explanation questions route to `general_knowledge_agent`.
- Knowledge agents cannot modify repo files.
- RAG can be added later without changing the router contract.

## Phase 3: Final Synthesis Agent

Status: implemented in `agents/final_synthesis_agent.py`.

Create a dedicated agent that owns the final user-facing answer.

Proposed files:

```text
agents/
  final_synthesis_agent.py
docs/agents/final-synthesis-agent.md
```

Rule:

```text
Departments produce department outputs.
Final Synthesis Agent produces the final answer.
```

It must receive:

```json
{
  "user_request": "...",
  "route_decision": {},
  "execution_plan": [],
  "department_outputs": {},
  "validation_evidence": [],
  "citations": [],
  "limits": []
}
```

Responsibilities:

- merge department outputs
- answer in the user's requested language
- expose uncertainty and limits
- include validation evidence for code tasks
- include citations for research tasks
- avoid mentioning internal routing unless useful

Acceptance checks:

- No department directly returns the final answer to the user.
- Code completion still reports tests/validation evidence.
- Knowledge answers stay concise and do not claim tool work happened.

## Phase 4: Research Department

Status: implemented as deterministic skeleton plus optional MCP hooks in
`agents/research_department/`. PDF/Text Extraction MCP is registered as
`pdf_text_extraction.extract_text`.

Add a department for current, external, paper, PDF, and citation-heavy work.

Proposed files:

```text
agents/
  research_department/
    __init__.py
    search_agent.py
    source_reader_agent.py
    pdf_text_extraction_agent.py
    citation_agent.py
mcp_servers/
  pdf_text_extraction_server.py
docs/agents/research-department.md
docs/mcp/pdf-text-extraction-mcp.md
```

Notes:

- Search MCP and Fetch MCP already exist in this repo; phase 4 wires them into
  the Research Department instead of rebuilding them.
- PDF/Text Extraction MCP can start as a small local text extractor and later
  expand to richer PDF parsing.
- Citation Agent is responsible for source formatting and source quality notes.

Phase 4 flow:

```text
RESEARCH_REQUIRED
  -> Search Agent
  -> Source Reader Agent
  -> PDF/Text Extraction Agent when needed
  -> Citation Agent
  -> Final Synthesis Agent
```

Research output shape:

```json
{
  "department": "research",
  "claims": [],
  "sources": [
    {
      "title": "...",
      "url_or_path": "...",
      "source_type": "web | paper | pdf | local_doc",
      "retrieved_at": "ISO timestamp",
      "relevance": "low | medium | high"
    }
  ],
  "citation_notes": [],
  "limits": []
}
```

Acceptance checks:

- Current or external-info questions route to Research Department.
- Final answers cite sources when research tools were used.
- Research agents do not write repo files.

## Phase 5: Mixed Routing

Status: implemented in `orchestration/intent_router.py` and
`orchestration/global_supervisor.py`.

Upgrade the router from single intent to an execution plan.

Additional route types:

```text
RESEARCH_REQUIRED
REPO_TASK
DEBUG_TASK
WRITING_TASK
PLANNING_TASK
MIXED_TASK
NEUROSCIENCE_TASK
PHILOSOPHY_TASK
```

Execution plan shape:

```json
{
  "intent": "MIXED_TASK",
  "confidence": 0.91,
  "execution_mode": "single | sequential | parallel",
  "needs_repo": true,
  "needs_code": true,
  "needs_web": false,
  "needs_memory": true,
  "steps": [
    {
      "department": "knowledge",
      "task": "Explain the concept needed for the design."
    },
    {
      "department": "coding",
      "task": "Map the concept into the target repo module."
    },
    {
      "department": "qa",
      "task": "Validate behavior with tests."
    }
  ]
}
```

Phase 5 flow examples:

```text
Single:
User -> Router -> Knowledge -> Final Synthesis

Sequential:
User -> Router -> Knowledge -> Coding -> Test -> Final Synthesis

Parallel:
User -> Router -> Research + Reasoning + Writing -> Final Synthesis
```

Acceptance checks:

- Mixed prompts can call more than one department.
- The plan is explicit before tools run.
- Final Synthesis receives all department outputs.
- The existing coding path is still callable as a subgraph.

## Phase 6: Safety Department

Status: implemented in `agents/safety/` and wired into
`orchestration/global_supervisor.py`.

Add a Safety Department before broad mixed routing is allowed to use tools.

Proposed files:

```text
agents/
  safety/
    __init__.py
    permission_agent.py
    risk_agent.py
    prompt_injection_agent.py
    tool_scope_agent.py
docs/agents/safety-department.md
```

Responsibilities:

- Permission Agent: decide whether the planned action needs explicit user
  approval or a narrower scope.
- Risk Agent: classify operational, repo, network, data, and destructive risk.
- Prompt Injection Agent: inspect external/web/PDF content before it influences
  tool use or repo edits.
- Tool Scope Agent: enforce department-level tool boundaries.

Phase 6 flow:

```text
User
  -> Global Supervisor
  -> Intent Router / Execution Plan
  -> Safety Department when tools, repo, web, or file writes are involved
  -> selected departments
  -> Final Synthesis Agent
```

Hard safety rules:

- Knowledge Department cannot write files.
- Research Department cannot modify repo files.
- Coding Department cannot browse by default unless the execution plan says
  current external information is required.
- Agent Factory cannot update registries without a test/smoke plan.
- Prompt-injected external content cannot change tool permissions.

Acceptance checks:

- Tool access is scoped by department.
- File writes require a coding/factory route, not a knowledge route.
- External content is treated as untrusted input.
- Final Synthesis discloses blockers instead of bypassing safety.

## Proposed Global State

Use a global state that can represent non-code tasks without forcing repo
context.

```python
class GlobalAgentState(TypedDict, total=False):
    user_request: str
    route_decision: dict[str, Any]
    execution_plan: list[dict[str, Any]]
    selected_department: str
    department_outputs: dict[str, Any]
    knowledge_context: dict[str, Any]
    repo_context: dict[str, Any]
    research_context: dict[str, Any]
    safety_report: dict[str, Any]
    validation_evidence: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    final_answer: str
    errors: list[str]
```

Important rule:

```text
repo_context is optional.
code tools are optional.
web/research tools are optional.
memory/RAG is optional.
```

## Proposed File Structure After All Phases

Low-risk structure, preserving existing files:

```text
orchestration/
  global_supervisor.py
  intent_router.py
  company_orchestrator.py
  software_factory_orchestrator.py
  langgraph_orchestrator.py

agents/
  knowledge/
    general_knowledge_agent/
      agent.py
      prompt.md
    philosophy_agent/
      agent.py
      prompt.md
  research_department/
    search_agent.py
    source_reader_agent.py
    pdf_text_extraction_agent.py
    citation_agent.py
  safety/
    permission_agent.py
    risk_agent.py
    prompt_injection_agent.py
    tool_scope_agent.py
  final_synthesis_agent.py
  code_agent.py
  test_agent.py
  review_agent.py
  planner_agent.py
  architect_agent.py
  research_agent.py

mcp_servers/
  pdf_text_extraction_server.py

docs/
  17_GENERAL_MULTI_AGENT_ROADMAP.md
  agents/
    knowledge-department.md
    research-department.md
    safety-department.md
    final-synthesis-agent.md
```

Do not rename or move current core agents in the first pass. The new structure
wraps the existing coding system instead of replacing it.

## Implementation Status Summary

1. Done: Phase 1 router/supervisor with smoke tests.
2. Done: Phase 2 read-only Knowledge Department with two agents.
3. Done: Phase 3 Final Synthesis Agent as final answer owner.
4. Done: Phase 4 Research Department and citation flow.
5. Done: Phase 5 multi-step execution plans for mixed tasks.
6. Done: Phase 6 Safety Department gate for tool/repo/web actions.
7. Done: Product-build route `PRODUCT_BUILD_TASK` sends large multi-file
   product prompts to Software Factory, then exposes implementation spec and
   code handoff packet to the existing coding path.

## Product-Build Routing Update

Large prompts such as `prompts/the_sims_complex_prompt.md` should not be
handled as a normal code edit and should not be misclassified as philosophy or
research because of filenames like `autonomy.py` or generic phrases like
`gioi han hien tai`.

Current route:

```text
User product prompt
  -> Global Supervisor
  -> Intent Router: PRODUCT_BUILD_TASK
  -> Safety Department
  -> Software Factory
  -> Coding Department delegate or real coding path when enabled
  -> Final Synthesis
```

Validation command:

```powershell
python run_global_supervisor_demo.py --task-file prompts/the_sims_complex_prompt.md --run-id global_supervisor_complex_trial
```

## Next Decision Point

Before expanding beyond the deterministic wrapper, confirm:

- whether Agent Factory should become a real department before mixed routing
- whether Safety Department should gate every tool plan or continue gating only
  repo/code/web/agent-factory plans
- whether Final Synthesis should start using LLM synthesis or stay deterministic
  until the global supervisor smoke is stable
- whether `run_coding=True` and `research_use_tools=True` should be exposed in
  a CLI runner or remain API-only for now
