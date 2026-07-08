"""
ResearchProvider Interface — collects research content for a given topic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ArticleResult:
    title: str
    url: str
    content: str
    summary: str
    author: str = ""
    published_at: datetime | None = None
    source_type: str = "rss"
    language: str = "en"
    quality_score: float = 0.5
    relevance_score: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchResult:
    topic: str
    articles: list[ArticleResult] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    quality_score: float = 0.0


class ResearchProvider(ABC):
    """Interface for all research content providers."""

    @abstractmethod
    async def research_topic(
        self,
        topic: str,
        keywords: list[str] | None = None,
        max_articles: int = 10,
        language: str = "en",
    ) -> ResearchResult:
        """Research a topic and return structured results."""
        ...

    @abstractmethod
    async def is_available(self) -> bool: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...
