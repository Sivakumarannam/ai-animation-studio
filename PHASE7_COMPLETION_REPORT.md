# Phase 7 — Animation Engine: Completion Report

**Date:** 2026-07-13  
**Updated:** 2026-07-15  
**Status:** Complete — all 24 tests passing, server running

---

## What Was Built

### Backend

| File | Description |
|------|-------------|
| `backend/database/models/animation_engine.py` | Three `an_*` SQLAlchemy models: `AnimationJob`, `AnimationRenderOutput`, `AnimationRetryQueue` |
| `backend/alembic/versions/f1a2b3c4d5e6_phase7_animation_engine.py` | Migration: creates `an_jobs`, `an_render_outputs`, `an_retry_queue` with indexes |
| `backend/agents/interfaces/animation_provider.py` | `AnimationProvider` ABC with `AnimationRenderRequest`, `AnimationRenderResult`, `CharacterPlacement` dataclasses |
| `backend/agents/implementations/mock_animation_provider.py` | `MockAnimationProvider` — deterministic, zero-dependency, fully tested |
| `backend/agents/provider_factory.py` | `_register_animation()` — reads `AN_ANIMATION_PROVIDER` env var, falls back to mock |
| `backend/agents/registry.py` | `get_animation_provider()` FastAPI dependency helper |
| `backend/apps/api/schemas/animation_engine.py` | Pydantic v2 schemas for jobs, outputs, retry-queue, dashboard stats, trigger requests |
| `backend/repositories/animation_engine_repository.py` | `AnimationJobRepository`, `AnimationRenderOutputRepository`, `AnimationRetryQueueRepository` |
| `backend/services/animation/__init__.py` | Package init |
| `backend/services/animation/render_job_service.py` | `RenderJobService` — create/start/complete/fail jobs |
| `backend/services/animation/scene_composition_service.py` | `SceneCompositionService` — composites Phase 6 image assets into clips via provider |
| `backend/services/animation/retry_engine_service.py` | `RetryEngineService` — enqueue/retrying/resolved/exhausted, max_retries=3, jittered seeds; includes `mark_failed_retry()` to return non-exhausted failures to `pending` |
| `backend/apps/worker/tasks/animation_tasks.py` | Three Celery tasks: `animation.render_scene`, `animation.render_episode`, `animation.process_retry_queue`; all `dispatcher.dispatch()` calls use correct signature; non-exhausted retry failures call `mark_failed_retry()` |
| `backend/apps/api/routers/animation_engine.py` | FastAPI router at `/an` prefix; literal routes declared before parameterized (lessons from Phase 6) |

**Wired in:**
- `backend/apps/api/main.py` — `v1.include_router(animation_engine.router)`
- `backend/apps/worker/main.py` — `"apps.worker.tasks.animation_tasks"` added to Celery `include` list
- `backend/agents/provider_factory.py` — `_register_animation()` called from `setup_providers()`

### Frontend

| File | Description |
|------|-------------|
| `frontend/src/api/animationEngine.ts` | Full typed API client for all `/an/*` endpoints |
| `frontend/src/pages/animationEngine/AnimationDashboardPage.tsx` | Dashboard with stat cards + **"Generate Animation" button** (corrected Phase 6 omission — spec called this out explicitly) |
| `frontend/src/pages/animationEngine/AnimationJobsPage.tsx` | Jobs list with pagination, status filter, and "New Render Job" modal |
| `frontend/src/pages/animationEngine/AnimationOutputsPage.tsx` | Render outputs list with type filter and pagination |
| `frontend/src/pages/animationEngine/AnimationRetryQueuePage.tsx` | Retry queue list with per-entry retry button |
| `frontend/src/App.tsx` | Routes: `/projects/:projectId/animation/*` |
| `frontend/src/pages/projects/ProjectDetailPage.tsx` | "Animation Engine" nav card added |

### Tests

`backend/tests/test_animation_engine.py` — **24 tests, all passing:**

