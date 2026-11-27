"""Typed contracts for source ingestion adapters."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol


class SourceError(Exception):
    """Actionable error raised when a source cannot be probed or downloaded."""

    def __init__(self, message: str, code: str = "source_error"):
        super().__init__(message)
        self.code = code


@dataclass
class SourceCapabilities:
    can_probe: bool = True
    can_download: bool = True
    requires_browser_handoff: bool = False
    platform: str = "unknown"


@dataclass
class SourceMetadata:
    canonical_url: str
    platform: str
    title: str = ""
    uploader: str = ""
    duration_sec: float = 0.0
    width: int = 0
    height: int = 0
    upload_date: str = ""
    is_live: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class DownloadedMedia:
    path: Path
    metadata: SourceMetadata
    sha256: str = ""
    size_bytes: int = 0


class SourceAdapter(Protocol):
    name: str

    def supports(self, source: str) -> bool:
        ...

    def capabilities(self, source: str) -> SourceCapabilities:
        ...

    def probe(self, source: str) -> SourceMetadata:
        ...

    def download(
        self,
        source: str,
        destination: Path,
        max_bytes: int = 2 * 1024 * 1024 * 1024,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> DownloadedMedia:
        ...
