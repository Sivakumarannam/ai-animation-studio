# Phase 5 — Research & Trend Intelligence Bug Report

**Audit Date:** 2026-07-09  
**Phase:** Phase 5 — Research & Trend Intelligence Engine (Trends, Topics, Facts, Opportunities, Scheduler, Analytics, History)  
**Status:** PRE-FIX — DO NOT DEPLOY

---

## 🔴 HIGH PRIORITY

### BUG-5-001 — Missing Backend Tests for Research Phase
- **Problem:** `test_research.py` exists in `backend/tests/` but inspection reveals it contains minimal or no coverage for: trend discovery pipeline trigger, topic research dispatch, fact verification scoring, opportunity scoring service, scheduler tick, or research history. Core pipeline functionality has no regression protection.
- **Root Cause:** Tests were not written alongside Phase 5 implementation.
- **Files:** `backend/tests/test_research.py`
- **Severity:** HIGH
- **Estimated Fix Time:** 4 hours — write tests for API endpoints, Celery task dispatch, and opportunity scoring

---

### BUG-5-002 — TopicExplorerPage: No Delete Topic Button
- **Problem:** `TopicExplorerPage.tsx` lists research topics and has a Create Topic form, but no Delete button on any topic row. Backend has `DELETE /rs/topics/{topic_id}` and API client has `deleteTopic()`.
- **Root Cause:** Delete UI never added.
- **Files:** `frontend/src/pages/research/TopicExplorerPage.tsx`
- **Severity:** HIGH (accumulates stale topics with no cleanup path)
- **Estimated Fix Time:** 1 hour

---

### BUG-5-003 — TopicExplorerPage: No Edit Topic Button
- **Problem:** Topics cannot be edited after creation. Backend has `PATCH /rs/topics/{topic_id}` and API client has `updateTopic()`.
- **Root Cause:** Edit dialog never implemented.
- **Files:** `frontend/src/pages/research/TopicExplorerPage.tsx`
- **Severity:** HIGH
- **Estimated Fix Time:** 1.5 hours

---

### BUG-5-004 — Missing Research Source Management Page
- **Problem:** There is no frontend page for managing research sources (RSS feeds, seed URLs, crawl configuration). Backend has full CRUD: `GET/POST/PATCH/DELETE /rs/sources`. API client has corresponding functions. Without source management, users cannot configure what the research engine crawls.
- **Root Cause:** Page was never created. No `ResearchSourcesPage.tsx` exists. No route in `App.tsx`.
- **Files:** `frontend/src/pages/research/` (missing), `frontend/src/App.tsx`, `backend/apps/api/routers/research.py`
- **Severity:** HIGH (sources drive the entire research pipeline)
- **Estimated Fix Time:** 4 hours — create page + add route

---

## 🟡 MEDIUM PRIORITY

### BUG-5-005 — FactVerificationPage: Hardcoded First Topic Selection
- **Problem:** `FactVerificationPage.tsx` (and `ResearchLibraryPage.tsx`) auto-select `items[0]` — the first topic in the list — as the active topic, with no user-selectable topic dropdown. If the first topic is unrelated to what the user wants to see, the page is stuck showing wrong data.
- **Root Cause:** State management for topic selection was never added.
- **Files:** `frontend/src/pages/research/FactVerificationPage.tsx`, `frontend/src/pages/research/ResearchLibraryPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour each (2 files)

---

### BUG-5-006 — `getAnalytics` Returns Untyped `Record<string, unknown>[]`
- **Problem:** `frontend/src/api/research.ts` types the `getAnalytics` response as `Record<string, unknown>[]`. Frontend code cannot safely access analytics fields (trend counts, topic metrics, etc.) without type assertions.
- **Root Cause:** TypeScript interface for analytics response never defined.
- **Files:** `frontend/src/api/research.ts`, `frontend/src/pages/research/TrendAnalyticsPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 30 min — define `ResearchAnalytics` interface matching backend schema

---

