"""
Vector Store Provider Interface — abstracts similarity search over embedded
chunks. Business logic depends ONLY on this class — never on implementations
(InMemoryVectorStore, ChromaVectorStore, ...).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorRecord:
    id: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorMatch:
    id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStoreProvider(ABC):
    """Interface for all vector store providers (memory, chromadb, qdrant, ...)."""

    @abstractmethod
    async def upsert(self, namespace: str, records: list[VectorRecord]) -> None:
        """Insert or update vectors within a namespace (e.g. a collection id)."""
        ...

    @abstractmethod
    async def query(
        self, namespace: str, vector: list[float], top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        """Return the top_k most similar records to `vector` within a namespace."""
        ...

    @abstractmethod
    async def delete(self, namespace: str, ids: list[str]) -> None:
        """Remove specific vectors from a namespace."""
        ...

    @abstractmethod
    async def delete_namespace(self, namespace: str) -> None:
        """Remove an entire namespace (e.g. when a collection is deleted)."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
