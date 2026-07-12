"""
Tests for WorkflowExecutor pause / cancel / delete and the Pipeline interrupt
mechanism (state_refresher hook), plus a resume-skips-completed-steps check.

All Redis interactions are mocked so these tests run without a live Redis instance.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from workflow.context import WorkflowContext, WorkflowState
from workflow.executor import WorkflowExecutor, _DELETABLE_STATES
from workflow.pipeline import Pipeline, PipelineBuilder
from workflow.retry import RetryPolicy
from workflow.state_machine import WorkflowStateMachine, InvalidTransitionError
from workflow.step import BaseStep, StepResult


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_ctx(**kwargs) -> WorkflowContext:
    return WorkflowContext(
        story_id=kwargs.get("story_id", str(uuid.uuid4())),
        project_id=kwargs.get("project_id", str(uuid.uuid4())),
        user_id=kwargs.get("user_id", str(uuid.uuid4())),
        plugin_id=kwargs.get("plugin_id", "test_plugin"),
        settings=kwargs.get("settings", {}),
        run_id=kwargs.get("run_id", str(uuid.uuid4())),
    )


def _make_executor(store: dict[str, str] | None = None) -> WorkflowExecutor:
    """
    Build an executor whose Redis client is a mock.
    The caller-provided `store` dict is used directly (not copied) so that
    tests can inspect or modify it after executor operations.
    """
    if store is None:
        store = {}

    executor = WorkflowExecutor.__new__(WorkflowExecutor)
    executor._redis_url = "redis://mock"
    executor._registry = MagicMock()
    executor._registry.build_ordered_steps.return_value = []
    executor._tracker = None
    executor._sm = WorkflowStateMachine()

    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(side_effect=lambda k: store.get(k))
    redis_mock.setex = AsyncMock(side_effect=lambda k, ttl, v: store.update({k: v}))
    redis_mock.delete = AsyncMock(side_effect=lambda k: store.pop(k, None))
    redis_mock.keys = AsyncMock(return_value=list(store.keys()))
    redis_mock.aclose = AsyncMock()
    executor._redis = redis_mock

    return executor


def _ctx_key(run_id: str) -> str:
    from workflow.executor import _CTX_KEY_PREFIX
    return f"{_CTX_KEY_PREFIX}{run_id}"


# ─── Test step implementations ────────────────────────────────────────────────
# Each test step must explicitly declare `retry_policy` because BaseStep defines
# it as a dataclasses.Field class attribute (for type hints in a non-dataclass),
# which means `hasattr(cls, "retry_policy")` is True for every subclass and
# __init_subclass__ never runs the fallback assignment.

class _OkStep(BaseStep):
    """A step that always succeeds."""
    retry_policy = RetryPolicy.fast()  # explicit — see note above

    @property
    def name(self) -> str:
        return "ok_step"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        return StepResult(success=True, output={"done": True})


class _FailStep(BaseStep):
    """A step that always fails."""
    retry_policy = RetryPolicy.none()  # no retries — fail immediately

    @property
    def name(self) -> str:
        return "fail_step"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        return StepResult(success=False, error="intentional failure")


# ─── State machine ────────────────────────────────────────────────────────────

class TestStateMachine:
    def test_running_to_paused(self):
        sm = WorkflowStateMachine()
        assert sm.transition(WorkflowState.RUNNING, "pause") == WorkflowState.PAUSED

    def test_running_to_cancelled(self):
        sm = WorkflowStateMachine()
        assert sm.transition(WorkflowState.RUNNING, "cancel") == WorkflowState.CANCELLED

    def test_paused_to_cancelled(self):
        sm = WorkflowStateMachine()
        assert sm.transition(WorkflowState.PAUSED, "cancel") == WorkflowState.CANCELLED

    def test_paused_to_running(self):
        sm = WorkflowStateMachine()
        assert sm.transition(WorkflowState.PAUSED, "resume") == WorkflowState.RUNNING

    def test_invalid_transition_raises(self):
        sm = WorkflowStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(WorkflowState.COMPLETED, "pause")

    def test_pending_to_cancelled(self):
        sm = WorkflowStateMachine()
        assert sm.transition(WorkflowState.PENDING, "cancel") == WorkflowState.CANCELLED


# ─── Executor.pause() ─────────────────────────────────────────────────────────

class TestExecutorPause:
    def test_pause_transitions_running_to_paused(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.RUNNING
        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        result = asyncio.run(executor.pause(ctx.run_id))

        assert result.state == WorkflowState.PAUSED

    def test_pause_persists_to_redis(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.RUNNING
        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        asyncio.run(executor.pause(ctx.run_id))

        # store is the live dict — setex side-effect updates it in-place
        persisted = json.loads(store[_ctx_key(ctx.run_id)])
        assert persisted["state"] == "paused"

    def test_pause_raises_if_not_running(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.COMPLETED
        executor = _make_executor({_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())})

        with pytest.raises(Exception):  # InvalidTransitionError
            asyncio.run(executor.pause(ctx.run_id))

    def test_pause_raises_if_run_not_found(self):
        executor = _make_executor()
        with pytest.raises(ValueError, match="No workflow context"):
            asyncio.run(executor.pause("nonexistent-run-id"))


# ─── Executor.cancel() ────────────────────────────────────────────────────────

class TestExecutorCancel:
    def test_cancel_running(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.RUNNING
        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        result = asyncio.run(executor.cancel(ctx.run_id))
        assert result.state == WorkflowState.CANCELLED

    def test_cancel_paused(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.PAUSED
        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        result = asyncio.run(executor.cancel(ctx.run_id))
        assert result.state == WorkflowState.CANCELLED

    def test_cancel_pending(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.PENDING
        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        result = asyncio.run(executor.cancel(ctx.run_id))
        assert result.state == WorkflowState.CANCELLED

    def test_cancel_persists_to_redis(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.RUNNING
        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        asyncio.run(executor.cancel(ctx.run_id))

        persisted = json.loads(store[_ctx_key(ctx.run_id)])
        assert persisted["state"] == "cancelled"

    def test_cancel_raises_if_run_not_found(self):
        executor = _make_executor()
        with pytest.raises(ValueError, match="No workflow context"):
            asyncio.run(executor.cancel("nonexistent"))

    def test_cancel_raises_on_completed(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.COMPLETED
        executor = _make_executor({_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())})

        with pytest.raises(Exception):  # InvalidTransitionError
            asyncio.run(executor.cancel(ctx.run_id))


# ─── Executor.delete() ────────────────────────────────────────────────────────

class TestExecutorDelete:
    @pytest.mark.parametrize("state", [
        WorkflowState.COMPLETED,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    ])
    def test_delete_allowed_for_terminal_states(self, state: WorkflowState):
        ctx = _make_ctx()
        ctx.state = state
        key = _ctx_key(ctx.run_id)
        store = {key: json.dumps(ctx.to_dict())}
        executor = _make_executor(store)

        asyncio.run(executor.delete(ctx.run_id))

        assert key not in store  # live store confirms deletion

    @pytest.mark.parametrize("state", [
        WorkflowState.RUNNING,
        WorkflowState.PAUSED,
        WorkflowState.PENDING,
    ])
    def test_delete_raises_for_non_terminal_states(self, state: WorkflowState):
        ctx = _make_ctx()
        ctx.state = state
        executor = _make_executor({_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())})

        with pytest.raises(ValueError, match="Cannot delete"):
            asyncio.run(executor.delete(ctx.run_id))

    def test_delete_raises_if_run_not_found(self):
        executor = _make_executor()
        with pytest.raises(ValueError, match="No workflow context"):
            asyncio.run(executor.delete("nonexistent"))

    def test_deletable_states_constant(self):
        assert WorkflowState.COMPLETED in _DELETABLE_STATES
        assert WorkflowState.CANCELLED in _DELETABLE_STATES
        assert WorkflowState.FAILED in _DELETABLE_STATES
        assert WorkflowState.RUNNING not in _DELETABLE_STATES
        assert WorkflowState.PAUSED not in _DELETABLE_STATES


# ─── Pipeline interrupt (pause/cancel at step boundary) ───────────────────────

class TestPipelineInterrupt:
    """
    Verify the pipeline's state_refresher hook causes it to halt at step boundaries
    when pause or cancel has been written to Redis externally.

    No executor or Redis is involved here — the refresher directly mutates ctx.state
    to simulate the signal an external pause/cancel would write to Redis.
    """

    def test_pipeline_halts_on_paused_state(self):
        """
        If state_refresher sets ctx.state = PAUSED before the first step,
        the pipeline should return immediately without running any steps.
        """
        ctx = _make_ctx()
        ctx.state = WorkflowState.PENDING

        async def _refresher():
            ctx.state = WorkflowState.PAUSED  # simulate external pause signal

        pipeline = (
            Pipeline.builder()
            .add(_OkStep())
            .with_state_refresher(_refresher)
            .build()
        )

        result = asyncio.run(pipeline.run(ctx))

        assert result.state == WorkflowState.PAUSED
        assert "ok_step" not in result.completed_steps

    def test_pipeline_halts_on_cancelled_state(self):
        ctx = _make_ctx()
        ctx.state = WorkflowState.PENDING

        async def _refresher():
            ctx.state = WorkflowState.CANCELLED  # simulate external cancel

        pipeline = (
            Pipeline.builder()
            .add(_OkStep())
            .with_state_refresher(_refresher)
            .build()
        )

        result = asyncio.run(pipeline.run(ctx))

        assert result.state == WorkflowState.CANCELLED
        assert "ok_step" not in result.completed_steps

    def test_pipeline_runs_fully_without_interrupt(self):
        """Without pause/cancel, the pipeline completes normally."""
        ctx = _make_ctx()
        ctx.state = WorkflowState.PENDING

        async def _noop_refresher():
            pass  # never changes state

        pipeline = (
            Pipeline.builder()
            .add(_OkStep())
            .with_state_refresher(_noop_refresher)
            .build()
        )

        result = asyncio.run(pipeline.run(ctx))

        assert result.state == WorkflowState.COMPLETED
        assert "ok_step" in result.completed_steps

    def test_pipeline_without_refresher_runs_normally(self):
        """Pipeline without a state_refresher still works (backward-compat)."""
        ctx = _make_ctx()
        ctx.state = WorkflowState.PENDING

        pipeline = Pipeline.builder().add(_OkStep()).build()
        result = asyncio.run(pipeline.run(ctx))

        assert result.state == WorkflowState.COMPLETED

    def test_pause_detected_between_steps(self):
        """
        Pause is only requested after the first step completes.
        The pipeline should complete step 1, detect pause, then halt before step 2.
        """
        ctx = _make_ctx()
        ctx.state = WorkflowState.PENDING
        call_count = 0

        class _TrackStep(BaseStep):
            retry_policy = RetryPolicy.fast()  # must be explicit — see note at top

            def __init__(self, step_name: str, tracker: list[str]):
                self._sname = step_name
                self._tracker = tracker

            @property
            def name(self) -> str:
                return self._sname

            async def execute(self, exc_ctx: WorkflowContext) -> StepResult:
                self._tracker.append(self._sname)
                return StepResult(success=True)

        completed: list[str] = []
        step1 = _TrackStep("step_one", completed)
        step2 = _TrackStep("step_two", completed)

        async def _refresher():
            nonlocal call_count
            call_count += 1
            # Only inject PAUSED on the 2nd refresh (before step 2)
            if call_count >= 2:
                ctx.state = WorkflowState.PAUSED

        pipeline = (
            Pipeline.builder()
            .add(step1)
            .add(step2)
            .with_state_refresher(_refresher)
            .build()
        )
        result = asyncio.run(pipeline.run(ctx))

        assert result.state == WorkflowState.PAUSED
        assert "step_one" in result.completed_steps
        assert "step_two" not in result.completed_steps
        assert completed == ["step_one"]  # step_two.execute() was never called


# ─── Resume skips completed steps ─────────────────────────────────────────────

class TestResumeSkipsCompletedSteps:
    """
    Confirm executor.resume() correctly skips steps already in completed_steps.
    This verifies the existing resume() behavior is not broken by the new changes.
    """

    def test_resume_skips_steps_already_in_completed(self):
        """
        A context with completed_steps=['step_one'] should skip step_one when resumed.
        """
        step_one_calls: list[str] = []
        step_two_calls: list[str] = []

        class _TrackableStep(BaseStep):
            retry_policy = RetryPolicy.fast()  # must be explicit — see note at top

            def __init__(self, sname: str, tracker: list[str]):
                self._sname = sname
                self._tracker = tracker

            @property
            def name(self) -> str:
                return self._sname

            async def execute(self, exc_ctx: WorkflowContext) -> StepResult:
                self._tracker.append(self._sname)
                return StepResult(success=True)

        step_one = _TrackableStep("step_one", step_one_calls)
        step_two = _TrackableStep("step_two", step_two_calls)

        ctx = _make_ctx()
        ctx.completed_steps = ["step_one"]
        ctx.state = WorkflowState.PAUSED

        registry_mock = MagicMock()
        registry_mock.build_ordered_steps.return_value = [step_one, step_two]

        store = {_ctx_key(ctx.run_id): json.dumps(ctx.to_dict())}

        executor = WorkflowExecutor.__new__(WorkflowExecutor)
        executor._redis_url = "redis://mock"
        executor._registry = registry_mock
        executor._tracker = None
        executor._sm = WorkflowStateMachine()

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(side_effect=lambda k: store.get(k))
        redis_mock.setex = AsyncMock(side_effect=lambda k, ttl, v: store.update({k: v}))
        redis_mock.aclose = AsyncMock()
        executor._redis = redis_mock

        result = asyncio.run(executor.resume(ctx.run_id))

        # step_one was already completed — should not have run again
        assert step_one_calls == [], f"step_one should have been skipped but was called"
        # step_two was not complete — should have run
        assert step_two_calls == ["step_two"]
        assert result.state == WorkflowState.COMPLETED


# ─── Executor.list_runs() ─────────────────────────────────────────────────────

class TestListRuns:
    def test_list_runs_returns_all(self):
        ctx1 = _make_ctx(project_id="proj-A")
        ctx2 = _make_ctx(project_id="proj-B")
        store = {
            _ctx_key(ctx1.run_id): json.dumps(ctx1.to_dict()),
            _ctx_key(ctx2.run_id): json.dumps(ctx2.to_dict()),
        }
        executor = _make_executor(store)
        executor._redis.keys = AsyncMock(return_value=list(store.keys()))

        result = asyncio.run(executor.list_runs())
        assert len(result) == 2

    def test_list_runs_filters_by_project_id(self):
        ctx1 = _make_ctx(project_id="proj-A")
        ctx2 = _make_ctx(project_id="proj-B")
        store = {
            _ctx_key(ctx1.run_id): json.dumps(ctx1.to_dict()),
            _ctx_key(ctx2.run_id): json.dumps(ctx2.to_dict()),
        }
        executor = _make_executor(store)
        executor._redis.keys = AsyncMock(return_value=list(store.keys()))

        result = asyncio.run(executor.list_runs(project_id="proj-A"))
        assert len(result) == 1
        assert result[0]["project_id"] == "proj-A"

    def test_list_runs_empty_when_no_runs(self):
        executor = _make_executor()
        executor._redis.keys = AsyncMock(return_value=[])
        result = asyncio.run(executor.list_runs())
        assert result == []
