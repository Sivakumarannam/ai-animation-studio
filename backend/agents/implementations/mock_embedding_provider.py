"""
MockEmbeddingProvider — deterministic, zero-dependency embedding provider
for development and testing. No network calls, no API keys required.

Vectors are generated via a hashing trick (bag-of-character-ngrams hashed
into fixed-size buckets, then L2-normalized) so that:
  - The same text always produces the same vector (deterministic).
  - Similar texts (sharing substrings/words) produce vectors with higher
    cosine similarity than unrelated texts — good enough for tests and
    offline development without any external AI dependency.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any

from agents.interfaces.embedding_provider import EmbeddingProvider, EmbeddingResult

_MOCK_MODEL = "mock/hash-embed-v1"
_DEFAULT_DIMS = 256


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dims: int = _DEFAULT_DIMS) -> None:
        self._dims = dims

    @property
    def provider_name(self) -> str:
        return _MOCK_MODEL

    @property
    def dims(self) -> int:
        return self._dims

    async def is_available(self) -> bool:
        return True

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        vectors = [self._embed_one(t) for t in texts]
        return EmbeddingResult(
            vectors=vectors, model=_MOCK_MODEL, dims=self._dims,
            metadata={"mock": True},
        )

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dims
        normalized = (text or "").lower()
        tokens = normalized.split() or [""]

        for token in tokens:
            for n in (3, 4):
                for i in range(max(1, len(token) - n + 1)):
                    gram = token[i : i + n] or token
                    digest = hashlib.sha256(gram.encode("utf-8")).digest()
                    bucket = int.from_bytes(digest[:4], "big") % self._dims
                    sign = 1.0 if digest[4] % 2 == 0 else -1.0
                    vec[bucket] += sign

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
