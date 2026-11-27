"""Tests for Phase 10: niche presets and topic deduplication ledger."""

import tempfile
import unittest
from pathlib import Path

from studio.discovery import NichePreset, TopicLedger


class TestDiscovery(unittest.TestCase):
    def test_topic_ledger_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = TopicLedger(Path(tmp) / "ledger.json")
            preset = NichePreset("tech_shorts", "Tech Explainers", keywords=["ai", "chips"])
            self.assertTrue(preset.require_manual_approval)

            self.assertFalse(ledger.is_duplicate("GPU Architecture", "https://example.com/v1"))
            ledger.record("GPU Architecture", "https://example.com/v1", "proj_1")
            self.assertTrue(ledger.is_duplicate("  gpu architecture ", "HTTPS://EXAMPLE.COM/v1"))


if __name__ == "__main__":
    unittest.main()
