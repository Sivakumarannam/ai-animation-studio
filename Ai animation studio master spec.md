# AI Animation Studio — Master Vision & Phase-Wise Execution Spec

**Repo:** `ai-animation-studio`
**Type:** Autonomous, revenue-generating YouTube animation business — not a portfolio project.
**Owner role at maturity:** strategic supervisor only (niche, characters, language, monetization). Everything else is automated.

---

## 0. North Star

Build a self-operating AI production company that discovers profitable niches, writes and remembers ongoing episodic stories, generates every asset (image, voice, music, animation), assembles and publishes videos to YouTube on a schedule, reads its own analytics, and rewrites its own prompts/strategy to improve — for multiple channels, indefinitely, on free/self-hosted infra wherever practical.

**Not the goal:** a single-shot image/script generator, a demo, a resume piece.
**The goal:** recurring AdSense + affiliate + sponsorship + membership revenue, with the software as the unpaid employee.

---

## 1. Content & Business Model (context every phase must respect)

| Dimension | Spec |
|---|---|
| Niche | 3D-style family cartoon (Cocomelon / Little Angel reference) |
| World hierarchy | Village → Family → Characters → Seasons → Episodes → Scenes → Animations → Videos |
| Episode length | 45–60 sec, ~12–18 scenes |
| Season size | 30 episodes |
| Long video | 8–12 min, built from a sequence of episodes in order (no skipping) |
| Shorts | 20–28 sec, 1/day forever, starting Day 1 |
| Long-form cadence | Every 2 days after Day 15, weighted to Sat/Sun |
| Timezone | Asia/Kolkata |
| Publishing | Fixed schedule → adaptive (AI-learned optimal time) once analytics exist |
| Monetization | AdSense, affiliate, sponsorship, membership, digital products |
| Multi-channel | Each channel = own niche, branding, characters, schedule, analytics, knowledge base |

---

## 2. Technology Stack (fixed reference — don't relitigate per phase)

- **Backend:** Python, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, Celery, Redis
- **Architecture pattern:** Repository pattern + Service layer + Provider factory + Dependency Injection
- **Frontend:** React, TypeScript, Tailwind CSS
- **AI:** Gemini (free tier), Ollama, Hugging Face, ChromaDB (vector store), LangGraph (agent orchestration)
- **Storage:** MinIO (S3-compatible), local filesystem fallback
- **Deployment:** Docker, Docker Compose
- **Principle:** free or self-hosted wherever practical; paid APIs only where there is no viable free alternative and revenue justifies it.

---

## 3. Phase Roadmap (build order)

```
Phase 1  → Foundation: Auth, Projects, Dashboard
Phase 2  → Character Studio
Phase 3  → Story Intelligence (worlds, memory, episodes)
Phase 4  → Knowledge Intelligence (RAG)
Phase 5  → Research Intelligence (trends, topics, scoring)
Phase 6  → AI Asset Generation (images)
Phase 7  → Animation Engine
Phase 8  → Voice Engine
Phase 9  → Music & Sound Engine
Phase 10 → Video Assembly Engine
Phase 11 → Thumbnail Engine
Phase 12 → SEO Engine
Phase 13 → Publishing Engine (YouTube upload)
Phase 14 → Analytics Engine
Phase 15 → Learning / Optimization Engine
Phase 16 → Self-Healing Engine (cross-cutting — start scaffolding in Phase 1, harden continuously)
Phase 17 → Multi-Channel Scaling
Phase 18 → Monetization Layer
```

Self-Healing is **not phase-16-only** — every phase from Phase 1 onward must emit structured errors into the recovery system defined in §16. Treat §16 as a contract every other phase implements against.

---

## Phase 1 — Foundation: Auth, Projects, Dashboard

**Goal:** a working skeleton every later phase plugs into.

**Scope**
- User authentication (JWT/OAuth), roles (owner/operator)
- Project entity = one YouTube channel's workspace (supports Phase 17 multi-channel from day one — don't hardcode single-channel assumptions)
- Dashboard shell: project switcher, empty-state widgets for pipeline stage, jobs, analytics (populated in later phases)
- Core DB schema: `users`, `projects`, `channels`, `settings`
- Celery + Redis wired up with a health-check task
- Docker Compose brings up: api, worker, postgres, redis, minio, frontend

**Acceptance criteria**
- Can register/login, create a project, see an empty dashboard, and see a Celery worker heartbeat in logs.
- `docker compose up` is a one-command dev environment.

---

## Phase 2 — Character Studio

**Goal:** characters exist as structured, persistent, versioned entities — never re-invented per episode.

**Data model per character**
Name, age, personality traits, appearance description, voice profile ref, emotion set, expression set, clothing/outfits, relationships (graph to other characters), memory log ref, catch phrases, growth/arc notes.

