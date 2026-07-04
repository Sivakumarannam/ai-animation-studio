"""
Workflow setup — registers all steps with the StepRegistry at startup.
Called once during FastAPI lifespan, after providers are registered.

Open/Closed: add new steps by adding an entry here.
The Pipeline and WorkflowExecutor never need to change.
"""
from __future__ import annotations

import structlog

from agents.registry import ProviderRegistry
from workflow.registry import StepRegistry

logger = structlog.get_logger()


def register_workflow_steps(
    registry: StepRegistry,
    provider_registry: ProviderRegistry,
) -> None:
    """
    Instantiate and register all workflow steps.
    Steps receive their provider dependencies at registration time.
    """
    from agents.interfaces.image_provider import ImageProvider
    from agents.interfaces.llm_provider import LLMProvider
    from agents.interfaces.renderer_provider import RendererProvider
    from agents.interfaces.subtitle_provider import SubtitleProvider
    from agents.interfaces.tts_provider import TTSProvider

    from workflow.steps.story_step import StoryGenerationStep
    from workflow.steps.scene_step import SceneBreakdownStep
    from workflow.steps.character_step import CharacterResolutionStep
    from workflow.steps.asset_step import AssetGenerationStep
    from workflow.steps.voice_step import VoiceGenerationStep
    from workflow.steps.subtitle_step import SubtitleGenerationStep
    from workflow.steps.render_step import VideoRenderStep

    # Resolve providers — these have been registered by setup_providers()
    llm = provider_registry.resolve(LLMProvider)
    image = provider_registry.resolve(ImageProvider)
    tts = provider_registry.resolve(TTSProvider)
    subtitle = provider_registry.resolve(SubtitleProvider)
    renderer = provider_registry.resolve(RendererProvider)

    # Register steps in execution order (lower number runs first)
    registry.register(StoryGenerationStep, order=10, llm=llm)
    registry.register(SceneBreakdownStep, order=20)
    registry.register(CharacterResolutionStep, order=30)
    registry.register(AssetGenerationStep, order=40, image_provider=image)
    registry.register(VoiceGenerationStep, order=50, tts=tts)
    registry.register(SubtitleGenerationStep, order=60, subtitle_provider=subtitle)
    registry.register(VideoRenderStep, order=70, renderer=renderer)

    step_count = len(registry.list_steps())
    logger.info("workflow_steps_registered", count=step_count, steps=registry.list_steps())
