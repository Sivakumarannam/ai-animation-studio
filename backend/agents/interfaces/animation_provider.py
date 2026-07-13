"""
Phase 7 — Animation Provider interface.

Abstracts the compositing/rendering backend: mock (dev) or FFmpeg (production).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CharacterPlacement:
    """A character placed in a scene with position, expression, and pose."""
    character_id: str
    asset_storage_key: str         # Phase 6 generated image
    position_x: float = 0.5       # 0.0–1.0 of canvas width
    position_y: float = 0.8       # 0.0–1.0 of canvas height
    scale: float = 1.0
    expression: str = "idle"
    pose: str = "idle"
    z_index: int = 1


@dataclass
class AnimationRenderRequest:
    """Input to the animation provider for a single scene clip."""
    project_id: str
    scene_id: str
    background_storage_key: str    # Phase 6 background image
    characters: list[CharacterPlacement] = field(default_factory=list)
    # duration: computed from dialogue length or explicit value
    duration_seconds: float = 5.0
    fps: int = 24
    width: int = 1920
    height: int = 1080
    output_format: str = "mp4"
    # Camera motion: "static" | "pan_left" | "pan_right" | "zoom_in" | "zoom_out"
    camera_motion: str = "static"
    # Transition: "cut" | "fade" | "dissolve"
    transition_in: str = "cut"
    transition_out: str = "cut"
    # Lip-sync timing placeholder: list of {start_ms, end_ms, text}
    dialogue_segments: list[dict[str, Any]] = field(default_factory=list)
    # Extra params for real providers
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnimationRenderResult:
    """Output from the animation provider."""
    video_bytes: bytes            # Raw video data (empty for mock)
    storage_key: str              # Where it was (or would be) stored
    duration_seconds: float
    file_size_bytes: int
    width: int
    height: int
    fps: int
    format: str
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AnimationProvider(ABC):
    """Base interface for animation rendering backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def render_scene(self, request: AnimationRenderRequest) -> AnimationRenderResult:
        """Composite images + motion into a scene clip."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider is ready to accept requests."""
        ...
