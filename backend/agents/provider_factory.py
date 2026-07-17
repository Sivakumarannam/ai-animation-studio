"""
Provider Factory — creates and registers all providers from application config.
Call `setup_providers(settings, registry)` once during FastAPI lifespan startup.
"""
from __future__ import annotations

import structlog

from agents.interfaces.embedding_provider import EmbeddingProvider
from agents.interfaces.image_provider import ImageProvider
from agents.interfaces.llm_provider import LLMProvider
from agents.interfaces.renderer_provider import RendererProvider
from agents.interfaces.seo_provider import SEOProvider
from agents.interfaces.subtitle_provider import SubtitleProvider
from agents.interfaces.music_provider import MusicProvider
from agents.interfaces.tts_provider import TTSProvider
from agents.interfaces.vector_store_provider import VectorStoreProvider
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
    _register_embedding(settings, registry)
    _register_vector_store(settings, registry)
    # Phase 5 — Research providers
    _register_trend(settings, registry)
    _register_research(settings, registry)
    _register_fact_verification(settings, registry)
    _register_search(settings, registry)
    _register_crawler(settings, registry)
    # Phase 6 — Asset Generation providers
    _register_asset_evaluation(settings, registry)
    # Phase 7 — Animation Engine providers
    _register_animation(settings, registry)
    # Phase 8 — Voice Engine providers
    _register_voice(settings, registry)
    # Phase 9 — Music & Sound Engine providers
    _register_music(settings, registry)

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
    """
    Select the image implementation based on `AG_IMAGE_PROVIDER`.

    Supported values today: "mock" (deterministic placeholder images, zero
    dependency) and "comfyui" (real SDXL backend via a running ComfyUI
    server). Unknown/future values fall back to "mock" with a warning so
    the app never crashes at startup.
    """
    provider_name: str = getattr(settings, "AG_IMAGE_PROVIDER", "mock").lower()

    if provider_name == "comfyui":
        from agents.implementations.comfyui_provider import ComfyUIProvider

        base_url: str = getattr(settings, "COMFYUI_BASE_URL", "http://localhost:8188")
        registry.register(ImageProvider, ComfyUIProvider(base_url=base_url))
        return

    if provider_name != "mock":
        logger.warning(
            "image_provider_unsupported_falling_back_to_mock",
            requested=provider_name,
        )

    from agents.implementations.mock_image_provider import MockImageProvider

    registry.register(ImageProvider, MockImageProvider())


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


def _register_embedding(settings: object, registry: ProviderRegistry) -> None:
    """
    Select the embedding implementation based on `EMBEDDING_PROVIDER`.

    Supported values today: "mock" (deterministic, zero-dependency) and
    "ollama" (local embedding model server). Unknown/future values fall back
    to "mock" with a warning so the app never crashes at startup.
    """
    provider_name: str = getattr(settings, "EMBEDDING_PROVIDER", "mock").lower()

    if provider_name == "ollama":
        from agents.implementations.ollama_embedding_provider import OllamaEmbeddingProvider

        base_url: str = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        model: str = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        registry.register(EmbeddingProvider, OllamaEmbeddingProvider(base_url=base_url, model=model))
        return

    if provider_name != "mock":
        logger.warning(
            "embedding_provider_unsupported_falling_back_to_mock",
            requested=provider_name,
        )

    from agents.implementations.mock_embedding_provider import MockEmbeddingProvider

    registry.register(EmbeddingProvider, MockEmbeddingProvider())


def _register_vector_store(settings: object, registry: ProviderRegistry) -> None:
    """
    Select the vector store implementation based on `VECTOR_DB_PROVIDER`.

    Supported values today: "memory" (default, zero-dependency, pure Python
    cosine similarity) and "chromadb" (optional persistent store). Unknown
    values, or chromadb import/instantiation failures, fall back to "memory"
    so the app never crashes at startup.
    """
    provider_name: str = getattr(settings, "VECTOR_DB_PROVIDER", "memory").lower()

    if provider_name == "chromadb":
        try:
            from agents.implementations.chroma_vector_store import ChromaVectorStore

            persist_dir: str = getattr(settings, "CHROMA_PERSIST_DIR", "./chroma_data")
            registry.register(VectorStoreProvider, ChromaVectorStore(persist_directory=persist_dir))
            return
        except Exception as exc:
            logger.warning(
                "vector_store_chromadb_unavailable_falling_back_to_memory",
                error=str(exc),
            )

    if provider_name not in ("memory", "chromadb"):
        logger.warning(
            "vector_store_provider_unsupported_falling_back_to_memory",
            requested=provider_name,
        )

    from agents.implementations.memory_vector_store import InMemoryVectorStore

    registry.register(VectorStoreProvider, InMemoryVectorStore())


# ---------------------------------------------------------------------------
# Phase 5 — Research providers
# ---------------------------------------------------------------------------

def _register_trend(settings: object, registry: ProviderRegistry) -> None:
    from agents.interfaces.trend_provider import TrendProvider
    from agents.implementations.mock_trend_provider import MockTrendProvider
    registry.register(TrendProvider, MockTrendProvider())


