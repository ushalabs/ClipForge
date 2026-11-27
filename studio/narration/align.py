"""Word-level forced alignment fallback and monotonic caption cue generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WordTiming:
    word: str
    start_sec: float
    end_sec: float


@dataclass(frozen=True)
class CaptionCue:
    index: int
    start_sec: float
    end_sec: float
    text: str
    words: list[WordTiming]

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "text": self.text,
            "words": [asdict(w) for w in self.words],
        }


def align_words(text: str, total_duration_sec: float) -> list[WordTiming]:
    """Distribute `text` words monotonically across `total_duration_sec`."""
    tokens = [t for t in (text or "").strip().split() if t]
    if not tokens or total_duration_sec <= 0:
        return []

    weights = [max(1, len(t)) for t in tokens]
    total_weight = sum(weights)
    timings: list[WordTiming] = []
    cursor = 0.0

    for idx, (tok, w) in enumerate(zip(tokens, weights)):
        slice_dur = (w / total_weight) * total_duration_sec
        start = round(cursor, 3)
        end = round(total_duration_sec if idx == len(tokens) - 1 else cursor + slice_dur, 3)
        if end <= start:
            end = round(start + 0.001, 3)
        timings.append(WordTiming(word=tok, start_sec=start, end_sec=end))
        cursor = end
    return timings


def build_caption_cues(
    word_timings: list[WordTiming],
    max_words_per_cue: int = 6,
) -> list[CaptionCue]:
    """Group word timings into non-overlapping, strictly monotonic caption cues."""
    if not word_timings:
        return []

    cues: list[CaptionCue] = []
    step = max(1, max_words_per_cue)
    for idx in range(0, len(word_timings), step):
        chunk = word_timings[idx : idx + step]
        cues.append(
            CaptionCue(
                index=len(cues) + 1,
                start_sec=chunk[0].start_sec,
                end_sec=chunk[-1].end_sec,
                text=" ".join(w.word for w in chunk),
                words=chunk,
            )
        )
    return cues
