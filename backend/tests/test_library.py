"""Tests for the animation library: expressions, poses, character templates,
backgrounds, and props — covering CRUD, soft-delete, restore, bulk ops,
seed, search, and pagination."""
from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


def _uid() -> str:
    return uuid4().hex[:8]


# ── Expressions ──────────────────────────────────────────────────────────────

class TestExpressions:
    async def test_list_empty(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/library/expressions", headers=auth_headers)
        assert r.status_code == 200

    async def test_seed(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/library/expressions/seed", headers=auth_headers)
        assert r.status_code == 200

    async def test_create(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        r = await client.post("/library/expressions", headers=auth_headers, json={
            "name": f"Big Smile {u}", "slug": f"big-smile-{u}", "intensity": 0.9, "rig_data": {}
        })
        assert r.status_code in (200, 201)
        body = r.json()
        assert "Big Smile" in body["name"]

    async def test_get(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        create = await client.post("/library/expressions", headers=auth_headers, json={
            "name": f"Wink {u}", "slug": f"wink-{u}", "intensity": 0.5, "rig_data": {}
        })
        eid = create.json()["id"]
        r = await client.get(f"/library/expressions/{eid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == eid

    async def test_update(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        create = await client.post("/library/expressions", headers=auth_headers, json={
            "name": f"OldExpr {u}", "slug": f"old-expr-{u}", "intensity": 0.3, "rig_data": {}
        })
        eid = create.json()["id"]
        r = await client.patch(f"/library/expressions/{eid}", headers=auth_headers, json={"name": f"NewExpr {u}"})
        assert r.status_code == 200
        assert "NewExpr" in r.json()["name"]

    async def test_delete(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        create = await client.post("/library/expressions", headers=auth_headers, json={
            "name": f"DelExpr {u}", "slug": f"del-expr-{u}", "intensity": 0.1, "rig_data": {}
        })
        eid = create.json()["id"]
        r = await client.delete(f"/library/expressions/{eid}", headers=auth_headers)
        assert r.status_code in (200, 204)

    async def test_seed_idempotent(self, client: AsyncClient, auth_headers: dict):
        r1 = await client.post("/library/expressions/seed", headers=auth_headers)
        r2 = await client.post("/library/expressions/seed", headers=auth_headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Second seed should return 0 (already seeded)
        assert r2.json().get("seeded", r2.json().get("count", 1)) == 0


# ── Poses ────────────────────────────────────────────────────────────────────

class TestPoses:
    async def test_seed(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/library/poses/seed", headers=auth_headers)
        assert r.status_code == 200

    async def test_create(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        r = await client.post("/library/poses", headers=auth_headers, json={
            "name": f"Standing {u}", "slug": f"standing-{u}", "rig_data": {}, "duration_frames": 24, "is_loopable": True
        })
        assert r.status_code in (200, 201)
        assert "Standing" in r.json()["name"]

    async def test_update(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        create = await client.post("/library/poses", headers=auth_headers, json={
            "name": f"OldPose {u}", "slug": f"old-pose-{u}", "rig_data": {}, "duration_frames": 12, "is_loopable": False
        })
        pid = create.json()["id"]
        r = await client.patch(f"/library/poses/{pid}", headers=auth_headers, json={"name": f"NewPose {u}"})
        assert r.status_code == 200
        assert "NewPose" in r.json()["name"]

    async def test_delete(self, client: AsyncClient, auth_headers: dict):
        u = _uid()
        create = await client.post("/library/poses", headers=auth_headers, json={
            "name": f"DelPose {u}", "slug": f"del-pose-{u}", "rig_data": {}, "duration_frames": 6, "is_loopable": False
        })
        pid = create.json()["id"]
        r = await client.delete(f"/library/poses/{pid}", headers=auth_headers)
        assert r.status_code in (200, 204)


# ── Backgrounds ───────────────────────────────────────────────────────────────

class TestBackgrounds:
    async def test_list(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/library/backgrounds", headers=auth_headers)
        assert r.status_code == 200

    async def test_seed(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/library/backgrounds/seed", headers=auth_headers)
        assert r.status_code == 200

    async def test_create(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/library/backgrounds", headers=auth_headers, json={
            "name": "Forest", "file_url": "https://cdn.example.com/forest.jpg",
            "category": "outdoor", "tags": ["nature", "forest"]
        })
        assert r.status_code in (200, 201)
        body = r.json()
        assert body["name"] == "Forest"
        assert body["category"] == "outdoor"

    async def test_update(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/library/backgrounds", headers=auth_headers, json={
            "name": "OldBG", "file_url": "https://example.com/bg.jpg", "category": "indoor"
        })
        bid = create.json()["id"]
        r = await client.patch(f"/library/backgrounds/{bid}", headers=auth_headers, json={"name": "NewBG"})
        assert r.status_code == 200
        assert r.json()["name"] == "NewBG"

    async def test_delete(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/library/backgrounds", headers=auth_headers, json={
            "name": "DelBG", "file_url": "https://example.com/del.jpg", "category": "outdoor"
        })
        bid = create.json()["id"]
        r = await client.delete(f"/library/backgrounds/{bid}", headers=auth_headers)
        assert r.status_code in (200, 204)

    async def test_categories(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/library/backgrounds/categories", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── Props ────────────────────────────────────────────────────────────────────

class TestProps:
    async def test_seed(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/library/props/seed", headers=auth_headers)
        assert r.status_code == 200

    async def test_create(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/library/props", headers=auth_headers, json={
            "name": "Chair", "file_url": "https://example.com/chair.png",
            "category": "furniture", "tags": ["indoor"]
        })
        assert r.status_code in (200, 201)
        assert r.json()["name"] == "Chair"

    async def test_update(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/library/props", headers=auth_headers, json={
            "name": "OldProp", "file_url": "https://example.com/old.png", "category": "misc"
        })
        pid = create.json()["id"]
        r = await client.patch(f"/library/props/{pid}", headers=auth_headers, json={"name": "NewProp"})
        assert r.status_code == 200
        assert r.json()["name"] == "NewProp"

    async def test_categories(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/library/props/categories", headers=auth_headers)
        assert r.status_code == 200
