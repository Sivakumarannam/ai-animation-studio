"""
MockResearchProvider — deterministic research collection for development and testing.
"""
from __future__ import annotations

from datetime import datetime, timezone

from agents.interfaces.research_provider import (
    ArticleResult,
    ResearchProvider,
    ResearchResult,
)

_MOCK_ARTICLES: dict[str, list[dict]] = {
    "default": [
        {
            "title": "Comprehensive Overview: {topic}",
            "url": "https://en.wikipedia.org/wiki/{slug}",
            "content": "This is a detailed Wikipedia-sourced article about {topic}. "
                       "Research shows that {topic} has become increasingly important in recent years. "
                       "Scientists and educators have noted a 35% increase in public interest. "
                       "Key facts: The field encompasses multiple sub-disciplines. "
                       "Major organisations have invested significantly. "
                       "Future projections indicate continued growth.",
            "summary": "A comprehensive overview of {topic} covering key facts, recent developments, and future outlook.",
            "author": "Wikipedia Contributors",
            "source_type": "wikipedia",
            "quality_score": 0.88,
            "relevance_score": 0.92,
        },
        {
            "title": "Recent Advances in {topic}",
            "url": "https://example-news.org/advances-{slug}",
            "content": "Breaking developments in {topic} have captured global attention. "
                       "A new study published this month reveals groundbreaking findings. "
                       "According to Dr. Jane Smith, 'This represents a major milestone.' "
                       "The research involved 10,000 participants across 15 countries. "
                       "Results show a 42% improvement in key metrics compared to previous benchmarks.",
            "summary": "Latest research breakthroughs and advances in {topic}.",
            "author": "News Desk",
            "source_type": "news_rss",
            "quality_score": 0.75,
            "relevance_score": 0.85,
        },
        {
            "title": "Educational Guide: Understanding {topic}",
            "url": "https://edu-resources.org/guide-{slug}",
            "content": "This educational guide explains {topic} in accessible terms. "
                       "What is {topic}? It is defined as the systematic study of related phenomena. "
                       "Why does it matter? Evidence shows significant societal impact. "
                       "Key concepts include: primary mechanisms, secondary effects, and long-term implications. "
                       "Suitable for ages 10 and above.",
            "summary": "A beginner-friendly educational guide to {topic}.",
            "author": "Education Team",
            "source_type": "open_education",
            "quality_score": 0.82,
            "relevance_score": 0.78,
        },
    ],
}

_MOCK_FACTS: list[str] = [
    "{topic} has seen a 35% increase in research publications over the last 5 years.",
    "Over 50 countries have active national programmes dedicated to {topic}.",
    "Public interest in {topic} peaked in 2024 and continues to grow.",
    "The global market related to {topic} is valued at over $200 billion.",
    "Educational institutions have integrated {topic} into curricula at record rates.",
]

_MOCK_ENTITIES: list[dict] = [
    {"entity_type": "organization", "name": "Global Research Institute", "description": "Leading organisation in {topic}"},
    {"entity_type": "person", "name": "Dr. Jane Smith", "description": "Pioneering researcher in {topic}"},
    {"entity_type": "event", "name": "World {topic} Summit 2025", "description": "Annual global conference"},
    {"entity_type": "statistic", "name": "35% growth", "description": "Year-over-year growth in {topic} activity"},
    {"entity_type": "place", "name": "Geneva Research Hub", "description": "Major centre for {topic} research"},
]


class MockResearchProvider(ResearchProvider):
    """Deterministic mock that returns pre-seeded research results."""

    @property
    def provider_name(self) -> str:
        return "mock/research-provider-v1"

    async def is_available(self) -> bool:
        return True

    async def research_topic(
        self,
        topic: str,
        keywords: list[str] | None = None,
        max_articles: int = 10,
        language: str = "en",
    ) -> ResearchResult:
        slug = topic.lower().replace(" ", "-")
        templates = _MOCK_ARTICLES["default"]
        articles: list[ArticleResult] = []

        for tmpl in templates[:max_articles]:
            articles.append(
                ArticleResult(
                    title=tmpl["title"].replace("{topic}", topic),
                    url=tmpl["url"].replace("{slug}", slug).replace("{topic}", topic),
                    content=tmpl["content"].replace("{topic}", topic),
                    summary=tmpl["summary"].replace("{topic}", topic),
                    author=tmpl["author"],
                    published_at=datetime(2025, 6, 15, tzinfo=timezone.utc),
                    source_type=tmpl["source_type"],
                    language=language,
                    quality_score=tmpl["quality_score"],
                    relevance_score=tmpl["relevance_score"],
                    metadata={"mock": True},
                )
            )

        facts = [f.replace("{topic}", topic) for f in _MOCK_FACTS]
        entities = [
            {**e, "description": e["description"].replace("{topic}", topic)}
            for e in _MOCK_ENTITIES
        ]

        return ResearchResult(
            topic=topic,
            articles=articles,
            facts=facts,
            entities=entities,
            summary=f"Comprehensive mock research summary for '{topic}'. "
                    f"Found {len(articles)} articles, {len(facts)} key facts, "
                    f"and {len(entities)} named entities.",
            quality_score=0.82,
        )
