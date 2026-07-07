---
name: Celery dispatch mode in tests
description: TaskDispatcher returns "sync" only when Redis is unreachable; with Redis running it uses async/celery mode. Tests must be mode-agnostic.
---

## Rule
Never assert `body["mode"] == "sync"` in integration tests. Always use:
```python
assert body["mode"] in ("sync", "async", "celery")
assert body["status"] in ("completed", "pending", "running")
```

When accessing `result` fields that are only populated in sync mode:
```python
if body["mode"] == "sync" and body.get("result"):
    assert body["result"]["some_field"] == expected
```

**Why:** `TaskDispatcher` checks broker reachability at dispatch time. In the Replit dev environment Redis IS running, so the dispatcher correctly uses Celery async mode. Tests written assuming "Redis is always down" break when tasks are properly registered and the broker is reachable.

**How to apply:** Any test that calls a generation endpoint (`/generate`, `/generate-episode`, etc.) and inspects the response shape must be mode-agnostic. Tests that need deterministic result assertions should use `pytest.skip()` when in async mode, or use the job-fetch endpoint after polling for completion.
