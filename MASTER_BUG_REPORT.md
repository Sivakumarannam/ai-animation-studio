# Master Bug Report — AI Animation Studio, Phases 2–5

**Audit Date:** 2026-07-09  
**Auditor:** AI Agent  
**Scope:** Production readiness audit of Phases 2, 3, 4, and 5  
**Method:** Full codebase inspection — frontend pages, API clients, backend routers, services, repositories, database models, Celery tasks, worker registration, provider factory, migrations, navigation, tests  
**Status:** PRE-FIX — AWAITING APPROVAL

---

## EXECUTIVE SUMMARY

| Phase | Critical | High | Medium | Low | Total | Est. Fix |
|---|---|---|---|---|---|---|
| Phase 2 — Animation Engine | 2 | 5 | 5 | 3 | **15** | ~30h |
| Phase 3 — Story Intelligence | 2 | 7 | 5 | 3 | **17** | ~28h |
| Phase 4 — Knowledge Intelligence | 0 | 5 | 5 | 3 | **13** | ~22h |
| Phase 5 — Research Intelligence | 0 | 4 | 6 | 4 | **14** | ~26h |
| **TOTAL** | **4** | **21** | **21** | **13** | **59** | **~106h** |

---

## 🔴 ALL CRITICAL BUGS (Fix First)

### CRIT-1 — Route Shadowing: `/library/backgrounds` and `/library/props` Registered Twice
- **Phase:** 2
- **Problem:** Both `assets.py` (read-only stubs) and `library.py` (full CRUD) define `GET /library/backgrounds` and `GET /library/props`. Both are mounted in `main.py`. FastAPI silently uses whichever was registered first, making CRUD mutations (POST/PATCH/DELETE) for backgrounds and props unreachable via the expected handler.
- **Root Cause:** `assets.py` is a legacy stub never removed after `library.py` was written.
- **Files:** `backend/apps/api/routers/assets.py`, `backend/apps/api/routers/library.py`, `backend/apps/api/main.py`
- **Fix:** Remove background/prop route definitions from `assets.py` and keep only the full CRUD in `library.py`.
- **Severity:** CRITICAL | **Fix Time:** 30 min

---

### CRIT-2 — Characters Page Missing Edit and Delete
- **Phase:** 2
- **Problem:** Users cannot edit or delete characters. The backend has `PATCH /characters/{id}` and `DELETE /characters/{id}` but no UI exists for either operation.
- **Files:** `frontend/src/pages/characters/CharactersPage.tsx`
- **Fix:** Add edit dialog + delete confirmation button.
- **Severity:** CRITICAL | **Fix Time:** 3h

---

### CRIT-3 — `update_idea` Endpoint Only Updates `status` Field
- **Phase:** 3
- **Problem:** `PATCH /si/ideas/{idea_id}` discards all fields except `status`. A user editing an idea's title or content sees no change.
- **Files:** `backend/apps/api/routers/story_intelligence.py` (~line 425), idea service
- **Fix:** Implement full update in `idea_service.update()` and call it in the endpoint.
- **Severity:** CRITICAL | **Fix Time:** 1h

---

### CRIT-4 — Celery Task Names Mismatch (Phase 2, 3, 4, 5)
- **Phase:** 2, 3, 4, 5
- **Problem:** Celery workers register tasks under names like `intelligence.generate_ideas`, `research.fetch_trends`, `knowledge.index_document`, `assets.process_upload`. The routers dispatch using different names (`si_run_full_pipeline`, `rs_discover_trends`, `kn_process_document`). Tasks are enqueued but never consumed by workers.
- **Files:** `backend/apps/worker/tasks/*.py`, all phase routers
- **Fix:** Audit and align all task names across dispatcher calls and worker registration.
- **Severity:** CRITICAL | **Fix Time:** 2h

---

## 🔴 ALL HIGH PRIORITY BUGS

