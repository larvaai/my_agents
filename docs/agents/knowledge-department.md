# Knowledge Department

Stage 2 adds a read-only Knowledge Department for stable conceptual questions.

Current agents:

- `agents/knowledge/general_knowledge_agent/`
- `agents/knowledge/philosophy_agent/`

Rules:

- No file writes.
- No terminal execution.
- No Python execution.
- RAG can be added later behind the same output contract.
- If the answer needs current facts or citations, route to Research Department.

Output contract:

```json
{
  "department": "knowledge",
  "agent": "general_knowledge_agent",
  "answer_draft": "...",
  "confidence": "low | medium | high",
  "needs_research": false,
  "sources": [],
  "limits": []
}
```
