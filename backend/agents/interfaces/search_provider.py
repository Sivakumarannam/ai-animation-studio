"""
SearchProvider Interface — searches the web for relevant content.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResultItem:
    title: str
    url: str
    snippet: str
    source: str = ""
    relevance_score: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


class SearchProvider(ABC):
    """Interface for all web search providers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "en",
        safe_search: bool = True,
    ) -> list[SearchResultItem]:
        """Search and return ranked results."""
        ...

    @abstractmethod
    async def is_available(self) -> bool: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...
