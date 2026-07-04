import asyncio
import io
import tempfile
from pathlib import Path
from typing import Any

from agents.interfaces.tts_provider import TTSProvider, TTSRequest, TTSResult
from packages.core.exceptions import ProviderError


class PiperTTSProvider(TTSProvider):
    """TTS provider using local Piper TTS binary."""

    def __init__(self, piper_binary: str = "piper", models_dir: str = "/models/piper") -> None:
        self._binary = piper_binary
        self._models_dir = Path(models_dir)

    @property
    def provider_name(self) -> str:
        return "piper_tts"

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        model_path = self._models_dir / request.language
        if not model_path.exists():
            model_path = self._models_dir / "en"

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name

        try:
            cmd = [
                self._binary,
                "--model", str(model_path),
                "--output_file", out_path,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate(input=request.text.encode("utf-8"))

            audio_bytes = Path(out_path).read_bytes()
            return TTSResult(
                audio_bytes=audio_bytes,
                duration_seconds=0.0,
                format="wav",
                sample_rate=22050,
                metadata={"model": str(model_path)},
            )
        except Exception as e:
            raise ProviderError("piper_tts", str(e)) from e
        finally:
            Path(out_path).unlink(missing_ok=True)

    async def list_voices(self, language: str | None = None) -> list[dict[str, Any]]:
        voices = []
        try:
            for model_dir in self._models_dir.iterdir():
                if model_dir.is_dir():
                    voices.append({"id": model_dir.name, "name": model_dir.name, "language": model_dir.name})
        except Exception:
            pass
        return voices

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
