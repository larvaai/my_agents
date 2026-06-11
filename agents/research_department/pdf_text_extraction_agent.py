from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.tool_registry import call_tool


@dataclass
class PDFTextExtractionAgent:
    """Extracts local workspace PDF/text content through a dedicated MCP."""

    use_tools: bool = False
    max_chars: int = 12000

    def run(self, path: str | None) -> dict[str, Any]:
        if not path:
            return {
                "agent": "pdf_text_extraction_agent",
                "ok": True,
                "path": None,
                "text": "",
                "used_tool": None,
                "notes": ["No local PDF/text path was provided."],
            }

        if self.use_tools:
            result = call_tool(
                "pdf_text_extraction.extract_text",
                {"path": path, "max_chars": self.max_chars},
            )
            return {
                "agent": "pdf_text_extraction_agent",
                "ok": result.get("ok") is True,
                "path": path,
                "text": result.get("text", ""),
                "document_type": result.get("document_type"),
                "truncated": result.get("truncated"),
                "error": result.get("error"),
                "used_tool": "pdf_text_extraction.extract_text",
            }

        return {
            "agent": "pdf_text_extraction_agent",
            "ok": True,
            "path": path,
            "text": "",
            "used_tool": None,
            "notes": ["PDF/Text Extraction MCP is wired but not used in deterministic smoke mode."],
        }
