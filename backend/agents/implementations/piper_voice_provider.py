"""
Phase 8 — Piper Voice Provider.

Wraps the existing PiperTTSProvider (backend/agents/implementations/piper_provider.py)
behind the VoiceProvider interface. Selected via VO_VOICE_PROVIDER=piper.
"""
from __future__ import annotations

from typing import Any

from agents.interfaces.tts_provider import TTSRequest
from agents.interfaces.voice_provider import (
    VoiceGenerationRequest,
    VoiceGenerationResult,
    VoiceProvider,
)
from packages.core.exceptions import ProviderError


class PiperVoiceProvider(VoiceProvider):
    """
    Real voice provider backed by Piper TTS binary.

    Delegates to PiperTTSProvider for the actual synthesis; adds the
    storage_key and VoiceGenerationResult envelope expected by Phase 8.
    """

    def __init__(
        self,
        piper_binary: str = "piper",
        models_dir: str = "/models/piper",
    ) -> None:
        from agents.implementations.piper_provider import PiperTTSProvider

        self._piper = PiperTTSProvider(
            piper_binary=piper_binary,
            models_dir=models_dir,
        )

    @property
    def provider_name(self) -> str:
        return "piper"

    async def generate_line(self, request: VoiceGenerationRequest) -> VoiceGenerationResult:
        try:
            tts_result = await self._piper.synthesize(
                TTSRequest(
                    text=request.dialogue_line,
                    language=request.language,
                    voice_id=request.voice_id,
                    speed=request.speed,
                    pitch=request.pitch,
                    output_format=request.output_format,
                )
            )
        except Exception as exc:
            raise ProviderError("piper_voice", str(exc)) from exc

        import hashlib

        line_hash = hashlib.sha256(
            f"{request.project_id}:{request.scene_id}:{request.character_id}:{request.dialogue_line}:{request.voice_seed}".encode()
        ).hexdigest()[:16]
        storage_key = (
            f"voice/{request.project_id}/{request.scene_id}/"
            f"{request.character_id}/{line_hash}.{tts_result.format}"
        )

        return VoiceGenerationResult(
            audio_bytes=tts_result.audio_bytes,
            storage_key=storage_key,
            duration_seconds=tts_result.duration_seconds,
            sample_rate=tts_result.sample_rate,
            format=tts_result.format,
            file_size_bytes=len(tts_result.audio_bytes),
            provider=self.provider_name,
            metadata={
                "character_name": request.character_name,
                "emotion": request.emotion,
                "language": request.language,
                "voice_id": request.voice_id,
                **tts_result.metadata,
            },
        )

    async def list_voices(self, language: str | None = None) -> list[dict[str, Any]]:
        return await self._piper.list_voices(language)

    async def is_available(self) -> bool:
        return await self._piper.is_available()
