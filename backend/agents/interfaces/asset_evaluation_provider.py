"""
Phase 6 — Asset Evaluation Provider interface.

Implementations evaluate a generated image against a set of criteria and
return a structured quality score with per-dimension breakdowns.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationRequest:
    """Input to the evaluator."""
    # Path or base64-encoded image data (provider decides)
    image_data: str                         # base64-encoded PNG/JPEG or storage key
    image_format: str = "storage_key"       # "base64" | "storage_key"
    asset_type: str = "character"           # "character" | "background" | "prop" | etc.
    prompt: str = ""                        # positive prompt that was used
    negative_prompt: str = ""
    style: str = "2d_cartoon"
    # optional reference for consistency checks
    reference_character_data: dict[str, Any] = field(default_factory=dict)
    reference_background_data: dict[str, Any] = field(default_factory=dict)
    quality_threshold: float = 90.0
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Output from the evaluator."""
    overall_score: float = 0.0
    passed: bool = False

    # per-dimension scores (0–100)
    prompt_quality: float = 0.0
    image_quality: float = 0.0
    character_consistency: float = 0.0
    background_consistency: float = 0.0
    composition_score: float = 0.0
    lighting_score: float = 0.0
    style_match: float = 0.0
    scene_match: float = 0.0
    resolution_score: float = 0.0
    artifact_score: float = 0.0
    hands_score: float = 0.0
    face_score: float = 0.0
    text_error_score: float = 0.0

    failure_reasons: list[str] = field(default_factory=list)
    notes: str = ""
    raw_scores: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "passed": self.passed,
            "prompt_quality": self.prompt_quality,
            "image_quality": self.image_quality,
            "character_consistency": self.character_consistency,
            "background_consistency": self.background_consistency,
            "composition_score": self.composition_score,
            "lighting_score": self.lighting_score,
            "style_match": self.style_match,
            "scene_match": self.scene_match,
            "resolution_score": self.resolution_score,
            "artifact_score": self.artifact_score,
            "hands_score": self.hands_score,
            "face_score": self.face_score,
            "text_error_score": self.text_error_score,
            "failure_reasons": self.failure_reasons,
            "notes": self.notes,
            "raw_scores": self.raw_scores,
        }


class AssetEvaluationProvider(ABC):
    """Evaluate a generated image and return a quality score breakdown."""

    @abstractmethod
    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        """Evaluate the image and return detailed scores."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
