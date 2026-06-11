# RAG System

## RAG Dùng Để Làm Gì?

RAG giúp agent tìm lại tri thức trong workspace: notes, docs, code, quyết định kỹ thuật. RAG không thay thế đọc source file khi cần chỉnh code chính xác.

## Stack

- MCP server: `mcp_servers/rag_server.py`
- Vector DB: Qdrant
- Embedding: FastEmbed
- Collection mặc định: `my_agents_rag`
- Workspace sandbox: `var/workspace/`

## Tools

- `rag.rag_health`
- `rag.rag_ingest`
- `rag.rag_search`

## Quy Trình Đúng

1. Đặt source vào `var/workspace/notes`, `var/workspace/code`, hoặc docs phù hợp.
2. Gọi `rag.rag_health`.
3. Nếu health fail, dừng và báo dependency failure.
4. Gọi `rag.rag_ingest` với path cụ thể.
5. Gọi `rag.rag_search` với query rõ và threshold phù hợp.
6. Kiểm tra source, score, nội dung trước khi dùng.

Ví dụ:

```json
{
  "action": "tool",
  "tool": "rag.rag_search",
  "args": {
    "query": "finish gate validation policy",
    "top_k": 5,
    "score_threshold": 0.7
  }
}
```

## Quality Gate

RAG hit không tự động đúng. Agent phải:

- Bỏ hit có source không liên quan.
- Bỏ hit score thấp.
- Không bịa khi hits rỗng.
- Báo thiếu context nếu RAG không đủ dữ liệu.
- Ingest lại khi source đã thay đổi.

## Env

| Env | Mặc định |
|---|---|
| `QDRANT_URL` | `http://localhost:6333` |
| `QDRANT_COLLECTION` | `my_agents_rag` |
| `EMBEDDING_MODEL` | tùy config server |
| `RAG_CHUNK_SIZE` | tùy config server |
| `RAG_CHUNK_OVERLAP` | tùy config server |

## Test

```powershell
python run_all_cases.py --group rag --fail-fast
python run_mcp_chain_smoke.py
```

## Anti-patterns

- Search trước khi health.
- Dùng RAG hit không đọc source.
- Ingest cả `.env`, secret, data rác.
- Dùng threshold quá thấp rồi coi mọi hit là đúng.
