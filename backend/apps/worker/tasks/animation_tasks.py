"""
Phase 7 — Animation Engine Celery tasks.

Follows the EXACT same pattern as Phase 6 asset_tasks.py:
  - @celery_app.task wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - session_scope() in every core function (NullPool + fork-safe commit)

IMPORTANT: Every dispatcher.dispatch() call uses the CORRECT signature:
  celery_task=, core_coro_factory=, job_id=, queue=, task_kwargs=
Grepped against apps/worker/dispatcher.py before shipping.
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
    from repositories.animation_engine_repository import (
        AnimationJobRepository,
        AnimationRenderOutputRepository,
        AnimationRetryQueueRepository,
    )
    return dict(
        job=AnimationJobRepository(session),
        output=AnimationRenderOutputRepository(session),
        retry=AnimationRetryQueueRepository(session),
    )


def _make_services(repos):
    from agents.registry import get_provider_registry
    from agents.interfaces.animation_provider import AnimationProvider
    from services.animation.render_job_service import RenderJobService
    from services.animation.scene_composition_service import SceneCompositionService
    from services.animation.retry_engine_service import RetryEngineService

    registry = get_provider_registry()
    animation_provider = registry.resolve(AnimationProvider)

    return dict(
        job=RenderJobService(repos["job"]),
        composition=SceneCompositionService(repos["output"], animation_provider),
        retry=RetryEngineService(repos["retry"]),
    )


# ---------------------------------------------------------------------------
# Core async functions (called directly in sync fallback mode)
# ---------------------------------------------------------------------------

async def _render_scene_core(job_id: str, scene_id: str, project_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos)
        job_svc = svcs["job"]
        comp_svc = svcs["composition"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            if job is None:
                raise ValueError(f"AnimationJob {job_id} not found")

            scene_data = {
                "background_storage_key": params.get("background_storage_key", ""),
                "characters": params.get("characters", []),
                "duration_seconds": float(params.get("duration_seconds", 5.0)),
                "fps": int(params.get("fps", 24)),
                "width": int(params.get("width", 1920)),
                "height": int(params.get("height", 1080)),
                "camera_motion": params.get("camera_motion", "static"),
                "transition_in": params.get("transition_in", "cut"),
                "transition_out": params.get("transition_out", "cut"),
                "dialogue_segments": params.get("dialogue_segments", []),
                "extra": params.get("extra", {}),
            }

            output = await comp_svc.render_scene(job, scene_data)

            result = {
                "job_id": job_id,
                "scene_id": scene_id,
                "output_id": str(output.id),
                "storage_key": output.storage_key,
                "duration_seconds": output.duration_seconds,
                "provider": output.provider,
                "status": "completed",
            }

            await job_svc.complete_job(job.id, result)
            logger.info(f"render_scene_complete job_id={job_id} scene_id={scene_id} output_id={output.id}")
            return result

        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _render_episode_core(job_id: str, episode_id: str, project_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID
    import time

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos)
        job_svc = svcs["job"]
        comp_svc = svcs["composition"]
        retry_svc = svcs["retry"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            if job is None:
                raise ValueError(f"AnimationJob {job_id} not found")

            start = time.time()
            scenes = params.get("scenes", [])
            rendered = 0
            failed = 0
            output_ids = []

            for scene_params in scenes:
                scene_id_str = scene_params.get("scene_id", "")
                try:
                    # Create a sub-job for each scene
                    from database.models.animation_engine import AnimationJob
                    sub_job = AnimationJob(
                        project_id=UUID(project_id),
                        scene_id=UUID(scene_id_str) if scene_id_str else None,
                        episode_id=UUID(episode_id),
                        job_type="render_scene",
                        status="running",
                        triggered_by="episode_render",
                        params=scene_params,
                    )
                    sub_job = await repos["job"].create(sub_job)
                    await session.flush()

                    output = await comp_svc.render_scene(sub_job, scene_params)
                    output_ids.append(str(output.id))

                    sub_job.status = "completed"
                    await session.flush()
                    rendered += 1
                except Exception as exc:
                    logger.warning(f"scene_render_failed scene_id={scene_id_str} error={exc}")
                    failed += 1
                    await retry_svc.enqueue(
                        project_id=UUID(project_id),
                        reason=str(exc),
                        scene_id=UUID(scene_id_str) if scene_id_str else None,
                        episode_id=UUID(episode_id),
                        original_job_id=job.id,
                        params=scene_params,
                    )

            duration = round(time.time() - start, 2)
            result = {
                "job_id": job_id,
                "episode_id": episode_id,
                "scenes_rendered": rendered,
                "scenes_failed": failed,
                "output_ids": output_ids,
                "duration_seconds": duration,
                "status": "completed" if failed == 0 else "partial",
            }

            await job_svc.complete_job(job.id, result)
            logger.info(f"render_episode_complete job_id={job_id} rendered={rendered} failed={failed}")
            return result

        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _process_animation_retry_queue_core(job_id: str, project_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(repos)
        job_svc = svcs["job"]
        retry_svc = svcs["retry"]
        comp_svc = svcs["composition"]

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
                    from database.models.animation_engine import AnimationJob
                    retry_job = AnimationJob(
                        project_id=UUID(project_id),
                        scene_id=entry.scene_id,
                        episode_id=entry.episode_id,
                        job_type="render_scene",
                        status="running",
                        triggered_by="retry_queue",
                        params=retry_svc.get_retry_params(entry),
                    )
                    retry_job = await repos["job"].create(retry_job)
                    await session.flush()

                    await comp_svc.render_scene(retry_job, retry_svc.get_retry_params(entry))
                    await retry_svc.mark_resolved(entry)
                    resolved += 1
                except Exception as exc:
                    logger.warning(f"animation_retry_failed entry_id={entry.id} error={exc}")
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

class BaseAnimationTask(celery_app.Task):  # type: ignore[misc]
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"task_failed task={self.name} task_id={task_id} error={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        result_keys = list(retval.keys()) if isinstance(retval, dict) else []
        logger.info(f"task_success task={self.name} result_keys={result_keys}")


@celery_app.task(
    bind=True, base=BaseAnimationTask, name="animation.render_scene",
    queue="render", max_retries=3, default_retry_delay=30,
)
def render_scene_task(self, job_id: str, scene_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_render_scene_core(job_id, scene_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id, scene_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseAnimationTask, name="animation.render_episode",
    queue="render", max_retries=2, default_retry_delay=60,
)
def render_episode_task(self, job_id: str, episode_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_render_episode_core(job_id, episode_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseAnimationTask, name="animation.process_retry_queue",
    queue="default", max_retries=2, default_retry_delay=60,
)
def process_animation_retry_queue_task(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_process_animation_retry_queue_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise
