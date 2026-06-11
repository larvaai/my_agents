from __future__ import annotations

import shutil
from pathlib import Path

from core.runtime_paths import WORKSPACE_DIR
from orchestration.software_factory_orchestrator import SoftwareFactoryOrchestrator


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    export_dir = WORKSPACE_DIR / "_software_factory_smoke_export"
    if export_dir.exists():
        shutil.rmtree(export_dir)

    task = """
    Build a terminal-only Python mini-project named `society_sim`.
    It must include people, houses, jobs, a world clock, automatic actions,
    save/load, a CLI demo, and assert-based tests. Do not use external packages.
    Required files: society_sim/models.py society_sim/rules.py
    society_sim/world.py society_sim/simulation.py society_sim/persistence.py
    society_sim/cli_demo.py society_sim/test_society_sim.py
    """.strip()

    result = SoftwareFactoryOrchestrator().run(
        task,
        run_id="software_factory_smoke",
        export_project_dir=export_dir,
    )
    _assert(result.get("ok") is True, f"factory did not pass: {result}")
    _assert(result.get("status") == "ready_for_real_code_test_review", "unexpected factory status")

    artifacts = result.get("artifacts", {})
    required_keys = [
        "protocol_strategy",
        "vision",
        "brd",
        "prd",
        "stories",
        "acceptance_criteria",
        "domain_analysis",
        "business_logic_model",
        "business_logic_validation",
        "technical_analysis",
        "pattern_decision",
        "implementation_spec",
        "code_handoff_packet",
        "docs_plan",
        "repo_scan",
        "api_inventory",
        "adr_candidates",
        "docs_package",
        "docs_verification",
        "factory_final",
    ]
    for key in required_keys:
        _assert(key in artifacts, f"missing artifact: {key}")
        path = Path(artifacts[key]["path"])
        _assert(path.exists(), f"artifact path does not exist: {path}")

    pattern_text = Path(artifacts["pattern_decision"]["path"]).read_text(encoding="utf-8")
    _assert("Change Hotspot Evidence" in pattern_text, "pattern decision lacks hotspot evidence")
    _assert("Pure rule functions" in pattern_text, "expected simulation rule decision missing")

    implementation_text = Path(artifacts["implementation_spec"]["path"]).read_text(encoding="utf-8")
    _assert("society_sim/models.py" in implementation_text, "implementation spec missed requested file")
    _assert("Coding Agent Contract" in implementation_text, "implementation contract missing")
    _assert("Business Logic Contract" in implementation_text, "business logic contract missing")

    handoff_text = Path(artifacts["code_handoff_packet"]["path"]).read_text(encoding="utf-8")
    _assert("artifact_reference_first" in handoff_text, "handoff packet did not select artifact references")

    exported_docs = result.get("exported_docs", {})
    _assert(exported_docs.get("artifact_count", 0) >= 20, exported_docs)
    export_path = export_dir / "docs" / "software_factory"
    _assert((export_path / "00_vision.md").exists(), "exported vision missing")
    _assert((export_path / "01_brd.md").exists(), "exported BRD missing")
    _assert((export_path / "02_prd.md").exists(), "exported PRD missing")
    _assert((export_path / "10_implementation_spec.md").exists(), "exported implementation spec missing")
    _assert((export_path / "README.md").exists(), "exported docs index missing")

    stages = result.get("stage_results", [])
    _assert(len(stages) >= 22, "not enough stage results")
    _assert(stages[-1]["route"]["next_agent"] == "done", "factory did not route to done")

    if export_dir.exists():
        shutil.rmtree(export_dir)

    print("SOFTWARE_FACTORY_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
