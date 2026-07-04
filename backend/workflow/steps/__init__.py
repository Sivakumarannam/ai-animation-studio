"""
Workflow steps — each step is an independent unit that reads from
WorkflowContext and writes its result back to context.step_results.

Registration order:
  10 - StoryGenerationStep
  20 - SceneBreakdownStep
  30 - CharacterResolutionStep
  40 - AssetGenerationStep
  50 - VoiceGenerationStep
  60 - SubtitleGenerationStep
  70 - VideoRenderStep
"""
from workflow.steps.story_step import StoryGenerationStep
from workflow.steps.scene_step import SceneBreakdownStep
from workflow.steps.character_step import CharacterResolutionStep
from workflow.steps.asset_step import AssetGenerationStep
from workflow.steps.voice_step import VoiceGenerationStep
from workflow.steps.subtitle_step import SubtitleGenerationStep
from workflow.steps.render_step import VideoRenderStep

__all__ = [
    "StoryGenerationStep",
    "SceneBreakdownStep",
    "CharacterResolutionStep",
    "AssetGenerationStep",
    "VoiceGenerationStep",
    "SubtitleGenerationStep",
    "VideoRenderStep",
]
