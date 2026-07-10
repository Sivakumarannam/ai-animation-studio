"""
Dead Letter Queue (DLQ) handler.
Tasks that exhaust all retries are routed here for inspection and alerting.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from celery.utils.log import get_task_logger

from apps.worker.main import celery_app
from apps.worker.async_utils import run_async as _run_async

logger = get_task_logger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DLQ_KEY = "dlq:failed_tasks"
DLQ_MAX_ENTRIES = 1000  # keep last N failed tasks in Redis list


@celery_app.task(
    name="dlq.dead_letter_task",
    queue="dlq",
    max_retries=0,  # DLQ tasks must never retry
    acks_late=True,
)
def dead_letter_task(
    task_name: str,
    task_args: dict[str, Any],
    error: str,
    celery_task_id: str = "",
) -> dict[str, Any]:
    """
    Persists failed task metadata to Redis for operator inspection.
    In production, extend this to send Slack/PagerDuty alerts.
    """
    entry = {
        "task_name": task_name,
        "task_args": task_args,
        "error": error,
        "celery_task_id": celery_task_id,
        "failed_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.error(f"DLQ entry: task={task_name} error={error} args={task_args}")

    # Store in Redis list (best-effort)
    async def _store():
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        try:
            await r.lpush(DLQ_KEY, json.dumps(entry))
            await r.ltrim(DLQ_KEY, 0, DLQ_MAX_ENTRIES - 1)
        finally:
            await r.aclose()

    try:
        _run_async(_store())
    except Exception as exc:
        logger.warning(f"DLQ Redis store failed: {exc}")

    return entry


@celery_app.task(
    name="dlq.list_failed",
    queue="dlq",
)
def list_failed_tasks(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent failed task entries from the DLQ."""
    async def _fetch():
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        try:
            raw_entries = await r.lrange(DLQ_KEY, 0, limit - 1)
            return [json.loads(e) for e in raw_entries]
        finally:
            await r.aclose()

    return _run_async(_fetch())


@celery_app.task(
    name="dlq.retry_failed",
    queue="default",
)
def retry_failed_task(dlq_entry_json: str) -> dict[str, Any]:
    """
    Manually re-queue a specific DLQ entry.
    Useful for operator-driven recovery after fixing a bug.
    """
    from apps.worker.tasks.workflow_tasks import run_pipeline, resume_pipeline

    entry = json.loads(dlq_entry_json)
    task_name = entry.get("task_name", "")
    task_args = entry.get("task_args", {})

    if task_name == "workflow.run_pipeline":
        result = run_pipeline.apply_async(kwargs=task_args, queue="ai")
        return {"requeued": True, "task_id": result.id}
    elif task_name == "workflow.resume_pipeline":
        result = resume_pipeline.apply_async(kwargs=task_args, queue="ai")
        return {"requeued": True, "task_id": result.id}
    else:
        return {"requeued": False, "reason": f"Unknown task: {task_name}"}