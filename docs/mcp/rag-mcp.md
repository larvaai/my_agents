# RAG MCP

## Purpose

RAG MCP ingest và search knowledge local trong workspace qua Qdrant.

## Server

- Server name: `rag`
- File: `mcp_servers/rag_server.py`
- Transport: stdio
- Storage: Qdrant
- Sandbox: `workspace/`

## Tools

| Tool | Dùng để |
|---|---|
| `rag.rag_health` | Kiểm Qdrant |
| `rag.rag_ingest` | Ingest `.md`, `.txt`, `.py` |
| `rag.rag_search` | Vector search |

## Required Flow

```text
rag_health -> rag_ingest optional -> rag_search -> verify source/score
```

Nếu `rag_health` fail, không gọi ingest/search. Báo dependency failure.

## Quality Gate

- Không dùng hit source sai.
- Không dùng hit score thấp.
- Nếu hits rỗng, báo thiếu context.
- Ingest lại khi source thay đổi.

## Test

```powershell
python run_all_cases.py --group rag --fail-fast
python run_all_cases.py --case chain_05_rag_health_gate_document_ledger --fail-fast
```

## Troubleshooting

```powershell
docker compose up -d qdrant
Invoke-RestMethod http://localhost:6333/collections
```

