# Software Factory v0.7

Software Factory v0.7 is the product-to-code planning layer for prompts that
are bigger than a narrow coding task.

It exists because strict JSON tool calls are excellent for coding actions, but
they are a poor container for long business analysis. v0.7 separates the two:

- Long business, product, domain, architecture, and docs analysis is written as
  artifacts under `workspace/factory_runs/<run_id>/`.
- Agent protocol JSON stays small and only contains decisions, route metadata,
  and artifact references.
- A compact handoff packet tells Code Agent which artifacts to read and what
  output contract to return.

## When To Use It

Use Software Factory first when the prompt asks for:

- Product or business analysis before coding.
- A new software product or mini-project with unclear domain logic.
- BRD/PRD/epics/stories/acceptance criteria.
- Architecture or pattern decisions that must be justified.
- Documentation that should be compiled from evidence.

Use the existing Company/LangGraph path directly when the task is already a
small code edit with clear files and tests.

## Pipeline

```text
Intake Protocol Agent
  -> Product Vision Agent
  -> BRD Agent
  -> PRD Agent
  -> Epic Story Agent
  -> Acceptance Criteria Agent
  -> Product Spec Validator Agent
  -> Product Spec Critic Agent
  -> Domain Analyst Agent
  -> Business Logic Model Agent
  -> Business Logic Validator Agent
  -> Technical Analyst Agent
  -> Pattern Decision Agent
  -> Implementation Spec Agent
  -> Code Handoff Packager Agent
  -> Code Agent handoff
  -> Docs Orchestrator Agent
  -> Repo Scanner Agent
  -> API Extractor Agent
  -> Architecture Decision Recorder Agent
  -> Docs Writer Agent
  -> Docs Verifier Agent
  -> Final Agent
```

The v0.7 run does not implement code by itself. It creates a gated
implementation spec that can be handed to the real Code/Test/Review/Ledger
pipeline.

## Core Rule

```text
No Protocol Strategy -> no product analysis
No Vision -> no BRD
No BRD -> no PRD
No Story + AC -> no technical design
No Business Logic Model -> no technical analysis
No Domain Analysis + Change Hotspots -> no pattern decision
No Pattern Decision evidence -> no code
No Code Handoff Packet -> no engineering execution
No Docs Verification -> not done
```

## Commands

Run the deterministic smoke:

```powershell
python run_software_factory_smoke.py
```

Expected marker:

```text
SOFTWARE_FACTORY_SMOKE_OK
```

Run on the life-simulation prompt:

```powershell
python run_software_factory_demo.py --task-file prompts/the_sims_prompt.md
```

Print the full compact JSON envelope:

```powershell
python run_software_factory_demo.py --task-file prompts/the_sims_prompt.md --full-json
```

Then hand the generated implementation spec to the real coding pipeline:

```powershell
python run_company_agents_demo.py --real --task-file workspace/factory_runs/<run_id>/10_implementation_spec.md --real-max-steps 260
```

## Artifact Protocol

Each stage returns a compact envelope:

```json
{
  "agent": "Pattern Decision Agent",
  "department": "Architecture Decision Department",
  "version": "v0.7",
  "ok": true,
  "decision": "pattern_decision_has_hotspot_evidence",
  "artifact_refs": [
    {
      "path": "workspace/factory_runs/.../09_pattern_decision.md",
      "kind": "pattern_decision",
      "producer": "Pattern Decision Agent",
      "title": "Pattern Decision",
      "summary": "Pattern Decision",
      "bytes": 1234,
      "sha256": "..."
    }
  ],
  "route": {
    "next_agent": "Implementation Spec Agent",
    "reason": "Pattern Decision is available as an artifact reference."
  }
}
```

The envelope never carries the full analysis. It carries the path and hash.

## Generated Artifacts

Typical run output:

```text
workspace/factory_runs/<run_id>/
  00_protocol_strategy.json
  00_vision.md
  01_brd.md
  02_prd.md
  03_epics_stories.md
  04_acceptance_criteria.md
  05_product_spec_validation.json
  06_product_spec_critique.md
  07_domain_analysis.md
  08_business_logic_model.md
  08_business_logic_validation.json
  08_technical_analysis.md
  09_pattern_decision.md
  10_implementation_spec.md
  11_code_handoff_packet.json
  11_docs_plan.md
  12_repo_scan.json
  13_api_inventory.json
  14_adr_candidates.md
  15_docs_package.md
  16_docs_verification.json
  17_factory_final.md
  99_factory_summary.json
```

## Pattern Decision Rule

Product specs are not allowed to select design patterns. Pattern decisions only
happen after the Domain Analyst has identified change hotspots.

Every pattern decision must answer:

- What problem does it solve?
- Why is it needed now?
- What happens if it is not used?
- What is the overengineering risk?
- Which module owns it?
- Which story, acceptance criterion, or hotspot proves the need?

## Protocol Adapter

v0.7 adds an Intake Protocol Agent before product analysis. It decides how the
task should move through the factory:

- `control_channel`: compact JSON envelope for route/status/artifact refs.
- `analysis_channel`: artifact files for BRD, PRD, domain, logic, and docs.
- `max_inline_chars`: small inline summaries only.

This is the adaptation for prompts where parseable JSON is too small for
business analysis. JSON remains strict for tool calls because each call is a
small coding action; long reasoning is stored in artifact files and passed by
path/hash.

## Business Logic Department

Business Logic Model Agent converts domain analysis into:

- invariants
- decision tables
- state transitions
- testable examples
- failure modes

Business Logic Validator Agent gates the pipeline before technical analysis.
This prevents Code Agent from receiving broad business prose without executable
logic.

## Code Handoff Packet

Code Handoff Packager Agent writes `11_code_handoff_packet.json`. The packet is
intentionally compact:

- read order for artifacts
- artifact refs with path/hash
- Code Agent must/must-not rules
- completion requirements

The handoff packet does not duplicate long analysis. It points to it.

## Docs Department

Docs are compiled from evidence, not invented.

The docs department includes:

- Docs Orchestrator Agent
- Repo Scanner Agent
- API Extractor Agent
- Architecture Decision Recorder Agent
- Docs Writer Agent
- Docs Verifier Agent

The verifier checks that docs are backed by artifacts and repo evidence. It also
marks the docs as needing re-verification after real code changes.

## Relationship To v0.5

v0.5 Company Agents are the execution room:

```text
Research -> Planner -> Architect -> Code -> Test -> Review -> Ledger -> Final
```

v0.7 Software Factory is the specification room:

```text
Business idea -> Product evidence -> Domain evidence -> Pattern evidence -> Implementation spec
```

For complex product prompts, run v0.7 first, then feed
`10_implementation_spec.md` to v0.5 real execution.
