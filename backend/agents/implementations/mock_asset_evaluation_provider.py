"""
Phase 6 — Mock Asset Evaluation Provider.

Deterministic, zero-dependency evaluator for testing and development.
Returns realistic scores derived from the input prompt length and asset type
so the pipeline exercises all code paths without requiring real image models.
"""
from __future__ import annotations

import hashlib

from agents.interfaces.asset_evaluation_provider import (
    AssetEvaluationProvider,
    EvaluationRequest,
    EvaluationResult,
)


class MockAssetEvaluationProvider(AssetEvaluationProvider):
    """Deterministic mock evaluator.

    Score is seeded from the SHA-256 of (prompt + asset_type) so the same
    inputs always produce the same score — unit tests are fully reproducible.
    Score is biased toward passing the 90-point threshold so development
    pipelines complete successfully without constant retries.
    """

    @property
    def provider_name(self) -> str:
        return "mock/asset-evaluator-v1"

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        # deterministic seed from prompt hash
        seed_input = (request.prompt + request.asset_type).encode()
        digest = int(hashlib.sha256(seed_input).hexdigest()[:8], 16)
        # map 0..0xFFFFFFFF → 88..100  (biased high so pipeline succeeds)
        base_score = 88.0 + (digest % 0xFFFF) / 0xFFFF * 12.0

        def _dim(offset: int) -> float:
            """Derive a per-dimension score with slight variation."""
            return round(min(100.0, max(60.0, base_score + (offset % 7) - 3)), 2)

        overall = round(base_score, 2)
        passed = overall >= request.quality_threshold

        return EvaluationResult(
            overall_score=overall,
            passed=passed,
            prompt_quality=_dim(1),
            image_quality=_dim(2),
            character_consistency=_dim(3),
            background_consistency=_dim(4),
            composition_score=_dim(5),
            lighting_score=_dim(6),
            style_match=_dim(7),
            scene_match=_dim(8),
            resolution_score=_dim(9),
            artifact_score=_dim(10),
            hands_score=_dim(11),
            face_score=_dim(12),
            text_error_score=_dim(13),
            failure_reasons=[] if passed else ["score_below_threshold"],
            notes=f"mock evaluation — score={overall:.1f} threshold={request.quality_threshold}",
            raw_scores={"provider": self.provider_name, "seed": digest},
        )
