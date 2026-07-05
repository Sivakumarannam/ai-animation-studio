"""Tests for Phase 3 — Story Intelligence: worlds, seasons, episodes, scenes,
ideas (CRUD, not LLM-generation), memory, jobs, and stats.

LLM-backed generation endpoints (idea generation, full pipeline dispatch,
episode generation) require a reachable Ollama provider and are intentionally
NOT exercised here — they are integration points, not pure CRUD, and the dev
sandbox has no LLM service running. Everything else is fully covered.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture()
async def world(client: AsyncClient, auth_headers: dict, project: dict) -> dict:
    r = await client.post(
        f"/si/projects/{project['id']}/worlds",
        headers=auth_headers,
        json={"name": "Test World", "description": "A world for tests"},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def season(client: AsyncClient, auth_headers: dict, world: dict) -> dict:
    r = await client.post(
        f"/si/worlds/{world['id']}/seasons",
        headers=auth_headers,
        json={"title": "Season 1", "episode_count": 5},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def episode(client: AsyncClient, auth_headers: dict, season: dict) -> dict:
    r = await client.post(
        f"/si/seasons/{season['id']}/episodes",
        headers=auth_headers,
        json={"title": "Episode 1", "synopsis": "A test episode"},
    )
    assert r.status_code == 201, r.text
    return r.json()


class TestWorlds:
    async def test_create_world(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/worlds",
            headers=auth_headers,
            json={"name": "My World", "description": "desc"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "My World"
        assert body["project_id"] == project["id"]

    async def test_list_worlds(self, client: AsyncClient, auth_headers: dict, project: dict, world: dict):
        r = await client.get(f"/si/projects/{project['id']}/worlds", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["meta"]["total"] >= 1
        assert any(w["id"] == world["id"] for w in body["items"])

    async def test_get_world(self, client: AsyncClient, auth_headers: dict, world: dict):
        r = await client.get(f"/si/worlds/{world['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == world["id"]

    async def test_get_world_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/si/worlds/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_world(self, client: AsyncClient, auth_headers: dict, world: dict):
        r = await client.patch(
            f"/si/worlds/{world['id']}", headers=auth_headers, json={"name": "Renamed World"}
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed World"

    async def test_delete_world(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/worlds",
            headers=auth_headers,
            json={"name": "To Delete"},
        )
        wid = r.json()["id"]
        r = await client.delete(f"/si/worlds/{wid}", headers=auth_headers)
        assert r.status_code == 204
        assert r.content == b""
        r = await client.get(f"/si/worlds/{wid}", headers=auth_headers)
        assert r.status_code == 404

    async def test_worlds_require_auth(self, client: AsyncClient, project: dict):
        r = await client.get(f"/si/projects/{project['id']}/worlds")
        assert r.status_code in (401, 403)


class TestSeasons:
    async def test_create_season(self, client: AsyncClient, auth_headers: dict, world: dict):
        r = await client.post(
            f"/si/worlds/{world['id']}/seasons",
            headers=auth_headers,
            json={"title": "Season A", "episode_count": 10},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Season A"
        assert body["world_id"] == world["id"]
        assert body["project_id"] == world["project_id"]

    async def test_list_seasons(self, client: AsyncClient, auth_headers: dict, world: dict, season: dict):
        r = await client.get(f"/si/worlds/{world['id']}/seasons", headers=auth_headers)
        assert r.status_code == 200
        assert any(s["id"] == season["id"] for s in r.json()["items"])

    async def test_get_season_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/si/seasons/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_season(self, client: AsyncClient, auth_headers: dict, season: dict):
        r = await client.patch(
            f"/si/seasons/{season['id']}", headers=auth_headers, json={"status": "in_progress"}
        )
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    async def test_delete_season(self, client: AsyncClient, auth_headers: dict, world: dict):
        r = await client.post(
            f"/si/worlds/{world['id']}/seasons", headers=auth_headers, json={"title": "Delete Me"}
        )
        sid = r.json()["id"]
        r = await client.delete(f"/si/seasons/{sid}", headers=auth_headers)
        assert r.status_code == 204


class TestEpisodes:
    async def test_create_episode(self, client: AsyncClient, auth_headers: dict, season: dict):
        r = await client.post(
            f"/si/seasons/{season['id']}/episodes",
            headers=auth_headers,
            json={"title": "Ep A", "synopsis": "synopsis"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Ep A"
        assert body["season_id"] == season["id"]

    async def test_list_episodes(self, client: AsyncClient, auth_headers: dict, season: dict, episode: dict):
        r = await client.get(f"/si/seasons/{season['id']}/episodes", headers=auth_headers)
        assert r.status_code == 200
        assert any(e["id"] == episode["id"] for e in r.json()["items"])

    async def test_get_episode_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/si/episodes/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_episode(self, client: AsyncClient, auth_headers: dict, episode: dict):
        r = await client.patch(
            f"/si/episodes/{episode['id']}", headers=auth_headers, json={"title": "Renamed Ep"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Renamed Ep"

    async def test_get_episode_evaluation_none(self, client: AsyncClient, auth_headers: dict, episode: dict):
        r = await client.get(f"/si/episodes/{episode['id']}/evaluation", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() is None

    async def test_get_episode_versions_empty(self, client: AsyncClient, auth_headers: dict, episode: dict):
        r = await client.get(f"/si/episodes/{episode['id']}/versions", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    async def test_delete_episode(self, client: AsyncClient, auth_headers: dict, season: dict):
        r = await client.post(
            f"/si/seasons/{season['id']}/episodes", headers=auth_headers, json={"title": "Delete Ep"}
        )
        eid = r.json()["id"]
        r = await client.delete(f"/si/episodes/{eid}", headers=auth_headers)
        assert r.status_code == 204


class TestStoryScenes:
    async def test_create_scene(self, client: AsyncClient, auth_headers: dict, episode: dict):
        r = await client.post(
            f"/si/episodes/{episode['id']}/scenes",
            headers=auth_headers,
            json={"scene_number": 1, "scene_goal": "Opening scene"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["episode_id"] == episode["id"]

    async def test_list_scenes(self, client: AsyncClient, auth_headers: dict, episode: dict):
        await client.post(
            f"/si/episodes/{episode['id']}/scenes",
            headers=auth_headers,
            json={"scene_number": 1, "scene_goal": "Scene"},
        )
        r = await client.get(f"/si/episodes/{episode['id']}/scenes", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

    async def test_get_scene_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/si/scenes/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_and_delete_scene(self, client: AsyncClient, auth_headers: dict, episode: dict):
        r = await client.post(
            f"/si/episodes/{episode['id']}/scenes",
            headers=auth_headers,
            json={"scene_number": 2, "scene_goal": "Another scene"},
        )
        scene_id = r.json()["id"]
        r = await client.patch(
            f"/si/scenes/{scene_id}", headers=auth_headers, json={"scene_goal": "Updated"}
        )
        assert r.status_code == 200
        assert r.json()["scene_goal"] == "Updated"
        r = await client.delete(f"/si/scenes/{scene_id}", headers=auth_headers)
        assert r.status_code == 204


class TestStoryIdeas:
    async def test_create_idea_manual(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas",
            headers=auth_headers,
            json={"title": "A Manual Idea", "logline": "Something happens", "genre": "comedy"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "A Manual Idea"
        assert body["project_id"] == project["id"]

    async def test_list_ideas(self, client: AsyncClient, auth_headers: dict, project: dict):
        await client.post(
            f"/si/projects/{project['id']}/ideas",
            headers=auth_headers,
            json={"title": "Idea X", "logline": "Log", "genre": "drama"},
        )
        r = await client.get(f"/si/projects/{project['id']}/ideas", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

    async def test_update_idea_status(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas",
            headers=auth_headers,
            json={"title": "Idea Y", "logline": "Log", "genre": "drama"},
        )
        idea_id = r.json()["id"]
        r = await client.patch(
            f"/si/ideas/{idea_id}", headers=auth_headers, json={"status": "approved"}
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    async def test_delete_idea(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas",
            headers=auth_headers,
            json={"title": "Idea Z", "logline": "Log", "genre": "drama"},
        )
        idea_id = r.json()["id"]
        r = await client.delete(f"/si/ideas/{idea_id}", headers=auth_headers)
        assert r.status_code == 204


class TestStoryMemory:
    async def test_store_and_list_memory(self, client: AsyncClient, auth_headers: dict, world: dict):
        r = await client.post(
            f"/si/worlds/{world['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "fact", "key": "hero_name", "value": {"name": "Ravi"}},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["world_id"] == world["id"]
        assert body["key"] == "hero_name"

        r = await client.get(f"/si/worlds/{world['id']}/memory", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

    async def test_list_memory_filtered_by_type(self, client: AsyncClient, auth_headers: dict, world: dict):
        await client.post(
            f"/si/worlds/{world['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "rule", "key": "no_violence", "value": {"ok": True}},
        )
        r = await client.get(
            f"/si/worlds/{world['id']}/memory?memory_type=rule", headers=auth_headers
        )
        assert r.status_code == 200
        assert all(m["memory_type"] == "rule" for m in r.json()["items"])


class TestGenerationJobs:
    async def test_list_jobs_empty(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.get(f"/si/projects/{project['id']}/jobs", headers=auth_headers)
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_get_job_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/si/jobs/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404


class TestStats:
    async def test_stats_shape(self, client: AsyncClient, auth_headers: dict, project: dict, world: dict, season: dict):
        r = await client.get(f"/si/projects/{project['id']}/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        for key in ("worlds", "seasons", "episodes", "scenes", "ideas", "memories", "jobs_by_status", "avg_story_score"):
            assert key in body
        assert body["worlds"] >= 1
        assert body["seasons"] >= 1

    async def test_stats_require_auth(self, client: AsyncClient, project: dict):
        r = await client.get(f"/si/projects/{project['id']}/stats")
        assert r.status_code in (401, 403)
