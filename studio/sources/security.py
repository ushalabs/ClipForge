"""URL, SSRF, redirect, and filesystem path hardening for source ingestion."""
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

from .base import SourceError

ALLOWED_SCHEMES = {"http", "https"}


class UnsafeSourceError(SourceError):
    def __init__(self, message: str):
        super().__init__(message, code="unsafe_source")


def _is_blocked_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_public_url(url: str, resolve_dns: bool = True) -> str:
    """Validate an external HTTP(S) URL and reject private/loopback/metadata targets."""
    raw = (url or "").strip()
    if not raw:
        raise UnsafeSourceError("Empty URL.")
    p = urlparse(raw)
    if p.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeSourceError(f"Unsupported URL scheme: {p.scheme or 'none'}.")
    if p.username or p.password:
        raise UnsafeSourceError("URLs with embedded credentials are not allowed.")
    host = (p.hostname or "").strip().rstrip(".")
    if not host:
        raise UnsafeSourceError("URL is missing a hostname.")
    if host.lower() in {"localhost", "metadata.google.internal"}:
        raise UnsafeSourceError(f"Blocked internal host: {host}.")

    # Literal IP check
    try:
        if _is_blocked_ip(host):
            raise UnsafeSourceError(f"Blocked non-public IP address: {host}.")
        return raw
    except ValueError:
        pass

    if resolve_dns:
        try:
            infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except OSError as exc:
            raise SourceError(f"Could not resolve host {host}: {exc}", code="dns_error") from exc
        if not infos:
            raise SourceError(f"Host {host} resolved to no addresses.", code="dns_error")
        for info in infos:
            addr = info[4][0].split("%")[0]
            if _is_blocked_ip(addr):
                raise UnsafeSourceError(f"Host {host} resolved to blocked address {addr}.")
    return raw


def safe_dest_path(base_dir: Path, filename: str) -> Path:
    """Resolve a filename strictly inside base_dir, rejecting traversal."""
    root = base_dir.resolve()
    clean = Path(filename).name
    if not clean or clean in {".", ".."}:
        raise UnsafeSourceError("Invalid destination filename.")
    target = (root / clean).resolve()
    if root not in target.parents and target != root:
        raise UnsafeSourceError("Path escapes destination directory.")
    return target
