# Phase 8 — Voice Engine: Completion Report

**Date:** 2026-07-15  
**Status:** Complete — 24 tests passing, frontend build clean, task names confirmed in Celery startup

---

## What Was Built

### Backend

| File | Description |
|------|-------------|
| `backend/database/models/voice_engine.py` | Three `vo_*` SQLAlchemy models: `VoiceGenerationJob`, `VoiceOutput`, `VoiceRetryQueue` |
| `backend/alembic/versions/a2b3c4d5e6f7_phase8_voice_engine.py` | Migration: creates `vo_jobs`, `vo_outputs`, `vo_retry_queue`; `down_revision='f1a2b3c4d5e6'`; Alembic head confirmed at `a2b3c4d5e6f7` |
| `backend/agents/interfaces/voice_provider.py` | `VoiceProvider` ABC with `VoiceGenerationRequest`, `VoiceGenerationResult` dataclasses — mirrors Phase 7 `AnimationProvider` shape exactly |
| `backend/agents/implementations/mock_voice_provider.py` | `MockVoiceProvider` — deterministic, zero-dependency; deterministic storage keys, duration from word count |
| `backend/agents/implementations/piper_voice_provider.py` | `PiperVoiceProvider` — wraps existing `PiperTTSProvider`, adds `VoiceGenerationResult` envelope |
| `backend/agents/provider_factory.py` | `_register_voice()` — reads `VO_VOICE_PROVIDER` env var; falls back to mock; `PIPER_BINARY` and `PIPER_MODELS_DIR` configurable |
| `backend/agents/registry.py` | `get_voice_provider()` FastAPI dependency helper |
| `backend/apps/api/schemas/voice_engine.py` | Pydantic v2 schemas for all endpoints |
| `backend/repositories/voice_engine_repository.py` | `VoiceJobRepository`, `VoiceOutputRepository`, `VoiceRetryQueueRepository` |
| `backend/services/voice/__init__.py` | Package init |
| `backend/services/voice/voice_job_service.py` | `VoiceJobService` — create/start/complete/fail jobs |
| `backend/services/voice/line_synthesis_service.py` | `LineSynthesisService` — calls provider, persists VoiceOutput record |
| `backend/services/voice/retry_engine_service.py` | `VoiceRetryEngineService` — enqueue/retrying/resolved/exhausted/mark_failed_retry; max_retries=3; exponential back-off |
| `backend/apps/worker/tasks/voice_tasks.py` | Three Celery tasks: `voice.generate_line`, `voice.generate_scene`, `voice.process_retry_queue`; all `dispatcher.dispatch()` calls use correct kwargs |
| `backend/apps/api/routers/voice_engine.py` | FastAPI router at `/vo` prefix; literal routes before parameterized; `registry.resolve(VoiceProvider)` (not `.get()`) |

**Wired in:**
- `backend/apps/api/main.py` — `v1.include_router(voice_engine.router)`
- `backend/apps/worker/main.py` — `"apps.worker.tasks.voice_tasks"` in Celery `include` list
- `backend/agents/provider_factory.py` — `_register_voice()` called from `setup_providers()`

### Frontend

| File | Description |
|------|-------------|
| `frontend/src/api/voiceEngine.ts` | Full typed API client for all `/vo/*` endpoints |
| `frontend/src/pages/voiceEngine/VoiceDashboardPage.tsx` | Dashboard with stat cards + **"Generate Voice" modal button** |
| `frontend/src/pages/voiceEngine/VoiceJobsPage.tsx` | Jobs list with pagination, status filter, "New Voice Job" modal |
| `frontend/src/pages/voiceEngine/VoiceOutputsPage.tsx` | Audio outputs list with language filter |
| `frontend/src/pages/voiceEngine/VoiceRetryQueuePage.tsx` | Retry queue; Retry button gated on `status === 'pending'` only (Phase 6/7 bug not repeated) |
| `frontend/src/App.tsx` | Routes: `/projects/:projectId/voice/*` |
| `frontend/src/pages/projects/ProjectDetailPage.tsx` | "Voice Engine" nav card with `Mic` icon |

### Tests

`backend/tests/test_voice_engine.py` — **24 tests, all passing:**

