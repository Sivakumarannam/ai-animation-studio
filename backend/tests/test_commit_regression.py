"""
Regression tests for the session-commit bug in Celery task core functions
(Phases 3, 4, and 5).

ROOT CAUSE: `async for session in get_session(): ... return result` causes
Python to call .aclose() on the generator, which fires GeneratorExit at the
yield line — so `await session.commit()` never executes.

FIX: Each core function now calls `await session.commit()` explicitly before
the `return`, ensuring persistence regardless of generator teardown semantics.

TEST DESIGN (the only pattern that catches a missing commit):
  1. Call the core function directly (not via HTTP, not via a mock session).
  2. After it returns, open a *separate, new* session and query for the rows
     that should have been written.
  3. Assert the rows exist.

A test that reuses the same session the function wrote to would NOT catch a
missing commit, because uncommitted writes are still visible within the same
transaction.

Requirements:
  - Backend must be running (uvicorn on :8000) so the shared API fixtures
    (auth, project, collection, document) can be set up via HTTP.
  - DATABASE_URL must be set in the environment (same requirement as the
    rest of the test suite).
"""
from __future__ import annotations

import os
from uuid import uuid4, UUID

import pytest
import pytest_asyncio
import httpx
from sqlalchemy import select, func

BASE_URL = "http://localhost:8000/api/v1"


# ---------------------------------------------------------------------------
# DB initialisation — once per session
# ---------------------------------------------------------------------------

def _init_test_db() -> None:
    """Initialise the async SQLAlchemy engine for direct DB access in tests."""
    from database.connection import init_db

    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        pytest.skip("DATABASE_URL not set; skipping commit-regression tests")

    # Normalize: asyncpg needs postgresql+asyncpg:// and no ?sslmode= param.
    url = raw.replace("postgresql://", "postgresql+asyncpg://")
    if "?" in url:
        url = url.split("?")[0]

    # NullPool is required in forked/thread contexts (same reason Celery uses it).
    init_db(url, use_null_pool=True)


def _init_providers() -> None:
    """Register all mock providers — mirrors FastAPI lifespan startup."""
    from agents.registry import get_provider_registry
    from agents.provider_factory import setup_providers
    from apps.api.config import get_settings

    registry = get_provider_registry()
    settings = get_settings()
    setup_providers(settings, registry)


_init_test_db()
_init_providers()


