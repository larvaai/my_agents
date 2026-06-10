from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
MAX_DOCUMENT_CHARS = 300_000

mcp = FastMCP(
    "document-server",
    instructions=(
        "Read and write document-like files inside the workspace. Supports text, "
        "Markdown, JSON, CSV, HTML, and optionally PDF/DOCX when dependencies exist."
    ),
)


class DocumentError(ValueError):
    pass


def _safe_workspace_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise DocumentError(f"Path is outside workspace: {raw_path}")

    return resolved


def _strip_html(text: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _read_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except Exception as exc:
        raise DocumentError("DOCX support requires python-docx.") from exc

    document = docx.Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:
        raise DocumentError("PDF support requires pypdf.") from exc

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".py", ".csv", ".tsv", ".json", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".json":
            try:
                parsed = json.loads(text)
                text = json.dumps(parsed, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        return text, "text"
    if suffix in {".html", ".htm"}:
        return _strip_html(path.read_text(encoding="utf-8", errors="replace")), "html"
    if suffix == ".docx":
        return _read_docx(path), "docx"
    if suffix == ".pdf":
        return _read_pdf(path), "pdf"
    raise DocumentError(f"Unsupported document extension: {suffix}")


@mcp.tool()
def document_extract_text(path: str, max_chars: int = 20000) -> dict[str, Any]:
    """
    Extract readable text from a workspace document.
    """
    try:
        file_path = _safe_workspace_path(path)
        if not file_path.exists():
            return {"ok": False, "tool": "document_extract_text", "error": "File does not exist.", "path": path}
        if not file_path.is_file():
            return {"ok": False, "tool": "document_extract_text", "error": "Path is not a file.", "path": path}

        text, document_type = _extract_text(file_path)
        max_chars = max(1, min(int(max_chars), MAX_DOCUMENT_CHARS))
        return {
            "ok": True,
            "tool": "document_extract_text",
            "path": path,
            "document_type": document_type,
            "chars": len(text),
            "text": text[:max_chars],
            "truncated": len(text) > max_chars,
        }
    except Exception as exc:
        return {"ok": False, "tool": "document_extract_text", "path": path, "error": str(exc)}


@mcp.tool()
def document_write_markdown(path: str, title: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    """
    Write a Markdown document inside the workspace.
    """
    try:
        file_path = _safe_workspace_path(path)
        if file_path.suffix.lower() not in {".md", ".txt"}:
            return {"ok": False, "tool": "document_write_markdown", "error": "Only .md and .txt outputs are allowed.", "path": path}
        if file_path.exists() and not overwrite:
            return {"ok": False, "tool": "document_write_markdown", "error": "File exists and overwrite is false.", "path": path}

        file_path.parent.mkdir(parents=True, exist_ok=True)
        text = f"# {title.strip()}\n\n{content.strip()}\n"
        file_path.write_text(text, encoding="utf-8")
        return {
            "ok": True,
            "tool": "document_write_markdown",
            "path": path,
            "chars": len(text),
        }
    except Exception as exc:
        return {"ok": False, "tool": "document_write_markdown", "path": path, "error": str(exc)}


@mcp.tool()
def document_append_section(path: str, heading: str, content: str) -> dict[str, Any]:
    """
    Append a section to a Markdown/text document in the workspace.
    """
    try:
        file_path = _safe_workspace_path(path)
        if file_path.suffix.lower() not in {".md", ".txt"}:
            return {"ok": False, "tool": "document_append_section", "error": "Only .md and .txt outputs are allowed.", "path": path}

        file_path.parent.mkdir(parents=True, exist_ok=True)
        section = f"\n\n## {heading.strip()}\n\n{content.strip()}\n"
        with file_path.open("a", encoding="utf-8") as file:
            file.write(section)
        return {"ok": True, "tool": "document_append_section", "path": path, "chars_appended": len(section)}
    except Exception as exc:
        return {"ok": False, "tool": "document_append_section", "path": path, "error": str(exc)}


@mcp.tool()
def document_outline(path: str, max_items: int = 100) -> dict[str, Any]:
    """
    Return Markdown-style headings or first non-empty lines as an outline.
    """
    try:
        file_path = _safe_workspace_path(path)
        text, document_type = _extract_text(file_path)
        max_items = max(1, min(int(max_items), 200))
        headings = []
        for line_number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped:
                continue
            markdown = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if markdown:
                headings.append(
                    {
                        "line": line_number,
                        "level": len(markdown.group(1)),
                        "text": markdown.group(2),
                    }
                )
            elif not headings and len(headings) < 10:
                headings.append({"line": line_number, "level": 0, "text": stripped[:160]})
            if len(headings) >= max_items:
                break

        return {
            "ok": True,
            "tool": "document_outline",
            "path": path,
            "document_type": document_type,
            "items": headings,
        }
    except Exception as exc:
        return {"ok": False, "tool": "document_outline", "path": path, "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
