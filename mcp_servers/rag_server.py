from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR

from fastembed import TextEmbedding
from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "my_agents_rag")

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "intfloat/multilingual-e5-large",
)

CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))

SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
}

mcp = FastMCP(
    "rag-server",
    instructions=(
        "RAG tools for ingesting workspace files into Qdrant and searching "
        "relevant chunks. All file access is sandboxed to the project workspace."
    ),
)


class RAGServerError(ValueError):
    pass


_embedder: TextEmbedding | None = None
_client: QdrantClient | None = None
_vector_size: int | None = None


def _safe_workspace_path(raw_path: str) -> Path:
    path = Path(raw_path)

    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()

    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise RAGServerError(f"Path is outside workspace: {raw_path}")

    return resolved


def _get_embedder() -> TextEmbedding:
    global _embedder

    if _embedder is None:
        _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)

    return _embedder


def _get_client() -> QdrantClient:
    global _client

    if _client is None:
        _client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

    return _client


def _qdrant_status() -> dict[str, Any]:
    try:
        collections = _get_client().get_collections().collections
        collection_names = [collection.name for collection in collections]

        return {
            "ok": True,
            "dependency": "qdrant",
            "qdrant_url": QDRANT_URL,
            "collection": QDRANT_COLLECTION,
            "collection_exists": QDRANT_COLLECTION in collection_names,
            "collections": collection_names,
        }
    except Exception as exc:
        return {
            "ok": False,
            "dependency": "qdrant",
            "dependency_failure": True,
            "qdrant_url": QDRANT_URL,
            "collection": QDRANT_COLLECTION,
            "error": str(exc),
        }


def _embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_embedder()
    vectors = list(model.embed(texts))
    return [vector.tolist() for vector in vectors]


def _embed_documents(chunks: list[str]) -> list[list[float]]:
    passages = [f"passage: {chunk}" for chunk in chunks]
    return _embed_texts(passages)


def _embed_query(query: str) -> list[float]:
    vectors = _embed_texts([f"query: {query}"])
    return vectors[0]


def _get_vector_size() -> int:
    global _vector_size

    if _vector_size is None:
        test_vector = _embed_query("dimension check")
        _vector_size = len(test_vector)

    return _vector_size


def _ensure_collection() -> None:
    client = _get_client()
    existing = client.get_collections().collections
    names = {collection.name for collection in existing}

    if QDRANT_COLLECTION not in names:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=_get_vector_size(),
                distance=Distance.COSINE,
            ),
        )


def _chunk_text(text: str) -> list[str]:
    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        next_start = end - CHUNK_OVERLAP

        if next_start <= start:
            break

        start = next_start

    return chunks


def _stable_point_id(source: str, chunk_index: int, content: str) -> str:
    raw = f"{source}:{chunk_index}:{content[:200]}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def _relative_source(path: Path) -> str:
    return str(path.resolve().relative_to(WORKSPACE_DIR.resolve())).replace("\\", "/")


def _delete_existing_source(source: str) -> None:
    client = _get_client()

    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source),
                )
            ]
        ),
        wait=True,
    )


def _collect_files(root_path: Path) -> list[Path]:
    if root_path.is_file():
        if root_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [root_path]
        return []

    files = []

    for path in root_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return sorted(files)


def _ingest_file(file_path: Path) -> dict[str, Any]:
    _ensure_collection()

    source = _relative_source(file_path)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    chunks = _chunk_text(text)

    if not chunks:
        return {
            "ok": False,
            "source": source,
            "error": "File is empty or could not be chunked.",
        }

    embeddings = _embed_documents(chunks)

    _delete_existing_source(source)

    points = []

    for index, chunk in enumerate(chunks):
        points.append(
            PointStruct(
                id=_stable_point_id(source, index, chunk),
                vector=embeddings[index],
                payload={
                    "content": chunk,
                    "source": source,
                    "file_name": file_path.name,
                    "chunk_index": index,
                },
            )
        )

    client = _get_client()

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points,
        wait=True,
    )

    return {
        "ok": True,
        "source": source,
        "chunks": len(chunks),
    }


@mcp.tool()
def rag_health() -> dict[str, Any]:
    """
    Check whether the Qdrant dependency is reachable before RAG ingest/search.
    """
    status = _qdrant_status()
    status["tool"] = "rag_health"
    status["embedding_model"] = EMBEDDING_MODEL
    return status


@mcp.tool()
def rag_ingest(path: str = ".") -> dict[str, Any]:
    """
    Ingest .md, .txt, and .py files from the workspace into Qdrant.

    Args:
        path: Relative path inside workspace. Example: ".", "notes", "code/test.py".
    """
    try:
        root_path = _safe_workspace_path(path)
        files = _collect_files(root_path)
        health = _qdrant_status()

        if not health["ok"]:
            return {
                "ok": False,
                "tool": "rag_ingest",
                "path": path,
                "error": health["error"],
                "dependency": health["dependency"],
                "dependency_failure": True,
                "qdrant_url": health["qdrant_url"],
                "files_count": len(files),
                "results": [],
            }

        results = []

        for file_path in files:
            try:
                results.append(_ingest_file(file_path))
            except Exception as exc:
                results.append(
                    {
                        "ok": False,
                        "source": _relative_source(file_path),
                        "error": str(exc),
                    }
                )

        return {
            "ok": True,
            "tool": "rag_ingest",
            "path": path,
            "files_count": len(files),
            "results": results,
        }

    except Exception as exc:
        return {
            "ok": False,
            "tool": "rag_ingest",
            "path": path,
            "error": str(exc),
            "files_count": 0,
            "results": [],
        }


@mcp.tool()
def rag_search(query: str, top_k: int = 5, score_threshold: float = 0.80) -> dict[str, Any]:
    """
    Search relevant chunks from Qdrant.

    Args:
        query: Search query.
        top_k: Number of chunks to return. Min 1, max 20.
    """
    try:
        if not query or not query.strip():
            return {
                "ok": False,
                "tool": "rag_search",
                "error": "Query is empty.",
                "hits": [],
            }

        health = _qdrant_status()

        if not health["ok"]:
            return {
                "ok": False,
                "tool": "rag_search",
                "query": query,
                "error": health["error"],
                "dependency": health["dependency"],
                "dependency_failure": True,
                "qdrant_url": health["qdrant_url"],
                "hits": [],
            }

        _ensure_collection()

        top_k = max(1, min(int(top_k), 20))
        query_vector = _embed_query(query)

        client = _get_client()

        if hasattr(client, "query_points"):
            result = client.query_points(
                collection_name=QDRANT_COLLECTION,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            points = result.points
        else:
            points = client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )

        hits = []

        for point in points:
            if point.score < score_threshold:
                continue

            payload = point.payload or {}

            hits.append(
                {
                    "score": point.score,
                    "source": payload.get("source", ""),
                    "file_name": payload.get("file_name", ""),
                    "chunk_index": payload.get("chunk_index", -1),
                    "content": payload.get("content", ""),
                }
            )

        return {
            "ok": True,
            "tool": "rag_search",
            "query": query,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "hits": hits,
        }

    except Exception as exc:
        return {
            "ok": False,
            "tool": "rag_search",
            "query": query,
            "error": str(exc),
            "hits": [],
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")

