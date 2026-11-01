"""Tests for templates.analyze, unibox.move_folder, api key purge and OAuth listings."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture
def client() -> Warmbly:
    return Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


@pytest.fixture
def aclient() -> AsyncWarmbly:
    return AsyncWarmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


# -- templates.analyze ------------------------------------------------------

# Built from the gin.H in AnalyzeTemplateContent (LLM path), spamcheck.Finding
# and warmlint.ScoreResult.
ANALYSIS = {
    "score": 62,
    "verdict": "Likely to be filtered",
    "findings": [
        {
            "severity": "high",
            "field": "subject",
            "text": "FREE MONEY",
            "line": 1,
            "excerpt": "FREE MONEY now",
            "issue": "All caps trigger words",
            "suggestion": "Say what you offer plainly",
            "category": "trigger_word",
        }
    ],
    "suggested_subject": "A quick idea for Acme",
    "improvements": ["Cut the second link"],
    "rules": {
        "score": 80,
        "issues": [
            {
                "severity": "warn",
                "code": "all_caps",
                "message": "Caps",
                "field": "subject",
            }
        ],
    },
    "judgment": {
        "reads_as": 0.8,
        "personalization": 0.2,
        "ask": "none",
        "spam_claim": 0.1,
        "confidence": 0.9,
        "model": "m",
        "input_tokens": 100,
    },
    "model": "gpt-x",
    "tokens_used": 321,
    "credits_remaining": 95,
    "credits_charged": 5,
}


def _assert_analysis(a: object) -> None:
    assert a.score == 62  # type: ignore[attr-defined]
    assert a.verdict == "Likely to be filtered"  # type: ignore[attr-defined]
    f = a.findings[0]  # type: ignore[attr-defined]
    assert f["severity"] == "high" and f["field"] == "subject" and f["line"] == 1
    assert a.suggested_subject == "A quick idea for Acme"  # type: ignore[attr-defined]
    assert a.improvements == ["Cut the second link"]  # type: ignore[attr-defined]
    assert a.rules.score == 80  # type: ignore[attr-defined]
    assert a.rules.issues[0]["code"] == "all_caps"  # type: ignore[attr-defined]
    assert a.judgment["ask"] == "none"  # type: ignore[attr-defined]
    assert a.model == "gpt-x" and a.tokens_used == 321  # type: ignore[attr-defined]
    assert a.credits_remaining == 95 and a.credits_charged == 5  # type: ignore[attr-defined]


@respx.mock
def test_templates_analyze(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )

    a = client.templates.analyze(subject="FREE MONEY", body_plain="Hello")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/templates/analyze"
    assert json.loads(request.content) == {
        "subject": "FREE MONEY",
        "body_plain": "Hello",
    }
    assert request.headers.get("idempotency-key")
    _assert_analysis(a)


@pytest.mark.anyio
@respx.mock
async def test_async_templates_analyze_judgment_only(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(
            200,
            json={
                "score": 70,
                "verdict": "Reads as a template",
                "findings": [],
                "rules": {"score": 70, "issues": []},
                "judgment": {"ask": "one", "confidence": 0.7},
                "model": "judge",
                "tokens_used": 10,
                "credits_remaining": 3,
                "credits_charged": 0,
            },
        )
    )

    a = await aclient.templates.analyze(body_html="<p>Hi</p>")

    assert json.loads(route.calls.last.request.content) == {"body_html": "<p>Hi</p>"}
    assert a.findings == []
    assert a.suggested_subject is None
    assert a.improvements == []
    assert a.credits_charged == 0
    assert a.rules.score == 70


# -- unibox.move_folder -----------------------------------------------------


@respx.mock
def test_unibox_move_folder(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": ["m1"], "thread_ids": ["t1"], "folder": "archive"}
        )
    )

    result = client.unibox.move_folder(
        folder="archive", email_ids=["m1"], thread_ids=["t1"]
    )

    request = route.calls.last.request
    assert request.method == "PATCH"
    assert request.url.path == "/v1/unibox/folder"
    assert json.loads(request.content) == {
        "folder": "archive",
        "email_ids": ["m1"],
        "thread_ids": ["t1"],
    }
    assert result.email_ids == ["m1"]
    assert result.thread_ids == ["t1"]
    assert result.folder == "archive"


@pytest.mark.anyio
@respx.mock
async def test_async_unibox_move_folder_threads_only(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": None, "thread_ids": ["t1"], "folder": "trash"}
        )
    )

    result = await aclient.unibox.move_folder(folder="trash", thread_ids=["t1"])

    assert json.loads(route.calls.last.request.content) == {
        "folder": "trash",
        "thread_ids": ["t1"],
    }
    assert result.thread_ids == ["t1"]
    assert result.folder == "trash"


# -- api_keys.delete_permanent ----------------------------------------------


@respx.mock
def test_api_keys_delete_permanent(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/key_1/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )

    result = client.api_keys.delete_permanent("key_1")

    assert route.calls.last.request.method == "DELETE"
    assert route.calls.last.request.url.path == "/v1/api-keys/key_1/permanent"
    assert result.status == "deleted"


@pytest.mark.anyio
@respx.mock
async def test_async_api_keys_delete_permanent(aclient: AsyncWarmbly) -> None:
    respx.delete(f"{BASE_URL}/api-keys/key_1/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    assert (await aclient.api_keys.delete_permanent("key_1")).status == "deleted"


@respx.mock
def test_api_key_permissions_grantable(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(
            200,
            json={
                "permissions": [
                    {
                        "name": "READ_EMAILS",
                        "value": 1,
                        "description": "d",
                        "category": "read",
                    }
                ],
                "presets": {"read_only": 1, "full_access": 3},
                "grantable": 3,
                "app_scopes": 1,
            },
        )
    )
    p = client.api_keys.permissions()
    assert p.grantable == 3 and p.app_scopes == 1
    assert p.permissions[0].name == "READ_EMAILS"


# -- oauth applications: listing and logo -----------------------------------

# Built from models.AppListing.
LISTING = {
    "application_id": "app_1",
    "organization_id": "org_1",
    "slug": "acme-sync",
    "tagline": "Sync Acme",
    "description": "Longer text",
    "category": "crm",
    "install_url": "https://acme.example.com/install",
    "support_url": "https://acme.example.com/help",
    "privacy_url": "https://acme.example.com/privacy",
    "status": "published",
    "status_note": "ok",
    "status_at": "2026-01-02T00:00:00Z",
    "submitted_at": "2026-01-01T00:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def _assert_listing(r: object) -> None:
    lst = r.listing  # type: ignore[attr-defined]
    assert lst.application_id == "app_1"
    assert lst.slug == "acme-sync"
    assert lst.tagline == "Sync Acme"
    assert lst.category == "crm"
    assert lst.install_url == "https://acme.example.com/install"
    assert lst.support_url == "https://acme.example.com/help"
    assert lst.privacy_url == "https://acme.example.com/privacy"
    assert lst.status == "published"
    assert lst.status_note == "ok"
    assert lst.submitted_at == "2026-01-01T00:00:00Z"


@respx.mock
def test_get_listing(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )

    _assert_listing(client.oauth_applications.get_listing("app_1"))

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/oauth/applications/app_1/listing"


@pytest.mark.anyio
@respx.mock
async def test_async_get_listing_unpublished(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"listing": None})
    )
    result = await aclient.oauth_applications.get_listing("app_1")
    assert result.listing is None


@respx.mock
def test_put_listing(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )

    result = client.oauth_applications.put_listing(
        "app_1",
        slug="acme-sync",
        tagline="Sync Acme",
        description="Longer text",
        category="crm",
        install_url="https://acme.example.com/install",
        support_url="https://acme.example.com/help",
        privacy_url="https://acme.example.com/privacy",
    )

    request = route.calls.last.request
    assert request.method == "PUT"
    assert request.url.path == "/v1/oauth/applications/app_1/listing"
    assert json.loads(request.content) == {
        "slug": "acme-sync",
        "tagline": "Sync Acme",
        "description": "Longer text",
        "category": "crm",
        "install_url": "https://acme.example.com/install",
        "support_url": "https://acme.example.com/help",
        "privacy_url": "https://acme.example.com/privacy",
    }
    _assert_listing(result)


@pytest.mark.anyio
@respx.mock
async def test_async_put_listing_partial(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"listing": LISTING})
    )

    result = await aclient.oauth_applications.put_listing("app_1", tagline="Sync Acme")

    assert json.loads(route.calls.last.request.content) == {"tagline": "Sync Acme"}
    _assert_listing(result)


@respx.mock
def test_delete_listing(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )

    result = client.oauth_applications.delete_listing("app_1")

    assert route.calls.last.request.method == "DELETE"
    assert route.calls.last.request.url.path == "/v1/oauth/applications/app_1/listing"
    assert result.deleted is True


@pytest.mark.anyio
@respx.mock
async def test_async_delete_listing(aclient: AsyncWarmbly) -> None:
    respx.delete(f"{BASE_URL}/oauth/applications/app_1/listing").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.oauth_applications.delete_listing("app_1")).deleted is True


APP = {
    "id": "app_1",
    "name": "Acme",
    "logo_url": "https://cdn.example.com/oauth-app-logos/app_1-1.png",
    "suspended_at": "2026-01-03T00:00:00Z",
    "suspended_reason": "policy",
}


@respx.mock
def test_set_logo_uploads_multipart(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications/app_1/logo").mock(
        return_value=httpx.Response(200, json=APP)
    )

    app = client.oauth_applications.set_logo(
        "app_1", file=b"\x89PNGdata", filename="l.png"
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/oauth/applications/app_1/logo"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="l.png"' in request.content
    assert b"\x89PNGdata" in request.content
    assert app.id == "app_1"
    assert app.logo_url == "https://cdn.example.com/oauth-app-logos/app_1-1.png"
    assert app.suspended_at == "2026-01-03T00:00:00Z"
    assert app.suspended_reason == "policy"


@pytest.mark.anyio
@respx.mock
async def test_async_set_logo(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/oauth/applications/app_1/logo").mock(
        return_value=httpx.Response(200, json=APP)
    )
    app = await aclient.oauth_applications.set_logo(
        "app_1", file=b"JPG", filename="l.jpg", content_type="image/jpeg"
    )
    assert b"Content-Type: image/jpeg" in route.calls.last.request.content
    assert app.logo_url.endswith("app_1-1.png")


@respx.mock
def test_delete_logo(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/oauth/applications/app_1/logo").mock(
        return_value=httpx.Response(200, json={**APP, "logo_url": ""})
    )

    app = client.oauth_applications.delete_logo("app_1")

    assert route.calls.last.request.method == "DELETE"
    assert route.calls.last.request.url.path == "/v1/oauth/applications/app_1/logo"
    assert app.id == "app_1"
    assert app.logo_url == ""


@pytest.mark.anyio
@respx.mock
async def test_async_delete_logo(aclient: AsyncWarmbly) -> None:
    respx.delete(f"{BASE_URL}/oauth/applications/app_1/logo").mock(
        return_value=httpx.Response(200, json={**APP, "logo_url": ""})
    )
    assert (await aclient.oauth_applications.delete_logo("app_1")).logo_url == ""
