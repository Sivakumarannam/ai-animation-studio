import asyncio
import tempfile
from pathlib import Path
from typing import Any

from agents.interfaces.renderer_provider import RenderRequest, RenderResult, RendererProvider
from packages.core.exceptions import ProviderError


class FFmpegRenderer(RendererProvider):
    """Video renderer using FFmpeg."""

    def __init__(self, ffmpeg_binary: str = "ffmpeg") -> None:
        self._binary = ffmpeg_binary

    @property
    def provider_name(self) -> str:
        return "ffmpeg"

    async def render(self, request: RenderRequest) -> RenderResult:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            output_path = tmp_path / f"output.{request.output_format}"

            concat_file = tmp_path / "concat.txt"
            scene_files: list[Path] = []

            for i, scene in enumerate(request.scenes):
                scene_output = tmp_path / f"scene_{i:04d}.mp4"
                cmd = [
                    self._binary, "-y",
                    "-loop", "1", "-i", scene.background_url,
                    "-i", scene.audio_url,
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-t", str(scene.duration_seconds),
                    "-vf", f"scale={request.resolution[0]}:{request.resolution[1]}",
                    str(scene_output),
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise ProviderError("ffmpeg", f"Scene {i} render failed: {stderr.decode()}")
                scene_files.append(scene_output)

            with concat_file.open("w") as f:
                for sf in scene_files:
                    f.write(f"file '{sf}'\n")

            concat_cmd = [
                self._binary, "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *concat_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise ProviderError("ffmpeg", f"Concat failed: {stderr.decode()}")

            video_bytes = output_path.read_bytes()
            total_duration = sum(s.duration_seconds for s in request.scenes)
            return RenderResult(
                video_bytes=video_bytes,
                duration_seconds=total_duration,
                file_size_bytes=len(video_bytes),
                format=request.output_format,
                resolution=request.resolution,
                metadata={"scenes": len(request.scenes)},
            )

    async def is_available(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._binary, "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False
