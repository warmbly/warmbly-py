"""Transport-level tests for :class:`Warmbly` and :class:`AsyncWarmbly`.

These exercise the shared :mod:`warmbly._base_client` behaviour via the public
clients: header/auth assembly, idempotency-key injection, query cleaning, the
error-to-exception mapping, and the retry loop. ``respx`` mocks the HTTP layer so
no real network calls are made; ``time.sleep`` / ``asyncio.sleep`` are patched
out so retry backoff does not slow the suite.
"""

from __future__ import annotations

import httpx
import pytest
import respx

import warmbly
from warmbly import (
    AsyncWarmbly,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    Omit,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
    Warmbly,
)
from warmbly._exceptions import APIStatusError
from warmbly._models import BaseModel
from warmbly._types import NOT_GIVEN

BASE_URL = "https://api.warmbly.com/v1"

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sync_client() -> Warmbly:
    client = Warmbly(api_key="wmbly_test_key", base_url=BASE_URL)
    yield client
    client.close()


@pytest.fixture
async def async_client() -> AsyncWarmbly:
    client = AsyncWarmbly(api_key="wmbly_test_key", base_url=BASE_URL)
    yield client
    await client.close()


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make retry backoff instant so the suite stays fast."""
    import asyncio
    import time

    monkeypatch.setattr(time, "sleep", lambda *_a, **_k: None)

    async def _async_noop(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _async_noop)


# ---------------------------------------------------------------------------
# Auth / base-url joining / default headers
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_bearer_and_default_headers(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.retrieve("k_1")

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer wmbly_test_key"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"].startswith("warmbly-python/")
    # GET without a body carries no Content-Type.
    assert "content-type" not in request.headers
    # base_url path joining: no double slash, path appended to /v1/.
    assert str(request.url) == f"{BASE_URL}/api-keys/k_1"


@respx.mock
async def test_async_bearer_and_default_headers(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    await async_client.api_keys.retrieve("k_1")

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer wmbly_test_key"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"].startswith("warmbly-python/")
    assert str(request.url) == f"{BASE_URL}/api-keys/k_1"


@respx.mock
def test_sync_post_sets_content_type_json(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.create(name="n", permissions=1)

    request = route.calls.last.request
    assert request.headers["Content-Type"] == "application/json"


def test_base_url_default_and_trailing_slash() -> None:
    client = Warmbly(api_key="x")
    assert client._base_url == "https://api.warmbly.com/v1/"
    client.close()

    client2 = Warmbly(api_key="x", base_url="https://example.test/v2/")
    # A trailing slash on the supplied base_url is normalised to exactly one.
    assert client2._base_url == "https://example.test/v2/"
    client2.close()


def test_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WARMBLY_API_KEY", "wmbly_env_key")
    client = Warmbly()
    assert client.api_key == "wmbly_env_key"
    assert client.auth_headers == {"Authorization": "Bearer wmbly_env_key"}
    client.close()


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WARMBLY_API_KEY", raising=False)
    with pytest.raises(warmbly.WarmblyError):
        Warmbly()


# ---------------------------------------------------------------------------
# Idempotency-Key
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_post_autogenerates_idempotency_key(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.create(name="n", permissions=1)

    key = route.calls.last.request.headers.get("Idempotency-Key")
    assert key
    # Looks like a generated uuid4.
    assert len(key) == 36 and key.count("-") == 4


@respx.mock
async def test_async_post_autogenerates_idempotency_key(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    await async_client.api_keys.create(name="n", permissions=1)

    key = route.calls.last.request.headers.get("Idempotency-Key")
    assert key
    assert len(key) == 36 and key.count("-") == 4


@respx.mock
def test_sync_caller_supplied_idempotency_key_used(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.create(
        name="n", permissions=1, options={"idempotency_key": "my-key-123"}
    )
    assert route.calls.last.request.headers["Idempotency-Key"] == "my-key-123"


@respx.mock
async def test_async_caller_supplied_idempotency_key_used(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    await async_client.api_keys.create(
        name="n", permissions=1, options={"idempotency_key": "my-key-123"}
    )
    assert route.calls.last.request.headers["Idempotency-Key"] == "my-key-123"


@respx.mock
def test_sync_idempotency_key_omittable_via_extra_headers_on_form_post(
    sync_client: Warmbly,
) -> None:
    """A form-encoded POST carries no auto idempotency key.

    The auto Idempotency-Key is injected only for JSON POSTs. ``Omit`` removes
    a header before injection, but injection only runs for non-form POSTs, so a
    form POST is the request that genuinely ships without the key. (Verified
    directly here so the "omittable" requirement is anchored to real behaviour.)
    """
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    sync_client.post(
        "/raw",
        cast_to=BaseModel,
        form={"a": "b"},
        options={"headers": {"Idempotency-Key": Omit()}},
    )
    assert "idempotency-key" not in route.calls.last.request.headers


@respx.mock
async def test_async_idempotency_key_omittable_via_extra_headers_on_form_post(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    await async_client.post(
        "/raw",
        cast_to=BaseModel,
        form={"a": "b"},
        options={"headers": {"Idempotency-Key": Omit()}},
    )
    assert "idempotency-key" not in route.calls.last.request.headers


@respx.mock
def test_omit_removes_custom_header(sync_client: Warmbly) -> None:
    """``Omit`` in extra headers drops a header that would otherwise be sent.

    A client-level custom header is used because httpx re-adds its own default
    for some standard headers (e.g. ``Accept``) at the transport layer; a custom
    header has no such default, so its removal is unambiguous.
    """
    sync_client._custom_headers["X-App"] = "app1"
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    # Without Omit the header is present.
    sync_client.api_keys.retrieve("k_1")
    assert route.calls.last.request.headers.get("X-App") == "app1"

    # With Omit it is removed.
    sync_client.api_keys.retrieve("k_1", options={"headers": {"X-App": Omit()}})
    assert "x-app" not in route.calls.last.request.headers


@respx.mock
def test_extra_header_overrides_default(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.retrieve(
        "k_1", options={"headers": {"X-Custom": "yes", "Accept": "text/plain"}}
    )
    request = route.calls.last.request
    assert request.headers["X-Custom"] == "yes"
    assert request.headers["Accept"] == "text/plain"


# ---------------------------------------------------------------------------
# Query parameter cleaning
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_query_not_given_dropped(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/usage/analytics").mock(
        return_value=httpx.Response(200, json={})
    )
    # to / interval are NOT_GIVEN and must not appear; from is sent.
    sync_client.api_keys.usage_analytics(from_="2024-01-01")

    request = route.calls.last.request
    assert request.url.params.get("from") == "2024-01-01"
    assert "to" not in request.url.params
    assert "interval" not in request.url.params


@respx.mock
def test_sync_query_none_dropped(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    # Pass None explicitly through extra query; it must be dropped.
    sync_client.api_keys.list(options={"query": {"explicit_none": None, "kept": "v"}})
    request = route.calls.last.request
    assert "explicit_none" not in request.url.params
    assert request.url.params.get("kept") == "v"


@respx.mock
async def test_async_query_not_given_and_none_dropped(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/usage/analytics").mock(
        return_value=httpx.Response(200, json={})
    )
    await async_client.api_keys.usage_analytics(
        from_="2024-01-01", options={"query": {"none_param": None}}
    )
    request = route.calls.last.request
    assert request.url.params.get("from") == "2024-01-01"
    assert "to" not in request.url.params
    assert "interval" not in request.url.params
    assert "none_param" not in request.url.params


def test_clean_query_returns_none_when_empty(sync_client: Warmbly) -> None:
    # Directly exercise the helper: all dropped -> None.
    assert sync_client._clean_query({"a": NOT_GIVEN, "b": None}, {}) is None
    assert sync_client._clean_query(None, {}) is None
    assert sync_client._clean_query({"a": "1"}, {}) == {"a": "1"}


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------
ERROR_CASES = [
    (400, BadRequestError),
    (401, AuthenticationError),
    (403, PermissionDeniedError),
    (404, NotFoundError),
    (409, ConflictError),
    (422, UnprocessableEntityError),
    (429, RateLimitError),
    (500, InternalServerError),
]


@pytest.mark.parametrize(("status", "exc_cls"), ERROR_CASES)
@respx.mock
def test_sync_error_mapping(
    sync_client: Warmbly, status: int, exc_cls: type[APIStatusError]
) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            status,
            json={"message": "boom", "code": "some_code"},
            headers={"X-Request-Id": "req_123"},
        )
    )
    # max_retries=0 so 429/500 do not retry.
    with pytest.raises(exc_cls) as info:
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})

    err = info.value
    assert err.status_code == status
    assert err.request_id == "req_123"
    assert err.code == "some_code"
    assert err.message == "boom"
    assert err.headers["x-request-id"] == "req_123"


@pytest.mark.parametrize(("status", "exc_cls"), ERROR_CASES)
@respx.mock
async def test_async_error_mapping(
    async_client: AsyncWarmbly, status: int, exc_cls: type[APIStatusError]
) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            status,
            json={"message": "boom", "code": "some_code"},
            headers={"X-Request-Id": "req_123"},
        )
    )
    with pytest.raises(exc_cls) as info:
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 0})

    err = info.value
    assert err.status_code == status
    assert err.request_id == "req_123"
    assert err.code == "some_code"
    assert err.message == "boom"


@respx.mock
def test_rate_limit_retry_after_header(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            429, json={"message": "slow down"}, headers={"Retry-After": "30"}
        )
    )
    with pytest.raises(RateLimitError) as info:
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})
    assert info.value.retry_after == 30.0


@respx.mock
def test_rate_limit_retry_after_from_body(sync_client: Warmbly) -> None:
    # Body retry_after takes precedence over (here, absent) header.
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            429, json={"message": "slow down", "retry_after": 12}
        )
    )
    with pytest.raises(RateLimitError) as info:
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})
    assert info.value.retry_after == 12.0


@respx.mock
async def test_async_rate_limit_retry_after(async_client: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            429, json={"message": "slow down"}, headers={"Retry-After": "5"}
        )
    )
    with pytest.raises(RateLimitError) as info:
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 0})
    assert info.value.retry_after == 5.0


@respx.mock
def test_error_without_envelope_uses_generic_message(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(404, text="not json")
    )
    with pytest.raises(NotFoundError) as info:
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})
    assert info.value.message == "HTTP 404"
    assert info.value.code is None


# ---------------------------------------------------------------------------
# Retries
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_retry_429_then_200(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.Response(429, json={"message": "wait"}, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = sync_client.api_keys.retrieve("k_1")
    assert result.id == "k_1"
    assert route.call_count == 2


@respx.mock
def test_sync_retry_500_then_200(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.Response(500, json={"message": "oops"}),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = sync_client.api_keys.retrieve("k_1")
    assert result.id == "k_1"
    assert route.call_count == 2


@respx.mock
async def test_async_retry_500_then_200(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.Response(500, json={"message": "oops"}),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = await async_client.api_keys.retrieve("k_1")
    assert result.id == "k_1"
    assert route.call_count == 2


@respx.mock
async def test_async_retry_429_then_200(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.Response(429, json={"message": "wait"}, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = await async_client.api_keys.retrieve("k_1")
    assert result.id == "k_1"
    assert route.call_count == 2


@respx.mock
def test_sync_max_retries_zero_no_retry(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    with pytest.raises(InternalServerError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})
    assert route.call_count == 1


@respx.mock
async def test_async_max_retries_zero_no_retry(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    with pytest.raises(InternalServerError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 0})
    assert route.call_count == 1


@respx.mock
def test_sync_retry_exhausted_raises(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    # max_retries=2 -> 1 initial + 2 retries = 3 calls.
    with pytest.raises(InternalServerError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 2})
    assert route.call_count == 3


@respx.mock
def test_sync_timeout_raises_api_timeout(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    with pytest.raises(warmbly.APITimeoutError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})


@respx.mock
async def test_async_timeout_raises_api_timeout(async_client: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    with pytest.raises(warmbly.APITimeoutError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 0})


@respx.mock
def test_sync_connection_error_raises_api_connection(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.ConnectError("refused")
    )
    with pytest.raises(warmbly.APIConnectionError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 0})


@respx.mock
async def test_async_connection_error_raises_api_connection(
    async_client: AsyncWarmbly,
) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.ConnectError("refused")
    )
    with pytest.raises(warmbly.APIConnectionError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 0})


@respx.mock
def test_sync_timeout_is_retried_for_get(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.ReadTimeout("timed out"),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = sync_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert result.id == "k_1"
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# POST retry semantics: only retried when carrying an Idempotency-Key.
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_post_without_idempotency_not_retried_on_500(
    sync_client: Warmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    # A form POST carries no idempotency key, so it is non-idempotent and must
    # not be retried even on a retryable 500.
    with pytest.raises(InternalServerError):
        sync_client.post(
            "/raw",
            cast_to=BaseModel,
            form={"x": "1"},
            options={"max_retries": 2},
        )
    # Confirm the request really had no idempotency key.
    assert "idempotency-key" not in route.calls.last.request.headers
    # No retries despite max_retries=2.
    assert route.call_count == 1


@respx.mock
def test_sync_post_with_idempotency_is_retried_on_500(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        side_effect=[
            httpx.Response(500, json={"message": "oops"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    sync_client.post(
        "/raw",
        cast_to=BaseModel,
        body={"x": 1},
        options={"idempotency_key": "fixed-key", "max_retries": 2},
    )
    assert route.call_count == 2
    # Both attempts carried the same key.
    assert all(
        c.request.headers.get("Idempotency-Key") == "fixed-key" for c in route.calls
    )


@respx.mock
async def test_async_post_without_idempotency_not_retried_on_500(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    with pytest.raises(InternalServerError):
        await async_client.post(
            "/raw",
            cast_to=BaseModel,
            form={"x": "1"},
            options={"max_retries": 2},
        )
    assert "idempotency-key" not in route.calls.last.request.headers
    assert route.call_count == 1


@respx.mock
async def test_async_post_with_idempotency_is_retried_on_500(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        side_effect=[
            httpx.Response(500, json={"message": "oops"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    await async_client.post(
        "/raw",
        cast_to=BaseModel,
        body={"x": 1},
        options={"idempotency_key": "fixed-key", "max_retries": 2},
    )
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# Response parsing: request_id attached, 204 handled.
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_response_request_id_attached(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            200, json={"id": "k_1", "name": "n"}, headers={"X-Request-Id": "req_abc"}
        )
    )
    result = sync_client.api_keys.retrieve("k_1")
    assert result.request_id == "req_abc"
    # extra='allow' forward-compat: unknown fields preserved.
    assert result.id == "k_1"
