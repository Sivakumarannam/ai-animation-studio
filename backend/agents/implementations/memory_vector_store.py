"""
InMemoryVectorStore — zero-dependency vector store backed by pure Python.
Default provider; always available regardless of external services.

Note: this store is process-local and non-persistent. It is rebuilt from
the `kn_chunks.embedding` JSON column on demand by the retrieval service,
so restarting the process never loses data — it just needs to re-hydrate.
"""
from __future__ import annotations

import math
import threading
from typing import Any

from agents.interfaces.vector_store_provider import (
    VectorMatch,
    VectorRecord,
    VectorStoreProvider,
)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(VectorStoreProvider):
    def __init__(self) -> None:
        self._data: dict[str, dict[str, VectorRecord]] = {}
        self._lock = threading.Lock()

    @property
    def provider_name(self) -> str:
        return "memory/cosine"

    async def is_available(self) -> bool:
        return True

    async def upsert(self, namespace: str, records: list[VectorRecord]) -> None:
        with self._lock:
            bucket = self._data.setdefault(namespace, {})
            for record in records:
                bucket[record.id] = record

    async def query(
        self, namespace: str, vector: list[float], top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        with self._lock:
            bucket = dict(self._data.get(namespace, {}))

        scored: list[VectorMatch] = []
        for record in bucket.values():
            if filters and not all(record.metadata.get(k) == v for k, v in filters.items()):
                continue
            score = _cosine_similarity(vector, record.vector)
            scored.append(VectorMatch(id=record.id, score=score, metadata=record.metadata))

        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:top_k]

    async def delete(self, namespace: str, ids: list[str]) -> None:
        with self._lock:
            bucket = self._data.get(namespace)
            if not bucket:
                return
            for id_ in ids:
                bucket.pop(id_, None)

    async def delete_namespace(self, namespace: str) -> None:
        with self._lock:
            self._data.pop(namespace, None)
