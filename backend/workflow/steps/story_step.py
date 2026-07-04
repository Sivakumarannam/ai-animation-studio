"""
StoryGenerationStep — generates the structured story script using the LLM provider.

The Story Service must NEVER directly import OllamaProvider or any concrete impl.
This step receives an LLMProvider through constructor injection.
"""
from __future__ import annotations

import structlog

from agents.interfaces.llm_provider import LLMProvider
from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class StoryGenerationStep(BaseStep):
    """
    Step 1 — Calls the LLM to generate a full story structure.

    Reads from context:
      - ctx.settings["story_prompt"]  : user's topic or theme
      - ctx.settings["episode_title"] : optional episode title
      - ctx.plugin_id                 : to load plugin-specific prompts

    Writes to context.step_results["story_generation"]:
      {
        "title": str,
        "synopsis": str,
        "scenes": list[{scene_number, title, setting, duration_hint}],
        "characters": list[{name, archetype, description}],
        "themes": list[str],
        "raw_llm_output": str,
      }
    """

    retry_policy = RetryPolicy(max_retries=3, base_delay=5.0, max_delay=60.0)

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    @property
    def name(self) -> str:
        return "story_generation"

    @property
    def description(self) -> str:
        return "Generating story script with LLM"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        settings = ctx.settings
        story_prompt = settings.get("story_prompt", "A heartwarming family comedy episode")
        episode_title = settings.get("episode_title", "")
        scene_count = settings.get("scene_count", 5)
        language = settings.get("language", "Telugu")

        # Load plugin-specific context if available
        plugin_context = await self._get_plugin_context(ctx)

        system_prompt = self._build_system_prompt(language, plugin_context)
        user_prompt = self._build_user_prompt(
            story_prompt=story_prompt,
            episode_title=episode_title,
            scene_count=scene_count,
            language=language,
            plugin_context=plugin_context,
        )

        logger.info(
            "story_generation_start",
            run_id=ctx.run_id,
            story_id=ctx.story_id,
            llm_provider=self._llm.provider_name,
        )

        raw_output = await self._llm.generate_text(
            user_prompt,
            system=system_prompt,
            temperature=0.8,
            max_tokens=6000,
        )

        story_data = await self._parse_story_output(raw_output, scene_count)
        story_data["raw_llm_output"] = raw_output

        logger.info(
            "story_generation_complete",
            run_id=ctx.run_id,
            scenes=len(story_data.get("scenes", [])),
            characters=len(story_data.get("characters", [])),
        )

        ctx.set_step_result(self.name, story_data)
        return StepResult(success=True, output=story_data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_plugin_context(self, ctx: WorkflowContext) -> dict:
        """Try to load plugin-specific prompts and defaults."""
        try:
            from plugins.registry import get_registry
            registry = get_registry()
            plugin = registry.get_plugin(ctx.plugin_id)
            if plugin:
                return plugin.get_prompt_context()
        except Exception:
            pass
        return {}

    def _build_system_prompt(self, language: str, plugin_context: dict) -> str:
        genre = plugin_context.get("genre", "family comedy")
        tone = plugin_context.get("tone", "warm, humorous, family-friendly")
        return (
            f"You are a professional {language} {genre} script writer. "
            f"Write in a {tone} tone. "
            "Your output must be a valid JSON object with the exact structure shown. "
            "All dialogue must be written in the target language with natural conversational flow. "
            "Reply with ONLY the JSON object — no markdown, no explanation."
        )

    def _build_user_prompt(
        self,
        story_prompt: str,
        episode_title: str,
        scene_count: int,
        language: str,
        plugin_context: dict,
    ) -> str:
        characters_hint = plugin_context.get("default_characters", [])
        char_str = "\n".join(f"- {c}" for c in characters_hint) if characters_hint else "Create appropriate characters"

        title_hint = f'Episode title: "{episode_title}"\n' if episode_title else ""

        return f"""Write a complete {language} family comedy episode.

{title_hint}Theme/Prompt: {story_prompt}

Available characters:
{char_str}

Generate EXACTLY {scene_count} scenes.

Return this JSON structure:
{{
  "title": "Episode title in {language}",
  "synopsis": "2-3 sentence summary in English",
  "characters": [
    {{
      "name": "Character name",
      "archetype": "archetype key e.g. grandfather",
      "description": "brief personality description",
      "voice_style": "voice direction note"
    }}
  ],
  "scenes": [
    {{
      "scene_number": 1,
      "title": "Scene title",
      "setting": "location description",
      "duration_hint_seconds": 30,
      "characters_present": ["name1", "name2"],
      "action": "What happens in this scene (narration in English)",
      "dialogue": [
        {{
          "character": "Name",
          "line": "Dialogue in {language}",
          "emotion": "happy|sad|angry|surprised|neutral",
          "timing_note": "optional delivery note"
        }}
      ],
      "mood": "scene mood",
      "visual_description": "What the scene looks like for image generation"
    }}
  ],
  "themes": ["theme1", "theme2"],
  "moral": "Episode moral/lesson in English"
}}"""

    async def _parse_story_output(self, raw: str, expected_scenes: int) -> dict:
        """Parse LLM JSON output with graceful fallback."""
        import json
        import re

        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON object substring
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                # Fallback minimal structure
                data = {
                    "title": "Generated Episode",
                    "synopsis": raw[:300],
                    "characters": [],
                    "scenes": [],
                    "themes": [],
                    "moral": "",
                }
        return data
