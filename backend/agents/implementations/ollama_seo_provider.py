"""
SEO Provider backed by any LLMProvider implementation.
Injects LLMProvider via constructor — not tied to Ollama directly.
"""
from __future__ import annotations

from agents.interfaces.llm_provider import LLMProvider
from agents.interfaces.seo_provider import SEOProvider, SEORequest, SEOResult


class OllamaSEOProvider(SEOProvider):
    """Generates SEO metadata using any LLMProvider implementation."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    @property
    def provider_name(self) -> str:
        return f"llm-seo/{self._llm.provider_name}"

    async def generate(self, request: SEORequest) -> SEOResult:
        system = (
            "You are an expert YouTube/social media SEO specialist. "
            "Given content metadata, produce a JSON object with keys: "
            "optimized_title (string), optimized_description (string), "
            "tags (array of strings max 30), hashtags (array of strings with # prefix). "
            "Reply with ONLY valid JSON."
        )
        prompt = (
            f"Content title: {request.title}\n"
            f"Content description: {request.description}\n"
            f"Language: {request.language}\n"
            f"Genre: {request.genre}\n"
            f"Keyword hints: {', '.join(request.keywords_hint)}\n"
            "Generate SEO metadata."
        )
        try:
            data = await self._llm.generate_json(prompt, system=system, temperature=0.3)
            return SEOResult(
                optimized_title=data.get("optimized_title", request.title),
                optimized_description=data.get("optimized_description", request.description),
                tags=data.get("tags", []),
                hashtags=data.get("hashtags", []),
                metadata={"provider": self.provider_name},
            )
        except Exception as exc:
            return SEOResult(
                optimized_title=request.title,
                optimized_description=request.description,
                tags=[],
                hashtags=[],
                metadata={"error": str(exc)},
            )

    async def is_available(self) -> bool:
        return await self._llm.is_available()
