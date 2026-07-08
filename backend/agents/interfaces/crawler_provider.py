"""
CrawlerProvider Interface — fetches and extracts text from URLs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    content_type: str = "text/html"
    language: str = "en"
    word_count: int = 0
    success: bool = True
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class CrawlerProvider(ABC):
    """Interface for all web crawler/content-extraction providers."""

    @abstractmethod
    async def crawl(self, url: str, timeout_seconds: int = 10) -> CrawlResult:
        """Fetch a URL and extract clean text content."""
        ...

    @abstractmethod
    async def crawl_many(
        self,
        urls: list[str],
        timeout_seconds: int = 10,
        max_concurrent: int = 5,
    ) -> list[CrawlResult]:
        """Crawl multiple URLs concurrently."""
        ...

    @abstractmethod
    async def is_available(self) -> bool: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...
