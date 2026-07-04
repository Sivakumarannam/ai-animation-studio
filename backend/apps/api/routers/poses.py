"""Pose library REST API."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_pose_service
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.poses import PoseCreate, PoseResponse, PoseUpdate
from packages.utils.pagination import PaginationParams
from services.animation_service import PoseService

router = APIRouter(tags=["poses"])
PoseSvcDep = Annotated[PoseService, Depends(get_pose_service)]


def _to_response(p) -> PoseResponse:
    return PoseResponse(
        id=str(p.id), name=p.name, slug=p.slug, description=p.description,
        category=p.category, rig_data=p.rig_data, thumbnail_url=p.thumbnail_url,
        preview_url=p.preview_url, tags=p.tags, duration_frames=p.duration_frames,
        is_loopable=p.is_loopable, is_library=p.is_library, sort_order=p.sort_order,
        created_at=p.created_at.isoformat(), updated_at=p.updated_at.isoformat(),
    )


@router.get("/library/poses", response_model=PaginatedResponse[PoseResponse])
async def list_poses(
    current_user: CurrentUser, svc: PoseSvcDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> PaginatedResponse[PoseResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_library(pagination, category=category, search=search)
    return PaginatedResponse(
        items=[_to_response(p) for p in result.items], total=result.total,
        page=result.page, page_size=result.page_size,
        total_pages=result.total_pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@router.get("/library/poses/all", response_model=list[PoseResponse])
async def list_all_poses(current_user: CurrentUser, svc: PoseSvcDep) -> list[PoseResponse]:
    return [_to_response(p) for p in await svc.get_all_library()]


@router.post("/library/poses", response_model=PoseResponse, status_code=status.HTTP_201_CREATED)
async def create_pose(body: PoseCreate, current_user: CurrentUser, svc: PoseSvcDep) -> PoseResponse:
    return _to_response(await svc.create(body.model_dump()))


@router.get("/library/poses/{pose_id}", response_model=PoseResponse)
async def get_pose(pose_id: UUID, current_user: CurrentUser, svc: PoseSvcDep) -> PoseResponse:
    try:
        return _to_response(await svc.get_by_id(pose_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/library/poses/{pose_id}", response_model=PoseResponse)
async def update_pose(pose_id: UUID, body: PoseUpdate, current_user: CurrentUser, svc: PoseSvcDep) -> PoseResponse:
    try:
        return _to_response(await svc.update(pose_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/library/poses/{pose_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pose(pose_id: UUID, current_user: CurrentUser, svc: PoseSvcDep) -> None:
    try:
        await svc.delete(pose_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/library/poses/seed", response_model=dict)
async def seed_poses(current_user: CurrentUser, svc: PoseSvcDep) -> dict:
    count = await svc.seed_defaults()
    return {"seeded": count, "message": f"Seeded {count} poses"}
