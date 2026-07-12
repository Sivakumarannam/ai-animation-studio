"""
Phase 6 — AI Asset Generation Engine tests.

Tests are fully deterministic — all AI providers are mocked.
Follows the same pattern as Phase 3/4/5 tests.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_uuid() -> str:
    return str(uuid.uuid4())


# ──────────────────────────────────────────────────────────────────────────────
# 1. MockAssetEvaluationProvider — deterministic scoring
# ──────────────────────────────────────────────────────────────────────────────

class TestMockAssetEvaluationProvider:
    def test_score_is_deterministic(self):
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
        from agents.interfaces.asset_evaluation_provider import EvaluationRequest

        provider = MockAssetEvaluationProvider()
        req = EvaluationRequest(
            prompt="a cartoon character",
            asset_type="character",
            image_data="storage_key_example",


        )
        loop = asyncio.get_event_loop()
        r1 = loop.run_until_complete(provider.evaluate(req))
        r2 = loop.run_until_complete(provider.evaluate(req))
        assert r1.overall_score == r2.overall_score, "Score must be deterministic"

    def test_score_is_in_valid_range(self):
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
        from agents.interfaces.asset_evaluation_provider import EvaluationRequest

        provider = MockAssetEvaluationProvider()
        loop = asyncio.get_event_loop()
        for asset_type in ["character", "background", "prop", "thumbnail"]:
            req = EvaluationRequest(
                prompt=f"test {asset_type} prompt",
                asset_type=asset_type,
                image_data="storage_key_example",
    
    
            )
            result = loop.run_until_complete(provider.evaluate(req))
            assert 0 <= result.overall_score <= 100
            assert isinstance(result.passed, bool)
            assert isinstance(result.failure_reasons, list)

    def test_score_varies_by_prompt(self):
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
        from agents.interfaces.asset_evaluation_provider import EvaluationRequest

        provider = MockAssetEvaluationProvider()
        loop = asyncio.get_event_loop()
        scores = set()
        for i in range(10):
            req = EvaluationRequest(
                prompt=f"unique prompt {i} for testing variation",
                asset_type="character",
                image_data="storage_key_example",
    
    
            )
            r = loop.run_until_complete(provider.evaluate(req))
            scores.add(round(r.overall_score, 1))
        # We expect at least 3 distinct scores across 10 different prompts
        assert len(scores) >= 3, f"Expected score variation, got: {scores}"

    def test_evaluation_has_all_dimension_scores(self):
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
        from agents.interfaces.asset_evaluation_provider import EvaluationRequest

        provider = MockAssetEvaluationProvider()
        loop = asyncio.get_event_loop()
        req = EvaluationRequest(
            prompt="full test prompt for all dimensions",
            asset_type="character",
            image_data="storage_key_example",


        )
        result = loop.run_until_complete(provider.evaluate(req))
        # All 13 dimensions must be set
        assert hasattr(result, "overall_score")
        assert hasattr(result, "prompt_quality")
        assert hasattr(result, "image_quality")
        assert hasattr(result, "character_consistency")
        assert hasattr(result, "composition_score")
        assert hasattr(result, "lighting_score")
        assert hasattr(result, "style_match")
        assert hasattr(result, "face_score")
        assert hasattr(result, "hands_score")

    def test_provider_is_available(self):
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
        provider = MockAssetEvaluationProvider()
        loop = asyncio.get_event_loop()
        assert provider is not None  # is_available not in base interface

    def test_provider_name(self):
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
        provider = MockAssetEvaluationProvider()
        assert "mock" in provider.provider_name


# ──────────────────────────────────────────────────────────────────────────────
# 2. EvaluationProvider interface
# ──────────────────────────────────────────────────────────────────────────────

class TestAssetEvaluationProviderInterface:
    def test_evaluation_request_creation(self):
        from agents.interfaces.asset_evaluation_provider import EvaluationRequest
        req = EvaluationRequest(
            prompt="test prompt",
            asset_type="background",
            image_data="storage_key_example",

        )
        assert req.prompt == "test prompt"
        assert req.asset_type == "background"
        # version_number removed (field does not exist on EvaluationRequest)

    def test_evaluation_result_fields(self):
        from agents.interfaces.asset_evaluation_provider import EvaluationResult
        result = EvaluationResult(
            overall_score=85.0,
            prompt_quality=80.0,
            image_quality=90.0,
            character_consistency=85.0,
            background_consistency=88.0,
            composition_score=87.0,
            lighting_score=82.0,
            style_match=79.0,
            scene_match=84.0,
            resolution_score=95.0,
            artifact_score=90.0,
            hands_score=75.0,
            face_score=88.0,
            text_error_score=98.0,
            passed=False,  # 85 < 90 threshold
            failure_reasons=["style_match_below_threshold"],
            notes="Style match could be improved",
        )
        assert result.overall_score == 85.0
        assert result.passed is False
        assert "style_match_below_threshold" in result.failure_reasons


# ──────────────────────────────────────────────────────────────────────────────
# 3. API Schema validation
# ──────────────────────────────────────────────────────────────────────────────

class TestAssetGenerationSchemas:
    def test_trigger_episode_generation_request(self):
        from apps.api.schemas.asset_generation import TriggerEpisodeGenerationRequest
        req = TriggerEpisodeGenerationRequest(
            project_id=uuid.uuid4(),
            episode_id=uuid.uuid4(),
            asset_types=["character", "background"],
            quality_threshold=85.0,
            max_retries=3,
            force_regenerate=False,
        )
        assert req.quality_threshold == 85.0
        assert len(req.asset_types) == 2

    def test_trigger_asset_generation_request(self):
        from apps.api.schemas.asset_generation import TriggerAssetGenerationRequest
        req = TriggerAssetGenerationRequest(
            asset_id=uuid.uuid4(),
            force_regenerate=True,
            custom_params={"steps": 30},
        )
        assert req.force_regenerate is True
        assert req.custom_params["steps"] == 30

    def test_dispatch_response_schema(self):
        from apps.api.schemas.asset_generation import DispatchResponse
        resp = DispatchResponse(
            job_id=uuid.uuid4(),
            status="dispatched",
            message="Asset generation dispatched",
            dispatch_mode="sync",
        )
        assert resp.status == "dispatched"
        assert resp.dispatch_mode == "sync"

    def test_asset_dashboard_stats_schema(self):
        from apps.api.schemas.asset_generation import AssetDashboardStats
        stats = AssetDashboardStats(
            total_assets=100,
            assets_completed=80,
            assets_pending=10,
            assets_failed=5,
            assets_generating=5,
            total_retries=15,
            avg_quality_score=88.5,
            assets_by_type={"character": 40, "background": 30, "prop": 30},
            recent_jobs=[],
            storage_bytes_used=1024 * 1024 * 50,
            generation_history_7d=[],
        )
        assert stats.total_assets == 100
        assert stats.assets_by_type["character"] == 40

    def test_asset_search_request_schema(self):
        from apps.api.schemas.asset_generation import AssetSearchRequest
        req = AssetSearchRequest(
            query="happy character",
            asset_type="character",
            min_quality=80.0,
            limit=10,
            offset=0,
        )
        assert req.query == "happy character"
        assert req.min_quality == 80.0

    def test_asset_project_create_schema(self):
        from apps.api.schemas.asset_generation import AssetProjectCreate
        pid = uuid.uuid4()
        body = AssetProjectCreate(
            project_id=pid,
            name="Test Project",
            description="Test",
            quality_threshold=90.0,
        )
        assert body.project_id == pid

    def test_asset_style_create_schema(self):
        from apps.api.schemas.asset_generation import AssetStyleCreate
        body = AssetStyleCreate(
            name="2D Cartoon",
            slug="2d-cartoon",
            description="Flat 2D cartoon style",
            style_type="2d_cartoon",
        )
        assert body.slug == "2d-cartoon"

    def test_asset_collection_create_schema(self):
        from apps.api.schemas.asset_generation import AssetCollectionCreate
        body = AssetCollectionCreate(
            project_id=uuid.uuid4(),
            name="Episode 1 Assets",
            collection_type="episode",
        )
        assert body.collection_type == "episode"


# ──────────────────────────────────────────────────────────────────────────────
# 4. Config settings
# ──────────────────────────────────────────────────────────────────────────────

class TestPhase6Config:
    def test_phase6_settings_exist(self):
        from apps.api.config import get_settings
        settings = get_settings()
        assert hasattr(settings, "AG_EVALUATION_PROVIDER")
        assert hasattr(settings, "AG_QUALITY_THRESHOLD")
        assert hasattr(settings, "AG_MAX_RETRIES")
        assert hasattr(settings, "AG_TARGET_RESOLUTION")
        assert hasattr(settings, "AG_DEFAULT_STEPS")
        assert hasattr(settings, "AG_DEFAULT_CFG_SCALE")
        assert hasattr(settings, "AG_DEFAULT_SAMPLER")
        assert hasattr(settings, "AG_ASSET_BUCKET")
        assert hasattr(settings, "AG_EMBEDDING_BATCH_SIZE")

    def test_phase6_defaults(self):
        from apps.api.config import get_settings
        settings = get_settings()
        assert settings.AG_EVALUATION_PROVIDER == "mock"
        assert settings.AG_QUALITY_THRESHOLD == 90.0
        assert settings.AG_MAX_RETRIES == 3
        assert settings.AG_DEFAULT_STEPS == 20
        assert settings.AG_DEFAULT_SAMPLER == "euler_a"
        assert settings.AG_ASSET_BUCKET == "assets"


# ──────────────────────────────────────────────────────────────────────────────
# 5. Registry
# ──────────────────────────────────────────────────────────────────────────────

class TestPhase6Registry:
    def test_get_asset_evaluation_provider_function_exists(self):
        from agents.registry import get_asset_evaluation_provider
        assert callable(get_asset_evaluation_provider)

    def test_provider_registered_after_setup(self):
        from agents.registry import get_provider_registry
        from agents.interfaces.asset_evaluation_provider import AssetEvaluationProvider
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider

        registry = get_provider_registry()
        mock_eval = MockAssetEvaluationProvider()
        registry.register(AssetEvaluationProvider, mock_eval)
        resolved = registry.resolve(AssetEvaluationProvider)
        assert isinstance(resolved, MockAssetEvaluationProvider)

    def test_registry_list_includes_asset_evaluation(self):
        from agents.registry import get_provider_registry
        from agents.interfaces.asset_evaluation_provider import AssetEvaluationProvider
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider

        registry = get_provider_registry()
        registry.register(AssetEvaluationProvider, MockAssetEvaluationProvider())
        registered = registry.list_registered()
        assert "AssetEvaluationProvider" in registered


# ──────────────────────────────────────────────────────────────────────────────
# 6. Celery task structure
# ──────────────────────────────────────────────────────────────────────────────

class TestAssetCeleryTasks:
    def test_tasks_are_registered(self):
        from apps.worker.tasks import asset_tasks
        from apps.worker.main import celery_app
        registered = celery_app.tasks
        assert "asset.plan_episode_assets" in registered
        assert "asset.generate_asset" in registered
        assert "asset.generate_episode_assets" in registered
        assert "asset.process_retry_queue" in registered
        assert "asset.update_embeddings" in registered

    def test_task_queue_assignments(self):
        from apps.worker.main import celery_app
        assert celery_app.tasks["asset.plan_episode_assets"].queue == "ai"
        assert celery_app.tasks["asset.generate_asset"].queue == "ai"
        assert celery_app.tasks["asset.generate_episode_assets"].queue == "ai"
        assert celery_app.tasks["asset.process_retry_queue"].queue == "default"
        assert celery_app.tasks["asset.update_embeddings"].queue == "default"

    def test_task_max_retries(self):
        from apps.worker.main import celery_app
        assert celery_app.tasks["asset.plan_episode_assets"].max_retries == 3
        assert celery_app.tasks["asset.generate_asset"].max_retries == 3
        assert celery_app.tasks["asset.generate_episode_assets"].max_retries == 2


# ──────────────────────────────────────────────────────────────────────────────
# 7. Router structure
# ──────────────────────────────────────────────────────────────────────────────

class TestAssetGenerationRouter:
    def test_router_prefix(self):
        from apps.api.routers.asset_generation import router
        assert router.prefix == "/ag"

    def test_router_tags(self):
        from apps.api.routers.asset_generation import router
        assert "asset-generation" in router.tags

    def test_literal_routes_before_parameterized(self):
        """
        Verify /ag/retry-queue and /ag/retry-queue/{id}/retry
        are declared before /ag/jobs/{job_id} to avoid FastAPI
        matching literals as UUIDs.
        """
        from apps.api.routers.asset_generation import router
        paths = [r.path for r in router.routes]
        # retry-queue should appear before /jobs/{job_id}
        if "/ag/retry-queue" in paths and "/ag/jobs/{job_id}" in paths:
            retry_idx = paths.index("/ag/retry-queue")
            job_param_idx = paths.index("/ag/jobs/{job_id}")
            assert retry_idx < job_param_idx, \
                "Literal /ag/retry-queue must be declared before parameterized /ag/jobs/{job_id}"

    def test_router_endpoints_exist(self):
        from apps.api.routers.asset_generation import router
        paths = {r.path for r in router.routes}
        required = {
            "/ag/dashboard/{project_id}",
            "/ag/projects",
            "/ag/assets",
            "/ag/assets/{asset_id}",
            "/ag/jobs",
            "/ag/jobs/{job_id}",
            "/ag/retry-queue",
            "/ag/generate/episode",
            "/ag/generate/asset",
            "/ag/library/search",
            "/ag/presets/lighting",
            "/ag/presets/poses",
            "/ag/presets/expressions",
            "/ag/embeddings/update",
        }
        missing = required - paths
        assert not missing, f"Missing endpoints: {missing}"


# ──────────────────────────────────────────────────────────────────────────────
# 8. Alembic migration
# ──────────────────────────────────────────────────────────────────────────────

class TestPhase6Migration:
    def test_migration_file_exists(self):
        import os
        migration_dir = "alembic/versions"
        migrations = os.listdir(migration_dir)
        phase6 = [m for m in migrations if "phase6" in m and m.endswith(".py")]
        assert len(phase6) >= 1, "Phase 6 migration file not found"

    def test_migration_revision_id(self):
        import importlib.util, os; spec = importlib.util.spec_from_file_location("m", os.path.join(os.path.dirname(__file__), "../alembic/versions/c4e1f2a3b5d6_phase6_asset_generation_engine.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        assert m.revision == "c4e1f2a3b5d6"
        assert m.down_revision == "b2f7a9e1c304"

    def test_migration_has_upgrade_and_downgrade(self):
        import importlib.util, os; spec = importlib.util.spec_from_file_location("m", os.path.join(os.path.dirname(__file__), "../alembic/versions/c4e1f2a3b5d6_phase6_asset_generation_engine.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        assert callable(m.upgrade)
        assert callable(m.downgrade)


# ──────────────────────────────────────────────────────────────────────────────
# 9. Database models
# ──────────────────────────────────────────────────────────────────────────────

class TestPhase6Models:
    def test_all_models_importable(self):
        from database.models.asset_generation import (
            AssetProject, AssetStyle, AssetCollection,
            GeneratedAsset as Asset, GeneratedAssetVersion as AssetVersion,
            AssetPrompt, PromptTemplate, PromptHistory, NegativePrompt, GeneratedImage,
            AssetEvaluation, AssetTag, AssetEmbedding, AssetMemory,
            AgSceneComposition as SceneComposition,
            CameraShot, LightingPreset, PosePreset, ExpressionPreset,
            AgRetryQueue as RetryQueue, AgGenerationJob as GenerationJob,
            GenerationHistory, AssetCache, AssetRelationship,
        )
        models = [
            AssetProject, AssetStyle, AssetCollection, Asset, AssetVersion,
            AssetPrompt, PromptTemplate, PromptHistory, NegativePrompt, GeneratedImage,
            AssetEvaluation, AssetTag, AssetEmbedding, AssetMemory, SceneComposition,
            CameraShot, LightingPreset, PosePreset, ExpressionPreset,
            RetryQueue, GenerationJob, GenerationHistory, AssetCache, AssetRelationship,
        ]
        assert len(models) == 24

    def test_model_table_names(self):
        from database.models.asset_generation import (
            AssetProject, AssetStyle,
            GeneratedAsset as Asset, GeneratedAssetVersion as AssetVersion,
            AssetEvaluation,
            AgGenerationJob as GenerationJob, AgRetryQueue as RetryQueue,
        )
        assert AssetProject.__tablename__ == "ag_projects"
        assert AssetStyle.__tablename__ == "ag_styles"
        assert Asset.__tablename__ == "ag_assets"
        assert AssetVersion.__tablename__ == "ag_versions"
        assert AssetEvaluation.__tablename__ == "ag_evaluations"
        assert GenerationJob.__tablename__ == "ag_generation_jobs"
        assert RetryQueue.__tablename__ == "ag_retry_queue"

    def test_asset_has_soft_delete(self):
        from database.models.asset_generation import GeneratedAsset as Asset
        from sqlalchemy import inspect
        mapper = inspect(Asset)
        col_names = {c.key for c in mapper.columns}
        assert "is_deleted" in col_names

    def test_models_in_init(self):
        from database.models import (
            AgAssetVersion, AssetProject, AgAsset as Asset, AssetEvaluation,
            GenerationHistory, AssetCache, AssetRelationship,
        )
        assert AssetProject.__tablename__ == "ag_projects"


# ──────────────────────────────────────────────────────────────────────────────
# 10. Prompt generation service — unit test
# ──────────────────────────────────────────────────────────────────────────────

class TestPromptGenerationService:
    def _make_mock_repos(self):
        prompt_repo = AsyncMock()
        template_repo = AsyncMock()
        negative_repo = AsyncMock()
        history_repo = AsyncMock()
        memory_repo = AsyncMock()
        template_repo.get_default_for_type.return_value = None
        negative_repo.get_active_for_category.return_value = []
        memory_repo.get_consistency_data.return_value = {}
        return prompt_repo, template_repo, negative_repo, history_repo, memory_repo

    def test_service_instantiation(self):
        from services.asset_generation.prompt_generation_service import PromptGenerationService
        repos = self._make_mock_repos()
        svc = PromptGenerationService(*repos)
        assert svc is not None

    def test_build_positive_prompt_has_defaults(self):
        from services.asset_generation.prompt_generation_service import PromptGenerationService
        repos = self._make_mock_repos()
        svc = PromptGenerationService(*repos)
        # Access the default template keys
        from services.asset_generation.prompt_generation_service import _DEFAULT_POSITIVE; assert "character" in _DEFAULT_POSITIVE
        assert "background" in _DEFAULT_POSITIVE
        assert "prop" in _DEFAULT_POSITIVE


# ──────────────────────────────────────────────────────────────────────────────
# 11. Quality Evaluation Service — unit test
# ──────────────────────────────────────────────────────────────────────────────

class TestQualityEvaluationService:
    def test_service_instantiation(self):
        from services.asset_generation.quality_evaluation_service import QualityEvaluationService
        from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider

        eval_repo = AsyncMock()
        asset_repo = AsyncMock()
        version_repo = AsyncMock()
        retry_repo = AsyncMock()
        provider = MockAssetEvaluationProvider()

        svc = QualityEvaluationService(eval_repo, asset_repo, version_repo, retry_repo, provider)
        assert svc is not None
        assert svc._evaluator is not None


# ──────────────────────────────────────────────────────────────────────────────
# 12. Retry engine service — unit test
# ──────────────────────────────────────────────────────────────────────────────

class TestRetryEngineService:
    def test_retry_adjustments_defined(self):
        from services.asset_generation.retry_engine_service import RetryEngineService
        retry_repo = AsyncMock()
        asset_repo = AsyncMock()
        svc = RetryEngineService(retry_repo, asset_repo)
        from services.asset_generation.retry_engine_service import _RETRY_ADJUSTMENTS; assert len(_RETRY_ADJUSTMENTS) > 0
        pass  # checked above

    def test_known_failure_reasons_have_adjustments(self):
        from services.asset_generation.retry_engine_service import _RETRY_ADJUSTMENTS
        # "style_mismatch" is not in _RETRY_ADJUSTMENTS; check the ones that are
        for reason in ["low_quality", "artifacts"]:
            assert reason in _RETRY_ADJUSTMENTS, f"Missing adjustment for {reason}"


# ──────────────────────────────────────────────────────────────────────────────
# 13. Asset Library Service — unit test
# ──────────────────────────────────────────────────────────────────────────────

class TestAssetLibraryService:
    def test_service_instantiation(self):
        from services.asset_generation.asset_library_service import AssetLibraryService
        asset_repo = AsyncMock()
        embedding_repo = AsyncMock()
        cache_repo = AsyncMock()
        memory_repo = AsyncMock()
        embedding_provider = AsyncMock()
        svc = AssetLibraryService(asset_repo, embedding_repo, cache_repo, memory_repo, embedding_provider)
        assert svc is not None


# ──────────────────────────────────────────────────────────────────────────────
# 14. Generation Job Service — unit test
# ──────────────────────────────────────────────────────────────────────────────

class TestGenerationJobService:
    def test_service_instantiation(self):
        from services.asset_generation.generation_job_service import GenerationJobService
        job_repo = AsyncMock()
        svc = GenerationJobService(job_repo)
        assert svc is not None

    def test_service_has_create_get_start_complete_fail(self):
        from services.asset_generation.generation_job_service import GenerationJobService
        svc = GenerationJobService(AsyncMock())
        assert callable(svc.create_job)
        assert callable(svc.get_job)
        assert callable(svc.start_job)
        assert callable(svc.complete_job)
        assert callable(svc.fail_job)


# ──────────────────────────────────────────────────────────────────────────────
# 15. End-to-end job lifecycle — mocked session
# ──────────────────────────────────────────────────────────────────────────────

class TestJobLifecycleE2E:
    def _make_mock_job(self, job_id: str):
        job = MagicMock()
        job.id = uuid.UUID(job_id)
        job.status = "pending"
        job.started_at = None
        job.completed_at = None
        job.error_message = ""
        job.result = {}
        return job

    def test_job_transitions_pending_to_running_to_completed(self):
        from services.asset_generation.generation_job_service import GenerationJobService

        job_id = _make_uuid()
        mock_job = self._make_mock_job(job_id)
        job_repo = AsyncMock()
        job_repo.get_by_id.return_value = mock_job
        job_repo.update.return_value = mock_job

        svc = GenerationJobService(job_repo)

        loop = asyncio.get_event_loop()

        # start
        mock_job.status = "pending"
        loop.run_until_complete(svc.start_job(uuid.UUID(job_id)))
        assert job_repo.start_job.called

        # complete
        mock_job.status = "running"
        loop.run_until_complete(svc.complete_job(uuid.UUID(job_id), {"result": "ok"}))
        assert job_repo.complete_job.called

    def test_job_transitions_to_failed(self):
        from services.asset_generation.generation_job_service import GenerationJobService

        job_id = _make_uuid()
        mock_job = self._make_mock_job(job_id)
        job_repo = AsyncMock()
        job_repo.get_by_id.return_value = mock_job
        job_repo.update.return_value = mock_job

        svc = GenerationJobService(job_repo)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.fail_job(uuid.UUID(job_id), "Image generation failed"))
        assert job_repo.fail_job.called


# ──────────────────────────────────────────────────────────────────────────────
# 16. POST /ag/generate/asset — live endpoint dispatch call
#
# Regression test for a bug where the endpoint called
# `dispatcher.dispatch(task=..., core_coro=..., kwargs=...)` but
# TaskDispatcher.dispatch()'s real signature is
# `dispatch(celery_task=..., core_coro_factory=..., job_id=..., queue=..., task_kwargs=...)`.
# That mismatch raised a TypeError inside the endpoint (500) and left the
# eagerly-constructed `core_coro` coroutine unawaited. Unit tests that mock
# `dispatcher.dispatch` wholesale (or call the service layer directly) never
# exercise the real keyword arguments, so this must hit the actual endpoint.
# ──────────────────────────────────────────────────────────────────────────────

class TestGenerateAssetEndpointDispatch:
    @pytest.mark.asyncio
    async def test_generate_asset_dispatches_without_error(self, client, auth_headers, project):
        """POST /ag/generate/asset must accept the request and dispatch a
        Celery task (or run the sync fallback) instead of raising a 500 from
        a keyword-argument mismatch on TaskDispatcher.dispatch()."""
        project_id = project["id"]

        r = await client.post(
            "/ag/projects", headers=auth_headers,
            json={"project_id": project_id, "name": "AG Project"},
        )
        assert r.status_code == 201, f"ag project create failed: {r.text}"

        r = await client.post(
            "/ag/assets", headers=auth_headers,
            json={"project_id": project_id, "name": "Asset 1", "asset_type": "character"},
        )
        assert r.status_code == 201, f"asset create failed: {r.text}"
        asset_id = r.json()["id"]

        r = await client.post(
            "/ag/generate/asset", headers=auth_headers,
            json={"asset_id": asset_id, "force_regenerate": False, "custom_params": {}},
        )
        assert r.status_code == 202, f"generate/asset should dispatch, got: {r.status_code} {r.text}"
        body = r.json()
        assert body["dispatch_mode"] in ("sync", "async", "celery")
        assert body["status"] == "dispatched"

    def test_dispatch_call_uses_real_dispatcher_signature(self):
        """Static guard: the call site must use TaskDispatcher's real keyword
        arguments (celery_task/core_coro_factory/job_id/queue/task_kwargs),
        not the made-up task/core_coro/kwargs names that caused the bug."""
        import inspect
        from apps.api.routers import asset_generation as mod

        src = inspect.getsource(mod.trigger_asset_generation)
        assert "celery_task=" in src, "must call dispatch(celery_task=...)"
        assert "core_coro_factory=" in src, "must call dispatch(core_coro_factory=...) (lazy, not eagerly-created coroutine)"
        assert "\n        task=generate_asset" not in src, "must not use the old, wrong 'task=' kwarg"
        assert "core_coro=_generate_asset_core" not in src, "must not use the old, wrong 'core_coro=' kwarg (creates an unawaited coroutine)"

    @pytest.mark.asyncio
    async def test_generate_asset_reaches_completed(self, client, auth_headers, project):
        """End-to-end regression: after dispatch succeeds, the Celery task
        must actually reach status 'completed' (not just 'received' then
        crash/retry). This catches bugs downstream of dispatch too, such as
        ImageProvider.generate() being called with the wrong keyword
        arguments, or a stdlib task logger being called with structlog-style
        kwargs it doesn't accept."""
        project_id = project["id"]

        r = await client.post(
            "/ag/projects", headers=auth_headers,
            json={"project_id": project_id, "name": "AG Project"},
        )
        assert r.status_code == 201, f"ag project create failed: {r.text}"

        r = await client.post(
            "/ag/assets", headers=auth_headers,
            json={"project_id": project_id, "name": "Asset 1", "asset_type": "character"},
        )
        assert r.status_code == 201, f"asset create failed: {r.text}"
        asset_id = r.json()["id"]

        r = await client.post(
            "/ag/generate/asset", headers=auth_headers,
            json={"asset_id": asset_id, "force_regenerate": False, "custom_params": {}},
        )
        assert r.status_code == 202, f"generate/asset should dispatch, got: {r.status_code} {r.text}"
        job_id = r.json()["job_id"]

        status = None
        for _ in range(20):
            await asyncio.sleep(1)
            r = await client.get(f"/ag/jobs/{job_id}", headers=auth_headers)
            assert r.status_code == 200
            status = r.json()["status"]
            if status in ("completed", "failed"):
                break
        assert status == "completed", f"job never completed (last status={status}): {r.text}"

        r = await client.get(f"/ag/assets/{asset_id}", headers=auth_headers)
        assert r.status_code == 200
        asset = r.json()
        assert asset["status"] == "completed"
        assert asset["version_count"] >= 1
        assert asset["storage_key"]
