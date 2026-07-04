from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SEORequest:
    title: str
    description: str
    language: str = "en"
    genre: str = ""
    keywords_hint: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.keywords_hint is None:
            self.keywords_hint = []


@dataclass
class SEOResult:
    optimized_title: str
    optimized_description: str
    tags: list[str]
    hashtags: list[str]
    metadata: dict[str, Any]


class SEOProvider(ABC):
    """Interface for SEO metadata generation."""

    @abstractmethod
    async def generate(self, request: SEORequest) -> SEOResult:
        """Generate SEO metadata for a video."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
