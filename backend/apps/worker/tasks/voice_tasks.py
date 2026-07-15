"""
Phase 8 — Voice Engine Celery tasks.

Follows the EXACT same pattern as Phase 7 animation_tasks.py:
  - @celery_app.task wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - session_scope() in every core function (NullPool + fork-safe commit)

IMPORTANT: Every dispatcher.dispatch() call uses the CORRECT signature:
  celery_task=, core_coro_factory=, job_id=, queue=, task_kwargs=
Verified against apps/worker/dispatcher.py before shipping.
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
    from repositories.voice_engine_repository import (
        VoiceJobRepository,
        VoiceOutputRepository,
        VoiceRetryQueueRepository,
    )
    return dict(
        job=VoiceJobRepository(session),
        output=VoiceOutputRepository(session),
        retry=VoiceRetryQueueRepository(session),
    )


def _make_services(repos):
    from agents.registry import get_provider_registry
    from agents.interfaces.voice_provider import VoiceProvider
    from services.voice.voice_job_service import VoiceJobService
    from services.voice.line_synthesis_service import LineSynthesisService
    from services.voice.retry_engine_service import VoiceRetryEngineService

    registry = get_provider_registry()
    voice_provider = registry.resolve(VoiceProvider)

    return dict(
        job=VoiceJobService(repos["job"]),
        synthesis=LineSynthesisService(repos["output"], voice_provider),
        retry=VoiceRetryEngineService(repos["retry"]),
    )


# ---------------------------------------------------------------------------
# Core async functions
# ---------------------------------------------------------------------------

async def _generate_line_core(
    job_id: str, project_id: str, params: dict
) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos)
        job_svc = svcs["job"]
        synthesis_svc = svcs["synthesis"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            if job is None:
                raise ValueError(f"VoiceGenerationJob {job_id} not found")

            output = await synthesis_svc.synthesize_line(job, params)

            result = {
                "job_id": job_id,
                "output_id": str(output.id),
                "storage_key": output.storage_key,
                "duration_seconds": output.duration_seconds,
                "provider": output.provider,
                "status": "completed",
            }
            await job_svc.complete_job(job.id, result)
            logger.info(
                f"generate_line_complete job_id={job_id} "
                f"character={params.get('character_id', '')} "
                f"output_id={output.id}"
            )
            return result

        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _generate_scene_core(
    job_id: str, scene_id: str, project_id: str, params: dict
) -> dict[str, Any]:
    """Generate voice audio for all dialogue lines in a scene."""
    from database.connection import session_scope
    from uuid import UUID
    import time

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos)
        job_svc = svcs["job"]
        synthesis_svc = svcs["synthesis"]
        retry_svc = svcs["retry"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            if job is None:
                raise ValueError(f"VoiceGenerationJob {job_id} not found")

            start = time.time()
            dialogue_lines = params.get("dialogue_lines", [])
            succeeded = 0
            failed = 0
            output_ids = []

            for line_data in dialogue_lines:
                try:
                    from database.models.voice_engine import VoiceGenerationJob
                    line_job = VoiceGenerationJob(
                        project_id=UUID(project_id),
                        scene_id=UUID(scene_id) if scene_id else None,
                        episode_id=UUID(params["episode_id"]) if params.get("episode_id") else None,
                        character_id=line_data.get("character_id"),
                        job_type="generate_line",
                        status="running",
                        triggered_by="scene_voice",
                        params=line_data,
                    )
                    line_job = await repos["job"].create(line_job)
                    await session.flush()

                    output = await synthesis_svc.synthesize_line(line_job, line_data)
                    output_ids.append(str(output.id))
                    line_job.status = "completed"
                    await session.flush()
                    succeeded += 1

                except Exception as exc:
                    logger.warning(
                        f"voice_line_failed scene_id={scene_id} "
                        f"character={line_data.get('character_id', '')} error={exc}"
                    )
                    failed += 1
                    await retry_svc.enqueue(
                        project_id=UUID(project_id),
                        reason=str(exc),
                        scene_id=UUID(scene_id) if scene_id else None,
                        episode_id=UUID(params["episode_id"]) if params.get("episode_id") else None,
                        original_job_id=job.id,
                        params=line_data,
                    )

            duration = round(time.time() - start, 2)
            result = {
                "job_id": job_id,
                "scene_id": scene_id,
                "lines_succeeded": succeeded,
                "lines_failed": failed,
                "output_ids": output_ids,
                "duration_seconds": duration,
                "status": "completed" if failed == 0 else "partial",
            }
            await job_svc.complete_job(job.id, result)
            logger.info(
                f"generate_scene_complete job_id={job_id} "
                f"succeeded={succeeded} failed={failed}"
            )
            return result

        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _process_voice_retry_queue_core(
    job_id: str, project_id: str, params: dict
) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos)
        job_svc = svcs["job"]
        retry_svc = svcs["retry"]
        synthesis_svc = svcs["synthesis"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            pending = await retry_svc.get_pending(UUID(project_id), limit=params.get("limit", 10))
            resolved = 0
            exhausted = 0

            for entry in pending:
                await retry_svc.mark_retrying(entry)
                await session.flush()

                try:
                    from database.models.voice_engine import VoiceGenerationJob
                    retry_job = VoiceGenerationJob(
                        project_id=UUID(project_id),
                        scene_id=entry.scene_id,
                        episode_id=entry.episode_id,
                        job_type="generate_line",
                        status="running",
                        triggered_by="retry_queue",
                        params=retry_svc.get_retry_params(entry),
                    )
                    retry_job = await repos["job"].create(retry_job)
                    await session.flush()

                    await synthesis_svc.synthesize_line(
                        retry_job, retry_svc.get_retry_params(entry)
                    )
                    await retry_svc.mark_resolved(entry)
                    resolved += 1

                except Exception as exc:
                    logger.warning(f"voice_retry_failed entry_id={entry.id} error={exc}")
                    if entry.retry_count >= entry.max_retries:
                        await retry_svc.mark_exhausted(entry)
                        exhausted += 1
                    else:
                        # Transition back to pending so it's picked up next run
                        await retry_svc.mark_failed_retry(entry, reason=str(exc))

            result = {
                "project_id": project_id,
                "processed": len(pending),
                "resolved": resolved,
                "exhausted": exhausted,
            }
            if job:
                await job_svc.complete_job(job.id, result)
            return result

        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


# ---------------------------------------------------------------------------
# Celery task wrappers
# ---------------------------------------------------------------------------

class BaseVoiceTask(celery_app.Task):  # type: ignore[misc]
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"task_failed task={self.name} task_id={task_id} error={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        result_keys = list(retval.keys()) if isinstance(retval, dict) else []
        logger.info(f"task_success task={self.name} result_keys={result_keys}")


@celery_app.task(
    bind=True, base=BaseVoiceTask, name="voice.generate_line",
    queue="ai", max_retries=3, default_retry_delay=30,
)
def generate_line_task(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_generate_line_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseVoiceTask, name="voice.generate_scene",
    queue="ai", max_retries=2, default_retry_delay=60,
)
def generate_scene_task(self, job_id: str, scene_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_generate_scene_core(job_id, scene_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseVoiceTask, name="voice.process_retry_queue",
    queue="default", max_retries=2, default_retry_delay=60,
)
def process_voice_retry_queue_task(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_process_voice_retry_queue_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise
