"""Tests for the OAuth2 authorization-code / refresh / client-credentials flows."""

from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from warmbly import OAuthError
from warmbly.oauth import AsyncOAuth2Client, OAuth2Client, OAuth2Token

BASE_URL = "https://api.warmbly.test"
APP_URL = "https://app.warmbly.test"
TOKEN_URL = f"{BASE_URL}/v1/oauth/token"
REVOKE_URL = f"{BASE_URL}/v1/oauth/revoke"

CLIENT_ID = "wmcid_abc123"
CLIENT_SECRET = "wmcs_secret456"
REDIRECT_URI = "https://app.example.com/callback"


def _public_client() -> OAuth2Client:
    return OAuth2Client(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )


def _confidential_client() -> OAuth2Client:
    return OAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )


def _token_body() -> dict[str, object]:
    return {
        "access_token": "wmat_access",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "wmrt_new",
        "scope": "read_campaigns write_campaigns",
    }


# --------------------------------------------------------------------------
# authorization_url
# --------------------------------------------------------------------------
def test_authorization_url_contains_all_params() -> None:
    client = _public_client()
    url, state, verifier = client.authorization_url(
        scopes=["read_campaigns", "write_campaigns"]
    )

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "app.warmbly.test"
    assert parsed.path == "/oauth/authorize"

    q = parse_qs(parsed.query)
    assert q["response_type"] == ["code"]
    assert q["client_id"] == [CLIENT_ID]
    assert q["redirect_uri"] == [REDIRECT_URI]
    assert q["scope"] == ["read_campaigns write_campaigns"]
    assert q["state"] == [state]
    assert q["code_challenge_method"] == ["S256"]
    # The challenge is present and corresponds to the returned verifier.
    from warmbly.oauth import verify_pkce

    assert verify_pkce(verifier, q["code_challenge"][0]) is True


def test_authorization_url_uses_supplied_state() -> None:
    client = _public_client()
    url, state, _verifier = client.authorization_url(
        scopes=["read_campaigns"], state="my-csrf-state"
    )
    assert state == "my-csrf-state"
    q = parse_qs(urlparse(url).query)
    assert q["state"] == ["my-csrf-state"]


def test_authorization_url_generates_unique_state_and_verifier() -> None:
    client = _public_client()
    _, state1, verifier1 = client.authorization_url(scopes=["read_campaigns"])
    _, state2, verifier2 = client.authorization_url(scopes=["read_campaigns"])
    assert state1 != state2
    assert verifier1 != verifier2


def test_authorization_url_requires_redirect_uri() -> None:
    client = OAuth2Client(client_id=CLIENT_ID, base_url=BASE_URL, app_url=APP_URL)
    with pytest.raises(OAuthError) as excinfo:
        client.authorization_url(scopes=["read_campaigns"])
    assert excinfo.value.error == "invalid_request"


# --------------------------------------------------------------------------
# exchange_code
# --------------------------------------------------------------------------
@respx.mock
def test_exchange_code_posts_form_and_parses_token() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    client = _public_client()
    token = client.exchange_code("wmac_code", code_verifier="the-verifier")

    assert isinstance(token, OAuth2Token)
    assert token.access_token == "wmat_access"
    assert token.refresh_token == "wmrt_new"
    assert token.scopes == ["read_campaigns", "write_campaigns"]

    request = route.calls.last.request
    assert request.headers["content-type"] == "application/x-www-form-urlencoded"
    form = parse_qs(request.content.decode())
    assert form["grant_type"] == ["authorization_code"]
    assert form["code"] == ["wmac_code"]
    assert form["code_verifier"] == ["the-verifier"]
    assert form["redirect_uri"] == [REDIRECT_URI]


@respx.mock
def test_exchange_code_public_client_puts_client_id_in_body() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    client = _public_client()
    client.exchange_code("wmac_code", code_verifier="v")

    request = route.calls.last.request
    assert "authorization" not in request.headers
    form = parse_qs(request.content.decode())
    assert form["client_id"] == [CLIENT_ID]


