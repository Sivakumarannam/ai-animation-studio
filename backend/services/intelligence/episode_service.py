"""EpisodePlannerService — episode CRUD and AI-driven planning."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import Episode, StoryEvaluation
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import (
    EpisodeRepository, StoryEvaluationRepository, StoryVersionRepository,
)


class EpisodeService:
    def __init__(
        self,
        repo: EpisodeRepository,
        eval_repo: StoryEvaluationRepository,
        version_repo: StoryVersionRepository,
        llm: LLMProvider,
    ) -> None:
        self._repo = repo
        self._eval_repo = eval_repo
        self._versions = version_repo
        self._llm = llm
        self._cfg = get_settings()

    async def create(
        self, season_id: UUID, world_id: UUID, project_id: UUID, data: dict[str, Any]
    ) -> Episode:
        if "episode_number" not in data or data["episode_number"] is None:
            data["episode_number"] = await self._repo.get_next_episode_number(season_id)
        ep = Episode(season_id=season_id, world_id=world_id, project_id=project_id, **data)
        return await self._repo.create(ep)

    async def get_by_id(self, episode_id: UUID) -> Episode:
        ep = await self._repo.get_by_id(episode_id)
        if ep is None:
            raise NotFoundError(f"Episode {episode_id} not found")
        return ep

    async def list_by_season(
        self, season_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Episode]:
        return await self._repo.get_by_season(season_id, pagination)

    async def list_by_project(
        self, project_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[Episode]:
        return await self._repo.get_by_project(project_id, pagination, status=status)

    async def update(self, episode_id: UUID, data: dict[str, Any]) -> Episode:
        ep = await self.get_by_id(episode_id)
        await self._snapshot(ep)
        return await self._repo.update(ep, data)

    async def delete(self, episode_id: UUID) -> None:
        ep = await self.get_by_id(episode_id)
        await self._repo.delete(ep)

    async def ai_plan_episode(
        self,
        world_context: dict[str, Any],
        season_context: dict[str, Any],
        episode_number: int,
        previous_episode_summaries: list[str] | None = None,
    ) -> dict[str, Any]:
        prev = "\n".join(previous_episode_summaries or []) or "None (first episode)"
        prompt = (
            f"Plan episode {episode_number} for:\n"
            f"World: {world_context.get('name', '')}\n"
            f"Season: {season_context.get('title', '')} — arc: {season_context.get('story_arc', '')}\n"
            f"Previous episodes:\n{prev}\n\n"
            "Generate a complete episode plan with opening, middle, ending, moral, and scene count."
        )
        return await self._llm.generate_json(
            prompt,
            system="You are a creative episode planning AI. Return ONLY valid JSON.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )

    async def get_evaluation(self, episode_id: UUID) -> StoryEvaluation | None:
        return await self._eval_repo.get_latest_for_episode(episode_id)

    async def _snapshot(self, ep: Episode) -> None:
        version_num = await self._versions.get_next_version_number("episode", ep.id)
        from database.models.intelligence import StoryVersion
        v = StoryVersion(
            entity_type="episode", entity_id=ep.id,
            version_number=version_num,
            snapshot={
                "title": ep.title, "summary": ep.summary,
                "opening": ep.opening, "middle": ep.middle, "ending": ep.ending,
                "moral": ep.moral, "story_score": ep.story_score,
            },
            change_summary="pre-update snapshot",
        )
        await self._versions.create(v)
