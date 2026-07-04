"""
BaseStep — the abstract base class every workflow step extends.

Open/Closed Principle: add a new step by creating a subclass.
The Pipeline never needs to change.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog

from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy

logger = structlog.get_logger()


@dataclass
class StepResult:
    """Returned by every step upon completion."""
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_seconds: float = 0.0
    retry_count: int = 0


class BaseStep(ABC):
    """
    Abstract workflow step.

    Subclasses implement execute() only.
    Retry, logging, progress, and error handling are handled by the engine.
    """

    # Override in subclasses to customise retry behaviour
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy.fast)  # type: ignore[assignment]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Each subclass can declare its own retry_policy as a class attribute
        if not hasattr(cls, "retry_policy"):
            cls.retry_policy = RetryPolicy.fast()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique step identifier used as the key in context.step_results."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description shown in progress messages."""
        return self.name.replace("_", " ").title()

    @abstractmethod
    async def execute(self, ctx: WorkflowContext) -> StepResult:
        """
        Core logic. Must be idempotent — it may be called again on retry.
        Read inputs from ctx, write outputs back to ctx.step_results.
        """
        ...

    def can_skip(self, ctx: WorkflowContext) -> bool:
        """
        Return True if the step should be skipped because it already ran successfully.
        Default: skip if context.completed_steps contains this step's name (resume support).
        """
        return ctx.is_step_done(self.name)

    def can_retry(self, exc: Exception) -> bool:
        """Return True if this exception warrants a retry."""
        return self.retry_policy.is_retryable(exc)

    async def on_before(self, ctx: WorkflowContext) -> None:
        """Hook called before execute(). Override for pre-step setup."""

    async def on_success(self, ctx: WorkflowContext, result: StepResult) -> None:
        """Hook called after a successful execute(). Override for post-step cleanup."""

    async def on_failure(self, ctx: WorkflowContext, exc: Exception, attempt: int) -> None:
        """Hook called after each failed attempt (before retry or giving up)."""
        logger.warning(
            "step_attempt_failed",
            step=self.name,
            attempt=attempt,
            error=str(exc),
        )

    async def run(self, ctx: WorkflowContext) -> StepResult:
        """
        Called by the Pipeline. Wraps execute() with retry, timing, and hooks.
        Do not override this method — override execute() instead.
        """
        from workflow.retry import retry_async

        if self.can_skip(ctx):
            logger.info("step_skipped", step=self.name, reason="already_completed")
            return StepResult(success=True, output=ctx.get_step_result(self.name, {}))

        await self.on_before(ctx)
        start = time.monotonic()
        attempt_count = 0

        async def _attempt() -> StepResult:
            nonlocal attempt_count
            attempt_count += 1
            return await self.execute(ctx)

        async def _on_retry(attempt: int, exc: Exception, delay: float) -> None:
            await self.on_failure(ctx, exc, attempt)

        try:
            result = await retry_async(
                _attempt,
                policy=self.retry_policy,
                on_retry=_on_retry,
            )
            result.duration_seconds = time.monotonic() - start
            result.retry_count = attempt_count - 1
            await self.on_success(ctx, result)
            return result
        except Exception as exc:
            duration = time.monotonic() - start
            return StepResult(
                success=False,
                error=str(exc),
                duration_seconds=duration,
                retry_count=attempt_count - 1,
            )
