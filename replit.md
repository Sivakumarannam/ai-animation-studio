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

## Required Environment Variables

See `.env.example` for all variables. Key ones:
- `DATABASE_URL` — PostgreSQL connection string (asyncpg driver)
- `SECRET_KEY` — JWT signing key (min 64 chars)
- `REDIS_URL` — Redis for Celery broker/backend
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` — Object storage

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

## Gotchas

- `DATABASE_URL` must use `postgresql+asyncpg://` driver prefix — the config validator normalizes it automatically
- asyncpg does not support `sslmode` query param — the config validator strips it
- `email-validator` package is required separately for Pydantic v2 `EmailStr`
- MinIO `ensure_bucket` runs at startup; MinIO service must be reachable or startup will fail
- The `CORS_ORIGINS` setting must include the Replit dev proxy domain in production

## User preferences
