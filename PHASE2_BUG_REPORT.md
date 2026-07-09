# Phase 2 — Animation Engine Bug Report

**Audit Date:** 2026-07-09  
**Phase:** Module 2 — Animation Engine (Character Library, Templates, Backgrounds, Props, Asset Manager)  
**Status:** PRE-FIX — DO NOT DEPLOY

---

## 🔴 CRITICAL BUGS

### BUG-2-001 — Duplicate Route Shadowing: `/library/backgrounds` and `/library/props`
- **Problem:** Both `assets.py` and `library.py` define `GET /library/backgrounds` and `GET /library/props`. Both routers are included in `main.py` (lines 181 and 192). FastAPI registers whichever is mounted first. `assets.py` has READ-ONLY endpoints with no CRUD, while `library.py` has full CRUD (POST/PATCH/DELETE). Any POST/PATCH/DELETE call reaching the shadowed router returns 404 or routes to the wrong handler.
- **Root Cause:** `assets.py` was an early stub that was never removed after `library.py` was written. Both are `v1.include_router()`-ed.
- **Files:** `backend/apps/api/routers/assets.py`, `backend/apps/api/routers/library.py`, `backend/apps/api/main.py` (lines 181, 192)
- **Severity:** CRITICAL
- **Estimated Fix Time:** 30 min — remove background/prop routes from `assets.py` or exclude it from main.py

---

### BUG-2-002 — `CharactersPage.tsx` Missing Edit and Delete
- **Problem:** The Characters page has a "New Character" create flow but no Edit Character dialog and no Delete Character button, even though the backend has `PATCH /characters/{id}` and `DELETE /characters/{id}`.
- **Root Cause:** UI was never implemented for update/delete operations.
- **Files:** `frontend/src/pages/characters/CharactersPage.tsx`, `backend/apps/api/routers/characters.py`
- **Severity:** CRITICAL (users cannot modify or remove characters)
- **Estimated Fix Time:** 3 hours — add edit dialog + delete confirmation

---

## 🔴 HIGH PRIORITY

### BUG-2-003 — Character Library Page: List Only, No CRUD
- **Problem:** `CharacterLibraryPage.tsx` only lists character templates via `getCharacterTemplates`. There is no Create, Edit, or Delete button. Backend `character_templates.py` has full CRUD.
- **Root Cause:** Page was scaffolded with read-only intent; CRUD never added.
- **Files:** `frontend/src/pages/library/CharacterLibraryPage.tsx`, `backend/apps/api/routers/character_templates.py`
- **Severity:** HIGH
- **Estimated Fix Time:** 4 hours

---

### BUG-2-004 — Background Library Page: List Only, No CRUD
- **Problem:** `BackgroundLibraryPage.tsx` only lists backgrounds. No Create, Edit, or Delete UI. Backend `library.py` has `POST/PATCH/DELETE /library/backgrounds`.
- **Root Cause:** Same as BUG-2-003.
- **Files:** `frontend/src/pages/library/BackgroundLibraryPage.tsx`, `backend/apps/api/routers/library.py`
- **Severity:** HIGH
- **Estimated Fix Time:** 3 hours

---

### BUG-2-005 — Props Library Page: List Only, No CRUD
- **Problem:** `PropsLibraryPage.tsx` only lists props. No Create, Edit, or Delete UI. Backend `library.py` has `POST/PATCH/DELETE /library/props`.
- **Root Cause:** Same as BUG-2-003.
- **Files:** `frontend/src/pages/library/PropsLibraryPage.tsx`, `backend/apps/api/routers/library.py`
- **Severity:** HIGH
- **Estimated Fix Time:** 3 hours

---

### BUG-2-006 — No Character Image Upload on CharactersPage
- **Problem:** Characters page has no file upload button for character images/sprites. Backend `asset_manager.py` supports `POST /asset-manager/upload` (multipart). The `CharactersPage` cannot attach images to characters.
- **Root Cause:** Upload UI never connected to the characters workflow.
- **Files:** `frontend/src/pages/characters/CharactersPage.tsx`, `backend/apps/api/routers/asset_manager.py`
- **Severity:** HIGH (core feature for an animation studio)
- **Estimated Fix Time:** 4 hours

---

### BUG-2-007 — AssetManagerPage: Hardcoded `duration_seconds: 5.0` for Audio Uploads
- **Problem:** `AssetManagerPage.tsx` upload mutation hardcodes `duration_seconds: 5.0` for audio asset types regardless of actual file duration.
- **Root Cause:** Placeholder value never replaced with real metadata extraction.
- **Files:** `frontend/src/pages/studio/AssetManagerPage.tsx`
- **Severity:** HIGH (produces incorrect data in DB)
- **Estimated Fix Time:** 2 hours — read HTML5 audio duration from the File object before submitting

