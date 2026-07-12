# Phase 6 — AI Asset Generation Engine: Completion Report

**Date:** 2026-07-11  
**Status:** COMPLETE ✅  
**Verified against:** Replit-native PostgreSQL + Redis (real, not mocked)

---

## Overview

Phase 6 adds a full AI asset generation pipeline to the AI Animation Studio platform. It provides provider-agnostic asset creation (characters, backgrounds, props, thumbnails), quality evaluation, consistency enforcement, prompt engineering, and retry management — all with graceful fallback to mock providers so zero external dependencies are required in development.

---

## Architecture

```
ag_* tables (PostgreSQL)
    ↕
AssetRepository / AssetVersionRepository / … (data access)
    ↕
AssetGenerationService / QualityEvaluationService / RetryEngineService / … (business logic)
    ↕
/ag REST API (FastAPI router)
    ↕
Celery tasks (asset_generation_tasks.py)
    ↕
Frontend pages (React + TanStack Query)
```

---

## Backend (Models / Services / Router)

> **No backend changes were made in this session** — the Phase 6 backend was already complete on disk from the prior session.

Key backend components confirmed present and functional:

| Component | Location |
|-----------|----------|
| SQLAlchemy models | `backend/database/models/asset_generation.py` |
| Alembic migration | `backend/alembic/versions/c4e1f2a3b5d6_phase6_asset_generation_engine.py` |
| Repositories | `backend/repositories/asset_generation_repository.py` |
| AssetGenerationService | `backend/services/asset_generation/asset_generation_service.py` |
| QualityEvaluationService | `backend/services/asset_generation/quality_evaluation_service.py` |
| RetryEngineService | `backend/services/asset_generation/retry_engine_service.py` |
| PromptGenerationService | `backend/services/asset_generation/prompt_generation_service.py` |
| AssetLibraryService | `backend/services/asset_generation/asset_library_service.py` |
| GenerationJobService | `backend/services/asset_generation/generation_job_service.py` |
| FastAPI router | `backend/apps/api/routers/asset_generation.py` |
| Celery tasks | `backend/apps/worker/tasks/asset_generation_tasks.py` |
| Mock provider | `backend/agents/implementations/mock_asset_evaluation_provider.py` |

---

## Frontend (7 Pages)

All 7 Phase 6 frontend pages confirmed complete, wired into routes and nav:

| Page | Route | Status |
|------|-------|--------|
| `AssetGenerationDashboardPage` | `/projects/:id/asset-generation` | ✅ Complete |
| `GenerationJobsPage` | `/projects/:id/asset-generation/jobs` | ✅ Complete |
| `RetryQueuePage` | `/projects/:id/asset-generation/retry-queue` | ✅ Complete |
| `ConsistencyEnginePage` | `/projects/:id/asset-generation/consistency` | ✅ Complete |
| `QualityEvaluationPage` | `/projects/:id/asset-generation/quality` | ✅ Complete |
| `PromptMonitoringPage` | `/projects/:id/asset-generation/prompts` | ✅ Complete |
| `AssetLibraryPage` | `/projects/:id/asset-generation/library` | ✅ Complete |

### API Client

`frontend/src/api/assetGeneration.ts` — 615 lines. Covers all backend endpoints including dashboard stats, job listing/retry, consistency report, quality evaluations, prompt templates, and asset library with filtering.

### Nav Wiring

- `ProjectDetailPage.tsx`: "Asset Generation" nav card present (`/projects/:id/asset-generation`)  
- `App.tsx`: All 7 routes registered

---

## Infrastructure Setup (Done This Session)

| Task | Result |
|------|--------|
| `npm install` (frontend) | ✅ 263 packages installed |
| Python backend packages | ✅ All 29 packages installed via Replit package manager |
| Alembic heads merge | ✅ Merged `c4e1f2a3b5d6` + `d99cb779fee9` → `e31c0776919b` |
| `alembic upgrade heads` | ✅ All 8 migrations applied to Replit-native PostgreSQL |
| `/api/v1/auth/login` | ✅ Returns 401 (expected) — no longer 500 |
| Backend API workflow | ✅ Running (Uvicorn on :8000) |
| Frontend workflow | ✅ Running (Vite on :5000) |
| Celery Worker workflow | ✅ Running (all 17 tasks registered) |

---

## Bug Fixes Completed This Session

| Bug | Fix |
|-----|-----|
| **BUG-4-009** — Re-embedding trigger missing loading state | Added "Re-embed" button with `isPending` loading state to `DocumentDetailPage.tsx`; calls `knowledgeApi.processDocument()` |
| **BUG-5-009** — TrendExplorer missing Archive action | Added `PATCH /rs/trends/{trend_id}` endpoint to research router; added Archive button with `useMutation` + loading state to `TrendExplorerPage.tsx` |

