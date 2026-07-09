"""
Provider Registry — the Dependency Injection container for AI providers.

Usage
-----
Register providers once at startup (e.g. in FastAPI lifespan):

    registry = get_provider_registry()
    registry.register(LLMProvider, OllamaProvider(...))
    registry.register(ImageProvider, ComfyUIProvider(...))

Resolve in services / route handlers:

    llm: LLMProvider = get_provider_registry().resolve(LLMProvider)

Or via FastAPI dependency:

    Depends(get_llm_provider)
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, TypeVar

from packages.core.exceptions import AppError

if TYPE_CHECKING:
    from agents.interfaces.embedding_provider import EmbeddingProvider
    from agents.interfaces.image_provider import ImageProvider
    from agents.interfaces.llm_provider import LLMProvider
    from agents.interfaces.renderer_provider import RendererProvider
    from agents.interfaces.seo_provider import SEOProvider
    from agents.interfaces.stt_provider import STTProvider
    from agents.interfaces.subtitle_provider import SubtitleProvider
    from agents.interfaces.tts_provider import TTSProvider
    from agents.interfaces.vector_store_provider import VectorStoreProvider
    from agents.interfaces.trend_provider import TrendProvider
    from agents.interfaces.research_provider import ResearchProvider
    from agents.interfaces.fact_verification_provider import FactVerificationProvider
    from agents.interfaces.search_provider import SearchProvider
    from agents.interfaces.crawler_provider import CrawlerProvider
    from agents.interfaces.asset_evaluation_provider import AssetEvaluationProvider  # Phase 6

T = TypeVar("T")


class ProviderNotRegisteredError(AppError):
    def __init__(self, interface: type) -> None:
        super().__init__(
            f"No provider registered for interface '{interface.__name__}'. "
            "Register one at startup via ProviderRegistry.register().",
            code="PROVIDER_NOT_REGISTERED",
        )


class ProviderRegistry:
    """
    Thread-safe singleton registry mapping provider interfaces → implementations.
    Follows the Open/Closed Principle: register new providers without changing existing code.
    """

    def __init__(self) -> None:
        self._providers: dict[type, Any] = {}
        self._lock = threading.Lock()

    def register(self, interface: type, implementation: Any) -> None:
        """Bind an interface type to a concrete implementation."""
        with self._lock:
            self._providers[interface] = implementation

    def resolve(self, interface: type[T]) -> T:
        """Retrieve the registered implementation for an interface."""
        with self._lock:
            impl = self._providers.get(interface)
        if impl is None:
            raise ProviderNotRegisteredError(interface)
        return impl  # type: ignore[return-value]

    def is_registered(self, interface: type) -> bool:
        """Check whether an implementation is registered for an interface."""
        with self._lock:
            return interface in self._providers

    def list_registered(self) -> dict[str, str]:
        """Return a dict of {interface_name: provider_name} for observability."""
        with self._lock:
            result = {}
            for iface, impl in self._providers.items():
                name = getattr(impl, "provider_name", type(impl).__name__)
                result[iface.__name__] = name
        return result

    async def health_check(self) -> dict[str, bool]:
        """
        Call is_available() on every registered provider.
        Returns {interface_name: is_healthy}.
        """
        results: dict[str, bool] = {}
        with self._lock:
            snapshot = dict(self._providers)
        for iface, impl in snapshot.items():
            checker = getattr(impl, "is_available", None)
            if callable(checker):
                try:
                    results[iface.__name__] = await checker()
                except Exception:
                    results[iface.__name__] = False
            else:
                results[iface.__name__] = True  # assume healthy if no check
        return results


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: ProviderRegistry | None = None
_registry_lock = threading.Lock()


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ProviderRegistry()
    return _registry


# ---------------------------------------------------------------------------
# FastAPI dependency helpers
# ---------------------------------------------------------------------------

def get_llm_provider() -> "LLMProvider":
    from agents.interfaces.llm_provider import LLMProvider
    return get_provider_registry().resolve(LLMProvider)


def get_image_provider() -> "ImageProvider":
    from agents.interfaces.image_provider import ImageProvider
    return get_provider_registry().resolve(ImageProvider)


def get_tts_provider() -> "TTSProvider":
    from agents.interfaces.tts_provider import TTSProvider
    return get_provider_registry().resolve(TTSProvider)


def get_stt_provider() -> "STTProvider":
    from agents.interfaces.stt_provider import STTProvider
    return get_provider_registry().resolve(STTProvider)


def get_subtitle_provider() -> "SubtitleProvider":
    from agents.interfaces.subtitle_provider import SubtitleProvider
    return get_provider_registry().resolve(SubtitleProvider)


def get_renderer_provider() -> "RendererProvider":
    from agents.interfaces.renderer_provider import RendererProvider
    return get_provider_registry().resolve(RendererProvider)


def get_seo_provider() -> "SEOProvider":
    from agents.interfaces.seo_provider import SEOProvider
    return get_provider_registry().resolve(SEOProvider)


def get_embedding_provider() -> "EmbeddingProvider":
    from agents.interfaces.embedding_provider import EmbeddingProvider
    return get_provider_registry().resolve(EmbeddingProvider)


def get_vector_store_provider() -> "VectorStoreProvider":
    from agents.interfaces.vector_store_provider import VectorStoreProvider
    return get_provider_registry().resolve(VectorStoreProvider)


def get_trend_provider() -> "TrendProvider":
    from agents.interfaces.trend_provider import TrendProvider
    return get_provider_registry().resolve(TrendProvider)


def get_research_provider() -> "ResearchProvider":
    from agents.interfaces.research_provider import ResearchProvider
    return get_provider_registry().resolve(ResearchProvider)


def get_fact_verification_provider() -> "FactVerificationProvider":
    from agents.interfaces.fact_verification_provider import FactVerificationProvider
    return get_provider_registry().resolve(FactVerificationProvider)


def get_search_provider() -> "SearchProvider":
    from agents.interfaces.search_provider import SearchProvider
    return get_provider_registry().resolve(SearchProvider)


def get_crawler_provider() -> "CrawlerProvider":
    from agents.interfaces.crawler_provider import CrawlerProvider
    return get_provider_registry().resolve(CrawlerProvider)


# ---------------------------------------------------------------------------
# Phase 6 — Asset Generation providers
# ---------------------------------------------------------------------------

def get_asset_evaluation_provider() -> "AssetEvaluationProvider":
    from agents.interfaces.asset_evaluation_provider import AssetEvaluationProvider
    return get_provider_registry().resolve(AssetEvaluationProvider)
