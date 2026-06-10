# ADR-0002: Use Qdrant For Local RAG

## Status

Accepted

## Context

Agent cần truy xuất knowledge local từ notes/docs/code. Cần vector search chạy local, không phụ thuộc cloud mặc định.

## Decision

Dùng Qdrant làm vector database local, gọi qua `mcp_servers/rag_server.py`.

## Consequences

Ưu điểm:

- Local-first.
- Có Docker compose.
- Phù hợp cho notes/code/document chunks.
- Dễ reset collection khi test.

Nhược điểm:

- Cần Docker/Qdrant đang chạy.
- Vector hit không đảm bảo đúng nếu dữ liệu nghèo.
- Cần quality gate: source/score/context phải được kiểm tra.

## Quality Rule

RAG hit chỉ là candidate context. Agent phải kiểm source, score và nội dung trước khi dùng.

