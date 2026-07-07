"""
Tests for Phase 4 — RAG & Knowledge Intelligence Engine.
CRUD tests for collections, documents, memory, jobs, stats, and versions.

These are live integration tests against the running API server on localhost:8000.
No Ollama dependency — the backend uses MockEmbeddingProvider and InMemoryVectorStore.
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
        json={"name": "Test Collection", "description": "A collection for tests", "collection_type": "general"},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def document(client: AsyncClient, auth_headers: dict, collection: dict) -> dict:
    r = await client.post(
        f"/kn/collections/{collection['id']}/documents",
        headers=auth_headers,
        json={"title": "Test Document", "source_type": "text", "raw_text": "This is a test document with some content for chunking and embedding."},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
async def memory(client: AsyncClient, auth_headers: dict, project: dict) -> dict:
    r = await client.post(
        f"/kn/projects/{project['id']}/memory",
        headers=auth_headers,
        json={"memory_type": "fact", "key": "test_key", "value": {"text": "some fact"}, "confidence": 0.9},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Collection CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestCollections:
    async def test_create_collection(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/collections",
            headers=auth_headers,
            json={"name": "My Collection", "description": "desc", "collection_type": "general"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "My Collection"
        assert body["project_id"] == project["id"]
        assert body["collection_type"] == "general"
        assert body["document_count"] == 0
        assert body["chunk_count"] == 0

    async def test_create_collection_minimal(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/collections",
            headers=auth_headers,
            json={"name": "Minimal"},
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Minimal"

    async def test_create_collection_with_world(self, client: AsyncClient, auth_headers: dict, project: dict):
        world_r = await client.post(
            f"/si/projects/{project['id']}/worlds",
            headers=auth_headers,
            json={"name": "Scoped World", "description": "For collection scoping test"},
        )
        assert world_r.status_code == 201
        world_id = world_r.json()["id"]
        r = await client.post(
            f"/kn/projects/{project['id']}/collections",
            headers=auth_headers,
            json={"name": "World Collection", "world_id": world_id},
        )
        assert r.status_code == 201
        assert r.json()["world_id"] == world_id

    async def test_list_collections(self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict):
        r = await client.get(f"/kn/projects/{project['id']}/collections", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 1
        assert any(c["id"] == collection["id"] for c in body["items"])

    async def test_list_collections_empty_for_new_project(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/projects", headers=auth_headers, json={
            "title": "Empty Project", "description": "", "plugin_id": "telugu_family_comedy",
        })
        assert r.status_code in (200, 201)
        proj_id = r.json()["id"]
        r2 = await client.get(f"/kn/projects/{proj_id}/collections", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["meta"]["total"] == 0

    async def test_get_collection(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.get(f"/kn/collections/{collection['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == collection["id"]
        assert r.json()["name"] == collection["name"]

    async def test_get_collection_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/kn/collections/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_collection(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.patch(
            f"/kn/collections/{collection['id']}",
            headers=auth_headers,
            json={"name": "Renamed Collection", "description": "New desc"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Renamed Collection"
        assert body["description"] == "New desc"

    async def test_update_collection_partial(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.patch(
            f"/kn/collections/{collection['id']}",
            headers=auth_headers,
            json={"name": "Only Name Updated"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Only Name Updated"

    async def test_delete_collection(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/collections",
            headers=auth_headers,
            json={"name": "To Delete"},
        )
        assert r.status_code == 201
        cid = r.json()["id"]
        r2 = await client.delete(f"/kn/collections/{cid}", headers=auth_headers)
        assert r2.status_code == 204
        r3 = await client.get(f"/kn/collections/{cid}", headers=auth_headers)
        assert r3.status_code == 404

    async def test_collection_requires_auth(self, client: AsyncClient, project: dict):
        r = await client.get(f"/kn/projects/{project['id']}/collections")
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Document CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestDocuments:
    async def test_create_text_document(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            json={"title": "My Doc", "source_type": "text", "raw_text": "Hello world content."},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "My Doc"
        assert body["source_type"] == "text"
        assert body["collection_id"] == collection["id"]

    async def test_create_document_empty_title_fails(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            json={"title": "", "source_type": "text"},
        )
        assert r.status_code == 422

    async def test_list_documents(self, client: AsyncClient, auth_headers: dict, collection: dict, document: dict):
        r = await client.get(f"/kn/collections/{collection['id']}/documents", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert body["meta"]["total"] >= 1
        assert any(d["id"] == document["id"] for d in body["items"])

    async def test_get_document(self, client: AsyncClient, auth_headers: dict, document: dict):
        r = await client.get(f"/kn/documents/{document['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == document["id"]
        assert r.json()["title"] == document["title"]

    async def test_get_document_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/kn/documents/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_delete_document(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            json={"title": "To Delete", "source_type": "text", "raw_text": "some content"},
        )
        assert r.status_code == 201
        did = r.json()["id"]
        r2 = await client.delete(f"/kn/documents/{did}", headers=auth_headers)
        assert r2.status_code == 204
        r3 = await client.get(f"/kn/documents/{did}", headers=auth_headers)
        assert r3.status_code == 404

    async def test_document_requires_auth(self, client: AsyncClient, collection: dict):
        r = await client.get(f"/kn/collections/{collection['id']}/documents")
        assert r.status_code == 401

    async def test_get_document_chunks_empty(self, client: AsyncClient, auth_headers: dict, document: dict):
        r = await client.get(f"/kn/documents/{document['id']}/chunks", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─────────────────────────────────────────────────────────────────────────────
# Document Upload
# ─────────────────────────────────────────────────────────────────────────────

class TestDocumentUpload:
    async def test_upload_text_file(self, client: AsyncClient, auth_headers: dict, collection: dict):
        content = b"Sample text file content for testing upload and processing pipeline."
        files = {"file": ("sample.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        body = r.json()
        assert "job_id" in body
        assert "status" in body
        assert body["mode"] in ("sync", "async", "celery")

    async def test_upload_markdown_file(self, client: AsyncClient, auth_headers: dict, collection: dict):
        content = b"# Heading\n\nMarkdown content for testing."
        files = {"file": ("readme.md", content, "text/markdown")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        body = r.json()
        assert "job_id" in body

    async def test_upload_creates_document(self, client: AsyncClient, auth_headers: dict, collection: dict):
        content = b"Content that becomes a document."
        files = {"file": ("doc.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        r2 = await client.get(f"/kn/collections/{collection['id']}/documents", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["meta"]["total"] >= 1

    async def test_process_document(self, client: AsyncClient, auth_headers: dict, document: dict):
        r = await client.post(f"/kn/documents/{document['id']}/process", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "job_id" in body
        assert body["mode"] in ("sync", "async", "celery")


# ─────────────────────────────────────────────────────────────────────────────
# Search / Retrieval
# ─────────────────────────────────────────────────────────────────────────────

class TestSearch:
    async def test_search_empty_collection(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "test query"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["query"] == "test query"
        assert isinstance(body["results"], list)
        assert body["result_count"] == len(body["results"])

    async def test_search_with_top_k(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "test query", "top_k": 5},
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["results"]) <= 5

    async def test_search_with_min_score(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "test", "min_score": 0.5},
        )
        assert r.status_code == 200
        for result in r.json()["results"]:
            assert result["score"] >= 0.5

    async def test_search_requires_query(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": ""},
        )
        assert r.status_code == 422

    async def test_search_result_shape(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.post(
            f"/kn/collections/{collection['id']}/search",
            headers=auth_headers,
            json={"query": "anything"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "query" in body
        assert "results" in body
        assert "result_count" in body


# ─────────────────────────────────────────────────────────────────────────────
# Embedding Jobs
# ─────────────────────────────────────────────────────────────────────────────

class TestEmbeddingJobs:
    async def test_list_jobs_empty(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.get(f"/kn/projects/{project['id']}/jobs", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "meta" in body

    async def test_list_jobs_after_upload(self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict):
        content = b"Content for job tracking test."
        files = {"file": ("test.txt", content, "text/plain")}
        await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        r = await client.get(f"/kn/projects/{project['id']}/jobs", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

    async def test_get_job(self, client: AsyncClient, auth_headers: dict, collection: dict):
        content = b"Content for job retrieval test."
        files = {"file": ("test.txt", content, "text/plain")}
        r = await client.post(
            f"/kn/collections/{collection['id']}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert r.status_code == 202
        job_id = r.json()["job_id"]
        r2 = await client.get(f"/kn/jobs/{job_id}", headers=auth_headers)
        assert r2.status_code == 200
        body = r2.json()
        assert body["id"] == job_id
        assert "status" in body
        assert "job_type" in body

    async def test_get_job_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get(f"/kn/jobs/{uuid4()}", headers=auth_headers)
        assert r.status_code == 404

    async def test_retry_queue(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/kn/jobs/retry-queue", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_list_jobs_status_filter(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.get(
            f"/kn/projects/{project['id']}/jobs",
            headers=auth_headers,
            params={"status": "completed"},
        )
        assert r.status_code == 200
        for job in r.json()["items"]:
            assert job["status"] == "completed"


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Memory
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeMemory:
    async def test_create_memory(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "fact", "key": "hero_name", "value": {"name": "Hero"}, "confidence": 1.0},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["key"] == "hero_name"
        assert body["memory_type"] == "fact"
        assert body["project_id"] == project["id"]
        assert body["is_active"] is True

    async def test_create_memory_rule_type(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "rule", "key": "no_violence", "value": {"rule": "no violence"}, "confidence": 1.0},
        )
        assert r.status_code == 201
        assert r.json()["memory_type"] == "rule"

    async def test_list_memory_by_project(self, client: AsyncClient, auth_headers: dict, project: dict, memory: dict):
        r = await client.get(f"/kn/projects/{project['id']}/memory", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "meta" in body
        assert any(m["id"] == memory["id"] for m in body["items"])

    async def test_list_memory_with_type_filter(self, client: AsyncClient, auth_headers: dict, project: dict):
        await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "lore", "key": "lore_key", "value": {}, "confidence": 0.8},
        )
        r = await client.get(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            params={"memory_type": "lore"},
        )
        assert r.status_code == 200
        for m in r.json()["items"]:
            assert m["memory_type"] == "lore"

    async def test_deactivate_memory(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "fact", "key": "to_deactivate", "value": {}},
        )
        assert r.status_code == 201
        mid = r.json()["id"]
        r2 = await client.delete(f"/kn/memory/{mid}", headers=auth_headers)
        assert r2.status_code == 204

    async def test_memory_requires_auth(self, client: AsyncClient, project: dict):
        r = await client.get(f"/kn/projects/{project['id']}/memory")
        assert r.status_code == 401

    async def test_memory_key_required(self, client: AsyncClient, auth_headers: dict, project: dict):
        r = await client.post(
            f"/kn/projects/{project['id']}/memory",
            headers=auth_headers,
            json={"memory_type": "fact", "key": "", "value": {}},
        )
        assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeStats:
    async def test_get_stats_empty(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/projects", headers=auth_headers, json={
            "title": "Stats Project", "description": "", "plugin_id": "telugu_family_comedy",
        })
        assert r.status_code in (200, 201)
        proj_id = r.json()["id"]
        r2 = await client.get(f"/kn/projects/{proj_id}/stats", headers=auth_headers)
        assert r2.status_code == 200
        body = r2.json()
        assert body["collections"] == 0
        assert body["documents"] == 0
        assert body["chunks"] == 0
        assert body["embedded_chunks"] == 0
        assert body["memories"] == 0
        assert "jobs_by_status" in body
        assert "embedding_provider" in body
        assert "vector_store_provider" in body

    async def test_get_stats_with_data(self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict, document: dict, memory: dict):
        r = await client.get(f"/kn/projects/{project['id']}/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["collections"] >= 1
        assert body["documents"] >= 1
        assert body["memories"] >= 1
        assert body["embedding_provider"] != ""
        assert body["vector_store_provider"] != ""

    async def test_stats_requires_auth(self, client: AsyncClient, project: dict):
        r = await client.get(f"/kn/projects/{project['id']}/stats")
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Versions
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeVersions:
    async def test_list_versions_empty(self, client: AsyncClient, auth_headers: dict, collection: dict):
        r = await client.get(f"/kn/collection/{collection['id']}/versions", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─────────────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────────────

class TestPagination:
    async def test_collections_pagination(self, client: AsyncClient, auth_headers: dict, project: dict):
        for i in range(3):
            await client.post(
                f"/kn/projects/{project['id']}/collections",
                headers=auth_headers,
                json={"name": f"Paginate Collection {i}"},
            )
        r = await client.get(
            f"/kn/projects/{project['id']}/collections",
            headers=auth_headers,
            params={"page": 1, "page_size": 2},
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) <= 2
        assert body["meta"]["page"] == 1
        assert body["meta"]["page_size"] == 2

    async def test_documents_pagination(self, client: AsyncClient, auth_headers: dict, collection: dict):
        for i in range(3):
            await client.post(
                f"/kn/collections/{collection['id']}/documents",
                headers=auth_headers,
                json={"title": f"Paginate Doc {i}", "source_type": "text", "raw_text": f"content {i}"},
            )
        r = await client.get(
            f"/kn/collections/{collection['id']}/documents",
            headers=auth_headers,
            params={"page": 1, "page_size": 2},
        )
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 2

    async def test_meta_structure(self, client: AsyncClient, auth_headers: dict, project: dict, collection: dict):
        r = await client.get(f"/kn/projects/{project['id']}/collections", headers=auth_headers)
        meta = r.json()["meta"]
        assert "page" in meta
        assert "page_size" in meta
        assert "total" in meta
        assert "total_pages" in meta
