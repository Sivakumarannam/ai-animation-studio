"""
VideoRenderStep — renders the final video from all generated assets.
Uses RendererProvider interface — never imports FFmpegRenderer directly.
"""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import structlog

from agents.interfaces.renderer_provider import RenderRequest, RendererProvider, SceneRenderSpec
from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class VideoRenderStep(BaseStep):
    """
    Step 7 — Final render: combines backgrounds + audio + subtitles into MP4.

    Reads from context.step_results:
      - "scene_breakdown"   : scene list
      - "asset_generation"  : background images
      - "voice_generation"  : audio per scene
      - "subtitle_generation": subtitle segments

    Writes to context.step_results["video_render"]:
      {
        "video_b64": str,        # base64-encoded MP4 (for small videos)
        "video_path": str,       # temp path (for large videos)
        "duration_seconds": float,
        "file_size_bytes": int,
        "format": str,
      }
    """

    retry_policy = RetryPolicy(max_retries=1, base_delay=10.0)

    def __init__(self, renderer: RendererProvider) -> None:
        self._renderer = renderer

    @property
    def name(self) -> str:
        return "video_render"

    @property
    def description(self) -> str:
        return "Rendering final video"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        scene_data = ctx.get_step_result("scene_breakdown", {})
        asset_data = ctx.get_step_result("asset_generation", {})
        voice_data = ctx.get_step_result("voice_generation", {})
        subtitle_data = ctx.get_step_result("subtitle_generation", {})

        scenes = scene_data.get("scenes", [])
        backgrounds = asset_data.get("backgrounds", {})
        audio_by_scene = voice_data.get("audio_by_scene", {})
        subtitles_by_scene = subtitle_data.get("subtitles_by_scene", {})

        resolution = (
            ctx.settings.get("video_width", 1280),
            ctx.settings.get("video_height", 720),
        )
        fps = ctx.settings.get("fps", 24)

        logger.info("video_render_start", run_id=ctx.run_id, scenes=len(scenes))

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            # Write assets to temp files for FFmpeg
            scene_specs: list[SceneRenderSpec] = []
            for scene in scenes:
                scene_num = str(scene.get("scene_number", 0))

                # Background
                bg = backgrounds.get(scene_num, {})
                bg_b64 = bg.get("image_bytes_b64", "")
                bg_path = str(tmp / f"bg_{scene_num}.png")
                if bg_b64:
                    (tmp / f"bg_{scene_num}.png").write_bytes(base64.b64decode(bg_b64))
                else:
                    # Write a blank black image if background failed
                    self._write_blank_image(bg_path, resolution)

                # Audio (concatenate all dialogue lines for this scene)
                audio_lines = audio_by_scene.get(scene_num, [])
                combined_audio = b"".join(
                    base64.b64decode(l["audio_b64"])
                    for l in audio_lines
                    if l.get("audio_b64")
                )
                audio_path = str(tmp / f"audio_{scene_num}.wav")
                if combined_audio:
                    (tmp / f"audio_{scene_num}.wav").write_bytes(combined_audio)
                else:
                    self._write_silence(audio_path, scene.get("duration_hint_seconds", 5))

                # Subtitles
                subs = subtitles_by_scene.get(scene_num, {})
                subtitle_segments = subs.get("segments", [])

                duration = scene.get("duration_hint_seconds", 5.0)
                if audio_lines:
                    duration = sum(l.get("duration_seconds", 0.0) for l in audio_lines) or duration

                scene_specs.append(SceneRenderSpec(
                    scene_id=scene_num,
                    background_url=bg_path,
                    character_frames=[],  # future: character sprites
                    audio_url=audio_path,
                    subtitle_segments=subtitle_segments,
                    duration_seconds=max(duration, 1.0),
                    resolution=resolution,
                ))

            if not scene_specs:
                return StepResult(success=False, error="No scenes to render")

            render_req = RenderRequest(
                story_id=ctx.story_id,
                scenes=scene_specs,
                output_format="mp4",
                fps=fps,
                resolution=resolution,
            )

            result = await self._renderer.render(render_req)

        # Store result (only b64 for small videos < 50MB; path otherwise)
        output: dict = {
            "duration_seconds": result.duration_seconds,
            "file_size_bytes": result.file_size_bytes,
            "format": result.format,
        }
        if result.file_size_bytes < 50 * 1024 * 1024:
            output["video_b64"] = base64.b64encode(result.video_bytes).decode()
        else:
            # For large videos, write to a well-known temp location
            out_path = f"/tmp/render_{ctx.run_id}.mp4"
            Path(out_path).write_bytes(result.video_bytes)
            output["video_path"] = out_path

        ctx.set_step_result(self.name, output)
        logger.info(
            "video_render_complete",
            run_id=ctx.run_id,
            duration=result.duration_seconds,
            size_mb=round(result.file_size_bytes / 1024 / 1024, 2),
        )
        return StepResult(success=True, output=output)

    @staticmethod
    def _write_blank_image(path: str, resolution: tuple[int, int]) -> None:
        try:
            from PIL import Image
            img = Image.new("RGB", resolution, color=(0, 0, 0))
            img.save(path, "PNG")
        except Exception:
            # Minimal 1x1 black PNG
            Path(path).write_bytes(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
                b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
                b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
            )

    @staticmethod
    def _write_silence(path: str, duration_seconds: float) -> None:
        """Write a WAV file of silence."""
        import struct
        import wave
        sample_rate = 22050
        num_samples = int(sample_rate * duration_seconds)
        with wave.open(path, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
