"""Server-sync tests for OAuth application logos, listings and suspension."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
APP = "5a8f0c1e-2b3d-4e5f-8a9b-0c1d2e3f4a5b"

APP_JSON = {
    "id": APP,
    "organization_id": "11111111-2222-3333-4444-555555555555",
    "name": "Acme Sync",
    "logo_url": "https://cdn.example.com/logo.png",
    "scopes": 3,
    "status": "active",
    "suspended_at": "2026-10-03T09:00:00Z",
    "suspended_reason": "policy",
}

LISTING_JSON = {
    "application_id": APP,
    "organization_id": "11111111-2222-3333-4444-555555555555",
    "slug": "acme-sync",
    "tagline": "Push positive replies into Acme as deals",
    "description": "",
    "category": "crm",
    "install_url": "https://acme.com/warmbly/install",
    "support_url": "https://acme.com/support",
    "privacy_url": "",
    "status": "hidden",
    "status_note": "taken down",
    "status_at": "2026-10-04T09:00:00Z",
    "submitted_at": "2026-10-03T09:00:00Z",
    "created_at": "2026-10-03T09:00:00Z",
    "updated_at": "2026-10-03T09:00:00Z",
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


def _check_app(app: object) -> None:
    assert app.id == APP  # type: ignore[attr-defined]
    assert app.suspended_at == "2026-10-03T09:00:00Z"  # type: ignore[attr-defined]
    assert app.suspended_reason == "policy"  # type: ignore[attr-defined]


def _check_listing(listing: object) -> None:
    assert listing.application_id == APP  # type: ignore[attr-defined]
    assert listing.slug == "acme-sync"  # type: ignore[attr-defined]
    assert listing.category == "crm"  # type: ignore[attr-defined]
    assert listing.status == "hidden"  # type: ignore[attr-defined]
    assert listing.status_note == "taken down"  # type: ignore[attr-defined]
    assert listing.install_url == "https://acme.com/warmbly/install"  # type: ignore[attr-defined]


@respx.mock
def test_set_logo(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APP_JSON)
    )
    app = client.oauth_applications.set_logo(APP, file=b"PNGDATA")
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"' in request.content
    assert b"PNGDATA" in request.content
    _check_app(app)


@respx.mock
def test_delete_logo(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APP_JSON)
    )
    app = client.oauth_applications.delete_logo(APP)
    assert route.calls.last.request.method == "DELETE"
    _check_app(app)


@respx.mock
def test_retrieve_listing(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING_JSON})
    )
    listing = client.oauth_applications.retrieve_listing(APP)
    assert route.calls.last.request.method == "GET"
    assert listing is not None
    _check_listing(listing)


@respx.mock
def test_retrieve_listing_unpublished(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": None})
    )
    assert client.oauth_applications.retrieve_listing(APP) is None


@respx.mock
def test_put_listing(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING_JSON})
    )
    listing = client.oauth_applications.put_listing(
        APP,
        slug="acme-sync",
        tagline="Push positive replies into Acme as deals",
        category="crm",
        install_url="https://acme.com/warmbly/install",
        support_url="https://acme.com/support",
    )
    request = route.calls.last.request
    assert request.method == "PUT"
    assert json.loads(request.content) == {
        "slug": "acme-sync",
        "tagline": "Push positive replies into Acme as deals",
        "category": "crm",
        "install_url": "https://acme.com/warmbly/install",
        "support_url": "https://acme.com/support",
    }
    _check_listing(listing)


@respx.mock
def test_put_listing_empty_response(client: Warmbly) -> None:
    respx.put(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={})
    )
    listing = client.oauth_applications.put_listing(
        APP, slug="abc", tagline="t", category="other", install_url="https://a.b"
    )
    assert listing.slug is None


@respx.mock
def test_delete_listing(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    result = client.oauth_applications.delete_listing(APP)
    assert route.calls.last.request.method == "DELETE"
    assert result.deleted is True


@pytest.mark.anyio
@respx.mock
async def test_async_logo_and_listing(aclient: AsyncWarmbly) -> None:
    logo = respx.post(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APP_JSON)
    )
    rm_logo = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APP_JSON)
    )
    url = f"{BASE_URL}/oauth/applications/{APP}/listing"
    get = respx.get(url).mock(
        return_value=httpx.Response(200, json={"listing": LISTING_JSON})
    )
    put = respx.put(url).mock(
        return_value=httpx.Response(200, json={"listing": LISTING_JSON})
    )
    rm = respx.delete(url).mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    res = aclient.oauth_applications

    _check_app(await res.set_logo(APP, file=b"PNGDATA"))
    assert b"PNGDATA" in logo.calls.last.request.content
    _check_app(await res.delete_logo(APP))
    assert rm_logo.called

    listing = await res.retrieve_listing(APP)
    assert listing is not None
    _check_listing(listing)
    assert get.calls.last.request.method == "GET"

    listing = await res.put_listing(
        APP,
        slug="acme-sync",
        tagline="Push positive replies into Acme as deals",
        category="crm",
        install_url="https://acme.com/warmbly/install",
        description="d",
        privacy_url="https://acme.com/privacy",
    )
    _check_listing(listing)
    assert json.loads(put.calls.last.request.content)["privacy_url"] == (
        "https://acme.com/privacy"
    )

    assert (await res.delete_listing(APP)).deleted is True
    assert rm.called


@pytest.mark.anyio
@respx.mock
async def test_async_listing_unpublished_and_empty(aclient: AsyncWarmbly) -> None:
    url = f"{BASE_URL}/oauth/applications/{APP}/listing"
    respx.get(url).mock(return_value=httpx.Response(200, json={"listing": None}))
    respx.put(url).mock(return_value=httpx.Response(200, json={}))
    assert await aclient.oauth_applications.retrieve_listing(APP) is None
    listing = await aclient.oauth_applications.put_listing(
        APP, slug="abc", tagline="t", category="other", install_url="https://a.b"
    )
    assert listing.slug is None
