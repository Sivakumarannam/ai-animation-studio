"""
Phase 6 — Asset Library Service.

Provides search, deduplication, and retrieval across the asset library.
Supports keyword search (metadata) and semantic similarity search (embeddings).
"""
from __future__ import annotations

import math
from typing import Any
from uuid import UUID

from database.models.asset_generation import GeneratedAsset as Asset, AssetEmbedding
from repositories.asset_generation_repository import (
    AssetCacheRepository,
    AssetEmbeddingRepository,
    AssetMemoryRepository,
    AssetRepository,
)
from packages.utils.pagination import PaginationParams


class AssetLibraryService:
    """Search, retrieve, and manage the asset library."""

    def __init__(
        self,
        asset_repo: AssetRepository,
        embedding_repo: AssetEmbeddingRepository,
        cache_repo: AssetCacheRepository,
        memory_repo: AssetMemoryRepository,
        embedding_provider,  # EmbeddingProvider
    ) -> None:
        self._asset_repo = asset_repo
        self._embedding_repo = embedding_repo
        self._cache_repo = cache_repo
        self._memory_repo = memory_repo
        self._embedder = embedding_provider

    async def search(
        self,
        project_id: UUID,
        query: str,
        asset_type: str | None = None,
        character_id: UUID | None = None,
        episode_id: UUID | None = None,
        tags: list[str] | None = None,
        min_quality: float = 0.0,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Keyword + tag search over the asset library."""
        pagination = PaginationParams(page=offset // limit + 1, page_size=limit)
        result = await self._asset_repo.get_by_project(
            project_id=project_id,
            pagination=pagination,
            asset_type=asset_type,
            status=status or "completed",
            character_id=character_id,
            episode_id=episode_id,
        )

        # Filter by quality and tags in-memory
        filtered = [
            a for a in result.items
            if a.quality_score >= min_quality
            and (not tags or any(t in a.tags for t in tags))
            and (not query or query.lower() in a.name.lower() or query.lower() in a.description.lower())
        ]

        return {
            "items": filtered,
            "total": len(filtered),
            "query": query,
        }

    async def semantic_search(
        self,
        query: str,
        project_id: UUID,
        asset_type: str | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Semantic similarity search using embedding vectors."""
        query_embedding = await self._embedder.embed(query)

        all_embeddings = await self._embedding_repo.get_all_for_search(asset_type)
        if not all_embeddings:
            return []

        scored: list[tuple[float, AssetEmbedding]] = []
        for emb in all_embeddings:
            score = _cosine_similarity(query_embedding, emb.vector)
            scored.append((score, emb))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        results = []
        for score, emb in top:
            asset = await self._asset_repo.get_by_id(emb.asset_id)
            if asset and asset.project_id == project_id:
                results.append({"score": round(score, 4), "asset_id": str(emb.asset_id)})
        return results

    async def get_character_library(self, project_id: UUID, pagination: PaginationParams) -> Any:
        return await self._asset_repo.get_by_project(
            project_id=project_id,
            pagination=pagination,
            asset_type="character",
            status="completed",
        )

    async def get_background_library(self, project_id: UUID, pagination: PaginationParams) -> Any:
        return await self._asset_repo.get_by_project(
            project_id=project_id,
            pagination=pagination,
            asset_type="background",
            status="completed",
        )

    async def get_prop_library(self, project_id: UUID, pagination: PaginationParams) -> Any:
        return await self._asset_repo.get_by_project(
            project_id=project_id,
            pagination=pagination,
            asset_type="prop",
            status="completed",
        )

    async def embed_asset(self, asset: Asset) -> AssetEmbedding | None:
        """Generate and store an embedding for an asset."""
        text = f"{asset.name} {asset.description} {' '.join(asset.tags)}"
        try:
            vector = await self._embedder.embed(text)
        except Exception:
            return None

        existing = await self._embedding_repo.get_by_asset(asset.id)
        if existing:
            existing.vector = vector
            existing.source_text = text
            await self._embedding_repo._session.flush()
            return existing

        from datetime import datetime, timezone
        embedding = AssetEmbedding(
            asset_id=asset.id,
            vector=vector,
            vector_dim=len(vector),
            source_text=text,
            embedding_model=getattr(self._embedder, "provider_name", "mock"),
            embedded_at=datetime.now(timezone.utc),
        )
        return await self._embedding_repo.create(embedding)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
