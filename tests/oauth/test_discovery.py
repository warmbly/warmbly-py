"""Tests for RFC 8414 authorization-server metadata discovery."""

from __future__ import annotations

import httpx
import pytest
import respx

from warmbly import OAuthError
from warmbly.oauth import (
    AuthorizationServerMetadata,
    async_discover,
    clear_discovery_cache,
    discover,
)
from warmbly.oauth._discovery import WELL_KNOWN_PATH

ISSUER = "https://auth.warmbly.com"
METADATA_URL = f"{ISSUER}{WELL_KNOWN_PATH}"


def _document() -> dict[str, object]:
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/oauth/authorize",
        "token_endpoint": f"{ISSUER}/oauth/token",
        "revocation_endpoint": f"{ISSUER}/oauth/revoke",
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["read_campaigns", "write_campaigns"],
    }


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_discovery_cache()


@respx.mock
def test_discover_parses_document() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    metadata = discover(ISSUER, use_cache=False)

    assert route.called
    assert isinstance(metadata, AuthorizationServerMetadata)
    assert metadata.issuer == ISSUER
    assert metadata.token_endpoint == f"{ISSUER}/oauth/token"
    assert metadata.code_challenge_methods_supported == ["S256"]


@respx.mock
def test_discover_strips_trailing_slash() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    metadata = discover(f"{ISSUER}/", use_cache=False)

    assert route.called
    assert metadata.issuer == ISSUER


@respx.mock
def test_discover_caches_per_issuer() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    first = discover(ISSUER)
    second = discover(ISSUER)

    assert first is second
    assert route.call_count == 1


@respx.mock
def test_clear_discovery_cache_forces_refetch() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    discover(ISSUER)
    clear_discovery_cache()
    discover(ISSUER)

    assert route.call_count == 2


@respx.mock
def test_discover_with_explicit_client_not_closed() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    with httpx.Client() as client:
        metadata = discover(ISSUER, http_client=client, use_cache=False)
        # The supplied client must remain usable (not closed by discover()).
        assert not client.is_closed

    assert route.called
    assert metadata.token_endpoint == f"{ISSUER}/oauth/token"


@respx.mock
def test_discover_http_error_wrapped_as_oauth_error() -> None:
    respx.get(METADATA_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(OAuthError) as excinfo:
        discover(ISSUER, use_cache=False)

    assert excinfo.value.error == "discovery_failed"


@respx.mock
def test_discover_non_object_document_raises() -> None:
    respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=["not", "an", "object"])
    )

    with pytest.raises(OAuthError) as excinfo:
        discover(ISSUER, use_cache=False)

    assert excinfo.value.error == "invalid_discovery_document"


@pytest.mark.anyio
@respx.mock
async def test_async_discover_parses_document() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    metadata = await async_discover(ISSUER, use_cache=False)

    assert route.called
    assert metadata.token_endpoint == f"{ISSUER}/oauth/token"


@pytest.mark.anyio
@respx.mock
async def test_async_discover_caches() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    first = await async_discover(ISSUER)
    second = await async_discover(ISSUER)

    assert first is second
    assert route.call_count == 1


@pytest.mark.anyio
@respx.mock
async def test_async_discover_with_explicit_client() -> None:
    route = respx.get(METADATA_URL).mock(
        return_value=httpx.Response(200, json=_document())
    )

    async with httpx.AsyncClient() as client:
        metadata = await async_discover(ISSUER, http_client=client, use_cache=False)
        assert not client.is_closed

    assert route.called
    assert metadata.issuer == ISSUER


@pytest.mark.anyio
@respx.mock
async def test_async_discover_http_error_wrapped() -> None:
    respx.get(METADATA_URL).mock(return_value=httpx.Response(500))

    with pytest.raises(OAuthError) as excinfo:
        await async_discover(ISSUER, use_cache=False)

    assert excinfo.value.error == "discovery_failed"
