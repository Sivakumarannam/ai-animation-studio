"""
FactVerificationProvider Interface — cross-checks facts across multiple sources.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationResult:
    statement: str
    is_verified: bool
    confidence: float
    supporting_sources: list[str] = field(default_factory=list)
    conflicting_sources: list[str] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    rejection_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class FactVerificationProvider(ABC):
    """Interface for all fact-verification providers."""

    @abstractmethod
    async def verify_fact(
        self,
        statement: str,
        topic: str,
        context: str = "",
    ) -> VerificationResult:
        """Verify a single factual statement. Returns confidence + citations."""
        ...

    @abstractmethod
    async def verify_facts_batch(
        self,
        facts: list[str],
        topic: str,
        context: str = "",
    ) -> list[VerificationResult]:
        """Verify multiple facts. May share context for efficiency."""
        ...

    @abstractmethod
    async def is_available(self) -> bool: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...
