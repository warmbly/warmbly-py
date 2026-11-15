"""Tests for app listings and logos, and permanent API-key deletion."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, ConflictError, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
APP = "3e3e3e3e-0000-4000-8000-000000000001"
KEY = "4f4f4f4f-0000-4000-8000-000000000002"


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


LISTING: dict[str, Any] = {
    "application_id": APP,
    "organization_id": "o1",
    "slug": "acme-sync",
    "tagline": "Sync Acme to Warmbly",
    "description": "Keeps contacts in step.",
    "category": "crm",
    "install_url": "https://acme.example/install",
    "support_url": "https://acme.example/help",
    "privacy_url": "",
    "status": "published",
    "status_note": "",
    "status_at": None,
    "submitted_at": "2026-11-01T09:00:00Z",
    "created_at": "2026-11-01T09:00:00Z",
    "updated_at": "2026-11-01T09:00:00Z",
}

APP_BODY: dict[str, Any] = {
    "id": APP,
    "name": "Acme Sync",
    "logo_url": "https://cdn.example/app-logos/x.png",
    "status": "active",
}

PUT_KWARGS: dict[str, Any] = {
    "slug": "acme-sync",
    "tagline": "Sync Acme to Warmbly",
    "category": "crm",
    "install_url": "https://acme.example/install",
    "description": "Keeps contacts in step.",
    "support_url": "https://acme.example/help",
    "privacy_url": "",
}


def _check_listing(out: Any) -> None:
    assert out.listing is not None
    assert out.listing.application_id == APP
    assert out.listing.slug == "acme-sync"
    assert out.listing.category == "crm"
    assert out.listing.status == "published"
    assert out.listing.status_at is None
    assert out.listing.support_url == "https://acme.example/help"


@respx.mock
def test_listing_sync(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    _check_listing(client.oauth_applications.get_listing(APP))
    assert _last(get).method == "GET"

    get.mock(return_value=httpx.Response(200, json={"listing": None}))
    assert client.oauth_applications.get_listing(APP).listing is None

    put = respx.put(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    _check_listing(client.oauth_applications.put_listing(APP, **PUT_KWARGS))
    assert json.loads(_last(put).content) == PUT_KWARGS
    client.oauth_applications.put_listing(
        APP,
        slug="s-1",
        tagline="t",
        category="other",
        install_url="https://x.example/i",
    )
    assert json.loads(_last(put).content) == {
        "slug": "s-1",
        "tagline": "t",
        "category": "other",
        "install_url": "https://x.example/i",
    }

    delete = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.oauth_applications.delete_listing(APP).deleted is True
    assert _last(delete).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_listing_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    _check_listing(await aclient.oauth_applications.get_listing(APP))

    put = respx.put(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    _check_listing(await aclient.oauth_applications.put_listing(APP, **PUT_KWARGS))
    assert json.loads(_last(put).content) == PUT_KWARGS

    respx.delete(f"{BASE_URL}/oauth/applications/{APP}/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.oauth_applications.delete_listing(APP)).deleted is True


@respx.mock
def test_logo_sync(client: Warmbly) -> None:
    post = respx.post(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APP_BODY)
    )
    app = client.oauth_applications.set_logo(
        APP, file=b"\x89PNG", filename="l.png", content_type="image/png"
    )
    request = _last(post)
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'filename="l.png"' in request.content
    assert "Idempotency-Key" not in request.headers
    assert app.logo_url == "https://cdn.example/app-logos/x.png"

    delete = respx.delete(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json={**APP_BODY, "logo_url": ""})
    )
    assert client.oauth_applications.remove_logo(APP).logo_url == ""
    assert _last(delete).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_logo_async(aclient: AsyncWarmbly) -> None:
    post = respx.post(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json=APP_BODY)
    )
    app = await aclient.oauth_applications.set_logo(APP, file=b"GIF89a")
    assert b'filename="logo.png"' in _last(post).content
    assert app.name == "Acme Sync"

    respx.delete(f"{BASE_URL}/oauth/applications/{APP}/logo").mock(
        return_value=httpx.Response(200, json={**APP_BODY, "logo_url": ""})
    )
    assert (await aclient.oauth_applications.remove_logo(APP)).logo_url == ""


@respx.mock
def test_delete_permanently_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/{KEY}/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    assert client.api_keys.delete_permanently(KEY).status == "deleted"
    assert _last(route).url.path == f"/v1/api-keys/{KEY}/permanent"

    route.mock(
        return_value=httpx.Response(
            409, json={"message": "Revoke the key first.", "code": "conflict"}
        )
    )
    with pytest.raises(ConflictError):
        client.api_keys.delete_permanently(KEY)


@respx.mock
@pytest.mark.anyio
async def test_delete_permanently_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/{KEY}/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    out = await aclient.api_keys.delete_permanently(KEY)
    assert out.status == "deleted"
    assert _last(route).method == "DELETE"
