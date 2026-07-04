from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_project_service, get_story_service
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.stories import StoryCreate, StoryResponse, StoryUpdate
from packages.utils.pagination import PaginationParams
from services.project_service import ProjectService
from services.story_service import StoryService

router = APIRouter(tags=["stories"])

StoryServiceDep = Annotated[StoryService, Depends(get_story_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def _to_response(s) -> StoryResponse:
    return StoryResponse(
        id=str(s.id),
        project_id=str(s.project_id),
        title=s.title,
        premise=s.premise,
        full_script=s.full_script,
        genre=s.genre,
        tone=s.tone,
        duration_target=s.duration_target,
        language=s.language,
        status=s.status,
        ai_metadata=s.ai_metadata,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


async def _verify_project(project_id: UUID, user_id, svc: ProjectService) -> None:
    try:
        await svc.get_by_id(project_id, user_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")


@router.get("/projects/{project_id}/stories", response_model=PaginatedResponse[StoryResponse])
async def list_stories(
    project_id: UUID,
    current_user: CurrentUser,
    svc: StoryServiceDep,
    project_svc: ProjectServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[StoryResponse]:
    await _verify_project(project_id, current_user.id, project_svc)
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_by_project(project_id, pagination)
    return PaginatedResponse(
        items=[_to_response(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.post("/projects/{project_id}/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    project_id: UUID,
    body: StoryCreate,
    current_user: CurrentUser,
    svc: StoryServiceDep,
    project_svc: ProjectServiceDep,
) -> StoryResponse:
    await _verify_project(project_id, current_user.id, project_svc)
    story = await svc.create(
        project_id=project_id,
        title=body.title,
        premise=body.premise,
        genre=body.genre,
        tone=body.tone,
        duration_target=body.duration_target,
        language=body.language,
    )
    return _to_response(story)


@router.get("/stories/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: UUID,
    current_user: CurrentUser,
    svc: StoryServiceDep,
) -> StoryResponse:
    try:
        story = await svc._repo.get_by_id(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return _to_response(story)


@router.patch("/stories/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: UUID,
    body: StoryUpdate,
    current_user: CurrentUser,
    svc: StoryServiceDep,
) -> StoryResponse:
    try:
        story = await svc._repo.get_by_id(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)
        updated = await svc._repo.update(story, body.model_dump(exclude_none=True))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return _to_response(updated)


@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    current_user: CurrentUser,
    svc: StoryServiceDep,
) -> None:
    story = await svc._repo.get_by_id(story_id)
    if story is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    await svc._repo.delete(story)
