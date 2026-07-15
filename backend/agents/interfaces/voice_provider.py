"""
Phase 8 — Voice Provider interface.

Abstracts the TTS/voice synthesis backend: mock (dev) or Piper (production).
Mirrors AnimationProvider shape exactly (Phase 7 pattern that worked first try).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VoiceGenerationRequest:
    """Input to the voice provider for a single dialogue line."""
    project_id: str
    scene_id: str
    character_id: str
    character_name: str
    dialogue_line: str
    language: str = "en"
    voice_id: str = ""
    emotion: str = "neutral"        # neutral | happy | sad | angry | fearful | surprised
    speed: float = 1.0
    pitch: float = 0.0
    output_format: str = "wav"
    # Per-character voice consistency seed — same character → same voice fingerprint
    voice_seed: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceGenerationResult:
    """Output from the voice provider for a single dialogue line."""
    audio_bytes: bytes            # Raw audio data (empty for mock)
    storage_key: str              # Where it was (or would be) stored
    duration_seconds: float
    sample_rate: int
    format: str
    file_size_bytes: int
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


class VoiceProvider(ABC):
    """Base interface for voice/TTS synthesis backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def generate_line(self, request: VoiceGenerationRequest) -> VoiceGenerationResult:
        """Synthesize a single dialogue line to audio."""
        ...

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[dict[str, Any]]:
        """List available voices, optionally filtered by language."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider is ready to accept requests."""
        ...
