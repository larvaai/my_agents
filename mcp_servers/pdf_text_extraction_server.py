from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR

from mcp.server.fastmcp import FastMCP


MAX_CHARS = 300_000

mcp = FastMCP(
    "pdf-text-extraction-server",
    instructions="Extract text from local workspace PDF and text-like files. Read-only.",
)


class ExtractionError(ValueError):
    pass


def _safe_workspace_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise ExtractionError(f"Path is outside workspace: {raw_path}")
    return resolved


def _strip_html(text: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:
        raise ExtractionError("PDF support requires pypdf.") from exc

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(path), "pdf"
    if suffix in {".txt", ".md", ".py", ".csv", ".tsv", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="replace"), "text"
    if suffix == ".json":
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            return json.dumps(json.loads(raw), ensure_ascii=False, indent=2), "json"
        except json.JSONDecodeError:
            return raw, "json"
    if suffix in {".html", ".htm"}:
        return _strip_html(path.read_text(encoding="utf-8", errors="replace")), "html"
    raise ExtractionError(f"Unsupported extension for PDF/Text Extraction MCP: {suffix}")


@mcp.tool()
def extract_text(path: str, max_chars: int = 20000) -> dict[str, Any]:
    """
    Extract text from a workspace PDF or text-like document.
    """
    try:
        file_path = _safe_workspace_path(path)
        if not file_path.exists():
            return {"ok": False, "tool": "extract_text", "path": path, "error": "File does not exist."}
        if not file_path.is_file():
            return {"ok": False, "tool": "extract_text", "path": path, "error": "Path is not a file."}

        text, document_type = _extract(file_path)
        max_chars = max(1, min(int(max_chars), MAX_CHARS))
        return {
            "ok": True,
            "tool": "extract_text",
            "path": path,
            "document_type": document_type,
            "chars": len(text),
            "text": text[:max_chars],
            "truncated": len(text) > max_chars,
        }
    except Exception as exc:
        return {"ok": False, "tool": "extract_text", "path": path, "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")

