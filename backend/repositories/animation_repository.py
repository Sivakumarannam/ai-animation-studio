"""
Repositories for Module 2 — Animation Engine models.
Expression, Pose, CharacterTemplate, SceneComposition, Timeline, AssetVersion.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select

from database.models.animation import (
    AssetVersion,
    CharacterTemplate,
    Expression,
    Pose,
    SceneComposition,
    Timeline,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# Expression Repository
# ---------------------------------------------------------------------------

class ExpressionRepository(BaseRepository[Expression]):
    model = Expression

    async def get_library(
        self,
        pagination: PaginationParams,
        category: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[Expression]:
        stmt = select(Expression).where(Expression.is_library == True)  # noqa: E712
        if category:
            stmt = stmt.where(Expression.category == category)
        if search:
            stmt = stmt.where(Expression.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Expression.sort_order.asc(), Expression.name.asc())
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_slug(self, slug: str) -> Expression | None:
        result = await self._session.execute(select(Expression).where(Expression.slug == slug))
        return result.scalar_one_or_none()

    async def get_all_library(self) -> list[Expression]:
        result = await self._session.execute(
            select(Expression).where(Expression.is_library == True).order_by(Expression.sort_order.asc())  # noqa: E712
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Pose Repository
# ---------------------------------------------------------------------------

class PoseRepository(BaseRepository[Pose]):
    model = Pose

    async def get_library(
        self,
        pagination: PaginationParams,
        category: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[Pose]:
        stmt = select(Pose).where(Pose.is_library == True)  # noqa: E712
        if category:
            stmt = stmt.where(Pose.category == category)
        if search:
            stmt = stmt.where(Pose.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Pose.sort_order.asc(), Pose.name.asc())
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_slug(self, slug: str) -> Pose | None:
        result = await self._session.execute(select(Pose).where(Pose.slug == slug))
        return result.scalar_one_or_none()

    async def get_all_library(self) -> list[Pose]:
        result = await self._session.execute(
            select(Pose).where(Pose.is_library == True).order_by(Pose.sort_order.asc())  # noqa: E712
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Character Template Repository
# ---------------------------------------------------------------------------

class CharacterTemplateRepository(BaseRepository[CharacterTemplate]):
    model = CharacterTemplate

    async def get_library(
        self,
        pagination: PaginationParams,
        plugin_id: str | None = None,
        archetype: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[CharacterTemplate]:
        stmt = select(CharacterTemplate).where(CharacterTemplate.is_library == True, CharacterTemplate.is_deleted == False)  # noqa: E712
        if plugin_id:
            stmt = stmt.where(
                or_(CharacterTemplate.plugin_id == plugin_id, CharacterTemplate.plugin_id == "")
            )
        if archetype:
            stmt = stmt.where(CharacterTemplate.archetype == archetype)
        if search:
            stmt = stmt.where(
                or_(
                    CharacterTemplate.name.ilike(f"%{search}%"),
                    CharacterTemplate.name_local.ilike(f"%{search}%"),
                    CharacterTemplate.archetype.ilike(f"%{search}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(CharacterTemplate.sort_order.asc(), CharacterTemplate.name.asc())
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_slug(self, slug: str) -> CharacterTemplate | None:
        result = await self._session.execute(
            select(CharacterTemplate).where(CharacterTemplate.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_plugin(self, plugin_id: str) -> list[CharacterTemplate]:
        result = await self._session.execute(
            select(CharacterTemplate)
            .where(CharacterTemplate.plugin_id == plugin_id)
            .where(CharacterTemplate.is_library == True)  # noqa: E712
            .where(CharacterTemplate.is_deleted == False)
            .order_by(CharacterTemplate.sort_order.asc())
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Scene Composition Repository
# ---------------------------------------------------------------------------

class SceneCompositionRepository(BaseRepository[SceneComposition]):
    model = SceneComposition

    async def get_by_scene(self, scene_id: UUID) -> SceneComposition | None:
        result = await self._session.execute(
            select(SceneComposition).where(SceneComposition.scene_id == scene_id)
        )
        return result.scalar_one_or_none()

    async def bump_version(self, composition: SceneComposition) -> SceneComposition:
        composition.version += 1
        await self._session.flush()
        await self._session.refresh(composition)
        return composition


# ---------------------------------------------------------------------------
# Timeline Repository
# ---------------------------------------------------------------------------

class TimelineRepository(BaseRepository[Timeline]):
    model = Timeline

    async def get_by_composition(self, composition_id: UUID) -> Timeline | None:
        result = await self._session.execute(
            select(Timeline).where(Timeline.composition_id == composition_id)
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Asset Version Repository
# ---------------------------------------------------------------------------

class AssetVersionRepository(BaseRepository[AssetVersion]):
    model = AssetVersion

    async def get_versions(
        self,
        asset_type: str,
        asset_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[AssetVersion]:
        stmt = (
            select(AssetVersion)
            .where(AssetVersion.asset_type == asset_type)
            .where(AssetVersion.asset_id == asset_id)
            .order_by(AssetVersion.version_number.desc())
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_latest(self, asset_type: str, asset_id: UUID) -> AssetVersion | None:
        result = await self._session.execute(
            select(AssetVersion)
            .where(AssetVersion.asset_type == asset_type)
            .where(AssetVersion.asset_id == asset_id)
            .order_by(AssetVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def next_version_number(self, asset_type: str, asset_id: UUID) -> int:
        result = await self._session.execute(
            select(func.max(AssetVersion.version_number))
            .where(AssetVersion.asset_type == asset_type)
            .where(AssetVersion.asset_id == asset_id)
        )
        current = result.scalar_one_or_none()
        return (current or 0) + 1