### BUG-5-007 — OpportunityBoardPage: No "Send to Story Intelligence" Button
- **Problem:** Opportunity scores are computed and displayed, but there is no button to send a high-scoring opportunity directly to the Story Intelligence pipeline (create a Story Idea from it). This is a critical cross-phase workflow link.
- **Root Cause:** Cross-phase integration action never implemented.
- **Files:** `frontend/src/pages/research/OpportunityBoardPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 2 hours

---

### BUG-5-008 — Knowledge Integration Has No Dedicated UI
- **Problem:** The research engine can push discovered facts to the Knowledge Intelligence (Phase 4) store. This is visible as a stat on the dashboard (`knowledge_docs_created`), but there is no UI page or button for users to trigger, review, or manage this integration. Users cannot see which research results were added to which knowledge collection.
- **Root Cause:** Integration service exists in backend but no frontend surface was built.
- **Files:** `frontend/src/pages/research/`, `backend/apps/api/routers/research.py`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 3 hours

---

### BUG-5-009 — TrendExplorerPage: List Only, No Create/Edit/Delete Trend
- **Problem:** Trends are discovered automatically, but users cannot manually add, edit, or archive trend entries. Backend has trend management endpoints. With no manual override, incorrect or outdated trends persist.
- **Files:** `frontend/src/pages/research/TrendExplorerPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 2 hours

---

### BUG-5-010 — ResearchLibraryPage: Topic Selector Broken
- **Problem:** Same issue as BUG-5-005. Uses first-item auto-selection. If a user has multiple research topics, they cannot browse articles for a specific one.
- **Files:** `frontend/src/pages/research/ResearchLibraryPage.tsx`
- **Severity:** MEDIUM
- **Estimated Fix Time:** 1 hour

---

## 🟢 LOW PRIORITY

### BUG-5-011 — Missing Loading/Empty States in ResearchDashboardPage Sub-Components
- **Problem:** Some dashboard widgets (trend velocity chart, opportunity list) show blank areas while loading and display nothing when empty. No spinner or empty state message.
- **Files:** `frontend/src/pages/research/ResearchDashboardPage.tsx`
- **Severity:** LOW
- **Estimated Fix Time:** 1 hour

---

### BUG-5-012 — FactVerificationPage Pagination Controls Potentially Obscured
- **Problem:** Pagination prev/next controls exist in code but may not render when `total_pages <= 1`, which is the common case when a topic has few facts. Users may not realize more pages exist.
- **Files:** `frontend/src/pages/research/FactVerificationPage.tsx`
- **Severity:** LOW
- **Estimated Fix Time:** 15 min — always show page indicator even when on page 1

---

### BUG-5-013 — Research Celery Task Names Mismatch
- **Problem:** Worker `research_tasks.py` registers tasks as `research.fetch_trends`, `research.crawl_topic`, `research.analyze_sentiment`, `research.generate_report`, `research.fact_check`, `research.schedule_crawls`. Router dispatches using `rs_discover_trends`, `rs_research_topic`, `rs_scheduler_tick`, etc. Names don't match.
- **Files:** `backend/apps/worker/tasks/research_tasks.py`, `backend/apps/api/routers/research.py`
- **Severity:** LOW (may fall back to sync via TaskDispatcher, masking the issue)
- **Estimated Fix Time:** 1 hour

---

### BUG-5-014 — Scheduler Page Does Not Show Next Run Time
- **Problem:** `SchedulerStatusPage.tsx` shows scheduler status but does not display when the next scheduled run will occur, or a countdown. Backend likely has this information.
- **Files:** `frontend/src/pages/research/SchedulerStatusPage.tsx`
- **Severity:** LOW
- **Estimated Fix Time:** 1 hour

---

## Summary

| Category | Count |
|---|---|
| Critical | 0 |
| High | 4 |
| Medium | 6 |
| Low | 4 |
| **Total** | **14** |

**Estimated Total Fix Time:** ~26 hours