# ---------------------------------------------------------------------------
# Shared HTTP fixtures (mirrors conftest.py pattern)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def _client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest_asyncio.fixture()
async def _auth_headers(_client):
    email = f"commit_regression_{uuid4().hex[:8]}@pytest.com"
    await _client.post("/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "full_name": "Commit Regression Test",
    })
    r = await _client.post("/auth/login", json={
        "email": email,
        "password": "TestPass123!",
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest_asyncio.fixture()
async def _project(_client, _auth_headers):
    r = await _client.post("/projects", headers=_auth_headers, json={
        "title": "Commit Regression Project",
        "description": "Created by test_commit_regression",
        "plugin_id": "telugu_family_comedy",
    })
    assert r.status_code in (200, 201), f"project create failed: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# Helper — fresh DB session
# ---------------------------------------------------------------------------

async def _fresh_query(stmt):
    """Run a SELECT in a brand-new session and return the scalar result.

    Using a separate session is critical: uncommitted writes from the core
    function's session would be invisible here, exposing any missing commit.
    """
    from database.connection import session_scope
    async with session_scope() as session:
        result = await session.execute(stmt)
        return result


# ===========================================================================
# Phase 4 — Knowledge tasks  (_process_document_core, _reembed_collection_core)
# ===========================================================================

@pytest.mark.asyncio
class TestKnowledgeTaskCommit:
    """Verify that _process_document_core commits its writes to the DB."""

    @pytest_asyncio.fixture()
    async def _collection(self, _client, _auth_headers, _project):
        r = await _client.post(
            f"/kn/projects/{_project['id']}/collections",
            headers=_auth_headers,
            json={"name": "Regression Collection", "collection_type": "general"},
        )
        assert r.status_code == 201, r.text
        return r.json()

    @pytest_asyncio.fixture()
    async def _document(self, _client, _auth_headers, _collection):
        r = await _client.post(
            f"/kn/collections/{_collection['id']}/documents",
            headers=_auth_headers,
            json={
                "title": "Regression Doc",
                "source_type": "text",
                "raw_text": (
                    "This is a test document written specifically to verify "
                    "that the Celery task core function commits its session. "
                    "It must appear in kn_chunks after _process_document_core "
                    "returns, when queried from a completely separate session."
                ),
            },
        )
        assert r.status_code == 201, r.text
        return r.json()

    async def test_process_document_core_commits(self, _document):
        """
        Call _process_document_core directly, then open a fresh session and
        assert that kn_chunks rows exist for the document.

        Before the fix, session.commit() was silently skipped on early return,
        so the fresh session would see zero chunks even though the function
        returned success.
        """
        from apps.worker.tasks.knowledge_tasks import _process_document_core
        from database.models.knowledge import KnowledgeChunk

        doc_id = _document["id"]

        # Call the core function directly (job_id is a random UUID;
        # job lookup will fail gracefully → job=None, function still runs).
        result = await _process_document_core(
            document_id=doc_id,
            job_id=str(uuid4()),
        )

        # Basic sanity: function returned a result dict
        assert isinstance(result, dict), f"Expected dict, got: {result!r}"
        assert result.get("document_id") == doc_id

        # Critical assertion: verify via a SEPARATE session that chunks exist.
        # A missing commit would cause this to return 0 rows.
        stmt = select(func.count()).where(
            KnowledgeChunk.document_id == UUID(doc_id)
        )
        count_result = await _fresh_query(stmt)
        chunk_count = count_result.scalar_one()

        assert chunk_count > 0, (
            f"Expected kn_chunks rows for document {doc_id} to be committed, "
            f"but a fresh session found {chunk_count} rows. "
            "This indicates session.commit() was not called before return."
        )

    async def test_reembed_collection_core_commits(self, _collection, _document):
        """
        Call _reembed_collection_core on a collection that has an unprocessed
        document, then verify via a fresh session that kn_chunks were created
        and committed.

        The document is intentionally left in "pending" state so that
        _reembed_collection_core processes it for the first time. Calling
        _process_document_core first would leave already-committed chunks,
        and the subsequent delete+re-insert in _reembed_collection_core would
        be tested differently from the commit path we care about.
        """
        from apps.worker.tasks.knowledge_tasks import _reembed_collection_core
        from database.models.knowledge import KnowledgeChunk

        doc_id = _document["id"]
        collection_id = _collection["id"]

        result = await _reembed_collection_core(
            collection_id=collection_id,
            job_id=str(uuid4()),
        )
        assert isinstance(result, dict)
        assert result.get("collection_id") == collection_id

        # Fresh session must see the chunks produced by _reembed_collection_core.
        stmt = select(func.count()).where(
            KnowledgeChunk.document_id == UUID(doc_id)
        )
        count_result = await _fresh_query(stmt)
        assert count_result.scalar_one() > 0, (
            "kn_chunks not visible in fresh session after _reembed_collection_core. "
            "session.commit() may not have been called before return."
        )


# ===========================================================================
# Phase 5 — Research tasks  (_discover_trends_core, _research_refresh_core)
# ===========================================================================

@pytest.mark.asyncio
class TestResearchTaskCommit:
    """Verify that research core functions commit their writes to the DB."""

    async def test_discover_trends_core_commits(self):
        """
        _discover_trends_core must write an rs_history row and commit it.
        A fresh session must see that row after the function returns.

        job_id is a random UUID; the job lookup fails gracefully → job=None.
        The scheduler still runs and writes rs_history regardless.
        """
        from apps.worker.tasks.research_tasks import _discover_trends_core
        from database.models.research import ResearchHistory

        # Count rows before the call
        count_before_stmt = select(func.count()).select_from(ResearchHistory).where(
            ResearchHistory.run_type == "trend_discovery"
        )
        before_result = await _fresh_query(count_before_stmt)
        count_before = before_result.scalar_one()

        result = await _discover_trends_core(job_id=str(uuid4()))
        assert isinstance(result, dict)

        # Fresh session must show a new rs_history row
        count_after_stmt = select(func.count()).select_from(ResearchHistory).where(
            ResearchHistory.run_type == "trend_discovery"
        )
        after_result = await _fresh_query(count_after_stmt)
        count_after = after_result.scalar_one()

        assert count_after > count_before, (
            f"Expected a new rs_history row (run_type='trend_discovery') to be "
            f"committed, but fresh-session count went from {count_before} to "
            f"{count_after}. session.commit() may not have been called before return."
        )

    async def test_research_refresh_core_commits(self):
        """
        _research_refresh_core must commit its rs_history write.
        """
        from apps.worker.tasks.research_tasks import _research_refresh_core
        from database.models.research import ResearchHistory

        count_before_stmt = select(func.count()).select_from(ResearchHistory)
        before_result = await _fresh_query(count_before_stmt)
        count_before = before_result.scalar_one()

        result = await _research_refresh_core(job_id=str(uuid4()))
        assert isinstance(result, dict)

        count_after_stmt = select(func.count()).select_from(ResearchHistory)
        after_result = await _fresh_query(count_after_stmt)
        count_after = after_result.scalar_one()

        assert count_after > count_before, (
            "No new rs_history rows visible in fresh session after "
            "_research_refresh_core. session.commit() may not have executed."
        )

    async def test_scheduler_tick_core_commits(self):
        """
        _scheduler_tick_core runs the full research pipeline in sequence and
        must commit. The composite result dict and fresh-session rs_history
        count increase together confirm the fix.
        """
        from apps.worker.tasks.research_tasks import _scheduler_tick_core
        from database.models.research import ResearchHistory

        count_before_stmt = select(func.count()).select_from(ResearchHistory)
        before_result = await _fresh_query(count_before_stmt)
        count_before = before_result.scalar_one()

        result = await _scheduler_tick_core(job_id=str(uuid4()))
        assert isinstance(result, dict), f"Expected dict, got: {result!r}"

        count_after_stmt = select(func.count()).select_from(ResearchHistory)
        after_result = await _fresh_query(count_after_stmt)
        count_after = after_result.scalar_one()

        assert count_after > count_before, (
            "No new rs_history rows visible in fresh session after "
            "_scheduler_tick_core. session.commit() may not have executed."
        )


# ===========================================================================
# Phase 3 — Intelligence tasks  (_run_full_pipeline_core, _generate_episode_core)
# ===========================================================================

@pytest.mark.asyncio
class TestIntelligenceTaskCommit:
    """Verify that intelligence core functions commit their writes to the DB."""

    @staticmethod
    async def _make_job(project_id: str, job_type: str) -> str:
        """Insert a GenerationJob row directly and return its UUID string.

        The intelligence orchestrator calls get_job(job_id) internally on both
        success and failure paths, so the job must exist in the DB before the
        core function is called.
        """
        from database.connection import session_scope
        from database.models.intelligence import GenerationJob

        job_id = uuid4()
        async with session_scope() as sess:
            job = GenerationJob(
                id=job_id,
                project_id=UUID(project_id),
                job_type=job_type,
                status="pending",
                execution_mode="sync",
            )
            sess.add(job)
        return str(job_id)

    async def test_run_full_pipeline_core_commits(self, _project):
        """
        _run_full_pipeline_core must persist si_worlds, si_seasons, si_episodes,
        and si_story_scenes. A fresh session opened after the call must see these
        rows.

        Before the fix, session.commit() was skipped on early return, so all
        four tables would show zero new rows despite the function logging
        "pipeline_complete success".
        """
        from apps.worker.tasks.intelligence_tasks import _run_full_pipeline_core
        from database.models.intelligence import World

        project_id = _project["id"]
        job_id = await self._make_job(project_id, "full_pipeline")

        # Count worlds before
        count_before_stmt = select(func.count()).select_from(World).where(
            World.project_id == UUID(project_id)
        )
        before_result = await _fresh_query(count_before_stmt)
        count_before = before_result.scalar_one()

        result = await _run_full_pipeline_core(
            project_id=project_id,
            job_id=job_id,
            genre="comedy",
            story_type="comedy",
            episode_count=1,
        )
        assert isinstance(result, dict), f"Expected dict, got: {result!r}"

        # Fresh session must see the new world
        count_after_stmt = select(func.count()).select_from(World).where(
            World.project_id == UUID(project_id)
        )
        after_result = await _fresh_query(count_after_stmt)
        count_after = after_result.scalar_one()

        assert count_after > count_before, (
            f"Expected si_worlds rows for project {project_id} to be committed, "
            f"but fresh-session count went from {count_before} to {count_after}. "
            "session.commit() may not have been called before return in "
            "_run_full_pipeline_core."
        )

    async def test_generate_episode_core_commits(self, _project):
        """
        _generate_episode_core must persist a new si_episodes row.

        We first run the full pipeline to create a world + season (using a fresh
        GenerationJob), then call _generate_episode_core with another fresh job
        and verify the new episode is visible in a separate session.
        """
        from apps.worker.tasks.intelligence_tasks import (
            _run_full_pipeline_core,
            _generate_episode_core,
        )
        from database.models.intelligence import World, Season, Episode
        from database.connection import session_scope

        project_id = _project["id"]

        # Bootstrap: create world + season via the full pipeline
        pipeline_job_id = await self._make_job(project_id, "full_pipeline")
        pipeline_result = await _run_full_pipeline_core(
            project_id=project_id,
            job_id=pipeline_job_id,
            genre="comedy",
            story_type="comedy",
            episode_count=1,
        )
        assert isinstance(pipeline_result, dict)

        # Find the created world and season from a fresh session
        async with session_scope() as sess:
            world_row = (await sess.execute(
                select(World).where(World.project_id == UUID(project_id))
            )).scalars().first()
            assert world_row is not None, "No si_worlds row found after _run_full_pipeline_core"

            season_row = (await sess.execute(
                select(Season).where(Season.world_id == world_row.id)
            )).scalars().first()
            assert season_row is not None, "No si_seasons row found after _run_full_pipeline_core"

            world_id = str(world_row.id)
            season_id = str(season_row.id)

        # Count episodes before the second call
        count_before_stmt = select(func.count()).select_from(Episode).where(
            Episode.season_id == UUID(season_id)
        )
        before_result = await _fresh_query(count_before_stmt)
        count_before = before_result.scalar_one()

        # Create the job required by the orchestrator, then call the core function
        ep_job_id = await self._make_job(project_id, "generate_episode")
        ep_result = await _generate_episode_core(
            project_id=project_id,
            job_id=ep_job_id,
            season_id=season_id,
            world_id=world_id,
        )
        assert isinstance(ep_result, dict), f"Expected dict, got: {ep_result!r}"

        # Fresh session must see the new episode
        count_after_stmt = select(func.count()).select_from(Episode).where(
            Episode.season_id == UUID(season_id)
        )
        after_result = await _fresh_query(count_after_stmt)
        count_after = after_result.scalar_one()

        assert count_after > count_before, (
            f"Expected new si_episodes row for season {season_id} to be committed, "
            f"but fresh-session count went from {count_before} to {count_after}. "
            "session.commit() may not have been called before return in "
            "_generate_episode_core."
        )
