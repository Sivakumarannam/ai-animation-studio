from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.project import Project
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository

from sqlalchemy import func


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def get_by_user(
        self, user_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[Project]:
        stmt = select(Project).where(Project.user_id == user_id)
        if status:
            stmt = stmt.where(Project.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Project.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_id_and_user(self, project_id: UUID, user_id: UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
