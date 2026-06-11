from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.research_department.citation_agent import CitationAgent
from agents.research_department.pdf_text_extraction_agent import PDFTextExtractionAgent
from agents.research_department.search_agent import SearchAgent
from agents.research_department.source_reader_agent import SourceReaderAgent


@dataclass
class ResearchDepartment:
    """Stage-4 research department wrapper."""

    use_tools: bool = False

    def run(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        search = SearchAgent(use_tools=self.use_tools).run(question)
        search_sources = [
            {
                "title": item.get("title", ""),
                "url_or_path": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "source_type": "web",
                "relevance": "medium",
            }
            for item in search.get("results", [])
            if isinstance(item, dict)
        ]
        source_read = SourceReaderAgent(use_tools=self.use_tools).run(search_sources)
        pdf_extract = PDFTextExtractionAgent(use_tools=self.use_tools).run(context.get("document_path"))
        citations = CitationAgent().run(search_sources)

        claims = []
        if search_sources:
            claims.append("Research collected source candidates through Search MCP.")
        else:
            claims.append("Research route was selected, but deterministic mode did not collect external sources.")

        summary = (
            "Research Department prepared a source-backed answer scaffold."
            if search_sources
            else "Research Department is wired for Search, Fetch, PDF/Text Extraction, and Citation, but no external lookup ran in deterministic mode."
        )
        return {
            "department": "research",
            "summary": summary,
            "claims": claims,
            "sources": citations.get("sources", []),
            "citation_notes": citations.get("citation_notes", []),
            "limits": [
                "Research Department defaults to deterministic no-network mode unless use_tools=True.",
            ],
            "agent_outputs": {
                "search": search,
                "source_reader": source_read,
                "pdf_text_extraction": pdf_extract,
                "citation": citations,
            },
        }
