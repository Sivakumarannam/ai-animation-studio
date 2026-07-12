---
name: TaskDispatcher.dispatch() call signature
description: The real keyword arguments for TaskDispatcher.dispatch() in backend/apps/worker/dispatcher.py, and how to spot copy-paste drift at call sites.
---

`TaskDispatcher.dispatch()` (backend/apps/worker/dispatcher.py) is keyword-only with signature:
`dispatch(celery_task=..., core_coro_factory=..., job_id=None, queue="ai", task_kwargs=None)`.

Some call sites (found in `asset_generation.py`) were written with made-up kwarg names instead —
`task=`, `core_coro=` (an eagerly-constructed coroutine, not a factory), and `kwargs=`. This raises
`TypeError: got an unexpected keyword argument 'task'` and leaves the eagerly-built coroutine
unawaited (RuntimeWarning), invisible to any test that mocks `dispatcher.dispatch` wholesale or only
calls the service layer beneath it.

**Why:** the correct pattern only exists in the working callers (`story_intelligence.py`,
`research.py`), so copy-paste into a new router file can silently drift to a wrong, never-tested
signature.

**How to apply:** when adding or auditing a `dispatcher.dispatch(...)` call, compare kwargs against a
known-working caller, and add a test that hits the real endpoint (not a mocked dispatcher) to catch
signature drift. `backend/apps/api/routers/asset_generation.py` had 4 call sites; only one
(`trigger_asset_generation`) was confirmed fixed — the other 3 likely have the same bug (see project
follow-up tasks).
