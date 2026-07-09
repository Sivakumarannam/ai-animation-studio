# Phase 3 — Story Intelligence Bug Report

**Audit Date:** 2026-07-09  
**Phase:** Phase 3 — Story Intelligence Engine (Worlds, Seasons, Episodes, Scenes, Ideas, Memory, Jobs, Pipeline)  
**Status:** PRE-FIX — DO NOT DEPLOY

---

## 🔴 CRITICAL BUGS

### BUG-3-001 — `update_idea` Endpoint Only Updates Status Field
- **Problem:** `PATCH /si/ideas/{idea_id}` ignores all fields except `status`. If a user sends a body with `title`, `premise`, `content`, `genre`, `target_audience`, etc., the endpoint silently discards them and only calls `update_status()`. The idea is never actually edited.
- **Root Cause:** Implementation in `story_intelligence.py` (~line 425–435) has a conditional that calls `update_status` when `body.status` is provided and returns the unchanged idea otherwise — never calling a full update service method.
- **Files:** `backend/apps/api/routers/story_intelligence.py` (~line 425), `backend/services/story_intelligence/idea_service.py`
- **Severity:** CRITICAL
- **Estimated Fix Time:** 1 hour — implement `idea_service.update()` and call it in the endpoint

---

### BUG-3-002 — Celery Task Names Mismatch Between Worker and Router Dispatch
- **Problem:** The Celery worker registers tasks named `intelligence.generate_ideas` and `intelligence.analyze_world`, but the story intelligence router dispatches tasks using different names (`si_run_full_pipeline`, `si_generate_episode`). The tasks are never executed by workers — they are enqueued but never consumed.
- **Root Cause:** Worker `asset_tasks.py` uses a different naming convention than the dispatcher in the router.
- **Files:** `backend/apps/worker/tasks/asset_tasks.py`, `backend/apps/worker/tasks/intelligence_tasks.py`, `backend/apps/api/routers/story_intelligence.py`
- **Severity:** CRITICAL (pipeline never actually runs via Celery)
- **Estimated Fix Time:** 2 hours — align task names or create correct task bindings

---

## 🔴 HIGH PRIORITY

### BUG-3-003 — WorldsPage: No Edit World Button/Dialog
- **Problem:** `WorldsPage.tsx` has "New World" creation but no way to edit an existing world's name, description, or settings. Backend has `PATCH /si/worlds/{world_id}`.
- **Root Cause:** Edit dialog never implemented.
- **Files:** `frontend/src/pages/intelligence/WorldsPage.tsx`, `backend/apps/api/routers/story_intelligence.py`
- **Severity:** HIGH
- **Estimated Fix Time:** 2 hours

---

### BUG-3-004 — WorldsPage: No Delete World Button
- **Problem:** Users cannot delete worlds from the UI. Backend has `DELETE /si/worlds/{world_id}` and API client has `deleteWorld()`.
- **Root Cause:** Delete action never wired to UI.
- **Files:** `frontend/src/pages/intelligence/WorldsPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 1 hour (button + confirm dialog)

---

### BUG-3-005 — WorldDetailPage: No Edit/Delete for World Entity
- **Problem:** The world detail page shows world information and seasons list but provides no way to edit world metadata or delete the world from that page.
- **Root Cause:** Read-only implementation.
- **Files:** `frontend/src/pages/intelligence/WorldDetailPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 2 hours

---

### BUG-3-006 — WorldDetailPage: Missing "Add Memory" Form
- **Problem:** `WorldDetailPage.tsx` displays story memories but has no button or form to add a new memory entry. Backend has `POST /si/memory` and API client has `createMemory()`.
- **Root Cause:** Create flow never connected.
- **Files:** `frontend/src/pages/intelligence/WorldDetailPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 1.5 hours

---

### BUG-3-007 — SeasonDetailPage: No Edit/Delete Season
- **Problem:** Season detail page lists episodes and creation form, but no Edit Season or Delete Season UI. Backend supports both operations.
- **Root Cause:** Not implemented.
- **Files:** `frontend/src/pages/intelligence/SeasonDetailPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 2 hours

---

