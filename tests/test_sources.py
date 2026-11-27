"""Tests for unified source ingestion and SSRF/path security."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from studio.sources import UnsafeSourceError, default_registry, safe_dest_path, validate_public_url
from studio.sources.base import SourceError


class SourceIngestionTests(unittest.TestCase):
    def test_rejects_unsafe_urls(self):
        bad_urls = [
            "",
            "file:///etc/passwd",
            "ftp://example.com/video.mp4",
            "https://user:pass@example.com/video.mp4",
            "http://127.0.0.1/video.mp4",
            "http://10.0.0.1/video.mp4",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/video.mp4",
            "http://localhost:8765/app",
        ]
        for u in bad_urls:
            with self.assertRaises(UnsafeSourceError, msg=f"Should reject {u!r}"):
                validate_public_url(u, resolve_dns=False)

    def test_safe_dest_path_blocks_traversal(self):
        tmp = Path(tempfile.mkdtemp(prefix="ff-path-"))
        try:
            p = safe_dest_path(tmp, "../../evil.mp4")
            self.assertEqual(p.parent, tmp.resolve())
            self.assertEqual(p.name, "evil.mp4")
            with self.assertRaises(UnsafeSourceError):
                safe_dest_path(tmp, ".")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_local_fixture_probe_and_download(self):
        tmp = Path(tempfile.mkdtemp(prefix="ff-src-"))
        try:
            src = tmp / "sample.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1",
                    "-c:v", "libx264", "-c:a", "aac", str(src),
                ],
                check=True,
                capture_output=True,
            )
            reg = default_registry()
            meta = reg.probe(str(src))
            self.assertEqual(meta.platform, "local_file")
            self.assertEqual(meta.width, 320)
            self.assertEqual(meta.height, 240)
            out_dir = tmp / "dest"
            dl = reg.download(str(src), out_dir)
            self.assertTrue(dl.path.exists())
            self.assertGreater(dl.size_bytes, 0)
            self.assertEqual(len(dl.sha256), 64)
            with self.assertRaises(SourceError):
                reg.download(str(src), out_dir, max_bytes=10)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
