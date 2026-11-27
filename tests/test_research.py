"""Tests for Phase 3: visual intelligence, transcript alignment, and semantic retrieval."""

import unittest

from studio.assets.catalog import AssetCatalog, AssetItem
from studio.creation.research import (
    build_research_brief,
    retrieve_assets,
    validate_asset_ids,
)


def _sample_catalog() -> AssetCatalog:
    assets = [
        AssetItem(
            asset_id="asset_0001",
            path="frames/asset_0001.jpg",
            thumbnail_path="thumbs/asset_0001_thumb.jpg",
            timestamp_sec=2.0,
            width=1280,
            height=720,
            sha256="a" * 64,
            dhash="0f0f0f0f0f0f0f0f",
            sharpness=25.0,
            mean_luma=120.0,
        ),
        AssetItem(
            asset_id="asset_0002",
            path="frames/asset_0002.jpg",
            thumbnail_path="thumbs/asset_0002_thumb.jpg",
            timestamp_sec=12.0,
            width=1280,
            height=720,
            sha256="b" * 64,
            dhash="f0f0f0f0f0f0f0f0",
            sharpness=30.0,
            mean_luma=130.0,
        ),
    ]
    return AssetCatalog(
        project_id="proj_1",
        source_path="source.mp4",
        target_count=2,
        extracted_count=2,
        rejected_quality=0,
        rejected_duplicate=0,
        shortfall=0,
        shortfall_reason="",
        contact_sheet_path=None,
        assets=assets,
    )


class TestResearch(unittest.TestCase):
    def test_transcript_alignment_and_retrieval(self):
        catalog = _sample_catalog()
        segments = [
            {"start": 0.0, "end": 4.0, "text": "Solar panels convert sunlight into electricity."},
            {"start": 10.0, "end": 14.0, "text": "Battery storage keeps the grid stable at night."},
        ]
        brief = build_research_brief(catalog, topic="Clean Energy", transcript_segments=segments)
        self.assertEqual(len(brief.enriched_assets), 2)
        self.assertGreaterEqual(len(brief.claims), 1)

        hits = retrieve_assets("battery grid night", brief, top_k=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].asset_id, "asset_0002")

    def test_validate_asset_ids_rejects_nonexistent(self):
        catalog = _sample_catalog()
        invalid = validate_asset_ids(["asset_0001", "asset_9999"], catalog)
        self.assertEqual(invalid, ["asset_9999"])
        self.assertEqual(validate_asset_ids(["asset_0001", "asset_0002"], catalog), [])


if __name__ == "__main__":
    unittest.main()
