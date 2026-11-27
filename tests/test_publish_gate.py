"""Tests for Phase 9: server-side approval gate and idempotent publishing."""

import tempfile
import unittest
from pathlib import Path

from studio import config
from studio.creation.projects import create_project, update_project_review
from studio.creation.publish_gate import PublishBlockedError, publish_with_gate


class TestPublishGate(unittest.TestCase):
    def test_blocks_unapproved_and_deduplicates_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = config.DATA_DIR
            config.DATA_DIR = Path(tmp)
            try:
                proj = create_project("Test Publish", uid="u1")
                pid = proj["project_id"]

                calls = []

                def fake_post(p, platform):
                    calls.append((p["project_id"], platform))
                    return {"post_id": "mock_123"}

                # Must block before approval
                with self.assertRaises(PublishBlockedError):
                    publish_with_gate(pid, "youtube", "key_1", fake_post, uid="u1")
                self.assertEqual(len(calls), 0)

                # Approve without rights_confirmed -> still blocked
                update_project_review(pid, approval_status="approved", rights_confirmed=False, uid="u1")
                with self.assertRaises(PublishBlockedError):
                    publish_with_gate(pid, "youtube", "key_1", fake_post, uid="u1")

                # Confirm rights -> allowed
                update_project_review(pid, rights_confirmed=True, uid="u1")
                r1 = publish_with_gate(pid, "youtube", "key_1", fake_post, uid="u1")
                self.assertFalse(r1["idempotent_replay"])
                self.assertEqual(len(calls), 1)

                # Replay with same idempotency_key -> does not call fake_post again
                r2 = publish_with_gate(pid, "youtube", "key_1", fake_post, uid="u1")
                self.assertTrue(r2["idempotent_replay"])
                self.assertEqual(len(calls), 1)
            finally:
                config.DATA_DIR = orig


if __name__ == "__main__":
    unittest.main()
