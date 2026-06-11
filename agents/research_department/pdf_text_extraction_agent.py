from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.capabilities import call_tool
from core.schemas import capability_data


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
            data = capability_data(result)
            return {
                "agent": "pdf_text_extraction_agent",
                "ok": result.get("ok") is True,
                "path": path,
                "text": data.get("text", ""),
                "document_type": data.get("document_type"),
                "truncated": data.get("truncated"),
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
