# PDF/Text Extraction MCP

Read-only MCP server:

```text
mcp_servers/pdf_text_extraction_server.py
```

Registered server:

```text
pdf_text_extraction
```

Tool:

```text
pdf_text_extraction.extract_text
```

Args:

```json
{
  "path": "workspace-relative PDF/text path",
  "max_chars": 20000
}
```

Supported inputs:

- `.pdf`
- `.txt`
- `.md`
- `.py`
- `.csv`
- `.tsv`
- `.json`
- `.yaml`
- `.yml`
- `.html`
- `.htm`

Safety:

- Read-only.
- Workspace-bound.
- No network.
- No file writes.
