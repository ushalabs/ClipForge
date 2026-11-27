"""Tests for Phase 8: unified creation project API and review state."""

import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from studio import config
from studio.server import app


class TestProjectsAPI(unittest.TestCase):
    def test_create_list_and_review_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig_data_dir = config.DATA_DIR
            config.DATA_DIR = Path(tmp)
            try:
                with TestClient(app, base_url="http://localhost:8765") as client:
                    headers = {"Origin": "http://localhost:8765"}
                    res = client.post(
                        "/api/projects",
                        json={"title": "Solar Grid Explainer", "aspect_ratio": "9:16", "target_frames": 80},
                        headers=headers,
                    )
                    self.assertEqual(res.status_code, 200)
                    proj = res.json()
                    pid = proj["project_id"]
                    self.assertEqual(proj["approval_status"], "pending_review")
                    self.assertFalse(proj["rights_confirmed"])

                    lst = client.get("/api/projects")
                    self.assertEqual(lst.status_code, 200)
                    self.assertEqual(len(lst.json()["projects"]), 1)

                    rev = client.post(
                        f"/api/projects/{pid}/review",
                        json={"approval_status": "approved", "rights_confirmed": True},
                        headers=headers,
                    )
                    self.assertEqual(rev.status_code, 200)
                    self.assertEqual(rev.json()["approval_status"], "approved")
                    self.assertTrue(rev.json()["rights_confirmed"])
            finally:
                config.DATA_DIR = orig_data_dir


if __name__ == "__main__":
    unittest.main()
