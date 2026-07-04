"""
Image Provider Interface — abstract contract for all image generation backends.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 1024
    height: int = 576
    steps: int = 20
    guidance_scale: float = 7.5
    seed: int = -1
    style_hints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageEditRequest:
    source_image_bytes: bytes
    prompt: str
    mask_bytes: bytes | None = None
    strength: float = 0.75
    negative_prompt: str = ""
    steps: int = 20
    guidance_scale: float = 7.5


@dataclass
class ImageUpscaleRequest:
    source_image_bytes: bytes
    scale_factor: int = 2
    model: str = "default"


@dataclass
class ImageGenerationResult:
    image_bytes: bytes
    width: int
    height: int
    format: str
    model: str
    seed: int = -1
    metadata: dict[str, Any] = field(default_factory=dict)


class ImageProvider(ABC):
    """Interface for all image generation / editing providers."""

    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate an image from a text prompt."""
        ...

    async def edit_image(self, request: ImageEditRequest) -> ImageGenerationResult:
        """
        Edit an existing image guided by a prompt.
        Default: raises NotImplementedError — override in providers that support it.
        """
        raise NotImplementedError(f"{self.provider_name} does not support image editing")

    async def upscale(self, request: ImageUpscaleRequest) -> ImageGenerationResult:
        """
        Upscale an image by a given factor.
        Default: raises NotImplementedError — override in providers that support it.
        """
        raise NotImplementedError(f"{self.provider_name} does not support upscaling")

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    # Backward-compat alias so existing code calling .generate() still works
    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        return await self.generate_image(request)
