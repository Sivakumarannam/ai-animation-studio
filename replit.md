# AI Animation Studio

A plugin-based, provider-agnostic AI animation studio platform. Generates complete animated videos from story prompts using interchangeable AI providers and a content plugin system.

## Run & Operate

- **Backend API**: `cd backend && PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload` (port 8000)
- **Frontend**: `cd frontend && PORT=5173 npm run dev` (port 5173, proxies /api → 8000)
- Both start automatically via the `Backend API` and `Frontend` workflows

## Stack

- **Backend**: Python 3.12, FastAPI, Celery + Redis, SQLAlchemy (asyncpg), Alembic, PostgreSQL
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS 3, TanStack Query, Zustand, Wouter
- **Storage**: MinIO (object storage for assets), PostgreSQL (relational data)
- **AI Providers**: Ollama (LLM), ComfyUI (image), Piper TTS (voice), Whisper (STT), FFmpeg (render)

## Where things live

- `backend/apps/api/` — FastAPI application, routers, config, dependencies
- `backend/database/models/` — SQLAlchemy models (asset.py, animation.py, character.py, etc.)
- `backend/repositories/` — Data access layer
- `backend/services/` — Business logic (library_service.py, animation_service.py)
- `backend/packages/schemas/` — Pydantic request/response schemas
- `backend/alembic/` — Database migrations
- `backend/plugins/` — Content type plugins (e.g. `telugu_family_comedy`)
- `frontend/src/pages/studio/AssetManagerPage.tsx` — Main Asset Manager UI
- `frontend/src/api/library.ts` — Unified API client for all asset operations
- `backend/apps/api/routers/story_intelligence.py` — Phase 3 `/si` router (worlds, seasons, episodes, scenes, ideas, memory, jobs, stats)
- `backend/services/intelligence/` — Story Intelligence business logic + orchestrator
- `backend/database/models/intelligence.py` — World/Season/Episode/StoryScene/StoryIdea/StoryMemory/GenerationJob models
- `frontend/src/pages/intelligence/` — Story Intelligence UI (dashboard, worlds, world/season/episode detail, ideas, retry queue)
- `frontend/src/api/storyIntelligence.ts` — API client for `/si` endpoints

## Required Environment Variables

See `.env.example` for all variables. Key ones:
- `DATABASE_URL` — PostgreSQL connection string (asyncpg driver)
- `SECRET_KEY` — JWT signing key (min 64 chars)
- `REDIS_URL` — Redis for Celery broker/backend
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` — Object storage
- `SI_AI_PROVIDER` — Story Intelligence LLM provider: `mock` (default, deterministic, no external dependency) or `ollama` (real generation, requires a reachable Ollama server). Any unrecognized value falls back to `mock` with a warning log. Dev/test environment has this set to `mock`.

## Architecture decisions

- Clean architecture: models → repositories → services → routers (no cross-layer skips)
- Plugin system: content type plugins register character archetypes, voice profiles, workflows
- Provider registry: LLM/Image/TTS/STT/Renderer are swappable at startup via `AGENTS_*` env vars
- Asset versioning: `AssetVersion` table snapshots any asset type by `(asset_type, asset_id)`
- Soft delete: all library assets use `is_deleted` flag; hard delete not exposed via API

## Implemented Features (Phase 1)

- Asset Manager with 7 library tabs: Characters, Backgrounds, Props, Animations, Audio, Music, Sound Effects
- Drag-and-drop file upload to MinIO
- Soft delete + restore (single and bulk)
- Bulk category/tag updates
- Version history with snapshot + restore
- Paginated search with category/tag/deleted filters
- Stats dashboard board

## Implemented Features (Phase 3 — Story Intelligence)

- Worlds → Seasons → Episodes → Scenes hierarchy with full CRUD
- Story idea generation (LLM-backed) plus manual idea creation, status workflow, and deletion
- World-scoped story memory (facts/rules/lore) with type filtering
- Episode evaluation + version history (snapshot/restore) via the shared `AssetVersion`-style versioning table
- Generation job queue with Celery dispatch + synchronous fallback (`TaskDispatcher`), job logs, and a retry queue
- Story Intelligence dashboard with per-project stats (worlds/seasons/episodes/scenes/ideas/memories, job counts, avg story score)
- Frontend: dashboard, Worlds list, World/Season/Episode detail pages, Story Ideas board, Retry Queue — all under `/projects/:projectId/intelligence/...`

## Gotchas

- `DATABASE_URL` must use `postgresql+asyncpg://` driver prefix — the config validator normalizes it automatically
- asyncpg does not support `sslmode` query param — the config validator strips it
- `email-validator` package is required separately for Pydantic v2 `EmailStr`
- MinIO `ensure_bucket` runs at startup; MinIO service must be reachable or startup will fail
- The `CORS_ORIGINS` setting must include the Replit dev proxy domain in production
- The `/api/v1` router lives on a separate mounted `FastAPI` sub-app (`v1 = FastAPI(...)`, then `app.mount(...)`) — exception handlers registered only on the outer `app` do NOT apply to sub-app routes; they must also be registered on `v1` directly, or `AppError`/`NotFoundError` etc. surface as raw 500s instead of mapped status codes
- Story generation endpoints (`/si/.../ideas/generate`, `/si/projects/{id}/generate`, `/si/seasons/{id}/generate-episode`) use whichever provider `SI_AI_PROVIDER` selects. With `SI_AI_PROVIDER=mock` (the dev/test default) they work fully offline with deterministic output; with `SI_AI_PROVIDER=ollama` they require a reachable Ollama server and will fail without one — that failure mode is expected only when `ollama` is explicitly selected
- `MockLLMProvider._route()` keyword-matches prompts to pick a response template — when adding a new prompt/template pair, always check existing prompts for substring collisions (e.g. an unrelated prompt containing "story idea" or "dialogue" as an embedded label) and order checks from most-specific phrase to least-specific

## User preferences
