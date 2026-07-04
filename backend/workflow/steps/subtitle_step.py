"""
SubtitleGenerationStep — generates SRT/VTT subtitle files from dialogue audio.
Uses SubtitleProvider interface — backs onto Whisper but provider-agnostic.
"""
from __future__ import annotations

import asyncio
import base64

import structlog

from agents.interfaces.subtitle_provider import SubtitleProvider
from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class SubtitleGenerationStep(BaseStep):
    """
    Step 6 — Transcribes TTS audio back to timed subtitle segments.

    Reads from context.step_results["voice_generation"]["audio_by_scene"]
    Reads from context.settings["subtitle_language", "subtitle_format"]

    Writes to context.step_results["subtitle_generation"]:
      {
        "subtitles_by_scene": {
          scene_number: {
            "srt": str,           # SRT formatted subtitles
            "segments": list,     # raw SubtitleSegment dicts
          }
        },
        "total_segments": int,
      }
    """

    retry_policy = RetryPolicy(max_retries=2, base_delay=5.0)

    def __init__(self, subtitle_provider: SubtitleProvider) -> None:
        self._provider = subtitle_provider

    @property
    def name(self) -> str:
        return "subtitle_generation"

    @property
    def description(self) -> str:
        return "Generating subtitles"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        voice_data = ctx.get_step_result("voice_generation", {})
        audio_by_scene = voice_data.get("audio_by_scene", {})
        language = ctx.settings.get("subtitle_language", None)

        logger.info("subtitle_generation_start", run_id=ctx.run_id, scenes=len(audio_by_scene))

        semaphore = asyncio.Semaphore(2)
        subtitles_by_scene: dict[str, dict] = {}
        total_segments = 0

        async def _process_scene(scene_num: str, audio_lines: list[dict]) -> None:
            nonlocal total_segments
            # Concatenate all audio for this scene into one bytes buffer
            combined_bytes = b""
            for line in audio_lines:
                audio_b64 = line.get("audio_b64", "")
                if audio_b64:
                    combined_bytes += base64.b64decode(audio_b64)

            if not combined_bytes:
                subtitles_by_scene[scene_num] = {"srt": "", "segments": []}
                return

            async with semaphore:
                try:
                    result = await self._provider.transcribe(
                        combined_bytes, language=language, output_format="srt"
                    )
                    srt = self._segments_to_srt(result.segments)
                    subtitles_by_scene[scene_num] = {
                        "srt": srt,
                        "segments": [
                            {
                                "start": s.start_seconds,
                                "end": s.end_seconds,
                                "text": s.text,
                                "language": s.language,
                            }
                            for s in result.segments
                        ],
                    }
                    total_segments += len(result.segments)
                except Exception as exc:
                    logger.warning("subtitle_scene_failed", scene=scene_num, error=str(exc))
                    # Fall back to dialogue text as untimed subtitles
                    subtitles_by_scene[scene_num] = {
                        "srt": self._dialogue_fallback_srt(audio_lines),
                        "segments": [],
                    }

        await asyncio.gather(*[_process_scene(k, v) for k, v in audio_by_scene.items()])

        output = {
            "subtitles_by_scene": subtitles_by_scene,
            "total_segments": total_segments,
        }
        ctx.set_step_result(self.name, output)
        logger.info("subtitle_generation_complete", run_id=ctx.run_id, total_segments=total_segments)
        return StepResult(success=True, output=output)

    @staticmethod
    def _segments_to_srt(segments: list) -> str:
        lines = []
        for i, seg in enumerate(segments, 1):
            start = SubtitleGenerationStep._fmt_ts(seg.start_seconds)
            end = SubtitleGenerationStep._fmt_ts(seg.end_seconds)
            lines.append(f"{i}\n{start} --> {end}\n{seg.text}\n")
        return "\n".join(lines)

    @staticmethod
    def _fmt_ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _dialogue_fallback_srt(audio_lines: list[dict]) -> str:
        """Produce untimed SRT from dialogue text when Whisper isn't available."""
        lines = []
        t = 0.0
        for i, line in enumerate(audio_lines, 1):
            duration = max(line.get("duration_seconds", 3.0), 1.0)
            start = SubtitleGenerationStep._fmt_ts(t)
            end = SubtitleGenerationStep._fmt_ts(t + duration)
            text = line.get("line", "")
            char = line.get("character", "")
            lines.append(f"{i}\n{start} --> {end}\n[{char}]: {text}\n")
            t += duration
        return "\n".join(lines)
