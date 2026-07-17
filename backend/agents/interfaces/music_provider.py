"""
Phase 9 — Music Provider interface.

Abstracts the music/SFX generation backend: mock (dev) or real provider
(Suno, Udio, MusicGen, etc.).
Mirrors AnimationProvider / VoiceProvider shape exactly (Phase 7-8 pattern).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MusicGenerationRequest:
    """Input to the music provider for a single background track or SFX mix."""
    project_id: str
    mood: str              # comedy | adventure | sad | happy | tension | victory | neutral
    scene_id: str = ""     # empty string if generating for a full episode / not scene-specific
    duration_seconds: float = 30.0
    output_format: str = "wav"
    # "looping" | "one_shot"
    loop_type: str = "looping"
    # Descriptive prompt to guide generation (e.g. "upbeat comedy background")
    prompt: str = ""
    # BPM hint (0 = let provider decide)
    bpm: int = 0
    # Instrumentation hints: ["piano", "strings", "drums"]
    instruments: list[str] = field(default_factory=list)
    # Extra params for real providers (API-specific)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MusicGenerationResult:
    """Output from the music provider for a single track."""
    audio_bytes: bytes        # Raw audio data (empty for mock)
    storage_key: str          # Where it was (or would be) stored
    duration_seconds: float
    sample_rate: int
    format: str
    file_size_bytes: int
    copyright_safe: bool
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MusicProvider(ABC):
    """Base interface for music/SFX generation backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def generate_track(self, request: MusicGenerationRequest) -> MusicGenerationResult:
        """Generate a mood-matched background track."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider is ready to accept requests."""
        ...
