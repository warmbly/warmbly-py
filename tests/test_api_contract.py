"""Client behavior tied to the API's cross-cutting contract.

Covers the error envelope (``code`` and ``reason``), retryable 503s and their
``Retry-After``, the one 503 that is permanent, header hygiene (the server
refuses a repeated credential or ``Idempotency-Key`` line), and the named
constants for error codes and scopes.
"""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest
import respx

from warmbly import (
    ALL_SCOPES,
    APP_GRANTABLE_SCOPES,
    SCOPES,
    APIError,
    AsyncWarmbly,
    ErrorCode,
    ServiceUnavailableError,
    Warmbly,
)
from warmbly._exceptions import make_status_error

BASE_URL = "https://api.warmbly.com/v1"
URL = f"{BASE_URL}/api-keys/k_1"

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s, *_a, **_k: slept.append(s))

    async def _async_sleep(s: float, *_a: object, **_k: object) -> None:
        slept.append(s)

    monkeypatch.setattr(asyncio, "sleep", _async_sleep)
    return slept


# -- error envelope -----------------------------------------------------------


def test_api_error_reads_reason() -> None:
    err = APIError("x", body={"code": "reauth_required", "reason": "fresh_auth"})
    assert err.code == ErrorCode.REAUTH_REQUIRED
    assert err.reason == "fresh_auth"


@pytest.mark.parametrize("body", [None, {"code": "x"}, {"reason": 5}, [1]])
def test_api_error_reason_defaults_to_none(body: object) -> None:
    assert APIError("x", body=body).reason is None


def test_service_unavailable_carries_retry_after() -> None:
    err = make_status_error(
        status_code=503,
        request_id="r1",
        headers={"retry-after": "5"},
        body={"code": "attempt_check_unavailable", "message": "later"},
        retry_after=5.0,
    )
    assert isinstance(err, ServiceUnavailableError)
    assert err.retry_after == 5.0
    assert err.code == ErrorCode.ATTEMPT_CHECK_UNAVAILABLE
    assert err.status_code == 503


def test_service_unavailable_retry_after_defaults_to_none() -> None:
    err = ServiceUnavailableError("down", status_code=503)
    assert err.retry_after is None


def test_error_code_values_are_the_wire_strings() -> None:
    assert ErrorCode.DUPLICATE_QUERY_PARAMETER == "duplicate_query_parameter"
    assert ErrorCode.DUPLICATE_HEADER == "duplicate_header"
    assert ErrorCode.SESSION_ENDED == "session_ended"
    assert ErrorCode.API_KEY_PERMISSIONS_EXCEED_CALLER == (
        "api_key_permissions_exceed_caller"
    )
    values = [
        v for k, v in vars(ErrorCode).items() if k.isupper() and isinstance(v, str)
    ]
    assert len(values) == len(set(values))
    assert all(v == v.lower() for v in values)


# -- 503 retry semantics -------------------------------------------------------


@respx.mock
def test_sync_503_is_retried_honoring_retry_after(_no_sleep: list[float]) -> None:
    route = respx.get(URL).mock(
        side_effect=[
            httpx.Response(
                503,
                json={"code": "service_unavailable", "message": "later"},
                headers={"Retry-After": "7"},
            ),
            httpx.Response(200, json={"id": "k_1"}),
        ]
    )
    with Warmbly(api_key="wmbly_k", base_url=BASE_URL) as client:
        assert client.api_keys.retrieve("k_1").id == "k_1"
    assert route.call_count == 2
    assert _no_sleep == [7.0]


@respx.mock
async def test_async_503_is_retried_honoring_retry_after(
    _no_sleep: list[float],
) -> None:
    route = respx.get(URL).mock(
        side_effect=[
            httpx.Response(
                503, json={"code": "service_unavailable"}, headers={"Retry-After": "3"}
            ),
            httpx.Response(200, json={"id": "k_1"}),
        ]
    )
    async with AsyncWarmbly(api_key="wmbly_k", base_url=BASE_URL) as client:
        assert (await client.api_keys.retrieve("k_1")).id == "k_1"
    assert route.call_count == 2
    assert _no_sleep == [3.0]


@respx.mock
def test_sync_ai_not_configured_503_is_not_retried() -> None:
    route = respx.get(URL).mock(
        return_value=httpx.Response(
            503, json={"code": "ai_not_configured", "message": "no AI here"}
        )
    )
    with (
        Warmbly(api_key="wmbly_k", base_url=BASE_URL) as client,
        pytest.raises(ServiceUnavailableError) as info,
    ):
        client.api_keys.retrieve("k_1")
    assert route.call_count == 1
    assert info.value.code == ErrorCode.AI_NOT_CONFIGURED


@respx.mock
async def test_async_ai_not_configured_503_is_not_retried() -> None:
    route = respx.get(URL).mock(
        return_value=httpx.Response(503, json={"code": "ai_not_configured"})
    )
    async with AsyncWarmbly(api_key="wmbly_k", base_url=BASE_URL) as client:
        with pytest.raises(ServiceUnavailableError):
            await client.api_keys.retrieve("k_1")
    assert route.call_count == 1


@respx.mock
def test_sync_503_with_non_json_body_is_retried() -> None:
    route = respx.get(URL).mock(
        side_effect=[
            httpx.Response(503, text="<html>bad gateway</html>"),
            httpx.Response(200, json={"id": "k_1"}),
        ]
    )
    with Warmbly(api_key="wmbly_k", base_url=BASE_URL) as client:
        assert client.api_keys.retrieve("k_1").id == "k_1"
    assert route.call_count == 2


# -- header hygiene -------------------------------------------------------------


@respx.mock
def test_credential_and_idempotency_headers_are_sent_once() -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"id": "k_1"})
    )
    with Warmbly(api_key="wmbly_k", base_url=BASE_URL) as client:
        client.api_keys.create(
            name="n",
            permissions=1,
            options={
                "idempotency_key": "b",
                "headers": {"Idempotency-KEY": "c", "authorization": "Bearer other"},
            },
        )
    headers = route.calls.last.request.headers
    assert len(headers.get_list("authorization")) == 1
    assert len(headers.get_list("idempotency-key")) == 1
    assert headers["idempotency-key"] == "c"


# -- scopes ---------------------------------------------------------------------


def test_app_grantable_scopes_exclude_key_management() -> None:
    assert not APP_GRANTABLE_SCOPES & SCOPES["api_keys"]
    assert APP_GRANTABLE_SCOPES | SCOPES["api_keys"] == ALL_SCOPES
