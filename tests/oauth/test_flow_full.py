"""Exhaustive tests for warmbly.oauth._flow (sync + async, all branches)."""

from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from warmbly import OAuthError
from warmbly.oauth._flow import (
    AsyncOAuth2Client,
    OAuth2Client,
    _error_from_response,
    _parse_token_response,
)
from warmbly.oauth._tokens import OAuth2Token

BASE_URL = "https://api.warmbly.com"
APP_URL = "https://app.warmbly.com"
TOKEN_URL = f"{BASE_URL}/v1/oauth/token"
REVOKE_URL = f"{BASE_URL}/v1/oauth/revoke"

CLIENT_ID = "wmcid_full"
CLIENT_SECRET = "wmcs_full_secret"
REDIRECT_URI = "https://app.example.com/cb"


def _token_body() -> dict[str, object]:
    return {
        "access_token": "wmat_full",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "wmrt_rotated",
        "scope": "read write",
    }


def _public() -> OAuth2Client:
    return OAuth2Client(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )


def _confidential() -> OAuth2Client:
    return OAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )


def _expected_basic() -> str:
    return "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(
        "ascii"
    )


# ---------------------------------------------------------------------------
# Pure-helper unit tests (_parse_token_response / _error_from_response)
# ---------------------------------------------------------------------------
def test_parse_token_response_non_dict_raises() -> None:
    with pytest.raises(OAuthError) as excinfo:
        _parse_token_response(["not", "a", "dict"])
    assert excinfo.value.error == "invalid_response"
    assert "non-object" in (excinfo.value.error_description or "")


def test_parse_token_response_error_body_with_description() -> None:
    with pytest.raises(OAuthError) as excinfo:
        _parse_token_response({"error": "invalid_grant", "error_description": "nope"})
    assert excinfo.value.error == "invalid_grant"
    assert excinfo.value.error_description == "nope"


def test_parse_token_response_error_body_non_string_description() -> None:
    with pytest.raises(OAuthError) as excinfo:
        _parse_token_response({"error": "invalid_client", "error_description": 42})
    assert excinfo.value.error == "invalid_client"
    # Non-string descriptions are coerced to None.
    assert excinfo.value.error_description is None


def test_parse_token_response_missing_access_token_raises() -> None:
    with pytest.raises(OAuthError) as excinfo:
        _parse_token_response({"token_type": "Bearer"})
    assert excinfo.value.error == "invalid_response"
    assert "access_token" in (excinfo.value.error_description or "")


def test_parse_token_response_success_returns_token() -> None:
    token = _parse_token_response(_token_body())
    assert isinstance(token, OAuth2Token)
    assert token.access_token == "wmat_full"


def test_error_from_response_json_error() -> None:
    resp = httpx.Response(
        400, json={"error": "invalid_request", "error_description": "bad"}
    )
    err = _error_from_response(resp)
    assert err.error == "invalid_request"
    assert err.error_description == "bad"


def test_error_from_response_non_json_body() -> None:
    resp = httpx.Response(500, text="<html>down</html>")
    err = _error_from_response(resp)
    assert err.error == "http_error"
    assert "HTTP 500" in (err.error_description or "")


def test_error_from_response_json_without_error_key() -> None:
    resp = httpx.Response(503, json={"unrelated": "field"})
    err = _error_from_response(resp)
    assert err.error == "http_error"
    assert "HTTP 503" in (err.error_description or "")


# ---------------------------------------------------------------------------
# authorization_url
# ---------------------------------------------------------------------------
def test_authorization_url_full_param_set() -> None:
    with _public() as client:
        url, state, verifier = client.authorization_url(scopes=["read", "write"])
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "app.warmbly.com"
    assert parsed.path == "/oauth/authorize"
    q = parse_qs(parsed.query)
    assert q["response_type"] == ["code"]
    assert q["client_id"] == [CLIENT_ID]
    assert q["redirect_uri"] == [REDIRECT_URI]
    assert q["scope"] == ["read write"]
    assert q["state"] == [state]
    assert q["code_challenge_method"] == ["S256"]
    assert q["code_challenge"][0]
    assert isinstance(verifier, str) and verifier


def test_authorization_url_random_state_when_none() -> None:
    with _public() as client:
        _, state, _ = client.authorization_url(scopes=["read"])
    assert isinstance(state, str)
    assert len(state) > 0


def test_authorization_url_uses_caller_state() -> None:
    with _public() as client:
        url, state, _ = client.authorization_url(scopes=["read"], state="csrf-1")
    assert state == "csrf-1"
    assert parse_qs(urlparse(url).query)["state"] == ["csrf-1"]


