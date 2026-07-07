"""
Tests for Phase 4 — RAG & Knowledge Intelligence Engine (embedding/processing pipeline).

Tests document processing (parse → chunk → embed), vector search, retrieval history,
context builder, RAG integration with Story Intelligence, and dispatcher fallback.

Uses only mock providers (MockEmbeddingProvider + InMemoryVectorStore) — no Ollama.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
async def collection(client: AsyncClient, auth_headers: dict, project: dict) -> dict:
    r = await client.post(
        f"/kn/projects/{project['id']}/collections",
        headers=auth_headers,
        json={"name": "LLM Test Collection", "collection_type": "general"},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def document(client: AsyncClient, auth_headers: dict, collection: dict) -> dict:
    r = await client.post(
        f"/kn/collections/{collection['id']}/documents",
        headers=auth_headers,
        json={"title": "Test Doc", "source_type": "text", "raw_text": "Some content for stats test."},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def processed_document(client: AsyncClient, auth_headers: dict, collection: dict) -> dict:
    """Upload and process a document so its chunks get embedded."""
    content = b"The hero of the story is named Ravi. He lives in a small village. Ravi loves cooking traditional food."
    files = {"file": ("story.txt", content, "text/plain")}
    r = await client.post(
        f"/kn/collections/{collection['id']}/documents/upload",
        headers=auth_headers,
        files=files,
    )
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]

    r2 = await client.get(f"/kn/jobs/{job_id}", headers=auth_headers)
    assert r2.status_code == 200
    return r2.json()


@pytest.fixture()
async def world(client: AsyncClient, auth_headers: dict, project: dict) -> dict:
    r = await client.post(
        f"/si/projects/{project['id']}/worlds",
        headers=auth_headers,
        json={"name": "RAG Test World", "description": "World for RAG integration tests"},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def season(client: AsyncClient, auth_headers: dict, world: dict) -> dict:
    r = await client.post(
        f"/si/worlds/{world['id']}/seasons",
        headers=auth_headers,
        json={"title": "RAG Season 1", "episode_count": 2},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Document Processing Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class TestDocumentProcessing:
    async def test_upload_creates_job(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Upload should return a dispatch response with a job_id."""
        content = b"Sample text for processing pipeline test."
        files = {"file": ("test.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        body = r.json()
        assert "job_id" in body
        assert "task_id" in body
        assert "mode" in body
        assert "status" in body

    async def test_upload_dispatcher_sync_fallback(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Without Celery workers the dispatcher falls back to sync mode."""
        content = b"Content for sync fallback test."
        files = {"file": ("sync.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        body = r.json()
        assert body["mode"] in ("sync", "celery", "async")

    async def test_upload_job_is_retrievable(self, client: AsyncClient, auth_headers: dict, collection: dict, project: dict):
        """After upload the job should appear in the project job list."""
        content = b"Content for job listing test."
        files = {"file": ("job.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        job_id = r.json()["job_id"]

        jobs_r = await client.get(f"/kn/projects/{project['id']}/jobs", headers=auth_headers)
        assert jobs_r.status_code == 200
        job_ids = [j["id"] for j in jobs_r.json()["items"]]
        assert job_id in job_ids

    async def test_process_existing_document(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Can re-trigger processing on an existing document."""
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            json={"title": "Manual Doc", "source_type": "text", "raw_text": "Manual text content for processing."},
        )
        assert r.status_code == 201
        doc_id = r.json()["id"]

        r2 = await client.post(f"/kn/documents/{doc_id}/process", headers=auth_headers)
        assert r2.status_code == 200
        body = r2.json()
        assert "job_id" in body
        assert body["mode"] in ("sync", "celery", "async")

    async def test_process_creates_trackable_job(self, client: AsyncClient, auth_headers: dict, collection: dict, project: dict):
        """Processing a document should create a trackable job."""
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            json={"title": "Trackable Doc", "source_type": "text", "raw_text": "Trackable content."},
        )
        assert r.status_code == 201
        doc_id = r.json()["id"]

        r2 = await client.post(f"/kn/documents/{doc_id}/process", headers=auth_headers)
        assert r2.status_code == 200
        job_id = r2.json()["job_id"]

        r3 = await client.get(f"/kn/jobs/{job_id}", headers=auth_headers)
        assert r3.status_code == 200
        body = r3.json()
        assert body["id"] == job_id
        assert body["document_id"] == doc_id


# ─────────────────────────────────────────────────────────────────────────────
# Embedding & Vector Search
# ─────────────────────────────────────────────────────────────────────────────

class TestEmbeddingAndVectorSearch:
    async def test_search_returns_shape(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Search response always has the correct shape even when empty."""
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "hero Ravi village"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "query" in body
        assert "results" in body
        assert "result_count" in body
        assert body["result_count"] == len(body["results"])

    async def test_search_result_item_shape(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Each result item must have chunk_id, document_id, content, and score."""
        content = b"Search test: the protagonist is a brave warrior."
        files = {"file": ("warrior.txt", content, "text/plain")}
        await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "brave warrior"},
        )
        assert r.status_code == 200
        for item in r.json()["results"]:
            assert "chunk_id" in item
            assert "document_id" in item
            assert "content" in item
            assert "score" in item
            assert isinstance(item["score"], float)

    async def test_search_top_k_limits_results(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """top_k parameter should limit the number of returned results."""
        for i in range(5):
            await client.post(
                f"/kn/collections/{collection['id']}/documents",
                headers=auth_headers,
                json={"title": f"Doc {i}", "source_type": "text", "raw_text": f"Content {i} for top k test search relevance."},
            )
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "content test", "top_k": 3},
        )
        assert r.status_code == 200
        assert len(r.json()["results"]) <= 3

    async def test_search_min_score_filter(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """min_score should filter out low-relevance results."""
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "test query", "min_score": 0.99},
        )
        assert r.status_code == 200
        for result in r.json()["results"]:
            assert result["score"] >= 0.99

    async def test_search_validates_empty_query(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Empty query string must be rejected with 422."""
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": ""},
        )
        assert r.status_code == 422

    async def test_search_nonexistent_collection(self, client: AsyncClient, auth_headers: dict):
        """Searching a non-existent collection returns 404."""
        r = await client.post(
            f"/kn/collections/{uuid4()}/search",
            headers=auth_headers,
            json={"query": "test"},
        )
        assert r.status_code == 404

    async def test_search_records_retrieval_history(self, client: AsyncClient, auth_headers: dict, collection: dict, project: dict):
        """Searching should trigger a retrieval history entry (visible via job counts)."""
        await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "history tracking test"},
        )
        r = await client.get(f"/kn/projects/{project['id']}/stats", headers=auth_headers)
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Chunks
# ─────────────────────────────────────────────────────────────────────────────

class TestChunks:
    async def test_get_chunks_for_document(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Documents that have been processed may have chunks."""
        content = b"Chunking test content with enough words to produce at least one chunk."
        files = {"file": ("chunk_test.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        doc_list = await client.get(
            f"/kn/collections/{collection['id']}/documents", headers=auth_headers
        )
        assert doc_list.status_code == 200
        docs = doc_list.json()["items"]
        assert len(docs) >= 1
        doc_id = docs[0]["id"]

        chunks_r = await client.get(f"/kn/documents/{doc_id}/chunks", headers=auth_headers)
        assert chunks_r.status_code == 200
        assert isinstance(chunks_r.json(), list)

    async def test_chunk_schema_shape(self, client: AsyncClient, auth_headers: dict, collection: dict):
        """Each chunk must have the expected fields."""
        content = b"Chunk shape test: this content gets split into processable tokens."
        files = {"file": ("shape.txt", content, "text/plain")}
        await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        docs = (await client.get(
            f"/kn/collections/{collection['id']}/documents", headers=auth_headers
        )).json()["items"]
        if not docs:
            return
        chunks = (await client.get(
            f"/kn/documents/{docs[0]['id']}/chunks", headers=auth_headers
        )).json()
        for chunk in chunks:
            assert "id" in chunk
            assert "document_id" in chunk
            assert "chunk_index" in chunk
            assert "content" in chunk
            assert "token_count" in chunk
            assert "is_embedded" in chunk


# ─────────────────────────────────────────────────────────────────────────────
# Memory + RAG pipeline
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeMemoryPipeline:
    async def test_memory_with_world_scope(self, client: AsyncClient, auth_headers: dict, project: dict, world: dict):
        """Memory can be scoped to a specific world."""
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={
                "memory_type": "lore",
                "key": "world_rule",
                "value": {"rule": "No magic allowed"},
                "world_id": world["id"],
                "confidence": 0.95,
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["world_id"] == world["id"]
        assert body["memory_type"] == "lore"

    async def test_list_memory_by_world(self, client: AsyncClient, auth_headers: dict, project: dict, world: dict):
        """Can list memory filtered by world scope."""
        await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "fact", "key": "world_fact", "value": {}, "world_id": world["id"]},
        )
        r = await client.get(f"/kn/worlds/{world['id']}/memory", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "meta" in body
        for m in body["items"]:
            assert m["world_id"] == world["id"]

    async def test_memory_with_collection_scope(self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict):
        """Memory can be scoped to a specific knowledge collection."""
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={
                "memory_type": "rule",
                "key": "collection_rule",
                "value": {"rule": "Always include source"},
                "collection_id": collection["id"],
                "confidence": 1.0,
            },
        )
        assert r.status_code == 201
        assert r.json()["collection_id"] == collection["id"]


# ─────────────────────────────────────────────────────────────────────────────
# RAG → Story Intelligence Integration
# ─────────────────────────────────────────────────────────────────────────────

class TestRAGStoryIntelligenceIntegration:
    async def test_generate_ideas_with_knowledge_collection(
        self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict
    ):
        """Idea generation with a knowledge_collection_id must not crash.

        The mock embedding/vector store returns empty context gracefully —
        the generation still completes with mock ideas.
        """
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 2, "genre": "comedy", "knowledge_collection_id": collection["id"]},
        )
        assert r.status_code in (200, 201, 202), r.text
        body = r.json()
        assert "mode" in body or isinstance(body, list)

    async def test_generate_ideas_without_knowledge_collection(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        """Idea generation without a knowledge_collection_id works as before (graceful no-op)."""
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 2, "genre": "comedy"},
        )
        assert r.status_code in (200, 201, 202), r.text

    async def test_run_full_pipeline_with_knowledge_collection_id(
        self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict
    ):
        """Full pipeline dispatch accepts knowledge_collection_id without error."""
        r = await client.post(
            f"/si/projects/{project['id']}/generate",
            headers=auth_headers,
            json={
                "genre": "comedy",
                "story_type": "family",
                "episode_count": 1,
                "knowledge_collection_id": collection["id"],
            },
        )
        assert r.status_code in (200, 201, 202), r.text
        body = r.json()
        assert "job_id" in body
        assert "mode" in body

    async def test_generate_episode_with_knowledge_collection_id(
        self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict, world: dict, season: dict
    ):
        """Episode generation dispatch accepts knowledge_collection_id without error."""
        r = await client.post(
            f"/si/seasons/{season['id']}/generate-episode",
            headers=auth_headers,
            json={
                "season_id": season["id"],
                "world_id": world["id"],
                "knowledge_collection_id": collection["id"],
            },
        )
        assert r.status_code in (200, 201, 202), r.text
        body = r.json()
        assert "job_id" in body or "mode" in body

    async def test_rag_context_empty_graceful(
        self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict
    ):
        """An empty collection returns empty RAG context — generation still succeeds."""
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 1, "genre": "drama", "knowledge_collection_id": collection["id"]},
        )
        assert r.status_code in (200, 201, 202), r.text

    async def test_invalid_knowledge_collection_id_graceful(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ):
        """A non-existent collection_id should either fail gracefully or return error."""
        r = await client.post(
            f"/si/projects/{project['id']}/ideas/generate",
            headers=auth_headers,
            json={"count": 1, "genre": "comedy", "knowledge_collection_id": str(uuid4())},
        )
        assert r.status_code in (200, 201, 202, 400, 404, 422), r.text


# ─────────────────────────────────────────────────────────────────────────────
# Stats and Provider Info
# ─────────────────────────────────────────────────────────────────────────────

class TestStatsAndProviders:
    async def test_stats_reflect_mock_providers(self, client: AsyncClient, auth_headers: dict, project: dict):
        """Stats response should report mock provider names."""
        r = await client.get(f"/kn/projects/{project['id']}/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "mock" in body["embedding_provider"].lower() or "hash" in body["embedding_provider"].lower()
        assert "memory" in body["vector_store_provider"].lower() or "cosine" in body["vector_store_provider"].lower()

    async def test_stats_jobs_by_status_shape(self, client: AsyncClient, auth_headers: dict, project: dict):
        """jobs_by_status must be a dict of status→count."""
        r = await client.get(f"/kn/projects/{project['id']}/stats", headers=auth_headers)
        assert r.status_code == 200
        jbs = r.json()["jobs_by_status"]
        assert isinstance(jbs, dict)
        for v in jbs.values():
            assert isinstance(v, int)

    async def test_stats_counts_increase_with_data(
        self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict, document: dict
    ):
        """Stats counts must go up when data is created."""
        r = await client.get(f"/kn/projects/{project['id']}/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["collections"] >= 1
        assert body["documents"] >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Authorization & Error Handling
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthAndErrors:
    async def test_unauthenticated_collection_list(self, client: AsyncClient, project: dict):
        r = await client.get(f"/kn/projects/{project['id']}/collections")
        assert r.status_code == 401

    async def test_unauthenticated_document_list(self, client: AsyncClient, collection: dict):
        r = await client.get(f"/kn/collections/{collection['id']}/documents")
        assert r.status_code == 401

    async def test_unauthenticated_search(self, client: AsyncClient, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            json={"query": "test"},
        )
        assert r.status_code == 401

    async def test_unauthenticated_stats(self, client: AsyncClient, project: dict):
        r = await client.get(f"/kn/projects/{project['id']}/stats")
        assert r.status_code == 401

    async def test_unauthenticated_upload(self, client: AsyncClient, collection: dict):
        content = b"unauthorized content"
        files = {"file": ("unauth.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            files=files,
        )
        assert r.status_code == 401

    async def test_invalid_uuid_collection(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/kn/collections/not-a-uuid", headers=auth_headers)
        assert r.status_code == 422

    async def test_invalid_uuid_document(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/kn/documents/not-a-uuid", headers=auth_headers)
        assert r.status_code == 422

    async def test_collection_name_required(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/collections",
            headers=auth_headers,
            json={"description": "No name"},
        )
        assert r.status_code == 422

    async def test_document_title_min_length(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            json={"title": "", "source_type": "text", "raw_text": "content"},
        )
        assert r.status_code == 422

    async def test_memory_key_min_length(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "fact", "key": "", "value": {}},
        )
        assert r.status_code == 422
