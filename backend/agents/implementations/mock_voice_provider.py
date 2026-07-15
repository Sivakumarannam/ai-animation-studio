"""
Phase 8 — Mock Voice Provider.

Deterministic, zero-dependency TTS backend for development/testing.
Mirrors MockAnimationProvider shape exactly (Phase 7 pattern).
"""
from __future__ import annotations

import hashlib
from typing import Any

from agents.interfaces.voice_provider import (
    VoiceGenerationRequest,
    VoiceGenerationResult,
    VoiceProvider,
)


class MockVoiceProvider(VoiceProvider):
    """Deterministic mock that produces empty audio bytes with predictable metadata."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_line(self, request: VoiceGenerationRequest) -> VoiceGenerationResult:
        # Deterministic duration: ~0.05s per word, seeded by character + line
        words = len(request.dialogue_line.split()) if request.dialogue_line else 1
        duration = round(words * 0.05 * max(0.5, 1.0 / request.speed), 3)

        # Deterministic storage key based on project + scene + character + line hash
        line_hash = hashlib.sha256(
            f"{request.project_id}:{request.scene_id}:{request.character_id}:{request.dialogue_line}:{request.voice_seed}".encode()
        ).hexdigest()[:16]
        storage_key = (
            f"voice/{request.project_id}/{request.scene_id}/"
            f"{request.character_id}/{line_hash}.{request.output_format}"
        )

        return VoiceGenerationResult(
            audio_bytes=b"",  # mock: no real audio
            storage_key=storage_key,
            duration_seconds=duration,
            sample_rate=22050,
            format=request.output_format,
            file_size_bytes=0,
            provider=self.provider_name,
            metadata={
                "character_name": request.character_name,
                "emotion": request.emotion,
                "language": request.language,
                "voice_id": request.voice_id,
                "words": words,
                "voice_seed": request.voice_seed,
            },
        )

    async def list_voices(self, language: str | None = None) -> list[dict[str, Any]]:
        voices = [
            {"id": "narrator_m", "name": "Narrator (Male)", "language": "en", "gender": "male"},
            {"id": "narrator_f", "name": "Narrator (Female)", "language": "en", "gender": "female"},
            {"id": "child", "name": "Child", "language": "en", "gender": "neutral"},
            {"id": "narrator_te", "name": "Narrator Telugu", "language": "te", "gender": "male"},
        ]
        if language:
            voices = [v for v in voices if v["language"] == language]
        return voices

    async def is_available(self) -> bool:
        return True
