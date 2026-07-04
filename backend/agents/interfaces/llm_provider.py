"""
LLM Provider Interface — the single contract all business logic depends on.
Never import a concrete implementation (OllamaProvider, etc.) from services.
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMStreamChunk:
    delta: str
    finished: bool
    model: str


class LLMProvider(ABC):
    """
    Interface for all LLM providers.
    Business logic depends ONLY on this class — never on implementations.
    """

    # ------------------------------------------------------------------
    # Core primitive — all higher-level helpers are built on top of this
    # ------------------------------------------------------------------

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a list of messages and return a single completion."""
        ...

    # ------------------------------------------------------------------
    # Convenience helpers (concrete defaults — providers may override)
    # ------------------------------------------------------------------

    async def generate_text(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Single-turn text generation. Returns the raw string content."""
        messages: list[LLMMessage] = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))
        response = await self.complete(messages, temperature=temperature, max_tokens=max_tokens)
        return response.content

    async def generate_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output.
        Instructs the model to reply with valid JSON and parses the result.
        """
        import json
        import re

        json_system = (
            (system + "\n\n") if system else ""
        ) + "Reply with ONLY valid JSON. No markdown fences, no explanation."

        raw = await self.generate_text(
            prompt, system=json_system, temperature=temperature, max_tokens=max_tokens
        )
        # Strip optional ```json ... ``` fences if the model adds them anyway
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        return json.loads(cleaned)  # type: ignore[no-any-return]

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """
        Stream tokens as they are generated.
        Default implementation wraps complete() for providers that don't support streaming.
        Override for real streaming support.
        """
        response = await self.complete(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)
        yield LLMStreamChunk(delta=response.content, finished=True, model=response.model)

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider endpoint is reachable."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable identifier, e.g. 'ollama/qwen2.5:7b'."""
        ...
