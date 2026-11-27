"""Direct local file and direct HTTP(S) media ingestion adapter."""
import hashlib
import shutil
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import httpx

from .. import media
from .base import DownloadedMedia, SourceCapabilities, SourceError, SourceMetadata
from .security import safe_dest_path, validate_public_url

DIRECT_EXTS = (".mp4", ".webm", ".mov", ".mkv", ".m4v")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class DirectMediaAdapter:
    name = "direct"

    def supports(self, source: str) -> bool:
        s = (source or "").strip()
        if not s:
            return False
        if Path(s).exists():
            return True
        p = urlparse(s)
        return p.scheme in {"http", "https"} and p.path.lower().endswith(DIRECT_EXTS)

    def capabilities(self, source: str) -> SourceCapabilities:
        is_local = Path((source or "").strip()).exists()
        return SourceCapabilities(
            can_probe=True,
            can_download=True,
            requires_browser_handoff=False,
            platform="local_file" if is_local else "direct_url",
        )

    def probe(self, source: str) -> SourceMetadata:
        s = (source or "").strip()
        local = Path(s)
        if local.exists():
            info = media.probe(local)
            return SourceMetadata(
                canonical_url=str(local.resolve()),
                platform="local_file",
                title=local.stem,
                duration_sec=float(info.get("duration") or 0.0),
                width=int(info.get("width") or 0),
                height=int(info.get("height") or 0),
            )
        validate_public_url(s)
        return SourceMetadata(canonical_url=s, platform="direct_url", title=Path(urlparse(s).path).stem or "video")

    def download(
        self,
        source: str,
        destination: Path,
        max_bytes: int = 2 * 1024 * 1024 * 1024,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> DownloadedMedia:
        s = (source or "").strip()
        destination.mkdir(parents=True, exist_ok=True)
        local = Path(s)
        if local.exists():
            size = local.stat().st_size
            if size > max_bytes:
                raise SourceError(f"File exceeds size limit ({size} > {max_bytes} bytes).", code="size_limit")
            out = safe_dest_path(destination, local.name)
            if out.resolve() != local.resolve():
                shutil.copy2(local, out)
            if on_progress:
                on_progress(1.0)
            meta = self.probe(str(out))
            return DownloadedMedia(path=out, metadata=meta, sha256=_sha256_file(out), size_bytes=size)

        url = validate_public_url(s)
        name = Path(urlparse(url).path).name or "source.mp4"
        out = safe_dest_path(destination, name)
        total = 0
        with httpx.Client(follow_redirects=False, timeout=30) as client:
            cur = url
            for _ in range(5):
                validate_public_url(cur)
                with client.stream("GET", cur) as resp:
                    if resp.is_redirect:
                        loc = resp.headers.get("location")
                        if not loc:
                            raise SourceError("Redirect without location header.", code="redirect_error")
                        cur = str(httpx.URL(cur).join(loc))
                        continue
                    if resp.status_code != 200:
                        raise SourceError(f"Download failed with HTTP {resp.status_code}.", code="http_error")
                    with out.open("wb") as f:
                        for chunk in resp.iter_bytes(256 * 1024):
                            total += len(chunk)
                            if total > max_bytes:
                                raise SourceError("Download exceeds size limit.", code="size_limit")
                            f.write(chunk)
                    break
            else:
                raise SourceError("Too many redirects.", code="redirect_limit")
        if on_progress:
            on_progress(1.0)
        info = media.probe(out)
        meta = SourceMetadata(
            canonical_url=url,
            platform="direct_url",
            title=out.stem,
            duration_sec=float(info.get("duration") or 0.0),
            width=int(info.get("width") or 0),
            height=int(info.get("height") or 0),
        )
        return DownloadedMedia(path=out, metadata=meta, sha256=_sha256_file(out), size_bytes=total)
