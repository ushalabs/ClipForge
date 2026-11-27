"""Adapter registry with deterministic priority."""
from pathlib import Path
from typing import Callable, Optional

from .base import DownloadedMedia, SourceAdapter, SourceCapabilities, SourceError, SourceMetadata
from .direct import DirectMediaAdapter
from .ytdlp_adapter import YtDlpAdapter


class SourceRegistry:
    def __init__(self, adapters: list[SourceAdapter]):
        self.adapters = adapters

    def resolve(self, source: str) -> SourceAdapter:
        for adapter in self.adapters:
            if adapter.supports(source):
                return adapter
        raise SourceError("No ingestion adapter supports this source.", code="unsupported_source")

    def capabilities(self, source: str) -> SourceCapabilities:
        return self.resolve(source).capabilities(source)

    def probe(self, source: str) -> SourceMetadata:
        return self.resolve(source).probe(source)

    def download(
        self,
        source: str,
        destination: Path,
        max_bytes: int = 2 * 1024 * 1024 * 1024,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> DownloadedMedia:
        return self.resolve(source).download(source, destination, max_bytes=max_bytes, on_progress=on_progress)


def default_registry() -> SourceRegistry:
    return SourceRegistry([DirectMediaAdapter(), YtDlpAdapter()])
