"""
WorkflowStateMachine — validates and applies state transitions.

Valid transitions
-----------------
PENDING   → RUNNING
RUNNING   → PAUSED | COMPLETED | FAILED | CANCELLED
PAUSED    → RUNNING | CANCELLED
FAILED    → RUNNING  (retry / resume)
CANCELLED → (terminal)
COMPLETED → (terminal)
"""
from __future__ import annotations

from workflow.context import WorkflowState
from packages.core.exceptions import AppError


class InvalidTransitionError(AppError):
    def __init__(self, from_state: WorkflowState, event: str) -> None:
        super().__init__(
            f"Cannot apply event '{event}' in state '{from_state.value}'",
            code="INVALID_STATE_TRANSITION",
        )


_TRANSITIONS: dict[WorkflowState, dict[str, WorkflowState]] = {
    WorkflowState.PENDING: {
        "start": WorkflowState.RUNNING,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.RUNNING: {
        "pause": WorkflowState.PAUSED,
        "complete": WorkflowState.COMPLETED,
        "fail": WorkflowState.FAILED,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.PAUSED: {
        "resume": WorkflowState.RUNNING,
        "cancel": WorkflowState.CANCELLED,
    },
    WorkflowState.FAILED: {
        "resume": WorkflowState.RUNNING,  # manual retry
    },
    WorkflowState.COMPLETED: {},   # terminal
    WorkflowState.CANCELLED: {},   # terminal
}

_TERMINAL_STATES = {WorkflowState.COMPLETED, WorkflowState.CANCELLED}


class WorkflowStateMachine:

    def transition(self, current: WorkflowState, event: str) -> WorkflowState:
        """Return the next state after applying *event* from *current*."""
        allowed = _TRANSITIONS.get(current, {})
        next_state = allowed.get(event)
        if next_state is None:
            raise InvalidTransitionError(current, event)
        return next_state

    def can_transition(self, current: WorkflowState, event: str) -> bool:
        return event in _TRANSITIONS.get(current, {})

    def is_terminal(self, state: WorkflowState) -> bool:
        return state in _TERMINAL_STATES