@respx.mock
def test_exchange_code_confidential_client_uses_basic_auth() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    client = _confidential_client()
    client.exchange_code("wmac_code", code_verifier="v")

    request = route.calls.last.request
    expected = "Basic " + base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode("ascii")
    assert request.headers["authorization"] == expected
    # client_id must NOT be duplicated in the body for confidential clients.
    form = parse_qs(request.content.decode())
    assert "client_id" not in form


def test_exchange_code_state_mismatch_raises() -> None:
    client = _public_client()
    with pytest.raises(OAuthError) as excinfo:
        client.exchange_code(
            "wmac_code",
            code_verifier="v",
            state="returned-state",
            expected_state="different-state",
        )
    assert excinfo.value.error == "invalid_state"


@respx.mock
def test_exchange_code_matching_state_succeeds() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_body()))
    client = _public_client()
    token = client.exchange_code(
        "wmac_code",
        code_verifier="v",
        state="same-state",
        expected_state="same-state",
    )
    assert token.access_token == "wmat_access"


@respx.mock
def test_exchange_code_rfc6749_error_body_raises_oautherror() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            400,
            json={
                "error": "invalid_grant",
                "error_description": "Authorization code is invalid or expired.",
            },
        )
    )
    client = _public_client()
    with pytest.raises(OAuthError) as excinfo:
        client.exchange_code("wmac_bad", code_verifier="v")
    assert excinfo.value.error == "invalid_grant"
    assert excinfo.value.error_description == (
        "Authorization code is invalid or expired."
    )


@respx.mock
def test_exchange_code_connection_error_raises_oautherror() -> None:
    respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError("boom"))
    client = _public_client()
    with pytest.raises(OAuthError) as excinfo:
        client.exchange_code("wmac_code", code_verifier="v")
    assert excinfo.value.error == "connection_error"


# --------------------------------------------------------------------------
# refresh_token / client_credentials / revoke
# --------------------------------------------------------------------------
@respx.mock
def test_refresh_token_posts_refresh_grant() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    client = _public_client()
    token = client.refresh_token("wmrt_old")

    form = parse_qs(route.calls.last.request.content.decode())
    assert form["grant_type"] == ["refresh_token"]
    assert form["refresh_token"] == ["wmrt_old"]
    assert token.refresh_token == "wmrt_new"


@respx.mock
def test_revoke_posts_token_and_returns_none() -> None:
    route = respx.post(REVOKE_URL).mock(return_value=httpx.Response(200))
    client = _confidential_client()
    assert client.revoke("wmat_access") is None

    form = parse_qs(route.calls.last.request.content.decode())
    assert form["token"] == ["wmat_access"]
    # confidential client -> Basic auth, no client_id in body
    assert "client_id" not in form
    assert "authorization" in route.calls.last.request.headers


# --------------------------------------------------------------------------
# Async mirror
# --------------------------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_async_exchange_code_parses_token() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=_token_body())
    )
    client = AsyncOAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        base_url=BASE_URL,
        app_url=APP_URL,
    )
    try:
        token = await client.exchange_code("wmac_code", code_verifier="v")
    finally:
        await client.close()

    assert token.access_token == "wmat_access"
    expected = "Basic " + base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode("ascii")
    assert route.calls.last.request.headers["authorization"] == expected


@pytest.mark.anyio
@respx.mock
async def test_async_refresh_invalid_grant_raises() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            400, json={"error": "invalid_grant", "error_description": "expired"}
        )
    )
    client = AsyncOAuth2Client(
        client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, base_url=BASE_URL
    )
    try:
        with pytest.raises(OAuthError) as excinfo:
            await client.refresh_token("wmrt_old")
    finally:
        await client.close()
    assert excinfo.value.error == "invalid_grant"
