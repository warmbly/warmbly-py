"""Error envelope, error-code constants and app-scope helpers added by the sync."""

from __future__ import annotations

import re
from typing import Any

import httpx
import pytest
import respx

from warmbly import (
    APP_GRANTABLE_SCOPES,
    SCOPES,
    AsyncWarmbly,
    ErrorCode,
    OAuthError,
    PermissionDeniedError,
    Warmbly,
    mask_to_scopes,
)
from warmbly._exceptions import APIError, make_status_error
from warmbly.oauth._flow import (
    AsyncOAuth2Client,
    OAuth2Client,
    _error_from_response,
)

BASE = "https://api.warmbly.com"


def _envelope(code: str, **extra: Any) -> dict[str, Any]:
    return {
        "error": "Forbidden",
        "message": "Not allowed.",
        "code": code,
        "request_id": "4bbbd1b2-8f86-47dd-8a7f-9476501ad20e",
        **extra,
    }


# -- error codes -----------------------------------------------------------


def test_error_code_constants_are_the_lowercase_wire_strings() -> None:
    names = [n for n in vars(ErrorCode) if not n.startswith("_")]
    assert len(names) > 250
    for name in names:
        value = getattr(ErrorCode, name)
        assert value == name.lower()
        assert re.fullmatch(r"[a-z][a-z0-9_]*", value)


@pytest.mark.parametrize(
    ("constant", "wire"),
    [
        (ErrorCode.BAD_REQUEST, "bad_request"),
        (ErrorCode.INSUFFICIENT_CREDITS, "insufficient_credits"),
        (ErrorCode.RATE_LIMIT_EXCEEDED, "rate_limit_exceeded"),
        (ErrorCode.SESSION_ENDED, "session_ended"),
        (ErrorCode.DUPLICATE_QUERY_PARAMETER, "duplicate_query_parameter"),
        (ErrorCode.DUPLICATE_HEADER, "duplicate_header"),
        (ErrorCode.OAUTH_TOKEN_NOT_ALLOWED, "oauth_token_not_allowed"),
        (
            ErrorCode.API_KEY_PERMISSIONS_EXCEED_CALLER,
            "api_key_permissions_exceed_caller",
        ),
        (ErrorCode.API_KEY_HOLDER_LEFT, "api_key_holder_left"),
        (ErrorCode.API_KEY_MAILBOX_LIMITED, "api_key_mailbox_limited"),
        (ErrorCode.DEVELOPER_ACCESS_BLOCKED, "developer_access_blocked"),
        (ErrorCode.APP_SUSPENDED, "app_suspended"),
        (ErrorCode.PLACEMENT_QUOTA_EXCEEDED, "placement_quota_exceeded"),
        (ErrorCode.MAILBOX_ALLOWANCE_REACHED, "mailbox_allowance_reached"),
        (ErrorCode.STORAGE_LIMIT_REACHED, "storage_limit_reached"),
        (ErrorCode.CONTACT_EMAIL_TAKEN, "contact_email_taken"),
        (ErrorCode.WORKSPACE_SENDING_SUSPENDED, "workspace_sending_suspended"),
        (ErrorCode.INVALID_TLS_PIN, "invalid_tls_pin"),
    ],
)
def test_selected_codes(constant: str, wire: str) -> None:
    assert constant == wire


def test_envelope_populates_code_reason_and_request_id() -> None:
    body = _envelope("api_key_permissions_exceed_caller", reason="role")
    err = make_status_error(
        status_code=403,
        request_id=body["request_id"],
        headers={},
        body=body,
    )
    assert isinstance(err, PermissionDeniedError)
    assert err.code == ErrorCode.API_KEY_PERMISSIONS_EXCEED_CALLER
    assert err.reason == "role"
    assert err.request_id == body["request_id"]
    assert err.message == "Not allowed."


@pytest.mark.parametrize("body", [None, {}, {"code": 7, "reason": ["x"]}, "text"])
def test_missing_or_odd_code_and_reason_never_raise(body: object) -> None:
    err = APIError("boom", body=body)
    assert err.reason is None
    assert err.code is None