def test_authorization_url_requires_redirect_uri() -> None:
    with (
        OAuth2Client(client_id=CLIENT_ID, base_url=BASE_URL, app_url=APP_URL) as client,
        pytest.raises(OAuthError) as excinfo,
    ):
        client.authorization_url(scopes=["read"])
    assert excinfo.value.error == "invalid_request"


# ---------------------------------------------------------------------------
# _require_redirect_uri override semantics
# ---------------------------------------------------------------------------
def test_require_redirect_uri_override_wins() -> None:
    with _public() as client:
        assert client._require_redirect_uri("https://other/cb") == "https://other/cb"


def test_require_redirect_uri_falls_back_to_client_default() -> None:
    with _public() as client:
        assert client._require_redirect_uri(None) == REDIRECT_URI


def test_require_redirect_uri_none_anywhere_raises() -> None:
    with (
        OAuth2Client(client_id=CLIENT_ID, base_url=BASE_URL) as client,
        pytest.raises(OAuthError) as excinfo,
    ):
        client._require_redirect_uri(None)
    assert excinfo.value.error == "invalid_request"


# ---------------------------------------------------------------------------
# exchange_code (sync): body, client auth, override redirect_uri
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_exchange_code_public_body() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    with _public() as client:
        token = client.exchange_code(
            "wmac_code",
            code_verifier="ver",
            redirect_uri="https://override/cb",
        )
    assert isinstance(token, OAuth2Token)
    assert token.access_token == "wmat_full"
    request = route.calls.last.request
    assert "authorization" not in request.headers
    form = parse_qs(request.content.decode())
    assert form["grant_type"] == ["authorization_code"]
    assert form["code"] == ["wmac_code"]
    assert form["code_verifier"] == ["ver"]
    assert form["redirect_uri"] == ["https://override/cb"]
    assert form["client_id"] == [CLIENT_ID]


@respx.mock
def test_sync_exchange_code_confidential_basic_auth() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    with _confidential() as client:
        client.exchange_code("wmac_code", code_verifier="v")
    request = route.calls.last.request
    assert request.headers["authorization"] == _expected_basic()
    form = parse_qs(request.content.decode())
    assert "client_id" not in form


@respx.mock
def test_sync_exchange_code_matching_state_ok() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_body()))
    with _public() as client:
        token = client.exchange_code(
            "wmac_code", code_verifier="v", state="s", expected_state="s"
        )
    assert token.access_token == "wmat_full"


def test_sync_exchange_code_state_mismatch_no_http() -> None:
    with respx.mock:
        route = respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(200, json=_token_body())
        )
        with _public() as client, pytest.raises(OAuthError) as excinfo:
            client.exchange_code(
                "wmac_code",
                code_verifier="v",
                state="returned",
                expected_state="issued",
            )
        assert not route.called
    assert excinfo.value.error == "invalid_state"


def test_sync_exchange_code_missing_state_no_http() -> None:
    with respx.mock:
        route = respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(200, json=_token_body())
        )
        with _public() as client, pytest.raises(OAuthError) as excinfo:
            client.exchange_code(
                "wmac_code", code_verifier="v", expected_state="issued"
            )
        assert not route.called
    assert excinfo.value.error == "invalid_state"


# ---------------------------------------------------------------------------
# refresh_token / client_credentials / revoke (sync)
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_refresh_token() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    with _public() as client:
        token = client.refresh_token("wmrt_old")
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["grant_type"] == ["refresh_token"]
    assert form["refresh_token"] == ["wmrt_old"]
    assert token.refresh_token == "wmrt_rotated"


@respx.mock
def test_sync_client_credentials_with_scopes() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    with _confidential() as client:
        client.client_credentials(scopes=["read", "write"])
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["grant_type"] == ["client_credentials"]
    assert form["scope"] == ["read write"]


@respx.mock
def test_sync_client_credentials_without_scopes() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    with _confidential() as client:
        client.client_credentials()
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["grant_type"] == ["client_credentials"]
    assert "scope" not in form


@respx.mock
def test_sync_revoke_returns_none() -> None:
    route = respx.post(REVOKE_URL).mock(return_value=httpx.Response(200))
    with _confidential() as client:
        assert client.revoke("wmat_full") is None
    request = route.calls.last.request
    form = parse_qs(request.content.decode())
    assert form["token"] == ["wmat_full"]
    assert "client_id" not in form
    assert request.headers["authorization"] == _expected_basic()