def _register_research(settings: object, registry: ProviderRegistry) -> None:
    from agents.interfaces.research_provider import ResearchProvider
    from agents.implementations.mock_research_provider import MockResearchProvider
    registry.register(ResearchProvider, MockResearchProvider())


def _register_fact_verification(settings: object, registry: ProviderRegistry) -> None:
    from agents.interfaces.fact_verification_provider import FactVerificationProvider
    from agents.implementations.mock_fact_verification_provider import MockFactVerificationProvider
    registry.register(FactVerificationProvider, MockFactVerificationProvider())


def _register_search(settings: object, registry: ProviderRegistry) -> None:
    from agents.interfaces.search_provider import SearchProvider
    from agents.implementations.mock_search_provider import MockSearchProvider
    registry.register(SearchProvider, MockSearchProvider())


def _register_crawler(settings: object, registry: ProviderRegistry) -> None:
    from agents.interfaces.crawler_provider import CrawlerProvider
    from agents.implementations.mock_crawler_provider import MockCrawlerProvider
    registry.register(CrawlerProvider, MockCrawlerProvider())


# ---------------------------------------------------------------------------
# Phase 6 — Asset Generation providers
# ---------------------------------------------------------------------------

def _register_asset_evaluation(settings: object, registry: ProviderRegistry) -> None:
    from agents.interfaces.asset_evaluation_provider import AssetEvaluationProvider
    from agents.implementations.mock_asset_evaluation_provider import MockAssetEvaluationProvider
    registry.register(AssetEvaluationProvider, MockAssetEvaluationProvider())


# ---------------------------------------------------------------------------
# Phase 7 — Animation Engine providers
# ---------------------------------------------------------------------------

def _register_animation(settings: object, registry: ProviderRegistry) -> None:
    """
    Select the animation rendering backend based on `AN_ANIMATION_PROVIDER`.

    Supported values: "mock" (deterministic, zero-dependency) and
    "ffmpeg" (real FFmpeg compositing). Unknown values fall back to "mock".
    """
    from agents.interfaces.animation_provider import AnimationProvider

    provider_name: str = getattr(settings, "AN_ANIMATION_PROVIDER", "mock").lower()

    if provider_name == "ffmpeg":
        try:
            from agents.implementations.ffmpeg_animation_provider import FFmpegAnimationProvider
            registry.register(AnimationProvider, FFmpegAnimationProvider())
            return
        except Exception as exc:
            logger.warning("ffmpeg_animation_provider_unavailable_falling_back_to_mock", error=str(exc))

    if provider_name != "mock":
        logger.warning("animation_provider_unsupported_falling_back_to_mock", requested=provider_name)

    from agents.implementations.mock_animation_provider import MockAnimationProvider
    registry.register(AnimationProvider, MockAnimationProvider())


# ---------------------------------------------------------------------------
# Phase 8 — Voice Engine providers
# ---------------------------------------------------------------------------

def _register_voice(settings: object, registry: ProviderRegistry) -> None:
    """
    Select the voice synthesis backend based on `VO_VOICE_PROVIDER`.

    Supported values: "mock" (deterministic, zero-dependency) and
    "piper" (real Piper TTS binary). Unknown values fall back to "mock".
    """
    from agents.interfaces.voice_provider import VoiceProvider

    provider_name: str = getattr(settings, "VO_VOICE_PROVIDER", "mock").lower()

    if provider_name == "piper":
        try:
            from agents.implementations.piper_voice_provider import PiperVoiceProvider

            piper_binary: str = getattr(settings, "PIPER_BINARY", "piper")
            models_dir: str = getattr(settings, "PIPER_MODELS_DIR", "/models/piper")
            registry.register(VoiceProvider, PiperVoiceProvider(piper_binary=piper_binary, models_dir=models_dir))
            return
        except Exception as exc:
            logger.warning("piper_voice_provider_unavailable_falling_back_to_mock", error=str(exc))

    if provider_name != "mock":
        logger.warning("voice_provider_unsupported_falling_back_to_mock", requested=provider_name)

    from agents.implementations.mock_voice_provider import MockVoiceProvider
    registry.register(VoiceProvider, MockVoiceProvider())


# ---------------------------------------------------------------------------
# Phase 9 — Music & Sound Engine providers
# ---------------------------------------------------------------------------

def _register_music(settings: object, registry: ProviderRegistry) -> None:
    """
    Select the music generation backend based on `MU_MUSIC_PROVIDER`.

    Supported values: "mock" (deterministic sine-tone WAV, zero-dependency).
    Unknown values fall back to "mock" with a warning so the app never
    crashes at startup — swap in a real implementation (suno, udio, musicgen)
    without touching any calling code.
    """
    provider_name: str = getattr(settings, "MU_MUSIC_PROVIDER", "mock").lower()

    if provider_name != "mock":
        logger.warning("music_provider_unsupported_falling_back_to_mock", requested=provider_name)

    from agents.implementations.mock_music_provider import MockMusicProvider
    registry.register(MusicProvider, MockMusicProvider())
