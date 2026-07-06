# Test Report — AI Animation Studio
**Date:** 2026-07-06 (Phase 3 addendum; original audit 2026-07-04)  
**Scope:** Phase 1 (Asset Management) + Phase 2 (Character Studio) + Phase 3 (Story Intelligence)  
**Auditor:** Production-Readiness Audit

---

## Summary

| Metric | Result |
|--------|--------|
| Automated test cases | **142** |
| Tests passing | **142 / 142 (100%)** |
| API endpoints swept (live server) | **50** |
| API endpoints passing | **49 / 50 (98%)** |
| Bugs fixed during audit | **12** (10 Phase 1/2 + 2 Phase 3) |
| Frontend production build | **✅ Passing** (`tsc -b && vite build`) |

---

## Automated Test Suite

Tests live in `backend/tests/` and run against the **live API server** (`http://localhost:8000`).  
Execution: `cd backend && PYTHONPATH=. python -m pytest tests/ -v`

### Test Files

| File | Class | Tests | Description |
|------|-------|-------|-------------|
| `test_auth.py` | `TestRegister` | 4 | Register: success, duplicate email → 409, invalid email, missing fields |
| `test_auth.py` | `TestLogin` | 3 | Login: success, wrong password → 401, unknown user → 401 |
| `test_auth.py` | `TestMe` | 3 | Me: authenticated, unauthenticated, invalid token |
| `test_auth.py` | `TestRefresh` | 2 | Token refresh: success, invalid token |
| `test_projects.py` | `TestProjects` | 9 | Project CRUD, auth guard, 404 |
| `test_projects.py` | `TestStories` | 5 | Story CRUD, paginated list |
| `test_projects.py` | `TestScenes` | 4 | Scene CRUD (with required `scene_number`) |
| `test_projects.py` | `TestCharacters` | 5 | Character CRUD |
| `test_library.py` | `TestExpressions` | 7 | Expressions: list, seed, CRUD, idempotent seed |
| `test_library.py` | `TestPoses` | 4 | Poses: seed, CRUD |
| `test_library.py` | `TestBackgrounds` | 6 | Backgrounds: list, seed, CRUD, categories |
| `test_library.py` | `TestProps` | 4 | Props: seed, CRUD, categories |
| `test_asset_manager.py` | `TestAssetManagerStats` | 1 | Stats endpoint: all 6 asset types |
| `test_asset_manager.py` | `TestAssetManagerSearch` | 4 | GET + POST search, query filter, show_deleted |
| `test_asset_manager.py` | `TestAssetManagerSeed` | 2 | Seed all types, idempotency |
| `test_asset_manager.py` | `TestAssetManagerCRUD` | 7 | List, create (all 6 types), get, update, soft-delete, restore, deleted-not-in-list |
| `test_asset_manager.py` | `TestAssetManagerBulk` | 3 | Bulk delete, restore, update |
| `test_asset_manager.py` | `TestAssetManagerVersions` | 2 | Create version snapshot, restore version |
| `test_asset_manager.py` | `TestCharacterTemplateAssetManager` | 1 | List character templates through asset manager |
| `test_projects.py` | `TestCrossUserAuthorization` | 5 | User A cannot read/mutate/delete User B's projects or stories |
| `test_story_intelligence.py` | `TestWorlds` | 7 | World CRUD, auth guard, 404 |
| `test_story_intelligence.py` | `TestSeasons` | 5 | Season CRUD |
| `test_story_intelligence.py` | `TestEpisodes` | 7 | Episode CRUD, evaluation-none, versions-empty |
| `test_story_intelligence.py` | `TestStoryScenes` | 4 | Scene CRUD under episode |
| `test_story_intelligence.py` | `TestStoryIdeas` | 4 | Manual idea create/list/update-status/delete |
| `test_story_intelligence.py` | `TestStoryMemory` | 2 | Store + list memory, filter by type |
| `test_story_intelligence.py` | `TestGenerationJobs` | 2 | Job list empty, job not found |
| `test_story_intelligence.py` | `TestStats` | 2 | Stats shape, auth guard |
| `test_story_intelligence_llm.py` | `TestIdeaGeneration` | 5 | LLM-backed idea generation: with/without world context, count respected, persisted, auth |
| `test_story_intelligence_llm.py` | `TestEpisodeEvaluation` | 5 | Evaluate episode, score update, version history, not-found, get-evaluation |
| `test_story_intelligence_llm.py` | `TestGenerateEpisodeDispatch` | 4 | Single-episode generation dispatch shape, sync-fallback result, real episode+scenes created, job record |
| `test_story_intelligence_llm.py` | `TestFullPipelineDispatch` | 6 | Full pipeline: without world, with existing world, builds world when missing, persists memory, stats reflect generation, auth guard |
| `test_story_intelligence_llm.py` | `TestDispatcherFallbackBehavior` | 2 | Dispatcher never returns async mode without a broker; result always present on sync completion |
| `test_story_intelligence_llm.py` | `TestJobLogsAndRetryIntegration` | 4 | Job logs shape, jobs listed after generation, filter by status/type |
| `test_story_intelligence_llm.py` | `TestWorkflowIntegrationEndToEnd` | 2 | Manual hierarchy → AI evaluation → memory; idea generation feeds manual season creation |

### Final Run Output

```
142 passed in 108.14s (0:01:48)
```

All tests green. Full suite (`backend/tests/`) run against the live server with `SI_AI_PROVIDER=mock` — no external LLM dependency required.

---

