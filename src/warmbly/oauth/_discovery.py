"""RFC 8414 authorization-server metadata discovery.

Fetches ``{issuer}/.well-known/oauth-authorization-server`` and exposes the
endpoint URLs the SDK needs. Results are cached per issuer for the process
lifetime, since this document changes rarely.

This module talks HTTP directly through ``httpx`` (the OAuth subsystem is the one
place outside the base client that is permitted to). Transport failures are
wrapped as :class:`~warmbly.OAuthError` so ``httpx`` never escapes.
"""

from __future__ import annotations

from typing import Any

import httpx

from .._exceptions import OAuthError
from .._models import BaseModel

__all__ = [
    "WELL_KNOWN_PATH",
    "AuthorizationServerMetadata",
    "async_discover",
    "clear_discovery_cache",
    "discover",
]

WELL_KNOWN_PATH = "/.well-known/oauth-authorization-server"

# Per-issuer cache of fetched metadata for the life of the process.
_CACHE: dict[str, AuthorizationServerMetadata] = {}


class AuthorizationServerMetadata(BaseModel):
    """A subset of the RFC 8414 authorization-server metadata document.

    Unknown fields are preserved (the base model allows extras), so additional
    metadata the server publishes remains accessible via attribute access.

    Attributes:
        issuer: The authorization server's issuer identifier.
        authorization_endpoint: Browser endpoint for the authorization request.
        token_endpoint: Endpoint for exchanging codes / refresh tokens.
        revocation_endpoint: Endpoint for token revocation (RFC 7009).
        response_types_supported: Supported ``response_type`` values.
        grant_types_supported: Supported ``grant_type`` values.
        code_challenge_methods_supported: Supported PKCE methods (``S256``).
        token_endpoint_auth_methods_supported: Supported client-auth methods.
        scopes_supported: Scopes the server advertises.
    """

    issuer: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    revocation_endpoint: str | None = None
    response_types_supported: list[str] | None = None
    grant_types_supported: list[str] | None = None
    code_challenge_methods_supported: list[str] | None = None
    token_endpoint_auth_methods_supported: list[str] | None = None
    scopes_supported: list[str] | None = None


def _metadata_url(issuer: str) -> str:
    return issuer.rstrip("/") + WELL_KNOWN_PATH


def _parse(data: Any, issuer: str) -> AuthorizationServerMetadata:
    if not isinstance(data, dict):
        raise OAuthError(
            "invalid_discovery_document",
            f"Discovery document at {_metadata_url(issuer)} was not a JSON object.",
        )
    return AuthorizationServerMetadata.model_validate(data)


def clear_discovery_cache() -> None:
    """Empty the per-issuer discovery cache (mainly for tests)."""
    _CACHE.clear()


def discover(
    issuer: str,
    *,
    http_client: httpx.Client | None = None,
    use_cache: bool = True,
    timeout: float = 30.0,
) -> AuthorizationServerMetadata:
    """Fetch and cache the RFC 8414 metadata for *issuer* (sync).

    Args:
        issuer: The authorization server issuer URL, e.g.
            ``https://api.warmbly.com``.
        http_client: An optional pre-configured :class:`httpx.Client`. When
            given, it is used (and not closed) instead of a temporary one.
        use_cache: Whether to read from / write to the process-wide cache.
        timeout: Request timeout in seconds (ignored if *http_client* is given).

    Returns:
        The parsed :class:`AuthorizationServerMetadata`.

    Raises:
        OAuthError: If the document cannot be fetched or is not valid JSON.
    """
    if use_cache and issuer in _CACHE:
        return _CACHE[issuer]
    url = _metadata_url(issuer)
    try:
        if http_client is not None:
            response = http_client.get(url)
        else:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise OAuthError(
            "discovery_failed", f"Could not fetch OAuth metadata from {url}: {exc}"
        ) from exc
    metadata = _parse(data, issuer)
    if use_cache:
        _CACHE[issuer] = metadata
    return metadata


async def async_discover(
    issuer: str,
    *,
    http_client: httpx.AsyncClient | None = None,
    use_cache: bool = True,
    timeout: float = 30.0,
) -> AuthorizationServerMetadata:
    """Fetch and cache the RFC 8414 metadata for *issuer* (async).

    See :func:`discover` for argument and error semantics.
    """
    if use_cache and issuer in _CACHE:
        return _CACHE[issuer]
    url = _metadata_url(issuer)
    try:
        if http_client is not None:
            response = await http_client.get(url)
        else:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                response = await client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise OAuthError(
            "discovery_failed", f"Could not fetch OAuth metadata from {url}: {exc}"
        ) from exc
    metadata = _parse(data, issuer)
    if use_cache:
        _CACHE[issuer] = metadata
    return metadata
