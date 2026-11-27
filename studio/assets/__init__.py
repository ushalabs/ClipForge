"""Frame extraction, quality filtering, perceptual deduplication, and asset catalog."""

from studio.assets.catalog import AssetCatalog, AssetItem, build_asset_catalog
from studio.assets.extract import ExtractionStrategy, extract_frames, probe_duration
from studio.assets.quality import QualityMetrics, analyze_frame, compute_dhash, compute_sha256, hamming_distance

__all__ = [
    "AssetCatalog",
    "AssetItem",
    "ExtractionStrategy",
    "QualityMetrics",
    "analyze_frame",
    "build_asset_catalog",
    "compute_dhash",
    "compute_sha256",
    "extract_frames",
    "hamming_distance",
    "probe_duration",
]
