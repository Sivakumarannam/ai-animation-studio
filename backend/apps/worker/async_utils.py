
"""
Shared async-bridge helper for Celery task modules.

Problem: calling asyncio.run(coro) on every task creates a NEW event loop
each time and closes it when done. But the SQLAlchemy async engine's
connection pool is created once per worker process (in worker_process_init)
and gets bound to whichever loop existed at that moment. When a later task's
fresh loop tries to reuse/clean up pooled connections tied to the old,
now-closed loop, it raises "RuntimeError: Event loop is closed".

Fix: maintain ONE persistent event loop per worker process and run every
task's coroutine on that same loop via run_until_complete(), instead of
creating and closing a new loop each time.

Safe under Celery's solo pool (single process, single thread) and prefork
(each forked child gets its own loop lazily on first use).
"""
from __future__ import annotations

import asyncio
from typing import Any, Coroutine

_worker_loop: asyncio.AbstractEventLoop | None = None


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
    return _worker_loop


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine on this worker process's single persistent event loop."""
    loop = _get_worker_loop()
    return loop.run_until_complete(coro)






