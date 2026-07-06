"""
ChromaVectorStore — optional persistent vector store backed by chromadb.

Only imported/instantiated when VECTOR_DB_PROVIDER=chromadb. If the
`chromadb` package is not installed, raises a clear ProviderError at
construction time so provider_factory can be extended safely without
breaking the default (memory) path.
"""
from __future__ import annotations

from typing import Any

from agents.interfaces.vector_store_provider import (
    VectorMatch,
    VectorRecord,
    VectorStoreProvider,
)
from packages.core.exceptions import ProviderError


class ChromaVectorStore(VectorStoreProvider):
    def __init__(self, persist_directory: str = "./chroma_data") -> None:
        try:
            import chromadb
        except ImportError as e:
            raise ProviderError(
                "chromadb",
                "chromadb package is not installed. Install it or set "
                "VECTOR_DB_PROVIDER=memory.",
            ) from e
        self._client = chromadb.PersistentClient(path=persist_directory)

    @property
    def provider_name(self) -> str:
        return "chromadb"

    async def is_available(self) -> bool:
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False

    def _collection(self, namespace: str):
        return self._client.get_or_create_collection(name=f"kn_{namespace}")

    async def upsert(self, namespace: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        col = self._collection(namespace)
        col.upsert(
            ids=[r.id for r in records],
            embeddings=[r.vector for r in records],
            metadatas=[r.metadata or {} for r in records],
        )

    async def query(
        self, namespace: str, vector: list[float], top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        col = self._collection(namespace)
        result = col.query(
            query_embeddings=[vector], n_results=top_k,
            where=filters or None,
        )
        matches: list[VectorMatch] = []
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        for id_, dist, meta in zip(ids, distances, metadatas):
            score = 1.0 - dist  # chroma default distance is cosine distance
            matches.append(VectorMatch(id=id_, score=score, metadata=meta or {}))
        return matches

    async def delete(self, namespace: str, ids: list[str]) -> None:
        if not ids:
            return
        self._collection(namespace).delete(ids=ids)

    async def delete_namespace(self, namespace: str) -> None:
        try:
            self._client.delete_collection(name=f"kn_{namespace}")
        except Exception:
            pass
