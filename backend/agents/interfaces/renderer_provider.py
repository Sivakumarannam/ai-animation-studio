from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SceneRenderSpec:
    scene_id: str
    background_url: str
    character_frames: list[dict[str, Any]]
    audio_url: str
    subtitle_segments: list[dict[str, Any]]
    duration_seconds: float
    resolution: tuple[int, int] = (1920, 1080)


@dataclass
class RenderRequest:
    story_id: str
    scenes: list[SceneRenderSpec]
    output_format: str = "mp4"
    fps: int = 24
    resolution: tuple[int, int] = (1920, 1080)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderResult:
    video_bytes: bytes
    duration_seconds: float
    file_size_bytes: int
    format: str
    resolution: tuple[int, int]
    metadata: dict[str, Any]


class RendererProvider(ABC):
    """Interface for video rendering providers."""

    @abstractmethod
    async def render(self, request: RenderRequest) -> RenderResult:
        """Render scenes into a video."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
