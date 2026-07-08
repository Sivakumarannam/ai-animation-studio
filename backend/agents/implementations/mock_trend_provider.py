"""
MockTrendProvider — deterministic trend discovery for development and testing.
No network calls, no API keys required.
"""
from __future__ import annotations

import hashlib
from typing import Any

from agents.interfaces.trend_provider import TrendProvider, TrendResult

_MOCK_TRENDS = [
    ("artificial intelligence education", "technology", 92.0, 15.0, 0.35, True),
    ("climate change solutions", "environment", 88.0, 8.0, 0.20, True),
    ("space exploration 2026", "science", 85.0, 12.0, 0.28, True),
    ("renewable energy adoption", "environment", 82.0, 6.0, 0.15, False),
    ("quantum computing breakthroughs", "technology", 79.0, 18.0, 0.42, True),
    ("biodiversity conservation", "nature", 76.0, 4.0, 0.10, False),
    ("ocean plastic cleanup", "environment", 74.0, 7.0, 0.18, True),
    ("ancient history discoveries", "history", 71.0, 3.0, 0.08, False),
    ("mathematics for children", "education", 68.0, 5.0, 0.12, False),
    ("animal migration patterns", "nature", 65.0, 9.0, 0.22, True),
    ("human brain mysteries", "science", 88.0, 14.0, 0.33, True),
    ("sustainable agriculture", "environment", 77.0, 6.0, 0.16, False),
    ("indigenous cultures preservation", "culture", 66.0, 3.0, 0.07, False),
    ("robotics in daily life", "technology", 84.0, 11.0, 0.26, True),
    ("deep sea exploration", "science", 72.0, 8.0, 0.19, True),
    ("meditation and mental health", "health", 80.0, 5.0, 0.13, False),
    ("urban farming innovations", "food", 69.0, 7.0, 0.17, True),
    ("ancient languages revival", "culture", 60.0, 2.0, 0.05, False),
    ("water conservation technology", "environment", 75.0, 9.0, 0.21, True),
    ("stem education for girls", "education", 78.0, 4.0, 0.11, False),
]


def _normalize(keyword: str) -> str:
    return keyword.lower().strip().replace(" ", "_")


class MockTrendProvider(TrendProvider):
    """Deterministic mock that returns pre-seeded trend data."""

    provider_name_str: str = "mock/trend-provider-v1"

    @property
    def provider_name(self) -> str:
        return self.provider_name_str

    async def is_available(self) -> bool:
        return True

    async def discover_trends(
        self,
        categories: list[str] | None = None,
        region: str = "global",
        language: str = "en",
        limit: int = 50,
    ) -> list[TrendResult]:
        results: list[TrendResult] = []
        for keyword, cat, score, vel, growth, emerging in _MOCK_TRENDS:
            if categories and cat not in categories:
                continue
            results.append(
                TrendResult(
                    keyword=keyword,
                    normalized_keyword=_normalize(keyword),
                    category=cat,
                    region=region,
                    language=language,
                    trend_score=score,
                    velocity=vel,
                    growth_rate=growth,
                    popularity_index=score * 0.9,
                    is_emerging=emerging,
                    is_declining=False,
                    raw_data={"mock": True, "source": "mock_trend_provider"},
                    source_name="mock_trend_provider",
                )
            )
        return results[:limit]
