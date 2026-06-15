"""Tests for the ``api_keys`` resource."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from warmbly import Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture
def client() -> Warmbly:
    return Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


@respx.mock
def test_create_returns_secret(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "ak_1",
                "name": "CI key",
                "permissions": 7,
                "secret": "wmbly_sk_supersecret",
                "key_prefix": "wmbly_",
            },
        )
    )

    key = client.api_keys.create(name="CI key", permissions=7, description="for ci")

    assert route.called
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/api-keys"
    body = json.loads(request.content)
    assert body == {
        "name": "CI key",
        "permissions": 7,
        "description": "for ci",
    }
    # Auto idempotency-key is attached on POST.
    assert request.headers.get("idempotency-key")
    assert request.headers["authorization"] == "Bearer wmbly_test"
    assert key.id == "ak_1"
    assert key.secret == "wmbly_sk_supersecret"


@respx.mock
def test_list_paginates(client: Warmbly) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        if cursor is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "ak_1", "name": "one", "permissions": 1}],
                    "pagination": {
                        "next_cursor": "c2",
                        "has_more": True,
                        "total": 2,
                    },
                },
            )
        assert cursor == "c2"
        return httpx.Response(
            200,
            json={
                "data": [{"id": "ak_2", "name": "two", "permissions": 1}],
                "pagination": {"next_cursor": None, "has_more": False, "total": 2},
            },
        )

    route = respx.get(f"{BASE_URL}/api-keys").mock(side_effect=handler)

    ids = [k.id for k in client.api_keys.list(limit=1)]

    assert ids == ["ak_1", "ak_2"]
    assert route.call_count == 2
    assert route.calls[0].request.url.params.get("limit") == "1"


@respx.mock
def test_retrieve(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/ak_1").mock(
        return_value=httpx.Response(
            200, json={"id": "ak_1", "name": "one", "permissions": 1}
        )
    )

    key = client.api_keys.retrieve("ak_1")

    assert route.called
    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/api-keys/ak_1"
    assert key.id == "ak_1"


@respx.mock
def test_update(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/api-keys/ak_1").mock(
        return_value=httpx.Response(
            200, json={"id": "ak_1", "name": "renamed", "permissions": 3}
        )
    )

    key = client.api_keys.update("ak_1", name="renamed", permissions=3)

    request = route.calls.last.request
    assert request.method == "PATCH"
    assert request.url.path == "/v1/api-keys/ak_1"
    assert json.loads(request.content) == {"name": "renamed", "permissions": 3}
    assert key.name == "renamed"


@respx.mock
def test_delete_reason_is_query_param(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/ak_1").mock(
        return_value=httpx.Response(200, json={"status": "revoked"})
    )

    result = client.api_keys.delete("ak_1", reason="compromised")

    request = route.calls.last.request
    assert request.method == "DELETE"
    assert request.url.path == "/v1/api-keys/ak_1"
    assert request.url.params.get("reason") == "compromised"
    assert result.status == "revoked"


@respx.mock
def test_permissions(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(
            200,
            json={
                "permissions": [{"name": "read", "value": 1, "category": "core"}],
                "presets": {"read_only": 1},
            },
        )
    )

    perms = client.api_keys.permissions()

    assert route.calls.last.request.url.path == "/v1/api-keys/permissions"
    assert perms.presets == {"read_only": 1}
    assert perms.permissions[0].name == "read"


@respx.mock
def test_usage_summary(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys/usage/summary").mock(
        return_value=httpx.Response(
            200, json={"active_keys": 3, "revoked_keys": 1, "requests_24h": 42}
        )
    )

    summary = client.api_keys.usage_summary()

    assert route.calls.last.request.url.path == "/v1/api-keys/usage/summary"
    assert summary.active_keys == 3
    assert summary.requests_24h == 42
