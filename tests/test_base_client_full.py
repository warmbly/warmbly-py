"""Exhaustive transport-core tests for :mod:`warmbly._base_client`.

These cover the retry/backoff math, ``Retry-After`` parsing (numeric, HTTP-date,
past-date clamp, malformed, body precedence), the retry loop on both the sync
and async clients (status retries, transport-error retries, non-idempotent POST
behaviour), header assembly, query cleaning, 204 handling, non-dict pagination
bodies, context-manager close, and the base ``auth_headers`` default.

``respx`` mocks the HTTP layer; ``time.sleep`` / ``asyncio.sleep`` are patched so
no real backoff slows the suite. ``filterwarnings = error`` means a passing run
emits zero warnings, so every client is always closed.
"""

from __future__ import annotations

import email.utils
import time

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Omit, Warmbly
from warmbly._base_client import (
    INITIAL_RETRY_DELAY,
    MAX_SERVER_RETRY_AFTER,
    AsyncAPIClient,
    BaseClient,
    SyncAPIClient,
    _get_header,
    _parse_retry_after,
    _user_agent,
)
from warmbly._exceptions import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
)
from warmbly._models import BaseModel
from warmbly._types import NOT_GIVEN

BASE_URL = "https://api.warmbly.com/v1"

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sync_client() -> Warmbly:
    client = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
    yield client
    client.close()