### BUG-3-008 — EpisodeDetailPage: No Edit/Delete Episode or Scene
- **Problem:** Episode detail shows scene list and creation, but no Edit Episode, Delete Episode, Edit Scene, or Delete Scene UI. Backend supports all four.
- **Root Cause:** Not implemented.
- **Files:** `frontend/src/pages/intelligence/EpisodeDetailPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 3 hours

---

### BUG-3-009 — StoryIdeasPage: No Edit/Delete Ideas
- **Problem:** Ideas page has "New Idea" and "Generate Ideas" but no way to edit or delete an existing idea. Backend has update and delete endpoints.
- **Root Cause:** Not implemented. Further compounded by BUG-3-001 (update endpoint is broken anyway).
- **Files:** `frontend/src/pages/intelligence/StoryIdeasPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 2 hours

---

## 🟡 MEDIUM PRIORITY

### BUG-3-010 — No Pagination Controls on WorldsPage and StoryIdeasPage
- **Problem:** Both pages fetch paginated data (page=1, page_size=20 hardcoded) but render no Next/Prev pagination controls. Users with more than 20 worlds or ideas cannot browse.
- **Files:** `frontend/src/pages/intelligence/WorldsPage.tsx`, `frontend/src/pages/intelligence/StoryIdeasPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour

---

### BUG-3-011 — RetryQueuePage is Actually a Jobs Page (Misleading)
- **Problem:** `App.tsx` maps `/projects/:id/intelligence/jobs` to `RetryQueuePage.tsx`, but the page actually shows all generation jobs with status filters, not a dedicated retry queue. The route name and page name are inconsistent.
- **Root Cause:** Page was built as a combined jobs+retry view without renaming the component.
- **Files:** `frontend/src/pages/intelligence/RetryQueuePage.tsx`, `frontend/src/App.tsx`
- **Severity:** MEDIUM (UX confusion)
- **Estimated Fix Time:** 30 min — rename or split

---

### BUG-3-012 — Job Logs TypeScript Type Missing
- **Problem:** `storyIntelligence.ts` `getJobLogs()` returns `{ logs: unknown[] }` but the backend returns structured objects with `step_name`, `duration_ms`, `status`, `output` fields. Frontend cannot safely access these fields.
- **Files:** `frontend/src/api/storyIntelligence.ts`, `backend/apps/api/routers/story_intelligence.py`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 30 min — add `GenerationLog` TypeScript interface

---

### BUG-3-013 — No Loading/Empty States on WorldsPage When World Count is 0
- **Problem:** WorldsPage shows a blank list area when no worlds exist rather than an actionable empty state ("Create your first world").
- **Files:** `frontend/src/pages/intelligence/WorldsPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 30 min

---

### BUG-3-014 — `delete_world` and `delete_season` Don't Check Existence Before Delete
- **Problem:** Backend delete endpoints don't validate that the entity exists before attempting deletion, leading to generic 500 errors instead of informative 404 responses when the ID is invalid.
- **Files:** `backend/apps/api/routers/story_intelligence.py`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour — add existence check in service or router

---

## 🟢 LOW PRIORITY

### BUG-3-015 — Orphaned Ideas When World Is Deleted
- **Problem:** `StoryIdea.world_id` uses `ondelete="SET NULL"`, so deleting a world leaves ideas without a world reference. No frontend filter exists to find or manage orphaned ideas.
- **Files:** `backend/database/models/intelligence.py`, `frontend/src/pages/intelligence/StoryIdeasPage.tsx`
- **Severity:** LOW
- **Estimated Fix Time:** 1 hour — add "Orphaned" filter tab

---

### BUG-3-016 — Analytics Endpoint Uses Raw SQL in Router
- **Problem:** `GET /si/stats` executes manual SQL for aggregate counts directly in the router function. This bypasses the repository layer and makes testing/refactoring harder.
- **Files:** `backend/apps/api/routers/story_intelligence.py`
- **Severity:** LOW (architectural, not user-facing)
- **Estimated Fix Time:** 2 hours — extract into AnalyticsRepository

---

### BUG-3-017 — Missing Tests for CRUD Operations
- **Problem:** `test_story_intelligence.py` exists but CRUD tests for Season, Episode, Scene update/delete, and Memory create/delete are absent. The broken `update_idea` endpoint (BUG-3-001) has no test that would have caught the regression.
- **Files:** `backend/tests/test_story_intelligence.py`
- **Severity:** LOW
- **Estimated Fix Time:** 4 hours

---

## Summary

| Category | Count |
|---|---|
| Critical | 2 |
| High | 7 |
| Medium | 5 |
| Low | 3 |
| **Total** | **17** |

**Estimated Total Fix Time:** ~28 hours