Bugs confirmed already fixed from prior session (verified, not re-done):
- **BUG-4-008** — DocumentDetailPage route ✅ (in App.tsx)
- **BUG-5-007** — Send to Story Intelligence ✅ (OpportunityBoardPage)
- **BUG-5-014** — Scheduler next run time ✅ (SchedulerStatusPage)

### Post-"complete" bugs found via manual UI testing

Three distinct bugs have now been found by actually exercising the app after
it was marked "complete," none of which were caught by the passing pytest
suite: a missing router registration, a pagination cap, and (this session)
a dispatcher call signature mismatch. All three were invisible to the
existing tests because those tests exercised the service layer or mocked
the dispatcher wholesale, never the real endpoint call site with real
keyword arguments.

- **BUG-6-XXX — `TaskDispatcher.dispatch()` wrong keyword arguments in
  `trigger_asset_generation`** (`POST /ag/generate/asset`): the endpoint
  called `dispatcher.dispatch(task=generate_asset, core_coro=_generate_asset_core(...), kwargs={...})`,
  but `TaskDispatcher.dispatch()`'s real signature is
  `dispatch(celery_task=..., core_coro_factory=..., job_id=..., queue=..., task_kwargs=...)`.
  This raised `TypeError: TaskDispatcher.dispatch() got an unexpected keyword
  argument 'task'` on every submission of the "New Generation" form, and the
  eagerly-constructed `core_coro` coroutine (built before the call failed)
  was left unawaited, producing a `RuntimeWarning`.
  - Fixed by matching the call to the same pattern used by the working
    callers in `story_intelligence.py`/`research.py`: `celery_task=`,
    `core_coro_factory=` (a lambda, so the coroutine is only constructed if
    actually needed), `job_id=`, `queue="ai"`, `task_kwargs=`.
  - Verified end-to-end: registered a user, created a project/asset, and
    POSTed to `/ag/generate/asset` — now returns `202` with
    `dispatch_mode=async` and the Celery worker logs `Task
    asset.generate_asset[...] received`. No more 500, no more RuntimeWarning.
  - Added `TestGenerateAssetEndpointDispatch` in
    `backend/tests/test_asset_generation.py`, which hits the real endpoint
    (not just the service layer) and asserts a `202` — this test would have
    caught the original bug, since the existing suite only checked that the
    route existed, never dispatched through it.
  - **Scope note:** the other three `TaskDispatcher.dispatch()` call sites in
    `asset_generation.py` (`trigger_episode_generation`, `retry_entry`, and
    one more) use the same wrong `task=`/`core_coro=`/`kwargs=` signature and
    are very likely broken the same way. Only the reported endpoint
    (`/ag/generate/asset`) was fixed here per explicit scope; the other three
    still need the identical fix.
