# Docs Package Draft

## Evidence
- protocol_strategy: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\00_protocol_strategy.json`
- vision: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\00_vision.md`
- brd: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\01_brd.md`
- prd: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\02_prd.md`
- stories: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\03_epics_stories.md`
- acceptance_criteria: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\04_acceptance_criteria.md`
- domain_analysis: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\07_domain_analysis.md`
- business_logic_model: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\08_business_logic_model.md`
- business_logic_validation: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\08_business_logic_validation.json`
- implementation_spec: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\10_implementation_spec.md`
- code_handoff_packet: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\11_code_handoff_packet.json`
- repo_scan: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\12_repo_scan.json`
- api_inventory: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\13_api_inventory.json`
- adr_candidates: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\14_adr_candidates.md`

## Start Here
Run Spec Factory first when the task has business/product ambiguity:

```powershell
python run_software_factory_demo.py --task-file prompts/the_sims_prompt.md
```

Then feed the implementation spec artifact to the real coding pipeline:

```powershell
python run_company_agents_demo.py --real --task-file <factory-run>/10_implementation_spec.md --real-max-steps 260
```

## Architecture Summary
- Product Department creates Vision, BRD, PRD, Stories, and AC.
- Product Quality gates completeness before technical design.
- Domain and Technical Analysis identify boundaries and change hotspots.
- Business Logic Department turns domain analysis into invariants, decision
  tables, state transitions, failure modes, and testable examples.
- Pattern Decision maps design choices to evidence.
- Engineering receives an implementation spec plus a compact code handoff
  packet, not a raw brainstorm.
- Documentation Department compiles docs from repo evidence and artifacts.

## Verification Rule
Docs must mention only paths, commands, APIs, and env vars supported by evidence.
