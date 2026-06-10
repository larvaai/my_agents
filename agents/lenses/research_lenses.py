from __future__ import annotations

from agents.lenses.base_lens import LensSpec


RESEARCH_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="source_scout",
        department="research",
        purpose="Find candidate sources, search queries, official docs, papers, issues, and repos.",
        allowed_tools=("search.web_search", "fetch.fetch_url", "context7.*", "rag.rag_search", "code_index.*"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "source_scout",
            "queries": [],
            "candidate_sources": [],
            "recommended_fetch": [],
        },
    ),
    LensSpec(
        name="source_credibility",
        department="research",
        purpose="Score whether sources are official, current, trustworthy, or merely opinion/forum material.",
        allowed_tools=("fetch.fetch_url", "document.document_extract_text", "rag.rag_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "source_credibility",
            "accepted_sources": [],
            "rejected_sources": [],
            "credibility_notes": [],
        },
    ),
    LensSpec(
        name="fact_check",
        department="research",
        purpose="Compare claims across sources, find conflicts, and avoid conclusions from weak evidence.",
        allowed_tools=("fetch.fetch_url", "rag.rag_search", "document.document_extract_text"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "fact_check",
            "claims": [],
            "supported_claims": [],
            "conflicting_claims": [],
            "uncertain_claims": [],
        },
    ),
    LensSpec(
        name="synthesis",
        department="research",
        purpose="Turn long research material into compact usable context while preserving source references.",
        allowed_tools=("document.document_extract_text", "rag.rag_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "synthesis",
            "summary": "",
            "key_points": [],
            "actionable_knowledge": [],
            "sources": [],
        },
    ),
    LensSpec(
        name="knowledge_curator",
        department="research",
        purpose="Decide what is worth ingesting into durable knowledge and avoid noisy or stale notes.",
        allowed_tools=("rag.rag_search", "document.document_extract_text", "obsidian.obsidian_search_notes"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "knowledge_curator",
            "should_ingest": False,
            "note_path": "notes/research/...",
            "tags": [],
            "reason": "",
        },
    ),
)
