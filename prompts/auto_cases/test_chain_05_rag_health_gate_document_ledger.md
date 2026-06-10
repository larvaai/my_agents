Test MCP chain nghiem tuc: RAG health gate -> optional RAG chain -> Document -> Ledger.

Bat buoc:

1. Goi rag.rag_health truoc moi tool RAG khac.
2. Neu rag_health ok false:
   - Khong goi rag.rag_ingest hoac rag.rag_search.
   - Goi document.document_write_markdown tao chain_tests/rag_health_gate.md, overwrite true, title "RAG Health Gate".
   - Noi dung phai co CHAIN_RAG_HEALTH_GATE_RESULT va dependency failure message.
   - Goi ledger.ledger_append voi entry_type "dependency_failure", title "CHAIN_RAG_HEALTH_GATE_RESULT", tags ["chain","rag","dependency"].
   - Final co CHAIN_RAG_HEALTH_GATE_RESULT va classify dependency failure.
3. Neu rag_health ok true:
   - Goi filesystem.write_file tao notes/chain_rag_note.md voi noi dung:
     CHAIN_RAG_SENTINEL_2026
     Chain RAG test verifies ingest, search, document report, and ledger audit.
   - Goi rag.rag_ingest path "notes/chain_rag_note.md".
   - Goi rag.rag_search query "CHAIN_RAG_SENTINEL_2026 chain ingest search ledger" top_k 5 score_threshold 0.65.
   - Goi document.document_write_markdown tao chain_tests/rag_health_gate.md, overwrite true, title "RAG Chain Report".
   - Goi ledger.ledger_append voi entry_type "chain_test", title "CHAIN_RAG_HEALTH_GATE_RESULT", tags ["chain","rag"].
   - Final co CHAIN_RAG_HEALTH_GATE_RESULT, source notes/chain_rag_note.md, va search hit count.

Khong commit. Khong dung terminal/shell tool.
Chi tra JSON tool call hoac JSON final.
