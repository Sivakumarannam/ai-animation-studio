"""
MockSearchProvider — deterministic web search for development and testing.
"""
from __future__ import annotations

from agents.interfaces.search_provider import SearchProvider, SearchResultItem


class MockSearchProvider(SearchProvider):
    @property
    def provider_name(self) -> str:
        return "mock/search-provider-v1"

    async def is_available(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "en",
        safe_search: bool = True,
    ) -> list[SearchResultItem]:
        slug = query.lower().replace(" ", "-")
        results = [
            SearchResultItem(
                title=f"Wikipedia: {query}",
                url=f"https://en.wikipedia.org/wiki/{slug}",
                snippet=f"Wikipedia article providing comprehensive coverage of {query}. "
                        "Includes history, key facts, and references.",
                source="wikipedia",
                relevance_score=0.95,
                metadata={"mock": True},
            ),
            SearchResultItem(
                title=f"Latest Research on {query}",
                url=f"https://research.example.org/{slug}",
                snippet=f"Recent academic research publications covering {query}. "
                        "Peer-reviewed studies and meta-analyses.",
                source="academic",
                relevance_score=0.88,
                metadata={"mock": True},
            ),
            SearchResultItem(
                title=f"Educational Overview: {query}",
                url=f"https://edu.example.org/{slug}",
                snippet=f"Educational guide to understanding {query} for learners of all ages.",
                source="education",
                relevance_score=0.82,
                metadata={"mock": True},
            ),
            SearchResultItem(
                title=f"Wikidata: {query} facts",
                url=f"https://www.wikidata.org/wiki/Special:Search?search={slug}",
                snippet=f"Structured data and facts about {query} from Wikidata.",
                source="wikidata",
                relevance_score=0.78,
                metadata={"mock": True},
            ),
            SearchResultItem(
                title=f"News: {query} in 2025",
                url=f"https://news.example.org/{slug}-2025",
                snippet=f"Recent news coverage of {query} and its impact.",
                source="news",
                relevance_score=0.72,
                metadata={"mock": True},
            ),
        ]
        return results[:max_results]
