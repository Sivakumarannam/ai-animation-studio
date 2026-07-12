"""
Celery tasks that drive the Workflow Engine.
These tasks are thin wrappers — business logic lives in the engine, not here.

Task hierarchy
--------------
run_pipeline          → executes a full WorkflowContext from scratch
resume_pipeline       → resumes a failed/paused run by run_id
run_single_step       → executes exactly one named step (for targeted retries)
"""
from __future__ import annotations


import os
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger
from apps.worker.async_utils import run_async as _run_async

from apps.worker.main import celery_app

logger = get_task_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# ---------------------------------------------------------------------------
# Helper — run async code from a sync Celery task
# ---------------------------------------------------------------------------



def _build_executor():
    """Lazy import to avoid circular deps at module load time."""
    from workflow.executor import WorkflowExecutor
    return WorkflowExecutor(redis_url=REDIS_URL)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="workflow.run_pipeline",
    queue="ai",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def run_pipeline(
    self: Task,
    story_id: str,
    project_id: str,
    user_id: str,
    plugin_id: str,
    settings: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Start a full generation pipeline for a story.

    Parameters
    ----------
    story_id, project_id, user_id, plugin_id:
        Identity fields stored in WorkflowContext.
    settings:
        Arbitrary generation settings (scene_count, language, image_style, …).

    Returns the final WorkflowContext serialised as a dict.
    """
    logger.info(f"run_pipeline start story_id={story_id} task_id={self.request.id}")

    async def _execute():
        from workflow.context import WorkflowContext
        ctx = WorkflowContext(
            story_id=story_id,
            project_id=project_id,
            user_id=user_id,
            plugin_id=plugin_id,
            settings=settings,
            run_id=run_id,  # Use API-provided run_id when given (enables immediate status polling)
        )
        executor = _build_executor()
        try:
            result = await executor.execute(ctx)
            return result.to_dict()
        finally:
            await executor.close()

    try:
        return _run_async(_execute())
    except Exception as exc:
        logger.error(f"run_pipeline failed story_id={story_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            # Route to DLQ after exhausting retries
            dead_letter_task.apply_async(
                kwargs={
                    "task_name": "workflow.run_pipeline",
                    "task_args": {"story_id": story_id, "plugin_id": plugin_id},
                    "error": str(exc),
                },
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="workflow.resume_pipeline",
    queue="ai",
    max_retries=1,
    acks_late=True,
)
def resume_pipeline(self: Task, run_id: str) -> dict[str, Any]:
    """
    Resume an interrupted pipeline by run_id.
    Completed steps are skipped; failed/pending steps are re-executed.
    """
    logger.info(f"resume_pipeline run_id={run_id}")

    async def _resume():
        executor = _build_executor()
        try:
            ctx = await executor.resume(run_id)
            return ctx.to_dict()
        finally:
            await executor.close()

    try:
        return _run_async(_resume())
    except Exception as exc:
        logger.error(f"resume_pipeline failed run_id={run_id} error={exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(
    bind=True,
    name="workflow.run_single_step",
    queue="ai",
    max_retries=3,
    acks_late=True,
)
def run_single_step(
    self: Task,
    run_id: str,
    step_name: str,
) -> dict[str, Any]:
    """
    Execute a single named step against an existing WorkflowContext.
    Used for targeted retries from the UI without re-running the full pipeline.
    """
    logger.info(f"run_single_step run_id={run_id} step={step_name}")

    async def _run_step():
        from workflow.executor import WorkflowExecutor
        from workflow.context import WorkflowState

        executor = WorkflowExecutor(redis_url=REDIS_URL)
        try:
            ctx = await executor._load_context(run_id)
            if ctx is None:
                raise ValueError(f"No context for run_id={run_id}")

            # Remove the step from completed so it re-runs
            if step_name in ctx.completed_steps:
                ctx.completed_steps.remove(step_name)
            if step_name in ctx.failed_steps:
                ctx.failed_steps.remove(step_name)

            # Build step instance from registry
            from workflow.registry import get_step_registry
            registry = get_step_registry()
            steps = registry.build_ordered_steps()
            target = next((s for s in steps if s.name == step_name), None)
            if target is None:
                raise ValueError(f"Step '{step_name}' not found in registry")

            result = await target.run(ctx)
            if result.success:
                ctx.set_step_result(step_name, result.output)
                ctx.mark_step_complete(step_name)
            else:
                ctx.mark_step_failed(step_name, result.error or "unknown")

            await executor._save_context(ctx)
            return {"run_id": run_id, "step": step_name, "success": result.success, "error": result.error}
        finally:
            await executor.close()

    try:
        return _run_async(_run_step())
    except Exception as exc:
        logger.error(f"run_single_step failed run_id={run_id} step={step_name} error={exc}")
        raise self.retry(exc=exc, countdown=15)


# ---------------------------------------------------------------------------
# Pause / Cancel Celery wrappers
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="workflow.pause_run",
    queue="default",
    max_retries=1,
    acks_late=True,
)
def pause_run(self: Task, run_id: str) -> dict[str, Any]:
    """
    Thin Celery wrapper for WorkflowExecutor.pause().
    Sets run state to PAUSED in Redis; the in-flight pipeline detects this at
    the next step boundary via the state_refresher hook.
    """
    logger.info(f"pause_run run_id={run_id}")

    async def _pause():
        executor = _build_executor()
        try:
            ctx = await executor.pause(run_id)
            return ctx.to_dict()
        finally:
            await executor.close()

    try:
        return _run_async(_pause())
    except Exception as exc:
        logger.error(f"pause_run failed run_id={run_id} error={exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(
    bind=True,
    name="workflow.cancel_run",
    queue="default",
    max_retries=1,
    acks_late=True,
)
def cancel_run(self: Task, run_id: str) -> dict[str, Any]:
    """
    Thin Celery wrapper for WorkflowExecutor.cancel().
    Sets run state to CANCELLED in Redis; any in-flight Celery task will detect
    this at the next step boundary and exit cleanly.
    """
    logger.info(f"cancel_run run_id={run_id}")

    async def _cancel():
        executor = _build_executor()
        try:
            ctx = await executor.cancel(run_id)
            return ctx.to_dict()
        finally:
            await executor.close()

    try:
        return _run_async(_cancel())
    except Exception as exc:
        logger.error(f"cancel_run failed run_id={run_id} error={exc}")
        raise self.retry(exc=exc, countdown=5)


# Import here to avoid circular reference issues
from apps.worker.tasks.dead_letter import dead_letter_task  # noqa: E402
