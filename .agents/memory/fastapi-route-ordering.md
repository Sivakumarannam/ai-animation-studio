---
name: FastAPI route ordering — literal vs path param
description: Literal string route segments must be declared before parameterized routes or FastAPI matches the literal as the parameter type (e.g. UUID) and returns 422.
---

## Rule
In any FastAPI router, declare routes with literal string path segments **before** routes with parameterized segments of the same prefix.

## Example
```python
# CORRECT
router.get("/jobs/retry-queue")   # literal — declared first
router.get("/jobs/{job_id}")      # UUID param — declared second

# WRONG — FastAPI tries to parse "retry-queue" as UUID → 422
router.get("/jobs/{job_id}")
router.get("/jobs/retry-queue")
```

**Why:** FastAPI registers routes in declaration order and matches the first route whose pattern fits. When `{job_id}` is typed as `UUID`, FastAPI attempts UUID validation on the literal string and returns 422 before reaching the correct route.

**How to apply:** Whenever adding a fixed-path route alongside a `{id}`-parameterized route on the same prefix, scroll up and confirm the literal route comes first.
