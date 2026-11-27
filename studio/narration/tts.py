"""Pluggable local TTS interface, deterministic fallback synthesizer, and audio normalization."""

from __future__ import annotations

import math
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class NarrationAudio:
    path: Path
    duration_sec: float
    sample_rate: int
    backend: str


class TTSBackend(Protocol):
    name: str

    def synthesize(self, text: str, output_path: Path, voice: str = "default") -> NarrationAudio:
        ...


class FallbackToneTTS:
    """Offline fallback synthesizer that produces a valid, paced WAV file when no neural TTS is installed."""

    name = "fallback_tone"

    def synthesize(self, text: str, output_path: Path, voice: str = "default") -> NarrationAudio:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        words = max(1, len((text or "").split()))
        duration_sec = max(1.0, round(words / 2.5, 2))
        sample_rate = 22050
        num_samples = int(duration_sec * sample_rate)

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # Soft, low-amplitude 220Hz tone so audio streams are valid and measurable.
            frames = bytearray()
            amp = 1200
            for i in range(num_samples):
                val = int(amp * math.sin(2.0 * math.pi * 220.0 * (i / sample_rate)))
                frames.extend(struct.pack("<h", val))
            wf.writeframes(bytes(frames))

        return NarrationAudio(
            path=output_path,
            duration_sec=duration_sec,
            sample_rate=sample_rate,
            backend=self.name,
        )


def normalize_audio(input_path: Path, output_path: Path) -> Path:
    """Normalize narration audio using ffmpeg loudnorm."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(input_path),
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar",
        "44100",
        "-ac",
        "1",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output_path
