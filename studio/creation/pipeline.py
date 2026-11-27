"""End-to-end FrameForge creation pipeline: ingest -> assets -> research -> script -> narration -> render."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from studio import config, ctx
from studio.assets import build_asset_catalog
from studio.creation.projects import _projects_dir, get_project
from studio.creation.render_pipeline import build_render_manifest, render_from_manifest
from studio.creation.research import build_research_brief
from studio.creation.script import generate_script
from studio.creation.storyboard import build_storyboard
from studio.narration import FallbackToneTTS, align_words, build_caption_cues, normalize_audio
from studio.sources import default_registry


def _save_project(project: dict[str, Any], uid: str | None = None) -> None:
    pid = project["project_id"]
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    (_projects_dir(uid) / f"{pid}.json").write_text(json.dumps(project, indent=2), encoding="utf-8")
    ctx.bump()


def run_project_pipeline(project_id: str, uid: str | None = None, prefer_remotion: bool = True) -> dict[str, Any]:
    """Execute the full FrameForge creation pipeline for `project_id`."""
    project = get_project(project_id, uid)
    if not project:
        raise ValueError(f"Project not found: {project_id}")

    user_id = uid or ctx.uid()
    work_dir = _projects_dir(user_id) / project_id
    work_dir.mkdir(parents=True, exist_ok=True)

    project["status"] = "running"
    project["error"] = ""
    _save_project(project, user_id)

    try:
        source_url = (project.get("source_url") or "").strip()
        if not source_url:
            raise ValueError("source_url is required to run the creation pipeline.")

        source_dir = work_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        local_candidate = Path(source_url)
        if local_candidate.exists() and local_candidate.is_file():
            video_path = source_dir / local_candidate.name
            shutil.copy2(local_candidate, video_path)
        else:
            dl = default_registry().download(source_url, source_dir / "source.mp4")
            video_path = dl.path

        catalog = build_asset_catalog(
            video_path=video_path,
            asset_dir=work_dir / "assets",
            project_id=project_id,
            source_id=source_url,
            target_count=int(project.get("target_frames", 100)),
        )
        if not catalog.assets:
            raise RuntimeError("No usable frames could be extracted from source video.")

        brief = build_research_brief(catalog, topic=project.get("topic") or project.get("title") or "Untitled")
        script = generate_script(brief)
        storyboard = build_storyboard(
            script,
            brief,
            catalog,
            aspect_ratio=project.get("aspect_ratio", "9:16"),
        )

        raw_wav = work_dir / "narration_raw.wav"
        norm_wav = work_dir / "narration.wav"
        narration_text = script.full_narration()
        audio = FallbackToneTTS().synthesize(narration_text, raw_wav)
        normalize_audio(raw_wav, norm_wav)
        cues = build_caption_cues(align_words(narration_text, audio.duration_sec))

        manifest = build_render_manifest(storyboard, catalog, norm_wav, cues)
        (work_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        out_mp4 = work_dir / "output.mp4"
        report = render_from_manifest(manifest, out_mp4, prefer_remotion=prefer_remotion)
        if not report.passed:
            raise RuntimeError(f"Render quality gate failed: {report.errors}")

        project["status"] = "ready"
        project["approval_status"] = "pending_review"
        project["output_path"] = str(out_mp4)
        project["output_url"] = f"/api/projects/{project_id}/video"
        project["asset_count"] = catalog.extracted_count
        project["shortfall"] = catalog.shortfall
        project["shortfall_reason"] = catalog.shortfall_reason
        project["duration_sec"] = report.duration_sec
        project["resolution"] = f"{report.width}x{report.height}"
        project["script"] = script.to_dict()
        project["storyboard"] = storyboard.to_dict()
        _save_project(project, user_id)
        return project
    except Exception as exc:
        project["status"] = "failed"
        project["error"] = str(exc)
        _save_project(project, user_id)
        raise
