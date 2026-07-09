# Phase 4 — Knowledge Intelligence Bug Report

**Audit Date:** 2026-07-09  
**Phase:** Phase 4 — RAG & Knowledge Intelligence Engine (Collections, Documents, Chunks, Embeddings, Semantic Search, Memory)  
**Status:** PRE-FIX — DO NOT DEPLOY

---

## 🔴 HIGH PRIORITY

### BUG-4-001 — Missing Document Detail Page and Chunk Viewer
- **Problem:** Users can upload and list documents in `CollectionDetailPage.tsx`, but clicking a document does nothing — there is no `DocumentDetailPage.tsx`. Users cannot view individual chunks, their text content, embedding status, or metadata. Backend has `GET /kn/collections/{id}/documents/{doc_id}` and `GET /kn/documents/{doc_id}/chunks` endpoints, and the API client has the corresponding functions.
- **Root Cause:** Page component was never created. The feature was left at the list level.
- **Files:** `frontend/src/pages/knowledge/CollectionDetailPage.tsx`, `frontend/src/api/knowledge.ts` (has `getDocument`, `getChunks`), `backend/apps/api/routers/knowledge.py`
- **Severity:** HIGH (fundamental feature of a knowledge system — inspecting what was indexed)
- **Estimated Fix Time:** 4 hours — create `DocumentDetailPage.tsx` with chunk list and metadata view

---

### BUG-4-002 — KnowledgeMemoryPage: Cannot Create New Memory Entries
- **Problem:** `KnowledgeMemoryPage.tsx` lists existing memory items but has no Create button or form. Backend has `POST /kn/memory` and API client has `createMemory()`. Users cannot manually add facts, rules, or lore.
- **Root Cause:** Create flow never implemented.
- **Files:** `frontend/src/pages/knowledge/KnowledgeMemoryPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 2 hours

---

### BUG-4-003 — KnowledgeMemoryPage: Cannot Delete Memory Entries
- **Problem:** Memory page only has a "Deactivate" button (soft-disable), not a Delete button. Backend has `DELETE /kn/memory/{id}`. Deactivated memories clutter the list indefinitely.
- **Root Cause:** Delete was intentionally replaced with deactivate but no delete escape hatch was added.
- **Files:** `frontend/src/pages/knowledge/KnowledgeMemoryPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 1 hour

---

### BUG-4-004 — CollectionDetailPage: No Edit Collection Button
- **Problem:** Collection detail page shows collection info (name, description, document count) but has no way to edit the collection name or description. Backend has `PATCH /kn/collections/{id}` and API client has `updateCollection()`.
- **Root Cause:** Edit form/dialog never implemented.
- **Files:** `frontend/src/pages/knowledge/CollectionDetailPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 1.5 hours

---

### BUG-4-005 — EmbeddingJobsPage: No Pagination Controls
- **Problem:** `EmbeddingJobsPage.tsx` fetches jobs but has no Next/Prev pagination controls. With many embedding jobs, users can only see the first page.
- **Root Cause:** Pagination state not connected to UI.
- **Files:** `frontend/src/pages/knowledge/EmbeddingJobsPage.tsx`
- **Severity:** HIGH (usability degradation as data grows)
- **Estimated Fix Time:** 1 hour

---

## 🟡 MEDIUM PRIORITY

### BUG-4-006 — CollectionsPage: No Edit Collection
- **Problem:** `CollectionsPage.tsx` has List and Delete but no Edit Collection button/dialog. Users cannot rename collections.
- **Files:** `frontend/src/pages/knowledge/CollectionsPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour

---

### BUG-4-007 — KnowledgeMemoryPage: No Pagination Controls
- **Problem:** Memory list is fetched but has no pagination UI. Memory items grow indefinitely and users cannot browse beyond the first page.
- **Files:** `frontend/src/pages/knowledge/KnowledgeMemoryPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 30 min

---

### BUG-4-008 — No Route for Document Detail in App.tsx
- **Problem:** Even after creating `DocumentDetailPage.tsx` (BUG-4-001 fix), there is no route registered in `App.tsx` for it. The page cannot be navigated to.
- **Root Cause:** Missing route registration.
- **Files:** `frontend/src/App.tsx`
- **Severity:** MEDIUM (blocker for BUG-4-001 fix)
- **Estimated Fix Time:** 15 min

---

### BUG-4-009 — Missing Loading State When Triggering Re-Embedding
- **Problem:** When a user triggers collection re-embedding (embedding job dispatch), there is no loading/pending state shown. The button does not disable during the async dispatch, allowing double-click submissions.
- **Files:** `frontend/src/pages/knowledge/EmbeddingJobsPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 30 min

---

### BUG-4-010 — RAG Retrieval Not Integrated Into Story Intelligence Pipeline
- **Problem:** Phase 4 provides a semantic search/retrieval API (`POST /kn/collections/{id}/search`), but Phase 3's story generation pipeline does not pass retrieved knowledge context to the LLM. The RAG system exists in isolation.
- **Root Cause:** Integration between Phase 3 and Phase 4 never implemented.
- **Files:** `backend/services/story_intelligence/`, `backend/services/knowledge/`, `backend/apps/worker/tasks/intelligence_tasks.py`
- **Severity:** MEDIUM (core cross-phase feature)
- **Estimated Fix Time:** 6 hours

---

## 🟢 LOW PRIORITY

### BUG-4-011 — Celery Task Names Mismatch (Knowledge)
- **Problem:** Worker `knowledge_tasks.py` registers tasks as `knowledge.index_document` and `knowledge.query_collection`, but the knowledge router dispatches `kn_process_document`. Names don't match, meaning Celery workers may not pick up knowledge tasks.
- **Files:** `backend/apps/worker/tasks/knowledge_tasks.py`, `backend/apps/api/routers/knowledge.py`
- **Severity:** LOW (may work if dispatcher falls back to sync)
- **Estimated Fix Time:** 1 hour — verify and align task names

---

### BUG-4-012 — Missing Empty State on KnowledgeMemoryPage
- **Problem:** When memory list is empty, page shows a blank area with no guidance for users.
- **Files:** `frontend/src/pages/knowledge/KnowledgeMemoryPage.tsx`
- **Severity:** LOW
- **Estimated Fix Time:** 30 min

---

### BUG-4-013 — Missing Tests for Knowledge CRUD
- **Problem:** `test_knowledge.py` exists but does not cover: Document update, Memory CRUD, Collection update, semantic search result validation, or chunk metadata verification.
- **Files:** `backend/tests/test_knowledge.py`
- **Severity:** LOW
- **Estimated Fix Time:** 3 hours

---

## Summary

| Category | Count |
|---|---|
| Critical | 0 |
| High | 5 |
| Medium | 5 |
| Low | 3 |
| **Total** | **13** |

**Estimated Total Fix Time:** ~22 hours
