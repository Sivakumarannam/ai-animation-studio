from uuid import UUID

from sqlalchemy import func, select, update

from database.models.scene import Scene
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


class SceneRepository(BaseRepository[Scene]):
    model = Scene

    async def get_by_story(
        self, story_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Scene]:
        stmt = select(Scene).where(Scene.story_id == story_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Scene.ordering.asc(), Scene.scene_number.asc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_id_and_story(self, scene_id: UUID, story_id: UUID) -> Scene | None:
        stmt = select(Scene).where(Scene.id == scene_id, Scene.story_id == story_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def reorder(self, scene_ids: list[UUID]) -> None:
        for i, scene_id in enumerate(scene_ids):
            stmt = update(Scene).where(Scene.id == scene_id).values(ordering=i)
            await self._session.execute(stmt)
        await self._session.flush()
