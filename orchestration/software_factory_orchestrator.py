from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from agents.artifact_protocol import (
    FACTORY_VERSION,
    ensure_artifact_dir,
    make_run_id,
    write_json_artifact,
)
from agents.software_factory_agents import (
    FACTORY_AGENTS,
    StageResult,
    compact_stage_results,
    final_factory_payload,
)
from core.runtime_paths import WORKSPACE_DIR


DOC_EXPORT_SUBDIR = Path("docs") / "software_factory"


def infer_project_export_dir(task: str) -> Path | None:
    """
    Infer the runtime workspace project directory from required Python file paths.
    """
    counts: dict[str, int] = {}
    for match in re.finditer(r"(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_-]+)[/\\][A-Za-z0-9_./\\-]+\.py", task):
        folder = match.group(1)
        if folder in {"agent_runs", "docs", "prompts", "test_runs", "var", "workspace"}:
            continue
        counts[folder] = counts.get(folder, 0) + 1

    if not counts:
        return None

    project_name = max(counts.items(), key=lambda item: item[1])[0]
    return WORKSPACE_DIR / project_name


class SoftwareFactoryOrchestrator:
    """
    Artifact-first product-to-code specification pipeline.

    The orchestrator is intentionally separate from the real coding runtime.
    It prepares a gated implementation spec that can be handed to the existing
    Company/LangGraph Code-Test-Review-Ledger chain.
    """

    def __init__(
        self,
        *,
        artifact_root: str | Path = WORKSPACE_DIR / "factory_runs",
        repo_root: str | Path = ".",
    ) -> None:
        self.version = FACTORY_VERSION
        self.artifact_root = Path(artifact_root)
        self.repo_root = Path(repo_root)

    def run(
        self,
        task: str,
        *,
        run_id: str | None = None,
        export_project_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        run_id = run_id or make_run_id("software_factory")
        artifact_dir = ensure_artifact_dir(artifact_root=self.artifact_root, run_id=run_id)
        context: dict[str, Any] = {
            "run_id": run_id,
            "artifact_dir": artifact_dir,
            "repo_root": self.repo_root,
            "artifacts": {},
        }
        results: list[StageResult] = []
        status = "ready_for_real_code_test_review"

        for agent in FACTORY_AGENTS:
            result = agent.run(task, context)
            results.append(result)
            if not result.ok:
                status = "blocked"
                break

        payload = final_factory_payload(context, results)
        payload.update(
            {
                "ok": status != "blocked",
                "status": status,
                "version": self.version,
                "stage_results": compact_stage_results(results),
            }
        )

        summary_ref = write_json_artifact(
            artifact_dir,
            "99_factory_summary.json",
            payload,
            kind="factory_summary",
            producer="SoftwareFactoryOrchestrator",
            title="Software Factory Summary",
            summary=f"Software factory run {run_id} ended with status {status}.",
        )
        payload["summary_artifact"] = summary_ref.to_dict()
        payload["next_recommended_command"] = self._next_command(payload)
        if export_project_dir is not None:
            payload["exported_docs"] = self._export_project_docs(
                payload,
                export_project_dir=export_project_dir,
            )
        return payload

    def _next_command(self, payload: dict[str, Any]) -> str:
        implementation = payload.get("implementation_spec") or {}
        path = implementation.get("path", "<implementation_spec>")
        return (
            "python run_company_agents_demo.py --real "
            f"--task-file {path} --real-max-steps 260"
        )

    def _export_project_docs(
        self,
        payload: dict[str, Any],
        *,
        export_project_dir: str | Path,
    ) -> dict[str, Any]:
        project_dir = Path(export_project_dir)
        export_dir = project_dir / DOC_EXPORT_SUBDIR
        export_dir.mkdir(parents=True, exist_ok=True)

        copied: list[dict[str, Any]] = []
        artifacts = payload.get("artifacts", {})
        if isinstance(artifacts, dict):
            for key, ref in sorted(artifacts.items()):
                if not isinstance(ref, dict):
                    continue
                source = Path(str(ref.get("path", "")))
                if not source.is_absolute():
                    source = self.repo_root / source
                if not source.exists() or not source.is_file():
                    continue
                destination = export_dir / source.name
                shutil.copy2(source, destination)
                copied.append(
                    {
                        "artifact_key": key,
                        "artifact_kind": ref.get("kind"),
                        "title": ref.get("title"),
                        "source": str(source),
                        "path": str(destination),
                        "sha256": ref.get("sha256"),
                    }
                )

        manifest = {
            "run_id": payload.get("run_id"),
            "factory_version": payload.get("version", self.version),
            "source_artifact_dir": payload.get("artifact_dir"),
            "project_dir": str(project_dir),
            "export_dir": str(export_dir),
            "artifact_count": len(copied),
            "artifacts": copied,
        }
        manifest_path = export_dir / "artifact_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

        readme_path = export_dir / "README.md"
        readme_lines = [
            "# Software Factory Documentation",
            "",
            f"- Run ID: `{payload.get('run_id')}`",
            f"- Source artifact dir: `{payload.get('artifact_dir')}`",
            f"- Exported artifact count: `{len(copied)}`",
            "",
            "## Artifact Index",
            "",
            "| Key | Kind | File |",
            "|---|---|---|",
        ]
        for item in copied:
            readme_lines.append(
                f"| `{item['artifact_key']}` | `{item.get('artifact_kind')}` | `{Path(item['path']).name}` |"
            )
        readme_lines.extend(
            [
                "",
                "## Expected Flow",
                "",
                "Product Vision -> BRD -> PRD -> Epic/Story -> Acceptance Criteria -> "
                "Product Validator/Critic -> Domain -> Business Logic -> Technical -> "
                "Pattern -> Implementation Spec -> Code Handoff -> Docs Orchestrator -> "
                "Repo Scanner -> API Extractor -> ADR -> Docs Writer -> Docs Verifier -> Final",
                "",
                "The source of truth remains the factory run directory; this folder is a "
                "project-local mirror for product readers and downstream coding agents.",
                "",
            ]
        )
        readme_path.write_text("\n".join(readme_lines), encoding="utf-8")

        manifest["manifest_path"] = str(manifest_path)
        manifest["readme_path"] = str(readme_path)
        return manifest
