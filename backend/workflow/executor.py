"""
WorkflowExecutor — the top-level entry point for running and resuming workflows.

Responsibilities:
- Persist WorkflowContext to Redis (start, after each step, on completion/failure).
- Support resume: reload context from Redis and skip already-completed steps.
- Build the Pipeline from the StepRegistry.
- Integrate ProgressTracker.
- Expose pause(), cancel(), delete(), and list_runs() for workflow control.
"""
from __future__ import annotations

import json
from typing import Any

import structlog

from workflow.context import WorkflowContext, WorkflowState
from workflow.pipeline import Pipeline
from workflow.progress import ProgressTracker, get_progress_tracker
from workflow.registry import StepRegistry, get_step_registry
from workflow.state_machine import WorkflowStateMachine

logger = structlog.get_logger()

_CTX_KEY_PREFIX = "workflow:ctx:"
_CTX_TTL = 86400 * 7  # 7 days

_DELETABLE_STATES = {WorkflowState.COMPLETED, WorkflowState.CANCELLED, WorkflowState.FAILED}


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
        self._sm = WorkflowStateMachine()

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

    # States that may be written externally to signal the running pipeline to halt
    _CONTROL_SIGNAL_STATES = frozenset([WorkflowState.PAUSED, WorkflowState.CANCELLED])

    async def _refresh_state(self, ctx: WorkflowContext) -> None:
        """
        Re-read state from Redis and update ctx.state in-place.
        Called between pipeline steps so that an external pause/cancel is detected
        at the next clean step boundary.

        Important: only applies PAUSED or CANCELLED signals from Redis.
        We never downgrade RUNNING back to PENDING/FAILED — Redis may hold a stale
        pre-run state (PENDING) if execute() saved the context before the pipeline
        started its own PENDING→RUNNING transition.
        """
        try:
            r = await self._get_redis()
            raw = await r.get(f"{_CTX_KEY_PREFIX}{ctx.run_id}")
            if raw:
                data = json.loads(raw)
                redis_state = WorkflowState(data.get("state", ctx.state.value))
                if redis_state in self._CONTROL_SIGNAL_STATES and redis_state != ctx.state:
                    logger.info(
                        "state_refreshed",
                        run_id=ctx.run_id,
                        old_state=ctx.state.value,
                        new_state=redis_state.value,
                    )
                    ctx.state = redis_state
        except Exception:
            pass  # Never crash the pipeline on a refresh failure

    async def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        """
        Run the full pipeline for ctx.
        Persists context before starting and after every step.
        """
        await self._save_context(ctx)
        logger.info("workflow_started", run_id=ctx.run_id, story_id=ctx.story_id)

        pipeline = self._build_pipeline(ctx)
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
        Paused workflows are automatically unpaused before re-entry.
        """
        ctx = await self._load_context(run_id)
        if ctx is None:
            raise ValueError(f"No workflow context found for run_id={run_id}")

        logger.info("workflow_resuming", run_id=run_id, completed=ctx.completed_steps)
        # Reset state so the state machine allows re-entry
        if ctx.state in (WorkflowState.FAILED, WorkflowState.PAUSED):
            ctx.state = WorkflowState.PENDING

        return await self.execute(ctx)

    async def pause(self, run_id: str) -> WorkflowContext:
        """
        Request a pause for a RUNNING workflow.
        Transitions state to PAUSED and persists to Redis.
        The running pipeline will detect this at the next step boundary and halt cleanly.
        """
        ctx = await self._load_context(run_id)
        if ctx is None:
            raise ValueError(f"No workflow context found for run_id={run_id}")

        ctx.state = self._sm.transition(ctx.state, "pause")
        await self._save_context(ctx)
        logger.info("workflow_pause_requested", run_id=run_id)
        return ctx

    async def cancel(self, run_id: str) -> WorkflowContext:
        """
        Cancel a RUNNING or PAUSED workflow.
        Transitions state to CANCELLED and persists to Redis.
        In-flight Celery tasks will detect the CANCELLED state at the next step boundary
        and exit cleanly without advancing to the next step.
        """
        ctx = await self._load_context(run_id)
        if ctx is None:
            raise ValueError(f"No workflow context found for run_id={run_id}")

        ctx.state = self._sm.transition(ctx.state, "cancel")
        await self._save_context(ctx)
        logger.info("workflow_cancelled", run_id=run_id)
        return ctx

    async def delete(self, run_id: str) -> None:
        """
        Permanently delete a workflow run's Redis context and metadata.
        Only allowed when the run is in a terminal state (COMPLETED, CANCELLED, FAILED).
        Raises ValueError if the run is still RUNNING or PAUSED — cancel it first.
        """
        ctx = await self._load_context(run_id)
        if ctx is None:
            raise ValueError(f"No workflow context found for run_id={run_id}")

        if ctx.state not in _DELETABLE_STATES:
            raise ValueError(
                f"Cannot delete run in state='{ctx.state.value}'. "
                f"Cancel it first (allowed states: {[s.value for s in _DELETABLE_STATES]})"
            )

        r = await self._get_redis()
        await r.delete(f"{_CTX_KEY_PREFIX}{run_id}")
        logger.info("workflow_deleted", run_id=run_id, state=ctx.state.value)

    async def get_status(self, run_id: str) -> dict[str, Any] | None:
        """Return the latest persisted context as a dict, or None if not found."""
        ctx = await self._load_context(run_id)
        if ctx is None:
            return None
        return ctx.to_dict()

    async def list_runs(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        List all workflow runs stored in Redis, optionally filtered by project_id.
        Returns runs sorted newest-first.
        """
        try:
            r = await self._get_redis()
            keys = await r.keys(f"{_CTX_KEY_PREFIX}*")
            runs: list[dict[str, Any]] = []
            for key in keys:
                raw = await r.get(key)
                if raw:
                    try:
                        data = json.loads(raw)
                        if project_id is None or data.get("project_id") == project_id:
                            runs.append(data)
                    except Exception:
                        pass
            return sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True)
        except Exception as exc:
            logger.warning("list_runs_failed", error=str(exc))
            return []

    def _build_pipeline(self, ctx: WorkflowContext) -> Pipeline:
        """
        Build the ordered pipeline from all registered steps.

        A state_refresher closure is passed to the pipeline so it can detect
        externally-requested pause/cancel signals at each step boundary.
        """
        steps = self._registry.build_ordered_steps()
        builder = Pipeline.builder().with_tracker(self._tracker)
        for step in steps:
            builder.add(step)
        # Closure captures self + ctx so the pipeline can check Redis state
        builder.with_state_refresher(lambda: self._refresh_state(ctx))
        return builder.build()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
