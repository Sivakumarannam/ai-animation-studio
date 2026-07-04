"""
Enhanced Background, Prop, AnimationPreset, Audio, Music, and SoundEffect library services.
"""
from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select

from database.models.asset import Background, Prop, AnimationPreset, Audio, Music, SoundEffect
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.asset_repository import (
    BackgroundRepository, PropRepository, AnimationPresetRepository,
    AudioRepository, MusicRepository, SoundEffectRepository
)


class BackgroundLibraryService:
    def __init__(self, repo: BackgroundRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> Background:
        bg = Background(
            name=data["name"],
            category=data.get("category", ""),
            tags=data.get("tags", []),
            file_url=data.get("file_url", ""),
            thumbnail_url=data.get("thumbnail_url", ""),
            is_library=data.get("is_library", True),
            project_id=data.get("project_id"),
            created_at=datetime.datetime.utcnow().isoformat(),
            is_deleted=False,
            metadata_=data.get("metadata_", {}),
        )
        return await self._repo.create(bg)

    async def get_by_id(self, bg_id: UUID) -> Background:
        bg = await self._repo.get_by_id(bg_id)
        if bg is None:
            raise NotFoundError("Background", bg_id)
        return bg

    async def search(
        self,
        pagination: PaginationParams,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_library: bool | None = True,
        show_deleted: bool = False,
    ) -> PaginatedResult[Background]:
        stmt = select(Background)
        if is_library is not None:
            stmt = stmt.where(Background.is_library == is_library)
        stmt = stmt.where(Background.is_deleted == show_deleted)
        if category:
            stmt = stmt.where(Background.category == category)
        if query:
            stmt = stmt.where(Background.name.ilike(f"%{query}%"))
        if tags:
            for tag in tags:
                stmt = stmt.where(Background.tags.contains([tag]))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._repo._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Background.name.asc()).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._repo._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update(self, bg_id: UUID, data: dict[str, Any]) -> Background:
        bg = await self.get_by_id(bg_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata_")
        return await self._repo.update(bg, clean_data)

    async def delete(self, bg_id: UUID) -> None:
        bg = await self.get_by_id(bg_id)
        await self._repo.delete(bg)

    async def soft_delete(self, bg_id: UUID) -> Background:
        bg = await self.get_by_id(bg_id)
        return await self._repo.update(bg, {"is_deleted": True})

    async def restore(self, bg_id: UUID) -> Background:
        bg = await self.get_by_id(bg_id)
        return await self._repo.update(bg, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                bg = await self.get_by_id(item_id)
                await self._repo.update(bg, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                bg = await self.get_by_id(item_id)
                await self._repo.update(bg, {"is_deleted": False})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_update(self, ids: list[UUID], data: dict[str, Any]) -> int:
        count = 0
        update_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in update_data:
            update_data["metadata_"] = update_data.pop("metadata_")
        for item_id in ids:
            try:
                bg = await self.get_by_id(item_id)
                await self._repo.update(bg, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def get_categories(self) -> list[str]:
        result = await self._repo._session.execute(
            select(Background.category).distinct().where(Background.category != "").where(Background.is_deleted == False)
        )
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> int:
        """Seed default background library entries."""
        from sqlalchemy import func as f_
        count_result = await self._repo._session.execute(
            select(f_(func.count)(Background.id)).where(Background.is_library == True).where(Background.is_deleted == False)  # noqa: E712
        )
        if count_result.scalar_one() > 0:
            return 0

        defaults = [
            {"name": "Village", "category": "outdoor"},
            {"name": "House Exterior", "category": "outdoor"},
            {"name": "Kitchen", "category": "indoor"},
            {"name": "Bedroom", "category": "indoor"},
            {"name": "School", "category": "educational"},
            {"name": "Hospital", "category": "medical"},
            {"name": "Market", "category": "commercial"},
            {"name": "Farm", "category": "outdoor"},
            {"name": "Office", "category": "workplace"},
            {"name": "Road", "category": "outdoor"},
            {"name": "Temple", "category": "religious"},
            {"name": "Restaurant", "category": "commercial"},
            {"name": "Festival Ground", "category": "outdoor"},
            {"name": "Rainy Street", "category": "outdoor"},
            {"name": "Night Sky", "category": "outdoor"},
            {"name": "Sunset Beach", "category": "outdoor"},
        ]
        ts = datetime.datetime.utcnow().isoformat()
        for d in defaults:
            bg = Background(
                name=d["name"],
                category=d["category"],
                tags=[d["category"]],
                is_library=True,
                created_at=ts,
                is_deleted=False,
                metadata_={},
            )
            await self._repo.create(bg)
        return len(defaults)


class PropLibraryService:
    def __init__(self, repo: PropRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> Prop:
        prop = Prop(
            name=data["name"],
            category=data.get("category", ""),
            tags=data.get("tags", []),
            file_url=data.get("file_url", ""),
            thumbnail_url=data.get("thumbnail_url", ""),
            is_library=data.get("is_library", True),
            project_id=data.get("project_id"),
            created_at=datetime.datetime.utcnow().isoformat(),
            is_deleted=False,
            metadata_=data.get("metadata_", {}),
        )
        return await self._repo.create(prop)

    async def get_by_id(self, prop_id: UUID) -> Prop:
        prop = await self._repo.get_by_id(prop_id)
        if prop is None:
            raise NotFoundError("Prop", prop_id)
        return prop

    async def search(
        self,
        pagination: PaginationParams,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_library: bool | None = True,
        show_deleted: bool = False,
    ) -> PaginatedResult[Prop]:
        stmt = select(Prop)
        if is_library is not None:
            stmt = stmt.where(Prop.is_library == is_library)
        stmt = stmt.where(Prop.is_deleted == show_deleted)
        if category:
            stmt = stmt.where(Prop.category == category)
        if query:
            stmt = stmt.where(Prop.name.ilike(f"%{query}%"))
        if tags:
            for tag in tags:
                stmt = stmt.where(Prop.tags.contains([tag]))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._repo._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Prop.name.asc()).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._repo._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update(self, prop_id: UUID, data: dict[str, Any]) -> Prop:
        prop = await self.get_by_id(prop_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata_")
        return await self._repo.update(prop, clean_data)

    async def delete(self, prop_id: UUID) -> None:
        prop = await self.get_by_id(prop_id)
        await self._repo.delete(prop)

    async def soft_delete(self, prop_id: UUID) -> Prop:
        prop = await self.get_by_id(prop_id)
        return await self._repo.update(prop, {"is_deleted": True})

    async def restore(self, prop_id: UUID) -> Prop:
        prop = await self.get_by_id(prop_id)
        return await self._repo.update(prop, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                prop = await self.get_by_id(item_id)
                await self._repo.update(prop, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                prop = await self.get_by_id(item_id)
                await self._repo.update(prop, {"is_deleted": False})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_update(self, ids: list[UUID], data: dict[str, Any]) -> int:
        count = 0
        update_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in update_data:
            update_data["metadata_"] = update_data.pop("metadata_")
        for item_id in ids:
            try:
                prop = await self.get_by_id(item_id)
                await self._repo.update(prop, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def get_categories(self) -> list[str]:
        result = await self._repo._session.execute(
            select(Prop.category).distinct().where(Prop.category != "").where(Prop.is_deleted == False)
        )
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> int:
        """Seed default prop library entries."""
        from sqlalchemy import func as f_
        count_result = await self._repo._session.execute(
            select(f_(func.count)(Prop.id)).where(Prop.is_library == True).where(Prop.is_deleted == False)  # noqa: E712
        )
        if count_result.scalar_one() > 0:
            return 0

        defaults = [
            {"name": "Sofa", "category": "furniture"},
            {"name": "Dining Table", "category": "furniture"},
            {"name": "Chair", "category": "furniture"},
            {"name": "Auto Rickshaw", "category": "vehicles"},
            {"name": "Bicycle", "category": "vehicles"},
            {"name": "Motorcycle", "category": "vehicles"},
            {"name": "Cooking Pot", "category": "kitchen"},
            {"name": "Frying Pan", "category": "kitchen"},
            {"name": "Lunch Box", "category": "kitchen"},
            {"name": "School Bag", "category": "school"},
            {"name": "Books", "category": "school"},
            {"name": "Blackboard", "category": "school"},
            {"name": "Laptop", "category": "electronics"},
            {"name": "Mobile Phone", "category": "electronics"},
            {"name": "TV", "category": "electronics"},
            {"name": "Rice Bag", "category": "food"},
            {"name": "Vegetables Basket", "category": "food"},
            {"name": "Tea Cup", "category": "food"},
            {"name": "Rupee Notes", "category": "money"},
            {"name": "Banana Tree", "category": "nature"},
            {"name": "Coconut Tree", "category": "nature"},
            {"name": "Stethoscope", "category": "medical"},
            {"name": "Medicine Bottle", "category": "medical"},
        ]
        ts = datetime.datetime.utcnow().isoformat()
        for d in defaults:
            prop = Prop(
                name=d["name"],
                category=d["category"],
                tags=[d["category"]],
                is_library=True,
                created_at=ts,
                is_deleted=False,
                metadata_={},
            )
            await self._repo.create(prop)
        return len(defaults)


class AnimationPresetLibraryService:
    def __init__(self, repo: AnimationPresetRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> AnimationPreset:
        preset = AnimationPreset(
            name=data["name"],
            category=data.get("category", ""),
            data=data.get("data", {}),
            preview_url=data.get("preview_url", ""),
            is_library=data.get("is_library", True),
            created_at=datetime.datetime.utcnow().isoformat(),
            is_deleted=False,
            tags=data.get("tags", []),
            metadata_=data.get("metadata_", {}),
        )
        return await self._repo.create(preset)

    async def get_by_id(self, preset_id: UUID) -> AnimationPreset:
        preset = await self._repo.get_by_id(preset_id)
        if preset is None:
            raise NotFoundError("AnimationPreset", preset_id)
        return preset

    async def search(
        self,
        pagination: PaginationParams,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_library: bool | None = True,
        show_deleted: bool = False,
    ) -> PaginatedResult[AnimationPreset]:
        stmt = select(AnimationPreset)
        if is_library is not None:
            stmt = stmt.where(AnimationPreset.is_library == is_library)
        stmt = stmt.where(AnimationPreset.is_deleted == show_deleted)
        if category:
            stmt = stmt.where(AnimationPreset.category == category)
        if query:
            stmt = stmt.where(AnimationPreset.name.ilike(f"%{query}%"))
        if tags:
            for tag in tags:
                stmt = stmt.where(AnimationPreset.tags.contains([tag]))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._repo._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AnimationPreset.name.asc()).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._repo._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update(self, preset_id: UUID, data: dict[str, Any]) -> AnimationPreset:
        preset = await self.get_by_id(preset_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata_")
        return await self._repo.update(preset, clean_data)

    async def delete(self, preset_id: UUID) -> None:
        preset = await self.get_by_id(preset_id)
        await self._repo.delete(preset)

    async def soft_delete(self, preset_id: UUID) -> AnimationPreset:
        preset = await self.get_by_id(preset_id)
        return await self._repo.update(preset, {"is_deleted": True})

    async def restore(self, preset_id: UUID) -> AnimationPreset:
        preset = await self.get_by_id(preset_id)
        return await self._repo.update(preset, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                preset = await self.get_by_id(item_id)
                await self._repo.update(preset, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                preset = await self.get_by_id(item_id)
                await self._repo.update(preset, {"is_deleted": False})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_update(self, ids: list[UUID], data: dict[str, Any]) -> int:
        count = 0
        update_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in update_data:
            update_data["metadata_"] = update_data.pop("metadata_")
        for item_id in ids:
            try:
                preset = await self.get_by_id(item_id)
                await self._repo.update(preset, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def get_categories(self) -> list[str]:
        result = await self._repo._session.execute(
            select(AnimationPreset.category).distinct().where(AnimationPreset.category != "").where(AnimationPreset.is_deleted == False)
        )
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> int:
        """Seed default animation preset library entries."""
        from sqlalchemy import func as f_
        count_result = await self._repo._session.execute(
            select(f_(func.count)(AnimationPreset.id)).where(AnimationPreset.is_library == True).where(AnimationPreset.is_deleted == False)  # noqa: E712
        )
        if count_result.scalar_one() > 0:
            return 0

        defaults = [
            {"name": "Walk cycle", "category": "locomotion"},
            {"name": "Running fast", "category": "locomotion"},
            {"name": "Idle breathing", "category": "idle"},
            {"name": "Talking wave", "category": "gesture"},
            {"name": "Point right", "category": "gesture"},
            {"name": "Surprise jump", "category": "action"},
            {"name": "Sit down", "category": "pose"},
            {"name": "Stand up", "category": "pose"},
        ]
        ts = datetime.datetime.utcnow().isoformat()
        for d in defaults:
            preset = AnimationPreset(
                name=d["name"],
                category=d["category"],
                data={},
                preview_url="",
                is_library=True,
                created_at=ts,
                is_deleted=False,
                tags=[d["category"]],
                metadata_={},
            )
            await self._repo.create(preset)
        return len(defaults)


class AudioLibraryService:
    def __init__(self, repo: AudioRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> Audio:
        audio = Audio(
            name=data["name"],
            category=data.get("category", ""),
            tags=data.get("tags", []),
            file_url=data.get("file_url", ""),
            preview_url=data.get("preview_url", ""),
            duration_seconds=data.get("duration_seconds", 0.0),
            is_library=data.get("is_library", True),
            project_id=data.get("project_id"),
            is_deleted=False,
            metadata_=data.get("metadata_", {}),
        )
        return await self._repo.create(audio)

    async def get_by_id(self, audio_id: UUID) -> Audio:
        audio = await self._repo.get_by_id(audio_id)
        if audio is None:
            raise NotFoundError("Audio", audio_id)
        return audio

    async def search(
        self,
        pagination: PaginationParams,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_library: bool | None = True,
        show_deleted: bool = False,
    ) -> PaginatedResult[Audio]:
        stmt = select(Audio)
        if is_library is not None:
            stmt = stmt.where(Audio.is_library == is_library)
        stmt = stmt.where(Audio.is_deleted == show_deleted)
        if category:
            stmt = stmt.where(Audio.category == category)
        if query:
            stmt = stmt.where(Audio.name.ilike(f"%{query}%"))
        if tags:
            for tag in tags:
                stmt = stmt.where(Audio.tags.contains([tag]))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._repo._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Audio.name.asc()).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._repo._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update(self, audio_id: UUID, data: dict[str, Any]) -> Audio:
        audio = await self.get_by_id(audio_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata_")
        return await self._repo.update(audio, clean_data)

    async def delete(self, audio_id: UUID) -> None:
        audio = await self.get_by_id(audio_id)
        await self._repo.delete(audio)

    async def soft_delete(self, audio_id: UUID) -> Audio:
        audio = await self.get_by_id(audio_id)
        return await self._repo.update(audio, {"is_deleted": True})

    async def restore(self, audio_id: UUID) -> Audio:
        audio = await self.get_by_id(audio_id)
        return await self._repo.update(audio, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                audio = await self.get_by_id(item_id)
                await self._repo.update(audio, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                audio = await self.get_by_id(item_id)
                await self._repo.update(audio, {"is_deleted": False})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_update(self, ids: list[UUID], data: dict[str, Any]) -> int:
        count = 0
        update_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in update_data:
            update_data["metadata_"] = update_data.pop("metadata_")
        for item_id in ids:
            try:
                audio = await self.get_by_id(item_id)
                await self._repo.update(audio, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def get_categories(self) -> list[str]:
        result = await self._repo._session.execute(
            select(Audio.category).distinct().where(Audio.category != "").where(Audio.is_deleted == False)
        )
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> int:
        """Seed default audio library entries."""
        from sqlalchemy import func as f_
        count_result = await self._repo._session.execute(
            select(f_(func.count)(Audio.id)).where(Audio.is_library == True).where(Audio.is_deleted == False)  # noqa: E712
        )
        if count_result.scalar_one() > 0:
            return 0

        defaults = [
            {"name": "Telugu Male Narrative", "category": "voiceover", "duration_seconds": 15.5},
            {"name": "Telugu Female Narrative", "category": "voiceover", "duration_seconds": 12.0},
            {"name": "Rural Village Ambient", "category": "ambient", "duration_seconds": 60.0},
            {"name": "Crowded Market Noise", "category": "ambient", "duration_seconds": 45.0},
        ]
        for d in defaults:
            audio = Audio(
                name=d["name"],
                category=d["category"],
                tags=[d["category"]],
                is_library=True,
                is_deleted=False,
                duration_seconds=d["duration_seconds"],
                metadata_={},
            )
            await self._repo.create(audio)
        return len(defaults)


class MusicLibraryService:
    def __init__(self, repo: MusicRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> Music:
        music = Music(
            name=data["name"],
            category=data.get("category", ""),
            tags=data.get("tags", []),
            file_url=data.get("file_url", ""),
            preview_url=data.get("preview_url", ""),
            duration_seconds=data.get("duration_seconds", 0.0),
            is_library=data.get("is_library", True),
            project_id=data.get("project_id"),
            is_deleted=False,
            metadata_=data.get("metadata_", {}),
        )
        return await self._repo.create(music)

    async def get_by_id(self, music_id: UUID) -> Music:
        music = await self._repo.get_by_id(music_id)
        if music is None:
            raise NotFoundError("Music", music_id)
        return music

    async def search(
        self,
        pagination: PaginationParams,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_library: bool | None = True,
        show_deleted: bool = False,
    ) -> PaginatedResult[Music]:
        stmt = select(Music)
        if is_library is not None:
            stmt = stmt.where(Music.is_library == is_library)
        stmt = stmt.where(Music.is_deleted == show_deleted)
        if category:
            stmt = stmt.where(Music.category == category)
        if query:
            stmt = stmt.where(Music.name.ilike(f"%{query}%"))
        if tags:
            for tag in tags:
                stmt = stmt.where(Music.tags.contains([tag]))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._repo._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Music.name.asc()).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._repo._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update(self, music_id: UUID, data: dict[str, Any]) -> Music:
        music = await self.get_by_id(music_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata_")
        return await self._repo.update(music, clean_data)

    async def delete(self, music_id: UUID) -> None:
        music = await self.get_by_id(music_id)
        await self._repo.delete(music)

    async def soft_delete(self, music_id: UUID) -> Music:
        music = await self.get_by_id(music_id)
        return await self._repo.update(music, {"is_deleted": True})

    async def restore(self, music_id: UUID) -> Music:
        music = await self.get_by_id(music_id)
        return await self._repo.update(music, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                music = await self.get_by_id(item_id)
                await self._repo.update(music, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                music = await self.get_by_id(item_id)
                await self._repo.update(music, {"is_deleted": False})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_update(self, ids: list[UUID], data: dict[str, Any]) -> int:
        count = 0
        update_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in update_data:
            update_data["metadata_"] = update_data.pop("metadata_")
        for item_id in ids:
            try:
                music = await self.get_by_id(item_id)
                await self._repo.update(music, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def get_categories(self) -> list[str]:
        result = await self._repo._session.execute(
            select(Music.category).distinct().where(Music.category != "").where(Music.is_deleted == False)
        )
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> int:
        """Seed default music library entries."""
        from sqlalchemy import func as f_
        count_result = await self._repo._session.execute(
            select(f_(func.count)(Music.id)).where(Music.is_library == True).where(Music.is_deleted == False)  # noqa: E712
        )
        if count_result.scalar_one() > 0:
            return 0

        defaults = [
            {"name": "Happy Acoustic Theme", "category": "cheerful", "duration_seconds": 120.0},
            {"name": "Suspenseful Background", "category": "suspense", "duration_seconds": 90.0},
            {"name": "Traditional Flute Melody", "category": "traditional", "duration_seconds": 180.0},
            {"name": "Funny Cartoon Brass", "category": "comedy", "duration_seconds": 60.0},
        ]
        for d in defaults:
            music = Music(
                name=d["name"],
                category=d["category"],
                tags=[d["category"]],
                is_library=True,
                is_deleted=False,
                duration_seconds=d["duration_seconds"],
                metadata_={},
            )
            await self._repo.create(music)
        return len(defaults)


class SoundEffectLibraryService:
    def __init__(self, repo: SoundEffectRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> SoundEffect:
        sfx = SoundEffect(
            name=data["name"],
            category=data.get("category", ""),
            tags=data.get("tags", []),
            file_url=data.get("file_url", ""),
            preview_url=data.get("preview_url", ""),
            duration_seconds=data.get("duration_seconds", 0.0),
            is_library=data.get("is_library", True),
            project_id=data.get("project_id"),
            is_deleted=False,
            metadata_=data.get("metadata_", {}),
        )
        return await self._repo.create(sfx)

    async def get_by_id(self, sfx_id: UUID) -> SoundEffect:
        sfx = await self._repo.get_by_id(sfx_id)
        if sfx is None:
            raise NotFoundError("SoundEffect", sfx_id)
        return sfx

    async def search(
        self,
        pagination: PaginationParams,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_library: bool | None = True,
        show_deleted: bool = False,
    ) -> PaginatedResult[SoundEffect]:
        stmt = select(SoundEffect)
        if is_library is not None:
            stmt = stmt.where(SoundEffect.is_library == is_library)
        stmt = stmt.where(SoundEffect.is_deleted == show_deleted)
        if category:
            stmt = stmt.where(SoundEffect.category == category)
        if query:
            stmt = stmt.where(SoundEffect.name.ilike(f"%{query}%"))
        if tags:
            for tag in tags:
                stmt = stmt.where(SoundEffect.tags.contains([tag]))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._repo._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SoundEffect.name.asc()).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._repo._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def update(self, sfx_id: UUID, data: dict[str, Any]) -> SoundEffect:
        sfx = await self.get_by_id(sfx_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata_")
        return await self._repo.update(sfx, clean_data)

    async def delete(self, sfx_id: UUID) -> None:
        sfx = await self.get_by_id(sfx_id)
        await self._repo.delete(sfx)

    async def soft_delete(self, sfx_id: UUID) -> SoundEffect:
        sfx = await self.get_by_id(sfx_id)
        return await self._repo.update(sfx, {"is_deleted": True})

    async def restore(self, sfx_id: UUID) -> SoundEffect:
        sfx = await self.get_by_id(sfx_id)
        return await self._repo.update(sfx, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                sfx = await self.get_by_id(item_id)
                await self._repo.update(sfx, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                sfx = await self.get_by_id(item_id)
                await self._repo.update(sfx, {"is_deleted": False})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_update(self, ids: list[UUID], data: dict[str, Any]) -> int:
        count = 0
        update_data = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in update_data:
            update_data["metadata_"] = update_data.pop("metadata_")
        for item_id in ids:
            try:
                sfx = await self.get_by_id(item_id)
                await self._repo.update(sfx, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def get_categories(self) -> list[str]:
        result = await self._repo._session.execute(
            select(SoundEffect.category).distinct().where(SoundEffect.category != "").where(SoundEffect.is_deleted == False)
        )
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> int:
        """Seed default sound effect library entries."""
        from sqlalchemy import func as f_
        count_result = await self._repo._session.execute(
            select(f_(func.count)(SoundEffect.id)).where(SoundEffect.is_library == True).where(SoundEffect.is_deleted == False)  # noqa: E712
        )
        if count_result.scalar_one() > 0:
            return 0

        defaults = [
            {"name": "Boing sound", "category": "cartoon", "duration_seconds": 1.2},
            {"name": "Door Creak", "category": "foley", "duration_seconds": 2.5},
            {"name": "Laughter Track", "category": "studio", "duration_seconds": 5.0},
            {"name": "Whistle slide", "category": "cartoon", "duration_seconds": 1.5},
        ]
        for d in defaults:
            sfx = SoundEffect(
                name=d["name"],
                category=d["category"],
                tags=[d["category"]],
                is_library=True,
                is_deleted=False,
                duration_seconds=d["duration_seconds"],
                metadata_={},
            )
            await self._repo.create(sfx)
        return len(defaults)