---

## 🟡 MEDIUM PRIORITY

### BUG-2-008 — No Pagination Controls on CharactersPage, CharacterLibraryPage, BackgroundLibraryPage, PropsLibraryPage
- **Problem:** All four list pages use `PaginatedResponse` from the API but render no pagination UI (no Next/Prev buttons, no page indicator). Users cannot browse beyond the first page of results.
- **Root Cause:** Pagination state managed but UI never rendered.
- **Files:** `frontend/src/pages/characters/CharactersPage.tsx`, `frontend/src/pages/library/CharacterLibraryPage.tsx`, `frontend/src/pages/library/BackgroundLibraryPage.tsx`, `frontend/src/pages/library/PropsLibraryPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 2 hours (shared pagination component exists, needs wiring)

---

### BUG-2-009 — `assets.py` Endpoints Not Wired to Any Frontend API Client
- **Problem:** `backend/apps/api/routers/assets.py` defines read-only `GET /library/backgrounds` and `GET /library/props` that are never called by the frontend. The frontend calls `library.ts` functions which hit `library.py` endpoints. The `assets.py` endpoints are dead code.
- **Root Cause:** Legacy router never cleaned up.
- **Files:** `backend/apps/api/routers/assets.py`, `backend/apps/api/main.py`
- **Severity:** MEDIUM (dead code + shadowing risk)
- **Estimated Fix Time:** 30 min — remove or consolidate

---

### BUG-2-010 — Missing Navigation: Intelligence, Knowledge, Research Not in AppLayout Sidebar
- **Problem:** `AppLayout.tsx` sidebar includes Library, Studio, and Research links but has NO links to `/projects/:id/intelligence` (Phase 3), `/projects/:id/knowledge` (Phase 4). Users must navigate to these by knowing the URL.
- **Root Cause:** Sidebar was not updated when Phase 3/4 were added.
- **Files:** `frontend/src/components/layout/AppLayout.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour

---

### BUG-2-011 — `AssetManagerPage.tsx` Type-to-API Mapping Fragile
- **Problem:** The asset manager uses string type literals ("background", "prop", "character_template") to route API calls. The backend `_get_service_for_type` maps "character_template" while the frontend `TABS` may use "characters" in some stats key lookups, causing silent mismatches.
- **Root Cause:** No shared enum between frontend and backend for asset type strings.
- **Files:** `frontend/src/pages/studio/AssetManagerPage.tsx`, `backend/apps/api/routers/asset_manager.py`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 2 hours

---

### BUG-2-012 — Missing Delete Confirmation Dialogs
- **Problem:** Where delete buttons exist (e.g., in `AssetManagerPage`), there is no confirmation dialog before deletion. Users can accidentally delete assets.
- **Root Cause:** Confirmation step never implemented.
- **Files:** `frontend/src/pages/studio/AssetManagerPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour

---

## 🟢 LOW PRIORITY

### BUG-2-013 — TypeScript Type Mismatch: `rig_data` on Expression/Pose
- **Problem:** `frontend/src/api/library.ts` types `rig_data` as `Record<string, unknown>` for Expression and Pose interfaces, but there is no Pydantic validation on the backend ensuring the internal structure is consistent. Runtime errors possible if rig_data has unexpected shape.
- **Files:** `frontend/src/api/library.ts`, `backend/database/models/animation.py`
- **Severity:** LOW
- **Estimated Fix Time:** 1 hour

---

### BUG-2-014 — Missing Tests for Phase 2 CRUD Operations
- **Problem:** `test_library.py` covers Expressions, Poses, Backgrounds, Props read + seed. However there are no tests for: Character create/update/delete, CharacterTemplate create/update/delete, `asset_manager.py` bulk operations, upload endpoint, version restore.
- **Files:** `backend/tests/test_library.py`, `backend/tests/test_asset_manager.py`
- **Severity:** LOW
- **Estimated Fix Time:** 4 hours

---

### BUG-2-015 — Missing Empty State on Library Pages
- **Problem:** `CharacterLibraryPage`, `BackgroundLibraryPage`, `PropsLibraryPage` show a blank area when no items exist instead of an informative empty state with a CTA.
- **Files:** All three library pages
- **Severity:** LOW
- **Estimated Fix Time:** 1 hour

---

## Summary

| Category | Count |
|---|---|
| Critical | 2 |
| High | 5 |
| Medium | 5 |
| Low | 3 |
| **Total** | **15** |

**Estimated Total Fix Time:** ~30 hours
