"""
Ollama LLM Provider — implements LLMProvider using a local Ollama instance.
Supports real streaming via Ollama's streaming API.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import httpx

from agents.interfaces.llm_provider import LLMMessage, LLMProvider, LLMResponse, LLMStreamChunk
from packages.core.exceptions import ProviderError


class OllamaProvider(LLMProvider):
    """LLM provider backed by a local Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return f"ollama/{self._model}"

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                return LLMResponse(
                    content=content,
                    model=self._model,
                    tokens_used=tokens,
                    metadata={"done": data.get("done", False)},
                )
        except httpx.HTTPError as e:
            raise ProviderError("ollama", str(e)) from e

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Real token-by-token streaming via Ollama's streaming API."""
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        import json
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        delta = data.get("message", {}).get("content", "")
                        done = data.get("done", False)
                        yield LLMStreamChunk(delta=delta, finished=done, model=self._model)
                        if done:
                            break
        except httpx.HTTPError as e:
            raise ProviderError("ollama", str(e)) from e

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
