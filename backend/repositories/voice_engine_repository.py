"""
Phase 8 — Voice Engine Repositories.
Mirrors animation_engine_repository.py shape exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.voice_engine import VoiceGenerationJob, VoiceOutput, VoiceRetryQueue
from packages.utils.pagination import PaginationParams, PaginatedResult


class VoiceJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: VoiceGenerationJob) -> VoiceGenerationJob:
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> VoiceGenerationJob | None:
        result = await self._session.execute(
            select(VoiceGenerationJob).where(VoiceGenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult:
        q = select(VoiceGenerationJob).where(VoiceGenerationJob.project_id == project_id)
        if status:
            q = q.where(VoiceGenerationJob.status == status)
        if job_type:
            q = q.where(VoiceGenerationJob.job_type == job_type)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(VoiceGenerationJob.created_at.desc())
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_recent(self, project_id: uuid.UUID, limit: int = 5) -> list[VoiceGenerationJob]:
        rows = (
            await self._session.execute(
                select(VoiceGenerationJob)
                .where(VoiceGenerationJob.project_id == project_id)
                .order_by(VoiceGenerationJob.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    async def count_by_status(self, project_id: uuid.UUID) -> dict[str, int]:
        rows = (
            await self._session.execute(
                select(VoiceGenerationJob.status, func.count(VoiceGenerationJob.id))
                .where(VoiceGenerationJob.project_id == project_id)
                .group_by(VoiceGenerationJob.status)
            )
        ).all()
        return {row[0]: row[1] for row in rows}


class VoiceOutputRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, output: VoiceOutput) -> VoiceOutput:
        self._session.add(output)
        await self._session.flush()
        return output

    async def get_by_id(self, output_id: uuid.UUID) -> VoiceOutput | None:
        result = await self._session.execute(
            select(VoiceOutput).where(VoiceOutput.id == output_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        character_id: str | None = None,
        language: str | None = None,
        status: str | None = None,
    ) -> PaginatedResult:
        q = select(VoiceOutput).where(VoiceOutput.project_id == project_id)
        if character_id:
            q = q.where(VoiceOutput.character_id == character_id)
        if language:
            q = q.where(VoiceOutput.language == language)
        if status:
            q = q.where(VoiceOutput.status == status)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(VoiceOutput.created_at.desc())
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(VoiceOutput.id)).where(VoiceOutput.project_id == project_id)
        )
        return result.scalar_one()


class VoiceRetryQueueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entry: VoiceRetryQueue) -> VoiceRetryQueue:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_by_id(self, entry_id: uuid.UUID) -> VoiceRetryQueue | None:
        result = await self._session.execute(
            select(VoiceRetryQueue).where(VoiceRetryQueue.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_pending(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[VoiceRetryQueue]:
        now = datetime.now(timezone.utc)
        rows = (
            await self._session.execute(
                select(VoiceRetryQueue)
                .where(VoiceRetryQueue.project_id == project_id)
                .where(VoiceRetryQueue.status == "pending")
                .where(
                    (VoiceRetryQueue.next_retry_at == None)  # noqa: E711
                    | (VoiceRetryQueue.next_retry_at <= now)
                )
                .order_by(VoiceRetryQueue.created_at.asc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        status: str | None = None,
    ) -> PaginatedResult:
        q = select(VoiceRetryQueue).where(VoiceRetryQueue.project_id == project_id)
        if status:
            q = q.where(VoiceRetryQueue.status == status)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(VoiceRetryQueue.created_at.desc())
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(VoiceRetryQueue.id)).where(
                VoiceRetryQueue.project_id == project_id
            )
        )
        return result.scalar_one()
