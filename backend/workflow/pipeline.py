"""
Pipeline — the ordered sequence of steps that make up a workflow.

Design:
- Steps are added once at build time (or via StepRegistry).
- Pipeline.run() executes them in order, updating WorkflowContext as it goes.
- Failed (non-retryable) steps halt the pipeline unless the step is marked optional.
- Steps that already completed (ctx.completed_steps) are skipped — resume support.
"""
from __future__ import annotations

from typing import Any

import structlog

from workflow.context import WorkflowContext, WorkflowState
from workflow.progress import ProgressTracker
from workflow.state_machine import WorkflowStateMachine
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class Pipeline:
    """
    Ordered collection of steps.
    Construct via Pipeline.builder() or pass steps directly.
    """

    def __init__(
        self,
        steps: list[BaseStep],
        tracker: ProgressTracker | None = None,
        state_machine: WorkflowStateMachine | None = None,
        stop_on_failure: bool = True,
    ) -> None:
        self._steps = list(steps)
        self._tracker = tracker
        self._sm = state_machine or WorkflowStateMachine()
        self._stop_on_failure = stop_on_failure

    @classmethod
    def builder(cls) -> "PipelineBuilder":
        return PipelineBuilder()

    @property
    def step_names(self) -> list[str]:
        return [s.name for s in self._steps]

    def add_step(self, step: BaseStep) -> None:
        """Append a step without rebuilding the pipeline."""
        self._steps.append(step)

    async def run(self, ctx: WorkflowContext) -> WorkflowContext:
        """
        Execute all steps in order.
        Updates ctx.state and emits progress events along the way.
        Returns the final context (mutated in place).
        """
        total = len(self._steps)
        ctx.state = self._sm.transition(ctx.state, "start")
        await self._emit(ctx, "", 0.0, "Pipeline started")

        for idx, step in enumerate(self._steps):
            base_pct = (idx / total) * 100.0
            end_pct = ((idx + 1) / total) * 100.0
            ctx.current_step = step.name

            await self._emit(ctx, step.name, base_pct, f"Starting: {step.description}")
            logger.info("step_started", step=step.name, run_id=ctx.run_id)

            result: StepResult = await step.run(ctx)

            if result.success:
                ctx.set_step_result(step.name, result.output)
                ctx.mark_step_complete(step.name)
                await self._emit(ctx, step.name, end_pct, f"Completed: {step.description}")
                logger.info(
                    "step_completed",
                    step=step.name,
                    run_id=ctx.run_id,
                    duration=result.duration_seconds,
                    retries=result.retry_count,
                )
            else:
                ctx.mark_step_failed(step.name, result.error or "unknown error")
                await self._emit(
                    ctx, step.name, base_pct, f"Failed: {step.description} — {result.error}", status="failed"
                )
                logger.error(
                    "step_failed",
                    step=step.name,
                    run_id=ctx.run_id,
                    error=result.error,
                )
                if self._stop_on_failure:
                    ctx.state = self._sm.transition(ctx.state, "fail")
                    return ctx

        ctx.state = self._sm.transition(ctx.state, "complete")
        ctx.progress_percent = 100.0
        ctx.progress_message = "Workflow completed successfully"
        await self._emit(ctx, "done", 100.0, "All steps completed", status="completed")
        logger.info("pipeline_completed", run_id=ctx.run_id)
        return ctx

    async def _emit(
        self,
        ctx: WorkflowContext,
        step: str,
        percent: float,
        message: str,
        status: str = "running",
    ) -> None:
        ctx.progress_percent = percent
        ctx.progress_message = message
        if self._tracker:
            await self._tracker.publish(ctx.run_id, step, percent, message, status=status)


class PipelineBuilder:
    """Fluent builder for constructing pipelines."""

    def __init__(self) -> None:
        self._steps: list[BaseStep] = []
        self._tracker: ProgressTracker | None = None
        self._stop_on_failure: bool = True

    def add(self, step: BaseStep) -> "PipelineBuilder":
        self._steps.append(step)
        return self

    def with_tracker(self, tracker: ProgressTracker) -> "PipelineBuilder":
        self._tracker = tracker
        return self

    def continue_on_failure(self) -> "PipelineBuilder":
        self._stop_on_failure = False
        return self

    def build(self) -> Pipeline:
        return Pipeline(
            steps=self._steps,
            tracker=self._tracker,
            stop_on_failure=self._stop_on_failure,
        )
