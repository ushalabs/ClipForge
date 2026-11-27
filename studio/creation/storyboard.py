"""Semantic storyboard generation mapping script beats to verified catalog assets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from studio.assets.catalog import AssetCatalog
from studio.creation.research import ResearchBrief, retrieve_assets, validate_asset_ids
from studio.creation.script import OriginalScript


@dataclass
class StoryboardScene:
    scene_id: str
    beat_id: str
    asset_id: str
    narration: str
    visual_cue: str
    duration_sec: float
    transition: str = "crossfade"


@dataclass
class Storyboard:
    project_id: str
    title: str
    aspect_ratio: str
    scenes: list[StoryboardScene] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "aspect_ratio": self.aspect_ratio,
            "scenes": [asdict(s) for s in self.scenes],
        }


def build_storyboard(
    script: OriginalScript,
    brief: ResearchBrief,
    catalog: AssetCatalog,
    aspect_ratio: str = "9:16",
) -> Storyboard:
    """Map each script beat to a verified asset in `catalog`."""
    if not catalog.assets:
        raise ValueError("Cannot build storyboard: asset catalog is empty.")

    scenes: list[StoryboardScene] = []
    for idx, beat in enumerate(script.beats):
        hits = retrieve_assets(f"{beat.visual_cue} {beat.narration}", brief, top_k=1)
        chosen_id = hits[0].asset_id if hits else catalog.assets[idx % len(catalog.assets)].asset_id
        scenes.append(
            StoryboardScene(
                scene_id=f"scene_{idx + 1:02d}",
                beat_id=beat.beat_id,
                asset_id=chosen_id,
                narration=beat.narration,
                visual_cue=beat.visual_cue,
                duration_sec=beat.estimated_sec,
            )
        )

    invalid = validate_asset_ids([s.asset_id for s in scenes], catalog)
    if invalid:
        raise ValueError(f"Storyboard referenced nonexistent asset IDs: {invalid}")

    return Storyboard(
        project_id=script.project_id,
        title=script.title,
        aspect_ratio=aspect_ratio,
        scenes=scenes,
    )
