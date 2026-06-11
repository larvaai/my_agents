# Software Factory Documentation

- Run ID: `global_supervisor_product_smoke`
- Source artifact dir: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke`
- Exported artifact count: `22`

## Artifact Index

| Key | Kind | File |
|---|---|---|
| `acceptance_criteria` | `acceptance_criteria` | `04_acceptance_criteria.md` |
| `adr_candidates` | `adr_candidates` | `14_adr_candidates.md` |
| `api_inventory` | `api_inventory` | `13_api_inventory.json` |
| `brd` | `business_requirements` | `01_brd.md` |
| `business_logic_model` | `business_logic_model` | `08_business_logic_model.md` |
| `business_logic_validation` | `business_logic_validation` | `08_business_logic_validation.json` |
| `code_handoff_packet` | `code_handoff_packet` | `11_code_handoff_packet.json` |
| `docs_package` | `docs_package` | `15_docs_package.md` |
| `docs_plan` | `docs_plan` | `11_docs_plan.md` |
| `docs_verification` | `docs_verification` | `16_docs_verification.json` |
| `domain_analysis` | `domain_analysis` | `07_domain_analysis.md` |
| `factory_final` | `factory_final` | `17_factory_final.md` |
| `implementation_spec` | `implementation_spec` | `10_implementation_spec.md` |
| `pattern_decision` | `pattern_decision` | `09_pattern_decision.md` |
| `prd` | `product_requirements` | `02_prd.md` |
| `product_critique` | `product_spec_critique` | `06_product_spec_critique.md` |
| `product_validation` | `product_spec_validation` | `05_product_spec_validation.json` |
| `protocol_strategy` | `protocol_strategy` | `00_protocol_strategy.json` |
| `repo_scan` | `repo_scan` | `12_repo_scan.json` |
| `stories` | `epics_stories` | `03_epics_stories.md` |
| `technical_analysis` | `technical_analysis` | `08_technical_analysis.md` |
| `vision` | `product_vision` | `00_vision.md` |

## Expected Flow

Product Vision -> BRD -> PRD -> Epic/Story -> Acceptance Criteria -> Product Validator/Critic -> Domain -> Business Logic -> Technical -> Pattern -> Implementation Spec -> Code Handoff -> Docs Orchestrator -> Repo Scanner -> API Extractor -> ADR -> Docs Writer -> Docs Verifier -> Final

The source of truth remains the factory run directory; this folder is a project-local mirror for product readers and downstream coding agents.