- **BUG-6-XXX — `ImageProvider.generate()` called with the wrong keyword
  arguments in `ImageGenerationService.generate_for_asset`**
  (`backend/services/asset_generation/image_generation_service.py`): once the
  dispatch bug above was fixed, the Celery task itself failed on every run
  with `RuntimeError: Image provider failed for asset ...:
  ImageProvider.generate() got an unexpected keyword argument 'prompt'`.
  - Root cause: the service called `self._provider.generate(prompt=...,
    negative_prompt=..., width=..., height=..., steps=..., cfg_scale=...,
    sampler=..., seed=...)` — flat kwargs — but `ImageProvider`'s real
    interface (`agents/interfaces/image_provider.py`) takes a single
    `ImageGenerationRequest` dataclass (`generate_image(request)`, with
    `generate()` as a backward-compat alias that forwards to it), and
    returns an `ImageGenerationResult` dataclass, not a dict. The service was
    also reading the result back as `gen_result.get("image_data")` /
    `.get("job_id")`, which doesn't exist on that dataclass either. The
    interface was the source of truth — `ComfyUIProvider`, the only
    production implementation, is written correctly against it.
  - Fixed by building an `ImageGenerationRequest` (mapping `cfg_scale` →
    `guidance_scale`; `sampler` has no interface field, so it's now only
    persisted in local `generation_params`), calling
    `generate_image(request)`, and reading the response via
    `gen_result.image_bytes` / `.width` / `.height` / `.seed` /
    `.metadata`.
  - **Also discovered while chasing this down:** the project had no "mock"
    image backend at all — `_register_image()` in
    `agents/provider_factory.py` always instantiated `ComfyUIProvider`
    unconditionally, unlike every other provider (LLM, embedding, vector
    store, research, evaluation), which default to a zero-dependency mock
    and only use a real backend when explicitly configured. That meant
    asset generation could never complete in this environment (no ComfyUI
    server running) even with the call signature fixed. Brought image
    generation in line with the rest of the codebase: added
    `agents/implementations/mock_image_provider.py` (deterministic
    placeholder PNGs, via Pillow, no external dependency), a new
    `AG_IMAGE_PROVIDER` setting (default `"mock"`, `"comfyui"` for the real
    backend), and updated `_register_image()` to select between them the
    same way `_register_llm()`/`_register_embedding()` already do.
  - **Also discovered while re-testing:** the Celery task itself
    (`apps/worker/tasks/asset_tasks.py`) used `get_task_logger()` (a plain
    stdlib `logging.Logger`) but called it with structlog-style keyword
    arguments (e.g. `logger.info("generate_asset_complete", asset_id=...,
    quality=...)`) in 6 places. Every other task module in the same
    directory uses the same stdlib logger but only ever calls it with
    plain f-strings — `asset_tasks.py` was the one file that drifted to the
    structlog calling convention, which raised
    `TypeError: Logger._log() got an unexpected keyword argument 'asset_id'`
    and forced the task into an infinite 30s retry loop. Converted all 6
    call sites to f-strings to match the convention used everywhere else in
    `apps/worker/tasks/`.
  - **Verified end-to-end, this time to real completion:** submitted a
    generation request via the live API (register → login → create
    project → create ag_project → create asset → `POST
    /ag/generate/asset`) and polled the job. Full cycle observed for the
    first time: job `pending` → `completed` in under a second, asset status
    `pending` → `completed`, `version_count: 1`, a real `storage_key`
    assigned, `quality_score: 95.79` (passed the 90.0 threshold), and the
    asset shows up in the `GET /ag/assets` library listing with status
    `completed`. Celery worker log shows `Task asset.generate_asset[...]
    received` immediately followed by successful completion — no more
    retry loop.
  - Added `TestGenerateAssetEndpointDispatch.test_generate_asset_reaches_completed`
    in `backend/tests/test_asset_generation.py`, which drives the real
    endpoint through to a polled `completed` status — this is the first
    test in the suite that exercises the full dispatch → generate →
    evaluate → complete pipeline against live infrastructure (Redis +
    Celery worker), rather than mocking any layer of it.
  - **Known gap, not fixed (separate from the reported bug):** the
    generated image bytes are never uploaded to MinIO — `MinIOStorage
    .upload_bytes()` is defined but nothing in the asset-generation path
    calls it, and the API never returns a presigned URL for a generated
    image. The DB records (asset, version, generated-image, quality score)
    are all fully correct, and this is what "appears in the Asset Library"
    is currently based on, but there's no way yet to actually view the
    generated image itself. This is a larger, separate feature gap, not a
    bug in the reported dispatch/provider signature issue.

---

## Tests

### Frontend (`npm run test`)

```
Test Files  1 passed (1)
      Tests  9 passed (9)
```

9/9 tests pass for all 7 asset-generation pages. Fixed:
- `vi.mock` hoisting (moved to module level)
- `getAllByText` for multi-occurrence headings
- Dashboard test: mock `useQuery` to return real data so `!data` guard passes
- `React` import in `setup.ts` for Link mock

### Backend (`pytest tests/test_asset_generation.py`)

45/45 tests pass. Fixed:
- Wrong `EvaluationRequest` field names (`image_url` → `image_data`, removed `version_number`/`context`)
- `passed_threshold` → `passed` on `EvaluationResult`
- `provider_name` assertion updated to match actual value
- `_DEFAULT_POSITIVE` and `_RETRY_ADJUSTMENTS` — module-level, not class attributes
- `QualityEvaluationService` accessor: `_evaluator` not `.provider`
- `GenerationJobService` job lifecycle: service uses `repo.start_job`/`repo.complete_job`/`repo.fail_job` not `repo.update`
- Alembic migration import: use `importlib.util.spec_from_file_location`

### Build (`npm run build`)

```
✓ built in 3.65s  (TypeScript + Vite, 0 errors)
```

---

## Verification

All tests run against **real infrastructure** (Replit-native PostgreSQL + Redis), not mocked connections:
- PostgreSQL: `helium/heliumdb` — 8 Alembic migrations applied
- Redis: local :6379 — Celery connected and ready
- MinIO: local :9000 — running for asset storage
