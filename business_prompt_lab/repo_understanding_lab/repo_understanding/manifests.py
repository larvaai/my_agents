from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any


FRAMEWORK_HINTS = {
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "langgraph": "langgraph",
    "langchain": "langchain",
    "pytest": "pytest",
    "react": "react",
    "next": "nextjs",
    "vite": "vite",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_requirements(path: Path) -> list[str]:
    dependencies: list[str] = []
    for line in read_text(path).splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        dependencies.append(cleaned.split(";")[0].strip())
    return dependencies


def read_pyproject(path: Path) -> tuple[list[str], dict[str, Any]]:
    data = tomllib.loads(read_text(path))
    dependencies = list(data.get("project", {}).get("dependencies", []))
    optional = data.get("project", {}).get("optional-dependencies", {})
    for values in optional.values():
        dependencies.extend(values)
    scripts = data.get("project", {}).get("scripts", {})
    return dependencies, {"scripts": scripts, "tool": list(data.get("tool", {}).keys())}


def read_package_json(path: Path) -> tuple[list[str], dict[str, Any]]:
    data = json.loads(read_text(path))
    dependencies = []
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        dependencies.extend(data.get(key, {}).keys())
    return dependencies, {"scripts": data.get("scripts", {})}


def detect_frameworks(dependencies: list[str]) -> list[str]:
    frameworks = set()
    lowered = " ".join(dependencies).lower()
    for hint, framework in FRAMEWORK_HINTS.items():
        if hint in lowered:
            frameworks.add(framework)
    return sorted(frameworks)


def read_manifests(repo_path: Path, file_map: list[dict[str, Any]]) -> dict[str, Any]:
    languages = sorted({node["language"] for node in file_map if node["language"] != "unknown"})
    manifests: list[dict[str, Any]] = []
    dependencies: list[str] = []
    scripts: dict[str, Any] = {}
    parse_errors: list[dict[str, str]] = []

    for node in file_map:
        if node["role"] != "manifest":
            continue
        rel_path = Path(node["path"])
        path = repo_path / rel_path
        name = rel_path.name.lower()
        try:
            if name == "requirements.txt":
                deps = read_requirements(path)
                dependencies.extend(deps)
                manifests.append({"path": node["path"], "kind": "python_requirements", "dependency_count": len(deps)})
            elif name == "pyproject.toml":
                deps, metadata = read_pyproject(path)
                dependencies.extend(deps)
                scripts.update(metadata.get("scripts", {}))
                manifests.append({"path": node["path"], "kind": "pyproject", **metadata})
            elif name == "package.json":
                deps, metadata = read_package_json(path)
                dependencies.extend(deps)
                scripts.update(metadata.get("scripts", {}))
                manifests.append({"path": node["path"], "kind": "package_json", **metadata})
            else:
                manifests.append({"path": node["path"], "kind": name})
        except Exception as exc:  # pragma: no cover - exact parser errors vary
            parse_errors.append({"path": node["path"], "error": str(exc)})

    entrypoints = [
        node["path"]
        for node in file_map
        if node["role"] == "entrypoint" or node["path"] in {"main.py", "app.py"}
    ]

    package_managers = []
    manifest_paths = {manifest["path"] for manifest in manifests}
    if "requirements.txt" in manifest_paths or "pyproject.toml" in manifest_paths:
        package_managers.append("pip")
    if "package.json" in manifest_paths:
        package_managers.append("npm")

    return {
        "repo_path": str(repo_path),
        "languages": languages,
        "frameworks": detect_frameworks(dependencies),
        "package_managers": sorted(package_managers),
        "dependencies": sorted(set(dependencies)),
        "manifests": manifests,
        "scripts": scripts,
        "entrypoints": sorted(entrypoints),
        "parse_errors": parse_errors,
        "confidence": 0.75 if manifests else 0.45,
    }

