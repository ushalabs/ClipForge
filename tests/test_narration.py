"""Tests for Phase 5: local TTS fallback, audio normalization, word alignment, and monotonic cues."""

import tempfile
import unittest
from pathlib import Path

from studio.narration import FallbackToneTTS, align_words, build_caption_cues, normalize_audio


class TestNarration(unittest.TestCase):
    def test_tts_and_normalize(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            raw_wav = tmp_dir / "raw.wav"
            norm_wav = tmp_dir / "norm.wav"
            tts = FallbackToneTTS()
            audio = tts.synthesize("Hello world this is a test narration.", raw_wav)
            self.assertTrue(audio.path.exists())
            self.assertGreater(audio.duration_sec, 0.5)

            out = normalize_audio(raw_wav, norm_wav)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 1000)

    def test_word_alignment_and_monotonic_cues(self):
        text = "One two three four five six seven eight nine ten"
        words = align_words(text, total_duration_sec=5.0)
        self.assertEqual(len(words), 10)
        for i, w in enumerate(words):
            self.assertLess(w.start_sec, w.end_sec)
            if i > 0:
                self.assertGreaterEqual(w.start_sec, words[i - 1].end_sec)

        cues = build_caption_cues(words, max_words_per_cue=4)
        self.assertEqual(len(cues), 3)
        for i, c in enumerate(cues):
            self.assertLess(c.start_sec, c.end_sec)
            if i > 0:
                self.assertGreaterEqual(c.start_sec, cues[i - 1].end_sec)


if __name__ == "__main__":
    unittest.main()
