"""Unified source ingestion adapters for FrameForge."""
from .base import DownloadedMedia, SourceAdapter, SourceCapabilities, SourceError, SourceMetadata
from .registry import SourceRegistry, default_registry
from .security import UnsafeSourceError, safe_dest_path, validate_public_url

__all__ = [
    "DownloadedMedia",
    "SourceAdapter",
    "SourceCapabilities",
    "SourceError",
    "SourceMetadata",
    "SourceRegistry",
    "UnsafeSourceError",
    "default_registry",
    "safe_dest_path",
    "validate_public_url",
]
