"""End-to-end integration test for FrameForge creation pipeline + Remotion render + API."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from studio import config
from studio.server import app


class TestEndToEndPipeline(unittest.TestCase):
    def test_e2e_project_create_run_remotion_and_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            src_mp4 = tmp_dir / "source.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=640x360:rate=10:duration=3",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(src_mp4),
                ],
                check=True,
            )

            orig_data = config.DATA_DIR
            config.DATA_DIR = tmp_dir / "data"
            try:
                with TestClient(app, base_url="http://localhost:8765") as client:
                    headers = {"Origin": "http://localhost:8765"}
                    created = client.post(
                        "/api/projects",
                        json={
                            "title": "E2E FrameForge Test",
                            "source_url": str(src_mp4),
                            "aspect_ratio": "9:16",
                            "target_frames": 4,
                        },
                        headers=headers,
                    )
                    self.assertEqual(created.status_code, 200)
                    pid = created.json()["project_id"]

                    run_res = client.post(f"/api/projects/{pid}/run?sync=true", headers=headers)
                    self.assertEqual(run_res.status_code, 200)
                    proj = run_res.json()
                    self.assertEqual(proj["status"], "ready")
                    self.assertEqual(proj["approval_status"], "pending_review")
                    self.assertEqual(proj["resolution"], "1080x1920")

                    vid = client.get(f"/api/projects/{pid}/video")
                    self.assertEqual(vid.status_code, 200)
                    self.assertGreater(len(vid.content), 1000)

                    rev = client.post(
                        f"/api/projects/{pid}/review",
                        json={"approval_status": "approved", "rights_confirmed": True},
                        headers=headers,
                    )
                    self.assertEqual(rev.status_code, 200)
                    self.assertEqual(rev.json()["approval_status"], "approved")
            finally:
                config.DATA_DIR = orig_data


if __name__ == "__main__":
    unittest.main()
