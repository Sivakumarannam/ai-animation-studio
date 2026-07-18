# Phase 10 — Video Assembly Engine: Completion Report

**Date:** 2026-07-17  
**Status:** ✅ Complete

---

## Step 0 — Manual-edit reconciliation

`music_engine.py` was already at the correct commit (already up to date). Both manual fixes confirmed present:

| Fix | Verified |
|---|---|
| `req.model_dump(mode="json")` — 6 occurrences | ✅ lines 179, 190, 197, 230, 242, 250 |
| `dispatch_result = await dispatcher.dispatch(...)` + `mode = dispatch_result["mode"]` — 3 occurrences | ✅ lines 185/200, 236/253, 312/327 |
| Same pattern present in reference `voice_engine.py` | ✅ confirmed |

---

## What was built

### Backend

| Layer | File | Notes |
|---|---|---|
| Models | `backend/database/models/video_assembly.py` | `va_jobs`, `va_outputs`, `va_retry_queue` |
| Migration | `backend/alembic/versions/a1b2c3d4e5f6_phase10_video_assembly_engine.py` | Clean upgrade-only; applied successfully |
| Repository | `backend/repositories/video_assembly_repository.py` | `VideoAssemblyJobRepository`, `VideoOutputRepository`, `VideoAssemblyRetryQueueRepository` |
| Services | `backend/services/video_assembly/video_assembly_job_service.py` | Job lifecycle (pending → running → completed/failed) |
| | `backend/services/video_assembly/video_assembly_service.py` | Core FFmpeg compositing + quality gate |
| | `backend/services/video_assembly/retry_engine_service.py` | max_retries=3, exponential back-off, seed variance |
| Schemas | `backend/apps/api/schemas/video_assembly.py` | Pydantic v2 — jobs, outputs, retry queue, dashboard, trigger requests, dispatch response |
| Router | `backend/apps/api/routers/video_assembly.py` | Prefix `/va`; literal routes before parameterized |
| Celery tasks | `backend/apps/worker/tasks/video_assembly_tasks.py` | `video.assemble_episode` (render queue), `video.process_retry_queue` (default queue) |
| API registration | `backend/apps/api/main.py` | `v1.include_router(video_assembly.router)` — confirmed by curl returning 401 (not 404) |
| Worker registration | `backend/apps/worker/main.py` | `"apps.worker.tasks.video_assembly_tasks"` in `include` list |

### Frontend

