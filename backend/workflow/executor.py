"""
WorkflowExecutor — the top-level entry point for running and resuming workflows.

Responsibilities:
- Persist WorkflowContext to Redis (start, after each step, on completion/failure).
- Support resume: reload context from Redis and skip already-completed steps.
- Build the Pipeline from the StepRegistry.
- Integrate ProgressTracker.
"""
from __future__ import annotations

import json
from typing import Any

import structlog

from workflow.context import WorkflowContext, WorkflowState
from workflow.pipeline import Pipeline
from workflow.progress import ProgressTracker, get_progress_tracker
from workflow.registry import StepRegistry, get_step_registry

logger = structlog.get_logger()

_CTX_KEY_PREFIX = "workflow:ctx:"
_CTX_TTL = 86400 * 7  # 7 days


class WorkflowExecutor:
    """
    Runs a workflow pipeline end-to-end, with Redis-backed persistence.

    Usage
    -----
        executor = WorkflowExecutor()
        ctx = WorkflowContext(story_id=..., project_id=..., ...)
        result = await executor.execute(ctx)
    """

    def __init__(
        self,
        registry: StepRegistry | None = None,
        tracker: ProgressTracker | None = None,
        redis_url: str = "redis://localhost:6379/0",
    ) -> None:
        self._registry = registry or get_step_registry()
        self._tracker = tracker or get_progress_tracker(redis_url)
        self._redis_url = redis_url
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def _save_context(self, ctx: WorkflowContext) -> None:
        try:
            r = await self._get_redis()
            await r.setex(
                f"{_CTX_KEY_PREFIX}{ctx.run_id}",
                _CTX_TTL,
                json.dumps(ctx.to_dict()),
            )
        except Exception as exc:
            logger.warning("context_persist_failed", run_id=ctx.run_id, error=str(exc))

    async def _load_context(self, run_id: str) -> WorkflowContext | None:
        try:
            r = await self._get_redis()
            raw = await r.get(f"{_CTX_KEY_PREFIX}{run_id}")
            if raw:
                return WorkflowContext.from_dict(json.loads(raw))
        except Exception as exc:
            logger.warning("context_load_failed", run_id=run_id, error=str(exc))
        return None

    async def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        """
        Run the full pipeline for ctx.
        Persists context before starting and after every step.
        """
        await self._save_context(ctx)
        logger.info("workflow_started", run_id=ctx.run_id, story_id=ctx.story_id)

        pipeline = self._build_pipeline()
        try:
            ctx = await pipeline.run(ctx)
        except Exception as exc:
            ctx.state = WorkflowState.FAILED
            ctx.errors["executor"] = str(exc)
            logger.error("workflow_executor_error", run_id=ctx.run_id, error=str(exc))
        finally:
            await self._save_context(ctx)

        return ctx

    async def resume(self, run_id: str) -> WorkflowContext:
        """
        Resume an interrupted workflow by reloading context from Redis.
        Completed steps are skipped; failed/pending steps are re-executed.
        """
        ctx = await self._load_context(run_id)
        if ctx is None:
            raise ValueError(f"No workflow context found for run_id={run_id}")

        logger.info("workflow_resuming", run_id=run_id, completed=ctx.completed_steps)
        # Reset state so the state machine allows re-entry
        if ctx.state in (WorkflowState.FAILED, WorkflowState.PAUSED):
            ctx.state = WorkflowState.PENDING

        return await self.execute(ctx)

    async def get_status(self, run_id: str) -> dict[str, Any] | None:
        """Return the latest persisted context as a dict, or None if not found."""
        ctx = await self._load_context(run_id)
        if ctx is None:
            return None
        return ctx.to_dict()

    def _build_pipeline(self) -> Pipeline:
        """Build the ordered pipeline from all registered steps."""
        steps = self._registry.build_ordered_steps()
        return (
            Pipeline.builder()
            .with_tracker(self._tracker)
            .build()
            if not steps
            else Pipeline.builder()
            .with_tracker(self._tracker)
            .__class__.__new__(Pipeline.builder().__class__)  # type hint workaround
        )

    def _build_pipeline(self) -> Pipeline:  # noqa: F811
        steps = self._registry.build_ordered_steps()
        builder = Pipeline.builder().with_tracker(self._tracker)
        for step in steps:
            builder.add(step)
        return builder.build()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
