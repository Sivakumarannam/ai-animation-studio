"""Tests for project CRUD, story CRUD, scene CRUD, and character CRUD."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestProjects:
    async def test_list_projects_empty(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/projects", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        # Returns paginated: {"items": [], "total": 0, ...}
        assert "items" in body or isinstance(body, list)

    async def test_create_project(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/projects", headers=auth_headers, json={
            "title": "My Project",
            "description": "Desc",
            "plugin_id": "telugu_family_comedy",
        })
        assert r.status_code in (200, 201)
        body = r.json()
        assert body["title"] == "My Project"
        assert "id" in body

    async def test_create_project_missing_title(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/projects", headers=auth_headers, json={"plugin_id": "x"})
        assert r.status_code == 422

    async def test_create_project_missing_plugin(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/projects", headers=auth_headers, json={"title": "X"})
        assert r.status_code == 422

    async def test_get_project(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.get(f"/projects/{project['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == project["id"]

    async def test_update_project(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.patch(f"/projects/{project['id']}", headers=auth_headers, json={"title": "Updated"})
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

    async def test_delete_project(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/projects", headers=auth_headers, json={
            "title": "To Delete", "plugin_id": "telugu_family_comedy"
        })
        pid = r.json()["id"]
        r = await client.delete(f"/projects/{pid}", headers=auth_headers)
        assert r.status_code in (200, 204)

    async def test_get_project_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/projects/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert r.status_code == 404

    async def test_projects_require_auth(self, client: AsyncClient):
        r = await client.get("/projects")
        assert r.status_code in (401, 403)


class TestStories:
    async def test_list_stories(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.get(f"/projects/{project['id']}/stories", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body or isinstance(body, list)

    async def test_create_story(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/stories", headers=auth_headers, json={
            "title": "Test Story", "description": "A story"
        })
        assert r.status_code in (200, 201)
        body = r.json()
        assert body["title"] == "Test Story"

    async def test_get_story(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/stories", headers=auth_headers, json={"title": "S"})
        sid = r.json()["id"]
        r = await client.get(f"/stories/{sid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == sid

    async def test_update_story(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/stories", headers=auth_headers, json={"title": "Old"})
        sid = r.json()["id"]
        r = await client.patch(f"/stories/{sid}", headers=auth_headers, json={"title": "New"})
        assert r.status_code == 200
        assert r.json()["title"] == "New"

    async def test_delete_story(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/stories", headers=auth_headers, json={"title": "Del"})
        sid = r.json()["id"]
        r = await client.delete(f"/stories/{sid}", headers=auth_headers)
        assert r.status_code in (200, 204)


class TestScenes:
    async def _story(self, client, headers, project):
        r = await client.post(f"/projects/{project['id']}/stories", headers=headers, json={"title": "Story"})
        return r.json()["id"]

    async def test_list_scenes(self, client: AsyncClient, auth_headers: dict, project: dict):
        sid = await self._story(client, auth_headers, project)
        r = await client.get(f"/stories/{sid}/scenes", headers=auth_headers)
        assert r.status_code == 200

    async def test_create_scene(self, client: AsyncClient, auth_headers: dict, project: dict):
        sid = await self._story(client, auth_headers, project)
        r = await client.post(f"/stories/{sid}/scenes", headers=auth_headers, json={
            "scene_number": 1, "title": "Scene 1"
        })
        assert r.status_code in (200, 201)
        assert r.json()["title"] == "Scene 1"

    async def test_update_scene(self, client: AsyncClient, auth_headers: dict, project: dict):
        sid = await self._story(client, auth_headers, project)
        r = await client.post(f"/stories/{sid}/scenes", headers=auth_headers, json={"scene_number": 1, "title": "A"})
        scid = r.json()["id"]
        r = await client.patch(f"/scenes/{scid}", headers=auth_headers, json={"title": "B"})
        assert r.status_code == 200
        assert r.json()["title"] == "B"

    async def test_delete_scene(self, client: AsyncClient, auth_headers: dict, project: dict):
        sid = await self._story(client, auth_headers, project)
        r = await client.post(f"/stories/{sid}/scenes", headers=auth_headers, json={"scene_number": 1, "title": "Del"})
        scid = r.json()["id"]
        r = await client.delete(f"/scenes/{scid}", headers=auth_headers)
        assert r.status_code in (200, 204)


class TestCharacters:
    async def test_list_characters(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.get(f"/projects/{project['id']}/characters", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body or isinstance(body, list)

    async def test_create_character(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/characters", headers=auth_headers, json={
            "name": "Hero", "description": "Main character"
        })
        assert r.status_code in (200, 201)
        assert r.json()["name"] == "Hero"

    async def test_get_character(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/characters", headers=auth_headers, json={"name": "H"})
        cid = r.json()["id"]
        r = await client.get(f"/characters/{cid}", headers=auth_headers)
        assert r.status_code == 200

    async def test_update_character(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/characters", headers=auth_headers, json={"name": "Old"})
        cid = r.json()["id"]
        r = await client.patch(f"/characters/{cid}", headers=auth_headers, json={"name": "New", "asset_data": {"color": "red"}})
        assert r.status_code == 200

    async def test_delete_character(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(f"/projects/{project['id']}/characters", headers=auth_headers, json={"name": "Del"})
        cid = r.json()["id"]
        r = await client.delete(f"/characters/{cid}", headers=auth_headers)
        assert r.status_code in (200, 204)
