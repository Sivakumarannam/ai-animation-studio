"""
MockCrawlerProvider — deterministic URL crawling for development and testing.
"""
from __future__ import annotations

from agents.interfaces.crawler_provider import CrawlerProvider, CrawlResult


class MockCrawlerProvider(CrawlerProvider):
    @property
    def provider_name(self) -> str:
        return "mock/crawler-provider-v1"

    async def is_available(self) -> bool:
        return True

    async def crawl(self, url: str, timeout_seconds: int = 10) -> CrawlResult:
        # Extract a topic hint from the URL
        slug = url.rstrip("/").split("/")[-1].replace("-", " ")
        topic = slug if slug else "the topic"

        content = (
            f"Crawled content from {url}.\n\n"
            f"This page discusses {topic} in depth.\n"
            f"Key findings: Research indicates a 35% increase in related activity.\n"
            f"Expert opinion: 'This field is transforming rapidly,' says Dr. Smith.\n"
            f"Statistics: 50+ countries are actively engaged in {topic} programmes.\n"
            f"Historical context: Interest began growing significantly in 2020.\n"
            f"Future outlook: Projections suggest continued expansion through 2030.\n"
            f"This content was retrieved via the mock crawler provider."
        )
        return CrawlResult(
            url=url,
            title=f"Page about {topic}",
            content=content,
            content_type="text/html",
            language="en",
            word_count=len(content.split()),
            success=True,
            error="",
            metadata={"mock": True, "source_url": url},
        )

    async def crawl_many(
        self,
        urls: list[str],
        timeout_seconds: int = 10,
        max_concurrent: int = 5,
    ) -> list[CrawlResult]:
        return [await self.crawl(url, timeout_seconds) for url in urls]
