"""Creation project persistence and review workflow state."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from studio import config, ctx


def _projects_dir(uid: str | None = None) -> Path:
    user_id = uid or ctx.uid()
    d = config.DATA_DIR / "projects" / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_project(
    title: str,
    source_url: str = "",
    topic: str = "",
    aspect_ratio: str = "9:16",
    target_frames: int = 100,
    uid: str | None = None,
) -> dict[str, Any]:
    pid = f"proj_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    project = {
        "project_id": pid,
        "owner_uid": uid or ctx.uid(),
        "title": (title or "Untitled Project").strip(),
        "topic": (topic or title or "").strip(),
        "source_url": source_url.strip(),
        "aspect_ratio": aspect_ratio,
        "target_frames": max(1, int(target_frames)),
        "status": "draft",
        "approval_status": "pending_review",
        "rights_confirmed": False,
        "created_at": now,
        "updated_at": now,
    }
    path = _projects_dir(uid) / f"{pid}.json"
    path.write_text(json.dumps(project, indent=2), encoding="utf-8")
    ctx.bump()
    return project


def list_projects(uid: str | None = None) -> list[dict[str, Any]]:
    d = _projects_dir(uid)
    items: list[dict[str, Any]] = []
    for p in sorted(d.glob("proj_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            items.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return items


def get_project(project_id: str, uid: str | None = None) -> dict[str, Any] | None:
    p = _projects_dir(uid) / f"{project_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def update_project_review(
    project_id: str,
    approval_status: str | None = None,
    rights_confirmed: bool | None = None,
    uid: str | None = None,
) -> dict[str, Any] | None:
    project = get_project(project_id, uid)
    if not project:
        return None
    if approval_status in ("pending_review", "approved", "rejected"):
        project["approval_status"] = approval_status
    if rights_confirmed is not None:
        project["rights_confirmed"] = bool(rights_confirmed)
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    (_projects_dir(uid) / f"{project_id}.json").write_text(json.dumps(project, indent=2), encoding="utf-8")
    ctx.bump()
    return project
