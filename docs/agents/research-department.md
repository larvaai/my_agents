# Research Department

Stage 4 adds a research path for current, external, paper, PDF, and
citation-heavy work.

Current files:

```text
agents/research_department/search_agent.py
agents/research_department/source_reader_agent.py
agents/research_department/pdf_text_extraction_agent.py
agents/research_department/citation_agent.py
agents/research_department/department.py
```

Tool wiring:

- `search.web_search`
- `fetch.fetch_url`
- `pdf_text_extraction.extract_text`

The deterministic smoke mode does not call network tools. Set `use_tools=True`
in `ResearchDepartment` when a caller intentionally wants MCP-backed research.

Output contract:

```json
{
  "department": "research",
  "claims": [],
  "sources": [],
  "citation_notes": [],
  "limits": []
}
```