## Live API Endpoint Sweep

The sweep used `httpx.AsyncClient` against the running server with correct payloads.

### Auth (`/api/v1/auth`)

| Method | Endpoint | Status | Result |
|--------|----------|--------|--------|
| POST | `/auth/register` | 201 | ✓ |
| POST | `/auth/login` | 200 | ✓ |
| POST | `/auth/refresh` | 200 | ✓ |
| GET | `/auth/me` | 200 | ✓ |

### Projects

| Method | Endpoint | Status | Result |
|--------|----------|--------|--------|
| POST | `/projects` | 201 | ✓ |
| GET | `/projects/{id}` | 200 | ✓ |
| PATCH | `/projects/{id}` | 200 | ✓ |
| POST | `/projects/{id}/stories` | 201 | ✓ |
| GET | `/stories/{id}` | 200 | ✓ |
| PATCH | `/stories/{id}` | 200 | ✓ |
| POST | `/stories/{id}/scenes` | **422** | ✗ — `scene_number` required, not documented |
| GET | `/scenes/{id}` | 200 | ✓ |
| PATCH | `/scenes/{id}` | 200 | ✓ |
| GET | `/scenes/{id}/composition` | 200 | ✓ |
| POST | `/projects/{id}/characters` | 201 | ✓ |
| GET | `/characters/{id}` | 200 | ✓ |
| PATCH | `/characters/{id}` | 200 | ✓ |
| DELETE | `/characters/{id}` | 204 | ✓ |

### Library — Character Templates

| Method | Endpoint | Status | Result |
|--------|----------|--------|--------|
| POST | `/library/character-templates` | 201 | ✓ (requires `slug`) |
| GET | `/library/character-templates/{id}` | 200 | ✓ |
| PATCH | `/library/character-templates/{id}` | 200 | ✓ |
| DELETE | `/library/character-templates/{id}` | 204 | ✓ |

### Asset Manager — All 6 Types

Types: `background`, `prop`, `animation_preset`, `audio`, `music`, `sound_effect`

| Method | Endpoint | Status | Result |
|--------|----------|--------|--------|
| POST | `/asset-manager/{type}` | 200 | ✓ all 6 |
| GET | `/asset-manager/{type}/{id}` | 200 | ✓ all 6 |
| PATCH | `/asset-manager/{type}/{id}` | 200 | ✓ all 6 |
| DELETE | `/asset-manager/{type}/{id}` | 204 | ✓ all 6 |
| POST | `/asset-manager/{type}/{id}/restore` | 200 | ✓ all 6 |
| POST | `/asset-manager/{type}/bulk-delete` | 200 | ✓ |
| POST | `/asset-manager/{type}/bulk-restore` | 200 | ✓ |
| POST | `/asset-manager/{type}/bulk-update` | 200 | ✓ |
| POST | `/asset-manager/versions/{type}/{id}` | 201 | ✓ |
| GET | `/asset-manager/versions/{type}/{id}` | 200 | ✓ |
| GET | `/asset-manager/stats` | 200 | ✓ |
| GET | `/asset-manager/search` | 200 | ✓ |
| POST | `/asset-manager/search` | 200 | ✓ |

### Known Untested Endpoints (require Redis/Celery/MinIO)

- `POST /api/v1/generation/story` — Celery task dispatch (Redis not available)
- `GET /api/v1/generation/status/{task_id}` — Celery result backend
- `WebSocket /ws/{project_id}` — WebSocket server (needs Redis pubsub)
- `POST /api/v1/assets/upload` — MinIO file upload

---

## Test Infrastructure Notes

- Tests are **integration tests** against the live running server (not ASGI in-process)
- Each test creates a unique user via `auth_headers` fixture (unique UUID email prefix) to avoid cross-test pollution
- All slugs and names in library tests use `uuid4().hex[:8]` suffix to avoid unique-constraint conflicts on the real DB
- Tests do **not** roll back — test data accumulates in the development database
- The `conftest.py` fixtures are designed to be idempotent (duplicate seed calls return 0)

---

## Phase 3 — Story Intelligence (LLM-Backed Endpoints)

`SI_AI_PROVIDER=mock` is set for the dev/test environment, so all LLM-backed Story Intelligence endpoints are fully covered by deterministic tests with **no dependency on a running Ollama server**. `SI_AI_PROVIDER=ollama` remains available for real generation when an Ollama server is reachable.

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| `/si/projects/{id}/ideas/generate` | POST | 201 | ✓ mock-backed idea generation, with/without world context |
| `/si/episodes/{id}/evaluate` | POST | 200 | ✓ scores computed, episode score updated, version snapshot created |
| `/si/episodes/{id}/evaluation` | GET | 200 | ✓ |
| `/si/seasons/{id}/generate-episode` | POST | 200 | ✓ dispatcher sync-fallback, real episode + scenes (with dialogue + narration) persisted |
| `/si/projects/{id}/generate` (full pipeline) | POST | 200 | ✓ world → idea → season → episodes → scenes → evaluation → memory, sync-fallback dispatch |
| `/si/projects/{id}/jobs` | GET | 200 | ✓ job records created, filterable by status/type |
| `/si/projects/{id}/jobs/retry-queue` and job logs | GET | 200 | ✓ |
| `/si/projects/{id}/stats` | GET | 200 | ✓ reflects worlds/seasons/episodes/scenes/jobs after generation |

**Bugs found and fixed while writing this coverage:** see `BUG-015` and `BUG-016` in `BUG_REPORT.md`.
