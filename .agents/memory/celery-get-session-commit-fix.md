---
name: Celery task get_session commit bug — fix pattern
description: The broken async-for-get_session pattern in Celery core functions, how it was fixed, and what regression tests need to run correctly.
---

# Celery task get_session commit bug

## The rule
In Celery task "core" async functions, `async for session in get_session(): … return result` **skips the commit** because Python calls `.aclose()` on the generator, which fires `GeneratorExit` at the yield line before `await session.commit()` can execute.

**Fix applied:** Add `await session.commit()` explicitly before every `return` inside the `async for session in get_session():` loop.

**Why:** `get_session()` is correctly designed for FastAPI `Depends()` where the framework fully drains the generator. When used in Celery with an early `return`, the post-yield commit never runs.

**How to apply:** In any Celery core function that uses `async for session in get_session():`, add `await session.commit()` immediately before the `return` statement inside the loop body. Better long-term: migrate all Celery core functions to use `async with session_scope() as session:` (which already exists in `backend/database/connection.py`) — that's what Phases 6-8 use correctly.

## Files fixed
- `backend/apps/worker/tasks/intelligence_tasks.py` — `_run_full_pipeline_core`, `_generate_episode_core`
- `backend/apps/worker/tasks/knowledge_tasks.py` — `_process_document_core`, `_reembed_collection_core`
- `backend/apps/worker/tasks/research_tasks.py` — `_discover_trends_core`, `_research_topic_core`, `_verify_facts_core`, `_research_refresh_core`, `_score_opportunities_core`, `_scheduler_tick_core`

## Regression test setup requirements
Tests in `backend/tests/test_commit_regression.py` call core functions directly (not via HTTP). Two things must be initialized before the tests run:
1. `_init_test_db()` — calls `init_db(url, use_null_pool=True)` with normalized asyncpg URL
2. `_init_providers()` — calls `setup_providers(get_settings(), get_provider_registry())` to register mock providers

**Intelligence tests specifically** require a real `GenerationJob` row in `si_generation_jobs` before calling `_run_full_pipeline_core` or `_generate_episode_core`, because the orchestrator calls `get_job(job_id)` internally on both success and error paths. Use `session_scope()` to insert the row directly in the test.
