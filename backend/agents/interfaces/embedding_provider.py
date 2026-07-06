"""
Embedding Provider Interface — the single contract all Knowledge Engine
business logic depends on. Never import a concrete implementation
(MockEmbeddingProvider, OllamaEmbeddingProvider, ...) from services.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    model: str
    dims: int
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingProvider(ABC):
    """
    Interface for all embedding providers.
    Business logic depends ONLY on this class — never on implementations.
    """

    @abstractmethod
    async def embed(self, texts: list[str]) -> EmbeddingResult:
        """Embed a batch of texts and return their vectors (same order as input)."""
        ...

    async def embed_one(self, text: str) -> list[float]:
        """Convenience helper for embedding a single string."""
        result = await self.embed([text])
        return result.vectors[0] if result.vectors else []

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider endpoint is reachable."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable identifier, e.g. 'ollama/nomic-embed-text'."""
        ...

    @property
    @abstractmethod
    def dims(self) -> int:
        """Dimensionality of the vectors this provider produces."""
        ...
