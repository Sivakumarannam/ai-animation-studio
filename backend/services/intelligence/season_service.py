"""SeasonPlannerService — season CRUD and AI-driven planning."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import Season
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import SeasonRepository


class SeasonService:
    def __init__(self, repo: SeasonRepository, llm: LLMProvider) -> None:
        self._repo = repo
        self._llm = llm
        self._cfg = get_settings()

    async def create(self, world_id: UUID, project_id: UUID, data: dict[str, Any]) -> Season:
        if "season_number" not in data or data["season_number"] is None:
            data["season_number"] = await self._repo.get_next_season_number(world_id)
        season = Season(world_id=world_id, project_id=project_id, **data)
        return await self._repo.create(season)

    async def get_by_id(self, season_id: UUID) -> Season:
        s = await self._repo.get_by_id(season_id)
        if s is None:
            raise NotFoundError(f"Season {season_id} not found")
        return s

    async def list_by_world(
        self, world_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Season]:
        return await self._repo.get_by_world(world_id, pagination)

    async def update(self, season_id: UUID, data: dict[str, Any]) -> Season:
        season = await self.get_by_id(season_id)
        return await self._repo.update(season, data)

    async def delete(self, season_id: UUID) -> None:
        season = await self.get_by_id(season_id)
        await self._repo.delete(season)

    async def ai_plan_season(
        self,
        world_context: dict[str, Any],
        story_idea: str,
        season_number: int,
        episode_count: int | None = None,
    ) -> dict[str, Any]:
        """Use the LLM to generate a season plan. Returns raw JSON dict."""
        ep_count = episode_count or self._cfg.SI_DEFAULT_EPISODES_PER_SEASON
        prompt = (
            f"Plan a season for this story world:\n"
            f"World: {world_context.get('name', 'Unknown')}\n"
            f"Description: {world_context.get('description', '')}\n"
            f"Story idea: {story_idea}\n"
            f"Season number: {season_number}\n"
            f"Target episodes: {ep_count}\n\n"
            "Generate a detailed season plan with episode summaries."
        )
        return await self._llm.generate_json(
            prompt,
            system="You are a creative story planning AI. Return ONLY valid JSON.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
