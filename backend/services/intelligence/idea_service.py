"""StoryIdeaService — idea generation and management."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import StoryIdea
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import StoryIdeaRepository


class StoryIdeaService:
    def __init__(self, repo: StoryIdeaRepository, llm: LLMProvider) -> None:
        self._repo = repo
        self._llm = llm
        self._cfg = get_settings()

    async def generate_ideas(
        self,
        project_id: UUID,
        genre: str = "comedy",
        story_type: str = "comedy",
        count: int = 3,
        world_context: dict[str, Any] | None = None,
        world_id: UUID | None = None,
        rag_context: str = "",
    ) -> list[StoryIdea]:
        """Generate N story ideas via LLM and persist them.

        `rag_context` is optional retrieved knowledge-base text (Phase 4 RAG).
        Empty string is the expected/valid default when no knowledge base is
        configured or nothing relevant was retrieved — the prompt degrades
        gracefully with no knowledge-base section in that case.
        """
        world_info = ""
        if world_context:
            world_info = (
                f"World: {world_context.get('name', '')}\n"
                f"Description: {world_context.get('description', '')}\n"
                f"Rules: {world_context.get('rules', [])}\n"
            )
        knowledge_info = f"\nRelevant knowledge base context:\n{rag_context}\n" if rag_context else ""
        prompt = (
            f"Generate {count} unique story ideas for a {genre} {story_type} animation.\n"
            f"{world_info}"
            f"{knowledge_info}"
            "Each idea should have: title, premise, genre, tone, story_type, "
            "target_audience, estimated_episodes, themes (list)."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a story idea generator AI. Return ONLY a valid JSON array of ideas.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        ideas_data = result if isinstance(result, list) else [result]
        saved: list[StoryIdea] = []
        for idea_data in ideas_data[:count]:
            idea = StoryIdea(
                project_id=project_id,
                world_id=world_id,
                title=idea_data.get("title", "Untitled Idea"),
                premise=idea_data.get("premise", ""),
                genre=idea_data.get("genre", genre),
                tone=idea_data.get("tone", "light"),
                story_type=idea_data.get("story_type", story_type),
                target_audience=idea_data.get("target_audience", "general"),
                estimated_episodes=idea_data.get("estimated_episodes", 3),
                metadata_=idea_data,
            )
            saved.append(await self._repo.create(idea))
        return saved

    async def get_by_id(self, idea_id: UUID) -> StoryIdea:
        idea = await self._repo.get_by_id(idea_id)
        if idea is None:
            raise NotFoundError(f"StoryIdea {idea_id} not found")
        return idea

    async def list_by_project(
        self, project_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[StoryIdea]:
        return await self._repo.get_by_project(project_id, pagination, status=status)

    async def update_status(self, idea_id: UUID, status: str) -> StoryIdea:
        idea = await self.get_by_id(idea_id)
        return await self._repo.update(idea, {"status": status})

    async def delete(self, idea_id: UUID) -> None:
        idea = await self.get_by_id(idea_id)
        await self._repo.delete(idea)