| Class | Tests |
|-------|-------|
| `TestMockAnimationProvider` | deterministic, varies-by-scene, is_available |
| `TestRenderJobService` | create → start → complete → fail lifecycle |
| `TestRetryEngineService` | enqueue → retrying → resolved/exhausted, seed variance, `mark_failed_retry` requeues as pending, full state machine (pending→retrying→pending×2→exhausted), process_retry_queue non-exhausted path, stuck-in-retrying prevention |
| `TestSceneCompositionService` | provider call + output record creation |
| `TestDispatcherSignatureVerification` | correct kwarg names for `dispatcher.dispatch()` |
| `TestGenerateSceneEndpointDispatch` | **end-to-end**: `_render_scene_core` drives full dispatch → complete chain |
| `TestCeleryTaskRegistration` | include list, task names for all 3 tasks |

---

## Verified End-to-End

- ✅ Backend starts cleanly; `providers_registered` log shows `"AnimationProvider": "mock"`
- ✅ `/api/v1/an/dashboard/{id}`, `/api/v1/an/jobs`, `/api/v1/an/outputs`, `/api/v1/an/retry-queue`, `/api/v1/an/generate/scene` — all return 401 (correct; auth required) confirming routes are mounted
- ✅ Frontend build succeeds (Vite running on port 5000, no console errors)
- ✅ `animation.render_scene`, `animation.render_episode`, `animation.process_retry_queue` task names visible in Celery startup log

## Episode-Level Render — Verification Path

Episode render (`animation.render_episode`) was NOT triggered during automated testing. To verify it manually, make a real authenticated POST to:

```
POST /api/v1/an/generate/episode
{
  "project_id": "<your-project-uuid>",
  "episode_id": "<your-episode-uuid>",
  "scene_ids": ["<scene-uuid-1>", "<scene-uuid-2>"],
  "fps": 24,
  "width": 1280,
  "height": 720
}
```

Expected result: Celery worker log shows `render_episode_complete job_id=... rendered=2 failed=0`. Each scene generates a sub-job and a `VoiceOutput` record. If any scene fails, it is enqueued in `an_retry_queue`.

**Architecture note:** Episode render loops serially over scenes (not truly parallel — no `asyncio.gather` across scenes). Multi-scene parallelism inside a single episode task is a future optimization.

## AnimationRetryQueuePage Self-Check

**The Phase 6 retry-button-on-exhausted bug does NOT exist in Phase 7.**

Checked `AnimationRetryQueuePage.tsx` line 106:
```tsx
{entry.status === 'pending' && (
  <button ...>Retry</button>
)}
```

The Retry button is rendered only for `pending` entries. Entries in `retrying`, `resolved`, or `exhausted` state show no button. The Phase 6 regression is explicitly prevented by this status guard.

## Retry State Machine — Fixed

The code reviewer identified a bug: `mark_retrying` increments `retry_count` and sets status to `"retrying"`, but a failed attempt below `max_retries` previously had no transition back to `"pending"`. This meant `get_pending` (which fetches `status == "pending"` only) would never re-pick the entry.

**Fix applied:**
- `RetryEngineService.mark_failed_retry()` added — sets status back to `"pending"`, sets `next_retry_at` with exponential back-off
- `_process_animation_retry_queue_core` `except` block calls `mark_failed_retry()` for the non-exhausted path
- 5 new tests verify the full state machine: pending→retrying→pending (non-exhausted), pending→retrying→exhausted, re-queued entries re-fetched by `get_pending`

## Not Yet Verified (requires running database + auth)

- Alembic migration (requires PostgreSQL with existing schema at `down_revision='e31c0776919b'`)
- Episode render multi-scene parallelism under real Celery with a real PostgreSQL database

## Key Architecture Decisions

- All `dispatcher.dispatch()` calls use `celery_task=`, `core_coro_factory=`, `job_id=`, `queue=`, `task_kwargs=` (Phase 6 bug lessons applied)
- Literal routes (`/an/retry-queue`, `/an/generate/scene`, `/an/generate/episode`) declared before parameterized routes in the router
- `MockAnimationProvider` is the default; `FFmpegAnimationProvider` is selected by `AN_ANIMATION_PROVIDER=ffmpeg` env var
- Episode renders auto-enqueue failed scenes to `an_retry_queue`
- Non-exhausted retry failures return to `pending` via `mark_failed_retry()`; exhausted entries (retry_count >= max_retries) go terminal via `mark_exhausted()`