**Scope**
- CRUD UI + API for characters
- Character reference image slots (uploaded or generated in Phase 6, versioned)
- Relationship graph (character ↔ character, typed: family/friend/rival/etc.)
- Consistency rule engine: personality/appearance fields are immutable without an explicit "growth event" — prevents silent drift
- Template library (starter character archetypes for the target niche)

**Acceptance criteria**
- Can create a full cast for a world and each character has a stable ID reused by every later phase (assets, dialogue, voice).

---

## Phase 3 — Story Intelligence

**Goal:** the AI plans and remembers stories at every level of the hierarchy, with zero continuity errors.

**Scope**
- World builder: village/family setting, lore, rules
- Season planner: generates a 30-episode arc outline
- Episode planner: 45–60s beat sheet per episode, tied to season arc
- Scene breakdown: 12–18 scenes per episode with camera shots, dialogue, emotional pacing, hooks/cliffhangers
- **Story memory store**: previous episodes, running jokes, promises made, unresolved threads, object/location state — queried before generating anything new (this is the RAG consumer, built on top of Phase 4)
- Continuity validator: flags contradictions against memory before an episode is marked "ready for production"
- Retry queue: failed generation steps requeue instead of silently dropping

**Acceptance criteria**
- Given a world + cast, system produces a full season outline, then a fully scripted episode 1 that references established lore correctly.

---

## Phase 4 — Knowledge Intelligence (RAG)

**Goal:** nothing gets generated from ungrounded model memory — everything is retrieved first.

**Scope**
- ChromaDB vector store; embeddings pipeline for: uploaded docs, story lore, character history, world rules, prior episodes, brand/style guides, research notes
- Ingestion pipeline: chunk → embed → tag → store, with source metadata
- Retrieval API: semantic search + filtered search (by world/character/type)
- Standard flow baked into every generation call: **Retrieve → Build Context → Generate**
- Collections per project (isolate one channel's knowledge from another's — required for Phase 17)

**Acceptance criteria**
- Any generation call in Phases 3, 6–12 can be traced to the retrieved context it used; hallucinated facts are the exception, not the norm.

---

## Phase 5 — Research Intelligence

**Goal:** the system finds what to make, without manual research.

**Scope**
- Trend discovery job (YouTube trends, general web/topic trend sources)
- Topic research: expand a trend into a content angle
- Fact verification pass before anything enters the knowledge base
- Opportunity scoring model: competition, search volume proxy, format fit, monetization potential
- Auto-injection of verified research into Phase 4's knowledge base
- Scheduler: daily research run as a background job

**Acceptance criteria**
- A daily job produces a ranked list of content opportunities with scores and verified supporting facts, stored and queryable.

---

## Phase 6 — AI Asset Generation (Images)

**Goal:** every visual element a story needs exists as a generated, versioned, reusable asset.

**Scope**
- Prompt engineering layer (character + style + scene context → provider-ready prompt), built on Phase 4 context
- Generators: characters, backgrounds, props, poses, expressions, camera angles, lighting variants, objects
- Job queue (Celery) with provider abstraction (swap providers on failure — first real Self-Healing integration point)
- Asset storage in MinIO with metadata: version, tags, category, source prompt, linked character/world IDs
- Asset search/reuse UI (don't regenerate what already exists)

**Acceptance criteria**
- Given an episode's scene list, system generates a consistent asset set (same character looks the same across scenes) and stores it queryably.

---

## Future Phases (7–18) — spec at the same rigor, build after 1–6 are solid

### Phase 7 — Animation Engine
Scene animation, lip sync, camera movement, transitions, character/object/background movement. Input: Phase 6 assets + Phase 3 scene/shot data. Output: rendered scene clips.

### Phase 8 — Voice Engine
Multi-voice (male/female/child/narrator), multi-language, emotion control, per-character voice consistency (voice profile stored on the character in Phase 2).

### Phase 9 — Music & Sound Engine
Mood-matched background music (comedy/adventure/sad/happy/tension/victory), looping, scene-matched transitions, copyright-safe sourcing/generation, SFX library.

### Phase 10 — Video Assembly Engine
Merge animation + voice + music + SFX + captions/subtitles + transitions + logo + end screen → export. Produces both the Short and the compiled long-form video from the same episode sequence.

### Phase 11 — Thumbnail Engine
CTR-optimized thumbnail generation, A/B variants, text placement, character positioning, emotion optimization.

### Phase 12 — SEO Engine
Title, description, tags, keywords, hashtags, chapters, end screens, cards, pinned comment — generated per video, informed by Phase 5 research.

### Phase 13 — Publishing Engine
Automated YouTube upload: visibility, playlist, category, language, audience, monetization settings, scheduling per §1 cadence rules, retry-safe (dedupe against YouTube state before retrying — Self-Healing contract).

### Phase 14 — Analytics Engine
Pull views, CTR, retention, watch time, subscribers, revenue, RPM/CPM, demographics, traffic source, returning viewers. Store time-series per video/channel.

### Phase 15 — Learning / Optimization Engine
Daily loop: collect analytics → compare to expectations → identify underperformance → adjust prompts/hooks/pacing/thumbnails/titles → feed improvements into Phases 3, 11, 12. This closes the loop back to Phase 1's dashboard.

### Phase 16 — Self-Healing Engine (cross-cutting, start in Phase 1)
**Detect:** API/provider errors, network timeouts, DB errors, Celery task failures, queue stalls, storage failures, upload failures, token expiry, missing/corrupted assets, low-quality outputs, disk/memory pressure, rate limits, outages.
**Recover:** classify error → log root cause → exponential-backoff retry → switch provider if available → resume from last checkpoint (never regenerate completed work) → notify human only after retry limits are exhausted.
**Monitor:** worker health, queue depth, latency, API response times, disk/CPU/memory, DB connections, provider availability — auto-restart/rebalance on threshold breach.
**Audit:** every failure logged with timestamp, root cause, recovery action, retry count, outcome, time-to-recover.

### Phase 17 — Multi-Channel Scaling
Generalize every phase's data model to be channel-scoped (should already be true from Phase 1's `project` entity). Add channel-level branding, isolated knowledge base, independent schedule/analytics/learning loop. Target: 10 → 50 → 100+ channels.

