"""MemoryService — persistent story memory storage and retrieval."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import StoryMemory
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import StoryMemoryRepository


class MemoryService:
    """
    Stores and retrieves story memory entries for a world.
    Memories are queryable by type (character, location, event, relationship, joke, lesson).
    Phase 4: embedding_vector field is reserved for RAG integration.
    """

    MEMORY_TYPES = frozenset(
        ["character", "location", "event", "relationship", "joke", "lesson", "object", "fact"]
    )

    def __init__(self, repo: StoryMemoryRepository, llm: LLMProvider) -> None:
        self._repo = repo
        self._llm = llm
        self._cfg = get_settings()

    async def store(
        self,
        world_id: UUID,
        memory_type: str,
        key: str,
        value: dict[str, Any],
        episode_id: UUID | None = None,
    ) -> StoryMemory:
        """Upsert a memory entry (update if key exists, create otherwise)."""
        memory = await self._repo.upsert(world_id, memory_type, key, value)
        if episode_id:
            memory.episode_id = episode_id
            await self._repo.update(memory, {"episode_id": episode_id})
        return memory

    async def get_memories(
        self,
        world_id: UUID,
        pagination: PaginationParams,
        memory_type: str | None = None,
    ) -> PaginatedResult[StoryMemory]:
        return await self._repo.get_by_world(world_id, pagination, memory_type=memory_type)

    async def get_by_key(self, world_id: UUID, key: str) -> StoryMemory | None:
        return await self._repo.get_by_key(world_id, key)

    async def deactivate(self, memory_id: UUID) -> None:
        m = await self._repo.get_by_id(memory_id)
        if m:
            await self._repo.update(m, {"is_active": False})

    async def ai_extract_and_save(
        self,
        world_id: UUID,
        episode_id: UUID,
        episode_content: dict[str, Any],
    ) -> list[StoryMemory]:
        """
        Ask the LLM to extract important memories from a completed episode
        and persist them automatically.
        """
        prompt = (
            f"Extract important story memories from this episode:\n"
            f"Title: {episode_content.get('title', '')}\n"
            f"Summary: {episode_content.get('summary', '')}\n"
            f"Moral: {episode_content.get('moral', '')}\n\n"
            "Return a JSON array of memory objects, each with: "
            "memory_type (character/location/event/relationship/joke/lesson), key, value (object)."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a story memory extraction AI. Return ONLY a valid JSON array.",
            temperature=0.3,
        )
        memories_data = result if isinstance(result, list) else result.get("memories_stored", [])
        saved: list[StoryMemory] = []
        for m in memories_data:
            mtype = m.get("type") or m.get("memory_type", "fact")
            key = m.get("key", "")
            value = m.get("value", m)
            if key:
                mem = await self.store(world_id, mtype, key, value, episode_id=episode_id)
                saved.append(mem)
        return saved

    async def build_context_for_llm(
        self,
        world_id: UUID,
        memory_types: list[str] | None = None,
        limit: int = 30,
    ) -> dict[str, list[Any]]:
        """
        Compile memory entries into a structured context dict usable in LLM prompts.
        Returns {memory_type: [entries...]}.
        """
        pagination = PaginationParams(page=1, page_size=limit)
        context: dict[str, list[Any]] = {}
        types = memory_types or list(self.MEMORY_TYPES)
        for mtype in types:
            result = await self._repo.get_by_world(world_id, pagination, memory_type=mtype)
            if result.items:
                context[mtype] = [{"key": m.key, "value": m.value} for m in result.items]
        return context
