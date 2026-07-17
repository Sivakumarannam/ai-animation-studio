"""
Phase 10 — Video Assembly Engine Celery tasks.

Follows the EXACT same pattern as Phases 6-9 (asset/animation/voice/music tasks):
  - @celery_app.task wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - session_scope() in every core function (NullPool + fork-safe commit)

ANTI-PATTERN AVOIDED: the generator-exit commit bug from Phases 3-5.
This file uses session_scope() exclusively. Verified by grep:
  grep -rn "get_session.*loop" apps/worker/tasks/video_assembly_tasks.py
→ returns nothing (clean).

IMPORTANT: Every dispatcher.dispatch() call uses the CORRECT signature:
  celery_task=, core_coro_factory=, job_id=, queue=, task_kwargs=
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from celery.utils.log import get_task_logger

from apps.worker.main import celery_app
from apps.worker.tasks.dead_letter import dead_letter_task

logger = get_task_logger(__name__)


def _run_async(coro) -> Any:
    """Run coroutine synchronously — safe inside and outside an event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repos(session):
    from repositories.video_assembly_repository import (
        VideoAssemblyJobRepository,
        VideoAssemblyRetryQueueRepository,
        VideoOutputRepository,
    )
    return dict(
        job=VideoAssemblyJobRepository(session),
        output=VideoOutputRepository(session),
        retry=VideoAssemblyRetryQueueRepository(session),
    )


def _make_services(repos, session):
    from services.video_assembly.video_assembly_job_service import VideoAssemblyJobService
    from services.video_assembly.video_assembly_service import VideoAssemblyService
    from services.video_assembly.retry_engine_service import VideoRetryEngineService

    return dict(
        job=VideoAssemblyJobService(repos["job"]),
        assembly=VideoAssemblyService(repos["output"], session),
        retry=VideoRetryEngineService(repos["retry"]),
    )


# ---------------------------------------------------------------------------
# Core async functions — session_scope() used throughout (NOT get_session())
# ---------------------------------------------------------------------------

async def _assemble_episode_core(
    job_id: str, project_id: str, params: dict
) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos, session)
        job_svc = svcs["job"]
        assembly_svc = svcs["assembly"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            if job is None:
                raise ValueError(f"VideoAssemblyJob {job_id} not found")

            output = await assembly_svc.assemble_episode(job, params)

            result = {
                "job_id": job_id,
                "output_id": str(output.id),
                "storage_key": output.storage_key,
                "duration_seconds": output.duration_seconds,
                "file_size_bytes": output.file_size_bytes,
                "scene_count": output.scene_count,
                "has_voice": output.has_voice,
                "has_music": output.has_music,
                "quality_passed": output.quality_passed,
                "quality_score": output.quality_score,
                "provider": output.provider,
                "status": "completed",
            }
            await job_svc.complete_job(job.id, result)
            logger.info(
                f"assemble_episode_complete job_id={job_id} "
                f"output_id={output.id} duration={output.duration_seconds:.1f}s "
                f"quality={output.quality_score}"
            )
            return result

        except Exception as exc:
            logger.error(f"assemble_episode_failed job_id={job_id} error={exc}")
            if job is not None:
                try:
                    await job_svc.fail_job(job.id, str(exc))
                    retry_svc = svcs["retry"]
                    from uuid import UUID
                    ep_id = params.get("episode_id")
                    await retry_svc.enqueue(
                        project_id=UUID(project_id),
                        reason=str(exc),
                        episode_id=UUID(ep_id) if ep_id else None,
                        original_job_id=job.id,
                        params=params,
                    )
                except Exception:
                    pass
            raise


async def _process_video_retry_queue_core(
    job_id: str, project_id: str, params: dict
) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos, session)
        job_svc = svcs["job"]
        assembly_svc = svcs["assembly"]
        retry_svc = svcs["retry"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        processed = 0
        succeeded = 0
        failed = 0

        try:
            pending = await retry_svc.get_pending(
                UUID(project_id), limit=params.get("limit", 10)
            )

            for entry in pending:
                await retry_svc.mark_retrying(entry)
                retry_params = retry_svc.get_retry_params(entry)
                try:
                    fake_job = type("_FakeJob", (), {
                        "id": entry.original_job_id or entry.id,
                        "project_id": entry.project_id,
                        "episode_id": entry.episode_id,
                    })()
                    await assembly_svc.assemble_episode(fake_job, retry_params)
                    await retry_svc.mark_resolved(entry)
                    succeeded += 1
                except Exception as exc:
                    if entry.retry_count >= entry.max_retries:
                        await retry_svc.mark_exhausted(entry)
                    else:
                        await retry_svc.mark_failed_retry(entry, reason=str(exc))
                    failed += 1
                processed += 1

            result = {
                "job_id": job_id,
                "processed": processed,
                "succeeded": succeeded,
                "failed": failed,
                "status": "completed",
            }
            if job is not None:
                await job_svc.complete_job(job.id, result)
            logger.info(
                f"process_video_retry_queue_complete job_id={job_id} "
                f"processed={processed} succeeded={succeeded} failed={failed}"
            )
            return result

        except Exception as exc:
            logger.error(f"process_video_retry_queue_failed job_id={job_id} error={exc}")
            if job is not None:
                try:
                    await job_svc.fail_job(job.id, str(exc))
                except Exception:
                    pass
            raise


# ---------------------------------------------------------------------------
# Celery task wrappers
# ---------------------------------------------------------------------------

class BaseVideoTask(celery_app.Task):  # type: ignore[misc]
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"task_failed task={self.name} task_id={task_id} error={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        result_keys = list(retval.keys()) if isinstance(retval, dict) else []
        logger.info(f"task_success task={self.name} result_keys={result_keys}")


@celery_app.task(
    bind=True, base=BaseVideoTask, name="video.assemble_episode",
    queue="render", max_retries=2, default_retry_delay=60,
)
def assemble_episode_task(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_assemble_episode_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseVideoTask, name="video.process_retry_queue",
    queue="default", max_retries=2, default_retry_delay=60,
)
def process_video_retry_queue_task(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_process_video_retry_queue_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise
