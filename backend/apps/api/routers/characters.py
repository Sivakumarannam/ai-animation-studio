from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_character_service, get_project_service
from packages.core.exceptions import NotFoundError
from packages.schemas.characters import CharacterCreate, CharacterResponse, CharacterUpdate
from packages.schemas.common import PaginatedResponse
from packages.utils.pagination import PaginationParams
from services.character_service import CharacterService
from services.project_service import ProjectService

router = APIRouter(tags=["characters"])

CharacterServiceDep = Annotated[CharacterService, Depends(get_character_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def _to_response(c) -> CharacterResponse:
    return CharacterResponse(
        id=str(c.id),
        project_id=str(c.project_id),
        name=c.name,
        description=c.description,
        personality=c.personality,
        voice_profile=c.voice_profile,
        age_range=c.age_range,
        gender=c.gender,
        is_library=c.is_library,
        thumbnail_url=c.thumbnail_url,
        asset_data=c.asset_data,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


@router.get("/library/characters", response_model=PaginatedResponse[CharacterResponse])
async def list_library_characters(
    current_user: CurrentUser,
    svc: CharacterServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[CharacterResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_library(pagination)
    return PaginatedResponse(
        items=[_to_response(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/projects/{project_id}/characters", response_model=PaginatedResponse[CharacterResponse])
async def list_project_characters(
    project_id: UUID,
    current_user: CurrentUser,
    svc: CharacterServiceDep,
    project_svc: ProjectServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[CharacterResponse]:
    try:
        await project_svc.get_by_id(project_id, current_user.id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_by_project(project_id, pagination)
    return PaginatedResponse(
        items=[_to_response(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.post("/projects/{project_id}/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    project_id: UUID,
    body: CharacterCreate,
    current_user: CurrentUser,
    svc: CharacterServiceDep,
    project_svc: ProjectServiceDep,
) -> CharacterResponse:
    try:
        await project_svc.get_by_id(project_id, current_user.id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    character = await svc.create(
        project_id=project_id,
        name=body.name,
        description=body.description,
        personality=body.personality,
        voice_profile=body.voice_profile,
        age_range=body.age_range,
        gender=body.gender,
        asset_data=body.asset_data,
    )
    return _to_response(character)


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID,
    current_user: CurrentUser,
    svc: CharacterServiceDep,
) -> CharacterResponse:
    try:
        character = await svc.get_by_id(character_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return _to_response(character)


@router.patch("/characters/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: UUID,
    body: CharacterUpdate,
    current_user: CurrentUser,
    svc: CharacterServiceDep,
) -> CharacterResponse:
    try:
        character = await svc.update(character_id, body.model_dump(exclude_none=True))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return _to_response(character)


@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: UUID,
    current_user: CurrentUser,
    svc: CharacterServiceDep,
) -> None:
    try:
        await svc.delete(character_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
