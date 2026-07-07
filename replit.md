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
- `backend/apps/api/routers/knowledge.py` — Phase 4 `/kn` router (collections, documents, search, jobs, memory, stats)
- `backend/services/knowledge/` — Knowledge engine: chunking, embedding, retrieval, RAG context builder
- `backend/database/models/knowledge.py` — KnowledgeCollection/Document/Chunk/EmbeddingJob/RetrievalHistory/KnowledgeMemory/KnowledgeVersion models
- `frontend/src/pages/knowledge/` — Knowledge Intelligence UI (dashboard, collections, collection detail, memory, embedding jobs)
- `frontend/src/api/knowledge.ts` — API client for `/kn` endpoints

## Required Environment Variables

See `.env.example` for all variables. Key ones:
- `DATABASE_URL` — PostgreSQL connection string (asyncpg driver)
- `SECRET_KEY` — JWT signing key (min 64 chars)
- `REDIS_URL` — Redis for Celery broker/backend
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` — Object storage
- `SI_AI_PROVIDER` — Story Intelligence LLM provider: `mock` (default, deterministic, no external dependency) or `ollama` (real generation, requires a reachable Ollama server). Any unrecognized value falls back to `mock` with a warning log. Dev/test environment has this set to `mock`.
- `KN_EMBEDDING_PROVIDER` — Knowledge embedding provider: `mock` (default, hash-based deterministic) or `ollama` (requires Ollama server with an embedding model). Falls back to `mock` on any error.
- `KN_VECTOR_STORE` — Vector store backend: `memory` (default, pure-Python cosine similarity, no external dependency) or `chromadb` (requires ChromaDB). Falls back to `memory` on any error.
- `KN_CHUNK_SIZE_TOKENS` — Chunk size for document splitting (default: 512)
- `KN_CHUNK_OVERLAP_TOKENS` — Overlap between chunks (default: 50)
- `KN_DEFAULT_TOP_K` — Default number of retrieval results (default: 5)

## Architecture decisions

- Clean architecture: models → repositories → services → routers (no cross-layer skips)
- Plugin system: content type plugins register character archetypes, voice profiles, workflows
- Provider registry: LLM/Image/TTS/STT/Renderer are swappable at startup via `AGENTS_*` env vars
- Asset versioning: `AssetVersion` table snapshots any asset type by `(asset_type, asset_id)`
- Soft delete: all library assets use `is_deleted` flag; hard delete not exposed via API
- RAG integration: Knowledge collections attach to Story Intelligence generation via `knowledge_collection_id`; retrieval failures always fall back gracefully (empty context, generation continues)
- Dispatcher mode: with Redis available Celery is used (mode=`async`/`celery`); without Redis the `TaskDispatcher` falls back to sync inline execution (mode=`sync`). Tests must accept both modes.

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

## Implemented Features (Phase 4 — RAG & Knowledge Intelligence Engine)

- **Knowledge Collections**: project/world-scoped document stores; full CRUD with pagination
- **Document ingestion pipeline**: text input or file upload → parse → chunk (with overlap) → embed → index
- **Provider-agnostic embeddings**: `MockEmbeddingProvider` (hash-based, zero deps) or `OllamaEmbeddingProvider`; swapped via `KN_EMBEDDING_PROVIDER`
- **Vector search**: `InMemoryVectorStore` (pure-Python cosine similarity, zero deps) or `ChromaDBVectorStore`; swapped via `KN_VECTOR_STORE`
- **Semantic search**: `POST /kn/collections/{id}/search` — top-k retrieval with score threshold
- **RAG context**: `knowledge_collection_id` on generation endpoints prepends relevant chunks to LLM prompts; graceful fallback on any retrieval error
- **Knowledge memory**: structured facts/rules/lore scoped to project or world
- **Embedding job queue**: Celery tasks for async document processing with retry queue
- **Frontend**: Knowledge dashboard, Collections list, Collection detail (docs + search), Knowledge memory, Embedding jobs — all under `/projects/:projectId/knowledge/...`
- **84 tests** covering CRUD, pipeline, RAG, auth — all passing with mock providers (zero external dependencies)
- Alembic migration `9c163cebabb8` adds 7 `kn_*` tables

## Gotchas

- `DATABASE_URL` must use `postgresql+asyncpg://` driver prefix — the config validator normalizes it automatically
- asyncpg does not support `sslmode` query param — the config validator strips it
- `email-validator` package is required separately for Pydantic v2 `EmailStr`
- MinIO `ensure_bucket` runs at startup; MinIO service must be reachable or startup will fail
- The `CORS_ORIGINS` setting must include the Replit dev proxy domain in production
- The `/api/v1` router lives on a separate mounted `FastAPI` sub-app (`v1 = FastAPI(...)`, then `app.mount(...)`) — exception handlers registered only on the outer `app` do NOT apply to sub-app routes; they must also be registered on `v1` directly, or `AppError`/`NotFoundError` etc. surface as raw 500s instead of mapped status codes
- Story generation endpoints (`/si/.../ideas/generate`, `/si/projects/{id}/generate`, `/si/seasons/{id}/generate-episode`) use whichever provider `SI_AI_PROVIDER` selects. With `SI_AI_PROVIDER=mock` (the dev/test default) they work fully offline with deterministic output; with `SI_AI_PROVIDER=ollama` they require a reachable Ollama server and will fail without one — that failure mode is expected only when `ollama` is explicitly selected
- `MockLLMProvider._route()` keyword-matches prompts to pick a response template — when adding a new prompt/template pair, always check existing prompts for substring collisions (e.g. an unrelated prompt containing "story idea" or "dialogue" as an embedded label) and order checks from most-specific phrase to least-specific
- Knowledge `/kn/jobs/retry-queue` route MUST be declared before `/kn/jobs/{job_id}` in the router — FastAPI will otherwise match the literal string `retry-queue` as a UUID parameter and return 422
- Dispatch mode (`sync` vs `async`/`celery`) depends on Redis availability at runtime — tests that assert a specific mode must accept both via `in ("sync", "async", "celery")`

## User preferences
