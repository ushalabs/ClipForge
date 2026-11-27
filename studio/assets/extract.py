"""Frame extraction from source video using ffmpeg with scene-balanced, scene-change, or uniform sampling."""

from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw

ExtractionStrategy = Literal["scene_balanced", "scene_change", "uniform"]


@dataclass(frozen=True)
class RawFrame:
    path: Path
    timestamp_sec: float
    index: int


def probe_duration(video_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(video_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout or "{}")
    return max(0.0, float(data.get("format", {}).get("duration", 0.0) or 0.0))


def _run_ffmpeg_extract(video_path: Path, vf_filter: str, out_pattern: Path, max_frames: int) -> list[Path]:
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vf",
        vf_filter,
        "-frames:v",
        str(max_frames),
        "-q:v",
        "2",
        str(out_pattern),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return sorted(out_pattern.parent.glob(out_pattern.name.replace("%05d", "*")))


def extract_frames(
    video_path: Path,
    output_dir: Path,
    target_count: int = 100,
    strategy: ExtractionStrategy = "scene_balanced",
    oversample_factor: float = 1.6,
) -> list[RawFrame]:
    """Extract candidate frames from `video_path` into `output_dir`.

    Oversamples slightly so quality/dedup filtering can still hit `target_count`
    when enough distinct frames exist, without ever padding duplicates.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(video_path)
    if duration <= 0.0:
        return []

    candidate_budget = max(target_count, int(math.ceil(target_count * oversample_factor)))
    out_pattern = output_dir / "raw_%05d.jpg"

    if strategy == "scene_change":
        vf = "select='gt(scene,0.25)'"
        files = _run_ffmpeg_extract(video_path, vf, out_pattern, candidate_budget)
        if not files:
            # Fallback to uniform if no hard cuts were detected.
            strategy = "uniform"

    if strategy == "scene_balanced":
        # Combine scene-change candidates with uniform coverage by sampling at a higher fps
        # and letting downstream deduplication + quality filtering pick the best frames.
        fps = max(0.2, candidate_budget / duration)
        vf = f"fps={fps:.4f}"
        files = _run_ffmpeg_extract(video_path, vf, out_pattern, candidate_budget)
    elif strategy == "uniform":
        fps = max(0.1, candidate_budget / duration)
        vf = f"fps={fps:.4f}"
        files = _run_ffmpeg_extract(video_path, vf, out_pattern, candidate_budget)

    total = len(files)
    frames: list[RawFrame] = []
    for idx, p in enumerate(files):
        ts = (idx + 0.5) * (duration / max(1, total))
        frames.append(RawFrame(path=p, timestamp_sec=round(ts, 3), index=idx))
    return frames


def create_thumbnail(src_path: Path, thumb_path: Path, size: tuple[int, int] = (320, 180)) -> Path:
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src_path) as img:
        copy = img.copy()
        copy.thumbnail(size, Image.Resampling.LANCZOS)
        copy.save(thumb_path, format="JPEG", quality=85)
    return thumb_path


def create_contact_sheet(
    image_paths: list[Path],
    output_path: Path,
    cols: int = 5,
    cell_size: tuple[int, int] = (240, 135),
) -> Path | None:
    if not image_paths:
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = math.ceil(len(image_paths) / cols)
    sheet = Image.new("RGB", (cols * cell_size[0], rows * cell_size[1]), (18, 22, 28))
    draw = ImageDraw.Draw(sheet)

    for idx, p in enumerate(image_paths):
        r, c = divmod(idx, cols)
        x, y = c * cell_size[0], r * cell_size[1]
        with Image.open(p) as img:
            thumb = img.copy()
            thumb.thumbnail(cell_size, Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x, y))
        draw.text((x + 6, y + 6), f"#{idx + 1}", fill=(240, 244, 248))

    sheet.save(output_path, format="JPEG", quality=85)
    return output_path
