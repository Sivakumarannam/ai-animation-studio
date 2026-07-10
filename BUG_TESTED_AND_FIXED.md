# AI Animation Studio — Local Setup, Bugs Found & Fixed, Testing Log

**Date:** July 8, 2026
**Environment:** Local Windows laptop (Git Bash / MINGW64), Docker Desktop, Python 3.11.9, Node/npm 11.13.0
**Scope:** Fresh local clone → environment setup → Phase 1 verification (per the 14-step verification plan)

---

## 1. Environment Setup Summary

| Step | Component | Result |
|---|---|---|
| 1 | `git pull` latest code (Phase 5 + Phase 6 in progress) | ✅ Done |
| 2 | Python venv + `pip install -r requirements.txt` | ✅ Done, all packages installed clean |
| 2 | Frontend `npm install` | ⚠️ Failed first, fixed (see Bug #1), then ✅ |
| 3 | Docker Compose: Postgres, Redis, MinIO | ⚠️ Redis unreachable at first, fixed (see Bug #2), then ✅ all healthy |
| 4 | `alembic upgrade head` | ✅ All migrations applied cleanly through `d99cb779fee9` (Phase 5 + nullable fix) |
| 5 | Backend `uvicorn` startup | ⚠️ Wrong module path + Swagger docs collision, fixed (see Bugs #3, #4) |
| 6 | Celery worker startup | ⚠️ Module import error + event loop errors, fixed (see Bugs #5, #6) |
| 7 | Frontend `npm run dev` (Vite) | ✅ Running on `localhost:5173` |
| 8–9 | Manual verification — Phase 1 (Core Platform) | ⚠️ Found and fixed Bug #7 (project delete). All other Phase 1 flows ✅ |

---

## 2. Bugs Found & Fixed

### Bug #1 — Frontend `npm install` failing (Replit package firewall)
**Symptom:**
```
npm error network request to http://package-firewall.replit.local/npm/...
npm error network getaddrinfo ENOTFOUND package-firewall.replit.local
```
**Root cause:** npm registry was pointed at a Replit-internal proxy (only reachable inside Replit's environment), left over from the project having been developed/pushed via Replit.

**Fix:**
```bash
npm config set registry https://registry.npmjs.org/
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```
**Result:** 170 packages installed, 0 vulnerabilities.

---

### Bug #2 — Redis unreachable from host (`localhost:6379` connection refused)
**Symptom:**
```
Cannot connect to redis://localhost:6379/1: Error 10061 ... target machine actively refused it
```
**Root cause:** `docker-compose.yml`'s `redis` service had no `ports:` mapping, so port 6379 was never exposed to the Windows host — only reachable from inside the Docker network.

**Fix:** Added port mapping to the `redis` service in `docker-compose.yml`:
```yaml
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
```
**Result:** `docker ps` confirmed `0.0.0.0:6379->6379/tcp`, container healthy.

*(Note: full Docker Compose build of `api`/`worker`/`frontend` services was skipped entirely for local dev — only `postgres`, `redis`, `minio` are run via Docker; backend/worker/frontend run natively via `uvicorn`, `celery`, `npm run dev`. The `frontend` Docker build also has a broken `pnpm --frozen-lockfile` step since the repo uses npm, not pnpm — not fixed, since it's unused in local dev workflow.)*

---

### Bug #3 — `uvicorn app.main:app` → `ModuleNotFoundError: No module named 'app'`
**Root cause:** Wrong module path assumed. Actual FastAPI entry point lives at `apps/api/main.py` (plural `apps`), not `app/main.py`.

**Fix:** Correct start command:
```bash
uvicorn apps.api.main:app --reload
```

---

### Bug #4 — Swagger docs showing "No operations defined in spec!"
**Symptom:** `/api/v1/docs` returned `200 OK` but with an empty OpenAPI spec — none of the real routes appeared.

**Root cause:** The outer `app = FastAPI(...)` explicitly declared its own `docs_url`, `redoc_url`, and `openapi_url` at `/api/v1/docs` etc. Separately, a **sub-app** `v1 = FastAPI(...)` — which actually had all routers (`health`, `auth`, `projects`, `characters`, etc.) — was mounted onto `app` at that same prefix via `app.mount(API_V1_PREFIX, v1)`. Because `app`'s own docs route was registered directly on `app`, it intercepted requests before Starlette could delegate to the mounted `v1` sub-app, so the browser only ever saw `app`'s own (empty) spec.

**Fix — `backend/apps/api/main.py`:**

Removed docs config from the outer `app`:
```python
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Generic AI Animation Studio Platform — Plugin-based, provider-agnostic",
    lifespan=lifespan,
)
```

Added it to the `v1` sub-app instead (defaults to `/docs`, which becomes `/api/v1/docs` once mounted):
```python
v1 = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Generic AI Animation Studio Platform — Plugin-based, provider-agnostic",
)
```
**Result:** `http://localhost:8000/api/v1/docs` now shows the full Swagger UI with all registered routes.

**Known non-blocking warning (not fixed, low priority):**
```
UserWarning: Duplicate Operation ID list_backgrounds_library_backgrounds_get for function list_backgrounds at .../library.py
UserWarning: Duplicate Operation ID list_props_library_props_get for function list_props at .../library.py
```
Two function names in `library.py` are reused across different registered routes, causing duplicate OpenAPI operation IDs. Server still runs fine; flagged for a future cleanup pass (Step 12).

---

### Bug #5 — Celery worker: `ModuleNotFoundError: No module named 'database'`
**Symptom:** Worker started and listed all tasks correctly, but a signal handler (`_init_worker_db`, triggered on `worker_process_init`) failed with a missing-module error even though `backend/database/` exists and imports fine via plain `python -c "import database"`.

**Root cause:** The standalone `celery` command-line entry point does not automatically add the current working directory to `sys.path`, unlike Python's `-c`/`-m` invocation. Since `backend/` (containing `database/`) wasn't on `sys.path`, the import failed only under the `celery` command specifically.

**Fix:** Run Celery as a Python module instead, which does add the CWD to `sys.path`:
```bash
python -m celery -A apps.worker.main.celery_app worker -l info -P solo
```
(`-P solo` is also required on Windows since Celery's default `prefork` pool relies on POSIX `fork()`, unavailable on Windows.)

**Result:** `worker_process_db_initialized` logged successfully, worker reached `ready.` state.

---

### Bug #6 — Celery worker: repeating `RuntimeError: Event loop is closed`
**Symptom:** Every time a new Celery task started (`discover_trends`, `research_refresh`, `score_opportunities`, `scheduler_tick`, etc.), the log showed:
```
Exception terminating connection <AdaptedConnection ...>
...
RuntimeError: Event loop is closed
```
Tasks still completed successfully afterward (`task_success`), but the error was firing consistently on every task boundary — a real underlying issue, not just noise, and a risk for connection-pool exhaustion under load.

**Root cause:**
- `database/connection.py` creates the SQLAlchemy async engine **once** as a module-level singleton via `init_db()`, called from the `worker_process_init` signal at worker startup. Its internal `asyncpg` connection pool becomes bound to whichever asyncio event loop exists at that moment.
- Every task wrapper (in `research_tasks.py`, `knowledge_tasks.py`, `intelligence_tasks.py`, `workflow_tasks.py`, `dead_letter.py`) called a locally duplicated `_run_async()` helper that ultimately called `asyncio.run(coro)` — which creates a **brand new** event loop per task and **closes it** when the task finishes.
- On the next task, a new loop is created, but the engine's pool still holds connections tied to the previous (now-closed) loop. When the pool tried to clean those up, `RuntimeError: Event loop is closed` was raised.

**Fix:** Created one shared helper module maintaining a **single persistent event loop per worker process**, reused across all tasks instead of creating/closing a new loop every time. Safe under Celery's `-P solo` pool (single process/thread).

**New file — `backend/apps/worker/async_utils.py`:**
```python
from __future__ import annotations

import asyncio
from typing import Any, Coroutine

_worker_loop: asyncio.AbstractEventLoop | None = None


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
    return _worker_loop


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine on this worker process's single persistent event loop."""
    loop = _get_worker_loop()
    return loop.run_until_complete(coro)
```

**Applied to all 5 task modules** — removed each file's local duplicated `_run_async` (or inline `asyncio.run(...)` calls) and replaced with:
```python
from apps.worker.async_utils import run_async as _run_async
```
Files updated:
- `backend/apps/worker/tasks/research_tasks.py`
- `backend/apps/worker/tasks/knowledge_tasks.py`
- `backend/apps/worker/tasks/intelligence_tasks.py`
- `backend/apps/worker/tasks/workflow_tasks.py`
- `backend/apps/worker/tasks/dead_letter.py` (two call sites: `dead_letter_task`'s `_store()` and `list_failed_tasks`'s `_fetch()`)

**Result:** Confirmed by re-running scheduler-triggered tasks — `RuntimeError: Event loop is closed` no longer appears in worker logs.

**Note:** `apps/worker/dispatcher.py` (a separate, API-side synchronous-fallback dispatcher used only when Celery/Redis is unreachable) still has its own local `_run_sync()` with the same `asyncio.run()` pattern. It was **not** touched, since it is not executed inside the actual Celery worker process and wasn't implicated in the observed errors — flagged here for awareness if the same symptom ever appears on the API side.

---

### Bug #7 — Deleting a Project with linked Characters → `500 Internal Server Error`
**Symptom:**
```
sqlalchemy.exc.IntegrityError: ... NotNullViolationError: null value in column "project_id" 
of relation "characters" violates not-null constraint
[SQL: UPDATE characters SET project_id=$1::UUID ... ]
```
Deleting a project with no linked characters worked (`204 No Content`), but deleting a project that had at least one character attached failed.

**Root cause:** In `database/models/project.py`, the `characters` and `stories` relationships had no `cascade`/`passive_deletes` configuration. SQLAlchemy's ORM-level default behavior when deleting a parent is to **detach** children by setting their foreign key to `NULL` in Python before issuing the delete — it does not automatically use the database's own `ON DELETE CASCADE`. Since `characters.project_id` (and `stories.project_id`) are `NOT NULL` columns at the DB level (with `ondelete="CASCADE"` already correctly set on the FK itself), the ORM's `SET project_id = NULL` attempt violated the not-null constraint before the database's cascade rule ever got a chance to run.

**Fix — `backend/database/models/project.py`:** Added `passive_deletes=True` to both relationships, which tells SQLAlchemy to let the database's own `ON DELETE CASCADE` handle child rows directly, instead of trying to manage them in Python first.

```python
stories: Mapped[list["Story"]] = relationship(
    "Story", back_populates="project", lazy="select", passive_deletes=True
)
characters: Mapped[list["Character"]] = relationship(
    "Character", back_populates="project", lazy="select", passive_deletes=True
)
```

**Result:** Re-tested — create project → add character → delete project → `204 No Content`. Confirmed working.

---

## 3. Testing Completed (Phase 1 — Core Platform)

| Test | Result | Notes |
|---|---|---|
| Register | ✅ 200/201 | Duplicate registration correctly returns `409 Conflict` |
| Login | ✅ 200 | Returns auth token, `GET /auth/me` confirms session |
| Dashboard load | ✅ 200 | `/projects`, `/plugins`, `/rs/dashboard`, `/rs/history`, `/rs/scheduler/status` all responding |
| Create Project | ✅ 201 Created | |
| View Project detail | ✅ 200 | Including nested `/stories` fetch |
| Delete Project (no children) | ✅ 204 No Content | |
| Delete Project (with linked Character) | ❌ → ✅ | Failed with 500 (Bug #7), fixed, retested, now 204 |

**Phase 1 status: ✅ Fully verified**

---

## 4. Additional Endpoints Observed Working (Phase 5 — Research & Trend Intelligence, ahead of formal test pass)

The following were exercised incidentally while triggering the scheduler for Celery testing, and all returned `200 OK` / `202 Accepted`:
- `POST /rs/scheduler/trigger` → `202 Accepted`
- `GET /rs/scheduler/status`
- `GET /rs/dashboard`
- `GET /rs/history` (with `run_type` filters: `trend_discovery`, `research_refresh`, `opportunity_report`, `manual`)
- `GET /rs/analytics`
- `GET /rs/jobs` (with `status` filters: `pending`, `running`, `completed`, `failed`)
- `GET /rs/topics`, `GET /rs/queue`, `GET /rs/opportunities`, `GET /rs/trends`
- `GET /asset-manager/character_template`, `GET /asset-manager/stats`
- `GET /library/props`, `/library/props/categories`, `/library/backgrounds`, `/library/backgrounds/categories`, `/library/character-templates`

Celery task types confirmed executing successfully end-to-end (mock providers):
- `research.discover_trends` — 20 trends discovered, 6 clusters created
- `research.research_refresh` — 5 topics researched, 25 facts verified
- `research.score_opportunities` — 5 opportunities scored/queued
- `research.scheduler_tick` — full pipeline (trends → research → opportunities) in ~1–2s

These are not yet part of a formal Phase 5 manual test pass but indicate the pipeline is functioning correctly post-fix.

---

## 5. Outstanding / Deferred Items (for future bug-fixing pass, Step 12)

1. **Duplicate OpenAPI operation IDs** in `apps/api/routers/library.py` (`list_backgrounds`, `list_props`) — cosmetic Swagger warning, non-blocking.
2. **`apps/worker/dispatcher.py`** still uses the old per-call `asyncio.run()` pattern in its synchronous-fallback path (`_run_sync`). Not yet implicated in any observed bug, but inconsistent with the fix applied to the 5 task modules — worth aligning for consistency for future events.
3. **Frontend Docker build** (`infrastructure/docker/frontend.Dockerfile`) fails on `pnpm install --frozen-lockfile` since the repo actually uses npm (no `pnpm-lock.yaml` present). Not fixed — irrelevant to local dev workflow (frontend runs natively via `npm run dev`), but will block a full `docker compose up -d` (all services) or a production-style build until addressed.

---

## 6. Next Steps

Continue the verification plan from **Step 9, Phase 2 (Character Studio)**:
- Character Studio load
- Character CRUD (create/edit/delete)
- Character image upload/generation
- Character editing

Then proceed sequentially through Phases 3–6 per the original test plan, applying the same fix → retest → commit cycle for any further issues found.




# Backend Tests are passing Total 243 

243 tests are passed on backend 