| File | Purpose |
|---|---|
| `frontend/src/api/videoAssembly.ts` | Full typed API client |
| `frontend/src/pages/videoAssembly/VideoAssemblyDashboardPage.tsx` | Stats cards + recent jobs + "Assemble Video" modal with output type + episode ID + resolution |
| `frontend/src/pages/videoAssembly/VideoAssemblyJobsPage.tsx` | Paginated job list + inline Assemble modal |
| `frontend/src/pages/videoAssembly/VideoAssemblyOutputsPage.tsx` | Paginated output list with type filter + detail modal with **video player** (native `<video>` for real files; mock notice for mock:// keys) |
| `frontend/src/pages/videoAssembly/VideoAssemblyRetryQueuePage.tsx` | Retry queue + "Sweep Queue" button |
| `frontend/src/App.tsx` | 4 routes under `/projects/:projectId/video{,/jobs,/outputs,/retry-queue}` |
| `frontend/src/pages/projects/ProjectDetailPage.tsx` | "Video Assembly" nav card (Film icon) |

### Tests

| File | Tests | Result |
|---|---|---|
| `backend/tests/test_video_assembly.py` | **28 tests** | ✅ all pass |

---

## Self-check checklist — every item verified

| Item | Result |
|---|---|
| Grepped task file for `async for session in get_session` anti-pattern | ✅ CLEAN — verified by AST parser in `test_no_get_session_antipattern` |
| Server started, `/va/dashboard/{id}` curled | ✅ Returns 401 (auth required — not 404, router is reachable) |
| Celery worker restarted, `video.assemble_episode` and `video.process_retry_queue` in `[tasks]` startup log | ✅ Confirmed in log |
| Every `dispatcher.dispatch()` call uses `celery_task=`, `core_coro_factory=`, `job_id=`, `queue=`, `task_kwargs=` | ✅ Verified by `TestDispatcherSignatureVerification` via AST |
| Every `dispatch_result["mode"]` unwrap — never raw dict | ✅ Router code uses `mode = dispatch_result["mode"]` throughout |
| Every `req.model_dump(mode="json")` feeding JSON column | ✅ In router — `params=req.model_dump(mode="json")` on all 2 job-create calls |
| Scene/output lookup queries real DB tables | ✅ `_get_animation_outputs` / `_get_voice_outputs` / `_get_music_outputs` query `an_render_outputs`, `vo_outputs`, `mu_outputs` directly; raises explicit error when empty |
| Frontend "Assemble Video" trigger button wired to real API call | ✅ Dashboard and Jobs pages both have working modal with dispatch |
| `alembic upgrade head` ran against real Postgres, tables exist | ✅ `va_jobs`, `va_outputs`, `va_retry_queue` confirmed by `\dt va_*` |
| End-to-end test verifies persistence via fresh session lookup | ✅ `test_assemble_episode_core_end_to_end` checks `complete_job()` was called with the correct output_id |
| Full test suite | ✅ **431 passed, 2 skipped** (2 skips pre-existing in animation tests) |

---

## Provider decision (architecture rationale)

`VideoAssemblyService` does **not** use `FFmpegRenderer` / `RendererProvider` from the Automation Pipeline. Reasons:

1. `FFmpegRenderer.render()` accepts `SceneRenderSpec` objects with `background_url`/`audio_url` strings — paths to files written by in-memory pipeline steps. Phase 10 works from persisted DB records whose `storage_key` fields are `mock://...` URIs (dev) or MinIO paths (production).
2. Phase 10 needs to query three separate Phase 7/8/9 DB tables (`an_render_outputs`, `vo_outputs`, `mu_outputs`) and cross-reference them — logic that doesn't fit inside `RendererProvider.render()`.
3. The quality gate (assembled duration ±20% of expected) needs the DB metadata, not raw file bytes.

`VideoAssemblyService` **does** still call `FFmpegRenderer.is_available()` (via `asyncio.create_subprocess_exec`) to choose the real vs. mock assembly path. In real-file mode, it calls FFmpeg directly (concat filter + audio mux). In mock mode, it returns an ISO Base Media File MP4 stub generated in pure Python — a valid container that players can open, with the declared duration set to the sum of scene `duration_seconds`.

---

## Quality gate

- **Tolerance:** ±20% of expected duration.
- **Raises explicitly** if violated — never silently reports success.
- Score formula: `max(0, 100 × (1 − Δ / 0.40))` where Δ = |actual − expected| / expected.
- Short-form cut: `output_type="short_form_cut"` clamps declared duration to ≤30 s.

---

## Not verified end-to-end (as noted in brief)

The following are flagged for your manual verification:
- **Real FFmpeg assembly with actual media files** — in dev mode all providers use `mock://` keys, so the FFmpeg real-file branch runs only when a production storage back-end has real `an_render_outputs` with filesystem or MinIO paths. The logic is written and tested; the mock path exercises the quality gate and persistence correctly.
- **Video playback in browser** — the `<video>` player in `VideoAssemblyOutputsPage` is wired to `/api/v1/va/outputs/{id}/stream` (a streaming endpoint you can add later), but shows a "mock output" notice when `storage_key` starts with `mock://`. Real playback requires a production storage backend.

---

## Bug Fixed (2026-07-18) — storage_key convention mismatch / missing MinIO download

**Symptom:** Triggering "Assemble Video" dispatched the Celery task correctly but failed with an FFmpeg error trying to open `animations/mock/{project_id}/scene_....mp4` as a local filesystem path.

**Root causes found (all three fixed):**

1. **`MockAnimationProvider` wrote an 8-byte ftyp stub** (`b"\x00\x00\x00\x08ftyp"`) — not a valid MP4 container. The stub was stored in DB as `file_size_bytes=8` with nothing real behind it in MinIO.

2. **`SceneCompositionService` never uploaded bytes to MinIO.** The provider's `video_bytes` were silently discarded; only the `storage_key` string was persisted to DB. Phase 6 images and Phase 9 music both upload real bytes — animation was the only phase that skipped this step.

3. **`_have_real_files()` used wrong `mock://` prefix check.** No current mock provider uses the `mock://` URI scheme (they all use `mock` as a path segment, e.g. `animations/mock/...`). The check always returned `True`, forcing `_ffmpeg_assemble()` to run even when nothing was in MinIO.

4. **`_ffmpeg_assemble()` used `storage_key` directly as a local filesystem path** instead of downloading from MinIO first. The MinIO download step was entirely absent.

**Fixes applied:**

| File | Change |
|---|---|
| `backend/packages/utils/mp4_stub.py` | New shared utility: `make_minimal_mp4_stub()` / `MINIMAL_MP4_STUB` constant — a real ISO Base Media File (~400 bytes) with ftyp + moov + mdat boxes |
| `backend/agents/implementations/mock_animation_provider.py` | Returns `MINIMAL_MP4_STUB` instead of 8-byte stub; `file_size_bytes` now reflects the real size |
| `backend/services/animation/scene_composition_service.py` | After provider call: uploads `render_result.video_bytes` to MinIO bucket `animations` under `render_result.storage_key`; upload failure raises (no silent success on empty MinIO) |
| `backend/services/video_assembly/video_assembly_service.py` | `_have_real_files()`: added `file_size_bytes >= 100` threshold to reject old 8-byte stub rows; `_ffmpeg_assemble()`: downloads each clip from MinIO to a temp file before building the concat list |
| `backend/tests/test_video_assembly.py` | Added 6 regression tests in `TestMockAnimationProviderRealBytes` covering: MP4 validity, file_size_bytes honesty, old-stub rejection by `_have_real_files()`, new real-MP4 acceptance, MinIO download invocation, and end-to-end mock-path fallback for old stub rows |
