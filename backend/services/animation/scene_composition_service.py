"""
Phase 7 — SceneCompositionService (animation layer).

Takes Phase 6 image assets and composites them into animated scene clips.
Uses the AnimationProvider (mock or FFmpeg-backed) to produce video output.

FIX (2026-07-18): After calling the provider, if video_bytes are non-empty,
the service now uploads them to MinIO under the provider's storage_key.
Previously the bytes were silently discarded and only the key was stored in
the DB, leaving nothing in MinIO for Phase 10 to download.  Phase 6 images
and Phase 9 music both upload real bytes; this brings animation into parity.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from agents.interfaces.animation_provider import (
    AnimationProvider,
    AnimationRenderRequest,
    CharacterPlacement,
)
from database.models.animation_engine import AnimationJob, AnimationRenderOutput
from repositories.animation_engine_repository import AnimationRenderOutputRepository

logger = structlog.get_logger()

# MinIO bucket used for animation scene clips.
_ANIMATION_BUCKET = "animations"


class SceneCompositionService:
    """
    Converts a scene's Phase 6 assets into an animated clip.

    Responsibilities:
    - Build an AnimationRenderRequest from scene data (background, characters, timing)
    - Call the AnimationProvider
    - Persist the AnimationRenderOutput record
    """

    def __init__(
        self,
        output_repo: AnimationRenderOutputRepository,
        animation_provider: AnimationProvider,
    ) -> None:
        self._outputs = output_repo
        self._provider = animation_provider

    async def render_scene(
        self,
        job: AnimationJob,
        scene_data: dict[str, Any],
    ) -> AnimationRenderOutput:
        """
        Render a single scene into an animated clip.

        scene_data keys:
          - background_storage_key: str
          - characters: list[{character_id, asset_storage_key, position_x, position_y,
                               scale, expression, pose}]
          - duration_seconds: float (from dialogue duration or explicit)
          - camera_motion: str
          - dialogue_segments: list[{start_ms, end_ms, text}]
          - fps: int
          - width: int
          - height: int
        """
        characters = [
            CharacterPlacement(
                character_id=c.get("character_id", ""),
                asset_storage_key=c.get("asset_storage_key", ""),
                position_x=float(c.get("position_x", 0.5)),
                position_y=float(c.get("position_y", 0.8)),
                scale=float(c.get("scale", 1.0)),
                expression=c.get("expression", "idle"),
                pose=c.get("pose", "idle"),
                z_index=int(c.get("z_index", 1)),
            )
            for c in scene_data.get("characters", [])
        ]

        request = AnimationRenderRequest(
            project_id=str(job.project_id),
            scene_id=str(job.scene_id) if job.scene_id else "",
            background_storage_key=scene_data.get("background_storage_key", ""),
            characters=characters,
            duration_seconds=float(scene_data.get("duration_seconds", 5.0)),
            fps=int(scene_data.get("fps", 24)),
            width=int(scene_data.get("width", 1920)),
            height=int(scene_data.get("height", 1080)),
            output_format=scene_data.get("output_format", "mp4"),
            camera_motion=scene_data.get("camera_motion", "static"),
            transition_in=scene_data.get("transition_in", "cut"),
            transition_out=scene_data.get("transition_out", "cut"),
            dialogue_segments=scene_data.get("dialogue_segments", []),
            extra=scene_data.get("extra", {}),
        )

        logger.info("scene_render_start",
                    job_id=str(job.id), scene_id=str(job.scene_id),
                    provider=self._provider.provider_name)

        render_result = await self._provider.render_scene(request)

        # ------------------------------------------------------------------
        # Upload video bytes to MinIO so Phase 10 assembly can download them.
        # Previously this step was missing: only the storage_key string was
        # saved to the DB while the actual bytes were discarded, leaving nothing
        # in MinIO for FFmpeg to read.  Phase 6 images and Phase 9 music both
        # upload real bytes; animation must do the same.
        # ------------------------------------------------------------------
        if render_result.video_bytes:
            try:
                from plugins.storage.minio_storage import MinIOStorage
                storage = MinIOStorage.from_settings(bucket=_ANIMATION_BUCKET)
                storage.upload_bytes(
                    _ANIMATION_BUCKET,
                    render_result.storage_key,
                    render_result.video_bytes,
                    content_type="video/mp4",
                )
                logger.info(
                    "scene_render_uploaded",
                    job_id=str(job.id),
                    storage_key=render_result.storage_key,
                    bytes_uploaded=len(render_result.video_bytes),
                )
            except Exception as exc:
                # Upload failure is logged but must not silently hide the error —
                # raise so the job is marked failed instead of appearing successful
                # with an empty MinIO object behind it.
                logger.error(
                    "scene_render_upload_failed",
                    job_id=str(job.id),
                    storage_key=render_result.storage_key,
                    error=str(exc),
                )
                raise

        output = AnimationRenderOutput(
            job_id=job.id,
            project_id=job.project_id,
            scene_id=job.scene_id,
            episode_id=job.episode_id,
            output_type="scene_clip",
            status="completed",
            storage_key=render_result.storage_key,
            storage_bucket=_ANIMATION_BUCKET,
            file_size_bytes=render_result.file_size_bytes,
            duration_seconds=render_result.duration_seconds,
            width=render_result.width,
            height=render_result.height,
            fps=render_result.fps,
            format=render_result.format,
            provider=render_result.provider,
            render_params={
                "camera_motion": request.camera_motion,
                "character_count": len(characters),
                "dialogue_segments": len(request.dialogue_segments),
            },
            metadata_=render_result.metadata,
        )
        saved = await self._outputs.create(output)

        logger.info("scene_render_complete",
                    job_id=str(job.id), output_id=str(saved.id),
                    storage_key=render_result.storage_key)
        return saved
