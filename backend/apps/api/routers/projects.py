from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_project_service
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from packages.utils.pagination import PaginationParams
from services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def _to_response(p) -> ProjectResponse:
    return ProjectResponse(
        id=str(p.id),
        user_id=str(p.user_id),
        title=p.title,
        description=p.description,
        status=p.status,
        plugin_id=p.plugin_id,
        animation_style=p.animation_style,
        metadata=p.metadata_,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    current_user: CurrentUser,
    svc: ProjectServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
) -> PaginatedResponse[ProjectResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_by_user(current_user.id, pagination, status)
    return PaginatedResponse(
        items=[_to_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: CurrentUser,
    svc: ProjectServiceDep,
) -> ProjectResponse:
    project = await svc.create(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        plugin_id=body.plugin_id,
        animation_style=body.animation_style,
        metadata=body.metadata,
    )
    return _to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    svc: ProjectServiceDep,
) -> ProjectResponse:
    try:
        project = await svc.get_by_id(project_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return _to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    current_user: CurrentUser,
    svc: ProjectServiceDep,
) -> ProjectResponse:
    try:
        project = await svc.update(project_id, current_user.id, body.model_dump(exclude_none=True))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return _to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    svc: ProjectServiceDep,
) -> None:
    try:
        await svc.delete(project_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
