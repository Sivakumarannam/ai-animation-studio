"""
Workflow Control API router.
Prefix: /workflow

Endpoints
---------
GET    /workflow/runs                  — list runs (filter by project_id)
GET    /workflow/runs/{run_id}         — get single run status
POST   /workflow/runs                  — start a new run (dispatches Celery task)
POST   /workflow/runs/{run_id}/pause   — pause a running workflow
POST   /workflow/runs/{run_id}/resume  — resume a paused/failed workflow
POST   /workflow/runs/{run_id}/cancel  — cancel a running or paused workflow
DELETE /workflow/runs/{run_id}         — delete a terminal-state workflow run
"""
from __future__ import annotations

import os
import uuid as _uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.api.dependencies import CurrentUser

logger = structlog.get_logger()

router = APIRouter(prefix="/workflow", tags=["workflow"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class WorkflowStartRequest(BaseModel):
    story_id: str
    project_id: str
    plugin_id: str = "default"
    settings: dict[str, Any] = {}


class WorkflowRunResponse(BaseModel):
    run_id: str
    story_id: str
    project_id: str
    user_id: str
    plugin_id: str
    state: str
    current_step: str
    completed_steps: list[str]
    failed_steps: list[str]
    errors: dict[str, str]
    progress_percent: float
    progress_message: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any]

    class Config:
        extra = "allow"


class WorkflowStartResponse(BaseModel):
    run_id: str
    state: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# DI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_executor():
    from workflow.executor import WorkflowExecutor
    return WorkflowExecutor(redis_url=REDIS_URL)


# ─────────────────────────────────────────────────────────────────────────────
# List runs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/runs", response_model=list[WorkflowRunResponse])
async def list_runs(
    current_user: CurrentUser,
    project_id: Annotated[str | None, Query(description="Filter runs by project_id")] = None,
) -> list[dict]:
    """
    Return all workflow runs from Redis, optionally filtered by project_id.
    Results are sorted newest-first.
    """
    executor = _build_executor()
    try:
        return await executor.list_runs(project_id=project_id)
    finally:
        await executor.close()


# ─────────────────────────────────────────────────────────────────────────────
# Get single run
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_run(
    run_id: str,
    current_user: CurrentUser,
) -> dict:
    """Return the current status of a workflow run."""
    executor = _build_executor()
    try:
        result = await executor.get_status(run_id)
        if result is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"No workflow run found with run_id={run_id}"},
            )
        return result
    finally:
        await executor.close()


# ─────────────────────────────────────────────────────────────────────────────
# Start a new run
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/runs", response_model=WorkflowStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_run(
    body: WorkflowStartRequest,
    current_user: CurrentUser,
) -> dict:
    """
    Start a new workflow pipeline run.

    Generates a run_id, persists a PENDING context to Redis immediately so the
    caller can poll status, then dispatches the Celery task asynchronously.
    Returns the run_id for subsequent status polling.
    """
    from workflow.context import WorkflowContext
    from apps.worker.tasks.workflow_tasks import run_pipeline

    run_id = str(_uuid.uuid4())

    # Persist initial PENDING context to Redis so GET /runs/{run_id} works immediately
    executor = _build_executor()
    try:
        ctx = WorkflowContext(
            story_id=body.story_id,
            project_id=body.project_id,
            user_id=str(current_user.id),
            plugin_id=body.plugin_id,
            settings=body.settings,
            run_id=run_id,
        )
        await executor._save_context(ctx)
    finally:
        await executor.close()

    # Dispatch Celery task
    run_pipeline.apply_async(
        kwargs={
            "story_id": body.story_id,
            "project_id": body.project_id,
            "user_id": str(current_user.id),
            "plugin_id": body.plugin_id,
            "settings": body.settings,
            "run_id": run_id,
        },
        queue="ai",
    )

    logger.info("workflow_run_dispatched", run_id=run_id, story_id=body.story_id)
    return {"run_id": run_id, "state": "pending", "message": "Workflow pipeline queued"}


# ─────────────────────────────────────────────────────────────────────────────
# Pause
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/runs/{run_id}/pause", response_model=WorkflowRunResponse)
async def pause_run(
    run_id: str,
    current_user: CurrentUser,
) -> dict:
    """
    Request a pause for a RUNNING workflow.
    The pipeline detects the pause signal at the next clean step boundary.
    """
    from packages.core.exceptions import AppError
    executor = _build_executor()
    try:
        ctx = await executor.pause(run_id)
        return ctx.to_dict()
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
    finally:
        await executor.close()


# ─────────────────────────────────────────────────────────────────────────────
# Resume
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/runs/{run_id}/resume", status_code=status.HTTP_202_ACCEPTED)
async def resume_run(
    run_id: str,
    current_user: CurrentUser,
) -> dict:
    """
    Resume a PAUSED or FAILED workflow.
    Dispatches a Celery task that will skip already-completed steps.
    """
    from apps.worker.tasks.workflow_tasks import resume_pipeline

    # Validate the run exists and is resumable before dispatching
    executor = _build_executor()
    try:
        ctx_dict = await executor.get_status(run_id)
        if ctx_dict is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"No workflow run found with run_id={run_id}"},
            )
        state = ctx_dict.get("state", "")
        if state not in ("paused", "failed"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": f"Cannot resume a run in state='{state}'. Only paused/failed runs can be resumed."},
            )
    finally:
        await executor.close()

    resume_pipeline.apply_async(kwargs={"run_id": run_id}, queue="ai")
    logger.info("workflow_resume_dispatched", run_id=run_id)
    return {"run_id": run_id, "state": state, "message": "Resume dispatched"}


# ─────────────────────────────────────────────────────────────────────────────
# Cancel
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/runs/{run_id}/cancel", response_model=WorkflowRunResponse)
async def cancel_run(
    run_id: str,
    current_user: CurrentUser,
) -> dict:
    """
    Cancel a RUNNING or PAUSED workflow.
    In-flight Celery tasks detect the CANCELLED state at the next step boundary.
    """
    executor = _build_executor()
    try:
        ctx = await executor.cancel(run_id)
        return ctx.to_dict()
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
    finally:
        await executor.close()


# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_run(
    run_id: str,
    current_user: CurrentUser,
) -> None:
    """
    Permanently delete a workflow run from Redis.
    Only allowed for terminal states (COMPLETED, CANCELLED, FAILED).
    Raises 400 if the run is still RUNNING or PAUSED — cancel it first.
    """
    executor = _build_executor()
    try:
        await executor.delete(run_id)
    except ValueError as exc:
        # HTTPException avoids returning a body on the 204 route
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    finally:
        await executor.close()
