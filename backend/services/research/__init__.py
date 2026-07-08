"""
Phase 5 — Research & Trend Intelligence Engine services.
"""
from services.research.job_service import ResearchJobService
from services.research.trend_service import TrendDiscoveryService
from services.research.topic_service import TopicService
from services.research.research_engine_service import ResearchEngineService
from services.research.fact_verification_service import FactVerificationService
from services.research.opportunity_scoring_service import OpportunityScoringService
from services.research.knowledge_integration_service import KnowledgeIntegrationService
from services.research.scheduler_service import SchedulerService

__all__ = [
    "ResearchJobService",
    "TrendDiscoveryService",
    "TopicService",
    "ResearchEngineService",
    "FactVerificationService",
    "OpportunityScoringService",
    "KnowledgeIntegrationService",
    "SchedulerService",
]
