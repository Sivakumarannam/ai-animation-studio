"""Asset Manager REST API — import, export, upload, versioning, search, soft delete, and bulk operations."""
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status

from apps.api.dependencies import (
    CurrentUser, get_asset_manager_service, get_storage,
    get_background_library_service, get_prop_library_service,
    get_character_template_service, get_animation_preset_service,
    get_audio_service, get_music_service, get_sound_effect_service
)
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.compositions import AssetVersionResponse
from packages.schemas.library import (
    AssetExportRequest, AssetImportRequest, AssetSearchRequest, AssetSearchResponse,
)
from packages.schemas.assets import (
    BackgroundResponse, PropResponse, AudioResponse, MusicResponse, SoundEffectResponse, AnimationPresetResponse,
    BulkDeleteRequest, BulkRestoreRequest, BulkUpdateRequest
)
from packages.schemas.character_templates import CharacterTemplateResponse
from packages.utils.pagination import PaginationParams
from services.animation_service import AssetManagerService, CharacterTemplateService
from services.library_service import (
    BackgroundLibraryService, PropLibraryService, AnimationPresetLibraryService,
    AudioLibraryService, MusicLibraryService, SoundEffectLibraryService
)
from plugins.storage.minio_storage import MinIOStorage
from apps.api.config import get_settings

router = APIRouter(prefix="/asset-manager", tags=["asset-manager"])

AMMgrDep = Annotated[AssetManagerService, Depends(get_asset_manager_service)]
StorageDep = Annotated[MinIOStorage, Depends(get_storage)]

BgSvcDep = Annotated[BackgroundLibraryService, Depends(get_background_library_service)]
PropSvcDep = Annotated[PropLibraryService, Depends(get_prop_library_service)]
CharSvcDep = Annotated[CharacterTemplateService, Depends(get_character_template_service)]
PresetSvcDep = Annotated[AnimationPresetLibraryService, Depends(get_animation_preset_service)]
AudioSvcDep = Annotated[AudioLibraryService, Depends(get_audio_service)]
MusicSvcDep = Annotated[MusicLibraryService, Depends(get_music_service)]
SfxSvcDep = Annotated[SoundEffectLibraryService, Depends(get_sound_effect_service)]


def _get_service_for_type(
    asset_type: str,
    bg_svc: BackgroundLibraryService,
    prop_svc: PropLibraryService,
    char_svc: CharacterTemplateService,
    preset_svc: AnimationPresetLibraryService,
    audio_svc: AudioLibraryService,
    music_svc: MusicLibraryService,
    sfx_svc: SoundEffectLibraryService,
):
    if asset_type == "background":
        return bg_svc
    elif asset_type == "prop":
        return prop_svc
    elif asset_type == "character_template":
        return char_svc
    elif asset_type == "animation_preset":
        return preset_svc
    elif asset_type == "audio":
        return audio_svc
    elif asset_type == "music":
        return music_svc
    elif asset_type == "sound_effect":
        return sfx_svc
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported asset type: {asset_type}")


# Response helper mapping
def _to_response_dict(asset_type: str, item) -> dict:
    if asset_type == "background":
        return {
            "id": str(item.id), "name": item.name, "category": item.category, "tags": item.tags or [],
            "file_url": item.file_url, "thumbnail_url": item.thumbnail_url, "is_library": item.is_library,
            "project_id": str(item.project_id) if item.project_id else None, "is_deleted": item.is_deleted,
            "metadata": item.metadata_ or {}, "created_at": str(item.created_at)
        }
    elif asset_type == "prop":
        return {
            "id": str(item.id), "name": item.name, "category": item.category, "tags": item.tags or [],
            "file_url": item.file_url, "thumbnail_url": item.thumbnail_url, "is_library": item.is_library,
            "project_id": str(item.project_id) if item.project_id else None, "is_deleted": item.is_deleted,
            "metadata": item.metadata_ or {}, "created_at": str(item.created_at)
        }
    elif asset_type == "character_template":
        return {
            "id": str(item.id), "name": item.name, "name_local": item.name_local, "slug": item.slug,
            "archetype": item.archetype, "plugin_id": item.plugin_id, "description": item.description,
            "personality": item.personality, "age_range": item.age_range, "gender": item.gender,
            "language": item.language, "voice_profile": item.voice_profile, "animation_rig": item.animation_rig,
            "expression_overrides": item.expression_overrides, "pose_overrides": item.pose_overrides,
            "clothing_variants": item.clothing_variants, "accessories": item.accessories,
            "thumbnail_url": item.thumbnail_url, "preview_url": item.preview_url, "tags": item.tags or [],
            "typical_expressions": item.typical_expressions or [], "is_library": item.is_library,
            "is_deleted": item.is_deleted, "version": item.version, "sort_order": item.sort_order,
            "created_at": item.created_at.isoformat(), "updated_at": item.updated_at.isoformat()
        }
    elif asset_type == "animation_preset":
        return {
            "id": str(item.id), "name": item.name, "category": item.category, "data": item.data or {},
            "preview_url": item.preview_url, "is_library": item.is_library, "is_deleted": item.is_deleted,
            "tags": item.tags or [], "metadata": item.metadata_ or {}, "created_at": str(item.created_at)
        }
    elif asset_type in ("audio", "music", "sound_effect"):
        return {
            "id": str(item.id), "name": item.name, "category": item.category, "tags": item.tags or [],
            "file_url": item.file_url, "preview_url": item.preview_url, "duration_seconds": item.duration_seconds,
            "is_library": item.is_library, "project_id": str(item.project_id) if item.project_id else None,
            "is_deleted": item.is_deleted, "metadata": item.metadata_ or {},
            "created_at": item.created_at.isoformat(), "updated_at": item.updated_at.isoformat()
        }
    return {}


