"""
TrendProvider Interface — discovers trending topics from external sources.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrendResult:
    keyword: str
    normalized_keyword: str
    category: str = "general"
    region: str = "global"
    language: str = "en"
    trend_score: float = 0.0
    velocity: float = 0.0
    growth_rate: float = 0.0
    popularity_index: float = 0.0
    is_emerging: bool = False
    is_declining: bool = False
    raw_data: dict[str, Any] = field(default_factory=dict)
    source_name: str = ""


class TrendProvider(ABC):
    """Interface for all trend discovery providers."""

    @abstractmethod
    async def discover_trends(
        self,
        categories: list[str] | None = None,
        region: str = "global",
        language: str = "en",
        limit: int = 50,
    ) -> list[TrendResult]:
        """Discover trending topics. Returns a list of TrendResult."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider is reachable."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...
