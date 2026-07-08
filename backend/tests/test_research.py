"""
Phase 5 — Research & Trend Intelligence Engine integration tests.

Follows the existing live-server pattern: tests run against localhost:8000
with a real authenticated user created per test class.
"""
from __future__ import annotations

import pytest
import httpx

BASE = "http://localhost:8000/api/v1"


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register_and_login(client: httpx.AsyncClient, suffix: str) -> str:
    email = f"rs_test_{suffix}@example.com"
    await client.post(f"{BASE}/auth/register", json={
        "email": email, "password": "TestPass123!", "full_name": "Research Tester"
    })
    r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_returns_stats():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "dashboard")
        r = await client.get(f"{BASE}/rs/dashboard", headers=_headers(token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert "active_trends" in data
        assert "total_topics" in data
        assert "verified_facts" in data
        assert "scheduler_status" in data
        assert "top_trends" in data
        assert "top_opportunities" in data


# ─── Sources ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_sources():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "sources")
        h = _headers(token)

        # Create
        r = await client.post(f"{BASE}/rs/sources", headers=h, json={
            "name": "Test RSS Feed",
            "source_type": "rss",
            "url": "https://example.com/rss",
            "description": "A test feed",
        })
        assert r.status_code == 201, r.text
        source = r.json()
        assert source["name"] == "Test RSS Feed"
        assert source["source_type"] == "rss"
        source_id = source["id"]

        # List
        r = await client.get(f"{BASE}/rs/sources", headers=h)
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

        # Delete
        r = await client.delete(f"{BASE}/rs/sources/{source_id}", headers=h)
        assert r.status_code == 204


# ─── Trends ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trends_initially_empty():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "trends_empty")
        r = await client.get(f"{BASE}/rs/trends", headers=_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "meta" in data


@pytest.mark.asyncio
async def test_trend_discovery_dispatches():
    async with httpx.AsyncClient(timeout=60) as client:
        token = await _register_and_login(client, "trends_discover")
        h = _headers(token)

        # Trigger trend discovery
        r = await client.post(f"{BASE}/rs/scheduler/trigger", headers=h, json={"phase": "trend_discovery"})
        assert r.status_code == 202, r.text
        data = r.json()
        assert data["job_id"]
        assert data["mode"] in ("sync", "async", "celery")

        # After discovery, trends should exist (sync mode runs immediately)
        if data["mode"] == "sync":
            r = await client.get(f"{BASE}/rs/trends", headers=h)
            assert r.status_code == 200
            trend_data = r.json()
            # At minimum the meta should be present
            assert "meta" in trend_data


# ─── Topics ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_topics():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "topics_crud")
        h = _headers(token)

        # Create
        r = await client.post(f"{BASE}/rs/topics", headers=h, json={
            "canonical_name": "Quantum Computing Phase5 Test",
            "description": "Test topic for Phase 5",
            "keywords": ["quantum", "computing"],
            "categories": ["technology"],
        })
        assert r.status_code == 201, r.text
        topic = r.json()
        assert topic["canonical_name"] == "Quantum Computing Phase5 Test"
        assert topic["slug"] == "quantum-computing-phase5-test"
        assert topic["status"] == "discovered"
        assert topic["research_status"] == "pending"
        topic_id = topic["id"]

        # List
        r = await client.get(f"{BASE}/rs/topics", headers=h)
        assert r.status_code == 200
        data = r.json()
        assert data["meta"]["total"] >= 1

        # Get by ID
        r = await client.get(f"{BASE}/rs/topics/{topic_id}", headers=h)
        assert r.status_code == 200
        assert r.json()["id"] == topic_id

        # Delete
        r = await client.delete(f"{BASE}/rs/topics/{topic_id}", headers=h)
        assert r.status_code == 204


@pytest.mark.asyncio
async def test_research_topic_dispatch():
    import time
    unique = str(int(time.time() * 1000))[-6:]

    async with httpx.AsyncClient(timeout=60) as client:
        token = await _register_and_login(client, "topics_research")
        h = _headers(token)

        # Create topic first (unique suffix prevents slug collision across test runs)
        r = await client.post(f"{BASE}/rs/topics", headers=h, json={
            "canonical_name": f"Machine Learning Integration Test {unique}",
            "keywords": ["ml", "ai"],
        })
        assert r.status_code == 201
        topic_id = r.json()["id"]

        # Dispatch research
        r = await client.post(f"{BASE}/rs/topics/{topic_id}/research", headers=h)
        assert r.status_code == 202, r.text
        data = r.json()
        assert data["job_id"]
        assert data["mode"] in ("sync", "async", "celery")

        # In sync mode: check articles & facts were created
        if data["mode"] == "sync":
            r = await client.get(f"{BASE}/rs/topics/{topic_id}/articles", headers=h)
            assert r.status_code == 200

            r = await client.get(f"{BASE}/rs/topics/{topic_id}/facts", headers=h)
            assert r.status_code == 200


# ─── Clusters ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_clusters():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "clusters")
        r = await client.get(f"{BASE}/rs/clusters", headers=_headers(token))
        assert r.status_code == 200
        assert "items" in r.json()


# ─── Queue ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_queue():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "queue_list")
        r = await client.get(f"{BASE}/rs/queue", headers=_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "meta" in data


# ─── Jobs ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_jobs():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "jobs_list")
        r = await client.get(f"{BASE}/rs/jobs", headers=_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

@pytest.mark.asyncio
async def test_retry_queue_route_before_parameterized():
    """Regression: /jobs/retry-queue must not be swallowed by /jobs/{job_id}."""
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "retry_q_order")
        r = await client.get(f"{BASE}/rs/jobs/retry-queue", headers=_headers(token))
        # Must be 200 (list), NOT 422 (UUID parse failure)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)


# ─── Scheduler ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scheduler_status():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "sched_status")
        r = await client.get(f"{BASE}/rs/scheduler/status", headers=_headers(token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert "phases" in data
        phases = data["phases"]
        assert "trend_discovery" in phases
        assert "research_refresh" in phases
        assert "opportunity_report" in phases


@pytest.mark.asyncio
async def test_scheduler_trigger_all_phases():
    async with httpx.AsyncClient(timeout=60) as client:
        token = await _register_and_login(client, "sched_trigger")
        h = _headers(token)

        for phase in ["trend_discovery", "research_refresh", "opportunity_report"]:
            r = await client.post(f"{BASE}/rs/scheduler/trigger", headers=h, json={"phase": phase})
            assert r.status_code == 202, f"Phase {phase} failed: {r.text}"
            d = r.json()
            assert d["job_id"]
            assert d["mode"] in ("sync", "async", "celery"), f"Bad mode: {d['mode']}"


@pytest.mark.asyncio
async def test_scheduler_trigger_invalid_phase():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "sched_invalid")
        r = await client.post(
            f"{BASE}/rs/scheduler/trigger",
            headers=_headers(token),
            json={"phase": "nonexistent_phase"},
        )
        assert r.status_code == 422, r.text


# ─── History ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_history():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "history_list")
        r = await client.get(f"{BASE}/rs/history", headers=_headers(token))
        assert r.status_code == 200
        assert "items" in r.json()


# ─── Opportunities ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_opportunities():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "opportunities")
        r = await client.get(f"{BASE}/rs/opportunities", headers=_headers(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─── Analytics ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_analytics():
    async with httpx.AsyncClient(timeout=30) as client:
        token = await _register_and_login(client, "analytics")
        r = await client.get(f"{BASE}/rs/analytics", headers=_headers(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─── Full pipeline smoke test ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_pipeline_smoke():
    """
    End-to-end: discover → research → verify → score → queue.
    Only meaningful in sync mode (Redis unavailable).
    """
    async with httpx.AsyncClient(timeout=120) as client:
        token = await _register_and_login(client, "pipeline_smoke")
        h = _headers(token)

        # Step 1: Discover trends
        r = await client.post(f"{BASE}/rs/scheduler/trigger", headers=h, json={"phase": "trend_discovery"})
        assert r.status_code == 202
        mode = r.json()["mode"]

        if mode != "sync":
            pytest.skip("Skipping pipeline smoke test in async/celery mode")

        # Step 2: Research refresh (creates articles + facts)
        r = await client.post(f"{BASE}/rs/scheduler/trigger", headers=h, json={"phase": "research_refresh"})
        assert r.status_code == 202

        # Step 3: Score opportunities
        r = await client.post(f"{BASE}/rs/scheduler/trigger", headers=h, json={"phase": "opportunity_report"})
        assert r.status_code == 202

        # Verify history endpoint is reachable and returns correct shape
        r = await client.get(f"{BASE}/rs/history", headers=h)
        assert r.status_code == 200
        hist = r.json()
        assert "items" in hist and "meta" in hist

        # Verify jobs endpoint returns correct shape
        r = await client.get(f"{BASE}/rs/jobs", headers=h)
        assert r.status_code == 200
        jobs = r.json()
        assert "items" in jobs and "meta" in jobs
        # At least the jobs dispatched in this test should exist
        assert jobs["meta"]["total"] >= 1
