"""
Phase 6 — AI Asset Generation Engine repositories.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.asset_generation import (
    Asset,
    AssetCache,
    AssetCollection,
    AssetEmbedding,
    AssetEvaluation,
    AssetMemory,
    AssetProject,
    AssetPrompt,
    AssetRelationship,
    AssetStyle,
    AssetTag,
    AssetVersion,
    CameraShot,
    ExpressionPreset,
    GeneratedImage,
    GenerationHistory,
    GenerationJob,
    LightingPreset,
    NegativePrompt,
    PosePreset,
    PromptHistory,
    PromptTemplate,
    RetryQueue,
    SceneComposition,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# AssetProjectRepository
# ---------------------------------------------------------------------------

class AssetProjectRepository(BaseRepository[AssetProject]):
    model = AssetProject

    async def get_by_project_id(self, project_id: UUID) -> AssetProject | None:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_active_projects(self, pagination: PaginationParams) -> PaginatedResult[AssetProject]:
        stmt = select(self.model).where(self.model.is_active.is_(True)).order_by(self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def increment_generated(self, ap_id: UUID, count: int = 1) -> None:
        await self._session.execute(
            update(self.model)
            .where(self.model.id == ap_id)
            .values(total_assets_generated=self.model.total_assets_generated + count)
        )

    async def increment_retries(self, ap_id: UUID, count: int = 1) -> None:
        await self._session.execute(
            update(self.model)
            .where(self.model.id == ap_id)
            .values(total_retries=self.model.total_retries + count)
        )


# ---------------------------------------------------------------------------
# AssetStyleRepository
# ---------------------------------------------------------------------------

class AssetStyleRepository(BaseRepository[AssetStyle]):
    model = AssetStyle

    async def get_by_slug(self, slug: str) -> AssetStyle | None:
        stmt = select(self.model).where(self.model.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_default_style(self) -> AssetStyle | None:
        stmt = select(self.model).where(self.model.is_default.is_(True), self.model.is_active.is_(True))
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_active_styles(self, pagination: PaginationParams, style_type: str | None = None) -> PaginatedResult[AssetStyle]:
        stmt = select(self.model).where(self.model.is_active.is_(True))
        if style_type:
            stmt = stmt.where(self.model.style_type == style_type)
        stmt = stmt.order_by(self.model.usage_count.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# AssetCollectionRepository
# ---------------------------------------------------------------------------

class AssetCollectionRepository(BaseRepository[AssetCollection]):
    model = AssetCollection

    async def get_by_project(self, project_id: UUID, pagination: PaginationParams) -> PaginatedResult[AssetCollection]:
        stmt = (
            select(self.model)
            .where(self.model.project_id == project_id, self.model.is_active.is_(True))
            .order_by(self.model.created_at.desc())
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def increment_asset_count(self, collection_id: UUID, delta: int = 1) -> None:
        await self._session.execute(
            update(self.model)
            .where(self.model.id == collection_id)
            .values(asset_count=self.model.asset_count + delta)
        )


# ---------------------------------------------------------------------------
# AssetRepository
# ---------------------------------------------------------------------------

class AssetRepository(BaseRepository[Asset]):
    model = Asset

    async def get_by_project(
        self,
        project_id: UUID,
        pagination: PaginationParams,
        asset_type: str | None = None,
        status: str | None = None,
        character_id: UUID | None = None,
        episode_id: UUID | None = None,
        collection_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> PaginatedResult[Asset]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted.is_(False))
        if asset_type:
            stmt = stmt.where(self.model.asset_type == asset_type)
        if status:
            stmt = stmt.where(self.model.status == status)
        if character_id:
            stmt = stmt.where(self.model.character_id == character_id)
        if episode_id:
            stmt = stmt.where(self.model.episode_id == episode_id)
        if collection_id:
            stmt = stmt.where(self.model.collection_id == collection_id)
        stmt = stmt.order_by(self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_episode(self, episode_id: UUID, asset_type: str | None = None) -> list[Asset]:
        stmt = select(self.model).where(
            self.model.episode_id == episode_id,
            self.model.is_deleted.is_(False),
        )
        if asset_type:
            stmt = stmt.where(self.model.asset_type == asset_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_character(self, character_id: UUID) -> list[Asset]:
        stmt = select(self.model).where(
            self.model.character_id == character_id,
            self.model.is_deleted.is_(False),
        ).order_by(self.model.quality_score.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self, project_id: UUID, limit: int = 20) -> list[Asset]:
        stmt = (
            select(self.model)
            .where(
                self.model.project_id == project_id,
                self.model.status == "pending",
                self.model.is_deleted.is_(False),
            )
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, project_id: UUID) -> dict[str, int]:
        stmt = (
            select(self.model.status, func.count())
            .where(self.model.project_id == project_id, self.model.is_deleted.is_(False))
            .group_by(self.model.status)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def count_by_type(self, project_id: UUID) -> dict[str, int]:
        stmt = (
            select(self.model.asset_type, func.count())
            .where(self.model.project_id == project_id, self.model.is_deleted.is_(False))
            .group_by(self.model.asset_type)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def soft_delete(self, asset_id: UUID) -> None:
        await self._session.execute(
            update(self.model)
            .where(self.model.id == asset_id)
            .values(is_deleted=True)
        )


# ---------------------------------------------------------------------------
# AssetVersionRepository
# ---------------------------------------------------------------------------

class AssetVersionRepository(BaseRepository[AssetVersion]):
    model = AssetVersion

    async def get_by_asset(self, asset_id: UUID) -> list[AssetVersion]:
        stmt = (
            select(self.model)
            .where(self.model.asset_id == asset_id)
            .order_by(self.model.version_number.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_best_version(self, asset_id: UUID) -> AssetVersion | None:
        stmt = (
            select(self.model)
            .where(self.model.asset_id == asset_id, self.model.is_approved.is_(True))
            .order_by(self.model.quality_score.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_next_version_number(self, asset_id: UUID) -> int:
        stmt = select(func.max(self.model.version_number)).where(self.model.asset_id == asset_id)
        result = await self._session.execute(stmt)
        max_ver = result.scalar_one_or_none()
        return (max_ver or 0) + 1

    async def get_paginated(self, asset_id: UUID, pagination: PaginationParams) -> PaginatedResult[AssetVersion]:
        stmt = select(self.model).where(self.model.asset_id == asset_id).order_by(self.model.version_number.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# AssetPromptRepository
# ---------------------------------------------------------------------------

class AssetPromptRepository(BaseRepository[AssetPrompt]):
    model = AssetPrompt

    async def get_by_asset(self, asset_id: UUID) -> list[AssetPrompt]:
        stmt = select(self.model).where(self.model.asset_id == asset_id).order_by(self.model.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_successful_by_type(self, prompt_type: str, limit: int = 10) -> list[AssetPrompt]:
        stmt = (
            select(self.model)
            .where(self.model.prompt_type == prompt_type, self.model.was_successful.is_(True))
            .order_by(self.model.quality_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_paginated(self, pagination: PaginationParams, prompt_type: str | None = None, successful_only: bool = False) -> PaginatedResult[AssetPrompt]:
        stmt = select(self.model)
        if prompt_type:
            stmt = stmt.where(self.model.prompt_type == prompt_type)
        if successful_only:
            stmt = stmt.where(self.model.was_successful.is_(True))
        stmt = stmt.order_by(self.model.quality_score.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# PromptTemplateRepository
# ---------------------------------------------------------------------------

class PromptTemplateRepository(BaseRepository[PromptTemplate]):
    model = PromptTemplate

    async def get_default_for_type(self, asset_type: str, style_type: str = "2d_cartoon") -> PromptTemplate | None:
        stmt = (
            select(self.model)
            .where(
                self.model.asset_type == asset_type,
                self.model.style_type == style_type,
                self.model.is_active.is_(True),
                self.model.is_default.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        tmpl = result.scalars().first()
        if tmpl:
            return tmpl
        # fallback: any active template for this type
        stmt2 = (
            select(self.model)
            .where(self.model.asset_type == asset_type, self.model.is_active.is_(True))
            .order_by(self.model.avg_quality_score.desc())
        )
        result2 = await self._session.execute(stmt2)
        return result2.scalars().first()


# ---------------------------------------------------------------------------
# PromptHistoryRepository
# ---------------------------------------------------------------------------

class PromptHistoryRepository(BaseRepository[PromptHistory]):
    model = PromptHistory

    async def get_by_asset(self, asset_id: UUID, limit: int = 20) -> list[PromptHistory]:
        stmt = (
            select(self.model)
            .where(self.model.asset_id == asset_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# NegativePromptRepository
# ---------------------------------------------------------------------------

class NegativePromptRepository(BaseRepository[NegativePrompt]):
    model = NegativePrompt

    async def get_active_by_category(self, category: str) -> list[NegativePrompt]:
        stmt = (
            select(self.model)
            .where(self.model.category == category, self.model.is_active.is_(True))
            .order_by(self.model.priority.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_universal(self) -> list[NegativePrompt]:
        stmt = (
            select(self.model)
            .where(self.model.category == "universal", self.model.is_active.is_(True))
            .order_by(self.model.priority.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# GeneratedImageRepository
# ---------------------------------------------------------------------------

class GeneratedImageRepository(BaseRepository[GeneratedImage]):
    model = GeneratedImage

    async def get_by_asset(self, asset_id: UUID) -> list[GeneratedImage]:
        stmt = (
            select(self.model)
            .where(self.model.asset_id == asset_id)
            .order_by(self.model.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self, limit: int = 20) -> list[GeneratedImage]:
        stmt = (
            select(self.model)
            .where(self.model.status == "pending")
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# AssetEvaluationRepository
# ---------------------------------------------------------------------------

class AssetEvaluationRepository(BaseRepository[AssetEvaluation]):
    model = AssetEvaluation

    async def get_by_asset(self, asset_id: UUID, pagination: PaginationParams) -> PaginatedResult[AssetEvaluation]:
        stmt = (
            select(self.model)
            .where(self.model.asset_id == asset_id)
            .order_by(self.model.created_at.desc())
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_latest_for_asset(self, asset_id: UUID) -> AssetEvaluation | None:
        stmt = (
            select(self.model)
            .where(self.model.asset_id == asset_id)
            .order_by(self.model.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_avg_score(self, project_id_list: list[UUID] | None = None) -> float:
        stmt = select(func.avg(self.model.overall_score))
        if project_id_list:
            # join via asset
            stmt = (
                select(func.avg(self.model.overall_score))
                .join(Asset, Asset.id == self.model.asset_id)
                .where(Asset.project_id.in_(project_id_list))
            )
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        return float(val) if val else 0.0


# ---------------------------------------------------------------------------
# AssetTagRepository
# ---------------------------------------------------------------------------

class AssetTagRepository(BaseRepository[AssetTag]):
    model = AssetTag

    async def get_by_slug(self, slug: str) -> AssetTag | None:
        stmt = select(self.model).where(self.model.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_all_active(self) -> list[AssetTag]:
        stmt = select(self.model).where(self.model.is_active.is_(True)).order_by(self.model.usage_count.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# AssetEmbeddingRepository
# ---------------------------------------------------------------------------

class AssetEmbeddingRepository(BaseRepository[AssetEmbedding]):
    model = AssetEmbedding

    async def get_by_asset(self, asset_id: UUID) -> AssetEmbedding | None:
        stmt = select(self.model).where(self.model.asset_id == asset_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_all_for_search(self, asset_type: str | None = None) -> list[AssetEmbedding]:
        """Return all embeddings for similarity search (caller does cosine in-memory)."""
        stmt = select(self.model)
        if asset_type:
            stmt = stmt.join(Asset, Asset.id == self.model.asset_id).where(Asset.asset_type == asset_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# AssetMemoryRepository
# ---------------------------------------------------------------------------

class AssetMemoryRepository(BaseRepository[AssetMemory]):
    model = AssetMemory

    async def get_by_type(self, project_id: UUID, memory_type: str, scope: str = "global") -> list[AssetMemory]:
        stmt = (
            select(self.model)
            .where(
                self.model.project_id == project_id,
                self.model.memory_type == memory_type,
                self.model.scope == scope,
            )
            .order_by(self.model.confidence.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_key(self, project_id: UUID, memory_type: str, key: str) -> AssetMemory | None:
        stmt = select(self.model).where(
            self.model.project_id == project_id,
            self.model.memory_type == memory_type,
            self.model.key == key,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_paginated(self, project_id: UUID, pagination: PaginationParams) -> PaginatedResult[AssetMemory]:
        stmt = select(self.model).where(self.model.project_id == project_id).order_by(self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# SceneCompositionRepository
# ---------------------------------------------------------------------------

class SceneCompositionRepository(BaseRepository[SceneComposition]):
    model = SceneComposition

    async def get_by_episode(self, episode_id: UUID) -> list[SceneComposition]:
        stmt = select(self.model).where(self.model.episode_id == episode_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_scene(self, scene_id: UUID) -> SceneComposition | None:
        stmt = select(self.model).where(self.model.scene_id == scene_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_project(self, project_id: UUID, pagination: PaginationParams) -> PaginatedResult[SceneComposition]:
        stmt = select(self.model).where(self.model.project_id == project_id).order_by(self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# CameraShotRepository
# ---------------------------------------------------------------------------

class CameraShotRepository(BaseRepository[CameraShot]):
    model = CameraShot

    async def get_by_episode(self, episode_id: UUID) -> list[CameraShot]:
        stmt = select(self.model).where(self.model.episode_id == episode_id).order_by(self.model.shot_order.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_composition(self, composition_id: UUID) -> list[CameraShot]:
        stmt = select(self.model).where(self.model.composition_id == composition_id).order_by(self.model.shot_order.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_paginated(self, episode_id: UUID, pagination: PaginationParams) -> PaginatedResult[CameraShot]:
        stmt = select(self.model).where(self.model.episode_id == episode_id).order_by(self.model.shot_order.asc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# LightingPresetRepository
# ---------------------------------------------------------------------------

class LightingPresetRepository(BaseRepository[LightingPreset]):
    model = LightingPreset

    async def get_active(self, pagination: PaginationParams) -> PaginatedResult[LightingPreset]:
        stmt = select(self.model).where(self.model.is_active.is_(True)).order_by(self.model.use_count.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_type(self, lighting_type: str) -> list[LightingPreset]:
        stmt = select(self.model).where(self.model.lighting_type == lighting_type, self.model.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# PosePresetRepository
# ---------------------------------------------------------------------------

class PosePresetRepository(BaseRepository[PosePreset]):
    model = PosePreset

    async def get_active(self, pagination: PaginationParams) -> PaginatedResult[PosePreset]:
        stmt = select(self.model).where(self.model.is_active.is_(True)).order_by(self.model.use_count.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# ExpressionPresetRepository
# ---------------------------------------------------------------------------

class ExpressionPresetRepository(BaseRepository[ExpressionPreset]):
    model = ExpressionPreset

    async def get_active(self, pagination: PaginationParams) -> PaginatedResult[ExpressionPreset]:
        stmt = select(self.model).where(self.model.is_active.is_(True)).order_by(self.model.use_count.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# RetryQueueRepository
# ---------------------------------------------------------------------------

class RetryQueueRepository(BaseRepository[RetryQueue]):
    model = RetryQueue

    async def get_pending(self, project_id: UUID, limit: int = 50) -> list[RetryQueue]:
        stmt = (
            select(self.model)
            .where(
                self.model.project_id == project_id,
                self.model.status == "pending",
                self.model.retry_count < self.model.max_retries,
            )
            .order_by(self.model.priority.desc(), self.model.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_paginated(self, project_id: UUID, pagination: PaginationParams, status: str | None = None) -> PaginatedResult[RetryQueue]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        if status:
            stmt = stmt.where(self.model.status == status)
        stmt = stmt.order_by(self.model.priority.desc(), self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_asset(self, asset_id: UUID) -> RetryQueue | None:
        stmt = select(self.model).where(
            self.model.asset_id == asset_id,
            self.model.status.in_(["pending", "retrying"]),
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()


# ---------------------------------------------------------------------------
# GenerationJobRepository
# ---------------------------------------------------------------------------

class GenerationJobRepository(BaseRepository[GenerationJob]):
    model = GenerationJob

    async def get_by_project(self, project_id: UUID, pagination: PaginationParams, status: str | None = None) -> PaginatedResult[GenerationJob]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        if status:
            stmt = stmt.where(self.model.status == status)
        stmt = stmt.order_by(self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_recent(self, project_id: UUID, limit: int = 10) -> list[GenerationJob]:
        stmt = (
            select(self.model)
            .where(self.model.project_id == project_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def complete_job(self, job_id: UUID, result: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(self.model)
            .where(self.model.id == job_id)
            .values(status="completed", result=result, completed_at=now)
        )

    async def fail_job(self, job_id: UUID, error: str) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(self.model)
            .where(self.model.id == job_id)
            .values(status="failed", error_message=error, completed_at=now)
        )

    async def start_job(self, job_id: UUID, mode: str = "sync") -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(self.model)
            .where(self.model.id == job_id)
            .values(status="running", dispatch_mode=mode, started_at=now)
        )


# ---------------------------------------------------------------------------
# GenerationHistoryRepository
# ---------------------------------------------------------------------------

class GenerationHistoryRepository(BaseRepository[GenerationHistory]):
    model = GenerationHistory

    async def get_by_project(self, project_id: UUID, pagination: PaginationParams) -> PaginatedResult[GenerationHistory]:
        stmt = select(self.model).where(self.model.project_id == project_id).order_by(self.model.created_at.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_recent_7d_stats(self, project_id: UUID) -> list[dict[str, Any]]:
        stmt = (
            select(self.model)
            .where(self.model.project_id == project_id)
            .order_by(self.model.created_at.desc())
            .limit(7)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        return [
            {
                "date": r.created_at.date().isoformat() if r.created_at else "",
                "assets_generated": r.assets_generated,
                "assets_accepted": r.assets_accepted,
                "avg_quality": r.avg_quality_score,
            }
            for r in rows
        ]


# ---------------------------------------------------------------------------
# AssetCacheRepository
# ---------------------------------------------------------------------------

class AssetCacheRepository(BaseRepository[AssetCache]):
    model = AssetCache

    async def get_by_key(self, cache_key: str) -> AssetCache | None:
        stmt = select(self.model).where(
            self.model.cache_key == cache_key,
            self.model.is_valid.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def invalidate(self, cache_key: str) -> None:
        await self._session.execute(
            update(self.model)
            .where(self.model.cache_key == cache_key)
            .values(is_valid=False)
        )

    async def record_hit(self, cache_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(self.model)
            .where(self.model.id == cache_id)
            .values(hit_count=self.model.hit_count + 1, last_hit_at=now)
        )


# ---------------------------------------------------------------------------
# AssetRelationshipRepository
# ---------------------------------------------------------------------------

class AssetRelationshipRepository(BaseRepository[AssetRelationship]):
    model = AssetRelationship

    async def get_by_source(self, source_asset_id: UUID, rel_type: str | None = None) -> list[AssetRelationship]:
        stmt = select(self.model).where(self.model.source_asset_id == source_asset_id)
        if rel_type:
            stmt = stmt.where(self.model.relationship_type == rel_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_target(self, target_asset_id: UUID, rel_type: str | None = None) -> list[AssetRelationship]:
        stmt = select(self.model).where(self.model.target_asset_id == target_asset_id)
        if rel_type:
            stmt = stmt.where(self.model.relationship_type == rel_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