### Phase 18 — Monetization Layer
AdSense linkage, affiliate link injection into descriptions, sponsorship slot tracking, membership tier management, digital product upsell hooks in end screens/pinned comments.

---

## 4. Cross-Phase Pipeline (how it all connects at runtime)

```
Trend Discovery (5) → Opportunity Scoring (5) → Topic Research (5) → Fact Verification (5)
   → Knowledge Base Update (4) → Story Planning (3) → Season Gen (3) → Episode Gen (3)
   → Scene Gen (3) → Character Selection (2) → Asset Generation (6) → Animation (7)
   → Voice (8) → Music (9) → Video Rendering (10) → Thumbnail (11) → SEO (12)
   → Quality Checks (16) → Schedule Selection (13) → YouTube Upload (13)
   → Analytics Collection (14) → Performance Analysis (15) → Prompt Optimization (15)
   → next content cycle
```

---

## 5. What "Done" Means

Not feature completion — **consistent, automated YouTube revenue**, measured by:
- Videos publish on schedule with zero manual editing
- Continuity holds across an entire season with no lore contradictions
- Failure rate requiring human intervention trends toward zero (Phase 16 metric)
- Month-over-month RPM/watch-time trending up from the Learning Engine's changes (Phase 15 metric)
- Same pipeline stood up for a second channel in under a day (Phase 17 metric)

---

## 6. Status Tracker — audited against your uploaded repo (2026-07-10)

**Note on naming:** your repo's own docs number phases differently than this spec (their "Phase 2" = Character/Asset Library CRUD, "Phase 3" = Story Intelligence, "Phase 4" = Knowledge/RAG, "Phase 5" = Research, "Phase 6" = Asset Generation — i.e. everything before rendering/animation output). Table below uses **this spec's** numbering, mapped to what actually exists in your code.

