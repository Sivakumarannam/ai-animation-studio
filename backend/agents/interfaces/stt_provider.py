"""
Speech-to-Text (STT) Provider Interface.
Separate from SubtitleProvider — STT converts raw audio to text/words,
while SubtitleProvider produces timed caption segments.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class STTRequest:
    audio_bytes: bytes
    language: str | None = None
    sample_rate: int = 16000
    audio_format: str = "wav"
    task: str = "transcribe"  # "transcribe" | "translate"


@dataclass
class STTWord:
    word: str
    start_seconds: float
    end_seconds: float
    confidence: float = 1.0


@dataclass
class STTResult:
    text: str
    language: str
    words: list[STTWord] = field(default_factory=list)
    confidence: float = 1.0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class STTProvider(ABC):
    """Interface for all Speech-to-Text providers."""

    @abstractmethod
    async def transcribe(self, request: STTRequest) -> STTResult:
        """Convert audio bytes to text, optionally with word-level timestamps."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
