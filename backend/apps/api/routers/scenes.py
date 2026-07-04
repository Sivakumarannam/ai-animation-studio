from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_scene_service, get_story_service
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.scenes import SceneCreate, SceneReorderRequest, SceneResponse, SceneUpdate
from packages.utils.pagination import PaginationParams
from services.scene_service import SceneService
from services.story_service import StoryService

router = APIRouter(tags=["scenes"])

SceneServiceDep = Annotated[SceneService, Depends(get_scene_service)]
StoryServiceDep = Annotated[StoryService, Depends(get_story_service)]


def _to_response(s) -> SceneResponse:
    return SceneResponse(
        id=str(s.id),
        story_id=str(s.story_id),
        scene_number=s.scene_number,
        title=s.title,
        description=s.description,
        dialogue=s.dialogue,
        action_notes=s.action_notes,
        duration_seconds=s.duration_seconds,
        background_id=str(s.background_id) if s.background_id else None,
        status=s.status,
        ordering=s.ordering,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


@router.get("/stories/{story_id}/scenes", response_model=PaginatedResponse[SceneResponse])
async def list_scenes(
    story_id: UUID,
    current_user: CurrentUser,
    svc: SceneServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> PaginatedResponse[SceneResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_by_story(story_id, pagination)
    return PaginatedResponse(
        items=[_to_response(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.post("/stories/{story_id}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    story_id: UUID,
    body: SceneCreate,
    current_user: CurrentUser,
    svc: SceneServiceDep,
) -> SceneResponse:
    bg_id = UUID(body.background_id) if body.background_id else None
    scene = await svc.create(
        story_id=story_id,
        scene_number=body.scene_number,
        title=body.title,
        description=body.description,
        dialogue=body.dialogue,
        action_notes=body.action_notes,
        duration_seconds=body.duration_seconds,
        background_id=bg_id,
        ordering=body.ordering,
    )
    return _to_response(scene)


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: UUID,
    current_user: CurrentUser,
    svc: SceneServiceDep,
) -> SceneResponse:
    scene = await svc._repo.get_by_id(scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return _to_response(scene)


@router.patch("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: UUID,
    body: SceneUpdate,
    current_user: CurrentUser,
    svc: SceneServiceDep,
) -> SceneResponse:
    scene = await svc._repo.get_by_id(scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    updated = await svc._repo.update(scene, body.model_dump(exclude_none=True))
    return _to_response(updated)


@router.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: UUID,
    current_user: CurrentUser,
    svc: SceneServiceDep,
) -> None:
    scene = await svc._repo.get_by_id(scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    await svc._repo.delete(scene)


@router.post("/scenes/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_scenes(
    body: SceneReorderRequest,
    current_user: CurrentUser,
    svc: SceneServiceDep,
) -> None:
    ids = [UUID(sid) for sid in body.scene_ids]
    await svc.reorder(ids)
