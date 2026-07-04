from uuid import UUID

from sqlalchemy import func, select

from database.models.story import Story
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


class StoryRepository(BaseRepository[Story]):
    model = Story

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Story]:
        stmt = select(Story).where(Story.project_id == project_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Story.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_id_and_project(self, story_id: UUID, project_id: UUID) -> Story | None:
        stmt = select(Story).where(Story.id == story_id, Story.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
