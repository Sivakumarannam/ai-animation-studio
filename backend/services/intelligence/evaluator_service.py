"""StoryEvaluatorService — 10-dimension quality scoring with auto-improvement."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import Episode, StoryEvaluation
from repositories.intelligence_repository import EpisodeRepository, StoryEvaluationRepository

logger = structlog.get_logger()


class StoryEvaluatorService:
    """
    Evaluates an episode on 10 dimensions (0-100 each), computes overall score,
    and determines whether it meets the quality threshold.
    If below threshold and retries remain, marks episode for auto-improvement.
    """

    def __init__(
        self,
        episode_repo: EpisodeRepository,
        eval_repo: StoryEvaluationRepository,
        llm: LLMProvider,
    ) -> None:
        self._episode_repo = episode_repo
        self._eval_repo = eval_repo
        self._llm = llm
        self._cfg = get_settings()

    async def evaluate_episode(self, episode_id: UUID) -> StoryEvaluation:
        ep = await self._episode_repo.get_by_id(episode_id)
        if ep is None:
            from packages.core.exceptions import NotFoundError
            raise NotFoundError(f"Episode {episode_id} not found")

        scores = await self._score_episode(ep)
        overall = self._compute_overall(scores)
        approved = overall >= self._cfg.SI_MIN_STORY_SCORE

        eval_obj = StoryEvaluation(
            episode_id=episode_id,
            evaluator_version="1.0",
            originality_score=scores.get("originality_score", 0.0),
            consistency_score=scores.get("consistency_score", 0.0),
            creativity_score=scores.get("creativity_score", 0.0),
            grammar_score=scores.get("grammar_score", 0.0),
            flow_score=scores.get("flow_score", 0.0),
            entertainment_score=scores.get("entertainment_score", 0.0),
            educational_value_score=scores.get("educational_value_score", 0.0),
            story_arc_score=scores.get("story_arc_score", 0.0),
            dialogue_score=scores.get("dialogue_score", 0.0),
            overall_score=overall,
            feedback=scores.get("feedback", {}),
            approved=approved,
            evaluated_at=datetime.now(timezone.utc),
        )
        saved = await self._eval_repo.create(eval_obj)

        # Update episode score and status
        new_status = "approved" if approved else "needs_revision"
        await self._episode_repo.update(ep, {
            "story_score": overall,
            "status": new_status,
        })
        logger.info(
            "episode_evaluated",
            episode_id=str(episode_id),
            score=overall,
            approved=approved,
        )
        return saved

    async def _score_episode(self, ep: Episode) -> dict[str, Any]:
        prompt = (
            f"Evaluate this episode on a scale of 0-100 for each dimension:\n"
            f"Title: {ep.title}\n"
            f"Summary: {ep.summary}\n"
            f"Opening: {ep.opening}\n"
            f"Middle: {ep.middle}\n"
            f"Ending: {ep.ending}\n"
            f"Moral: {ep.moral}\n\n"
            "Score dimensions: originality_score, consistency_score, creativity_score, "
            "grammar_score, flow_score, entertainment_score, educational_value_score, "
            "story_arc_score, dialogue_score.\n"
            "Also include a 'feedback' object with strengths (list), improvements (list), suggestions (list)."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a story quality evaluator AI. Score 0-100. Return ONLY valid JSON.",
            temperature=0.3,
        )
        return result

    def _compute_overall(self, scores: dict[str, Any]) -> float:
        dimensions = [
            "originality_score", "consistency_score", "creativity_score",
            "grammar_score", "flow_score", "entertainment_score",
            "educational_value_score", "story_arc_score", "dialogue_score",
        ]
        values = [float(scores.get(d, 0.0)) for d in dimensions]
        return round(sum(values) / len(values), 2) if values else 0.0
