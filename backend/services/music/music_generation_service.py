"""
Phase 9 — MusicGenerationService.
Calls the MusicProvider for a single track and persists a MusicOutput record.
Mirrors LineSynthesisService / SceneCompositionService from Phases 7-8.
"""
from __future__ import annotations

import uuid
from typing import Any

import structlog

from agents.interfaces.music_provider import MusicGenerationRequest, MusicProvider
from database.models.music_engine import MusicGenerationJob, MusicOutput
from repositories.music_engine_repository import MusicOutputRepository

logger = structlog.get_logger()


class MusicGenerationService:
    def __init__(self, output_repo: MusicOutputRepository, provider: MusicProvider) -> None:
        self._outputs = output_repo
        self._provider = provider

    async def generate_track(
        self,
        job: MusicGenerationJob,
        params: dict[str, Any],
    ) -> MusicOutput:
        """
        Generate a mood-matched background track via the provider and save the output.
        """
        request = MusicGenerationRequest(
            project_id=str(job.project_id),
            scene_id=str(job.scene_id) if job.scene_id else "",
            mood=params.get("mood", job.mood),
            duration_seconds=float(params.get("duration_seconds", 30.0)),
            output_format=params.get("output_format", "wav"),
            loop_type=params.get("loop_type", "looping"),
            prompt=params.get("prompt", ""),
            bpm=int(params.get("bpm", 0)),
            instruments=params.get("instruments", []),
            extra=params.get("extra_params", {}),
        )

        logger.info(
            "music_generate_start",
            job_id=str(job.id),
            mood=request.mood,
            provider=self._provider.provider_name,
        )

        result = await self._provider.generate_track(request)

        output = MusicOutput(
            job_id=job.id,
            project_id=job.project_id,
            scene_id=job.scene_id,
            episode_id=job.episode_id,
            output_type=params.get("output_type", "background_music"),
            mood=request.mood,
            loop_type=request.loop_type,
            storage_key=result.storage_key,
            duration_seconds=result.duration_seconds,
            sample_rate=result.sample_rate,
            format=result.format,
            file_size_bytes=result.file_size_bytes,
            provider=result.provider,
            copyright_safe=result.copyright_safe,
            status="completed",
            output_metadata=result.metadata,
        )
        saved = await self._outputs.create(output)

        logger.info(
            "music_generate_complete",
            job_id=str(job.id),
            output_id=str(saved.id),
            storage_key=result.storage_key,
        )
        return saved
