"""
Phase 10 — Video Assembly Engine repositories.

Pattern mirrors music_engine_repository.py exactly.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.video_assembly import VideoAssemblyJob, VideoAssemblyRetryQueue, VideoOutput


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------

@dataclass
class PageResult:
    items: list
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# VideoAssemblyJobRepository
# ---------------------------------------------------------------------------

class VideoAssemblyJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        project_id: uuid.UUID,
        episode_id: uuid.UUID | None,
        job_type: str,
        triggered_by: str = "api",
        params: dict | None = None,
    ) -> VideoAssemblyJob:
        job = VideoAssemblyJob(
            project_id=project_id,
            episode_id=episode_id,
            job_type=job_type,
            status="pending",
            triggered_by=triggered_by,
            params=params or {},
        )
        self._s.add(job)
        await self._s.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> VideoAssemblyJob | None:
        result = await self._s.execute(
            select(VideoAssemblyJob).where(VideoAssemblyJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: str,
        mode: str | None = None,
        result: dict | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        duration_seconds: float | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if mode is not None:
            values["mode"] = mode
        if result is not None:
            values["result"] = result
        if error_message is not None:
            values["error_message"] = error_message
        if started_at is not None:
            values["started_at"] = started_at
        if completed_at is not None:
            values["completed_at"] = completed_at
        if duration_seconds is not None:
            values["duration_seconds"] = duration_seconds
        await self._s.execute(
            update(VideoAssemblyJob).where(VideoAssemblyJob.id == job_id).values(**values)
        )

    async def get_recent(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[VideoAssemblyJob]:
        result = await self._s.execute(
            select(VideoAssemblyJob)
            .where(VideoAssemblyJob.project_id == project_id)
            .order_by(VideoAssemblyJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, project_id: uuid.UUID) -> dict[str, int]:
        rows = await self._s.execute(
            select(VideoAssemblyJob.status, func.count().label("n"))
            .where(VideoAssemblyJob.project_id == project_id)
            .group_by(VideoAssemblyJob.status)
        )
        return {row.status: row.n for row in rows}

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PageResult:
        q = select(VideoAssemblyJob).where(VideoAssemblyJob.project_id == project_id)
        if status:
            q = q.where(VideoAssemblyJob.status == status)
        if job_type:
            q = q.where(VideoAssemblyJob.job_type == job_type)

        total_row = await self._s.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = total_row.scalar_one()

        q = q.order_by(VideoAssemblyJob.created_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = await self._s.execute(q)
        return PageResult(
            items=list(rows.scalars().all()),
            total=total,
            page=page,
            page_size=page_size,
        )


# ---------------------------------------------------------------------------
# VideoOutputRepository
# ---------------------------------------------------------------------------

class VideoOutputRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        job_id: uuid.UUID,
        project_id: uuid.UUID,
        episode_id: uuid.UUID | None,
        output_type: str,
        storage_key: str,
        storage_bucket: str,
        file_size_bytes: int,
        duration_seconds: float,
        width: int,
        height: int,
        fps: int,
        format: str,
        provider: str,
        scene_count: int,
        has_voice: bool,
        has_music: bool,
        has_subtitles: bool,
        quality_passed: bool,
        quality_score: float,
        output_metadata: dict | None = None,
    ) -> VideoOutput:
        vo = VideoOutput(
            job_id=job_id,
            project_id=project_id,
            episode_id=episode_id,
            output_type=output_type,
            status="completed",
            storage_key=storage_key,
            storage_bucket=storage_bucket,
            file_size_bytes=file_size_bytes,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            fps=fps,
            format=format,
            provider=provider,
            scene_count=scene_count,
            has_voice=has_voice,
            has_music=has_music,
            has_subtitles=has_subtitles,
            quality_passed=quality_passed,
            quality_score=quality_score,
            output_metadata=output_metadata or {},
        )
        self._s.add(vo)
        await self._s.flush()
        return vo

    async def get_by_id(self, output_id: uuid.UUID) -> VideoOutput | None:
        result = await self._s.execute(
            select(VideoOutput).where(VideoOutput.id == output_id)
        )
        return result.scalar_one_or_none()

    async def get_by_episode(self, episode_id: uuid.UUID) -> list[VideoOutput]:
        result = await self._s.execute(
            select(VideoOutput)
            .where(VideoOutput.episode_id == episode_id)
            .order_by(VideoOutput.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        result = await self._s.execute(
            select(func.count()).where(VideoOutput.project_id == project_id)
        )
        return result.scalar_one()

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        output_type: str | None = None,
        status: str | None = None,
    ) -> PageResult:
        q = select(VideoOutput).where(VideoOutput.project_id == project_id)
        if output_type:
            q = q.where(VideoOutput.output_type == output_type)
        if status:
            q = q.where(VideoOutput.status == status)

        total_row = await self._s.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = total_row.scalar_one()

        q = q.order_by(VideoOutput.created_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = await self._s.execute(q)
        return PageResult(
            items=list(rows.scalars().all()),
            total=total,
            page=page,
            page_size=page_size,
        )


# ---------------------------------------------------------------------------
# VideoAssemblyRetryQueueRepository
# ---------------------------------------------------------------------------

class VideoAssemblyRetryQueueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        project_id: uuid.UUID,
        reason: str,
        episode_id: uuid.UUID | None = None,
        original_job_id: uuid.UUID | None = None,
        params: dict | None = None,
        max_retries: int = 3,
    ) -> VideoAssemblyRetryQueue:
        entry = VideoAssemblyRetryQueue(
            project_id=project_id,
            episode_id=episode_id,
            original_job_id=original_job_id,
            status="pending",
            reason=reason,
            params=params or {},
            max_retries=max_retries,
        )
        self._s.add(entry)
        await self._s.flush()
        return entry

    async def get_by_id(self, entry_id: uuid.UUID) -> VideoAssemblyRetryQueue | None:
        result = await self._s.execute(
            select(VideoAssemblyRetryQueue).where(VideoAssemblyRetryQueue.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_pending(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[VideoAssemblyRetryQueue]:
        result = await self._s.execute(
            select(VideoAssemblyRetryQueue)
            .where(
                VideoAssemblyRetryQueue.project_id == project_id,
                VideoAssemblyRetryQueue.status == "pending",
            )
            .order_by(VideoAssemblyRetryQueue.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self, entry_id: uuid.UUID, status: str, **kwargs: Any
    ) -> None:
        values: dict[str, Any] = {"status": status, **kwargs}
        await self._s.execute(
            update(VideoAssemblyRetryQueue)
            .where(VideoAssemblyRetryQueue.id == entry_id)
            .values(**values)
        )

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        result = await self._s.execute(
            select(func.count()).where(VideoAssemblyRetryQueue.project_id == project_id)
        )
        return result.scalar_one()

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PageResult:
        q = select(VideoAssemblyRetryQueue).where(
            VideoAssemblyRetryQueue.project_id == project_id
        )
        if status:
            q = q.where(VideoAssemblyRetryQueue.status == status)

        total_row = await self._s.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = total_row.scalar_one()

        q = q.order_by(VideoAssemblyRetryQueue.created_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = await self._s.execute(q)
        return PageResult(
            items=list(rows.scalars().all()),
            total=total,
            page=page,
            page_size=page_size,
        )
