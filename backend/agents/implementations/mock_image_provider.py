"""
MockImageProvider — deterministic, zero-dependency image provider for
development and testing. No external ComfyUI server or GPU required.

Renders a simple, deterministic placeholder PNG (solid color derived from a
hash of the prompt, plus the requested dimensions burned into the pixel
data) so that:
  - The same prompt + size always produces the same image (deterministic).
  - The full asset-generation pipeline (dispatch -> generate -> store ->
    evaluate -> version) can be exercised end-to-end without a real
    ComfyUI/SDXL backend.
"""
from __future__ import annotations

import hashlib
import io

from PIL import Image, ImageDraw

from agents.interfaces.image_provider import (
    ImageEditRequest,
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageProvider,
    ImageUpscaleRequest,
)

_MOCK_MODEL = "mock/placeholder-v1"


class MockImageProvider(ImageProvider):
    """Renders deterministic placeholder images instead of calling a real
    image generation backend."""

    @property
    def provider_name(self) -> str:
        return _MOCK_MODEL

    async def is_available(self) -> bool:
        return True

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        digest = hashlib.sha256(request.prompt.encode("utf-8")).digest()
        color = (digest[0], digest[1], digest[2])
        seed = request.seed if request.seed >= 0 else int.from_bytes(digest[3:7], "big") % (2**31)

        img = Image.new("RGB", (request.width, request.height), color=color)
        draw = ImageDraw.Draw(img)
        label = request.prompt[:60]
        draw.rectangle(
            [(0, 0), (request.width - 1, request.height - 1)],
            outline=(255, 255, 255),
            width=4,
        )
        draw.text((16, 16), label, fill=(255, 255, 255))
        draw.text((16, request.height - 32), f"seed={seed}", fill=(255, 255, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")

        return ImageGenerationResult(
            image_bytes=buf.getvalue(),
            width=request.width,
            height=request.height,
            format="png",
            model=_MOCK_MODEL,
            seed=seed,
            metadata={"mock": True, "prompt": request.prompt},
        )

    async def edit_image(self, request: ImageEditRequest) -> ImageGenerationResult:
        img = Image.open(io.BytesIO(request.source_image_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.text((16, 16), f"edit: {request.prompt[:40]}", fill=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ImageGenerationResult(
            image_bytes=buf.getvalue(),
            width=img.width,
            height=img.height,
            format="png",
            model=_MOCK_MODEL,
            metadata={"mock": True, "edited": True},
        )

    async def upscale(self, request: ImageUpscaleRequest) -> ImageGenerationResult:
        img = Image.open(io.BytesIO(request.source_image_bytes)).convert("RGB")
        new_size = (img.width * request.scale_factor, img.height * request.scale_factor)
        img = img.resize(new_size)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ImageGenerationResult(
            image_bytes=buf.getvalue(),
            width=img.width,
            height=img.height,
            format="png",
            model=_MOCK_MODEL,
            metadata={"mock": True, "upscaled": True},
        )
