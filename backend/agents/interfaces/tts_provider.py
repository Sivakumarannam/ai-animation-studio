from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TTSRequest:
    text: str
    language: str = "en"
    voice_id: str = ""
    speed: float = 1.0
    pitch: float = 0.0
    output_format: str = "wav"


@dataclass
class TTSResult:
    audio_bytes: bytes
    duration_seconds: float
    format: str
    sample_rate: int
    metadata: dict[str, Any]


class TTSProvider(ABC):
    """Interface for Text-to-Speech providers."""

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Convert text to speech audio."""
        ...

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[dict[str, Any]]:
        """List available voices, optionally filtered by language."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
