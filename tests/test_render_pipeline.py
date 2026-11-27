"""Tests for Phase 7: render orchestration and ffprobe quality gates."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from studio.assets.catalog import AssetCatalog, AssetItem
from studio.creation.render_pipeline import build_render_manifest, render_from_manifest
from studio.creation.storyboard import Storyboard, StoryboardScene
from studio.narration import FallbackToneTTS, align_words, build_caption_cues


class TestRenderPipeline(unittest.TestCase):
    def test_render_and_quality_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            img1 = tmp_dir / "f1.jpg"
            img2 = tmp_dir / "f2.jpg"
            Image.new("RGB", (640, 360), (40, 120, 200)).save(img1)
            Image.new("RGB", (640, 360), (200, 80, 40)).save(img2)

            catalog = AssetCatalog(
                project_id="proj_7",
                source_path="src.mp4",
                target_count=2,
                extracted_count=2,
                rejected_quality=0,
                rejected_duplicate=0,
                shortfall=0,
                shortfall_reason="",
                contact_sheet_path=None,
                assets=[
                    AssetItem("asset_0001", str(img1), str(img1), 1.0, 640, 360, "a" * 64, "0" * 16, 20.0, 120.0),
                    AssetItem("asset_0002", str(img2), str(img2), 3.0, 640, 360, "b" * 64, "f" * 16, 20.0, 120.0),
                ],
            )
            sb = Storyboard(
                project_id="proj_7",
                title="Render Test",
                aspect_ratio="9:16",
                scenes=[
                    StoryboardScene("scene_01", "beat_01", "asset_0001", "First scene", "blue", 1.5),
                    StoryboardScene("scene_02", "beat_02", "asset_0002", "Second scene", "red", 1.5),
                ],
            )
            wav = tmp_dir / "narration.wav"
            audio = FallbackToneTTS().synthesize("First scene. Second scene.", wav)
            cues = build_caption_cues(align_words("First scene. Second scene.", audio.duration_sec))

            manifest = build_render_manifest(sb, catalog, wav, cues)
            out_mp4 = tmp_dir / "out.mp4"
            report = render_from_manifest(manifest, out_mp4)

            self.assertTrue(report.passed, msg=f"Quality gate failed: {report.errors}")
            self.assertEqual((report.width, report.height), (1080, 1920))
            self.assertTrue(report.has_video)
            self.assertTrue(report.has_audio)
            self.assertGreaterEqual(report.duration_sec, 1.0)


if __name__ == "__main__":
    unittest.main()
