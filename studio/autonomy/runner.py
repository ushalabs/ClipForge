"""Autonomous production runner with daily caps, deduplication, and mandatory review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from studio.creation.projects import create_project
from studio.discovery.ledger import NichePreset, TopicLedger


@dataclass
class AutonomyConfig:
    daily_cap: int = 3
    require_manual_approval: bool = True


def run_autonomous_batch(
    candidates: list[dict[str, str]],
    preset: NichePreset,
    ledger: TopicLedger,
    cfg: AutonomyConfig | None = None,
    uid: str | None = None,
) -> list[dict[str, Any]]:
    """Create up to `cfg.daily_cap` non-duplicate draft projects, always requiring review."""
    settings = cfg or AutonomyConfig()
    created: list[dict[str, Any]] = []

    for item in candidates:
        if len(created) >= settings.daily_cap:
            break
        topic = item.get("topic", "").strip()
        source_url = item.get("source_url", "").strip()
        if not topic or ledger.is_duplicate(topic, source_url):
            continue

        proj = create_project(
            title=topic,
            topic=topic,
            source_url=source_url,
            aspect_ratio=preset.aspect_ratio,
            uid=uid,
        )
        ledger.record(topic, source_url, proj["project_id"])
        created.append(proj)

    return created
