"""Character template library REST API."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_character_template_service
from packages.core.exceptions import NotFoundError
from packages.schemas.character_templates import (
    CharacterTemplateCreate, CharacterTemplateResponse, CharacterTemplateUpdate,
)
from packages.schemas.common import PaginatedResponse
from packages.utils.pagination import PaginationParams
from services.animation_service import CharacterTemplateService

router = APIRouter(tags=["character-templates"])
TmplSvcDep = Annotated[CharacterTemplateService, Depends(get_character_template_service)]


def _to_response(t) -> CharacterTemplateResponse:
    return CharacterTemplateResponse(
        id=str(t.id), name=t.name, name_local=t.name_local, slug=t.slug,
        archetype=t.archetype, plugin_id=t.plugin_id, description=t.description,
        personality=t.personality, age_range=t.age_range, gender=t.gender,
        language=t.language, voice_profile=t.voice_profile, animation_rig=t.animation_rig,
        expression_overrides=t.expression_overrides, pose_overrides=t.pose_overrides,
        clothing_variants=t.clothing_variants, accessories=t.accessories,
        thumbnail_url=t.thumbnail_url, preview_url=t.preview_url, tags=t.tags,
        typical_expressions=t.typical_expressions, is_library=t.is_library,
        version=t.version, sort_order=t.sort_order,
        created_at=t.created_at.isoformat(), updated_at=t.updated_at.isoformat(),
    )


@router.get("/library/character-templates", response_model=PaginatedResponse[CharacterTemplateResponse])
async def list_templates(
    current_user: CurrentUser, svc: TmplSvcDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    plugin_id: str | None = Query(default=None),
    archetype: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> PaginatedResponse[CharacterTemplateResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_library(pagination, plugin_id=plugin_id, archetype=archetype, search=search)
    return PaginatedResponse(
        items=[_to_response(t) for t in result.items], total=result.total,
        page=result.page, page_size=result.page_size,
        total_pages=result.total_pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@router.get("/library/character-templates/by-plugin/{plugin_id}", response_model=list[CharacterTemplateResponse])
async def list_templates_by_plugin(
    plugin_id: str, current_user: CurrentUser, svc: TmplSvcDep,
) -> list[CharacterTemplateResponse]:
    return [_to_response(t) for t in await svc.get_by_plugin(plugin_id)]


@router.post("/library/character-templates", response_model=CharacterTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: CharacterTemplateCreate, current_user: CurrentUser, svc: TmplSvcDep,
) -> CharacterTemplateResponse:
    return _to_response(await svc.create(body.model_dump()))


@router.get("/library/character-templates/{template_id}", response_model=CharacterTemplateResponse)
async def get_template(template_id: UUID, current_user: CurrentUser, svc: TmplSvcDep) -> CharacterTemplateResponse:
    try:
        return _to_response(await svc.get_by_id(template_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/library/character-templates/{template_id}", response_model=CharacterTemplateResponse)
async def update_template(
    template_id: UUID, body: CharacterTemplateUpdate, current_user: CurrentUser, svc: TmplSvcDep,
) -> CharacterTemplateResponse:
    try:
        return _to_response(await svc.update(template_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/library/character-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: UUID, current_user: CurrentUser, svc: TmplSvcDep) -> None:
    try:
        await svc.delete(template_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/library/character-templates/seed/{plugin_id}", response_model=dict)
async def seed_from_plugin(plugin_id: str, current_user: CurrentUser, svc: TmplSvcDep) -> dict:
    count = await svc.seed_from_plugin(plugin_id)
    return {"seeded": count, "plugin_id": plugin_id}
