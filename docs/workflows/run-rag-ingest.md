# Workflow: Run RAG Ingest

## Goal

Đưa knowledge local vào Qdrant để agent có thể search.

## Steps

1. Đảm bảo Qdrant chạy:

```powershell
docker compose up -d qdrant
```

2. Kiểm health:

```json
{
  "action": "tool",
  "tool": "rag.rag_health",
  "args": {}
}
```

3. Đặt source vào workspace, ví dụ:

```text
workspace/notes/my-note.md
```

4. Ingest:

```json
{
  "action": "tool",
  "tool": "rag.rag_ingest",
  "args": {
    "path": "notes/my-note.md"
  }
}
```

5. Search với threshold:

```json
{
  "action": "tool",
  "tool": "rag.rag_search",
  "args": {
    "query": "noi dung can tim",
    "top_k": 5,
    "score_threshold": 0.7
  }
}
```

## Quality Checklist

- Source đúng chưa?
- Score đủ cao chưa?
- Hit có chứa nội dung thật không?
- Có cần ingest lại sau khi sửa note không?

