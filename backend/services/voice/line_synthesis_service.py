"""
Phase 8 — LineSynthesisService.
Calls the VoiceProvider for a single dialogue line and persists a VoiceOutput record.
Mirrors SceneCompositionService from Phase 7 exactly.
"""
from __future__ import annotations

import uuid
from typing import Any

from agents.interfaces.voice_provider import VoiceGenerationRequest, VoiceProvider
from database.models.voice_engine import VoiceGenerationJob, VoiceOutput
from repositories.voice_engine_repository import VoiceOutputRepository


class LineSynthesisService:
    def __init__(self, output_repo: VoiceOutputRepository, provider: VoiceProvider) -> None:
        self._output_repo = output_repo
        self._provider = provider

    async def synthesize_line(
        self,
        job: VoiceGenerationJob,
        line_data: dict[str, Any],
    ) -> VoiceOutput:
        """
        Synthesize one dialogue line and persist the output record.

        line_data keys (all optional except dialogue_line):
          character_id, character_name, dialogue_line, language,
          voice_id, emotion, speed, pitch, output_format, voice_seed
        """
        request = VoiceGenerationRequest(
            project_id=str(job.project_id),
            scene_id=str(job.scene_id) if job.scene_id else "",
            character_id=line_data.get("character_id", ""),
            character_name=line_data.get("character_name", ""),
            dialogue_line=line_data.get("dialogue_line", ""),
            language=line_data.get("language", "en"),
            voice_id=line_data.get("voice_id", ""),
            emotion=line_data.get("emotion", "neutral"),
            speed=float(line_data.get("speed", 1.0)),
            pitch=float(line_data.get("pitch", 0.0)),
            output_format=line_data.get("output_format", "wav"),
            voice_seed=int(line_data.get("voice_seed", 0)),
        )

        result = await self._provider.generate_line(request)

        output = VoiceOutput(
            job_id=job.id,
            project_id=job.project_id,
            scene_id=job.scene_id,
            character_id=request.character_id or None,
            character_name=request.character_name or None,
            dialogue_line=request.dialogue_line,
            language=request.language,
            emotion=request.emotion,
            voice_id=request.voice_id or None,
            storage_key=result.storage_key,
            duration_seconds=result.duration_seconds,
            sample_rate=result.sample_rate,
            format=result.format,
            file_size_bytes=result.file_size_bytes,
            provider=result.provider,
            status="completed",
            output_metadata=result.metadata,
        )
        return await self._output_repo.create(output)
