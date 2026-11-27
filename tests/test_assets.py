"""Tests for Phase 2: frame extraction, quality filtering, deduplication, and asset catalog."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from studio.assets import build_asset_catalog


class TestAssetExtraction(unittest.TestCase):
    def _make_multiscene_video(self, path: Path) -> None:
        # 3 distinct visual scenes (testsrc2, smptebars, life/mandelbrot) + 1 black segment
        cmd = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=640x360:rate=10:duration=2",
            "-f",
            "lavfi",
            "-i",
            "smptebars=size=640x360:rate=10:duration=2",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=640x360:r=10:d=1",
            "-f",
            "lavfi",
            "-i",
            "mandelbrot=size=640x360:rate=10:end_pts=20",
            "-filter_complex",
            "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]",
            "-map",
            "[v]",
            "-t",
            "6",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
        subprocess.run(cmd, check=True)

    def test_extract_dedup_quality_and_shortfall(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            video_path = tmp_dir / "scenes.mp4"
            self._make_multiscene_video(video_path)

            asset_dir = tmp_dir / "assets"
            # Request 50 frames from a 6-second video with mostly static scenes:
            # deduplication + black-frame rejection should yield < 50 and report shortfall.
            catalog = build_asset_catalog(
                video_path=video_path,
                asset_dir=asset_dir,
                project_id="proj_test",
                source_id="src_1",
                target_count=50,
                strategy="scene_balanced",
            )

            self.assertGreater(catalog.extracted_count, 0)
            self.assertLess(catalog.extracted_count, 50)
            self.assertEqual(catalog.shortfall, 50 - catalog.extracted_count)
            self.assertTrue(catalog.shortfall_reason)
            self.assertGreater(catalog.rejected_quality + catalog.rejected_duplicate, 0)

            # Verify files and metadata
            self.assertTrue((asset_dir / "catalog.json").exists())
            saved = json.loads((asset_dir / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["extracted_count"], catalog.extracted_count)
            for item in catalog.assets:
                self.assertTrue(Path(item.path).exists())
                self.assertTrue(Path(item.thumbnail_path).exists())
                self.assertEqual(item.rights_status, "pending_review")
                self.assertEqual(len(item.sha256), 64)

            if catalog.contact_sheet_path:
                self.assertTrue(Path(catalog.contact_sheet_path).exists())


if __name__ == "__main__":
    unittest.main()
