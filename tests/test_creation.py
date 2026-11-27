"""Tests for Phase 4: original script and semantic storyboard generation."""

import unittest
from unittest.mock import patch

from studio.assets.catalog import AssetCatalog, AssetItem
from studio.creation.research import build_research_brief
from studio.creation.script import generate_script, sanitize_untrusted
from studio.creation.storyboard import build_storyboard


def _catalog() -> AssetCatalog:
    return AssetCatalog(
        project_id="proj_4",
        source_path="src.mp4",
        target_count=2,
        extracted_count=2,
        rejected_quality=0,
        rejected_duplicate=0,
        shortfall=0,
        shortfall_reason="",
        contact_sheet_path=None,
        assets=[
            AssetItem("asset_0001", "f1.jpg", "t1.jpg", 1.0, 1280, 720, "a" * 64, "0" * 16, 20.0, 120.0),
            AssetItem("asset_0002", "f2.jpg", "t2.jpg", 5.0, 1280, 720, "b" * 64, "f" * 16, 25.0, 125.0),
        ],
    )


class TestCreation(unittest.TestCase):
    def test_sanitize_untrusted(self):
        raw = "Hello\x00\x07 world\n" + ("x" * 2000)
        cleaned = sanitize_untrusted(raw, max_len=50)
        self.assertEqual(len(cleaned), 50)
        self.assertNotIn("\x00", cleaned)

    def test_script_and_storyboard_offline_fallback(self):
        catalog = _catalog()
        brief = build_research_brief(
            catalog,
            topic="Ocean Currents",
            transcript_segments=[
                {"start": 0.0, "end": 3.0, "text": "Warm currents move heat toward the poles."},
                {"start": 4.0, "end": 7.0, "text": "Deep cold water returns along the ocean floor."},
            ],
        )
        with patch("studio.creation.script.ai.ready", return_value=False):
            script = generate_script(brief, target_duration_sec=20.0)
        self.assertGreaterEqual(len(script.beats), 1)
        self.assertTrue(script.full_narration())

        sb = build_storyboard(script, brief, catalog, aspect_ratio="9:16")
        self.assertEqual(len(sb.scenes), len(script.beats))
        valid_ids = {a.asset_id for a in catalog.assets}
        for scene in sb.scenes:
            self.assertIn(scene.asset_id, valid_ids)


if __name__ == "__main__":
    unittest.main()
