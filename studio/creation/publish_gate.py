"""Server-side approval gate and idempotent publishing ledger."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from studio import config, ctx
from studio.creation.projects import get_project


class PublishBlockedError(PermissionError):
    """Raised when a project has not passed human approval and rights confirmation."""


def _ledger_path(uid: str | None = None) -> Path:
    user_id = uid or ctx.uid()
    d = config.DATA_DIR / "projects" / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "publish_ledger.json"


def _load_ledger(uid: str | None = None) -> dict[str, Any]:
    p = _ledger_path(uid)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_ledger(data: dict[str, Any], uid: str | None = None) -> None:
    _ledger_path(uid).write_text(json.dumps(data, indent=2), encoding="utf-8")


def can_publish(project: dict[str, Any]) -> tuple[bool, str]:
    if not project:
        return False, "Project not found."
    if project.get("approval_status") != "approved":
        return False, "Project must be approved before publishing."
    if not project.get("rights_confirmed"):
        return False, "Source rights must be confirmed before publishing."
    return True, ""


def publish_with_gate(
    project_id: str,
    platform: str,
    idempotency_key: str,
    publish_fn: Callable[[dict[str, Any], str], dict[str, Any]],
    uid: str | None = None,
) -> dict[str, Any]:
    """Enforce approval + rights gate and idempotency before calling `publish_fn`."""
    project = get_project(project_id, uid)
    allowed, reason = can_publish(project or {})
    if not allowed:
        raise PublishBlockedError(reason)

    ledger = _load_ledger(uid)
    if idempotency_key in ledger:
        return {**ledger[idempotency_key], "idempotent_replay": True}

    result = publish_fn(project, platform)
    record = {
        "project_id": project_id,
        "platform": platform,
        "idempotency_key": idempotency_key,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
        "idempotent_replay": False,
    }
    ledger[idempotency_key] = record
    _save_ledger(ledger, uid)
    ctx.bump()
    return record
