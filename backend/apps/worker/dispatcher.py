"""
TaskDispatcher — production-ready Celery dispatch with synchronous fallback.

Design contract:
  - Callers always call `dispatcher.dispatch(task_name, **kwargs)` — they never
    care whether execution is async (Celery) or sync (fallback).
  - When Redis / the Celery broker is available:  task is dispatched to the queue.
  - When the broker is unavailable:               task logic runs synchronously in
    the current process, preserving all interfaces.
  - Enabling Redis later requires ONLY a configuration change — zero code refactoring.

Each Celery task module must expose a `_<task>_core(**kwargs) -> dict` coroutine
alongside the @celery_app.task decorator. The dispatcher calls either path.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger()

_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")

# Module-level cache: None = not yet probed, True/False = known
_broker_available: bool | None = None


async def _probe_broker() -> bool:
    """Non-destructive Redis ping to determine broker reachability."""
    global _broker_available
    if _broker_available is not None:
        return _broker_available
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(_BROKER_URL, socket_connect_timeout=1, socket_timeout=1)
        await r.ping()
        await r.close()
        _broker_available = True
        logger.info("dispatcher_mode", mode="async", broker=_BROKER_URL)
    except Exception:
        _broker_available = False
        logger.warning("dispatcher_mode", mode="sync_fallback", reason="broker_unreachable")
    return _broker_available


def _run_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run an async coroutine synchronously — safe inside and outside an event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


class TaskDispatcher:
    """
    Singleton dispatcher. Inject via FastAPI DI or call get_dispatcher() directly.

    Usage
    -----
        from apps.worker.dispatcher import get_dispatcher

        dispatcher = get_dispatcher()
        result = await dispatcher.dispatch(
            celery_task=si_generate_episode_task,
            core_coro_factory=lambda: _generate_episode_core(episode_id=..., ...),
            job_id="...",
            queue="ai",
        )
    """

    async def dispatch(
        self,
        *,
        celery_task: Any,                          # @celery_app.task decorated function
        core_coro_factory: Callable[[], Coroutine[Any, Any, dict]],
        job_id: str | None = None,
        queue: str = "ai",
        task_kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Dispatch a task.  Returns immediately with {task_id, mode, ...}.
        If mode=='sync' the 'result' key contains the complete output.
        """
        available = await _probe_broker()
        generated_job_id = job_id or str(uuid.uuid4())

        if available:
            try:
                kw = task_kwargs or {}
                async_result = celery_task.apply_async(
                    kwargs={**kw, "job_id": generated_job_id},
                    queue=queue,
                )
                return {
                    "job_id": generated_job_id,
                    "task_id": async_result.id,
                    "mode": "async",
                    "status": "pending",
                }
            except Exception as exc:
                logger.error("celery_dispatch_failed", error=str(exc), fallback=True)
                # fall through to sync fallback

        # Synchronous fallback
        logger.info("dispatcher_sync_fallback", job_id=generated_job_id)
        try:
            result = await core_coro_factory()
            return {
                "job_id": generated_job_id,
                "task_id": generated_job_id,
                "mode": "sync",
                "status": "completed",
                "result": result,
            }
        except Exception as exc:
            logger.error("dispatcher_sync_error", job_id=generated_job_id, error=str(exc))
            return {
                "job_id": generated_job_id,
                "task_id": generated_job_id,
                "mode": "sync",
                "status": "failed",
                "error": str(exc),
            }

    def reset_probe_cache(self) -> None:
        """Force re-probe on the next dispatch call. Useful in tests."""
        global _broker_available
        _broker_available = None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_dispatcher: TaskDispatcher | None = None


def get_dispatcher() -> TaskDispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = TaskDispatcher()
    return _dispatcher
