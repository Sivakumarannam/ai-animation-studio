from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SubtitleSegment:
    start_seconds: float
    end_seconds: float
    text: str
    language: str


@dataclass
class SubtitleResult:
    segments: list[SubtitleSegment]
    full_text: str
    language: str
    metadata: dict[str, Any]


class SubtitleProvider(ABC):
    """Interface for speech-to-text / subtitle generation providers."""

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str | None = None,
        output_format: str = "srt",
    ) -> SubtitleResult:
        """Transcribe audio bytes into subtitle segments."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
