"""
VoiceGenerationStep — generates TTS audio for each dialogue line in each scene.
Uses the TTSProvider interface — never imports PiperTTSProvider directly.
"""
from __future__ import annotations

import asyncio
import base64

import structlog

from agents.interfaces.tts_provider import TTSProvider, TTSRequest
from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class VoiceGenerationStep(BaseStep):
    """
    Step 5 — Generates audio for all dialogue lines using TTSProvider.

    Reads from context.step_results["scene_breakdown"]["scenes"]
    Reads from context.step_results["character_resolution"]["characters"]
    Reads from context.settings["language"]

    Writes to context.step_results["voice_generation"]:
      {
        "audio_by_scene": {
          scene_number: [
            {
              "character": str,
              "line": str,
              "audio_b64": str,
              "duration_seconds": float,
              "format": str,
            }
          ]
        },
        "total_lines": int,
        "total_duration_seconds": float,
      }
    """

    retry_policy = RetryPolicy(max_retries=3, base_delay=3.0, max_delay=30.0)

    def __init__(self, tts: TTSProvider) -> None:
        self._tts = tts

    @property
    def name(self) -> str:
        return "voice_generation"

    @property
    def description(self) -> str:
        return "Generating voice audio"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        scene_data = ctx.get_step_result("scene_breakdown", {})
        char_data = ctx.get_step_result("character_resolution", {})
        scenes = scene_data.get("scenes", [])
        language = ctx.settings.get("language", "te")  # Telugu ISO code

        # Build character → voice mapping
        voice_map = {
            c["name"]: c.get("voice_style", "neutral")
            for c in char_data.get("characters", [])
        }

        logger.info("voice_generation_start", run_id=ctx.run_id, scenes=len(scenes))

        semaphore = asyncio.Semaphore(2)  # limit concurrent TTS calls
        audio_by_scene: dict[str, list[dict]] = {}
        total_lines = 0
        total_duration = 0.0

        async def _synthesize_line(scene_num: str, dialogue: dict) -> dict:
            character = dialogue.get("character", "Narrator")
            line = dialogue.get("line", "")
            if not line.strip():
                return {"character": character, "line": line, "audio_b64": "", "duration_seconds": 0.0, "format": "wav"}

            voice_id = voice_map.get(character, "")
            async with semaphore:
                try:
                    result = await self._tts.synthesize(
                        TTSRequest(
                            text=line,
                            language=language,
                            voice_id=voice_id,
                            speed=ctx.settings.get("tts_speed", 1.0),
                        )
                    )
                    return {
                        "character": character,
                        "line": line,
                        "audio_b64": base64.b64encode(result.audio_bytes).decode(),
                        "duration_seconds": result.duration_seconds,
                        "format": result.format,
                        "emotion": dialogue.get("emotion", "neutral"),
                    }
                except Exception as exc:
                    logger.warning("tts_line_failed", character=character, error=str(exc))
                    return {
                        "character": character,
                        "line": line,
                        "audio_b64": "",
                        "duration_seconds": 0.0,
                        "format": "wav",
                        "error": str(exc),
                    }

        for scene in scenes:
            scene_num = str(scene.get("scene_number", 0))
            dialogue_lines = scene.get("dialogue", [])
            if not dialogue_lines:
                audio_by_scene[scene_num] = []
                continue

            tasks = [_synthesize_line(scene_num, d) for d in dialogue_lines]
            scene_audio = await asyncio.gather(*tasks)
            audio_by_scene[scene_num] = list(scene_audio)
            total_lines += len(scene_audio)
            total_duration += sum(a.get("duration_seconds", 0.0) for a in scene_audio)

        output = {
            "audio_by_scene": audio_by_scene,
            "total_lines": total_lines,
            "total_duration_seconds": round(total_duration, 2),
        }
        ctx.set_step_result(self.name, output)
        logger.info("voice_generation_complete", run_id=ctx.run_id, total_lines=total_lines)
        return StepResult(success=True, output=output)
