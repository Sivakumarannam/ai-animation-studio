"""
Provider Factory — creates and registers all providers from application config.
Call `setup_providers(settings, registry)` once during FastAPI lifespan startup.
"""
from __future__ import annotations

import structlog

from agents.interfaces.image_provider import ImageProvider
from agents.interfaces.llm_provider import LLMProvider
from agents.interfaces.renderer_provider import RendererProvider
from agents.interfaces.seo_provider import SEOProvider
from agents.interfaces.subtitle_provider import SubtitleProvider
from agents.interfaces.tts_provider import TTSProvider
from agents.registry import ProviderRegistry

logger = structlog.get_logger()


def setup_providers(settings: object, registry: ProviderRegistry) -> None:
    """
    Instantiate all providers from settings and register them.
    Add new providers here — everything else stays unchanged (Open/Closed).
    """
    _register_llm(settings, registry)
    _register_image(settings, registry)
    _register_tts(settings, registry)
    _register_subtitle(settings, registry)
    _register_renderer(settings, registry)
    _register_seo(settings, registry)

    registered = registry.list_registered()
    logger.info("providers_registered", providers=registered)


# ---------------------------------------------------------------------------
# Individual registration helpers — swap implementations by changing these
# ---------------------------------------------------------------------------

def _register_llm(settings: object, registry: ProviderRegistry) -> None:
    """
    Select the LLM implementation based on `SI_AI_PROVIDER`.

    Supported values today: "mock" (deterministic, zero-dependency) and
    "ollama" (local LLM server). Unknown/future values (openai, anthropic,
    gemini, openrouter, ...) fall back to "mock" with a warning so the app
    never crashes at startup — swap in a real implementation here as those
    providers are added, without touching any calling code.
    """
    provider_name: str = getattr(settings, "SI_AI_PROVIDER", "mock").lower()

    if provider_name == "ollama":
        from agents.implementations.ollama_provider import OllamaProvider

        base_url: str = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        model: str = getattr(settings, "OLLAMA_MODEL", "qwen2.5:7b")
        registry.register(LLMProvider, OllamaProvider(base_url=base_url, model=model))
        return

    if provider_name != "mock":
        logger.warning(
            "llm_provider_unsupported_falling_back_to_mock",
            requested=provider_name,
        )

    from agents.implementations.mock_llm_provider import MockLLMProvider

    registry.register(LLMProvider, MockLLMProvider())


def _register_image(settings: object, registry: ProviderRegistry) -> None:
    from agents.implementations.comfyui_provider import ComfyUIProvider

    base_url: str = getattr(settings, "COMFYUI_BASE_URL", "http://localhost:8188")
    registry.register(ImageProvider, ComfyUIProvider(base_url=base_url))


def _register_tts(settings: object, registry: ProviderRegistry) -> None:
    from agents.implementations.piper_provider import PiperTTSProvider

    registry.register(TTSProvider, PiperTTSProvider())


def _register_subtitle(settings: object, registry: ProviderRegistry) -> None:
    from agents.implementations.whisper_provider import WhisperProvider

    registry.register(SubtitleProvider, WhisperProvider())


def _register_renderer(settings: object, registry: ProviderRegistry) -> None:
    from agents.implementations.ffmpeg_renderer import FFmpegRenderer

    registry.register(RendererProvider, FFmpegRenderer())


def _register_seo(settings: object, registry: ProviderRegistry) -> None:
    from agents.implementations.ollama_seo_provider import OllamaSEOProvider
    from agents.implementations.ollama_provider import OllamaProvider

    base_url: str = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model: str = getattr(settings, "OLLAMA_MODEL", "qwen2.5:7b")
    llm = OllamaProvider(base_url=base_url, model=model)
    registry.register(SEOProvider, OllamaSEOProvider(llm=llm))