| Class | Tests |
|-------|-------|
| `TestMockVoiceProvider` | deterministic, varies-by-character, is_available, list_voices, language filter |
| `TestVoiceJobService` | create → start → complete → fail lifecycle |
| `TestVoiceRetryEngineService` | enqueue, retrying, resolved, exhausted, seed variance, mark_failed_retry, full state machine |
| `TestLineSynthesisService` | provider call + output record creation |
| `TestDispatcherSignatureVerification` | correct kwarg names in dispatcher.dispatch() + source-level grep |
| `TestGenerateLineEndpointDispatch` | **end-to-end**: `_generate_line_core` drives full start → synthesize → complete chain |
| `TestCeleryTaskRegistration` | include list, all 3 task names |

---

## Self-Check Results

### ✅ dispatcher.dispatch() kwargs verified
Grepped `backend/apps/api/routers/voice_engine.py` — found 19 lines containing `celery_task=`, `core_coro_factory=`, `job_id=`, `queue=`, `task_kwargs=`. All three dispatch call sites (generate/line, generate/scene, retry-queue) use the correct signature.

### ✅ Celery task names confirmed
```
voice.generate_line
voice.generate_scene
voice.process_retry_queue
```
All three appear in `celery_app.tasks` when the module is imported (verified with direct Python execution, not just `include=[]` check).

### ✅ Alembic migration created and accepted as new head
```
a2b3c4d5e6f7 (head)
```
`down_revision='f1a2b3c4d5e6'` (Phase 7) — linear chain maintained.

### ✅ Frontend build clean
No TypeScript errors. One chunk-size warning (pre-existing, not Phase 8).

### ✅ Retry queue button gating
`VoiceRetryQueuePage.tsx` line 107: `{entry.status === 'pending' && (<button>Retry</button>)}` — `exhausted`, `retrying`, `resolved` entries never get the button.

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| `VoiceProvider` interface mirrors `AnimationProvider` exactly | That shape worked on first real test in Phase 7 |
| `MockVoiceProvider` default; `PiperVoiceProvider` via `VO_VOICE_PROVIDER=piper` | Matches `AG_IMAGE_PROVIDER` / `AN_ANIMATION_PROVIDER` pattern |
| `PiperVoiceProvider` wraps existing `PiperTTSProvider` | Reuses proven implementation, adds Phase 8 `VoiceGenerationResult` envelope |
| `VoiceOutput.output_metadata` (DB column `vo_output_meta`) | SQLAlchemy 2.0 `DeclarativeBase` reserves the attribute name `metadata`; using it causes `InvalidRequestError` on reimport. Phase 7 solved this identically (`metadata_` → `an_render_output_meta`) |
| Literal routes first: `/vo/retry-queue`, `/vo/generate/line`, `/vo/generate/scene` | Phase 7 lesson: FastAPI matches literals as UUID params and returns 422 if they're declared after `/{job_id}` |
| `mark_failed_retry()` in `VoiceRetryEngineService` | Copied Phase 7's state-machine fix — non-exhausted failures must return to `pending` or `get_pending()` never re-picks them |

---

## Not Verified End-to-End (requires running database + auth)

- **Alembic migration applied to a real PostgreSQL database** — migration file is structurally correct and accepted as the new Alembic head, but `alembic upgrade head` was not run against a live DB (same caveat as Phase 7)
- **Real Piper binary execution** — `PiperVoiceProvider` wraps the existing `PiperTTSProvider` which requires the `piper` binary and voice models at `/models/piper`. Not available in this environment
- **Scene-level voice generation under real Celery** — `voice.generate_scene` serializes over multiple dialogue lines; per-line parallelism (`asyncio.gather`) is a future optimization
- **Authenticated HTTP cycle** — all endpoints return 401 without a JWT, confirming routes are mounted; full authenticated flow requires live DB tables

---

## API Endpoints (all confirmed 401 before auth)

```
GET  /api/v1/vo/dashboard/{project_id}
POST /api/v1/vo/generate/line
POST /api/v1/vo/generate/scene
GET  /api/v1/vo/retry-queue
POST /api/v1/vo/retry-queue/{entry_id}/retry
GET  /api/v1/vo/jobs
GET  /api/v1/vo/jobs/{job_id}
GET  /api/v1/vo/outputs
GET  /api/v1/vo/outputs/{output_id}
```

## To verify yourself

```bash
# Generate a single voice line (requires auth token):
curl -X POST https://<host>/api/v1/vo/generate/line \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<uuid>",
    "dialogue_line": "Hello, this is a test.",
    "character_name": "Narrator",
    "language": "en",
    "emotion": "neutral"
  }'

# Watch Celery worker for: task_success task=voice.generate_line
```
