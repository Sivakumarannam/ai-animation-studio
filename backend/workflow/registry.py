"""
StepRegistry — register workflow steps without modifying the engine.

Open/Closed Principle: new steps are registered here and are automatically
included in the pipeline. Order is controlled by the `order` parameter.

Usage
-----
    registry = get_step_registry()
    registry.register(StoryStep, order=10)
    registry.register(SceneStep, order=20)
    # The executor calls registry.build_ordered_steps() to get the sorted list.
"""
from __future__ import annotations

import threading
from typing import Any

from workflow.step import BaseStep


class StepRegistration:
    def __init__(self, step_class: type[BaseStep], order: int, kwargs: dict[str, Any]) -> None:
        self.step_class = step_class
        self.order = order
        self.kwargs = kwargs


class StepRegistry:
    """
    Thread-safe registry of workflow step classes.
    Steps are instantiated lazily when build_ordered_steps() is called,
    so provider injection can happen after registration.
    """

    def __init__(self) -> None:
        self._registrations: list[StepRegistration] = []
        self._lock = threading.Lock()

    def register(
        self,
        step_class: type[BaseStep],
        order: int = 100,
        **kwargs: Any,
    ) -> None:
        """
        Register a step class.

        Parameters
        ----------
        step_class:
            The BaseStep subclass to register.
        order:
            Execution order (lower = earlier). Steps with equal order execute
            in registration order.
        **kwargs:
            Constructor arguments passed to step_class(**kwargs) at build time.
        """
        with self._lock:
            self._registrations.append(StepRegistration(step_class, order, kwargs))

    def build_ordered_steps(self) -> list[BaseStep]:
        """Instantiate and return steps sorted by order."""
        with self._lock:
            sorted_regs = sorted(self._registrations, key=lambda r: r.order)
        return [reg.step_class(**reg.kwargs) for reg in sorted_regs]

    def list_steps(self) -> list[dict[str, Any]]:
        """Return metadata for all registered steps (for observability)."""
        with self._lock:
            return [
                {
                    "name": reg.step_class.__name__,
                    "order": reg.order,
                }
                for reg in sorted(self._registrations, key=lambda r: r.order)
            ]

    def clear(self) -> None:
        """Remove all registrations. Useful in tests."""
        with self._lock:
            self._registrations.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: StepRegistry | None = None
_lock = threading.Lock()


def get_step_registry() -> StepRegistry:
    global _registry
    if _registry is None:
        with _lock:
            if _registry is None:
                _registry = StepRegistry()
    return _registry
