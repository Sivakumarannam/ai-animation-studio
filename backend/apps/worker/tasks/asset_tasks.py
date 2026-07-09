"""
Phase 6 — AI Asset Generation Engine Celery tasks.

Follows the exact Phase 3/4/5 pattern:
  - @celery_app.task wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - All actual logic delegates to services (no business logic here)
  - session_scope() used in every core function (NullPool + fork-safe commit)

TaskDispatcher calls these via apply_async() when Redis is available,
or calls the underlying async core function directly in sync fallback mode.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from celery.utils.log import get_task_logger

from apps.worker.main import celery_app
from apps.worker.tasks.dead_letter import dead_letter_task

logger = get_task_logger(__name__)


def _run_async(coro) -> Any:
    """Run coroutine synchronously — safe inside and outside an event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Helper — build repo+service bundle from a session
# ---------------------------------------------------------------------------

def _make_repos(session):
    from repositories.asset_generation_repository import (
        AssetCacheRepository,
        AssetCollectionRepository,
        AssetEmbeddingRepository,
        AssetEvaluationRepository,
        AssetMemoryRepository,
        AssetProjectRepository,
        AssetPromptRepository,
        AssetRepository,
        AssetRelationshipRepository,
        AssetVersionRepository,
        CameraShotRepository,
        GeneratedImageRepository,
        GenerationHistoryRepository,
        GenerationJobRepository,
        LightingPresetRepository,
        NegativePromptRepository,
        PromptHistoryRepository,
        PromptTemplateRepository,
        RetryQueueRepository,
        SceneCompositionRepository,
    )
    return dict(
        ap=AssetProjectRepository(session),
        asset=AssetRepository(session),
        version=AssetVersionRepository(session),
        prompt=AssetPromptRepository(session),
        template=PromptTemplateRepository(session),
        negative=NegativePromptRepository(session),
        history_p=PromptHistoryRepository(session),
        image=GeneratedImageRepository(session),
        evaluation=AssetEvaluationRepository(session),
        memory=AssetMemoryRepository(session),
        composition=SceneCompositionRepository(session),
        shot=CameraShotRepository(session),
        lighting=LightingPresetRepository(session),
        retry=RetryQueueRepository(session),
        job=GenerationJobRepository(session),
        gen_history=GenerationHistoryRepository(session),
        collection=AssetCollectionRepository(session),
        embedding=AssetEmbeddingRepository(session),
        cache=AssetCacheRepository(session),
        relationship=AssetRelationshipRepository(session),
    )


def _make_services(repos, image_provider, evaluation_provider, embedding_provider):
    from services.asset_generation.generation_job_service import GenerationJobService
    from services.asset_generation.prompt_generation_service import PromptGenerationService
    from services.asset_generation.shot_planning_service import ShotPlanningService
    from services.asset_generation.asset_planning_service import AssetPlanningService
    from services.asset_generation.image_generation_service import ImageGenerationService
    from services.asset_generation.quality_evaluation_service import QualityEvaluationService
    from services.asset_generation.retry_engine_service import RetryEngineService
    from services.asset_generation.asset_library_service import AssetLibraryService
    from services.asset_generation.consistency_engine_service import ConsistencyEngineService

    return dict(
        job=GenerationJobService(repos["job"]),
        prompt=PromptGenerationService(
            repos["prompt"], repos["template"], repos["negative"],
            repos["history_p"], repos["memory"],
        ),
        shot=ShotPlanningService(repos["composition"], repos["shot"]),
        planner=AssetPlanningService(repos["asset"], repos["cache"]),
        gen=ImageGenerationService(repos["asset"], repos["version"], repos["image"], image_provider),
        eval=QualityEvaluationService(
            repos["evaluation"], repos["asset"], repos["version"],
            repos["retry"], evaluation_provider,
        ),
        retry=RetryEngineService(repos["retry"], repos["asset"]),
        library=AssetLibraryService(
            repos["asset"], repos["embedding"], repos["cache"],
            repos["memory"], embedding_provider,
        ),
        consistency=ConsistencyEngineService(repos["asset"], repos["relationship"], repos["memory"]),
    )


# ---------------------------------------------------------------------------
# Async core functions — called directly in sync fallback mode
# ---------------------------------------------------------------------------

