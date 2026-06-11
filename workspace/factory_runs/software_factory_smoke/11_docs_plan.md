# Documentation Plan

## Inputs
- implementation_spec: `workspace\factory_runs\software_factory_smoke\10_implementation_spec.md`
- code_handoff_packet: `workspace\factory_runs\software_factory_smoke\11_code_handoff_packet.json`

## Documentation Jobs
- Repo Scanner: identify real files, entrypoints, tests, docs, and generated artifacts.
- API Extractor: list public classes/functions and command entrypoints.
- ADR Recorder: capture architectural decisions with evidence.
- Docs Writer: compile usage, architecture, testing, and limitations from evidence.
- Docs Verifier: reject docs that mention missing paths, commands, env vars, or APIs.
- Business Logic Verifier: ensure docs explain the logic contract only from
  accepted artifacts and observed code/test evidence.

## Docs Rule
Docs are compiled from repo evidence and stage artifacts. They are not marketing
copy and should not claim unverified behavior.
