"""
Module 2 — Animation Engine Services.
ExpressionService, PoseService, CharacterTemplateService,
SceneCompositionService, TimelineService, AssetManagerService.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.animation import (
    AssetVersion,
    CharacterTemplate,
    Expression,
    Pose,
    SceneComposition,
    Timeline,
)
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.animation_repository import (
    AssetVersionRepository,
    CharacterTemplateRepository,
    ExpressionRepository,
    PoseRepository,
    SceneCompositionRepository,
    TimelineRepository,
)
from repositories.asset_repository import (
    BackgroundRepository,
    PropRepository,
    AnimationPresetRepository,
    AudioRepository,
    MusicRepository,
    SoundEffectRepository,
)


# ---------------------------------------------------------------------------
# Expression Service
# ---------------------------------------------------------------------------

class ExpressionService:
    def __init__(self, repo: ExpressionRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> Expression:
        expr = Expression(**{k: v for k, v in data.items() if hasattr(Expression, k)})
        return await self._repo.create(expr)

    async def get_by_id(self, expr_id: UUID) -> Expression:
        expr = await self._repo.get_by_id(expr_id)
        if expr is None:
            raise NotFoundError("Expression", expr_id)
        return expr

    async def get_by_slug(self, slug: str) -> Expression:
        expr = await self._repo.get_by_slug(slug)
        if expr is None:
            raise NotFoundError("Expression", slug)
        return expr

    async def get_library(
        self,
        pagination: PaginationParams,
        category: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[Expression]:
        return await self._repo.get_library(pagination, category=category, search=search)

    async def get_all_library(self) -> list[Expression]:
        return await self._repo.get_all_library()

    async def update(self, expr_id: UUID, data: dict[str, Any]) -> Expression:
        expr = await self.get_by_id(expr_id)
        return await self._repo.update(expr, {k: v for k, v in data.items() if v is not None})

    async def delete(self, expr_id: UUID) -> None:
        expr = await self.get_by_id(expr_id)
        await self._repo.delete(expr)

    async def seed_defaults(self) -> int:
        """Seed the standard expression library if empty."""
        existing = await self._repo.get_all_library()
        if existing:
            return 0

        defaults = [
            {"name": "Happy", "slug": "happy", "category": "positive", "sort_order": 10},
            {"name": "Sad", "slug": "sad", "category": "negative", "sort_order": 20},
            {"name": "Angry", "slug": "angry", "category": "negative", "sort_order": 30},
            {"name": "Laugh", "slug": "laugh", "category": "positive", "sort_order": 40},
            {"name": "Smile", "slug": "smile", "category": "positive", "sort_order": 50},
            {"name": "Shock", "slug": "shock", "category": "surprise", "sort_order": 60},
            {"name": "Fear", "slug": "fear", "category": "negative", "sort_order": 70},
            {"name": "Cry", "slug": "cry", "category": "negative", "sort_order": 80},
            {"name": "Thinking", "slug": "thinking", "category": "neutral", "sort_order": 90},
            {"name": "Confused", "slug": "confused", "category": "neutral", "sort_order": 100},
            {"name": "Sleeping", "slug": "sleeping", "category": "neutral", "sort_order": 110},
            {"name": "Excited", "slug": "excited", "category": "positive", "sort_order": 120},
            {"name": "Embarrassed", "slug": "embarrassed", "category": "negative", "sort_order": 130},
        ]
        for d in defaults:
            await self._repo.create(Expression(**d))
        return len(defaults)


# ---------------------------------------------------------------------------
# Pose Service
# ---------------------------------------------------------------------------

class PoseService:
    def __init__(self, repo: PoseRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> Pose:
        pose = Pose(**{k: v for k, v in data.items() if hasattr(Pose, k)})
        return await self._repo.create(pose)

    async def get_by_id(self, pose_id: UUID) -> Pose:
        pose = await self._repo.get_by_id(pose_id)
        if pose is None:
            raise NotFoundError("Pose", pose_id)
        return pose

    async def get_by_slug(self, slug: str) -> Pose:
        pose = await self._repo.get_by_slug(slug)
        if pose is None:
            raise NotFoundError("Pose", slug)
        return pose

    async def get_library(
        self,
        pagination: PaginationParams,
        category: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[Pose]:
        return await self._repo.get_library(pagination, category=category, search=search)

    async def get_all_library(self) -> list[Pose]:
        return await self._repo.get_all_library()

    async def update(self, pose_id: UUID, data: dict[str, Any]) -> Pose:
        pose = await self.get_by_id(pose_id)
        return await self._repo.update(pose, {k: v for k, v in data.items() if v is not None})

    async def delete(self, pose_id: UUID) -> None:
        pose = await self.get_by_id(pose_id)
        await self._repo.delete(pose)

    async def seed_defaults(self) -> int:
        """Seed the standard pose library if empty."""
        existing = await self._repo.get_all_library()
        if existing:
            return 0

        defaults = [
            {"name": "Idle", "slug": "idle", "category": "basic", "is_loopable": True, "duration_frames": 60, "sort_order": 10},
            {"name": "Walk", "slug": "walk", "category": "locomotion", "is_loopable": True, "duration_frames": 24, "sort_order": 20},
            {"name": "Run", "slug": "run", "category": "locomotion", "is_loopable": True, "duration_frames": 16, "sort_order": 30},
            {"name": "Sit", "slug": "sit", "category": "basic", "is_loopable": False, "duration_frames": 1, "sort_order": 40},
            {"name": "Stand", "slug": "stand", "category": "basic", "is_loopable": False, "duration_frames": 1, "sort_order": 50},
            {"name": "Jump", "slug": "jump", "category": "action", "is_loopable": False, "duration_frames": 30, "sort_order": 60},
            {"name": "Point", "slug": "point", "category": "gesture", "is_loopable": False, "duration_frames": 1, "sort_order": 70},
            {"name": "Wave", "slug": "wave", "category": "gesture", "is_loopable": True, "duration_frames": 48, "sort_order": 80},
            {"name": "Eat", "slug": "eat", "category": "activity", "is_loopable": True, "duration_frames": 72, "sort_order": 90},
            {"name": "Drink", "slug": "drink", "category": "activity", "is_loopable": False, "duration_frames": 48, "sort_order": 100},
            {"name": "Read", "slug": "read", "category": "activity", "is_loopable": True, "duration_frames": 120, "sort_order": 110},
            {"name": "Phone", "slug": "phone", "category": "activity", "is_loopable": True, "duration_frames": 90, "sort_order": 120},
            {"name": "Dance", "slug": "dance", "category": "action", "is_loopable": True, "duration_frames": 96, "sort_order": 130},
            {"name": "Drive", "slug": "drive", "category": "activity", "is_loopable": True, "duration_frames": 60, "sort_order": 140},
        ]
        for d in defaults:
            await self._repo.create(Pose(**d))
        return len(defaults)


# ---------------------------------------------------------------------------
# Character Template Service
# ---------------------------------------------------------------------------

class CharacterTemplateService:
    def __init__(self, repo: CharacterTemplateRepository) -> None:
        self._repo = repo

    async def create(self, data: dict[str, Any]) -> CharacterTemplate:
        # handle metadata_ alias
        if "metadata_" in data:
            data["metadata_"] = data.pop("metadata_")
        tmpl = CharacterTemplate(**{k: v for k, v in data.items() if hasattr(CharacterTemplate, k)})
        return await self._repo.create(tmpl)

    async def get_by_id(self, tmpl_id: UUID) -> CharacterTemplate:
        tmpl = await self._repo.get_by_id(tmpl_id)
        if tmpl is None:
            raise NotFoundError("CharacterTemplate", tmpl_id)
        return tmpl

    async def get_by_slug(self, slug: str) -> CharacterTemplate:
        tmpl = await self._repo.get_by_slug(slug)
        if tmpl is None:
            raise NotFoundError("CharacterTemplate", slug)
        return tmpl

    async def get_library(
        self,
        pagination: PaginationParams,
        plugin_id: str | None = None,
        archetype: str | None = None,
        search: str | None = None,
        show_deleted: bool = False,
    ) -> PaginatedResult[CharacterTemplate]:
        return await self._repo.get_library(
            pagination, plugin_id=plugin_id, archetype=archetype, search=search, show_deleted=show_deleted
        )

    async def get_by_plugin(self, plugin_id: str) -> list[CharacterTemplate]:
        return await self._repo.get_by_plugin(plugin_id)

    async def update(self, tmpl_id: UUID, data: dict[str, Any]) -> CharacterTemplate:
        tmpl = await self.get_by_id(tmpl_id)
        clean = {k: v for k, v in data.items() if v is not None}
        if "metadata_" in clean:
            clean["metadata_"] = clean.pop("metadata_")
        return await self._repo.update(tmpl, clean)

    async def delete(self, tmpl_id: UUID) -> None:
        tmpl = await self.get_by_id(tmpl_id)
        await self._repo.delete(tmpl)

    async def soft_delete(self, tmpl_id: UUID) -> CharacterTemplate:
        tmpl = await self.get_by_id(tmpl_id)
        return await self._repo.update(tmpl, {"is_deleted": True})

    async def restore(self, tmpl_id: UUID) -> CharacterTemplate:
        tmpl = await self.get_by_id(tmpl_id)
        return await self._repo.update(tmpl, {"is_deleted": False})

    async def bulk_delete(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                tmpl = await self.get_by_id(item_id)
                await self._repo.update(tmpl, {"is_deleted": True})
                count += 1
            except Exception:
                pass
        return count

    async def bulk_restore(self, ids: list[UUID]) -> int:
        count = 0
        for item_id in ids:
            try:
                tmpl = await self.get_by_id(item_id)
                await self._repo.update(tmpl, {"is_deleted": False})
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
                tmpl = await self.get_by_id(item_id)
                await self._repo.update(tmpl, update_data)
                count += 1
            except Exception:
                pass
        return count

    async def seed_from_plugin(self, plugin_id: str) -> int:
        """Seed character templates from a registered plugin."""
        existing = await self._repo.get_by_plugin(plugin_id)
        if existing:
            return 0

        try:
            from plugins.registry import get_registry
            registry = get_registry()
            plugin = registry.get_plugin(plugin_id)
            if plugin is None:
                return 0
            archetypes = plugin.get_character_archetypes()
        except Exception:
            return 0

        count = 0
        for arch in archetypes:
            slug = f"{plugin_id}_{arch.get('key', arch.get('archetype', arch.get('name', '').lower()))}"
            tmpl = CharacterTemplate(
                name=arch.get("name", ""),
                name_local=arch.get("name_local", ""),
                slug=slug,
                archetype=arch.get("archetype", arch.get("role", "")),
                plugin_id=plugin_id,
                description=arch.get("personality", ""),
                personality=arch.get("personality", ""),
                age_range=arch.get("age_range", ""),
                gender=arch.get("gender", ""),
                typical_expressions=arch.get("typical_expressions", []),
                tags=[plugin_id],
            )
            await self._repo.create(tmpl)
            count += 1
        return count


# ---------------------------------------------------------------------------
# Scene Composition Service
# ---------------------------------------------------------------------------

class SceneCompositionService:
    def __init__(self, repo: SceneCompositionRepository) -> None:
        self._repo = repo

    async def get_or_create(self, scene_id: UUID) -> SceneComposition:
        comp = await self._repo.get_by_scene(scene_id)
        if comp is None:
            comp = SceneComposition(
                scene_id=scene_id,
                camera={"x": 0, "y": 0, "zoom": 1.0, "rotation": 0},
                lighting={"ambient": 0.8, "time_of_day": "day"},
            )
            comp = await self._repo.create(comp)
        return comp

    async def get_by_scene(self, scene_id: UUID) -> SceneComposition:
        comp = await self._repo.get_by_scene(scene_id)
        if comp is None:
            raise NotFoundError("SceneComposition", scene_id)
        return comp

    async def get_by_id(self, comp_id: UUID) -> SceneComposition:
        comp = await self._repo.get_by_id(comp_id)
        if comp is None:
            raise NotFoundError("SceneComposition", comp_id)
        return comp

    async def update(self, comp_id: UUID, data: dict[str, Any]) -> SceneComposition:
        comp = await self.get_by_id(comp_id)
        clean = {k: v for k, v in data.items() if v is not None}
        updated = await self._repo.update(comp, clean)
        return await self._repo.bump_version(updated)

    async def add_character(self, comp_id: UUID, char_data: dict[str, Any]) -> SceneComposition:
        comp = await self.get_by_id(comp_id)
        chars = list(comp.characters)
        chars.append(char_data)
        return await self._repo.update(comp, {"characters": chars})

    async def remove_character(self, comp_id: UUID, character_ref_id: str) -> SceneComposition:
        comp = await self.get_by_id(comp_id)
        chars = [c for c in comp.characters if c.get("ref_id") != character_ref_id]
        return await self._repo.update(comp, {"characters": chars})

    async def add_prop(self, comp_id: UUID, prop_data: dict[str, Any]) -> SceneComposition:
        comp = await self.get_by_id(comp_id)
        props = list(comp.props)
        props.append(prop_data)
        return await self._repo.update(comp, {"props": props})

    async def remove_prop(self, comp_id: UUID, prop_ref_id: str) -> SceneComposition:
        comp = await self.get_by_id(comp_id)
        props = [p for p in comp.props if p.get("ref_id") != prop_ref_id]
        return await self._repo.update(comp, {"props": props})

    async def delete(self, comp_id: UUID) -> None:
        comp = await self.get_by_id(comp_id)
        await self._repo.delete(comp)


# ---------------------------------------------------------------------------
# Timeline Service
# ---------------------------------------------------------------------------

class TimelineService:
    def __init__(self, repo: TimelineRepository) -> None:
        self._repo = repo

    async def get_or_create(self, composition_id: UUID, fps: int = 24) -> Timeline:
        tl = await self._repo.get_by_composition(composition_id)
        if tl is None:
            tl = Timeline(composition_id=composition_id, fps=fps)
            tl = await self._repo.create(tl)
        return tl

    async def get_by_composition(self, composition_id: UUID) -> Timeline:
        tl = await self._repo.get_by_composition(composition_id)
        if tl is None:
            raise NotFoundError("Timeline", composition_id)
        return tl

    async def get_by_id(self, tl_id: UUID) -> Timeline:
        tl = await self._repo.get_by_id(tl_id)
        if tl is None:
            raise NotFoundError("Timeline", tl_id)
        return tl

    async def update(self, tl_id: UUID, data: dict[str, Any]) -> Timeline:
        tl = await self.get_by_id(tl_id)
        return await self._repo.update(tl, {k: v for k, v in data.items() if v is not None})

    async def add_keyframe(self, tl_id: UUID, keyframe: dict[str, Any]) -> Timeline:
        tl = await self.get_by_id(tl_id)
        frames = list(tl.keyframes)
        frames.append(keyframe)
        frames.sort(key=lambda k: k.get("frame", 0))
        return await self._repo.update(tl, {"keyframes": frames})

    async def add_clip(self, tl_id: UUID, clip: dict[str, Any]) -> Timeline:
        tl = await self.get_by_id(tl_id)
        clips = list(tl.clips)
        clips.append(clip)
        clips.sort(key=lambda c: c.get("start_frame", 0))
        return await self._repo.update(tl, {"clips": clips})

    async def remove_clip(self, tl_id: UUID, clip_id: str) -> Timeline:
        tl = await self.get_by_id(tl_id)
        clips = [c for c in tl.clips if c.get("id") != clip_id]
        return await self._repo.update(tl, {"clips": clips})

    async def set_playhead(self, tl_id: UUID, frame: int) -> Timeline:
        tl = await self.get_by_id(tl_id)
        return await self._repo.update(tl, {"playhead_frame": frame})

    async def delete(self, tl_id: UUID) -> None:
        tl = await self.get_by_id(tl_id)
        await self._repo.delete(tl)


# ---------------------------------------------------------------------------
# Asset Manager Service
# ---------------------------------------------------------------------------

class AssetManagerService:
    def __init__(
        self,
        version_repo: AssetVersionRepository,
        expression_repo: ExpressionRepository,
        pose_repo: PoseRepository,
        char_template_repo: CharacterTemplateRepository,
        background_repo: BackgroundRepository,
        prop_repo: PropRepository,
        preset_repo: AnimationPresetRepository,
        audio_repo: AudioRepository,
        music_repo: MusicRepository,
        sfx_repo: SoundEffectRepository,
    ) -> None:
        self._versions = version_repo
        self._expressions = expression_repo
        self._poses = pose_repo
        self._templates = char_template_repo
        self._backgrounds = background_repo
        self._props = prop_repo
        self._presets = preset_repo
        self._audios = audio_repo
        self._musics = music_repo
        self._sfxs = sfx_repo

    async def create_version(
        self,
        asset_type: str,
        asset_id: UUID,
        snapshot: dict[str, Any],
        change_summary: str = "",
        file_url: str = "",
        file_size_bytes: int = 0,
        created_by: UUID | None = None,
    ) -> AssetVersion:
        version_number = await self._versions.next_version_number(asset_type, asset_id)
        v = AssetVersion(
            asset_type=asset_type,
            asset_id=asset_id,
            version_number=version_number,
            snapshot=snapshot,
            change_summary=change_summary,
            file_url=file_url,
            file_size_bytes=file_size_bytes,
            created_by=created_by,
        )
        return await self._versions.create(v)

    async def get_versions(
        self,
        asset_type: str,
        asset_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[AssetVersion]:
        return await self._versions.get_versions(asset_type, asset_id, pagination)

    async def search(
        self,
        query: str = "",
        asset_types: list[str] | None = None,
        categories: list[str] | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 24,
        show_deleted: bool = False,
    ) -> dict:
        """Cross-table search across all 7 asset types."""
        from sqlalchemy import select
        results = []
        pagination = PaginationParams(page=page, page_size=page_size)
        types_to_search = set(asset_types or ["character_template", "background", "prop", "animation_preset", "audio", "music", "sound_effect"])

        if "character_template" in types_to_search:
            tmpls = await self._templates.get_library(
                pagination, search=query or None
            )
            for t in tmpls.items:
                results.append({
                    "asset_type": "character_template",
                    "id": str(t.id),
                    "name": t.name,
                    "category": t.archetype,
                    "tags": t.tags,
                    "thumbnail_url": t.thumbnail_url,
                    "is_library": t.is_library,
                    "is_deleted": t.is_deleted,
                })

        if "background" in types_to_search:
            stmt = select(self._backgrounds.model).where(self._backgrounds.model.is_deleted == show_deleted)
            if query:
                stmt = stmt.where(self._backgrounds.model.name.ilike(f"%{query}%"))
            res = await self._backgrounds._session.execute(stmt)
            for b in res.scalars().all():
                results.append({
                    "asset_type": "background",
                    "id": str(b.id),
                    "name": b.name,
                    "category": b.category,
                    "tags": b.tags,
                    "thumbnail_url": b.thumbnail_url,
                    "is_library": b.is_library,
                    "is_deleted": b.is_deleted,
                })

        if "prop" in types_to_search:
            stmt = select(self._props.model).where(self._props.model.is_deleted == show_deleted)
            if query:
                stmt = stmt.where(self._props.model.name.ilike(f"%{query}%"))
            res = await self._props._session.execute(stmt)
            for p in res.scalars().all():
                results.append({
                    "asset_type": "prop",
                    "id": str(p.id),
                    "name": p.name,
                    "category": p.category,
                    "tags": p.tags,
                    "thumbnail_url": p.thumbnail_url,
                    "is_library": p.is_library,
                    "is_deleted": p.is_deleted,
                })

        if "animation_preset" in types_to_search:
            stmt = select(self._presets.model).where(self._presets.model.is_deleted == show_deleted)
            if query:
                stmt = stmt.where(self._presets.model.name.ilike(f"%{query}%"))
            res = await self._presets._session.execute(stmt)
            for a in res.scalars().all():
                results.append({
                    "asset_type": "animation_preset",
                    "id": str(a.id),
                    "name": a.name,
                    "category": a.category,
                    "tags": a.tags,
                    "thumbnail_url": "",
                    "is_library": a.is_library,
                    "is_deleted": a.is_deleted,
                })

        if "audio" in types_to_search:
            stmt = select(self._audios.model).where(self._audios.model.is_deleted == show_deleted)
            if query:
                stmt = stmt.where(self._audios.model.name.ilike(f"%{query}%"))
            res = await self._audios._session.execute(stmt)
            for au in res.scalars().all():
                results.append({
                    "asset_type": "audio",
                    "id": str(au.id),
                    "name": au.name,
                    "category": au.category,
                    "tags": au.tags,
                    "thumbnail_url": "",
                    "is_library": au.is_library,
                    "is_deleted": au.is_deleted,
                })

        if "music" in types_to_search:
            stmt = select(self._musics.model).where(self._musics.model.is_deleted == show_deleted)
            if query:
                stmt = stmt.where(self._musics.model.name.ilike(f"%{query}%"))
            res = await self._musics._session.execute(stmt)
            for m in res.scalars().all():
                results.append({
                    "asset_type": "music",
                    "id": str(m.id),
                    "name": m.name,
                    "category": m.category,
                    "tags": m.tags,
                    "thumbnail_url": "",
                    "is_library": m.is_library,
                    "is_deleted": m.is_deleted,
                })

        if "sound_effect" in types_to_search:
            stmt = select(self._sfxs.model).where(self._sfxs.model.is_deleted == show_deleted)
            if query:
                stmt = stmt.where(self._sfxs.model.name.ilike(f"%{query}%"))
            res = await self._sfxs._session.execute(stmt)
            for s in res.scalars().all():
                results.append({
                    "asset_type": "sound_effect",
                    "id": str(s.id),
                    "name": s.name,
                    "category": s.category,
                    "tags": s.tags,
                    "thumbnail_url": "",
                    "is_library": s.is_library,
                    "is_deleted": s.is_deleted,
                })

        # Filter by categories/tags if provided
        if categories:
            results = [r for r in results if r["category"] in categories]
        if tags:
            results = [r for r in results if any(tag in r["tags"] for tag in tags)]

        total = len(results)
        sliced_results = results[(page - 1) * page_size : page * page_size]
        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "results": sliced_results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def export_asset(self, asset_type: str, asset_id: UUID) -> dict[str, Any]:
        """Export an asset as a JSON snapshot."""
        snapshot = {}
        if asset_type == "character_template":
            tmpl = await self._templates.get_by_id(asset_id)
            if tmpl:
                snapshot = {
                    "type": "character_template", "id": str(tmpl.id), "name": tmpl.name,
                    "slug": tmpl.slug, "archetype": tmpl.archetype, "plugin_id": tmpl.plugin_id,
                    "voice_profile": tmpl.voice_profile, "animation_rig": tmpl.animation_rig,
                    "tags": tmpl.tags, "metadata": tmpl.metadata_,
                }
        elif asset_type == "background":
            bg = await self._backgrounds.get_by_id(asset_id)
            if bg:
                snapshot = {
                    "type": "background", "id": str(bg.id), "name": bg.name,
                    "category": bg.category, "tags": bg.tags, "file_url": bg.file_url,
                    "thumbnail_url": bg.thumbnail_url, "metadata": bg.metadata_,
                }
        elif asset_type == "prop":
            pr = await self._props.get_by_id(asset_id)
            if pr:
                snapshot = {
                    "type": "prop", "id": str(pr.id), "name": pr.name,
                    "category": pr.category, "tags": pr.tags, "file_url": pr.file_url,
                    "thumbnail_url": pr.thumbnail_url, "metadata": pr.metadata_,
                }
        elif asset_type == "animation_preset":
            ap = await self._presets.get_by_id(asset_id)
            if ap:
                snapshot = {
                    "type": "animation_preset", "id": str(ap.id), "name": ap.name,
                    "category": ap.category, "data": ap.data, "preview_url": ap.preview_url,
                    "tags": ap.tags, "metadata": ap.metadata_,
                }
        elif asset_type == "audio":
            au = await self._audios.get_by_id(asset_id)
            if au:
                snapshot = {
                    "type": "audio", "id": str(au.id), "name": au.name,
                    "category": au.category, "tags": au.tags, "file_url": au.file_url,
                    "preview_url": au.preview_url, "duration_seconds": au.duration_seconds,
                    "metadata": au.metadata_,
                }
        elif asset_type == "music":
            mu = await self._musics.get_by_id(asset_id)
            if mu:
                snapshot = {
                    "type": "music", "id": str(mu.id), "name": mu.name,
                    "category": mu.category, "tags": mu.tags, "file_url": mu.file_url,
                    "preview_url": mu.preview_url, "duration_seconds": mu.duration_seconds,
                    "metadata": mu.metadata_,
                }
        elif asset_type == "sound_effect":
            sf = await self._sfxs.get_by_id(asset_id)
            if sf:
                snapshot = {
                    "type": "sound_effect", "id": str(sf.id), "name": sf.name,
                    "category": sf.category, "tags": sf.tags, "file_url": sf.file_url,
                    "preview_url": sf.preview_url, "duration_seconds": sf.duration_seconds,
                    "metadata": sf.metadata_,
                }
        return snapshot
