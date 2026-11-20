"""Tests for YouTube channel features: RSS parsing, heatmap/chapter markers, split layout, quota tracking."""
import unittest

from studio import accounts, brain, media, render


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>abc123XYZ00</yt:videoId>
    <title>Test Upload Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123XYZ00"/>
    <published>2026-11-20T00:00:00+00:00</published>
  </entry>
</feed>
"""


class YouTubeTests(unittest.TestCase):
    def test_parse_rss(self):
        vids = media.parse_rss(SAMPLE_RSS, limit=5)
        self.assertEqual(len(vids), 1)
        self.assertEqual(vids[0]["id"], "abc123XYZ00")
        self.assertEqual(vids[0]["title"], "Test Upload Title")
        self.assertIn("abc123XYZ00", vids[0]["url"])

    def test_peak_and_chapter_markers(self):
        words = [{"w": "hello", "s": 10.0, "e": 10.4}, {"w": "world", "s": 10.5, "e": 11.0}]
        lines = brain.make_lines(words, peaks=[(9.5, 12.0)])
        self.assertTrue(lines[0]["peak"])
        self.assertIn("(PEAK)", brain._fmt(lines))
        note = brain._chapters_note([{"start": 0.0, "end": 30.0, "title": "Intro"}], 0, 20)
        self.assertIn("Intro", note)

    def test_split_layout(self):
        layout, fg_h, hook_y, cap_y = render.geometry(1920, 1080, "split")
        self.assertEqual(layout, "split")
        self.assertEqual(fg_h, render.H)
        fc = render._filter("split", fg_h)
        self.assertIn("vstack=inputs=2", fc)

    def test_quota_tracker(self):
        q = accounts.youtube_quota_used()
        self.assertIn("used", q)
        self.assertEqual(q["limit"], 10000)


if __name__ == "__main__":
    unittest.main()
