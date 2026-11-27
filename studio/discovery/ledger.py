"""Channel niche presets and topic deduplication ledger."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class NichePreset:
    preset_id: str
    name: str
    aspect_ratio: str = "9:16"
    target_duration_sec: float = 45.0
    keywords: list[str] = field(default_factory=list)
    require_manual_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _topic_hash(topic: str, source_url: str = "") -> str:
    norm = f"{(topic or '').strip().lower()}|{(source_url or '').strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


class TopicLedger:
    """Persistent ledger preventing duplicate topic/source production."""

    def __init__(self, ledger_path: Path):
        self.path = ledger_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"entries": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def is_duplicate(self, topic: str, source_url: str = "") -> bool:
        return _topic_hash(topic, source_url) in self._data["entries"]

    def record(self, topic: str, source_url: str = "", project_id: str = "") -> str:
        key = _topic_hash(topic, source_url)
        self._data["entries"][key] = {
            "topic": topic,
            "source_url": source_url,
            "project_id": project_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()
        return key
