"""Tests for the Asset Manager: per-type CRUD, soft delete/restore, bulk ops,
version history, search, stats, and seed for all 7 asset types."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


ASSET_TYPES = ["background", "prop", "animation_preset", "audio", "music", "sound_effect"]

# Minimal valid payload for creating each asset type via the asset manager
_CREATE_PAYLOAD = {
    "background":        {"name": "Test BG",      "category": "outdoor"},
    "prop":              {"name": "Test Prop",     "category": "furniture"},
    "animation_preset":  {"name": "Test Anim",    "category": "action"},
    "audio":             {"name": "Test Audio",    "category": "sfx", "duration_seconds": 5.0},
    "music":             {"name": "Test Music",    "category": "background", "duration_seconds": 120.0},
    "sound_effect":      {"name": "Test SFX",     "category": "ambient", "duration_seconds": 2.0},
}


class TestAssetManagerStats:
    async def test_stats(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/asset-manager/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "backgrounds" in body
        assert "props" in body


class TestAssetManagerSearch:
    async def test_search_get(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/asset-manager/search", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "results" in body   # AssetSearchResponse uses "results" key
        assert "total" in body

    async def test_search_post(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/asset-manager/search", headers=auth_headers, json={
            "query": "", "page": 1, "page_size": 10
        })
        assert r.status_code == 200
        body = r.json()
        assert "results" in body   # AssetSearchResponse uses "results" key

    async def test_search_with_query(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/asset-manager/search", headers=auth_headers, json={
            "query": "nonexistent_xyz_12345", "page": 1, "page_size": 10
        })
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_search_show_deleted(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/asset-manager/search", headers=auth_headers, json={
            "query": "", "show_deleted": True, "page": 1, "page_size": 10
        })
        assert r.status_code == 200


class TestAssetManagerSeed:
    async def test_seed_all_types(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            r = await client.post(f"/asset-manager/{at}/seed", headers=auth_headers)
            assert r.status_code == 200, f"seed failed for {at}: {r.text}"

    async def test_seed_idempotent(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            await client.post(f"/asset-manager/{at}/seed", headers=auth_headers)
            r = await client.post(f"/asset-manager/{at}/seed", headers=auth_headers)
            assert r.status_code == 200


class TestAssetManagerCRUD:
    """Per-type create / list / get / update / delete (soft) / restore."""

    async def _create(self, client, headers, asset_type):
        payload = _CREATE_PAYLOAD[asset_type]
        r = await client.post(f"/asset-manager/{asset_type}", headers=headers, json=payload)
        assert r.status_code in (200, 201), f"create {asset_type} failed: {r.text}"
        return r.json()

    async def test_list(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            r = await client.get(f"/asset-manager/{at}", headers=auth_headers)
            assert r.status_code == 200, f"list {at}: {r.text}"

    async def test_create_all_types(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            body = await self._create(client, auth_headers, at)
            assert "id" in body

    async def test_get(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            created = await self._create(client, auth_headers, at)
            r = await client.get(f"/asset-manager/{at}/{created['id']}", headers=auth_headers)
            assert r.status_code == 200
            assert r.json()["id"] == created["id"]

    async def test_update(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            created = await self._create(client, auth_headers, at)
            r = await client.patch(
                f"/asset-manager/{at}/{created['id']}", headers=auth_headers,
                json={"name": f"Updated {at}"}
            )
            assert r.status_code == 200
            assert r.json()["name"] == f"Updated {at}"

    async def test_soft_delete(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            created = await self._create(client, auth_headers, at)
            r = await client.delete(f"/asset-manager/{at}/{created['id']}", headers=auth_headers)
            assert r.status_code in (200, 204), f"delete {at}: {r.text}"

    async def test_restore_after_delete(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            created = await self._create(client, auth_headers, at)
            await client.delete(f"/asset-manager/{at}/{created['id']}", headers=auth_headers)
            r = await client.post(f"/asset-manager/{at}/{created['id']}/restore", headers=auth_headers)
            assert r.status_code in (200, 201), f"restore {at}: {r.text}"
            assert r.json().get("is_deleted") is False

    async def test_deleted_not_in_default_list(self, client: AsyncClient, auth_headers: dict):
        for at in ASSET_TYPES:
            created = await self._create(client, auth_headers, at)
            await client.delete(f"/asset-manager/{at}/{created['id']}", headers=auth_headers)
            r = await client.get(f"/asset-manager/{at}", headers=auth_headers)
            ids = [item["id"] for item in r.json().get("items", r.json() if isinstance(r.json(), list) else [])]
            assert created["id"] not in ids


class TestAssetManagerBulk:
    async def _create_multiple(self, client, headers, asset_type, count=3):
        ids = []
        for i in range(count):
            payload = {**_CREATE_PAYLOAD[asset_type], "name": f"Bulk {asset_type} {i}"}
            r = await client.post(f"/asset-manager/{asset_type}", headers=headers, json=payload)
            assert r.status_code in (200, 201)
            ids.append(r.json()["id"])
        return ids

    async def test_bulk_delete(self, client: AsyncClient, auth_headers: dict):
        at = "background"
        ids = await self._create_multiple(client, auth_headers, at)
        r = await client.post(f"/asset-manager/{at}/bulk-delete", headers=auth_headers, json={"ids": ids})
        assert r.status_code == 200

    async def test_bulk_restore(self, client: AsyncClient, auth_headers: dict):
        at = "prop"
        ids = await self._create_multiple(client, auth_headers, at)
        await client.post(f"/asset-manager/{at}/bulk-delete", headers=auth_headers, json={"ids": ids})
        r = await client.post(f"/asset-manager/{at}/bulk-restore", headers=auth_headers, json={"ids": ids})
        assert r.status_code == 200

    async def test_bulk_update(self, client: AsyncClient, auth_headers: dict):
        at = "audio"
        ids = await self._create_multiple(client, auth_headers, at)
        r = await client.post(f"/asset-manager/{at}/bulk-update", headers=auth_headers, json={
            "ids": ids, "updates": {"category": "music", "tags": ["updated"]}
        })
        assert r.status_code == 200


class TestAssetManagerVersions:
    async def test_create_and_list_versions(self, client: AsyncClient, auth_headers: dict):
        # Create a background
        r = await client.post("/asset-manager/background", headers=auth_headers, json={
            "name": "Versioned BG", "category": "outdoor"
        })
        assert r.status_code in (200, 201)
        asset_id = r.json()["id"]

        # Create a version snapshot
        r = await client.post(f"/asset-manager/versions/background/{asset_id}", headers=auth_headers, json={
            "note": "Initial version"
        })
        assert r.status_code in (200, 201)

        # List versions — returns paginated {"items": [...], "total": ...}
        r = await client.get(f"/asset-manager/versions/background/{asset_id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        versions = body.get("items", body) if isinstance(body, dict) else body
        assert isinstance(versions, list)
        assert len(versions) >= 1

    async def test_restore_version(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/asset-manager/background", headers=auth_headers, json={
            "name": "Restore Me", "category": "indoor"
        })
        asset_id = r.json()["id"]
        snap = await client.post(f"/asset-manager/versions/background/{asset_id}", headers=auth_headers, json={"note": "v1"})
        assert snap.status_code in (200, 201)
        version_number = snap.json().get("version_number", 1)
        r = await client.post(f"/asset-manager/versions/background/{asset_id}/{version_number}/restore", headers=auth_headers)
        assert r.status_code in (200, 201, 204)


class TestCharacterTemplateAssetManager:
    async def test_list_character_templates(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/asset-manager/character_template", headers=auth_headers)
        assert r.status_code == 200
