"""Image quality checks, perceptual hashing, and cryptographic hashing for extracted frames."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageFilter, ImageStat


@dataclass(frozen=True)
class QualityMetrics:
    mean_luma: float
    luma_std: float
    sharpness: float
    is_black_or_flat: bool
    is_blurry: bool
    dhash: str
    sha256: str
    width: int
    height: int

    @property
    def passed(self) -> bool:
        return not self.is_black_or_flat and not self.is_blurry


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_dhash(img: Image.Image, hash_size: int = 8) -> str:
    """Compute a 64-bit difference hash (dHash) as a 16-char hex string."""
    gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    bits = 0
    for row in range(hash_size):
        offset = row * (hash_size + 1)
        for col in range(hash_size):
            bits = (bits << 1) | (1 if pixels[offset + col] > pixels[offset + col + 1] else 0)
    return f"{bits:0{hash_size * hash_size // 4}x}"


def hamming_distance(hex_a: str, hex_b: str) -> int:
    return (int(hex_a, 16) ^ int(hex_b, 16)).bit_count()


def analyze_frame(
    path: Path,
    min_luma: float = 12.0,
    min_luma_std: float = 6.0,
    min_sharpness: float = 4.0,
) -> QualityMetrics:
    """Inspect a frame for black/flat content, blur, dimensions, dHash, and SHA-256."""
    sha = compute_sha256(path)
    with Image.open(path) as img:
        width, height = img.size
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)
        mean_luma = float(stat.mean[0])
        luma_std = float(stat.stddev[0])

        # Edge energy via FIND_EDGES as a fast, dependency-free sharpness proxy.
        edges = gray.filter(ImageFilter.FIND_EDGES)
        sharpness = float(ImageStat.Stat(edges).stddev[0])
        dhash = compute_dhash(img)

    is_black_or_flat = mean_luma < min_luma or luma_std < min_luma_std
    is_blurry = sharpness < min_sharpness
    return QualityMetrics(
        mean_luma=round(mean_luma, 2),
        luma_std=round(luma_std, 2),
        sharpness=round(sharpness, 2),
        is_black_or_flat=is_black_or_flat,
        is_blurry=is_blurry,
        dhash=dhash,
        sha256=sha,
        width=width,
        height=height,
    )