### H-01 — No Character Image Upload (Phase 2)
`CharactersPage.tsx` — no file upload for character images. Backend supports multipart upload. **Fix Time: 4h**

### H-02 — AssetManagerPage: `duration_seconds` Hardcoded to 5.0 (Phase 2)
`AssetManagerPage.tsx` line ~92 hardcodes audio duration. **Fix Time: 2h**

### H-03 — CharacterLibraryPage: List Only (Phase 2)
No Create/Edit/Delete for character templates. Backend has full CRUD. **Fix Time: 4h**

### H-04 — BackgroundLibraryPage: List Only (Phase 2)
No Create/Edit/Delete for backgrounds. Backend has full CRUD. **Fix Time: 3h**

### H-05 — PropsLibraryPage: List Only (Phase 2)
No Create/Edit/Delete for props. Backend has full CRUD. **Fix Time: 3h**

### H-06 — WorldsPage: No Edit or Delete World (Phase 3)
Two separate missing operations on the same page. Backend has both. **Fix Time: 3h**

### H-07 — WorldDetailPage: No Edit/Delete World Entity (Phase 3)
Detail page is read-only. **Fix Time: 2h**

### H-08 — WorldDetailPage: No Add Memory Form (Phase 3)
Memory list shown but no create form. **Fix Time: 1.5h**

### H-09 — SeasonDetailPage: No Edit/Delete Season (Phase 3)
Both operations missing. **Fix Time: 2h**

### H-10 — EpisodeDetailPage: No Edit/Delete Episode or Scene (Phase 3)
Four missing operations. **Fix Time: 3h**

### H-11 — StoryIdeasPage: No Edit/Delete Ideas (Phase 3)
Backend has endpoints; UI missing. **Fix Time: 2h**

### H-12 — DocumentDetailPage Missing (Phase 4)
No page to inspect document chunks. Backend has the endpoints. **Fix Time: 4h**

### H-13 — KnowledgeMemoryPage: Cannot Create Memories (Phase 4)
No create form despite API support. **Fix Time: 2h**

### H-14 — KnowledgeMemoryPage: Cannot Delete Memories (Phase 4)
Only deactivate available. **Fix Time: 1h**

### H-15 — CollectionDetailPage: No Edit Collection (Phase 4)
No edit form for collection name/description. **Fix Time: 1.5h**

### H-16 — EmbeddingJobsPage: No Pagination Controls (Phase 4)
First-page only. **Fix Time: 1h**

### H-17 — No Backend Tests for Research Phase (Phase 5)
Core pipeline has no regression protection. **Fix Time: 4h**

### H-18 — TopicExplorerPage: No Delete or Edit Topic (Phase 5)
Both operations missing. **Fix Time: 2.5h**

### H-19 — Missing ResearchSourcesPage (Phase 5)
No UI for managing RSS/crawl sources. **Fix Time: 4h**

---

## 🟡 ALL MEDIUM PRIORITY BUGS

### M-01 — No Pagination Controls (Phase 2, 3, 4)
Affected pages: `CharactersPage`, `CharacterLibraryPage`, `BackgroundLibraryPage`, `PropsLibraryPage`, `WorldsPage`, `StoryIdeasPage`, `KnowledgeMemoryPage`. **Total Fix Time: 3h**

### M-02 — `assets.py` Endpoints are Dead Code (Phase 2)
Never called by frontend; shadowing library.py. **Fix Time: 30 min**

### M-03 — Missing Navigation Links for Phase 3/4 in AppLayout Sidebar (Phase 2/3/4)
Intelligence and Knowledge links not in sidebar. **Fix Time: 1h**

### M-04 — AssetManagerPage Type Mapping Fragile (Phase 2)
String-based type routing between frontend and backend. **Fix Time: 2h**

### M-05 — Missing Delete Confirmation Dialogs (Phase 2)
`AssetManagerPage` has no confirm step before deletion. **Fix Time: 1h**

