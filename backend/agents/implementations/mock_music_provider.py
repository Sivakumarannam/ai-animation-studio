"""
Phase 9 — Mock Music Provider.

Deterministic, zero-dependency music backend for development/testing.
Mirrors MockAnimationProvider / MockVoiceProvider shape exactly (Phase 7-8 pattern).

Generates a real (playable) short WAV file using Python's built-in `wave`
and `struct` modules — a simple sine tone whose frequency maps to the mood.
No external dependencies required.
"""
from __future__ import annotations

import hashlib
import io
import math
import struct
import wave

from agents.interfaces.music_provider import (
    MusicGenerationRequest,
    MusicGenerationResult,
    MusicProvider,
)

# Mood → base frequency (Hz) so different moods produce audibly different tones.
_MOOD_FREQ: dict[str, float] = {
    "comedy":    440.0,   # A4  — bright, lively
    "happy":     523.25,  # C5  — cheerful
    "adventure": 392.0,   # G4  — heroic
    "victory":   659.25,  # E5  — triumphant
    "tension":   311.13,  # Eb4 — dissonant
    "sad":       293.66,  # D4  — melancholic
    "neutral":   369.99,  # F#4 — balanced
}
_DEFAULT_FREQ = 440.0
_SAMPLE_RATE = 44100
_AMPLITUDE = 16000   # out of 32767 (16-bit PCM)


def _generate_sine_wav(
    frequency: float,
    duration_seconds: float,
    sample_rate: int = _SAMPLE_RATE,
) -> bytes:
    """
    Produce a raw WAV file in memory: a pure sine tone with a 20 ms
    linear fade-in/out to avoid clicks.
    """
    num_samples = int(sample_rate * duration_seconds)
    fade_samples = int(sample_rate * 0.02)  # 20 ms fade

    samples: list[int] = []
    for i in range(num_samples):
        raw = math.sin(2.0 * math.pi * frequency * i / sample_rate) * _AMPLITUDE
        # Fade in
        if i < fade_samples:
            raw *= i / fade_samples
        # Fade out
        elif i >= num_samples - fade_samples:
            raw *= (num_samples - i) / fade_samples
        samples.append(int(raw))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)       # mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


class MockMusicProvider(MusicProvider):
    """
    Zero-dependency mock that returns a deterministic short WAV tone.
    The mood maps to a distinct musical pitch so callers can tell them apart.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_track(self, request: MusicGenerationRequest) -> MusicGenerationResult:
        freq = _MOOD_FREQ.get(request.mood.lower(), _DEFAULT_FREQ)

        # Keep mock tracks short (max 3 s) to avoid slow tests
        duration = min(request.duration_seconds, 3.0)
        audio_bytes = _generate_sine_wav(freq, duration)

        # Deterministic storage key
        fingerprint = (
            f"{request.project_id}:{request.scene_id}:{request.mood}:{request.loop_type}"
        )
        key_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:8]
        storage_key = (
            f"music/mock/{request.project_id}/{request.scene_id or 'episode'}/"
            f"{request.mood}_{key_hash}.{request.output_format}"
        )

        return MusicGenerationResult(
            audio_bytes=audio_bytes,
            storage_key=storage_key,
            duration_seconds=duration,
            sample_rate=_SAMPLE_RATE,
            format=request.output_format,
            file_size_bytes=len(audio_bytes),
            copyright_safe=True,
            provider=self.provider_name,
            metadata={
                "mood": request.mood,
                "frequency_hz": freq,
                "loop_type": request.loop_type,
                "bpm": request.bpm or 120,
                "instruments": request.instruments or ["mock_synth"],
                "mock": True,
            },
        )

    async def is_available(self) -> bool:
        return True
