# Docs Package Draft

## Evidence
- vision: `workspace\factory_runs\20260610_201138_software_factory\00_vision.md`
- brd: `workspace\factory_runs\20260610_201138_software_factory\01_brd.md`
- prd: `workspace\factory_runs\20260610_201138_software_factory\02_prd.md`
- stories: `workspace\factory_runs\20260610_201138_software_factory\03_epics_stories.md`
- acceptance_criteria: `workspace\factory_runs\20260610_201138_software_factory\04_acceptance_criteria.md`
- implementation_spec: `workspace\factory_runs\20260610_201138_software_factory\10_implementation_spec.md`
- repo_scan: `workspace\factory_runs\20260610_201138_software_factory\12_repo_scan.json`
- api_inventory: `workspace\factory_runs\20260610_201138_software_factory\13_api_inventory.json`
- adr_candidates: `workspace\factory_runs\20260610_201138_software_factory\14_adr_candidates.md`

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
- Pattern Decision maps design choices to evidence.
- Engineering receives an implementation spec, not a raw brainstorm.
- Documentation Department compiles docs from repo evidence and artifacts.

## Verification Rule
Docs must mention only paths, commands, APIs, and env vars supported by evidence.