### M-06 — RetryQueuePage Name/Route Mismatch (Phase 3)
Page is a jobs list, not a retry queue. **Fix Time: 30 min**

### M-07 — Job Logs TypeScript Types Missing (Phase 3)
`getJobLogs` returns `unknown[]`. **Fix Time: 30 min**

### M-08 — No Loading/Empty States on WorldsPage (Phase 3)
Blank area when no worlds exist. **Fix Time: 30 min**

### M-09 — `delete_world`/`delete_season` No Existence Check (Phase 3)
500 instead of 404 for invalid IDs. **Fix Time: 1h**

### M-10 — CollectionsPage: No Edit Collection (Phase 4)
Cannot rename collections. **Fix Time: 1h**

### M-11 — No Pagination Controls on KnowledgeMemoryPage (Phase 4)
**Fix Time: 30 min**

### M-12 — Missing Route for DocumentDetailPage in App.tsx (Phase 4)
Prerequisite for H-12. **Fix Time: 15 min**

### M-13 — No Loading State on Re-Embedding Trigger (Phase 4)
Double-click risk. **Fix Time: 30 min**

### M-14 — RAG Not Integrated Into Story Generation Pipeline (Phase 4)
Phase 3 pipeline does not use Phase 4 retrieval. **Fix Time: 6h**

### M-15 — FactVerificationPage/ResearchLibraryPage: Hardcoded `items[0]` Selection (Phase 5)
No topic selector. **Fix Time: 2h**

### M-16 — `getAnalytics` Returns Untyped Response (Phase 5)
**Fix Time: 30 min**

### M-17 — OpportunityBoardPage: No "Send to Story Intelligence" Button (Phase 5)
Cross-phase workflow missing. **Fix Time: 2h**

### M-18 — Knowledge Integration Has No UI (Phase 5)
Research→Knowledge push has no frontend surface. **Fix Time: 3h**

### M-19 — TrendExplorerPage: List Only (Phase 5)
No manual create/edit/archive. **Fix Time: 2h**

### M-20 — ResearchLibraryPage: Topic Selector Missing (Phase 5)
Same as M-15. **Fix Time: 1h**

### M-21 — Analytics in Story Intelligence Router Uses Raw SQL (Phase 3)
Should use repository layer. **Fix Time: 2h**

---

## 🟢 ALL LOW PRIORITY BUGS

### L-01 — TypeScript `rig_data` Type Mismatch (Phase 2) — **Fix Time: 1h**
### L-02 — Missing Tests for Phase 2 CRUD (Phase 2) — **Fix Time: 4h**
### L-03 — Missing Empty States on Library Pages (Phase 2) — **Fix Time: 1h**
### L-04 — Orphaned Ideas When World Deleted (Phase 3) — **Fix Time: 1h**
### L-05 — Missing Tests for Phase 3 CRUD (Phase 3) — **Fix Time: 4h**
### L-06 — Celery Task Names Mismatch — Knowledge (Phase 4) — **Fix Time: 1h**
### L-07 — Missing Empty State on KnowledgeMemoryPage (Phase 4) — **Fix Time: 30 min**
### L-08 — Missing Tests for Knowledge CRUD (Phase 4) — **Fix Time: 3h**
### L-09 — Missing Loading/Empty States in ResearchDashboard (Phase 5) — **Fix Time: 1h**
### L-10 — FactVerificationPage Pagination Display Issue (Phase 5) — **Fix Time: 15 min**
### L-11 — Research Celery Task Names Mismatch (Phase 5) — **Fix Time: 1h**
### L-12 — Scheduler Page Missing Next Run Time (Phase 5) — **Fix Time: 1h**
### L-13 — Missing Tests: Phase 4/5 Coverage Gaps — **Fix Time: 3h**

---

## CROSS-CUTTING SYSTEMIC ISSUES

