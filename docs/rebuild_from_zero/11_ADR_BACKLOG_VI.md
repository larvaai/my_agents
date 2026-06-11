# ADR Backlog

## ADR-001 - Use JSON-Only Agent Protocol

Status: accepted.

Decision:

- Agent must return one JSON object for tool or final.

Reason:

- Orchestrator needs machine-checkable actions.
- Tool calls cannot depend on prose parsing.

Consequence:

- Need JsonGate and retry flow.

## ADR-002 - Use Agent Kernel And CapabilityResult Envelope

Status: accepted.

Decision:

- All tool calls go through `core.capabilities.call_tool()`.
- Results wrapped as `CapabilityResult`.

Reason:

- Decouple core orchestration from tool backend.
- Allow removable features.

Consequence:

- Adapters must normalize raw tool results.

## ADR-003 - MCP Tools As Removable Feature

Status: accepted.

Decision:

- MCP integration lives in `features/mcp_tools/`.
- Kernel knows only ToolPort/registry.

Reason:

- Avoid core depending on MCP implementation.

Consequence:

- Feature config and feature tests become required.

## ADR-004 - File Editor Is Primary Edit Path

Status: accepted.

Decision:

- Agent should edit via `file_editor.*`, not terminal.

Reason:

- Edits become auditable and scoped.
- `str_replace` can guard broad replacements.

Consequence:

- Generated long files need `write_lines` to avoid JSON string fragility.

## ADR-005 - Terminal Is Argv-Only

Status: accepted.

Decision:

- Terminal MCP accepts `argv` list, no shell string.

Reason:

- Shell is too broad and hard to audit.

Consequence:

- Some commands need dedicated MCP tools instead of shell hacks.

## ADR-006 - Finish Gate For Code Changes

Status: accepted.

Decision:

- Code change sets pending validation.
- Final success blocked until validation passes or blocker reported.

Reason:

- Prevent false "done".

Consequence:

- Orchestrator must detect code-change and validation tools.

## ADR-007 - Role Ownership

Status: accepted.

Decision:

- Code edits.
- Test validates.
- Review approves/requests changes.
- Ledger records.
- Final communicates.

Reason:

- Reduces self-approval and responsibility mixing.

Consequence:

- Role allowlists and route contracts required.

## ADR-008 - Artifact-First Software Factory

Status: accepted.

Decision:

- Long BRD/PRD/domain/logic/docs analysis goes into artifacts.
- JSON carries route and artifact refs only.

Reason:

- Long JSON payloads are fragile and hard to audit.

Consequence:

- Artifacts need path/hash/summary.
- Handoff packet points to artifacts.

## ADR-009 - Pattern Decisions Require Hotspot Evidence

Status: accepted.

Decision:

- Pattern Decision Agent cannot select pattern before Domain Analysis and
  Business Logic Validation.

Reason:

- Avoid overengineering from product prose.

Consequence:

- Implementation Spec depends on Pattern Decision.

## ADR-010 - Global Supervisor Routes Non-Code Tasks Away From Coding

Status: accepted.

Decision:

- IntentRouter classifies knowledge/research/code/product/mixed tasks.

Reason:

- Not every user request should enter repo/code tooling.

Consequence:

- Final Synthesis must merge department outputs.

## ADR Candidates For Future

### ADR-F01 - Persistent MCP Process Pool

Problem:

- Current stdio-per-call is simple but slow.

Decision to make:

- Keep per-call for correctness or add session pool.

### ADR-F02 - Event Viewer UI

Problem:

- JSONL inspect is useful but not enough for long runs.

Decision to make:

- Build local web UI or stay CLI-first.

### ADR-F03 - RAG Source Line Ranges

Problem:

- Current RAG hits have source/chunk but not line ranges.

Decision to make:

- Add line range metadata at ingest.

### ADR-F04 - Agent Factory Real Implementation

Problem:

- Global Supervisor can route agent creation, but Agent Factory is placeholder.

Decision to make:

- Define plugin/skill/agent scaffolding contract.

