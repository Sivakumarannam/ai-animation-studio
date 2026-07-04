from uuid import UUID

from sqlalchemy import func, select

from database.models.asset import Asset, Background, Prop, AnimationPreset, Audio, Music, SoundEffect
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    model = Asset

    async def get_by_scene(self, scene_id: UUID) -> list[Asset]:
        stmt = select(Asset).where(Asset.scene_id == scene_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class BackgroundRepository(BaseRepository[Background]):
    model = Background

    async def get_library(self, pagination: PaginationParams, category: str | None = None) -> PaginatedResult[Background]:
        stmt = select(Background).where(Background.is_library == True, Background.is_deleted == False)  # noqa: E712
        if category:
            stmt = stmt.where(Background.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Background.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


class PropRepository(BaseRepository[Prop]):
    model = Prop

    async def get_library(self, pagination: PaginationParams, category: str | None = None) -> PaginatedResult[Prop]:
        stmt = select(Prop).where(Prop.is_library == True, Prop.is_deleted == False)  # noqa: E712
        if category:
            stmt = stmt.where(Prop.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Prop.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


class AnimationPresetRepository(BaseRepository[AnimationPreset]):
    model = AnimationPreset

    async def get_library(self, pagination: PaginationParams, category: str | None = None) -> PaginatedResult[AnimationPreset]:
        stmt = select(AnimationPreset).where(AnimationPreset.is_library == True, AnimationPreset.is_deleted == False)  # noqa: E712
        if category:
            stmt = stmt.where(AnimationPreset.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(AnimationPreset.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


class AudioRepository(BaseRepository[Audio]):
    model = Audio

    async def get_library(self, pagination: PaginationParams, category: str | None = None) -> PaginatedResult[Audio]:
        stmt = select(Audio).where(Audio.is_library == True, Audio.is_deleted == False)  # noqa: E712
        if category:
            stmt = stmt.where(Audio.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Audio.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


class MusicRepository(BaseRepository[Music]):
    model = Music

    async def get_library(self, pagination: PaginationParams, category: str | None = None) -> PaginatedResult[Music]:
        stmt = select(Music).where(Music.is_library == True, Music.is_deleted == False)  # noqa: E712
        if category:
            stmt = stmt.where(Music.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Music.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


class SoundEffectRepository(BaseRepository[SoundEffect]):
    model = SoundEffect

    async def get_library(self, pagination: PaginationParams, category: str | None = None) -> PaginatedResult[SoundEffect]:
        stmt = select(SoundEffect).where(SoundEffect.is_library == True, SoundEffect.is_deleted == False)  # noqa: E712
        if category:
            stmt = stmt.where(SoundEffect.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(SoundEffect.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