async def _plan_episode_assets_core(job_id: str, episode_id: str, project_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from agents.registry import get_image_provider, get_asset_evaluation_provider, get_embedding_provider
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(
            repos,
            get_image_provider(),
            get_asset_evaluation_provider(),
            get_embedding_provider(),
        )
        job_svc = svcs["job"]
        planner = svcs["planner"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            # Build stub episode_data from params
            episode_data = params.get("episode_data", {
                "scenes": params.get("scenes", []),
                "characters": params.get("characters", []),
            })
            result = await planner.plan_episode_assets(
                project_id=UUID(project_id),
                episode_id=UUID(episode_id),
                episode_data=episode_data,
                requested_asset_types=params.get("asset_types"),
                force_regenerate=params.get("force_regenerate", False),
                quality_threshold=float(params.get("quality_threshold", 90.0)),
            )
            # persist planned assets
            asset_repo = repos["asset"]
            for asset in result.get("_assets", []):
                await asset_repo.create(asset)
            await session.flush()

            if job:
                await job_svc.complete_job(job.id, result)
            logger.info("plan_episode_assets_complete", result=result)
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _generate_asset_core(job_id: str, asset_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from agents.registry import get_image_provider, get_asset_evaluation_provider, get_embedding_provider
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(
            repos,
            get_image_provider(),
            get_asset_evaluation_provider(),
            get_embedding_provider(),
        )
        job_svc = svcs["job"]
        prompt_svc = svcs["prompt"]
        gen_svc = svcs["gen"]
        eval_svc = svcs["eval"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            asset = await repos["asset"].get_by_id(UUID(asset_id))
            if asset is None:
                raise ValueError(f"Asset {asset_id} not found")

            asset.status = "generating"
            await session.flush()

            # Generate prompt
            prompt = await prompt_svc.generate_prompt(
                asset=asset,
                style_data=params.get("style_data"),
                lighting_data=params.get("lighting_data"),
                pose_data=params.get("pose_data"),
                expression_data=params.get("expression_data"),
            )
            await session.flush()

            # Generate image
            version, gen_image = await gen_svc.generate_for_asset(
                asset=asset,
                prompt=prompt,
                generation_params=params.get("generation_params"),
            )
            await session.flush()

            # Evaluate
            evaluation = await eval_svc.evaluate_asset(
                asset=asset,
                version=version,
                prompt_text=prompt.full_prompt,
            )
            await session.flush()

            result = {
                "asset_id": str(asset.id),
                "version_id": str(version.id),
                "quality_score": evaluation.overall_score,
                "passed": evaluation.passed_threshold,
                "status": asset.status,
            }

            if job:
                await job_svc.complete_job(job.id, result)
            logger.info(
                "generate_asset_complete",
                asset_id=asset_id,
                quality=evaluation.overall_score,
                passed=evaluation.passed_threshold,
            )
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _generate_episode_assets_core(job_id: str, episode_id: str, project_id: str, params: dict) -> dict[str, Any]:
    """Plan + generate all assets for an episode in one shot."""
    from database.connection import session_scope
    from agents.registry import get_image_provider, get_asset_evaluation_provider, get_embedding_provider
    from uuid import UUID
    import time

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(
            repos,
            get_image_provider(),
            get_asset_evaluation_provider(),
            get_embedding_provider(),
        )
        job_svc = svcs["job"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            start = time.time()
            planner = svcs["planner"]
            prompt_svc = svcs["prompt"]
            gen_svc = svcs["gen"]
            eval_svc = svcs["eval"]

            episode_data = params.get("episode_data", {
                "scenes": params.get("scenes", []),
                "characters": params.get("characters", []),
            })
            quality_threshold = float(params.get("quality_threshold", 90.0))

            # 1. Plan assets
            plan_result = await planner.plan_episode_assets(
                project_id=UUID(project_id),
                episode_id=UUID(episode_id),
                episode_data=episode_data,
                requested_asset_types=params.get("asset_types"),
                force_regenerate=params.get("force_regenerate", False),
                quality_threshold=quality_threshold,
            )

            # 2. Persist planned assets
            asset_ids = []
            for asset_obj in plan_result.get("_assets", []):
                saved = await repos["asset"].create(asset_obj)
                asset_ids.append(saved.id)
            await session.flush()

            # 3. Generate each asset
            generated = 0
            accepted = 0
            failed = 0
            for aid in asset_ids:
                asset = await repos["asset"].get_by_id(aid)
                if asset is None:
                    continue
                try:
                    asset.status = "generating"
                    await session.flush()
                    prompt = await prompt_svc.generate_prompt(asset=asset)
                    await session.flush()
                    version, _ = await gen_svc.generate_for_asset(asset=asset, prompt=prompt)
                    await session.flush()
                    evaluation = await eval_svc.evaluate_asset(
                        asset=asset, version=version,
                        prompt_text=prompt.full_prompt,
                    )
                    await session.flush()
                    generated += 1
                    if evaluation.passed_threshold:
                        accepted += 1
                    else:
                        failed += 1
                except Exception as exc:
                    logger.warning("asset_generation_failed", asset_id=str(aid), error=str(exc))
                    failed += 1

            duration = round(time.time() - start, 2)

            # 4. Record generation history
            from database.models.asset_generation import GenerationHistory
            history = GenerationHistory(
                project_id=UUID(project_id),
                episode_id=UUID(episode_id),
                run_type="episode",
                triggered_by=params.get("triggered_by", "api"),
                assets_planned=len(asset_ids),
                assets_generated=generated,
                assets_accepted=accepted,
                assets_rejected=failed,
                avg_quality_score=0.0,
                duration_seconds=duration,
                run_status="completed" if failed == 0 else "partial",
            )
            await repos["gen_history"].create(history)

            result = {
                "episode_id": episode_id,
                "project_id": project_id,
                "assets_planned": len(asset_ids),
                "assets_generated": generated,
                "assets_accepted": accepted,
                "assets_failed": failed,
                "duration_seconds": duration,
            }
            if job:
                await job_svc.complete_job(job.id, result)
            logger.info("generate_episode_assets_complete", **result)
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _process_retry_queue_core(job_id: str, project_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from agents.registry import get_image_provider, get_asset_evaluation_provider, get_embedding_provider
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(
            repos,
            get_image_provider(),
            get_asset_evaluation_provider(),
            get_embedding_provider(),
        )
        job_svc = svcs["job"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            retry_svc = svcs["retry"]
            prompt_svc = svcs["prompt"]
            gen_svc = svcs["gen"]
            eval_svc = svcs["eval"]

            pending = await repos["retry"].get_pending(UUID(project_id), limit=params.get("limit", 10))
            resolved = 0
            exhausted = 0

            for entry in pending:
                asset = await repos["asset"].get_by_id(entry.asset_id)
                if asset is None:
                    continue
                retry_params = await retry_svc.get_retry_params(entry)
                await retry_svc.mark_retrying(entry)
                await session.flush()

                try:
                    asset.status = "generating"
                    await session.flush()
                    prompt = await prompt_svc.generate_prompt(
                        asset=asset,
                        extra_params=retry_params,
                    )
                    await session.flush()
                    version, _ = await gen_svc.generate_for_asset(
                        asset=asset, prompt=prompt,
                        generation_params=retry_params,
                    )
                    await session.flush()
                    evaluation = await eval_svc.evaluate_asset(
                        asset=asset, version=version,
                        prompt_text=prompt.full_prompt,
                    )
                    await session.flush()

                    if evaluation.passed_threshold:
                        await retry_svc.mark_resolved(entry)
                        resolved += 1
                    else:
                        if entry.retry_count >= entry.max_retries:
                            await retry_svc.mark_exhausted(entry)
                            exhausted += 1
                        # else stays pending for next run
                except Exception as exc:
                    logger.warning("retry_failed", asset_id=str(entry.asset_id), error=str(exc))
                    if entry.retry_count >= entry.max_retries:
                        await retry_svc.mark_exhausted(entry)
                        exhausted += 1

            result = {
                "project_id": project_id,
                "processed": len(pending),
                "resolved": resolved,
                "exhausted": exhausted,
            }
            if job:
                await job_svc.complete_job(job.id, result)
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


async def _update_embeddings_core(job_id: str, project_id: str, params: dict) -> dict[str, Any]:
    from database.connection import session_scope
    from agents.registry import get_image_provider, get_asset_evaluation_provider, get_embedding_provider
    from uuid import UUID

    async with session_scope() as session:
        repos = _make_repos(session)
        svcs = _make_services(
            repos,
            get_image_provider(),
            get_asset_evaluation_provider(),
            get_embedding_provider(),
        )
        job_svc = svcs["job"]

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            library_svc = svcs["library"]
            from packages.utils.pagination import PaginationParams
            completed_assets = await repos["asset"].get_by_project(
                project_id=UUID(project_id),
                pagination=PaginationParams(page=1, page_size=100),
                status="completed",
            )
            embedded = 0
            for asset in completed_assets.items:
                emb = await library_svc.embed_asset(asset)
                if emb:
                    embedded += 1

            result = {"project_id": project_id, "assets_embedded": embedded}
            if job:
                await job_svc.complete_job(job.id, result)
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise


# ---------------------------------------------------------------------------
# Celery task wrappers
# ---------------------------------------------------------------------------

class BaseAssetTask(celery_app.Task):  # type: ignore[misc]
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("task_failed", task=self.name, task_id=task_id, error=str(exc))

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("task_success", task=self.name, result_keys=list(retval.keys()) if isinstance(retval, dict) else [])


@celery_app.task(
    bind=True, base=BaseAssetTask, name="asset.plan_episode_assets",
    queue="ai", max_retries=3, default_retry_delay=60,
)
def plan_episode_assets(self, job_id: str, episode_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_plan_episode_assets_core(job_id, episode_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseAssetTask, name="asset.generate_asset",
    queue="ai", max_retries=3, default_retry_delay=30,
)
def generate_asset(self, job_id: str, asset_id: str, params: dict) -> dict:
    try:
        return _run_async(_generate_asset_core(job_id, asset_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id, asset_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseAssetTask, name="asset.generate_episode_assets",
    queue="ai", max_retries=2, default_retry_delay=60,
)
def generate_episode_assets(self, job_id: str, episode_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_generate_episode_assets_core(job_id, episode_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        dead_letter_task.apply_async(args=[self.name, [job_id], {"error": str(exc)}])
        raise


@celery_app.task(
    bind=True, base=BaseAssetTask, name="asset.process_retry_queue",
    queue="default", max_retries=2, default_retry_delay=60,
)
def process_retry_queue(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_process_retry_queue_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@celery_app.task(
    bind=True, base=BaseAssetTask, name="asset.update_embeddings",
    queue="default", max_retries=2, default_retry_delay=60,
)
def update_embeddings(self, job_id: str, project_id: str, params: dict) -> dict:
    try:
        return _run_async(_update_embeddings_core(job_id, project_id, params))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise
