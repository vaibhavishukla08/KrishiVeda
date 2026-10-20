"""Shared HTTP client for external APIs.

Uses the operating system's certificate store (via `truststore`) so requests also work on
networks that inspect TLS traffic with their own CA (common on campus/office networks).
Certificates are still fully verified.
"""

import ssl

import httpx

from app.config import get_settings

try:
    import truststore

    _VERIFY: ssl.SSLContext | bool = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
except ImportError:  # pragma: no cover - fall back to httpx's bundled certifi store
    _VERIFY = True


def make_client(timeout: float | None = None) -> httpx.Client:
    return httpx.Client(
        timeout=timeout or get_settings().http_timeout_seconds,
        verify=_VERIFY,
        headers={"User-Agent": "KrishiVeda/0.35 (academic project)"},
    )
