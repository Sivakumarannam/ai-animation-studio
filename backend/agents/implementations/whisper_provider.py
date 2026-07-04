import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any

from agents.interfaces.subtitle_provider import SubtitleProvider, SubtitleResult, SubtitleSegment
from packages.core.exceptions import ProviderError


class WhisperProvider(SubtitleProvider):
    """Subtitle provider using local OpenAI Whisper (whisper.cpp or Python whisper)."""

    def __init__(self, model: str = "base", whisper_binary: str = "whisper") -> None:
        self._model = model
        self._binary = whisper_binary

    @property
    def provider_name(self) -> str:
        return f"whisper/{self._model}"

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str | None = None,
        output_format: str = "srt",
    ) -> SubtitleResult:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            audio_path = tmp.name

        with tempfile.TemporaryDirectory() as out_dir:
            cmd = [
                self._binary,
                audio_path,
                "--model", self._model,
                "--output_dir", out_dir,
                "--output_format", "json",
            ]
            if language:
                cmd += ["--language", language]

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()

                json_files = list(Path(out_dir).glob("*.json"))
                if not json_files:
                    return SubtitleResult(segments=[], full_text="", language=language or "en", metadata={})

                data = json.loads(json_files[0].read_text())
                segments = [
                    SubtitleSegment(
                        start_seconds=seg["start"],
                        end_seconds=seg["end"],
                        text=seg["text"].strip(),
                        language=language or data.get("language", "en"),
                    )
                    for seg in data.get("segments", [])
                ]
                full_text = " ".join(s.text for s in segments)
                return SubtitleResult(
                    segments=segments,
                    full_text=full_text,
                    language=language or data.get("language", "en"),
                    metadata={"model": self._model},
                )
            except Exception as e:
                raise ProviderError("whisper", str(e)) from e
            finally:
                Path(audio_path).unlink(missing_ok=True)

    async def is_available(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._binary, "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return True
        except Exception:
            return False
