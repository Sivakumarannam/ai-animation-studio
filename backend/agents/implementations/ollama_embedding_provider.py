"""
Ollama Embedding Provider — implements EmbeddingProvider using a local
Ollama instance's /api/embed endpoint.
"""
from __future__ import annotations

import httpx

from agents.interfaces.embedding_provider import EmbeddingProvider, EmbeddingResult
from packages.core.exceptions import ProviderError


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 60.0,
        dims: int = 768,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._dims = dims

    @property
    def provider_name(self) -> str:
        return f"ollama/{self._model}"

    @property
    def dims(self) -> int:
        return self._dims

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        payload = {"model": self._model, "input": texts}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._base_url}/api/embed", json=payload)
                response.raise_for_status()
                data = response.json()
                vectors = data.get("embeddings", [])
                dims = len(vectors[0]) if vectors else self._dims
                return EmbeddingResult(
                    vectors=vectors, model=self._model, dims=dims,
                    metadata={"total_duration": data.get("total_duration")},
                )
        except httpx.HTTPError as e:
            raise ProviderError("ollama_embedding", str(e)) from e

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