def test_unknown_code_is_a_plain_string() -> None:
    err = APIError("x", body={"code": "brand_new_code", "reason": "brand_new_reason"})
    assert err.code == "brand_new_code"
    assert err.reason == "brand_new_reason"
    assert err.code not in vars(ErrorCode).values()


@respx.mock
def test_sync_client_surfaces_reason() -> None:
    respx.get(f"{BASE}/v1/me").mock(
        return_value=httpx.Response(
            403,
            json=_envelope("oauth_token_not_allowed", reason="app"),
            headers={"x-request-id": "rid-1"},
        )
    )
    with (
        Warmbly(api_key="wmbly_x", max_retries=0) as client,
        pytest.raises(PermissionDeniedError) as info,
    ):
        client.get("/me", cast_to=dict)
    assert info.value.code == ErrorCode.OAUTH_TOKEN_NOT_ALLOWED
    assert info.value.reason == "app"
    assert info.value.request_id == "rid-1"


@pytest.mark.anyio
@respx.mock
async def test_async_client_surfaces_reason(anyio_backend: str) -> None:
    respx.get(f"{BASE}/v1/me").mock(
        return_value=httpx.Response(
            403,
            json=_envelope("api_key_holder_left", reason="left"),
            headers={"x-request-id": "rid-2"},
        )
    )
    async with AsyncWarmbly(api_key="wmbly_x", max_retries=0) as client:
        with pytest.raises(PermissionDeniedError) as info:
            await client.get("/me", cast_to=dict)
    assert info.value.code == ErrorCode.API_KEY_HOLDER_LEFT
    assert info.value.reason == "left"


# -- scopes -----------------------------------------------------------------


def test_app_grantable_scopes_exclude_only_api_keys() -> None:
    assert "api_keys" not in mask_to_scopes(APP_GRANTABLE_SCOPES)
    assert set(mask_to_scopes(APP_GRANTABLE_SCOPES)) == set(SCOPES) - {"api_keys"}
    assert sum(SCOPES.values()) - SCOPES["api_keys"] == APP_GRANTABLE_SCOPES


# -- oauth error shape ------------------------------------------------------


def test_oauth_error_request_id_from_server_error_body() -> None:
    resp = httpx.Response(
        500,
        json={
            "error": "server_error",
            "error_description": "Something went wrong.",
            "request_id": "req-9",
        },
    )
    err = _error_from_response(resp)
    assert err.error == "server_error"
    assert err.request_id == "req-9"


def test_oauth_error_request_id_falls_back_to_header() -> None:
    resp = httpx.Response(
        400,
        json={
            "error": "invalid_request",
            "error_description": "Each parameter may be included only once.",
        },
        headers={"x-request-id": "hdr-1"},
    )
    assert _error_from_response(resp).request_id == "hdr-1"
    assert OAuthError("invalid_grant").request_id is None


@respx.mock
def test_sync_refresh_with_reused_token_reports_invalid_grant() -> None:
    respx.post(f"{BASE}/v1/oauth/token").mock(
        return_value=httpx.Response(
            400, json={"error": "invalid_grant", "error_description": "revoked"}
        )
    )
    with (
        OAuth2Client(client_id="wmcid", base_url=BASE) as client,
        pytest.raises(OAuthError) as info,
    ):
        client.refresh_token("wmrt_old")
    assert info.value.error == "invalid_grant"


@pytest.mark.anyio
@respx.mock
async def test_async_token_response_scope_may_be_narrower(anyio_backend: str) -> None:
    respx.post(f"{BASE}/v1/oauth/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "wmat_x",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "wmrt_y",
                "scope": "read_campaigns read_contacts",
            },
        )
    )
    client = AsyncOAuth2Client(client_id="wmcid", base_url=BASE)
    try:
        token = await client.exchange_code(
            "wmac_c", code_verifier="v", redirect_uri="https://a.example/cb"
        )
    finally:
        await client.close()
    assert token.scopes == ["read_campaigns", "read_contacts"]
