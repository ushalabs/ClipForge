"""Tests for Phase 11: autonomous production caps, dedup, and pending_review enforcement."""

import tempfile
import unittest
from pathlib import Path

from studio import config
from studio.autonomy import AutonomyConfig, run_autonomous_batch
from studio.discovery import NichePreset, TopicLedger


class TestAutonomy(unittest.TestCase):
    def test_daily_cap_and_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = config.DATA_DIR
            config.DATA_DIR = Path(tmp)
            try:
                ledger = TopicLedger(Path(tmp) / "ledger.json")
                preset = NichePreset("sci", "Science")
                candidates = [
                    {"topic": "Topic A", "source_url": "https://example.com/a"},
                    {"topic": "Topic A", "source_url": "https://example.com/a"},  # duplicate
                    {"topic": "Topic B", "source_url": "https://example.com/b"},
                    {"topic": "Topic C", "source_url": "https://example.com/c"},  # exceeds cap=2
                ]
                created = run_autonomous_batch(
                    candidates, preset, ledger, cfg=AutonomyConfig(daily_cap=2), uid="u1"
                )
                self.assertEqual(len(created), 2)
                for p in created:
                    self.assertEqual(p["approval_status"], "pending_review")
                    self.assertFalse(p["rights_confirmed"])
            finally:
                config.DATA_DIR = orig


if __name__ == "__main__":
    unittest.main()
