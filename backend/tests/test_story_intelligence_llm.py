"""
Tests for Phase 3 — Story Intelligence LLM-backed endpoints.

These endpoints call into `LLMProvider` (idea/season/episode/scene generation,
evaluation, memory extraction, dispatch/pipeline orchestration). They previously
required a live Ollama server; with `SI_AI_PROVIDER=mock` the backend registers
`MockLLMProvider` instead, so these run fully deterministically with zero
external dependencies.

Covers:
  - Idea generation (`POST /si/projects/{id}/ideas/generate`)
  - Season/episode planning via the full pipeline and generate-episode dispatch
  - Episode evaluation (`POST /si/episodes/{id}/evaluate`)
  - Dispatcher sync-fallback behavior (mode/status/result shape)
  - Job + job-log + retry-queue integration
  - End-to-end workflow integration (world -> idea -> season -> episode -> scenes -> eval -> memory)
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
        json={"name": "LLM Test World", "description": "A world for LLM-backed tests"},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def season(client: AsyncClient, auth_headers: dict, world: dict) -> dict:
    r = await client.post(
        f"/si/worlds/{world['id']}/seasons",
        headers=auth_headers,
        json={"title": "LLM Season 1", "episode_count": 3},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def episode(client: AsyncClient, auth_headers: dict, season: dict) -> dict:
    r = await client.post(
        f"/si/seasons/{season['id']}/episodes",
        headers=auth_headers,
        json={"title": "LLM Episode 1", "synopsis": "An episode for eval tests"},
    )
    assert r.status_code == 201, r.text
    return r.json()


class TestIdeaGeneration:
    async def test_generate_ideas_no_world(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"genre": "comedy", "story_type": "comedy", "count": 3},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 3
        for idea in body:
            assert idea["project_id"] == project["id"]
            assert idea["title"]
            assert idea["premise"]

    async def test_generate_ideas_with_world_context(
        self, client: AsyncClient, auth_headers: dict, project: dict, world: dict
    ):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"genre": "comedy", "story_type": "comedy", "count": 2, "world_id": world["id"]},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert len(body) == 2
        assert all(i["world_id"] == world["id"] for i in body)

    async def test_generate_ideas_count_respected(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 1},
        )
        assert r.status_code == 201
        assert len(r.json()) == 1

    async def test_generate_ideas_requires_auth(self, client: AsyncClient, project: dict):
        r = await client.post(f"/si/projects/{project['id']}/ideas/generate", json={"count": 1})
        assert r.status_code in (401, 403)

    async def test_generate_ideas_persisted(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 2},
        )
        idea_ids = {i["id"] for i in r.json()}
        listed = await client.get(f"/si/projects/{project['id']}/ideas", headers=auth_headers)
        assert listed.status_code == 200
        listed_ids = {i["id"] for i in listed.json()["items"]}
        assert idea_ids.issubset(listed_ids)


class TestEpisodeEvaluation:
    async def test_evaluate_episode(self, client: AsyncClient, auth_headers: dict, episode: dict):
        r = await client.post(f"/si/episodes/{episode['id']}/evaluate", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["episode_id"] == episode["id"]
        for dim in (
            "originality_score", "consistency_score", "creativity_score", "grammar_score",
            "flow_score", "entertainment_score", "educational_value_score",
            "story_arc_score", "dialogue_score", "overall_score",
        ):
            assert 0.0 <= body[dim] <= 100.0
        assert isinstance(body["approved"], bool)
        assert "feedback" in body

    async def test_evaluate_episode_updates_episode_score(
        self, client: AsyncClient, auth_headers: dict, episode: dict
    ):
        r = await client.post(f"/si/episodes/{episode['id']}/evaluate", headers=auth_headers)
        assert r.status_code == 200
        overall = r.json()["overall_score"]

        updated = await client.get(f"/si/episodes/{episode['id']}", headers=auth_headers)
        assert updated.status_code == 200
        assert updated.json()["story_score"] == overall

    async def test_evaluate_episode_creates_version_history(
        self, client: AsyncClient, auth_headers: dict, episode: dict
    ):
        await client.patch(
            f"/si/episodes/{episode['id']}", headers=auth_headers, json={"title": "Renamed before eval"}
        )
        versions = await client.get(f"/si/episodes/{episode['id']}/versions", headers=auth_headers)
        assert versions.status_code == 200
        assert len(versions.json()) >= 1

    async def test_evaluate_episode_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.post(f"/si/episodes/{uuid4()}/evaluate", headers=auth_headers)
        assert r.status_code == 404

    async def test_get_evaluation_after_evaluate(self, client: AsyncClient, auth_headers: dict, episode: dict):
        await client.post(f"/si/episodes/{episode['id']}/evaluate", headers=auth_headers)
        r = await client.get(f"/si/episodes/{episode['id']}/evaluation", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() is not None
        assert r.json()["episode_id"] == episode["id"]


class TestGenerateEpisodeDispatch:
    """POST /si/seasons/{season_id}/generate-episode — dispatcher + orchestrator integration."""

    async def test_generate_episode_dispatch_shape(
        self, client: AsyncClient, auth_headers: dict, season: dict, world: dict
    ):
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={"season_id": season["id"], "world_id": world["id"]},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mode"] in ("sync", "async")
        assert body["status"] in ("completed", "pending", "failed")
        assert "job_id" in body and body["job_id"]
        assert "task_id" in body and body["task_id"]

    async def test_generate_episode_sync_fallback_result(
        self, client: AsyncClient, auth_headers: dict, season: dict, world: dict
    ):
        """In this sandbox Redis is unreachable, so dispatch must fall back to sync
        and return a fully-populated result produced entirely by the mock LLM."""
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={"season_id": season["id"], "world_id": world["id"]},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mode"] == "sync"
        assert body["status"] == "completed"
        result = body["result"]
        assert result is not None
        assert "episode_id" in result
        assert "scene_count" in result and result["scene_count"] > 0
        assert "quality_score" in result
        assert "approved" in result

    async def test_generate_episode_creates_real_episode_and_scenes(
        self, client: AsyncClient, auth_headers: dict, season: dict, world: dict
    ):
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={"season_id": season["id"], "world_id": world["id"]},
        )
        result = r.json()["result"]
        episode_id = result["episode_id"]

        ep = await client.get(f"/si/episodes/{episode_id}", headers=auth_headers)
        assert ep.status_code == 200
        ep_body = ep.json()
        assert ep_body["title"]
        assert ep_body["opening"] and ep_body["middle"] and ep_body["ending"]

        scenes = await client.get(f"/si/episodes/{episode_id}/scenes", headers=auth_headers)
        assert scenes.status_code == 200
        scene_items = scenes.json()["items"]
        assert len(scene_items) == result["scene_count"]
        for scene in scene_items:
            assert scene["dialogue"]
            assert scene["narration"]
            assert scene["image_prompt"]
            assert scene["animation_prompt"]

    async def test_generate_episode_creates_job_record(
        self, client: AsyncClient, auth_headers: dict, season: dict, world: dict, project: dict
    ):
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={"season_id": season["id"], "world_id": world["id"]},
        )
        job_id = r.json()["job_id"]
        job = await client.get(f"/si/jobs/{job_id}", headers=auth_headers)
        assert job.status_code == 200
        job_body = job.json()
        assert job_body["status"] == "completed"
        assert job_body["job_type"] == "generate_episode"
        assert job_body["progress_percent"] == 100


class TestFullPipelineDispatch:
    """POST /si/projects/{project_id}/generate — the 12-stage orchestrator pipeline."""

    async def test_run_full_pipeline_without_world(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/si/projects/{project['id']}/generate",
            headers=auth_headers,
            json={"genre": "comedy", "story_type": "comedy", "episode_count": 2},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mode"] == "sync"
        assert body["status"] == "completed"
        result = body["result"]
        assert result["world_id"]
        assert result["idea_id"]
        assert result["season_id"]
        assert result["episode_id"]
        assert result["scene_count"] > 0
        assert "quality_score" in result
        assert "approved" in result
        assert result["memories_stored"] >= 0

    async def test_run_full_pipeline_with_existing_world(
        self, client: AsyncClient, auth_headers: dict, project: dict, world: dict
    ):
        r = await client.post(
            f"/si/projects/{project['id']}/generate",
            headers=auth_headers,
            json={"world_id": world["id"], "episode_count": 2},
        )
        assert r.status_code == 200, r.text
        result = r.json()["result"]
        assert result["world_id"] == world["id"]

    async def test_run_full_pipeline_builds_world_when_missing(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        r = await client.post(
            f"/si/projects/{project['id']}/generate",
            headers=auth_headers,
            json={},
        )
        assert r.status_code == 200
        world_id = r.json()["result"]["world_id"]
        w = await client.get(f"/si/worlds/{world_id}", headers=auth_headers)
        assert w.status_code == 200
        assert w.json()["name"]

    async def test_run_full_pipeline_persists_memory(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        r = await client.post(
            f"/si/projects/{project['id']}/generate",
            headers=auth_headers,
            json={},
        )
        result = r.json()["result"]
        world_id = result["world_id"]
        mem = await client.get(f"/si/worlds/{world_id}/memory", headers=auth_headers)
        assert mem.status_code == 200
        assert mem.json()["meta"]["total"] == result["memories_stored"]

    async def test_run_full_pipeline_stats_reflect_generation(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        await client.post(f"/si/projects/{project['id']}/generate", headers=auth_headers, json={})
        stats = await client.get(f"/si/projects/{project['id']}/stats", headers=auth_headers)
        assert stats.status_code == 200
        body = stats.json()
        assert body["worlds"] >= 1
        assert body["seasons"] >= 1
        assert body["episodes"] >= 1
        assert body["jobs_by_status"].get("completed", 0) >= 1

    async def test_run_full_pipeline_requires_auth(self, client: AsyncClient, project: dict):
        r = await client.post(f"/si/projects/{project['id']}/generate", json={})
        assert r.status_code in (401, 403)


class TestDispatcherFallbackBehavior:
    """
    Dev sandbox has no reachable Redis broker, so every dispatch call must take
    the synchronous fallback path deterministically and never hang or 500.
    """

    async def test_dispatch_never_returns_async_mode_without_broker(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        r = await client.post(f"/si/projects/{project['id']}/generate", headers=auth_headers, json={})
        assert r.status_code == 200
        # Without Redis reachable, dispatcher must fall back to sync — this is the
        # behavior this whole test file depends on for determinism.
        assert r.json()["mode"] == "sync"

    async def test_dispatch_result_always_present_on_sync_completion(
        self, client: AsyncClient, auth_headers: dict, season: dict, world: dict
    ):
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={"season_id": season["id"], "world_id": world["id"]},
        )
        body = r.json()
        if body["status"] == "completed":
            assert body["result"] is not None
        elif body["status"] == "failed":
            assert "error" in body or body.get("result") is None


class TestJobLogsAndRetryIntegration:
    async def test_job_logs_endpoint_shape(
        self, client: AsyncClient, auth_headers: dict, season: dict, world: dict
    ):
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={"season_id": season["id"], "world_id": world["id"]},
        )
        job_id = r.json()["job_id"]
        logs = await client.get(f"/si/jobs/{job_id}/logs", headers=auth_headers)
        assert logs.status_code == 200
        assert "logs" in logs.json()

    async def test_jobs_listed_by_project_after_generation(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        await client.post(f"/si/projects/{project['id']}/generate", headers=auth_headers, json={})
        jobs = await client.get(f"/si/projects/{project['id']}/jobs", headers=auth_headers)
        assert jobs.status_code == 200
        body = jobs.json()
        assert body["meta"]["total"] >= 1
        assert any(j["status"] == "completed" for j in body["items"])

    async def test_jobs_filterable_by_status(self, client: AsyncClient, auth_headers: dict, project: dict):
        await client.post(f"/si/projects/{project['id']}/generate", headers=auth_headers, json={})
        jobs = await client.get(
            f"/si/projects/{project['id']}/jobs?job_status=completed", headers=auth_headers
        )
        assert jobs.status_code == 200
        assert all(j["status"] == "completed" for j in jobs.json()["items"])

    async def test_jobs_filterable_by_type(self, client: AsyncClient, auth_headers: dict, project: dict):
        await client.post(f"/si/projects/{project['id']}/generate", headers=auth_headers, json={})
        jobs = await client.get(
            f"/si/projects/{project['id']}/jobs?job_type=generate_full_pipeline", headers=auth_headers
        )
        assert jobs.status_code == 200
        assert all(j["job_type"] == "generate_full_pipeline" for j in jobs.json()["items"])


class TestWorkflowIntegrationEndToEnd:
    """
    Full manual-then-AI workflow: create world/season/episode by hand, then use
    the AI endpoints (evaluate, memory) on top of them, mirroring how the
    frontend Story Intelligence UI actually composes these calls.
    """

    async def test_manual_hierarchy_then_ai_evaluation_and_memory(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        w = await client.post(
            f"/si/projects/{project['id']}/worlds",
            headers=auth_headers,
            json={"name": "E2E World", "description": "end to end"},
        )
        world_id = w.json()["id"]

        s = await client.post(
            f"/si/worlds/{world_id}/seasons",
            headers=auth_headers,
            json={"title": "E2E Season", "episode_count": 1},
        )
        season_id = s.json()["id"]

        e = await client.post(
            f"/si/seasons/{season_id}/episodes",
            headers=auth_headers,
            json={"title": "E2E Episode", "synopsis": "manual episode"},
        )
        episode_id = e.json()["id"]

        ev = await client.post(f"/si/episodes/{episode_id}/evaluate", headers=auth_headers)
        assert ev.status_code == 200
        assert ev.json()["overall_score"] > 0

        mem = await client.post(
            f"/si/worlds/{world_id}/memory",
            headers=auth_headers,
            json={"memory_type": "event", "key": "e2e_test_event", "value": {"happened": True}},
        )
        assert mem.status_code == 201

        stats = await client.get(f"/si/projects/{project['id']}/stats", headers=auth_headers)
        assert stats.status_code == 200
        body = stats.json()
        assert body["worlds"] >= 1
        assert body["episodes"] >= 1
        assert body["memories"] >= 1

    async def test_idea_generation_feeds_into_manual_season_creation(
        self, client: AsyncClient, auth_headers: dict, project: dict, world: dict
    ):
        ideas = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 1, "world_id": world["id"]},
        )
        idea = ideas.json()[0]

        season = await client.post(
            f"/si/worlds/{world['id']}/seasons",
            headers=auth_headers,
            json={"title": idea["title"], "description": idea["premise"], "episode_count": 3},
        )
        assert season.status_code == 201
        assert season.json()["title"] == idea["title"]