@router.post("/upload")
async def upload_asset_file(
    current_user: CurrentUser,
    storage: StorageDep,
    file: UploadFile = File(...),
    asset_type: str = Query(..., description="background, prop, audio, music, sound_effect, animation_preset")
) -> dict:
    content = await file.read()
    file_size = len(content)

    import uuid
    import os
    ext = os.path.splitext(file.filename)[1] or ""
    key = f"{asset_type}/{uuid.uuid4()}{ext}"

    storage.upload_bytes(
        bucket="assets",
        key=key,
        data=content,
        content_type=file.content_type or "application/octet-stream"
    )

    settings = get_settings()
    file_url = f"http://{settings.MINIO_ENDPOINT}/assets/{key}"

    return {
        "file_url": file_url,
        "storage_bucket": "assets",
        "storage_key": key,
        "file_size_bytes": file_size,
        "filename": file.filename
    }


@router.post("/search", response_model=AssetSearchResponse)
async def search_assets(body: AssetSearchRequest, current_user: CurrentUser, svc: AMMgrDep) -> AssetSearchResponse:
    result = await svc.search(
        query=body.query,
        asset_types=body.asset_types or None,
        categories=body.categories or None,
        tags=body.tags or None,
        page=body.page,
        page_size=body.page_size,
        show_deleted=body.show_deleted,
    )
    return AssetSearchResponse(**result)


@router.get("/search", response_model=AssetSearchResponse)
async def search_assets_get(
    current_user: CurrentUser, svc: AMMgrDep,
    q: str = Query(default=""),
    types: str = Query(default=""),
    categories: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    deleted: bool = Query(default=False),
) -> AssetSearchResponse:
    result = await svc.search(
        query=q,
        asset_types=[t for t in types.split(",") if t] or None,
        categories=[c for c in categories.split(",") if c] or None,
        page=page,
        page_size=page_size,
        show_deleted=deleted,
    )
    return AssetSearchResponse(**result)


@router.post("/export")
async def export_asset(body: AssetExportRequest, current_user: CurrentUser, svc: AMMgrDep) -> dict:
    snapshot = await svc.export_asset(body.asset_type, body.asset_id)
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return snapshot


