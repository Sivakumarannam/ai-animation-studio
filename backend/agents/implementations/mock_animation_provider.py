"""
Phase 7 — Mock Animation Provider.

Returns deterministic synthetic results with zero external dependencies.
Follows the same pattern as MockImageProvider (Phase 6).
"""
from __future__ import annotations

import hashlib
import time
from typing import Any

from agents.interfaces.animation_provider import (
    AnimationProvider,
    AnimationRenderRequest,
    AnimationRenderResult,
)


class MockAnimationProvider(AnimationProvider):
    """
    Zero-dependency mock that returns a small synthetic video placeholder.
    Deterministic: the same request always returns the same storage_key hash.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def render_scene(self, request: AnimationRenderRequest) -> AnimationRenderResult:
        # Deterministic key derived from scene_id + character count
        fingerprint = f"{request.scene_id}:{len(request.characters)}:{request.duration_seconds}"
        storage_key = f"animations/mock/{request.project_id}/scene_{request.scene_id}_{hashlib.md5(fingerprint.encode()).hexdigest()[:8]}.mp4"

        # Minimal valid fMP4 header (8 bytes) as placeholder — never decoded in dev
        placeholder_bytes = b"\x00\x00\x00\x08ftyp"

        return AnimationRenderResult(
            video_bytes=placeholder_bytes,
            storage_key=storage_key,
            duration_seconds=request.duration_seconds,
            file_size_bytes=len(placeholder_bytes),
            width=request.width,
            height=request.height,
            fps=request.fps,
            format=request.output_format,
            provider=self.provider_name,
            metadata={
                "scene_id": request.scene_id,
                "characters": len(request.characters),
                "camera_motion": request.camera_motion,
                "dialogue_segments": len(request.dialogue_segments),
                "mock": True,
            },
        )

    async def is_available(self) -> bool:
        return True
