from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from apps.api.dependencies import CurrentUser, get_background_repo, get_prop_repo
from packages.schemas.assets import BackgroundResponse, PropResponse
from packages.schemas.common import PaginatedResponse
from packages.utils.pagination import PaginationParams
from repositories.asset_repository import BackgroundRepository, PropRepository

router = APIRouter(tags=["assets"])

BackgroundRepoDep = Annotated[BackgroundRepository, Depends(get_background_repo)]
PropRepoDep = Annotated[PropRepository, Depends(get_prop_repo)]


def _bg_to_response(b) -> BackgroundResponse:
    return BackgroundResponse(
        id=str(b.id),
        name=b.name,
        category=b.category,
        tags=b.tags or [],
        file_url=b.file_url,
        thumbnail_url=b.thumbnail_url,
        is_library=b.is_library,
        project_id=str(b.project_id) if b.project_id else None,
        created_at=str(b.created_at),
    )


def _prop_to_response(p) -> PropResponse:
    return PropResponse(
        id=str(p.id),
        name=p.name,
        category=p.category,
        tags=p.tags or [],
        file_url=p.file_url,
        thumbnail_url=p.thumbnail_url,
        is_library=p.is_library,
        project_id=str(p.project_id) if p.project_id else None,
        created_at=str(p.created_at),
    )


@router.get("/library/backgrounds", response_model=PaginatedResponse[BackgroundResponse])
async def list_backgrounds(
    current_user: CurrentUser,
    repo: BackgroundRepoDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
) -> PaginatedResponse[BackgroundResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await repo.get_library(pagination, category)
    return PaginatedResponse(
        items=[_bg_to_response(b) for b in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/library/props", response_model=PaginatedResponse[PropResponse])
async def list_props(
    current_user: CurrentUser,
    repo: PropRepoDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
) -> PaginatedResponse[PropResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await repo.get_library(pagination, category)
    return PaginatedResponse(
        items=[_prop_to_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )
