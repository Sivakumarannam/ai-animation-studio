# Workflow Control — Completion Report

## Summary

Full pause/cancel/delete workflow control has been implemented across the pipeline
executor, REST API, Celery task layer, and frontend dashboard. All 33 backend unit
tests pass; the frontend TypeScript-compiles and Vite-bundles without errors.

---

## Task-by-Task Results

### Task 1 — Dead `_build_pipeline` Removal

**Finding:** `executor.py` contained two definitions of `_build_pipeline`. Python
always uses the **last** definition, making the first (lines 120–131) permanently
unreachable dead code. The first version contained a nonsensical
`__class__.__new__()` hack and never executed.

**Action:** Deleted the dead first definition. The surviving (correct) definition
now lives as the only `_build_pipeline` method.

---

### Task 2 — `pause()` (newly implemented)

`WorkflowExecutor.pause(run_id)` was **not previously implemented**. Added:

- Loads context from Redis.
- Calls `WorkflowStateMachine.transition(state, "pause")` → `PAUSED`.
- Persists updated context back to Redis.
- The running pipeline detects this signal via the `_state_refresher` hook at the
  **next clean step boundary** (never mid-step) and returns early.

Allowed from: `RUNNING` only (state machine enforces this; raises
`InvalidTransitionError` otherwise).

---

### Task 3 — `cancel()` (newly implemented)

`WorkflowExecutor.cancel(run_id)` was **not previously implemented**. Added:

- Loads context from Redis.
- Calls `WorkflowStateMachine.transition(state, "cancel")` → `CANCELLED`.
- Persists updated context back to Redis.
- In-flight Celery tasks detect `CANCELLED` at the next step boundary and exit
  cleanly without running further steps.

Allowed from: `RUNNING`, `PAUSED`, `PENDING`.

---

### Task 4 — `delete()` (newly implemented)

`WorkflowExecutor.delete(run_id)` was **not previously implemented**. Added:

- Loads context from Redis to validate state before deletion.
- **Guard:** raises `ValueError` if state is not `COMPLETED`, `CANCELLED`, or
  `FAILED`. Active runs must be cancelled first.
- On success: deletes the Redis key permanently.

---

### Task 5 — REST API router (`backend/apps/api/routers/workflow.py`)

New router registered at `/api/v1/workflow`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/workflow/runs` | List all runs; optional `?project_id=` filter |
| `GET` | `/workflow/runs/{run_id}` | Get single run status |
| `POST` | `/workflow/runs` | Start new run (dispatches Celery task, returns `run_id` immediately) |
| `POST` | `/workflow/runs/{run_id}/pause` | Pause a RUNNING workflow |
| `POST` | `/workflow/runs/{run_id}/resume` | Resume a PAUSED/FAILED workflow |
| `POST` | `/workflow/runs/{run_id}/cancel` | Cancel a RUNNING/PAUSED workflow |
| `DELETE` | `/workflow/runs/{run_id}` | Delete a terminal-state workflow run |

**Start design:** The API generates a `run_id` upfront, persists a `PENDING`
context to Redis immediately, then dispatches the Celery task. This means
`GET /runs/{run_id}` works from the first millisecond after `POST /runs` returns,
with no race window where status polling returns 404.

All endpoints require `CurrentUser` authentication.

---

### Task 6 — Celery tasks (`backend/apps/worker/tasks/workflow_tasks.py`)

Three changes:

1. **`run_pipeline`** — added optional `run_id: str | None = None` kwarg. When
   provided (from the API), the existing `run_id` is passed into `WorkflowContext`
   so the pre-saved PENDING context is adopted rather than generating a new ID.

2. **`pause_run`** (new) — thin Celery wrapper for `executor.pause()`, queued on
   `"default"`.

3. **`cancel_run`** (new) — thin Celery wrapper for `executor.cancel()`, queued on
   `"default"`.

---

### Task 7 — Frontend

Three frontend deliverables:

**`frontend/src/api/workflow.ts`** — typed API client with `workflowApi.*` methods
for all 7 endpoints, plus the `PIPELINE_STEPS` array (7 steps in pipeline order)
and the `WorkflowRun` / `WorkflowState` types.

**`frontend/src/pages/workflow/WorkflowPipelinePage.tsx`** — "Automation Pipeline"
dashboard featuring:
- Per-run cards showing state, progress bar, per-step status badges (✓ done,
  ✗ failed, ⟳ active, ○ pending), error detail, and timestamps.
- Step pipeline rendered inline: Story → Scenes → Characters → Assets → Voice →
  Subtitles → Video.
- Context-sensitive action buttons: Pause (running), Resume (paused/failed),
  Cancel (active), Delete (terminal).
- "Start New Pipeline Run" inline form.
- Auto-polls every 3 s when any run is RUNNING/PENDING; backs off to 15 s when idle.

**Route + nav card:**
- `App.tsx`: `<Route path="/projects/:projectId/pipeline" element={<WorkflowPipelinePage />} />`
- `ProjectDetailPage.tsx`: "Automation Pipeline" card added to the project sections
  grid (icon: `GitBranch`, links to `/projects/:projectId/pipeline`).

---

### Task 8 — Tests (`backend/tests/test_workflow_control.py`)

33 tests across 6 suites, all passing:

| Suite | Tests | What it covers |
|-------|-------|----------------|
| `TestStateMachine` | 6 | SM transitions: pause, cancel, resume, invalid |
| `TestExecutorPause` | 4 | pause() success, Redis persistence, guard on wrong state, missing run |
| `TestExecutorCancel` | 6 | cancel() from RUNNING/PAUSED/PENDING, persistence, guards |
| `TestExecutorDelete` | 4 | delete allowed for 3 terminal states, blocked for 3 active states, missing run, constant |
| `TestPipelineInterrupt` | 5 | Halt on PAUSED, halt on CANCELLED, full run without interrupt, no-refresher backward-compat, inter-step boundary detection |
| `TestResumeSkipsCompletedSteps` | 1 | Resume skips steps in completed_steps, runs only incomplete steps |
| `TestListRuns` | 3 | list all, filter by project_id, empty result |

**Notable bug found and fixed during testing:**

`_refresh_state` was reading all state values from Redis, including the stale
`PENDING` state written by `execute()` before the pipeline started. This caused
the in-flight pipeline's `RUNNING` state to be overwritten with `PENDING` on the
first refresh, breaking subsequent SM transitions. **Fix:** `_refresh_state` now
only applies `PAUSED` and `CANCELLED` from Redis — the two states that represent
external control signals. All other Redis states are ignored to avoid downgrading
a live in-flight state.

---

### Extra Bug Found During Startup — FastAPI + `from __future__ import annotations` + 204

`workflow.py` uses `from __future__ import annotations` (PEP 563 lazy annotations).
With this active, `-> None` return annotations are stored as the *string* `"None"`.
FastAPI evaluates that string via `typing.get_type_hints()` and resolves it to
`NoneType` — a class object, which is **truthy**. FastAPI then treats `NoneType` as
the inferred `response_model` and hits its own assertion:
`"Status code 204 must not have a response body"`.

**Fix:** added `response_model=None` explicitly to the `@router.delete` decorator.
When an explicit `None` is passed, FastAPI skips the type-hint inference path and
leaves `response_model` as `None` (falsy), bypassing the assertion. All other
existing 204 routes in the project don't use `from __future__ import annotations`,
so they were unaffected.

---

### Tasks 9 & 10 — Verification

**Backend tests:** `33 passed in 0.14s` ✓

**Frontend build:**
```
✓ 1757 modules transformed.
✓ built in 4.20s
```
TypeScript compiles, Vite bundles. ✓

---

## Scope Boundary (Explicit)

The following steps were intentionally **NOT** added to the pipeline and were
**NOT** touched:

- Thumbnail generation
- SEO metadata generation
- YouTube / social publish

The pipeline ends at `VideoRenderStep` (`video_render`), exactly as specified.
The 7-step sequence is:
`story_generation → scene_breakdown → character_resolution → asset_generation → voice_generation → subtitle_generation → video_render`

---

## Files Changed

| File | Change |
|------|--------|
| `backend/workflow/executor.py` | Removed dead `_build_pipeline`; added `pause()`, `cancel()`, `delete()`, `list_runs()`, `_refresh_state()` (control-signal-only); `_build_pipeline` now passes state-refresher closure to Pipeline |
| `backend/workflow/pipeline.py` | Added `state_refresher` param to `Pipeline.__init__` and `PipelineBuilder`; interrupt check (PAUSED/CANCELLED) at top of each step iteration |
| `backend/apps/api/routers/workflow.py` | **New** — 7-endpoint workflow control router |
| `backend/apps/api/main.py` | Registered `workflow_router` on `v1` |
| `backend/apps/worker/tasks/workflow_tasks.py` | `run_pipeline` accepts optional `run_id`; added `pause_run` and `cancel_run` Celery tasks |
| `frontend/src/api/workflow.ts` | **New** — typed API client |
| `frontend/src/pages/workflow/WorkflowPipelinePage.tsx` | **New** — "Automation Pipeline" dashboard |
| `frontend/src/App.tsx` | Added import + `/projects/:projectId/pipeline` route |
| `frontend/src/pages/projects/ProjectDetailPage.tsx` | Added "Automation Pipeline" nav card |
| `backend/tests/test_workflow_control.py` | **New** — 33 unit tests |
