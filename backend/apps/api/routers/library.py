"""
Background and Prop library REST APIs (enhanced with search/categories).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import (
    CurrentUser,
    get_background_library_service,
    get_prop_library_service,
)
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.library import (
    BackgroundCreate, BackgroundResponse, BackgroundUpdate,
    PropCreate, PropResponse, PropUpdate,
)
from packages.utils.pagination import PaginationParams
from services.library_service import BackgroundLibraryService, PropLibraryService

router = APIRouter(tags=["library"])
BgSvcDep = Annotated[BackgroundLibraryService, Depends(get_background_library_service)]
PropSvcDep = Annotated[PropLibraryService, Depends(get_prop_library_service)]


# ---------------------------------------------------------- helpers
def _bg_response(b) -> BackgroundResponse:
    return BackgroundResponse(
        id=str(b.id), name=b.name, category=b.category, tags=b.tags,
        file_url=b.file_url, thumbnail_url=b.thumbnail_url,
        is_library=b.is_library, project_id=str(b.project_id) if b.project_id else None,
        created_at=b.created_at,
    )


def _prop_response(p) -> PropResponse:
    return PropResponse(
        id=str(p.id), name=p.name, category=p.category, tags=p.tags,
        file_url=p.file_url, thumbnail_url=p.thumbnail_url,
        is_library=p.is_library, project_id=str(p.project_id) if p.project_id else None,
        created_at=p.created_at,
    )


# ---------------------------------------------------------- backgrounds
@router.get("/library/backgrounds", response_model=PaginatedResponse[BackgroundResponse])
async def list_backgrounds(
    current_user: CurrentUser, svc: BgSvcDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> PaginatedResponse[BackgroundResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.search(pagination, query=search, category=category, is_library=True)
    return PaginatedResponse(
        items=[_bg_response(b) for b in result.items], total=result.total,
        page=result.page, page_size=result.page_size,
        total_pages=result.total_pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@router.get("/library/backgrounds/categories", response_model=list[str])
async def list_bg_categories(current_user: CurrentUser, svc: BgSvcDep) -> list[str]:
    return await svc.get_categories()


@router.post("/library/backgrounds", response_model=BackgroundResponse, status_code=status.HTTP_201_CREATED)
async def create_background(body: BackgroundCreate, current_user: CurrentUser, svc: BgSvcDep) -> BackgroundResponse:
    return _bg_response(await svc.create(body.model_dump()))


@router.get("/library/backgrounds/{background_id}", response_model=BackgroundResponse)
async def get_background(background_id: UUID, current_user: CurrentUser, svc: BgSvcDep) -> BackgroundResponse:
    try:
        return _bg_response(await svc.get_by_id(background_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/library/backgrounds/{background_id}", response_model=BackgroundResponse)
async def update_background(
    background_id: UUID, body: BackgroundUpdate, current_user: CurrentUser, svc: BgSvcDep,
) -> BackgroundResponse:
    try:
        return _bg_response(await svc.update(background_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/library/backgrounds/{background_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_background(background_id: UUID, current_user: CurrentUser, svc: BgSvcDep) -> None:
    try:
        await svc.delete(background_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/library/backgrounds/seed", response_model=dict)
async def seed_backgrounds(current_user: CurrentUser, svc: BgSvcDep) -> dict:
    count = await svc.seed_defaults()
    return {"seeded": count}


# ---------------------------------------------------------- props
@router.get("/library/props", response_model=PaginatedResponse[PropResponse])
async def list_props(
    current_user: CurrentUser, svc: PropSvcDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> PaginatedResponse[PropResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.search(pagination, query=search, category=category, is_library=True)
    return PaginatedResponse(
        items=[_prop_response(p) for p in result.items], total=result.total,
        page=result.page, page_size=result.page_size,
        total_pages=result.total_pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@router.get("/library/props/categories", response_model=list[str])
async def list_prop_categories(current_user: CurrentUser, svc: PropSvcDep) -> list[str]:
    return await svc.get_categories()


@router.post("/library/props", response_model=PropResponse, status_code=status.HTTP_201_CREATED)
async def create_prop(body: PropCreate, current_user: CurrentUser, svc: PropSvcDep) -> PropResponse:
    return _prop_response(await svc.create(body.model_dump()))


@router.get("/library/props/{prop_id}", response_model=PropResponse)
async def get_prop(prop_id: UUID, current_user: CurrentUser, svc: PropSvcDep) -> PropResponse:
    try:
        return _prop_response(await svc.get_by_id(prop_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/library/props/{prop_id}", response_model=PropResponse)
async def update_prop(prop_id: UUID, body: PropUpdate, current_user: CurrentUser, svc: PropSvcDep) -> PropResponse:
    try:
        return _prop_response(await svc.update(prop_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/library/props/{prop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prop(prop_id: UUID, current_user: CurrentUser, svc: PropSvcDep) -> None:
    try:
        await svc.delete(prop_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/library/props/seed", response_model=dict)
async def seed_props(current_user: CurrentUser, svc: PropSvcDep) -> dict:
    count = await svc.seed_defaults()
    return {"seeded": count}
