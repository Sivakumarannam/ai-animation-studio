from uuid import UUID

from sqlalchemy import func, select

from database.models.character import Character
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    model = Character

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Character]:
        stmt = select(Character).where(Character.project_id == project_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Character.created_at.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_library(self, pagination: PaginationParams) -> PaginatedResult[Character]:
        stmt = select(Character).where(Character.is_library == True)  # noqa: E712

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Character.name.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