@respx.mock
def test_sync_revoke_public_puts_client_id() -> None:
    route = respx.post(REVOKE_URL).mock(return_value=httpx.Response(200))
    with _public() as client:
        client.revoke("wmat_full")
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["client_id"] == [CLIENT_ID]
    assert "authorization" not in route.calls.last.request.headers


@respx.mock
def test_sync_revoke_connection_error() -> None:
    respx.post(REVOKE_URL).mock(side_effect=httpx.ConnectError("down"))
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.revoke("wmat_full")
    assert excinfo.value.error == "connection_error"


# ---------------------------------------------------------------------------
# _post_token error paths (sync)
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_post_token_connection_error() -> None:
    respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError("boom"))
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.refresh_token("wmrt_old")
    assert excinfo.value.error == "connection_error"
    assert "boom" in (excinfo.value.error_description or "")


@respx.mock
def test_sync_post_token_non_json_200() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, text="not json at all"))
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.refresh_token("wmrt_old")
    assert excinfo.value.error == "invalid_response"
    assert "non-JSON" in (excinfo.value.error_description or "")


@respx.mock
def test_sync_post_token_error_status_rfc6749() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            400, json={"error": "invalid_grant", "error_description": "expired"}
        )
    )
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.refresh_token("wmrt_old")
    assert excinfo.value.error == "invalid_grant"
    assert excinfo.value.error_description == "expired"


@respx.mock
def test_sync_post_token_error_status_http_error() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(500, text="boom"))
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.refresh_token("wmrt_old")
    assert excinfo.value.error == "http_error"
    assert "HTTP 500" in (excinfo.value.error_description or "")


@respx.mock
def test_sync_post_token_success_non_dict_json() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=[1, 2, 3]))
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.refresh_token("wmrt_old")
    assert excinfo.value.error == "invalid_response"


@respx.mock
def test_sync_post_token_success_missing_access_token() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"token_type": "Bearer"})
    )
    with _public() as client, pytest.raises(OAuthError) as excinfo:
        client.refresh_token("wmrt_old")
    assert excinfo.value.error == "invalid_response"


# ---------------------------------------------------------------------------
# http_client ownership (sync)
# ---------------------------------------------------------------------------
def test_sync_external_http_client_not_closed() -> None:
    http = httpx.Client()
    try:
        client = OAuth2Client(client_id=CLIENT_ID, base_url=BASE_URL, http_client=http)
        assert client._owns_http is False
        client.close()
        # External client must remain usable (not closed).
        assert http.is_closed is False
    finally:
        http.close()


def test_sync_internal_http_client_closed() -> None:
    client = _public()
    internal = client._client()
    # Second call returns the same cached client (no new construction).
    assert client._client() is internal
    assert client._owns_http is True
    assert internal.is_closed is False
    client.close()
    assert internal.is_closed is True
    # close() is idempotent after the client is dropped.
    client.close()


def test_sync_client_reuses_external_http() -> None:
    http = httpx.Client()
    try:
        client = OAuth2Client(client_id=CLIENT_ID, base_url=BASE_URL, http_client=http)
        assert client._client() is http
    finally:
        http.close()


# ---------------------------------------------------------------------------
# Async mirror
# ---------------------------------------------------------------------------
def _async_public() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )


def _async_confidential() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )


def test_async_authorization_url_is_sync() -> None:
    client = _async_public()
    url, state, verifier = client.authorization_url(scopes=["read"])
    q = parse_qs(urlparse(url).query)
    assert q["client_id"] == [CLIENT_ID]
    assert q["state"] == [state]
    assert verifier


@pytest.mark.anyio
@respx.mock
async def test_async_exchange_code_public_body() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    async with _async_public() as client:
        token = await client.exchange_code(
            "wmac_code", code_verifier="v", redirect_uri="https://o/cb"
        )
    assert token.access_token == "wmat_full"
    request = route.calls.last.request
    assert "authorization" not in request.headers
    form = parse_qs(request.content.decode())
    assert form["client_id"] == [CLIENT_ID]
    assert form["redirect_uri"] == ["https://o/cb"]


@pytest.mark.anyio
@respx.mock
async def test_async_exchange_code_confidential_basic_auth() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    async with _async_confidential() as client:
        await client.exchange_code("wmac_code", code_verifier="v")
    request = route.calls.last.request
    assert request.headers["authorization"] == _expected_basic()
    assert "client_id" not in parse_qs(request.content.decode())


@pytest.mark.anyio
@respx.mock
async def test_async_exchange_code_matching_state_ok() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_body()))
    async with _async_public() as client:
        token = await client.exchange_code(
            "wmac_code", code_verifier="v", state="s", expected_state="s"
        )
    assert token.access_token == "wmat_full"


