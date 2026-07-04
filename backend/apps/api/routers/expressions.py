"""Expression library REST API."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, get_expression_service
from packages.core.exceptions import NotFoundError
from packages.schemas.common import PaginatedResponse
from packages.schemas.expressions import ExpressionCreate, ExpressionResponse, ExpressionUpdate
from packages.utils.pagination import PaginationParams
from services.animation_service import ExpressionService

router = APIRouter(tags=["expressions"])
ExprSvcDep = Annotated[ExpressionService, Depends(get_expression_service)]


def _to_response(e) -> ExpressionResponse:
    return ExpressionResponse(
        id=str(e.id), name=e.name, slug=e.slug, description=e.description,
        category=e.category, rig_data=e.rig_data, thumbnail_url=e.thumbnail_url,
        preview_url=e.preview_url, tags=e.tags, intensity=e.intensity,
        is_library=e.is_library, sort_order=e.sort_order,
        created_at=e.created_at.isoformat(), updated_at=e.updated_at.isoformat(),
    )


@router.get("/library/expressions", response_model=PaginatedResponse[ExpressionResponse])
async def list_expressions(
    current_user: CurrentUser,
    svc: ExprSvcDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> PaginatedResponse[ExpressionResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await svc.get_library(pagination, category=category, search=search)
    return PaginatedResponse(
        items=[_to_response(e) for e in result.items], total=result.total,
        page=result.page, page_size=result.page_size,
        total_pages=result.total_pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@router.get("/library/expressions/all", response_model=list[ExpressionResponse])
async def list_all_expressions(
    current_user: CurrentUser,
    svc: ExprSvcDep,
) -> list[ExpressionResponse]:
    items = await svc.get_all_library()
    return [_to_response(e) for e in items]


@router.post("/library/expressions", response_model=ExpressionResponse, status_code=status.HTTP_201_CREATED)
async def create_expression(
    body: ExpressionCreate,
    current_user: CurrentUser,
    svc: ExprSvcDep,
) -> ExpressionResponse:
    expr = await svc.create(body.model_dump())
    return _to_response(expr)


@router.get("/library/expressions/{expression_id}", response_model=ExpressionResponse)
async def get_expression(expression_id: UUID, current_user: CurrentUser, svc: ExprSvcDep) -> ExpressionResponse:
    try:
        return _to_response(await svc.get_by_id(expression_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/library/expressions/{expression_id}", response_model=ExpressionResponse)
async def update_expression(
    expression_id: UUID, body: ExpressionUpdate, current_user: CurrentUser, svc: ExprSvcDep,
) -> ExpressionResponse:
    try:
        return _to_response(await svc.update(expression_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/library/expressions/{expression_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expression(expression_id: UUID, current_user: CurrentUser, svc: ExprSvcDep) -> None:
    try:
        await svc.delete(expression_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/library/expressions/seed", response_model=dict)
async def seed_expressions(current_user: CurrentUser, svc: ExprSvcDep) -> dict:
    count = await svc.seed_defaults()
    return {"seeded": count, "message": f"Seeded {count} expressions"}
