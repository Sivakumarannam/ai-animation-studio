---
name: asyncio.run() in sync pytest tests (Python 3.12)
description: asyncio.get_event_loop().run_until_complete() breaks in sync test functions under pytest-asyncio auto mode on Python 3.12. Use asyncio.run() instead.
---

# asyncio.run() in sync pytest tests (Python 3.12)

**Rule:** In sync (non-async) pytest test functions, call `asyncio.run(coro)` — never `asyncio.get_event_loop().run_until_complete(coro)`.

**Why:** Python 3.12 + pytest-asyncio in `asyncio_mode = "auto"` no longer sets a "current" event loop for sync test functions. `asyncio.get_event_loop()` raises `RuntimeError: There is no current event loop in thread 'MainThread'`. `asyncio.run()` creates its own loop, runs the coroutine, and tears it down cleanly.

**How to apply:**
- For single awaits in a sync test: replace `loop = asyncio.get_event_loop(); result = loop.run_until_complete(coro)` with `result = asyncio.run(coro)`.
- For multiple sequential awaits: either call `asyncio.run()` multiple times (each creates a fresh loop), or convert the test to an `async def` (pytest-asyncio auto mode handles it automatically).
- Bulk fix: `sed` or Python regex to remove `loop = asyncio.get_event_loop()` lines and replace `loop.run_until_complete(` with `asyncio.run(`.

**Affected project:** `backend/tests/test_animation_engine.py` was updated 2026-07-18 to use `asyncio.run()` throughout.
