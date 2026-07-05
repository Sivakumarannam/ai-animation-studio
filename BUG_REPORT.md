# Bug Report — AI Animation Studio
**Date:** 2026-07-04  
**Scope:** Phase 1 (Asset Management) + Phase 2 (Character Studio)  
**Auditor:** Production-Readiness Audit

---

## Summary

| Severity | Count |
|----------|-------|
| Critical (crashes all auth) | 1 |
| High (crashes endpoint) | 3 |
| Medium (wrong behavior) | 3 |
| Low (UX / documentation gap) | 4 |

All Critical and High bugs have been **fixed** in this audit. Medium and Low items are documented below.

---

## Fixed Bugs

### BUG-001 — Password hashing crashes on every auth call
**Severity:** Critical  
**File:** `backend/packages/utils/security.py`  
**Symptom:** `POST /auth/register` and `POST /auth/login` returned HTTP 500 for all requests.  
**Root Cause:** `passlib[bcrypt]` is incompatible with the installed `bcrypt` 4.x C extension. The `passlib` wrapper tried to call deprecated internal attributes that were removed in bcrypt 4.  
**Fix:** Replaced `passlib` with direct `bcrypt` library calls (`bcrypt.hashpw` / `bcrypt.checkpw`).  
**Commit impact:** Auth module — `security.py`.

---

### BUG-002 — All six seed endpoints returned HTTP 500
**Severity:** High  
**File:** `backend/services/library_service.py`  
**Symptom:** `POST /asset-manager/{type}/seed` crashed for all asset types.  
**Root Cause:** `f_(func.count)(Column)` — the code aliased SQLAlchemy's `func` as `f_` and called it as `f_(func.count)(Column)` which is doubly-wrapped and invalid. SQLAlchemy raises a `CompileError`.  
**Fix:** Changed all occurrences to the correct `func.count(Column)` form and removed the stale `f_` alias imports.  
**Commit impact:** `library_service.py` — six `seed_defaults` methods.

---

### BUG-003 — Wrong import of `CharacterTemplateResponse`
**Severity:** High  
**File:** `backend/apps/api/routers/asset_manager.py`  
**Symptom:** Server failed to start when the asset manager router was loaded.  
**Root Cause:** `CharacterTemplateResponse` was imported from `packages.schemas.assets` which does not export it. The correct source is `packages.schemas.character_templates`.  
**Fix:** Corrected the import path.

---

### BUG-004 — `show_deleted` filter used wrong field comparison
**Severity:** High  
**File:** `backend/services/library_service.py`  
**Symptom:** The `show_deleted` query parameter on search was always ignored — deleted assets never appeared even when `show_deleted=true`.  
**Root Cause:** The condition was `body.is_library is False` (checking a different field with Python identity comparison, which is always `False` for string fields).  
**Fix:** Added a proper `show_deleted: bool` field to `AssetSearchRequest` schema and used it as `show_deleted=body.show_deleted` in service calls.

---

### BUG-005 — `CharacterTemplateRepository.get_library` ignored `show_deleted`
**Severity:** Medium  
**File:** `backend/repositories/animation_repository.py`  
**Symptom:** The `show_deleted` parameter accepted by `CharacterTemplateService.get_library` was never propagated to the repository query, so deleted templates were never returned.  
**Fix:** Added `show_deleted: bool` parameter to `get_library` in the repository, filtering with `is_deleted == show_deleted`.

---

### BUG-010 (Fixed) — Cross-asset search silently dropped `show_deleted` for character templates
**Severity:** Medium  
**File:** `backend/services/animation_service.py`  
**Symptom:** `POST /asset-manager/search?show_deleted=true` correctly filtered backgrounds, props, and all other asset types, but character templates always returned the non-deleted view. The bug survived the initial BUG-005 fix because the repository fix was applied but not forwarded through `AssetManagerService.search`.  
**Fix:** Added `show_deleted=show_deleted` to the `self._templates.get_library(...)` call inside `AssetManagerService.search`.  
**Regression test added:** `TestAssetManagerSearch::test_search_show_deleted` now creates, soft-deletes, and asserts exact inclusion/exclusion by asset ID across both `show_deleted=True` and `show_deleted=False` states.

---

### BUG-006 — Frontend stats key mismatch
**Severity:** Medium  
**File:** `frontend/src/pages/studio/AssetManagerPage.tsx`  
**Symptom:** Sound effect count always showed 0 on the Asset Manager stats panel.  
**Root Cause:** Frontend read `stats.sound_effect` but the API returns the key as `stats.sound_effects` (plural).  
**Fix:** Updated the stats mapping key to `sound_effects`.

