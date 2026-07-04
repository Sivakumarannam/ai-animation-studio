"""
RetryPolicy — configurable exponential-backoff retry logic for workflow steps.
"""
from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from typing import Any


@dataclass
class RetryPolicy:
    """
    Retry configuration for a workflow step.

    Attributes
    ----------
    max_retries:
        Maximum number of retry attempts (0 = no retries).
    base_delay:
        Delay (seconds) before the first retry.
    max_delay:
        Upper bound on delay regardless of exponential growth.
    exponential_base:
        Growth factor. Delay[n] = min(base_delay * exponential_base^n, max_delay).
    jitter:
        Add ±20 % random noise to avoid thundering-herd on shared backends.
    retryable_exceptions:
        If set, only retry these exception types; re-raise everything else immediately.
    """

    max_retries: int = 3
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = ()

    # Defaults for common scenarios
    @classmethod
    def none(cls) -> "RetryPolicy":
        """No retries at all."""
        return cls(max_retries=0)

    @classmethod
    def fast(cls) -> "RetryPolicy":
        """Up to 3 quick retries — for lightweight operations."""
        return cls(max_retries=3, base_delay=1.0, max_delay=10.0)

    @classmethod
    def slow(cls) -> "RetryPolicy":
        """Up to 5 retries with longer waits — for heavy AI calls."""
        return cls(max_retries=5, base_delay=5.0, max_delay=120.0)

    def get_delay(self, attempt: int) -> float:
        """Return how many seconds to wait before the next attempt."""
        import random

        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter:
            delay *= 0.8 + random.random() * 0.4  # ±20 %
        return delay

    def is_retryable(self, exc: Exception) -> bool:
        """Return True if this exception should trigger a retry."""
        if not self.retryable_exceptions:
            return True  # retry on any exception by default
        return isinstance(exc, self.retryable_exceptions)


async def retry_async(
    coro_factory: Any,
    policy: RetryPolicy,
    on_retry: Any = None,
) -> Any:
    """
    Execute an async function with retry logic.

    Parameters
    ----------
    coro_factory:
        A zero-argument callable that returns a coroutine each time it is called.
    policy:
        The RetryPolicy to apply.
    on_retry:
        Optional async callable(attempt, exc, delay) called before each retry.
    """
    last_exc: Exception | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return await coro_factory()
        except Exception as exc:
            last_exc = exc
            if attempt >= policy.max_retries or not policy.is_retryable(exc):
                raise
            delay = policy.get_delay(attempt)
            if on_retry is not None:
                await on_retry(attempt + 1, exc, delay)
            await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]
