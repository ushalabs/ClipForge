"""yt-dlp ingestion adapter wrapping studio.media with URL hardening."""
import hashlib
from pathlib import Path
from typing import Callable, Optional

from .. import media
from .base import DownloadedMedia, SourceCapabilities, SourceError, SourceMetadata
from .security import validate_public_url


class YtDlpAdapter:
    name = "ytdlp"

    def supports(self, source: str) -> bool:
        s = (source or "").strip()
        return s.startswith(("http://", "https://"))

    def capabilities(self, source: str) -> SourceCapabilities:
        return SourceCapabilities(
            can_probe=True,
            can_download=True,
            requires_browser_handoff=False,
            platform="ytdlp",
        )

    def probe(self, source: str) -> SourceMetadata:
        url = validate_public_url(source)
        try:
            info = media.preview(url)
        except Exception as exc:
            raise SourceError(str(exc), code="probe_failed") from exc
        return SourceMetadata(
            canonical_url=url,
            platform="ytdlp",
            title=str(info.get("title") or ""),
            uploader=str(info.get("uploader") or ""),
            duration_sec=float(info.get("duration") or 0.0),
            is_live=bool(info.get("is_live")),
        )

    def download(
        self,
        source: str,
        destination: Path,
        max_bytes: int = 2 * 1024 * 1024 * 1024,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> DownloadedMedia:
        url = validate_public_url(source)
        destination.mkdir(parents=True, exist_ok=True)
        try:
            path = media.download(url, destination)
        except Exception as exc:
            raise SourceError(str(exc), code="download_failed") from exc
        size = path.stat().st_size
        if size > max_bytes:
            raise SourceError(f"Downloaded file exceeds size limit ({size} > {max_bytes}).", code="size_limit")
        if on_progress:
            on_progress(1.0)
        info = media.probe(path)
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        meta = SourceMetadata(
            canonical_url=url,
            platform="ytdlp",
            title=path.stem,
            duration_sec=float(info.get("duration") or 0.0),
            width=int(info.get("width") or 0),
            height=int(info.get("height") or 0),
        )
        return DownloadedMedia(path=path, metadata=meta, sha256=h.hexdigest(), size_bytes=size)
