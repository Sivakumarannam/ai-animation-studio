"""
Phase 6 — Quality Evaluation Service.

Evaluates generated images and decides:
  - Accept (score ≥ threshold) → update asset to "completed"
  - Reject (score < threshold) → queue for retry
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from agents.interfaces.asset_evaluation_provider import EvaluationRequest
from database.models.asset_generation import Asset, AssetEvaluation, AssetVersion
from repositories.asset_generation_repository import (
    AssetEvaluationRepository,
    AssetRepository,
    AssetVersionRepository,
    RetryQueueRepository,
)
from database.models.asset_generation import RetryQueue


class QualityEvaluationService:
    """Evaluates assets and routes to accept/retry based on threshold."""

    def __init__(
        self,
        evaluation_repo: AssetEvaluationRepository,
        asset_repo: AssetRepository,
        version_repo: AssetVersionRepository,
        retry_repo: RetryQueueRepository,
        evaluation_provider,  # AssetEvaluationProvider
    ) -> None:
        self._eval_repo = evaluation_repo
        self._asset_repo = asset_repo
        self._version_repo = version_repo
        self._retry_repo = retry_repo
        self._evaluator = evaluation_provider

    async def evaluate_asset(
        self,
        asset: Asset,
        version: AssetVersion,
        prompt_text: str = "",
        style_type: str = "2d_cartoon",
        reference_character_data: dict[str, Any] | None = None,
        reference_background_data: dict[str, Any] | None = None,
    ) -> AssetEvaluation:
        """Evaluate a generated image and persist the result."""
        quality_threshold = asset.quality_threshold or 90.0

        request = EvaluationRequest(
            image_data=version.storage_key,
            image_format="storage_key",
            asset_type=asset.asset_type,
            prompt=prompt_text,
            negative_prompt="",
            style=style_type,
            reference_character_data=reference_character_data or dict(asset.consistency_fingerprint),
            reference_background_data=reference_background_data or {},
            quality_threshold=quality_threshold,
        )

        result = await self._evaluator.evaluate(request)

        evaluation = AssetEvaluation(
            asset_id=asset.id,
            version_id=version.id,
            overall_score=result.overall_score,
            prompt_quality=result.prompt_quality,
            image_quality=result.image_quality,
            character_consistency=result.character_consistency,
            background_consistency=result.background_consistency,
            composition_score=result.composition_score,
            lighting_score=result.lighting_score,
            style_match=result.style_match,
            scene_match=result.scene_match,
            resolution_score=result.resolution_score,
            artifact_score=result.artifact_score,
            hands_score=result.hands_score,
            face_score=result.face_score,
            text_error_score=result.text_error_score,
            passed_threshold=result.passed,
            failure_reasons=result.failure_reasons,
            notes=result.notes,
            evaluated_by=getattr(self._evaluator, "provider_name", "mock"),
            raw_scores=result.raw_scores,
        )
        evaluation = await self._eval_repo.create(evaluation)

        # Update version quality score
        version.quality_score = result.overall_score
        version.evaluation_scores = result.to_dict()
        if result.passed:
            version.is_approved = True
        else:
            version.is_rejected = True
            version.rejection_reason = "; ".join(result.failure_reasons)
        await self._version_repo._session.flush()

        # Accept or queue for retry
        if result.passed:
            await self._accept_asset(asset, version, result.overall_score)
        else:
            await self._queue_retry(asset, result.failure_reasons, result.overall_score)

        return evaluation

    async def _accept_asset(self, asset: Asset, version: AssetVersion, score: float) -> None:
        asset.status = "completed"
        asset.quality_score = score
        asset.best_version_id = version.id
        asset.generated_at = datetime.now(timezone.utc)
        await self._asset_repo._session.flush()

    async def _queue_retry(
        self,
        asset: Asset,
        failure_reasons: list[str],
        score: float,
    ) -> None:
        if asset.retry_count >= asset.max_retries:
            asset.status = "failed"
            await self._asset_repo._session.flush()
            return

        asset.status = "retrying"
        asset.retry_count += 1
        await self._asset_repo._session.flush()

        primary_reason = failure_reasons[0] if failure_reasons else "low_quality"
        entry = RetryQueue(
            asset_id=asset.id,
            project_id=asset.project_id,
            failure_reason=primary_reason,
            failure_details="; ".join(failure_reasons),
            quality_score=score,
            retry_count=asset.retry_count,
            max_retries=asset.max_retries,
            status="pending",
            priority=max(1, 10 - asset.retry_count),
        )
        await self._retry_repo.create(entry)
