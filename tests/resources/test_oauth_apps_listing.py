"""OAuth applications: per-app logo, directory listing, suspension, developer access."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, v  # noqa: F401

APP = {
    "id": "app_1",
    "organization_id": "org_1",
    "name": "Acme Sync",
    "logo_url": "https://cdn.warmbly.com/oauth-app-logos/org_1/abc.png",
    "scopes": 5,
    "status": "disabled",
    "suspended_at": "2026-10-01T00:00:00Z",
    "suspended_reason": "policy",
}

LISTING = {
    "application_id": "app_1",
    "organization_id": "org_1",
    "slug": "acme-sync",
    "tagline": "Push replies into Acme",
    "description": "Longer text",
    "category": "crm",
    "install_url": "https://acme.com/install",
    "support_url": "https://acme.com/help",
    "privacy_url": "https://acme.com/privacy",
    "status": "hidden",
    "status_note": "misleading name",
    "status_at": "2026-10-02T00:00:00Z",
    "submitted_at": "2026-10-01T00:00:00Z",
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-02T00:00:00Z",
}


def _check_listing(listing: Any) -> None:
    assert listing.application_id == "app_1"
    assert listing.organization_id == "org_1"
    assert (listing.slug, listing.tagline) == ("acme-sync", "Push replies into Acme")
    assert listing.description == "Longer text"
    assert listing.category == "crm"
    assert listing.install_url == "https://acme.com/install"
    assert listing.support_url == "https://acme.com/help"
    assert listing.privacy_url == "https://acme.com/privacy"
    assert (listing.status, listing.status_note) == ("hidden", "misleading name")
    assert listing.status_at == "2026-10-02T00:00:00Z"
    assert listing.submitted_at == "2026-10-01T00:00:00Z"
    assert listing.created_at == "2026-10-01T00:00:00Z"
    assert listing.updated_at == "2026-10-02T00:00:00Z"


@respx.mock
@pytest.mark.anyio
async def test_app_logo_listing_and_access(dual: Any) -> None:
    c = dual.oauth_applications

    logo = respx.post(f"{BASE_URL}/oauth/applications/app_1/logo").mock(
        return_value=httpx.Response(200, json=APP)
    )
    app = await v(c.upload_application_logo("app_1", file=b"\x89PNG", filename="l.png"))
    assert app.logo_url.endswith("abc.png")
    assert app.suspended_at == "2026-10-01T00:00:00Z"
    assert app.suspended_reason == "policy"
    req = last(logo)
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b'filename="l.png"' in req.content

    gone = respx.delete(f"{BASE_URL}/oauth/applications/app_1/logo").mock(
        return_value=httpx.Response(200, json={**APP, "logo_url": ""})
    )
    assert (await v(c.delete_application_logo("app_1"))).logo_url == ""
    assert last(gone).method == "DELETE"

    respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(
            200,
            json={
                "applications": [APP],
                "developer_access": {"blocked": True, "reason": "abuse"},
            },
        )
    )
    access = await v(c.developer_access())
    assert access.blocked is True
    assert access.reason == "abuse"
    listed = await items(c.list())
    assert listed[0].id == "app_1"

    respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(200, json={"applications": []})
    )
    assert (await v(c.developer_access())).blocked is None

    got = respx.get(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    _check_listing((await v(c.get_listing("app_1"))).listing)
    assert last(got).method == "GET"
    respx.get(f"{BASE_URL}/oauth/applications/app_2/listing").mock(
        return_value=httpx.Response(200, json={"listing": None})
    )
    assert (await v(c.get_listing("app_2"))).listing is None

    put = respx.put(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )
    saved = await v(
        c.put_listing(
            "app_1",
            slug="acme-sync",
            tagline="Push replies into Acme",
            category="crm",
            install_url="https://acme.com/install",
            description="Longer text",
            support_url="https://acme.com/help",
            privacy_url="https://acme.com/privacy",
        )
    )
    _check_listing(saved.listing)
    assert json.loads(last(put).content) == {
        "slug": "acme-sync",
        "tagline": "Push replies into Acme",
        "category": "crm",
        "install_url": "https://acme.com/install",
        "description": "Longer text",
        "support_url": "https://acme.com/help",
        "privacy_url": "https://acme.com/privacy",
    }
    await v(
        c.put_listing(
            "app_1",
            slug="acme-sync",
            tagline="t",
            category="crm",
            install_url="https://acme.com/install",
        )
    )
    assert set(json.loads(last(put).content)) == {
        "slug",
        "tagline",
        "category",
        "install_url",
    }

    drop = respx.delete(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await v(c.delete_listing("app_1"))).deleted is True
    assert last(drop).method == "DELETE"
