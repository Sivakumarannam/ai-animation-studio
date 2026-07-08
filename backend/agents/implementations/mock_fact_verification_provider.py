"""
MockFactVerificationProvider — deterministic fact checking for development and testing.
"""
from __future__ import annotations

from agents.interfaces.fact_verification_provider import (
    FactVerificationProvider,
    VerificationResult,
)

# Keywords that trigger a lower confidence / rejection in mock mode
_LOW_CONFIDENCE_SIGNALS = ["never", "always", "impossible", "guaranteed", "100%"]
_REJECT_SIGNALS = ["conspiracy", "hoax", "fake", "disproven"]


def _assess(statement: str, topic: str) -> VerificationResult:
    stmt_lower = statement.lower()

    if any(s in stmt_lower for s in _REJECT_SIGNALS):
        return VerificationResult(
            statement=statement,
            is_verified=False,
            confidence=0.05,
            supporting_sources=[],
            conflicting_sources=[
                "Wikipedia fact-check",
                "Snopes cross-reference",
                "Academic meta-analysis",
            ],
            citations=[],
            rejection_reason="Statement contains language associated with debunked claims.",
            metadata={"mock": True},
        )

    if any(s in stmt_lower for s in _LOW_CONFIDENCE_SIGNALS):
        confidence = 0.45
        is_verified = False
    else:
        confidence = 0.82
        is_verified = True

    return VerificationResult(
        statement=statement,
        is_verified=is_verified,
        confidence=confidence,
        supporting_sources=[
            f"Wikipedia: {topic}",
            "Wikidata structured data",
            "Open Government Dataset",
        ],
        conflicting_sources=[],
        citations=[
            {
                "source": "Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                "snippet": f"According to Wikipedia, the statement regarding {topic} is broadly accurate.",
            },
            {
                "source": "Wikidata",
                "url": "https://www.wikidata.org",
                "snippet": "Structured data confirms key numerical claims.",
            },
        ],
        rejection_reason="" if is_verified else "Confidence below threshold for absolute claims.",
        metadata={"mock": True},
    )


class MockFactVerificationProvider(FactVerificationProvider):
    """Deterministic mock that returns pre-assessed verification results."""

    @property
    def provider_name(self) -> str:
        return "mock/fact-verification-provider-v1"

    async def is_available(self) -> bool:
        return True

    async def verify_fact(
        self,
        statement: str,
        topic: str,
        context: str = "",
    ) -> VerificationResult:
        return _assess(statement, topic)

    async def verify_facts_batch(
        self,
        facts: list[str],
        topic: str,
        context: str = "",
    ) -> list[VerificationResult]:
        return [_assess(f, topic) for f in facts]
