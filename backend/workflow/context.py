"""
WorkflowContext — the shared state object that flows through every pipeline step.

Design rules:
- Steps READ from context to know what to do.
- Steps WRITE results back to context.step_results[step_name].
- The executor persists context snapshots to Redis for resume support.
- Never store raw SQLAlchemy models here — use plain dicts / primitives only.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkflowState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowContext:
    """
    Carries all state needed by every workflow step.
    Serialisable to / from plain dict for Redis persistence.
    """

    def __init__(
        self,
        story_id: str,
        project_id: str,
        user_id: str,
        plugin_id: str,
        settings: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> None:
        self.run_id: str = run_id or str(uuid.uuid4())
        self.story_id: str = story_id
        self.project_id: str = project_id
        self.user_id: str = user_id
        self.plugin_id: str = plugin_id
        self.settings: dict[str, Any] = settings or {}

        self.state: WorkflowState = WorkflowState.PENDING
        self.current_step: str = ""
        self.completed_steps: list[str] = []
        self.failed_steps: list[str] = []
        self.step_results: dict[str, Any] = {}
        self.errors: dict[str, str] = {}

        self.progress_percent: float = 0.0
        self.progress_message: str = "Initialising workflow…"

        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)
        self.metadata: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get_step_result(self, step_name: str, default: Any = None) -> Any:
        return self.step_results.get(step_name, default)

    def set_step_result(self, step_name: str, value: Any) -> None:
        self.step_results[step_name] = value
        self.updated_at = datetime.now(timezone.utc)

    def mark_step_complete(self, step_name: str) -> None:
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)
        self.updated_at = datetime.now(timezone.utc)

    def mark_step_failed(self, step_name: str, error: str) -> None:
        if step_name not in self.failed_steps:
            self.failed_steps.append(step_name)
        self.errors[step_name] = error
        self.updated_at = datetime.now(timezone.utc)

    def is_step_done(self, step_name: str) -> bool:
        return step_name in self.completed_steps

    # ------------------------------------------------------------------
    # Serialisation (for Redis persistence)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "story_id": self.story_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "plugin_id": self.plugin_id,
            "settings": self.settings,
            "state": self.state.value,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "step_results": self.step_results,
            "errors": self.errors,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowContext":
        ctx = cls(
            story_id=data["story_id"],
            project_id=data["project_id"],
            user_id=data["user_id"],
            plugin_id=data["plugin_id"],
            settings=data.get("settings", {}),
            run_id=data.get("run_id"),
        )
        ctx.state = WorkflowState(data.get("state", WorkflowState.PENDING.value))
        ctx.current_step = data.get("current_step", "")
        ctx.completed_steps = data.get("completed_steps", [])
        ctx.failed_steps = data.get("failed_steps", [])
        ctx.step_results = data.get("step_results", {})
        ctx.errors = data.get("errors", {})
        ctx.progress_percent = data.get("progress_percent", 0.0)
        ctx.progress_message = data.get("progress_message", "")
        ctx.metadata = data.get("metadata", {})
        ctx.created_at = datetime.fromisoformat(data["created_at"])
        ctx.updated_at = datetime.fromisoformat(data["updated_at"])
        return ctx
