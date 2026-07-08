---
name: session_scope fix for Celery task cores
description: async for session in get_session() skips commit when return exits the function; use session_scope() instead. Also Celery fork+asyncpg needs NullPool.
---

## Rule

Celery task core functions must use `async with session_scope() as session:` — never `async for session in get_session():`.

## Why

`async for session in get_session()` + `return result` inside the loop body causes Python to call `aclose()` on the generator asynchronously (not immediately). `aclose()` throws `GeneratorExit` (a `BaseException`) at the `yield` point. `get_session()` only catches `Exception`, so `GeneratorExit` bypasses `await session.commit()`. All `flush()` calls from `start_job()`, `complete_job()`, `fail_job()` are silently rolled back. Jobs stay at `"pending"` forever.

`async with session_scope() as session:` guarantees `__aexit__` runs synchronously on block exit (including on `return`), so `commit()` always executes.

## How to apply

Any new Celery task core coroutine that needs a DB session:
```python
from database.connection import session_scope

async def _my_task_core(...) -> dict:
    async with session_scope() as session:
        repo = MyRepository(session)
        ...
        return result  # commit() runs before this returns
```

`session_scope()` is in `backend/database/connection.py`. It catches `BaseException` (not just `Exception`) for safe handling of `asyncio.CancelledError`.

## Celery NullPool

Celery fork workers inherit the parent asyncpg connection pool. `asyncio.run()` creates a new event loop; pooled connections from the parent fail with "Future attached to a different loop".

Fix: `init_db(url, use_null_pool=True)` in `apps/worker/main.py`'s `@worker_process_init.connect` handler. `NullPool` opens/closes a fresh connection per `session_scope()` call — no cross-loop state.
