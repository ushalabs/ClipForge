"""Render orchestration: manifest generation, Remotion/ffmpeg rendering, and ffprobe quality gates."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from studio.assets.catalog import AssetCatalog
from studio.creation.storyboard import Storyboard
from studio.narration.align import CaptionCue

ASPECT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    width: int
    height: int
    duration_sec: float
    has_video: bool
    has_audio: bool
    errors: list[str]


def build_render_manifest(
    storyboard: Storyboard,
    catalog: AssetCatalog,
    audio_path: Path | None,
    captions: list[CaptionCue],
    fps: int = 30,
) -> dict[str, Any]:
    asset_map = {a.asset_id: a.path for a in catalog.assets}
    scenes = []
    for scene in storyboard.scenes:
        if scene.asset_id not in asset_map:
            raise ValueError(f"Missing asset_id in catalog: {scene.asset_id}")
        scenes.append(
            {
                "scene_id": scene.scene_id,
                "asset_path": asset_map[scene.asset_id],
                "duration_sec": scene.duration_sec,
                "visual_cue": scene.visual_cue,
            }
        )
    return {
        "project_id": storyboard.project_id,
        "title": storyboard.title,
        "aspect_ratio": storyboard.aspect_ratio,
        "fps": fps,
        "audio_path": str(audio_path) if audio_path else None,
        "scenes": scenes,
        "captions": [c.to_dict() for c in captions],
    }


def verify_rendered_video(
    video_path: Path,
    min_duration_sec: float = 0.5,
    require_audio: bool = True,
) -> QualityReport:
    """Run ffprobe quality gate on a rendered MP4."""
    if not video_path.exists() or video_path.stat().st_size == 0:
        return QualityReport(False, 0, 0, 0.0, False, False, ["Output file is missing or empty."])

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(video_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout or "{}")
    streams = data.get("streams", [])
    v_streams = [s for s in streams if s.get("codec_type") == "video"]
    a_streams = [s for s in streams if s.get("codec_type") == "audio"]
    duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)

    width = int(v_streams[0].get("width", 0)) if v_streams else 0
    height = int(v_streams[0].get("height", 0)) if v_streams else 0

    errors: list[str] = []
    if not v_streams:
        errors.append("No video stream found.")
    if require_audio and not a_streams:
        errors.append("No audio stream found.")
    if duration < min_duration_sec:
        errors.append(f"Duration {duration:.2f}s is below minimum {min_duration_sec:.2f}s.")

    return QualityReport(
        passed=len(errors) == 0,
        width=width,
        height=height,
        duration_sec=round(duration, 3),
        has_video=bool(v_streams),
        has_audio=bool(a_streams),
        errors=errors,
    )


def render_from_manifest(
    manifest: dict[str, Any],
    output_path: Path,
) -> QualityReport:
    """Render MP4 from `manifest` using ffmpeg fallback (or Remotion when bundled) and verify."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scenes = manifest.get("scenes", [])
    if not scenes:
        raise ValueError("Manifest has no scenes.")

    aspect = manifest.get("aspect_ratio", "9:16")
    width, height = ASPECT_DIMENSIONS.get(aspect, (1080, 1920))
    fps = int(manifest.get("fps", 30))

    concat_file = output_path.parent / f"{output_path.stem}_concat.txt"
    lines: list[str] = []
    for s in scenes:
        img_path = str(Path(s["asset_path"]).resolve()).replace("\\", "/")
        dur = max(0.5, float(s["duration_sec"]))
        lines.append(f"file '{img_path}'")
        lines.append(f"duration {dur:.3f}")
    # Repeat last image per ffmpeg concat demuxer requirement
    last_img = str(Path(scenes[-1]["asset_path"]).resolve()).replace("\\", "/")
    lines.append(f"file '{last_img}'")
    concat_file.write_text("\n".join(lines), encoding="utf-8")

    audio_path = manifest.get("audio_path")
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
    ]
    if audio_path and Path(audio_path).exists():
        cmd.extend(["-i", str(audio_path)])

    vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps},format=yuv420p"
    cmd.extend(["-vf", vf, "-c:v", "libx264", "-preset", "ultrafast"])
    if audio_path and Path(audio_path).exists():
        cmd.extend(["-c:a", "aac", "-shortest"])
    cmd.append(str(output_path))

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    finally:
        concat_file.unlink(missing_ok=True)

    return verify_rendered_video(output_path, require_audio=bool(audio_path and Path(audio_path).exists()))