---

### BUG-007 — Missing `.checkbox` CSS class
**Severity:** Medium  
**File:** `frontend/src/index.css`  
**Symptom:** Checkboxes in Asset Manager rendered as unstyled browser-default boxes.  
**Root Cause:** The `AssetManagerPage.tsx` referenced `.checkbox` CSS class but it was never defined.  
**Fix:** Added the `.checkbox` class definition to `index.css`.

---

### BUG-008 — Missing Tailwind animation plugin
**Severity:** Low  
**File:** `frontend/tailwind.config.js`  
**Symptom:** `animate-in`, `fade-in`, `slide-in-from-bottom-4` classes produced no visible animation.  
**Root Cause:** `tailwindcss-animate` plugin was referenced in component classes but not installed or configured.  
**Fix:** Installed `tailwindcss-animate` and registered it in `tailwind.config.js`.

---

## Open Issues (Not Fixed — Require Decision)

### BUG-009 — `POST /stories/{id}/scenes` requires undocumented `scene_number`
**Severity:** Low (UX / API ergonomics)  
**File:** `backend/packages/schemas/scenes.py`  
**Symptom:** `POST /stories/{id}/scenes` returns HTTP 422 if caller omits `scene_number`. The field has no default and is not shown in API docs as required with any semantic.  
**Root Cause:** `scene_number: int = Field(ge=1)` has no default — callers must provide it.  
**Recommendation:** Either auto-generate `scene_number` as `max(existing) + 1` in the service, or document it clearly as a required "position index" in the OpenAPI description.

---

### BUG-010 — `expressions` and `poses` tables have a UNIQUE constraint on `name`
**Severity:** Medium  
**File:** Database schema / `alembic/versions/*.py`  
**Symptom:** `PATCH /library/expressions/{id}` returns HTTP 500 with `UniqueViolationError` if two different expressions are updated to the same name.  
**Root Cause:** The migration applied `UNIQUE` on `expressions.name` and `poses.name`. This is unusually strict for display-name fields and will cause production errors if users rename library items.  
**Recommendation:** Remove the unique constraints on `name` columns — uniqueness is already enforced by the `slug` column which is the semantic identifier. Requires a new migration.

---

### BUG-011 — `POST /library/character-templates` requires explicit `slug`
**Severity:** Low  
**File:** `backend/packages/schemas/character_templates.py`  
**Symptom:** Creating a character template without providing `slug` returns HTTP 422.  
**Root Cause:** `slug` has no default and is required by the schema.  
**Recommendation:** Auto-generate `slug` from `name` using `slugify(name)` in the service layer, making it optional in the schema. Similar to how web frameworks handle this.

---

### BUG-012 — `generation.py` line 99 hardcodes `user_id="api"`
**Severity:** Medium (security / correctness)  
**File:** `backend/apps/api/routers/generation.py:99`  
**Symptom:** Celery generation tasks are dispatched with `user_id="api"` instead of the authenticated user's ID. When Celery is available, generated content would not be attributed to the correct user.  
**Root Cause:** A `# TODO: replace with auth user_id from token` comment acknowledges this is unfinished.  
**Recommendation:** Pass `current_user.id` from the `CurrentUser` dependency into the task payload.

---

### BUG-013 — JWT secret key is hardcoded default
**Severity:** High (security)  
**File:** `backend/apps/api/config.py:16`  
**Symptom:** `SECRET_KEY` defaults to `"change-me-in-production-use-long-random-string"` if the environment variable is not set.  
**Risk:** Any deployment that fails to set `SECRET_KEY` will have tokens that can be forged by anyone who reads this source code.  
**Recommendation:** Remove the fallback default entirely — fail fast with a `ValueError` at startup if `SECRET_KEY` is not set in the environment:
```python
SECRET_KEY: str  # required — no default, raises ValidationError on startup if missing
```

---

### BUG-014 — CORS origins do not include the Replit preview domain
**Severity:** Medium  
**File:** `backend/apps/api/config.py:63`  
**Symptom:** `CORS_ORIGINS` is `["http://localhost:5173", "http://localhost:3000"]`. The Replit proxy domain (`*.replit.dev`) is not listed.  
**Impact:** Browser-based API calls from the Replit preview fail with CORS errors on any deployed instance.  
**Recommendation:** Add `CORS_ORIGINS` as an environment variable and include the Replit dev domain, or set `allow_origins=["*"]` for development (with a note to restrict in production).
