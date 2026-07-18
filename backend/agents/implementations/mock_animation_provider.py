"""
Phase 7 — Mock Animation Provider.

Returns deterministic synthetic results with minimal external dependencies.
Follows the same pattern as MockImageProvider (Phase 6).

FIX (2026-07-18, rev 2): Phase 1 of this fix returned a pure-Python
MINIMAL_MP4_STUB (~493 bytes) which FFmpeg cannot open via its concat demuxer
because the container has an empty stsd box (no codec description).

Correct approach: generate a real, FFmpeg-decodable clip via FFmpeg itself —
a 16×16 black libx264 frame, 1 second, AAC-silent audio.  This produces
several KB of bytes that FFmpeg can concat directly.  When FFmpeg is not
available (e.g. pure-Python CI environments), the provider falls back to
MINIMAL_MP4_STUB so tests continue to exercise the storage/DB path.

The VideoAssemblyService uses a 1 KB file-size threshold to decide whether to
call _ffmpeg_assemble() or _mock_assemble().  FFmpeg-generated clips (several
KB) exceed this threshold; the pure-Python fallback stub (~493 bytes) stays
below it, so it correctly routes to the mock-assemble path.
"""
from __future__ import annotations

import asyncio
import hashlib
import tempfile
from pathlib import Path
from typing import Any

from agents.interfaces.animation_provider import (
    AnimationProvider,
    AnimationRenderRequest,
    AnimationRenderResult,
)
from packages.utils.mp4_stub import MINIMAL_MP4_STUB


class MockAnimationProvider(AnimationProvider):
    """
    Mock provider that generates a genuinely FFmpeg-decodable clip when
    FFmpeg is available, falling back to a pure-Python container stub when
    it is not.

    The storage_key is always deterministic (same inputs → same key).
    The video_bytes are not deterministic when FFmpeg is used (encoding
    includes timestamps), but that is acceptable — the key, not the bytes,
    is what the DB uses for deduplication.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def render_scene(self, request: AnimationRenderRequest) -> AnimationRenderResult:
        # Deterministic key derived from scene_id + character count + duration
        fingerprint = f"{request.scene_id}:{len(request.characters)}:{request.duration_seconds}"
        storage_key = (
            f"animations/mock/{request.project_id}/"
            f"scene_{request.scene_id}_{hashlib.md5(fingerprint.encode()).hexdigest()[:8]}.mp4"
        )

        # Try to produce a genuinely FFmpeg-decodable clip.  Falls back to the
        # pure-Python stub if FFmpeg is absent (e.g. pure-CI environments).
        video_bytes = await self._generate_ffmpeg_clip(
            duration_seconds=request.duration_seconds,
            width=request.width,
            height=request.height,
        )
        if video_bytes is None:
            # FFmpeg unavailable — use the container stub.  The file-size
            # threshold in VideoAssemblyService._have_real_files() (>= 1 KB)
            # will keep these stub rows out of the FFmpeg assembly path.
            video_bytes = MINIMAL_MP4_STUB

        return AnimationRenderResult(
            video_bytes=video_bytes,
            storage_key=storage_key,
            duration_seconds=request.duration_seconds,
            file_size_bytes=len(video_bytes),
            width=request.width,
            height=request.height,
            fps=request.fps,
            format=request.output_format,
            provider=self.provider_name,
            metadata={
                "scene_id": request.scene_id,
                "characters": len(request.characters),
                "camera_motion": request.camera_motion,
                "dialogue_segments": len(request.dialogue_segments),
                "mock": True,
                "ffmpeg_generated": video_bytes is not MINIMAL_MP4_STUB,
            },
        )

    async def _generate_ffmpeg_clip(
        self,
        duration_seconds: float,
        width: int = 16,
        height: int = 16,
    ) -> bytes | None:
        """
        Generate a tiny real MP4 clip using FFmpeg.

        Uses a 16×16 resolution regardless of the requested width/height to
        keep encoding fast (< 1 second) and the output small (a few KB).
        The clip is a black frame with silent audio — suitable as a placeholder
        that FFmpeg can actually decode and concatenate.

        Returns None if FFmpeg is not available or encoding fails.
        """
        # Cap duration to 2 seconds so test suites stay fast.
        capped = min(max(duration_seconds, 0.1), 2.0)
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                out = Path(tmp_dir) / "mock_clip.mp4"
                # Video-only clip (no audio track).  Silent-audio muxing needs
                # exact filter syntax that varies by FFmpeg version; omitting
                # audio (-an) keeps the command portable and the file small.
                # Concat demux works fine with video-only tracks.
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=c=black:s=16x16:r=24:d={capped:.3f}",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-an",                   # no audio track — keeps it portable
                    "-movflags", "+faststart",
                    str(out),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                if proc.returncode == 0 and out.stat().st_size > 0:
                    return out.read_bytes()
        except Exception:
            pass
        return None

    async def is_available(self) -> bool:
        return True
