"""
Phase 6 — Image Generation Service.

Orchestrates image generation through the ImageProvider (ComfyUI / mock),
stores the raw GeneratedImage record, uploads to MinIO, and updates the
Asset and AssetVersion records.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from agents.interfaces.image_provider import ImageGenerationRequest
from database.models.asset_generation import GeneratedAsset as Asset, AssetPrompt, GeneratedAssetVersion as AssetVersion, GeneratedImage
from repositories.asset_generation_repository import (
    AssetRepository,
    AssetVersionRepository,
    GeneratedImageRepository,
)


class ImageGenerationService:
    """Generates images via the ImageProvider and persists version records."""

    def __init__(
        self,
        asset_repo: AssetRepository,
        version_repo: AssetVersionRepository,
        image_repo: GeneratedImageRepository,
        image_provider,               # agents.interfaces.image_provider.ImageProvider
        storage=None,                 # plugins.storage.minio_storage.MinIOStorage
    ) -> None:
        self._asset_repo = asset_repo
        self._version_repo = version_repo
        self._image_repo = image_repo
        self._provider = image_provider
        self._storage = storage

    async def generate_for_asset(
        self,
        asset: Asset,
        prompt: AssetPrompt,
        generation_params: dict[str, Any] | None = None,
    ) -> tuple[AssetVersion, GeneratedImage]:
        """
        Generate one image for the asset using the given prompt.
        Returns the AssetVersion and GeneratedImage records.
        """
        params = generation_params or {}
        width_str, height_str = _parse_resolution(params.get("resolution", "1024x1024"))
        steps = int(params.get("steps", 20))
        cfg = float(params.get("cfg_scale", 7.0))
        sampler = params.get("sampler", "euler_a")
        seed = int(params.get("seed", _deterministic_seed(prompt.full_prompt)))

        # Call the image provider. ImageProvider.generate_image() takes a single
        # ImageGenerationRequest and returns an ImageGenerationResult — both are
        # dataclasses defined on the interface (agents/interfaces/image_provider.py).
        # `sampler` has no equivalent field on ImageGenerationRequest; it's only
        # persisted locally in generation_params below.
        try:
            start_ms = _now_ms()
            request = ImageGenerationRequest(
                prompt=prompt.full_prompt,
                negative_prompt=prompt.full_negative_prompt,
                width=width_str,
                height=height_str,
                steps=steps,
                guidance_scale=cfg,
                seed=seed,
            )
            gen_result = await self._provider.generate_image(request)
            duration_ms = _now_ms() - start_ms
        except Exception as exc:
            # Provider error — propagate with context
            raise RuntimeError(f"Image provider failed for asset {asset.id}: {exc}") from exc

        # Provider returns an ImageGenerationResult dataclass.
        image_data: bytes = gen_result.image_bytes
        actual_width: int = gen_result.width
        actual_height: int = gen_result.height
        actual_seed: int = gen_result.seed if gen_result.seed >= 0 else seed
        provider_job_id: str = str(gen_result.metadata.get("prompt_id", ""))

        # Storage key (MinIO object path)
        storage_key = _make_storage_key(asset, prompt)

        # Upload the generated image bytes to MinIO so it can actually be
        # viewed later (via the /assets/file/{storage_key} endpoint). Mirrors
        # the upload pattern used for user-uploaded assets in
        # apps/api/routers/asset_manager.py::upload_asset_file.
        if self._storage is not None:
            self._storage.upload_bytes(
                bucket="assets",
                key=storage_key,
                data=image_data,
                content_type="image/png",
            )

        # Persist GeneratedImage
        gen_image = GeneratedImage(
            asset_id=asset.id,
            storage_key=storage_key,
            storage_bucket="assets",
            width=actual_width,
            height=actual_height,
            file_size_bytes=len(image_data),
            mime_type="image/png",
            status="pending",
            generation_time_ms=duration_ms,
            provider=getattr(self._provider, "provider_name", "mock"),
            provider_job_id=provider_job_id,
            generation_params={
                "steps": steps,
                "cfg_scale": cfg,
                "sampler": sampler,
                "seed": actual_seed,
            },
            raw_metadata=dict(gen_result.metadata),
        )
        gen_image = await self._image_repo.create(gen_image)

        # Persist AssetVersion
        version_number = await self._version_repo.get_next_version_number(asset.id)
        version_label = "original" if version_number == 1 else f"revision_{version_number}"
        version = AssetVersion(
            asset_id=asset.id,
            prompt_id=prompt.id,
            version_number=version_number,
            version_label=version_label,
            storage_key=storage_key,
            storage_bucket="assets",
            width=actual_width,
            height=actual_height,
            file_size_bytes=len(image_data),
            generation_seed=actual_seed,
            generation_steps=steps,
            cfg_scale=cfg,
            sampler=sampler,
            generation_params={
                "steps": steps,
                "cfg_scale": cfg,
                "sampler": sampler,
                "seed": actual_seed,
                "provider": getattr(self._provider, "provider_name", "mock"),
            },
        )
        version = await self._version_repo.create(version)

        # Link image to version
        gen_image.version_id = version.id
        await self._image_repo._session.flush()

        # Update asset status
        asset.status = "evaluating"
        asset.version_count = version_number
        asset.current_version_id = version.id
        asset.storage_key = storage_key
        asset.width = actual_width
        asset.height = actual_height
        asset.file_size_bytes = len(image_data)
        asset.mime_type = "image/png"
        await self._asset_repo._session.flush()

        return version, gen_image


def _parse_resolution(resolution: str) -> tuple[int, int]:
    try:
        w, h = resolution.split("x")
        return int(w), int(h)
    except Exception:
        return 1024, 1024


def _deterministic_seed(prompt: str) -> int:
    return int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16) % (2**31)


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _make_storage_key(asset: Asset, prompt: AssetPrompt) -> str:
    short_hash = hashlib.sha256(prompt.full_prompt.encode()).hexdigest()[:8]
    return f"assets/{asset.project_id}/{asset.asset_type}/{asset.id}/{short_hash}.png"
