"""Tests for the ``oauth_applications`` resource."""

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
def test_create_returns_client_secret(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "app_1",
                "name": "My App",
                "client_id": "cid_123",
                "client_secret": "csecret_xyz",
                "redirect_uris": ["https://app.example.com/cb"],
                "scopes": 7,
            },
        )
    )

    app = client.oauth_applications.create(
        name="My App",
        scopes=7,
        redirect_uris=["https://app.example.com/cb"],
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/oauth/applications"
    assert json.loads(request.content) == {
        "name": "My App",
        "scopes": 7,
        "redirect_uris": ["https://app.example.com/cb"],
    }
    assert request.headers.get("idempotency-key")
    assert app.client_id == "cid_123"
    assert app.client_secret == "csecret_xyz"


@respx.mock
def test_rotate_secret(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications/app_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"client_secret": "new_secret"})
    )

    result = client.oauth_applications.rotate_secret("app_1")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/oauth/applications/app_1/rotate-secret"
    assert result.client_secret == "new_secret"


@respx.mock
def test_webhook_secret(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "whsec_abc"})
    )

    result = client.oauth_applications.webhook_secret("app_1")

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/oauth/applications/app_1/webhook-secret"
    assert result.webhook_secret == "whsec_abc"


@respx.mock
def test_rotate_webhook_secret(client: Warmbly) -> None:
    route = respx.post(
        f"{BASE_URL}/oauth/applications/app_1/webhook-secret/rotate"
    ).mock(return_value=httpx.Response(200, json={"webhook_secret": "whsec_new"}))

    result = client.oauth_applications.rotate_webhook_secret("app_1")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/oauth/applications/app_1/webhook-secret/rotate"
    assert result.webhook_secret == "whsec_new"


@respx.mock
def test_update(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(
            200, json={"id": "app_1", "name": "Renamed", "scopes": 15}
        )
    )

    app = client.oauth_applications.update("app_1", name="Renamed", scopes=15)

    request = route.calls.last.request
    assert request.method == "PATCH"
    assert request.url.path == "/v1/oauth/applications/app_1"
    assert json.loads(request.content) == {"name": "Renamed", "scopes": 15}
    assert app.name == "Renamed"


@respx.mock
def test_delete(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )

    result = client.oauth_applications.delete("app_1")

    request = route.calls.last.request
    assert request.method == "DELETE"
    assert request.url.path == "/v1/oauth/applications/app_1"
    assert result.deleted is True


@respx.mock
def test_list(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(
            200,
            json={"applications": [{"id": "app_1", "name": "One"}]},
        )
    )

    apps = list(client.oauth_applications.list())

    assert route.calls.last.request.url.path == "/v1/oauth/applications"
    assert [a.id for a in apps] == ["app_1"]
