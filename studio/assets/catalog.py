"""Visual asset catalog: deduplication, quality filtering, rights metadata, and shortfall reporting."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

from studio.assets.extract import (
    ExtractionStrategy,
    create_contact_sheet,
    create_thumbnail,
    extract_frames,
)
from studio.assets.quality import analyze_frame, hamming_distance


@dataclass
class AssetItem:
    asset_id: str
    path: str
    thumbnail_path: str
    timestamp_sec: float
    width: int
    height: int
    sha256: str
    dhash: str
    sharpness: float
    mean_luma: float
    rights_status: str = "pending_review"
    source_id: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class AssetCatalog:
    project_id: str
    source_path: str
    target_count: int
    extracted_count: int
    rejected_quality: int
    rejected_duplicate: int
    shortfall: int
    shortfall_reason: str
    contact_sheet_path: str | None
    assets: list[AssetItem]

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "source_path": self.source_path,
            "target_count": self.target_count,
            "extracted_count": self.extracted_count,
            "rejected_quality": self.rejected_quality,
            "rejected_duplicate": self.rejected_duplicate,
            "shortfall": self.shortfall,
            "shortfall_reason": self.shortfall_reason,
            "contact_sheet_path": self.contact_sheet_path,
            "assets": [asdict(a) for a in self.assets],
        }

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


def build_asset_catalog(
    video_path: Path,
    asset_dir: Path,
    project_id: str = "default",
    source_id: str = "",
    target_count: int = 100,
    strategy: ExtractionStrategy = "scene_balanced",
    dedup_max_distance: int = 6,
    min_luma: float = 12.0,
    min_luma_std: float = 6.0,
    min_sharpness: float = 4.0,
) -> AssetCatalog:
    """Extract, filter, deduplicate, and catalog visual assets from `video_path`.

    Never pads duplicates when fewer than `target_count` distinct, usable frames exist;
    instead reports `shortfall` and `shortfall_reason`.
    """
    raw_dir = asset_dir / "_raw"
    frames_dir = asset_dir / "frames"
    thumbs_dir = asset_dir / "thumbs"
    frames_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    raw_frames = extract_frames(
        video_path=video_path,
        output_dir=raw_dir,
        target_count=target_count,
        strategy=strategy,
    )

    accepted: list[AssetItem] = []
    seen_hashes: list[str] = []
    rejected_quality = 0
    rejected_duplicate = 0

    for raw in raw_frames:
        if len(accepted) >= target_count:
            break
        metrics = analyze_frame(
            raw.path,
            min_luma=min_luma,
            min_luma_std=min_luma_std,
            min_sharpness=min_sharpness,
        )
        if not metrics.passed:
            rejected_quality += 1
            continue

        if any(hamming_distance(metrics.dhash, h) <= dedup_max_distance for h in seen_hashes):
            rejected_duplicate += 1
            continue

        seen_hashes.append(metrics.dhash)
        asset_id = f"asset_{len(accepted) + 1:04d}"
        final_path = frames_dir / f"{asset_id}.jpg"
        shutil.copy2(raw.path, final_path)
        thumb_path = create_thumbnail(final_path, thumbs_dir / f"{asset_id}_thumb.jpg")

        accepted.append(
            AssetItem(
                asset_id=asset_id,
                path=str(final_path),
                thumbnail_path=str(thumb_path),
                timestamp_sec=raw.timestamp_sec,
                width=metrics.width,
                height=metrics.height,
                sha256=metrics.sha256,
                dhash=metrics.dhash,
                sharpness=metrics.sharpness,
                mean_luma=metrics.mean_luma,
                rights_status="pending_review",
                source_id=source_id,
            )
        )

    shutil.rmtree(raw_dir, ignore_errors=True)

    sheet_path = create_contact_sheet(
        [Path(a.thumbnail_path) for a in accepted[:25]],
        asset_dir / "contact_sheet.jpg",
    )

    shortfall = max(0, target_count - len(accepted))
    shortfall_reason = ""
    if shortfall > 0:
        shortfall_reason = (
            f"Extracted {len(accepted)} distinct usable frames out of {target_count} requested "
            f"(rejected {rejected_quality} low-quality, {rejected_duplicate} near-duplicates)."
        )

    catalog = AssetCatalog(
        project_id=project_id,
        source_path=str(video_path),
        target_count=target_count,
        extracted_count=len(accepted),
        rejected_quality=rejected_quality,
        rejected_duplicate=rejected_duplicate,
        shortfall=shortfall,
        shortfall_reason=shortfall_reason,
        contact_sheet_path=str(sheet_path) if sheet_path else None,
        assets=accepted,
    )
    catalog.save(asset_dir / "catalog.json")
    return catalog