@pytest.mark.anyio
async def test_async_exchange_code_state_mismatch_no_http() -> None:
    with respx.mock:
        route = respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(200, json=_token_body())
        )
        async with _async_public() as client:
            with pytest.raises(OAuthError) as excinfo:
                await client.exchange_code(
                    "wmac_code",
                    code_verifier="v",
                    state="returned",
                    expected_state="issued",
                )
        assert not route.called
    assert excinfo.value.error == "invalid_state"


@pytest.mark.anyio
@respx.mock
async def test_async_refresh_token() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    async with _async_public() as client:
        token = await client.refresh_token("wmrt_old")
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["grant_type"] == ["refresh_token"]
    assert form["refresh_token"] == ["wmrt_old"]
    assert token.refresh_token == "wmrt_rotated"


@pytest.mark.anyio
@respx.mock
async def test_async_client_credentials_with_scopes() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    async with _async_confidential() as client:
        await client.client_credentials(scopes=["read", "write"])
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["grant_type"] == ["client_credentials"]
    assert form["scope"] == ["read write"]


@pytest.mark.anyio
@respx.mock
async def test_async_client_credentials_without_scopes() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    async with _async_confidential() as client:
        await client.client_credentials()
    form = parse_qs(route.calls.last.request.content.decode())
    assert "scope" not in form


@pytest.mark.anyio
@respx.mock
async def test_async_revoke_returns_none() -> None:
    route = respx.post(REVOKE_URL).mock(return_value=httpx.Response(200))
    async with _async_confidential() as client:
        assert await client.revoke("wmat_full") is None
    form = parse_qs(route.calls.last.request.content.decode())
    assert form["token"] == ["wmat_full"]
    assert route.calls.last.request.headers["authorization"] == _expected_basic()


@pytest.mark.anyio
@respx.mock
async def test_async_revoke_connection_error() -> None:
    respx.post(REVOKE_URL).mock(side_effect=httpx.ConnectError("down"))
    async with _async_public() as client:
        with pytest.raises(OAuthError) as excinfo:
            await client.revoke("wmat_full")
    assert excinfo.value.error == "connection_error"


@pytest.mark.anyio
@respx.mock
async def test_async_post_token_connection_error() -> None:
    respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError("boom"))
    async with _async_public() as client:
        with pytest.raises(OAuthError) as excinfo:
            await client.refresh_token("wmrt_old")
    assert excinfo.value.error == "connection_error"


@pytest.mark.anyio
@respx.mock
async def test_async_post_token_non_json_200() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, text="nope"))
    async with _async_public() as client:
        with pytest.raises(OAuthError) as excinfo:
            await client.refresh_token("wmrt_old")
    assert excinfo.value.error == "invalid_response"
    assert "non-JSON" in (excinfo.value.error_description or "")


@pytest.mark.anyio
@respx.mock
async def test_async_post_token_http_error_status() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(502, text="bad gw"))
    async with _async_public() as client:
        with pytest.raises(OAuthError) as excinfo:
            await client.refresh_token("wmrt_old")
    assert excinfo.value.error == "http_error"
    assert "HTTP 502" in (excinfo.value.error_description or "")


@pytest.mark.anyio
@respx.mock
async def test_async_post_token_success_missing_access_token() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"token_type": "Bearer"})
    )
    async with _async_public() as client:
        with pytest.raises(OAuthError) as excinfo:
            await client.refresh_token("wmrt_old")
    assert excinfo.value.error == "invalid_response"


@pytest.mark.anyio
async def test_async_external_http_client_not_closed() -> None:
    http = httpx.AsyncClient()
    try:
        client = AsyncOAuth2Client(
            client_id=CLIENT_ID, base_url=BASE_URL, http_client=http
        )
        assert client._owns_http is False
        await client.close()
        assert http.is_closed is False
    finally:
        await http.aclose()


@pytest.mark.anyio
async def test_async_internal_http_client_closed() -> None:
    client = _async_public()
    internal = client._client()
    # Second call returns the same cached client.
    assert client._client() is internal
    assert client._owns_http is True
    assert internal.is_closed is False
    await client.close()
    assert internal.is_closed is True
    # Idempotent.
    await client.close()


@pytest.mark.anyio
async def test_async_client_reuses_external_http() -> None:
    http = httpx.AsyncClient()
    try:
        client = AsyncOAuth2Client(
            client_id=CLIENT_ID, base_url=BASE_URL, http_client=http
        )
        assert client._client() is http
    finally:
        await http.aclose()