| Phase | Status | Evidence in repo |
|---|---|---|
| 1 — Foundation (auth, projects, asset mgmt) | ✅ Done, functionally | JWT auth, project CRUD, 6-type Asset Manager (soft delete/restore/versioning), 142/142 tests passing. ⚠️ Not production-ready: Redis/MinIO not provisioned in your env, hardcoded default JWT secret, CORS gap |
| 2 — Character Studio | ✅ Done | `character_service.py`, `characters.py` + `character_templates.py` routers, expressions/poses libraries, full CRUD (bug-fixed per `PHASE2_COMPLETION_REPORT.md`) |
| 3 — Story Intelligence | ✅ Done | `backend/services/intelligence/` (world/season/episode/scene/idea/memory/orchestrator), `/si` router, full World→Season→Episode→Scene hierarchy, story memory, retry queue, dashboard — bug-fixed |
| 4 — Knowledge Intelligence (RAG) | ✅ Done | `backend/services/knowledge/` (chunking, embedding, retrieval), `/kn` router, Mock+Ollama embedding providers, Memory+ChromaDB vector store, 84 passing tests, wired into Story Intelligence generation |
| 5 — Research Intelligence | ✅ Done | `backend/services/research/` — trend, topic, research engine, fact verification, opportunity scoring, scheduler, knowledge-integration bridge to Phase 4. Marked "complete and production-ready" in `PHASE5_COMPLETION_REPORT.md` |
| 6 — Asset Generation | 🟡 In progress | Backend is substantial: migration `c4e1f2a3b5d6_phase6_asset_generation_engine`, 8 services (prompt gen, image gen, consistency engine, quality eval, retry engine, shot/asset planning, library), 35-endpoint `/asset-generation` router, `comfyui_provider.py`, `test_asset_generation.py`. **Gap: no frontend pages yet** — nothing under `frontend/src/pages` for asset generation, so it's not usable end-to-end from the UI |
| 7 — Animation Engine (execution) | 🟡 Scaffolded only | `workflow/steps/render_step.py`, `character_step.py`, `scene_step.py`, `ffmpeg_renderer.py` exist as workflow-pipeline steps, plus a separate legacy `animation_service.py` (709 lines) — but there's no dedicated Phase-7 data model/router/completion report the way Phases 2–6 have. Treat as "pipeline plumbing exists, engine not built out" |
| 8 — Voice Engine | 🟡 Scaffolded only | `piper_provider.py` (TTS) and `voice_step.py` exist as a provider + workflow step, no dedicated service layer, router, or DB models |
| 9 — Music & Sound Engine | ❌ Not started | No music/SFX provider, service, or model found |
| 10 — Video Assembly | 🟡 Scaffolded only | `subtitle_step.py`, `ffmpeg_renderer.py`, `whisper_provider.py` (STT) exist; no full assembly service tying render+voice+music+subtitles+export together yet |
| 11 — Thumbnail Engine | ❌ Not started | No matches for thumbnail generation anywhere in the codebase |
| 12 — SEO Engine | ❌ Not started | No title/description/tags/hashtag generation service found (Research phase produces topic data, but nothing packages it into YouTube metadata) |
| 13 — Publishing Engine | ❌ Not started | No YouTube API integration, no upload/scheduling code |
| 14 — Analytics Engine | ❌ Not started | No analytics ingestion/model |
| 15 — Learning/Optimization Engine | ❌ Not started | No feedback loop from analytics into prompt generation |
| 16 — Self-Healing | 🟡 Partial, foundational | `retry_engine_service.py` (Phase 6), `dead_letter.py` + retry queues (Celery tasks), `TaskDispatcher` sync/async fallback, graceful RAG-retrieval fallback — real patterns exist but only within Phases 3–6, not yet a unified cross-cutting system covering rendering/voice/publishing (because those phases don't exist yet) |
| 17 — Multi-Channel | 🟡 Data model ready, not exercised | `projects` entity is already channel-scoped (per `replit.md` architecture notes), but no UI/flow has been tested with 2+ channels yet |
| 18 — Monetization | ❌ Not started | No AdSense/affiliate/membership integration |

### What's actually blocking you from a full pipeline run today
1. **Infra not provisioned in your dev env** — Redis and MinIO must be reachable or generation, uploads, and WebSocket progress silently fail (`PRODUCTION_READINESS.md` BLOCK-1/BLOCK-2).
2. **Phase 6 has no frontend** — the asset-generation backend can't be driven by a user yet.
3. **Everything after Phase 6** (animation execution, voice, music, assembly, thumbnails, SEO, publishing, analytics, learning) is either a bare workflow-step stub or doesn't exist — this is the majority of the remaining build.

### Recommended next steps, in order
1. **Fix the two production blockers** (Redis + MinIO reachable, real `SECRET_KEY`, tighten CORS) — 30 min–1 hr, unblocks testing everything downstream.
2. **Finish Phase 6 frontend**: Asset Generation dashboard, prompt/job monitoring UI, consistency/quality review screens, reusing the patterns from the Story Intelligence and Knowledge frontends you already built.
3. **Promote Phase 7 (Animation) from workflow-step stub to a real phase**: give it its own service layer, DB models (render jobs, scene→clip mapping), router, and completion report — mirror the Phase 3–6 architecture (`models → repository → service → router → Celery task → frontend`) rather than leaving it inside generic `workflow/steps`.
4. **Phase 8 (Voice) next**, same pattern, building on the existing `piper_provider`.
5. Only after 6–8 are real, tackle **9–10 (Music, Assembly)** — video assembly needs voice + music + animation all producing real outputs first.
6. **11–13 (Thumbnail, SEO, Publishing)** can be built in parallel with each other once 10 outputs a finished video file — they all just consume the finished video + metadata.
7. **14–15 (Analytics, Learning)** only make sense once videos are actually being published (13), so they're correctly last before scaling.

> Re-paste this table's status after each phase lands and I'll keep it current.