@pytest.fixture
async def async_client() -> AsyncWarmbly:
    client = AsyncWarmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
    yield client
    await client.close()


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralise real backoff so the suite is instant."""
    import asyncio

    monkeypatch.setattr(time, "sleep", lambda *_a, **_k: None)

    async def _async_noop(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _async_noop)


# ---------------------------------------------------------------------------
# _parse_retry_after
# ---------------------------------------------------------------------------
def test_parse_retry_after_numeric_header() -> None:
    assert _parse_retry_after({"Retry-After": "30"}) == 30.0
    # Lowercase header name is also honoured.
    assert _parse_retry_after({"retry-after": "5"}) == 5.0


def test_parse_retry_after_http_date_future_positive() -> None:
    future = time.time() + 50
    raw = email.utils.formatdate(future, usegmt=True)
    delay = _parse_retry_after({"Retry-After": raw})
    assert delay is not None
    # Allow a little slack for clock movement between formatdate and parse.
    assert 40 < delay <= 51


def test_parse_retry_after_http_date_past_clamps_to_zero() -> None:
    past = time.time() - 500
    raw = email.utils.formatdate(past, usegmt=True)
    assert _parse_retry_after({"Retry-After": raw}) == 0.0


def test_parse_retry_after_malformed_header_returns_none() -> None:
    assert _parse_retry_after({"Retry-After": "not-a-date"}) is None


def test_parse_retry_after_no_header_returns_none() -> None:
    assert _parse_retry_after({}) is None


def test_parse_retry_after_body_precedence_over_header() -> None:
    # Body retry_after wins over the header.
    delay = _parse_retry_after({"Retry-After": "30"}, {"retry_after": 7})
    assert delay == 7.0


def test_parse_retry_after_body_non_numeric_falls_through_to_header() -> None:
    delay = _parse_retry_after({"Retry-After": "9"}, {"retry_after": "nope"})
    assert delay == 9.0


def test_parse_retry_after_body_without_key_uses_header() -> None:
    assert _parse_retry_after({"Retry-After": "3"}, {"other": 1}) == 3.0


# ---------------------------------------------------------------------------
# _retry_delay
# ---------------------------------------------------------------------------
def test_retry_delay_uses_server_value_within_bounds(sync_client: Warmbly) -> None:
    # A server Retry-After within (0, 60] is used verbatim.
    assert sync_client._retry_delay(1, {"Retry-After": "12"}) == 12.0
    assert sync_client._retry_delay(1, {"Retry-After": "60"}) == 60.0


def test_retry_delay_server_over_max_falls_back_to_backoff(
    sync_client: Warmbly,
) -> None:
    over = MAX_SERVER_RETRY_AFTER + 1
    delay = sync_client._retry_delay(0, {"Retry-After": str(over)})
    # Ignored: falls back to exponential backoff (attempt 0 -> ~INITIAL).
    assert delay != over
    assert 0 < delay <= INITIAL_RETRY_DELAY


def test_retry_delay_zero_server_value_falls_back(sync_client: Warmbly) -> None:
    # 0 is not within (0, 60], so backoff is used.
    delay = sync_client._retry_delay(0, {"Retry-After": "0"})
    assert 0 < delay <= INITIAL_RETRY_DELAY


def test_retry_delay_no_headers_uses_backoff(sync_client: Warmbly) -> None:
    delay = sync_client._retry_delay(0, None)
    assert 0 < delay <= INITIAL_RETRY_DELAY


def test_retry_delay_backoff_is_bounded_and_jittered(sync_client: Warmbly) -> None:
    # Large attempt is clamped to MAX_RETRY_DELAY * jitter; jitter is 0.75-1.0x.
    delay = sync_client._retry_delay(10, None)
    assert 0 < delay <= 8.0


# ---------------------------------------------------------------------------
# Base auth_headers default + _user_agent
# ---------------------------------------------------------------------------
def test_base_client_default_auth_headers_empty() -> None:
    client = BaseClient(base_url=BASE_URL, timeout=None, max_retries=0)
    assert client.auth_headers == {}


def test_bare_sync_api_client_auth_headers_empty() -> None:
    client = SyncAPIClient(base_url=BASE_URL)
    try:
        assert client.auth_headers == {}
    finally:
        client.close()


def test_user_agent_format() -> None:
    assert _user_agent().startswith("warmbly-python/")


# ---------------------------------------------------------------------------
# _get_header helper
# ---------------------------------------------------------------------------
def test_get_header_case_insensitive_and_miss() -> None:
    headers = {"X-Foo": "bar"}
    assert _get_header(headers, "x-foo") == "bar"
    assert _get_header(headers, "missing") is None


# ---------------------------------------------------------------------------
# Header assembly
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_default_headers(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.retrieve("k_1")
    request = route.calls.last.request
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"].startswith("warmbly-python/")
    assert request.headers["Authorization"] == "Bearer wmbly_test"
    assert "content-type" not in request.headers


@respx.mock
def test_sync_custom_headers_merge(sync_client: Warmbly) -> None:
    sync_client._custom_headers["X-App"] = "merged"
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.retrieve("k_1")
    assert route.calls.last.request.headers["X-App"] == "merged"


@respx.mock
def test_sync_extra_header_overrides_default_case_insensitively(
    sync_client: Warmbly,
) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    # Lowercase 'accept' must override the default 'Accept' default.
    sync_client.api_keys.retrieve(
        "k_1", options={"headers": {"accept": "text/plain", "X-New": "1"}}
    )
    request = route.calls.last.request
    assert request.headers["Accept"] == "text/plain"
    assert request.headers["X-New"] == "1"


@respx.mock
def test_sync_omit_removes_default_custom_header(sync_client: Warmbly) -> None:
    sync_client._custom_headers["X-App"] = "app1"
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    sync_client.api_keys.retrieve("k_1", options={"headers": {"X-App": Omit()}})
    assert "x-app" not in route.calls.last.request.headers


@respx.mock
def test_sync_omit_idempotency_key_suppresses_injection(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    sync_client.post(
        "/raw",
        cast_to=BaseModel,
        body={"x": 1},
        options={"headers": {"Idempotency-Key": Omit()}},
    )
    assert "idempotency-key" not in route.calls.last.request.headers


@respx.mock
def test_sync_explicit_idempotency_key_used_verbatim(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    sync_client.post(
        "/raw",
        cast_to=BaseModel,
        body={"x": 1},
        options={"idempotency_key": "verbatim-123"},
    )
    assert route.calls.last.request.headers["Idempotency-Key"] == "verbatim-123"


@respx.mock
def test_sync_caller_header_idempotency_key_disables_autogen(
    sync_client: Warmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    # An explicit header counts as has_idempotency -> no uuid injection.
    sync_client.post(
        "/raw",
        cast_to=BaseModel,
        body={"x": 1},
        options={"headers": {"Idempotency-Key": "header-key"}},
    )
    assert route.calls.last.request.headers["Idempotency-Key"] == "header-key"


# ---------------------------------------------------------------------------
# Query cleaning
# ---------------------------------------------------------------------------
def test_clean_query_drops_not_given_and_none(sync_client: Warmbly) -> None:
    assert sync_client._clean_query({"a": NOT_GIVEN, "b": None}, {}) is None
    assert sync_client._clean_query(None, {}) is None
    assert sync_client._clean_query({"a": "1", "b": None}, {}) == {"a": "1"}


def test_clean_query_merges_extra_query(sync_client: Warmbly) -> None:
    cleaned = sync_client._clean_query({"a": "1"}, {"query": {"b": "2", "c": None}})
    assert cleaned == {"a": "1", "b": "2"}


# ---------------------------------------------------------------------------
# Retry loop: status-based (sync)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("status", [429, 500, 408, 409])
@respx.mock
def test_sync_retries_status_then_succeeds(sync_client: Warmbly, status: int) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.Response(status, json={"message": "x"}, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = sync_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert result.id == "k_1"
    assert route.call_count == 2


@respx.mock
def test_sync_does_not_retry_400(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(400, json={"message": "bad"})
    )
    with pytest.raises(BadRequestError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 3})
    assert route.call_count == 1


@respx.mock
def test_sync_does_not_retry_404(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(404, json={"message": "missing"})
    )
    with pytest.raises(NotFoundError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 3})
    assert route.call_count == 1


@respx.mock
def test_sync_post_without_idempotency_not_retried(sync_client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    with pytest.raises(InternalServerError):
        sync_client.post(
            "/raw", cast_to=BaseModel, form={"x": "1"}, options={"max_retries": 3}
        )
    assert "idempotency-key" not in route.calls.last.request.headers
    assert route.call_count == 1


@respx.mock
def test_sync_post_with_idempotency_is_retried(sync_client: Warmbly) -> None:
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
        options={"idempotency_key": "fixed", "max_retries": 2},
    )
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# Retry loop: transport errors (sync)
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_timeout_retried_then_api_timeout(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.TimeoutException("x")
    )
    with pytest.raises(APITimeoutError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    # 1 initial + 1 retry = 2 attempts before exhaustion.
    assert route.call_count == 2


@respx.mock
def test_sync_connect_error_retried_then_api_connection(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.ConnectError("refused")
    )
    with pytest.raises(APIConnectionError):
        sync_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert route.call_count == 2


@respx.mock
def test_sync_timeout_then_success(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.TimeoutException("x"),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = sync_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert result.id == "k_1"
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# Retry loop: status-based (async)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("status", [429, 500, 408, 409])
@respx.mock
async def test_async_retries_status_then_succeeds(
    async_client: AsyncWarmbly, status: int
) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.Response(status, json={"message": "x"}, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = await async_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert result.id == "k_1"
    assert route.call_count == 2


@respx.mock
async def test_async_does_not_retry_400(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(400, json={"message": "bad"})
    )
    with pytest.raises(BadRequestError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 3})
    assert route.call_count == 1


@respx.mock
async def test_async_does_not_retry_404(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(404, json={"message": "missing"})
    )
    with pytest.raises(NotFoundError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 3})
    assert route.call_count == 1


@respx.mock
async def test_async_post_without_idempotency_not_retried(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.post(f"{BASE_URL}/raw").mock(
        return_value=httpx.Response(500, json={"message": "oops"})
    )
    with pytest.raises(InternalServerError):
        await async_client.post(
            "/raw", cast_to=BaseModel, form={"x": "1"}, options={"max_retries": 3}
        )
    assert "idempotency-key" not in route.calls.last.request.headers
    assert route.call_count == 1


@respx.mock
async def test_async_post_with_idempotency_is_retried(
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
        options={"idempotency_key": "fixed", "max_retries": 2},
    )
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# Retry loop: transport errors (async)
# ---------------------------------------------------------------------------
@respx.mock
async def test_async_timeout_retried_then_api_timeout(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.TimeoutException("x")
    )
    with pytest.raises(APITimeoutError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert route.call_count == 2


@respx.mock
async def test_async_connect_error_retried_then_api_connection(
    async_client: AsyncWarmbly,
) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=httpx.ConnectError("refused")
    )
    with pytest.raises(APIConnectionError):
        await async_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert route.call_count == 2


@respx.mock
async def test_async_timeout_then_success(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        side_effect=[
            httpx.TimeoutException("x"),
            httpx.Response(200, json={"id": "k_1", "name": "ok"}),
        ]
    )
    result = await async_client.api_keys.retrieve("k_1", options={"max_retries": 1})
    assert result.id == "k_1"
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# 204 No Content
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_204_returns_none(sync_client: Warmbly) -> None:
    # 204 short-circuits before any JSON parse; with a None cast it yields None.
    respx.delete(f"{BASE_URL}/raw").mock(return_value=httpx.Response(204))
    result = sync_client.delete("/raw", cast_to=type(None))
    assert result is None


@respx.mock
async def test_async_204_returns_none(async_client: AsyncWarmbly) -> None:
    respx.delete(f"{BASE_URL}/raw").mock(return_value=httpx.Response(204))
    result = await async_client.delete("/raw", cast_to=type(None))
    assert result is None


# ---------------------------------------------------------------------------
# HTTP verb helpers (patch / put / delete) on both clients
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_patch_put_delete(sync_client: Warmbly) -> None:
    respx.patch(f"{BASE_URL}/r").mock(return_value=httpx.Response(200, json={"ok": 1}))
    respx.put(f"{BASE_URL}/r").mock(return_value=httpx.Response(200, json={"ok": 1}))
    respx.delete(f"{BASE_URL}/r").mock(return_value=httpx.Response(200, json={"ok": 1}))
    assert sync_client.patch("/r", cast_to=BaseModel, body={"a": 1}) is not None
    assert sync_client.put("/r", cast_to=BaseModel, body={"a": 1}) is not None
    assert sync_client.delete("/r", cast_to=BaseModel) is not None


@respx.mock
async def test_async_patch_put_delete(async_client: AsyncWarmbly) -> None:
    respx.patch(f"{BASE_URL}/r").mock(return_value=httpx.Response(200, json={"ok": 1}))
    respx.put(f"{BASE_URL}/r").mock(return_value=httpx.Response(200, json={"ok": 1}))
    respx.delete(f"{BASE_URL}/r").mock(return_value=httpx.Response(200, json={"ok": 1}))
    assert await async_client.patch("/r", cast_to=BaseModel, body={"a": 1}) is not None
    assert await async_client.put("/r", cast_to=BaseModel, body={"a": 1}) is not None
    assert await async_client.delete("/r", cast_to=BaseModel) is not None


# ---------------------------------------------------------------------------
# Pagination: get_api_list happy path and non-dict body
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_get_api_list_paginates(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/items").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": "a"}],
                    "pagination": {
                        "next_cursor": "c2",
                        "has_more": True,
                        "total": 2,
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"id": "b"}],
                    "pagination": {"has_more": False},
                },
            ),
        ]
    )
    page = sync_client.get_api_list("/items", model=BaseModel)
    assert [m.id for m in page.data] == ["a"]
    assert page.has_more is True
    assert page.total == 2
    ids = [item.id for item in page]
    assert ids == ["a", "b"]
    assert route.call_count == 2
    # Cursor was forwarded on the second request.
    assert route.calls[1].request.url.params.get("cursor") == "c2"


@respx.mock
def test_sync_get_api_list_non_dict_body_empty(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/items").mock(
        return_value=httpx.Response(200, json=["not", "a", "dict"])
    )
    page = sync_client.get_api_list("/items", model=BaseModel)
    assert page.data == []
    assert page.has_more is False
    assert page.next_cursor is None
    assert page.total is None
    assert route.call_count == 1


@respx.mock
async def test_async_get_api_list_paginates(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/items").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": "a"}],
                    "pagination": {
                        "next_cursor": "c2",
                        "has_more": True,
                        "total": 2,
                    },
                },
            ),
            httpx.Response(
                200,
                json={"data": [{"id": "b"}], "pagination": {"has_more": False}},
            ),
        ]
    )
    ids = [
        item.id async for item in async_client.get_api_list("/items", model=BaseModel)
    ]
    assert ids == ["a", "b"]
    assert route.call_count == 2
    assert route.calls[1].request.url.params.get("cursor") == "c2"


@respx.mock
async def test_async_get_api_list_non_dict_body_empty(
    async_client: AsyncWarmbly,
) -> None:
    respx.get(f"{BASE_URL}/items").mock(
        return_value=httpx.Response(200, json="not-a-dict")
    )
    page = await async_client.get_api_list("/items", model=BaseModel)
    assert page.data == []
    assert page.has_more is False
    assert page.total is None


# ---------------------------------------------------------------------------
# _safe_json fallback: invalid JSON body falls back to text
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_error_non_json_body_falls_back_to_text(sync_client: Warmbly) -> None:
    # A non-JSON error body exercises the _safe_json except branch.
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(
            404,
            content=b"plain text error",
            headers={"Content-Type": "application/json"},
        )
    )
    with pytest.raises(NotFoundError) as info:
        sync_client.api_keys.retrieve("k_1")
    assert info.value.status_code == 404


# ---------------------------------------------------------------------------
# Context managers close the pool
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_context_manager_closes_pool() -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    with Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0) as client:
        client.api_keys.retrieve("k_1")
        http = client._http
    assert http.is_closed


@respx.mock
async def test_async_context_manager_closes_pool() -> None:
    respx.get(f"{BASE_URL}/api-keys/k_1").mock(
        return_value=httpx.Response(200, json={"id": "k_1", "name": "n"})
    )
    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as client:
        await client.api_keys.retrieve("k_1")
        http = client._http
    assert http.is_closed


def test_sync_api_client_enter_exit_closes() -> None:
    with SyncAPIClient(base_url=BASE_URL) as client:
        http = client._http
    assert http.is_closed


async def test_async_api_client_aenter_aexit_closes() -> None:
    async with AsyncAPIClient(base_url=BASE_URL) as client:
        http = client._http
    assert http.is_closed
