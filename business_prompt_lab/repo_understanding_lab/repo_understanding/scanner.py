from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .io_utils import sha256_file


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "agent_runs",
    "dist",
    "fixtures",
    "build",
    "node_modules",
    "OpenHands",
    "openhands-workspace",
    "qdrant_storage",
    "test_runs",
    "var",
    "venv",
}

BINARY_EXTENSIONS = {
    ".db",
    ".dll",
    ".exe",
    ".ico",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".webp",
    ".zip",
}

LANGUAGE_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".txt": "text",
    ".ps1": "powershell",
    ".sh": "shell",
}

MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "poetry.lock",
    "uv.lock",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "dockerfile",
    "docker-compose.yml",
}


def to_posix(path: Path) -> str:
    return path.as_posix()


def guess_language(path: Path) -> str:
    return LANGUAGE_BY_EXT.get(path.suffix.lower(), "unknown")


def is_generated(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        "__pycache__" in parts
        or name.endswith(".min.js")
        or name.endswith(".generated.py")
        or name.endswith(".lock")
    )


def guess_role(rel_path: Path) -> str:
    name = rel_path.name
    lower_name = name.lower()
    lower_parts = [part.lower() for part in rel_path.parts]
    is_root_file = len(rel_path.parts) == 1
    if lower_name in MANIFEST_NAMES:
        return "manifest"
    if is_root_file and lower_name in {"agent_room.py", "run.py", "talk.ps1", "run.ps1"}:
        return "entrypoint"
    if lower_name in {"readme.md", "contributing.md", "changelog.md"}:
        return "docs"
    if is_root_file and rel_path.suffix.lower() == ".md":
        return "docs"
    if "docs" in lower_parts or "adr" in lower_parts:
        return "docs"
    if "tests" in lower_parts or lower_name.startswith("test_") or lower_name.endswith("_test.py"):
        return "test"
    if lower_name.startswith(".env") or "config" in lower_parts or rel_path.suffix.lower() in {".yaml", ".yml", ".toml"}:
        return "config"
    if lower_name in {"main.py", "app.py", "server.py"}:
        return "entrypoint"
    if rel_path.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx"}:
        return "source"
    return "asset"


def scan_repo(repo_path: Path, limit_files: int | None = None) -> list[dict[str, Any]]:
    repo_path = repo_path.resolve()
    files: list[dict[str, Any]] = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = sorted(directory for directory in dirs if directory not in IGNORE_DIRS)
        root_path = Path(root)
        for filename in sorted(filenames):
            path = root_path / filename
            rel_path = path.relative_to(repo_path)
            if rel_path.suffix.lower() in BINARY_EXTENSIONS:
                continue
            if is_generated(rel_path):
                continue
            stat = path.stat()
            node = {
                "id": f"file:{to_posix(rel_path)}",
                "path": to_posix(rel_path),
                "language": guess_language(rel_path),
                "role": guess_role(rel_path),
                "size_bytes": stat.st_size,
                "hash": sha256_file(path),
                "is_test": guess_role(rel_path) == "test",
                "is_generated": False,
            }
            files.append(node)
            if limit_files is not None and len(files) >= limit_files:
                return files
    return files
