"""Tests for the per-application logo and listing routes of ``oauth_applications``.

Payloads follow ``OAuthApplication`` in ``internal/models/oauth_app.go`` and
``AppListing`` in ``internal/models/app_directory.go``.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, PermissionDeniedError, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
APP = "a6d7c1de-1f43-4b0e-9a77-5a1f2b3c4d5e"
PNG = b"\x89PNG\r\n\x1a\nfake"

APPLICATION: dict[str, Any] = {
    "id": APP,
    "organization_id": "0b6e5d62-6c43-4d8b-b8d4-6f7f6b8d1111",
    "created_by": "5c0f4f6e-8f43-4e0e-8a87-2d6f64a7f001",
    "name": "Sync Bot",
    "description": "Keeps things in sync",
    "logo_url": "https://cdn.warmbly.test/app-logos/a6d7c1de-1.png",
    "website_url": "https://syncbot.test",
    "client_id": "wmcid_abc",
    "redirect_uris": ["https://syncbot.test/cb"],
    "allowed_webhook_domains": [".syncbot.test"],
    "webhook_url": "https://hooks.syncbot.test/in",
    "webhook_events": ["contact.created"],
    "scopes": 5,
    "status": "active",
    "is_public": False,
    "dynamically_registered": False,
    "suspended_at": "2026-10-02T00:00:00Z",
    "suspended_reason": "abuse report",
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-10-01T00:00:00Z",
}

LISTING: dict[str, Any] = {
    "application_id": APP,
    "organization_id": APPLICATION["organization_id"],
    "slug": "sync-bot",
    "tagline": "Two-way contact sync",
    "description": "Mirrors your contacts.",
    "category": "data",
    "install_url": "https://syncbot.test/install",
    "support_url": "https://syncbot.test/help",
    "privacy_url": "https://syncbot.test/privacy",
    "status": "hidden",
    "status_note": "Missing privacy policy",
    "status_at": "2026-10-03T00:00:00Z",
    "submitted_at": "2026-10-01T00:00:00Z",
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-03T00:00:00Z",
}


@pytest.fixture
def client() -> Iterator[Warmbly]:
    c = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
    yield c
    c.close()


@pytest.fixture
async def aclient() -> AsyncIterator[AsyncWarmbly]:
    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as c:
        yield c


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _check_app(app: Any) -> None:
    assert app.id == APP
    assert app.logo_url == APPLICATION["logo_url"]
    assert app.client_id == "wmcid_abc"
    assert app.suspended_at == "2026-10-02T00:00:00Z"
    assert app.suspended_reason == "abuse report"
    assert app.scopes == 5


def _check_listing(listing: Any) -> None:
    assert listing.application_id == APP
    assert listing.slug == "sync-bot"
    assert listing.tagline == "Two-way contact sync"
    assert listing.category == "data"
    assert listing.install_url == "https://syncbot.test/install"
    assert listing.support_url == "https://syncbot.test/help"
    assert listing.privacy_url == "https://syncbot.test/privacy"
    assert listing.status == "hidden"
    assert listing.status_note == "Missing privacy policy"
    assert listing.status_at == "2026-10-03T00:00:00Z"
    assert listing.submitted_at == "2026-10-01T00:00:00Z"


# -- logo -------------------------------------------------------------------


@respx.mock
def test_set_logo_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APPLICATION)
    )
    _check_app(client.oauth_applications.set_logo(APP, file=PNG))
    request = _last(route)
    assert request.method == "POST"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="logo.png"' in request.content
    assert b"Content-Type: image/png" in request.content
    assert PNG in request.content
    client.oauth_applications.set_logo(
        APP, file=b"jpg", filename="mark.jpg", content_type="image/jpeg"
    )
    assert b'filename="mark.jpg"' in _last(route).content
    assert b"Content-Type: image/jpeg" in _last(route).content


@respx.mock
@pytest.mark.anyio
async def test_set_logo_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APPLICATION)
    )
    _check_app(await aclient.oauth_applications.set_logo(APP, file=PNG))
    request = _last(route)
    assert request.url.path == f"/v1/oauth/applications/{APP}/logo"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert PNG in request.content


@respx.mock
def test_remove_logo_sync(client: Warmbly) -> None:
    cleared = {**APPLICATION, "logo_url": ""}
    route = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=cleared)
    )
    app = client.oauth_applications.remove_logo(APP)
    assert _last(route).method == "DELETE"
    assert app.logo_url == ""
    assert app.id == APP


@respx.mock
@pytest.mark.anyio
async def test_remove_logo_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json={**APPLICATION, "logo_url": ""})
    )
    app = await aclient.oauth_applications.remove_logo(APP)
    assert _last(route).url.path == f"/v1/oauth/applications/{APP}/logo"
    assert app.logo_url == ""


# -- listing ----------------------------------------------------------------


@respx.mock
def test_retrieve_listing_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    result = client.oauth_applications.retrieve_listing(APP)
    assert _last(route).method == "GET"
    assert result.listing is not None
    _check_listing(result.listing)
    route.mock(return_value=httpx.Response(200, json={"listing": None}))
    assert client.oauth_applications.retrieve_listing(APP).listing is None


@respx.mock
@pytest.mark.anyio
async def test_retrieve_listing_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    result = await aclient.oauth_applications.retrieve_listing(APP)
    assert _last(route).url.path == f"/v1/oauth/applications/{APP}/listing"
    assert result.listing is not None
    _check_listing(result.listing)
    route.mock(return_value=httpx.Response(200, json={"listing": None}))
    assert (await aclient.oauth_applications.retrieve_listing(APP)).listing is None


@respx.mock
def test_put_listing_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    result = client.oauth_applications.put_listing(
        APP,
        slug="sync-bot",
        tagline="Two-way contact sync",
        category="data",
        install_url="https://syncbot.test/install",
        description="Mirrors your contacts.",
        support_url="https://syncbot.test/help",
        privacy_url="https://syncbot.test/privacy",
    )
    request = _last(route)
    assert request.method == "PUT"
    assert json.loads(request.content) == {
        "slug": "sync-bot",
        "tagline": "Two-way contact sync",
        "description": "Mirrors your contacts.",
        "category": "data",
        "install_url": "https://syncbot.test/install",
        "support_url": "https://syncbot.test/help",
        "privacy_url": "https://syncbot.test/privacy",
    }
    assert result.listing is not None
    _check_listing(result.listing)
    client.oauth_applications.put_listing(
        APP,
        slug="sync-bot",
        tagline="Two-way contact sync",
        category="data",
        install_url="https://syncbot.test/install",
    )
    assert json.loads(_last(route).content) == {
        "slug": "sync-bot",
        "tagline": "Two-way contact sync",
        "category": "data",
        "install_url": "https://syncbot.test/install",
    }


@respx.mock
@pytest.mark.anyio
async def test_put_listing_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    result = await aclient.oauth_applications.put_listing(
        APP,
        slug="sync-bot",
        tagline="Two-way contact sync",
        category="data",
        install_url="https://syncbot.test/install",
        privacy_url="https://syncbot.test/privacy",
    )
    request = _last(route)
    assert request.url.path == f"/v1/oauth/applications/{APP}/listing"
    assert json.loads(request.content)["privacy_url"] == "https://syncbot.test/privacy"
    assert "description" not in json.loads(request.content)
    assert result.listing is not None
    _check_listing(result.listing)


@respx.mock
def test_delete_listing_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.oauth_applications.delete_listing(APP).deleted is True
    assert _last(route).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_delete_listing_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.oauth_applications.delete_listing(APP)).deleted is True
    assert _last(route).url.path == f"/v1/oauth/applications/{APP}/listing"


# -- OAuth token refusal ----------------------------------------------------


@respx.mock
def test_oauth_token_refusal_surfaces_code(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(
            403,
            json={
                "error": "forbidden",
                "message": "OAuth app tokens cannot manage API keys or OAuth apps. "
                "Use the dashboard or an API key.",
                "code": "oauth_token_not_allowed",
                "request_id": "req_1",
            },
        )
    )
    with pytest.raises(PermissionDeniedError) as info:
        client.oauth_applications.retrieve_listing(APP)
    assert info.value.code == "oauth_token_not_allowed"
