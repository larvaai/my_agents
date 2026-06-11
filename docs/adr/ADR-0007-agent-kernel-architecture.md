# ADR-0007: Agent Kernel Architecture

## Status

Accepted.

## Context

The project grew from a direct ReAct loop into multiple runtimes:

- single-agent orchestrator
- LangGraph role orchestration
- Company Agents
- Software Factory
- Global Supervisor
- many MCP servers and tool schemas

Before this ADR, `tools/` acted as an implicit core. Agents and orchestrators
called a tool registry that delegated straight to MCP. This worked, but it made
capability discovery, feature boundaries, and null fallback behavior implicit.

## Decision

Introduce an Agent Kernel layer:

- `core.kernel.AgentKernel` owns state, events, and capability dispatch.
- `core.registry.CapabilityRegistry` owns feature/tool registration.
- `core.ports.*` defines stable port contracts for search, memory, browser,
  code edit, test run, issue tracking, and generic tool execution.
- `features.mcp_tools.MCPToolAdapter` wraps the existing MCP tool system.
- `core.capabilities.call_tool()` is the only internal tool entry point.
- `config/features.yaml` controls whether the `mcp_tools` feature is installed.
- Every enabled feature must declare tests, and `run_feature_tests.py` enforces
  that contract.

This is a strangler refactor: existing agents and orchestrators keep their
imports, while the runtime path now crosses the kernel boundary.

## Consequences

Positive:

- Core can run without a concrete MCP server installed; missing capability
  returns a structured failure instead of crashing the process.
- New adapters can be added behind ports without changing agents.
- Event bus and state store provide a central place for future replay,
  observability, and module coordination.
- `tools/` is no longer the architectural center; it only keeps compatibility helpers.

Tradeoffs:

- There is a stricter boundary: callers go through `core.capabilities`, while
  MCP-specific implementation stays inside `features/mcp_tools`.
- MCP schemas, config, client, and policy live under `features/mcp_tools/`.
- Existing agents still use direct role allowlists in code. Moving those to
  config should be a separate change.

## Migration Rules

1. New infrastructure contracts go in `core/`.
2. New external integrations go in `features/` or `mcp_servers/`.
3. Agents should depend on ports/facades, not concrete MCP server details.
4. Optional capabilities need a null fallback.
5. Every enabled feature needs at least one deterministic test module.
6. Tool results must remain structured dicts with `ok`, `tool`, and error
   metadata on failure.
