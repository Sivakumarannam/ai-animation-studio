"""
Shared pytest fixtures for the AI Animation Studio backend.

These are pure integration tests that hit the real running API server on
localhost:8000. This is the simplest, most reliable approach given that
the backend uses asyncpg + SQLAlchemy async sessions.

The backend MUST be running (via uvicorn) for these tests to work.
Run: cd backend && uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
import httpx


BASE_URL = "http://localhost:8000/api/v1"


@pytest_asyncio.fixture()
async def client() -> httpx.AsyncClient:
    """HTTP client pointing at the live API server."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest_asyncio.fixture()
async def auth_headers(client: httpx.AsyncClient) -> dict[str, str]:
    """Register + login a unique test user; return Bearer headers."""
    email = f"test_{uuid4().hex[:8]}@pytest.com"
    await client.post("/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "full_name": "Pytest User",
    })
    r = await client.post("/auth/login", json={
        "email": email,
        "password": "TestPass123!",
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest_asyncio.fixture()
async def project(client: httpx.AsyncClient, auth_headers: dict) -> dict[str, Any]:
    """Create and return a test project."""
    r = await client.post("/projects", headers=auth_headers, json={
        "title": "Test Project",
        "description": "Automated test",
        "plugin_id": "telugu_family_comedy",
    })
    assert r.status_code in (200, 201), f"project create failed: {r.text}"
    return r.json()
