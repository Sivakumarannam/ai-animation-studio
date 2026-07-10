# Critical Fix Report

**Date:** 2026-07-10  
**Scope:** SQLAlchemy naming collision fix + 4 Critical bugs from MASTER_BUG_REPORT.md

---

## SQLAlchemy Naming Collision Fix ✅

**Root Cause:** Five model classes in `backend/database/models/asset_generation.py` shared names with
classes in other model files, breaking SQLAlchemy's string-based relationship resolution and causing
`NoReferencedTableError` / `AmbiguousTableError` at application startup.

**Files Changed:**

| File | Change |
|------|--------|
| `backend/database/models/asset_generation.py` | Renamed `SceneComposition` → `AgSceneComposition`, `RetryQueue` → `AgRetryQueue`, `GenerationJob` → `AgGenerationJob` (tablenames unchanged) |
| `backend/database/models/__init__.py` | Updated re-exports to use new names directly |
| `backend/repositories/asset_generation_repository.py` | Updated imports with `as` aliases |
| `backend/services/asset_generation/generation_job_service.py` | Import updated |
| `backend/services/asset_generation/shot_planning_service.py` | Import updated |
| `backend/services/asset_generation/quality_evaluation_service.py` | Import updated |
| `backend/services/asset_generation/retry_engine_service.py` | Import updated |
| `backend/tests/test_asset_generation.py` | All 5 class names updated in `TestPhase6Models` tests |

**Verification:** `pytest backend/tests/test_asset_generation.py::TestPhase6Models` → 4 passed ✅

---

## CRIT-1 — Route Shadowing Fixed ✅

**Bug:** `backend/apps/api/main.py` mounted both `library.router` (full CRUD) and `assets.router` (read-only
subset) on the same `/library/backgrounds` and `/library/props` paths. FastAPI uses first-match routing,
so the assets.py endpoints were unreachable and the mount order caused ambiguity.

**Fix:** Removed the `assets` import and `v1.include_router(assets.router)` from `main.py`. The
`assets.py` file only contained `GET /library/backgrounds` and `GET /library/props` — both already covered
by `library.py` which provides full CRUD.

---

## CRIT-2 — Characters Edit/Delete Fixed ✅

**Bug:** `CharactersPage.tsx` only allowed creating characters; no edit or delete functionality existed.

**Fix:** Rewrote `frontend/src/pages/characters/CharactersPage.tsx` to include:
- **Edit modal** with pre-filled form fields (name, description, personality, gender, age_range)
- **Delete confirmation modal** with loading + error states
- `editMutation` (PATCH `/projects/{id}/characters/{charId}`)
- `deleteMutation` (DELETE `/projects/{id}/characters/{charId}`)
- Edit / Delete action buttons on each character card

---

## CRIT-3 — update_idea Endpoint ✅ (Pre-existing, No Change Needed)

**Investigation:** Reviewed `backend/apps/api/routers/story_intelligence.py` and
`backend/services/intelligence/idea_service.py`. The `PATCH /si/ideas/{idea_id}` endpoint correctly
calls `svc["idea"].update()`, which has a full implementation applying all provided fields. No fix required.

---

## CRIT-4 — Celery Task Names ✅ (Pre-existing, No Change Needed)

**Investigation:** Reviewed `backend/apps/worker/tasks/intelligence_tasks.py` and
`backend/apps/worker/main.py`. The `TaskDispatcher` passes actual Celery task function objects
(not name strings) to `apply_async()`, so the registered task name is always used correctly.
No mismatch exists. No fix required.

---

## Summary

| Item | Status |
|------|--------|
| SQLAlchemy naming collision | ✅ Fixed |
| CRIT-1 Route shadowing | ✅ Fixed |
| CRIT-2 Characters edit/delete | ✅ Fixed |
| CRIT-3 update_idea endpoint | ✅ Pre-existing (no change) |
| CRIT-4 Celery task names | ✅ Pre-existing (no change) |