### SYS-1 — Celery Task Name Convention Not Enforced
**Impact:** All phases. Tasks in worker files use dot-notation (`phase.action`) but dispatchers use snake_case (`phase_action`). This is a systemic inconsistency that causes Celery to enqueue tasks no worker knows how to execute. Result: all async background jobs silently fall through to sync execution (if TaskDispatcher has a fallback) or are lost.  
**Fix:** Establish and enforce a single convention. Recommend: snake_case module-prefixed names (`si_generate_episode`, `kn_process_document`, `rs_discover_trends`). Update all worker files to match.

### SYS-2 — No Pagination UI Reuse Component
**Impact:** Every page reinvents pagination or omits it. A shared `<Pagination>` React component would fix M-01 and similar issues across all phases simultaneously.  
**Fix:** Create `frontend/src/components/ui/Pagination.tsx` and use it in all list pages.

### SYS-3 — Missing Delete Confirmation Component
**Impact:** Phase 2, 3, 4, 5. Delete operations either have no confirm dialog or each implements their own. Risk of accidental data loss.  
**Fix:** Create `frontend/src/components/ui/ConfirmDialog.tsx` reusable across all phases.

### SYS-4 — Navigation Does Not Reflect Phase 3/4 Features
**Impact:** Users must know URLs to access Story Intelligence and Knowledge Intelligence. `AppLayout.tsx` sidebar never received entries for these phases.  
**Fix:** Add sidebar sections for Intelligence and Knowledge with project-scoped links.

---

## FIX EXECUTION ORDER

Per the spec, fix one phase completely before moving to the next.

### Phase 2 Fix Order:
1. CRIT-1 (route shadowing) — immediate, unblocks all background/prop CRUD
2. CRIT-2 (characters edit/delete)
3. H-01 (character image upload)
4. H-02 (audio duration hardcode)
5. H-03, H-04, H-05 (library CRUD)
6. M-01 (pagination controls)
7. M-02, M-03, M-04, M-05 (dead code, nav, type mapping, confirm dialogs)
8. L-01, L-02, L-03 (types, tests, empty states)

### Phase 3 Fix Order:
1. CRIT-3 (update_idea broken) — immediate
2. CRIT-4 (Celery task names) — audit all phases together
3. H-06 through H-11 (missing CRUD operations)
4. M-06 through M-09, M-21
5. L-04, L-05

### Phase 4 Fix Order:
1. H-12, M-12 (DocumentDetailPage + route)
2. H-13, H-14 (memory create/delete)
3. H-15 (collection edit)
4. H-16, M-11, M-13 (pagination, loading)
5. M-14 (RAG integration — largest item)
6. L-06, L-07, L-08

### Phase 5 Fix Order:
1. H-17 (write tests first — guides finding more bugs)
2. H-18 (topic delete/edit)
3. H-19 (ResearchSourcesPage)
4. M-15 through M-20
5. L-09 through L-13

---

## FILES NOT TOUCHED BY BUGS (Confirmed Working)

- `backend/apps/api/routers/auth.py` — ✅ Tested
- `backend/apps/api/routers/projects.py` — ✅ Tested
- `backend/apps/api/routers/health.py` — ✅ No issues
- `backend/apps/api/routers/expressions.py` — ✅ Full CRUD, tested
- `backend/apps/api/routers/poses.py` — ✅ Full CRUD, tested
- `backend/database/connection.py` — ✅ Fixed in prior session (NullPool, session_scope)
- `backend/agents/registry.py` — ✅ Correct
- `backend/agents/provider_factory.py` — ✅ Correct
- Phase 4 document upload flow — ✅ Works end-to-end
- Phase 5 Dashboard, Scheduler, Queue, Jobs pages — ✅ Auto-refresh working
- Phase 5 Opportunity Board — ✅ Scoring displays correctly

---

*This report was generated by comprehensive automated codebase audit. All findings are based on direct code inspection of frontend pages, API clients, backend routers, services, Celery tasks, and test files. No code was modified during this audit.*
