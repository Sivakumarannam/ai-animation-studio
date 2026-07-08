"""
Fact verification service — cross-checks facts across sources.
"""
from __future__ import annotations

from typing import Any

import structlog

from agents.interfaces.fact_verification_provider import FactVerificationProvider
from repositories.research_repository import ResearchFactRepository, ResearchTopicRepository

logger = structlog.get_logger()


class FactVerificationService:
    def __init__(
        self,
        fact_repo: ResearchFactRepository,
        topic_repo: ResearchTopicRepository,
        verification_provider: FactVerificationProvider,
    ) -> None:
        self._fact_repo = fact_repo
        self._topic_repo = topic_repo
        self._provider = verification_provider

    async def verify_pending_facts(self, batch_size: int = 20) -> dict[str, Any]:
        """Process a batch of unverified facts."""
        unverified = await self._fact_repo.get_unverified(limit=batch_size)
        if not unverified:
            return {"verified": 0, "rejected": 0, "total": 0}

        verified_count = 0
        rejected_count = 0

        # Group by topic for efficient context sharing
        topic_groups: dict[str, list] = {}
        for fact in unverified:
            key = str(fact.topic_id)
            topic_groups.setdefault(key, []).append(fact)

        for topic_id_str, facts in topic_groups.items():
            from uuid import UUID
            topic = await self._topic_repo.get_by_id(UUID(topic_id_str))
            topic_name = topic.canonical_name if topic else "unknown"

            statements = [f.statement for f in facts]
            results = await self._provider.verify_facts_batch(
                facts=statements,
                topic=topic_name,
            )

            for fact, vr in zip(facts, results):
                if vr.is_verified:
                    await self._fact_repo.update(fact, {
                        "is_verified": True,
                        "confidence": vr.confidence,
                        "supporting_sources": vr.supporting_sources,
                        "conflicting_sources": vr.conflicting_sources,
                        "citations": vr.citations,
                        "verification_count": fact.verification_count + 1,
                    })
                    verified_count += 1
                elif vr.confidence < 0.3:
                    await self._fact_repo.update(fact, {
                        "is_rejected": True,
                        "rejection_reason": vr.rejection_reason or "Confidence below threshold",
                        "conflicting_sources": vr.conflicting_sources,
                        "verification_count": fact.verification_count + 1,
                    })
                    rejected_count += 1
                else:
                    # Update confidence but leave unverified for retry
                    await self._fact_repo.update(fact, {
                        "confidence": vr.confidence,
                        "verification_count": fact.verification_count + 1,
                    })

        logger.info("fact_verification_done", verified=verified_count, rejected=rejected_count)
        return {"verified": verified_count, "rejected": rejected_count, "total": len(unverified)}

    async def get_verified_count(self) -> int:
        return await self._fact_repo.count_verified()
