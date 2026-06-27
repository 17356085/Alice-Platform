"""Redis Stack Vector Search — alternative to ChromaDB for RAG.

P6 (2026-06-25): Redis Stack provides built-in vector search via RediSearch module.
ChromaDB remains as fallback. Switch requires redis-stack Docker image.

Docker:
  docker run -d --name tlo-redis-stack -p 6379:6379 redis/redis-stack-server:latest

Usage:
  from aitest.knowledge.redis_vector import RedisVectorStore
  store = RedisVectorStore("known_issues")
  store.add("doc-1", "How to fix modal dialog...", embedding=[0.1, 0.2, ...])
  results = store.search("dialog not closing", k=5)

If Redis Stack is unavailable, returns empty — ChromaDB handles the query.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger("redis_vector")

_REDIS_AVAILABLE = False
_REDIS_STACK_AVAILABLE = False

try:
    import redis as _redis

    r_test = _redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
    r_test.ping()
    _REDIS_AVAILABLE = True

    # Check for RediSearch module (Redis Stack)
    modules = [m[b"name"].decode() for m in r_test.execute_command("MODULE", "LIST")]
    if "search" in modules:
        _REDIS_STACK_AVAILABLE = True
        logger.info("redis_stack_detected", modules=modules)
except Exception:
    pass


class RedisVectorStore:
    """Redis Stack vector search store. ChromaDB-compatible interface.

    Indexes in Redis with HNSW algorithm. Queries via KNN.
    """

    def __init__(self, collection_name: str, vector_dim: int = 768,
                 prefix: str = "tlo:vec"):
        self._name = collection_name
        self._dim = vector_dim
        self._prefix = f"{prefix}:{collection_name}"
        self._redis: Optional[_redis.Redis] = None
        self._ready = False

        if _REDIS_STACK_AVAILABLE:
            try:
                self._redis = _redis.Redis(
                    host="localhost", port=6379, socket_connect_timeout=2)
                self._ensure_index()
                self._ready = True
                logger.info("redis_vector_ready", collection=collection_name,
                            dim=vector_dim)
            except Exception as e:
                logger.warning("redis_vector_unavailable", error=str(e)[:100])

    @property
    def is_ready(self) -> bool:
        return self._ready

    def _ensure_index(self):
        """Create HNSW index if not exists."""
        idx_name = f"{self._prefix}:idx"
        try:
            self._redis.ft(idx_name).info()
        except Exception:
            # Create index
            from redis.commands.search.field import VectorField, TextField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType

            schema = (
                TextField("$.content", as_name="content"),
                VectorField("$.embedding", "HNSW", {
                    "TYPE": "FLOAT32",
                    "DIM": self._dim,
                    "DISTANCE_METRIC": "COSINE",
                }, as_name="embedding"),
            )
            definition = IndexDefinition(
                prefix=[f"{self._prefix}:doc:"], index_type=IndexType.JSON)
            self._redis.ft(idx_name).create_index(
                schema, definition=definition)

    def _doc_key(self, doc_id: str) -> str:
        return f"{self._prefix}:doc:{doc_id}"

    def add(self, doc_id: str, content: str, embedding: list[float],
            metadata: dict = None):
        """Add a document with its embedding vector."""
        if not self._ready:
            return
        doc = {
            "content": content,
            "embedding": embedding,
            "metadata": json.dumps(metadata or {}),
        }
        self._redis.json().set(self._doc_key(doc_id), "$", doc)

    def search(self, query_embedding: list[float], k: int = 5) -> list[dict]:
        """KNN search. Returns top-k results with content + metadata."""
        if not self._ready:
            return []

        from redis.commands.search.query import Query

        q = (
            Query(f"*=>[KNN {k} @embedding $vec AS score]")
            .sort_by("score")
            .return_fields("content", "metadata", "score")
            .dialect(2)
        )
        try:
            results = self._redis.ft(f"{self._prefix}:idx").search(
                q, query_params={"vec": _vector_bytes(query_embedding)})
            return [
                {
                    "id": doc.id.replace(f"{self._prefix}:doc:", ""),
                    "content": doc.content,
                    "metadata": json.loads(doc.metadata) if doc.metadata else {},
                    "score": float(doc.score) if hasattr(doc, 'score') else 0.0,
                }
                for doc in results.docs
            ]
        except Exception:
            return []

    def count(self) -> int:
        if not self._ready:
            return 0
        try:
            return self._redis.ft(f"{self._prefix}:idx").info().get("num_docs", 0)
        except Exception:
            return 0

    def delete(self, doc_id: str):
        if self._ready:
            self._redis.delete(self._doc_key(doc_id))

    def clear(self):
        if self._ready:
            keys = self._redis.keys(f"{self._prefix}:doc:*")
            if keys:
                self._redis.delete(*keys)
            try:
                self._redis.ft(f"{self._prefix}:idx").dropindex(delete_documents=True)
            except Exception:
                pass

    def stats(self) -> dict:
        if not self._ready:
            return {"backend": "redis_stack", "status": "unavailable"}
        return {
            "backend": "redis_stack",
            "collection": self._name,
            "dim": self._dim,
            "doc_count": self.count(),
        }


def _vector_bytes(vec: list[float]) -> bytes:
    """Convert float list to FLOAT32 byte representation."""
    import struct
    return b"".join(struct.pack("f", v) for v in vec)


# ── Async version (for ChromaDB drop-in) ──────────────────────────────

class RedisVectorStoreClient:
    """Thin wrapper mimicking ChromaDB client interface.

    Usage (drop-in):
        from aitest.knowledge.redis_vector import get_redis_vector_client
        client = get_redis_vector_client()
        if client.is_ready:
            results = client.search("known_issues", embedding, k=5)
        else:
            results = chroma_client.search("known_issues", embedding, k=5)
    """

    def __init__(self):
        self._stores: dict[str, RedisVectorStore] = {}
        self._ready = _REDIS_STACK_AVAILABLE

    @property
    def is_ready(self) -> bool:
        return self._ready

    def get_or_create(self, name: str, dim: int = 768) -> RedisVectorStore:
        if name not in self._stores:
            self._stores[name] = RedisVectorStore(name, vector_dim=dim)
        return self._stores[name]

    def stats(self) -> dict:
        return {
            "backend": "redis_stack" if self._ready else "unavailable",
            "collections": {
                name: store.stats() for name, store in self._stores.items()
            },
        }


redis_vector_client = RedisVectorStoreClient()
