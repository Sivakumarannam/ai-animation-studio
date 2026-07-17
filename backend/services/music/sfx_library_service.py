"""
Phase 9 — SFXLibraryService.
Browse and select preset sound effects from the mu_sfx_assets table.
"""
from __future__ import annotations

from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.music_engine_repository import SFXAssetRepository
from database.models.music_engine import SoundEffectAsset


class SFXLibraryService:
    """Browse and select preset sound effects."""

    def __init__(self, repo: SFXAssetRepository) -> None:
        self._repo = repo

    async def list_sfx(
        self,
        pagination: PaginationParams,
        *,
        category: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[SoundEffectAsset]:
        return await self._repo.get_paginated(
            pagination, category=category, search=search
        )

    async def get_by_key(self, sfx_key: str) -> SoundEffectAsset | None:
        return await self._repo.get_by_key(sfx_key)

    async def count_active(self) -> int:
        return await self._repo.count_active()