@router.get("/versions/{asset_type}/{asset_id}", response_model=PaginatedResponse[AssetVersionResponse])
async def list_versions(
    asset_type: str, asset_id: UUID,
    current_user: CurrentUser, svc: AMMgrDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[AssetVersionResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_versions(asset_type, asset_id, pagination)
    return PaginatedResponse(
        items=[
            AssetVersionResponse(
                id=str(v.id), asset_type=v.asset_type, asset_id=str(v.asset_id),
                version_number=v.version_number, change_summary=v.change_summary,
                file_url=v.file_url, file_size_bytes=v.file_size_bytes,
                is_published=v.is_published, created_at=v.created_at.isoformat(),
            )
            for v in result.items
        ],
        total=result.total, page=result.page, page_size=result.page_size,
        total_pages=result.total_pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@router.post("/versions/{asset_type}/{asset_id}", response_model=AssetVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    asset_type: str, asset_id: UUID, body: dict,
    current_user: CurrentUser, svc: AMMgrDep,
) -> AssetVersionResponse:
    v = await svc.create_version(
        asset_type=asset_type,
        asset_id=asset_id,
        snapshot=body.get("snapshot", {}),
        change_summary=body.get("change_summary", ""),
        created_by=current_user.id,
    )
    return AssetVersionResponse(
        id=str(v.id), asset_type=v.asset_type, asset_id=str(v.asset_id),
        version_number=v.version_number, change_summary=v.change_summary,
        file_url=v.file_url, file_size_bytes=v.file_size_bytes,
        is_published=v.is_published, created_at=v.created_at.isoformat(),
    )


@router.post("/versions/{asset_type}/{asset_id}/{version_number}/restore")
async def restore_version(
    asset_type: str, asset_id: UUID, version_number: int,
    current_user: CurrentUser, am_svc: AMMgrDep,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    pagination = PaginationParams(page=1, page_size=100)
    versions = await am_svc.get_versions(asset_type, asset_id, pagination)
    target = None
    for v in versions.items:
        if v.version_number == version_number:
            target = v
            break
    if not target:
        raise HTTPException(status_code=404, detail="Version not found")

    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    await svc.update(asset_id, target.snapshot)
    return {"status": "success", "message": f"Restored {asset_type} to version {version_number}"}


@router.get("/stats", response_model=dict)
async def asset_stats(
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    """Quick stats for the Asset Manager dashboard."""
    pagination = PaginationParams(page=1, page_size=1)
    bgs = await bg_svc.search(pagination)
    props = await prop_svc.search(pagination)
    chars = await char_svc.get_library(pagination)
    presets = await preset_svc.search(pagination)
    audios = await audio_svc.search(pagination)
    musics = await music_svc.search(pagination)
    sfxs = await sfx_svc.search(pagination)

    return {
        "backgrounds": bgs.total,
        "props": props.total,
        "characters": chars.total,
        "presets": presets.total,
        "audio": audios.total,
        "music": musics.total,
        "sound_effects": sfxs.total,
    }


# ---------------------------------------------------------------------------
# Central Library REST Operations per Asset Type
# ---------------------------------------------------------------------------

@router.get("/{asset_type}")
async def list_assets(
    asset_type: str,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    deleted: bool = Query(default=False),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    tag_list = [t for t in tags.split(",") if t] if tags else None

    if asset_type == "character_template":
        res = await char_svc.get_library(pagination, search=search, show_deleted=deleted)
    else:
        svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
        res = await svc.search(pagination, query=search, category=category, tags=tag_list, show_deleted=deleted)

    return {
        "items": [_to_response_dict(asset_type, item) for item in res.items],
        "total": res.total,
        "page": res.page,
        "page_size": res.page_size,
        "total_pages": res.total_pages,
        "has_next": res.has_next,
        "has_prev": res.has_prev
    }


@router.post("/{asset_type}")
async def create_asset(
    asset_type: str,
    body: dict,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    item = await svc.create(body)
    return _to_response_dict(asset_type, item)


@router.get("/{asset_type}/{asset_id}")
async def get_asset(
    asset_type: str,
    asset_id: UUID,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    try:
        item = await svc.get_by_id(asset_id)
        return _to_response_dict(asset_type, item)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/{asset_type}/{asset_id}")
async def update_asset(
    asset_type: str,
    asset_id: UUID,
    body: dict,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    try:
        item = await svc.update(asset_id, body)
        return _to_response_dict(asset_type, item)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/{asset_type}/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_type: str,
    asset_id: UUID,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> None:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    try:
        # Soft delete is requested by user, so we toggle is_deleted=True
        await svc.soft_delete(asset_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/{asset_type}/{asset_id}/restore")
async def restore_asset(
    asset_type: str,
    asset_id: UUID,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    try:
        item = await svc.restore(asset_id)
        return _to_response_dict(asset_type, item)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


# Bulk endpoints
@router.post("/{asset_type}/bulk-delete")
async def bulk_delete_assets(
    asset_type: str,
    body: BulkDeleteRequest,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    deleted_count = await svc.bulk_delete(body.ids)
    return {"deleted": deleted_count}


@router.post("/{asset_type}/bulk-restore")
async def bulk_restore_assets(
    asset_type: str,
    body: BulkRestoreRequest,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    restored_count = await svc.bulk_restore(body.ids)
    return {"restored": restored_count}


@router.post("/{asset_type}/bulk-update")
async def bulk_update_assets(
    asset_type: str,
    body: BulkUpdateRequest,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    update_data = {}
    if body.category is not None:
        update_data["category"] = body.category
    if body.tags is not None:
        update_data["tags"] = body.tags
    if body.metadata_ is not None:
        update_data["metadata_"] = body.metadata_

    updated_count = await svc.bulk_update(body.ids, update_data)
    return {"updated": updated_count}


@router.post("/{asset_type}/seed", response_model=dict)
async def seed_assets(
    asset_type: str,
    current_user: CurrentUser,
    bg_svc: BgSvcDep, prop_svc: PropSvcDep, char_svc: CharSvcDep,
    preset_svc: PresetSvcDep, audio_svc: AudioSvcDep, music_svc: MusicSvcDep, sfx_svc: SfxSvcDep,
) -> dict:
    if asset_type == "character_template":
        count = await char_svc.seed_from_plugin("telugu_family_comedy")
        return {"seeded": count}
    svc = _get_service_for_type(asset_type, bg_svc, prop_svc, char_svc, preset_svc, audio_svc, music_svc, sfx_svc)
    if hasattr(svc, "seed_defaults"):
        count = await svc.seed_defaults()
        return {"seeded": count}
    return {"seeded": 0}
