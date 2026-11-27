"""Local TTS synthesis, audio normalization, word alignment, and caption cues."""

from studio.narration.align import CaptionCue, WordTiming, align_words, build_caption_cues
from studio.narration.tts import FallbackToneTTS, NarrationAudio, TTSBackend, normalize_audio

__all__ = [
    "CaptionCue",
    "FallbackToneTTS",
    "NarrationAudio",
    "TTSBackend",
    "WordTiming",
    "align_words",
    "build_caption_cues",
    "normalize_audio",
]
