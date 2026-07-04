"""Provider interfaces — import from here for clean dependency declarations."""
from agents.interfaces.image_provider import (
    ImageEditRequest,
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageUpscaleRequest,
    ImageProvider,
)
from agents.interfaces.llm_provider import LLMMessage, LLMProvider, LLMResponse, LLMStreamChunk
from agents.interfaces.renderer_provider import RenderRequest, RenderResult, RendererProvider, SceneRenderSpec
from agents.interfaces.seo_provider import SEOProvider, SEORequest, SEOResult
from agents.interfaces.stt_provider import STTProvider, STTRequest, STTResult, STTWord
from agents.interfaces.subtitle_provider import SubtitleProvider, SubtitleResult, SubtitleSegment
from agents.interfaces.tts_provider import TTSProvider, TTSRequest, TTSResult

__all__ = [
    # LLM
    "LLMProvider", "LLMMessage", "LLMResponse", "LLMStreamChunk",
    # Image
    "ImageProvider", "ImageGenerationRequest", "ImageEditRequest",
    "ImageUpscaleRequest", "ImageGenerationResult",
    # TTS
    "TTSProvider", "TTSRequest", "TTSResult",
    # STT
    "STTProvider", "STTRequest", "STTResult", "STTWord",
    # Subtitles
    "SubtitleProvider", "SubtitleSegment", "SubtitleResult",
    # Renderer
    "RendererProvider", "RenderRequest", "RenderResult", "SceneRenderSpec",
    # SEO
    "SEOProvider", "SEORequest", "SEOResult",
]
