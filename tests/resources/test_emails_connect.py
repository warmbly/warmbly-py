"""Tests for the ``emails`` connect API, client links and warmup filter tag."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.emails import (
    ClientConnectLinkCreated,
    MailboxConnectBulkResult,
    MailboxConnected,
    MailboxConnectLink,
    MailboxOAuthApp,
    MailboxOAuthApps,
    WarmupFilterTag,
)

BASE_URL = "https://api.warmbly.com/v1"
MAILBOX_ID = "11111111-1111-1111-1111-111111111111"
LINK_ID = "22222222-2222-2222-2222-222222222222"
ORG_ID = "33333333-3333-3333-3333-333333333333"
USER_ID = "44444444-4444-4444-4444-444444444444"


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


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


# -- fixtures built from the Go structs ---------------------------------------

SMTP = {
    "username": "a@example.com",
    "password": "s3cret",
    "host": "smtp.example.com",
    "port": 587,
}
IMAP = {
    "username": "a@example.com",
    "password": "s3cret",
    "host": "imap.example.com",
    "port": 993,
}
WARMUP = {"enabled": True, "start": 2, "max": 40, "increase": 2, "reply_rate": 30}

CONNECTED = {
    "mailbox": {"id": MAILBOX_ID, "email": "a@example.com", "provider": "smtp_imap"},
    "warmup_note": "Warmup not started: plan limit reached.",
}

GRANT_CONNECTED = {
    "mailbox": {"id": MAILBOX_ID, "email": "b@example.com", "provider": "gmail"},
    "renewed": True,
    "warmup_note": "",
}

SMTP_BULK = {
    "data": [
        {"row": 1, "email": "a@example.com", "status": "connected", "id": MAILBOX_ID},
        {
            "row": 2,
            "email": "bad@example.com",
            "status": "failed",
            "code": "smtp_auth_failed",
            "message": "The SMTP server refused the password.",
        },
    ],
    "summary": {"total": 2, "connected": 1, "skipped": 0, "failed": 1},
    "allowance": {"used": 4, "allowance": 10, "remaining": 6, "basis": "plan"},
}

GRANT_BULK = {
    "data": [
        {"row": 1, "email": "b@example.com", "status": "renewed", "id": MAILBOX_ID},
    ],
    "summary": {"total": 1, "connected": 0, "renewed": 1, "failed": 0},
}

CONNECT_LINK = {
    "id": LINK_ID,
    "organization_id": ORG_ID,
    "created_by": USER_ID,
    "provider": "gmail",
    "email": "owner@example.com",
    "warmup": {"enabled": True, "max": 40},
    "return_url": "https://partner.example.com/done",
    "status": "pending",
    "expires_at": "2026-11-18T00:00:00Z",
    "created_at": "2026-11-15T00:00:00Z",
    "url": "https://app.warmbly.com/connect/mailbox/tok_secret",
}

REVOKED_CONNECT_LINK = {
    **{k: v for k, v in CONNECT_LINK.items() if k != "url"},
    "status": "revoked",
}

CONNECTED_LINK = {
    **{k: v for k, v in CONNECT_LINK.items() if k != "url"},
    "status": "connected",
    "email_account_id": MAILBOX_ID,
    "completed_at": "2026-11-15T01:00:00Z",
}

OAUTH_APP = {
    "id": LINK_ID,
    "organization_id": ORG_ID,
    "provider": "gmail",
    "client_id": "123.apps.googleusercontent.com",
    "has_secret": True,
    "app_name": "Partner Mail",
    "redirect_url": "https://app.warmbly.com/oauth/google/callback",
    "custom_redirect": False,
    "created_by": USER_ID,
    "created_at": "2026-11-15T00:00:00Z",
    "updated_at": "2026-11-15T00:00:00Z",
    "mailboxes": 3,
}

OAUTH_APPS = {
    "data": [OAUTH_APP],
    "callbacks": {
        "gmail": "https://app.warmbly.com/oauth/google/callback",
        "outlook": "https://app.warmbly.com/oauth/microsoft/callback",
    },
}

CLIENT_LINK = {
    "id": LINK_ID,
    "organization_id": ORG_ID,
    "created_by": USER_ID,
    "label": "Acme onboarding",
    "allowed_providers": ["gmail", "smtp_imap"],
    "max_mailboxes": 10,
    "mailboxes_connected": 2,
    "tag_ids": ["55555555-5555-5555-5555-555555555555"],
    "warmup": True,
    "expires_at": "2026-11-22T00:00:00Z",
    "revoked_at": None,
    "created_at": "2026-11-15T00:00:00Z",
    "last_used_at": "2026-11-15T02:00:00Z",
    "status": "active",
}

CLIENT_LINK_CREATED = {
    "link": CLIENT_LINK,
    "url": "https://app.warmbly.com/connect/tok_client_secret",
}

CLIENT_LINK_PAGE = {
    "data": [CLIENT_LINK],
    "pagination": {"next_cursor": None, "has_more": False},
}

REVOKED_CLIENT_LINK = {
    **CLIENT_LINK,
    "status": "revoked",
    "revoked_at": "2026-11-15T03:00:00Z",
}

CLIENT_LINK_USES = {
    "data": [
        {
            "id": "66666666-6666-6666-6666-666666666666",
            "link_id": LINK_ID,
            "email_account_id": MAILBOX_ID,
            "email": "client@acme.example",
            "provider": "gmail",
            "connected_at": "2026-11-15T02:00:00Z",
        }
    ]
}


def _check_connected(result: MailboxConnected) -> None:
    assert result.mailbox is not None
    assert result.mailbox.id == MAILBOX_ID
    assert result.mailbox.provider == "smtp_imap"
    assert result.warmup_note == "Warmup not started: plan limit reached."
    assert result.renewed is None


def _check_grant(result: MailboxConnected) -> None:
    assert result.mailbox is not None
    assert result.mailbox.provider == "gmail"
    assert result.renewed is True
    assert result.warmup_note == ""


def _check_smtp_bulk(result: MailboxConnectBulkResult) -> None:
    assert result.summary is not None
    assert result.summary.connected == 1
    assert result.summary.failed == 1
    assert result.summary.skipped == 0
    assert result.data[0].id == MAILBOX_ID
    assert result.data[1].status == "failed"
    assert result.data[1].code == "smtp_auth_failed"
    assert result.data[1].row == 2
    assert result.allowance is not None
    assert result.allowance.remaining == 6


def _check_grant_bulk(result: MailboxConnectBulkResult) -> None:
    assert result.summary is not None
    assert result.summary.renewed == 1
    assert result.summary.total == 1
    assert result.data[0].status == "renewed"
    assert result.data[0].email == "b@example.com"
    assert result.allowance is None


def _check_connect_link(link: MailboxConnectLink) -> None:
    assert link.id == LINK_ID
    assert link.organization_id == ORG_ID
    assert link.created_by == USER_ID
    assert link.provider == "gmail"
    assert link.email == "owner@example.com"
    assert link.warmup is not None
    assert link.warmup.enabled is True
    assert link.warmup.max == 40
    assert link.warmup.start is None
    assert link.return_url == "https://partner.example.com/done"
    assert link.status == "pending"
    assert link.expires_at == "2026-11-18T00:00:00Z"
    assert link.url == "https://app.warmbly.com/connect/mailbox/tok_secret"
    assert "tok_secret" not in repr(link)


def _check_oauth_app(app: MailboxOAuthApp) -> None:
    assert app.id == LINK_ID
    assert app.provider == "gmail"
    assert app.client_id == "123.apps.googleusercontent.com"
    assert app.has_secret is True
    assert app.app_name == "Partner Mail"
    assert app.custom_redirect is False
    assert app.mailboxes == 3
    assert app.created_by == USER_ID


def _check_oauth_apps(apps: MailboxOAuthApps) -> None:
    _check_oauth_app(apps.data[0])
    assert (
        apps.callbacks["outlook"] == "https://app.warmbly.com/oauth/microsoft/callback"
    )


def _check_client_link_created(created: ClientConnectLinkCreated) -> None:
    assert created.url == "https://app.warmbly.com/connect/tok_client_secret"
    assert "tok_client_secret" not in repr(created)
    assert created.link is not None
    assert created.link.label == "Acme onboarding"
    assert created.link.allowed_providers == ["gmail", "smtp_imap"]
    assert created.link.max_mailboxes == 10
    assert created.link.mailboxes_connected == 2
    assert created.link.tag_ids == ["55555555-5555-5555-5555-555555555555"]
    assert created.link.warmup is True
    assert created.link.revoked_at is None
    assert created.link.last_used_at == "2026-11-15T02:00:00Z"
    assert created.link.status == "active"


def _check_filter_tag(result: WarmupFilterTag, tag: str | None) -> None:
    assert result.tag == tag


# -- connect_smtp_imap --------------------------------------------------------


@respx.mock
def test_connect_smtp_imap_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/smtp-imap").mock(
        return_value=httpx.Response(201, json=CONNECTED)
    )
    result = client.emails.connect_smtp_imap(
        email="a@example.com", smtp=SMTP, imap=IMAP, name="Alex", warmup=WARMUP
    )
    _check_connected(result)
    request = _last(route)
    assert request.headers.get("Idempotency-Key")
    assert _body(route) == {
        "email": "a@example.com",
        "name": "Alex",
        "smtp": SMTP,
        "imap": IMAP,
        "warmup": WARMUP,
    }


@respx.mock
@pytest.mark.anyio
async def test_connect_smtp_imap_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/smtp-imap").mock(
        return_value=httpx.Response(201, json=CONNECTED)
    )
    result = await aclient.emails.connect_smtp_imap(
        email="a@example.com", smtp=SMTP, imap=IMAP
    )
    _check_connected(result)
    assert _last(route).method == "POST"
    assert _body(route) == {"email": "a@example.com", "smtp": SMTP, "imap": IMAP}


# -- connect_smtp_imap_bulk ---------------------------------------------------


@respx.mock
def test_connect_smtp_imap_bulk_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/smtp-imap/bulk").mock(
        return_value=httpx.Response(200, json=SMTP_BULK)
    )
    account = {"email": "a@example.com", "smtp": SMTP, "imap": IMAP}
    result = client.emails.connect_smtp_imap_bulk(accounts=[account], warmup=WARMUP)
    _check_smtp_bulk(result)
    assert _body(route) == {"accounts": [account], "warmup": WARMUP}


@respx.mock
@pytest.mark.anyio
async def test_connect_smtp_imap_bulk_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/smtp-imap/bulk").mock(
        return_value=httpx.Response(200, json=SMTP_BULK)
    )
    account = {"email": "a@example.com", "name": "A", "smtp": SMTP, "imap": IMAP}
    result = await aclient.emails.connect_smtp_imap_bulk(accounts=[account])
    _check_smtp_bulk(result)
    assert _last(route).method == "POST"
    assert _body(route) == {"accounts": [account]}


# -- connect_oauth ------------------------------------------------------------


@respx.mock
def test_connect_oauth_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/oauth").mock(
        return_value=httpx.Response(200, json=GRANT_CONNECTED)
    )
    result = client.emails.connect_oauth(
        provider="gmail", refresh_token="1//rt", email="b@example.com"
    )
    _check_grant(result)
    assert _body(route) == {
        "provider": "gmail",
        "refresh_token": "1//rt",
        "email": "b@example.com",
    }


@respx.mock
@pytest.mark.anyio
async def test_connect_oauth_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/oauth").mock(
        return_value=httpx.Response(200, json=GRANT_CONNECTED)
    )
    result = await aclient.emails.connect_oauth(
        provider="outlook",
        code="auth-code",
        redirect_uri="https://partner.example.com/cb",
        code_verifier="verifier",
        warmup={"enabled": True},
    )
    _check_grant(result)
    assert _last(route).method == "POST"
    assert _body(route) == {
        "provider": "outlook",
        "code": "auth-code",
        "redirect_uri": "https://partner.example.com/cb",
        "code_verifier": "verifier",
        "warmup": {"enabled": True},
    }


# -- connect_oauth_bulk -------------------------------------------------------


@respx.mock
def test_connect_oauth_bulk_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/oauth/bulk").mock(
        return_value=httpx.Response(200, json=GRANT_BULK)
    )
    grant = {"provider": "gmail", "refresh_token": "1//rt"}
    result = client.emails.connect_oauth_bulk(grants=[grant], warmup=WARMUP)
    _check_grant_bulk(result)
    assert _body(route) == {"grants": [grant], "warmup": WARMUP}


@respx.mock
@pytest.mark.anyio
async def test_connect_oauth_bulk_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/oauth/bulk").mock(
        return_value=httpx.Response(200, json=GRANT_BULK)
    )
    grant = {"provider": "gmail", "refresh_token": "1//rt"}
    result = await aclient.emails.connect_oauth_bulk(grants=[grant])
    _check_grant_bulk(result)
    assert _last(route).method == "POST"
    assert _body(route) == {"grants": [grant]}


# -- sign-in links ------------------------------------------------------------


@respx.mock
def test_create_connect_link_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/links").mock(
        return_value=httpx.Response(201, json=CONNECT_LINK)
    )
    link = client.emails.create_connect_link(
        provider="gmail",
        email="owner@example.com",
        warmup={"enabled": True, "max": 40},
        return_url="https://partner.example.com/done",
        expires_in_hours=72,
    )
    _check_connect_link(link)
    assert _body(route) == {
        "provider": "gmail",
        "email": "owner@example.com",
        "warmup": {"enabled": True, "max": 40},
        "return_url": "https://partner.example.com/done",
        "expires_in_hours": 72,
    }


@respx.mock
@pytest.mark.anyio
async def test_create_connect_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/connect/links").mock(
        return_value=httpx.Response(201, json=CONNECT_LINK)
    )
    link = await aclient.emails.create_connect_link(provider="gmail")
    _check_connect_link(link)
    assert _last(route).method == "POST"
    assert _body(route) == {"provider": "gmail"}


@respx.mock
def test_list_connect_links_sync(client: Warmbly) -> None:
    page_two = {
        "data": [CONNECTED_LINK],
        "pagination": {"next_cursor": None, "has_more": False},
    }
    route = respx.get(f"{BASE_URL}/emails/connect/links").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [REVOKED_CONNECT_LINK],
                    "pagination": {"next_cursor": "cur_2", "has_more": True},
                },
            ),
            httpx.Response(200, json=page_two),
        ]
    )
    links = list(client.emails.list_connect_links(limit=1))
    assert [link.status for link in links] == ["revoked", "connected"]
    assert links[1].email_account_id == MAILBOX_ID
    assert links[1].completed_at == "2026-11-15T01:00:00Z"
    assert links[1].url is None
    first, second = route.calls[0].request, route.calls[1].request
    assert first.url.params.get("limit") == "1"
    assert "cursor" not in first.url.params
    assert second.url.params.get("cursor") == "cur_2"


@respx.mock
@pytest.mark.anyio
async def test_list_connect_links_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/connect/links").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [CONNECTED_LINK],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    links = [link async for link in aclient.emails.list_connect_links(cursor="cur_1")]
    assert links[0].id == LINK_ID
    assert links[0].email_account_id == MAILBOX_ID
    assert _last(route).url.params.get("cursor") == "cur_1"


@respx.mock
def test_retrieve_connect_link_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/connect/links/{LINK_ID}").mock(
        return_value=httpx.Response(200, json=CONNECTED_LINK)
    )
    link = client.emails.retrieve_connect_link(LINK_ID)
    assert link.status == "connected"
    assert link.email_account_id == MAILBOX_ID
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_retrieve_connect_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/connect/links/{LINK_ID}").mock(
        return_value=httpx.Response(200, json=CONNECTED_LINK)
    )
    link = await aclient.emails.retrieve_connect_link(LINK_ID)
    assert link.status == "connected"
    assert link.warmup is not None and link.warmup.max == 40
    assert _last(route).method == "GET"


@respx.mock
def test_revoke_connect_link_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/emails/connect/links/{LINK_ID}").mock(
        return_value=httpx.Response(200, json=REVOKED_CONNECT_LINK)
    )
    link = client.emails.revoke_connect_link(LINK_ID)
    assert link.status == "revoked"
    assert link.provider == "gmail"
    assert _last(route).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_revoke_connect_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/emails/connect/links/{LINK_ID}").mock(
        return_value=httpx.Response(200, json=REVOKED_CONNECT_LINK)
    )
    link = await aclient.emails.revoke_connect_link(LINK_ID)
    assert link.status == "revoked"
    assert link.id == LINK_ID
    assert _last(route).method == "DELETE"


# -- OAuth apps ---------------------------------------------------------------


@respx.mock
def test_list_oauth_apps_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/oauth-apps").mock(
        return_value=httpx.Response(200, json=OAUTH_APPS)
    )
    _check_oauth_apps(client.emails.list_oauth_apps())
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_list_oauth_apps_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/oauth-apps").mock(
        return_value=httpx.Response(200, json=OAUTH_APPS)
    )
    _check_oauth_apps(await aclient.emails.list_oauth_apps())
    assert _last(route).method == "GET"


@respx.mock
def test_put_oauth_app_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/emails/oauth-apps/gmail").mock(
        return_value=httpx.Response(200, json=OAUTH_APP)
    )
    app = client.emails.put_oauth_app(
        "gmail",
        client_id="123.apps.googleusercontent.com",
        client_secret="GOCSPX-secret",
        app_name="Partner Mail",
        redirect_url="https://partner.example.com/cb",
    )
    _check_oauth_app(app)
    assert _body(route) == {
        "client_id": "123.apps.googleusercontent.com",
        "client_secret": "GOCSPX-secret",
        "app_name": "Partner Mail",
        "redirect_url": "https://partner.example.com/cb",
    }


@respx.mock
@pytest.mark.anyio
async def test_put_oauth_app_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/emails/oauth-apps/gmail").mock(
        return_value=httpx.Response(200, json=OAUTH_APP)
    )
    app = await aclient.emails.put_oauth_app(
        "gmail", client_id="123.apps.googleusercontent.com"
    )
    _check_oauth_app(app)
    assert _last(route).method == "PUT"
    assert _body(route) == {"client_id": "123.apps.googleusercontent.com"}


@respx.mock
def test_delete_oauth_app_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/emails/oauth-apps/outlook").mock(
        return_value=httpx.Response(204)
    )
    client.emails.delete_oauth_app("outlook")
    assert _last(route).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_delete_oauth_app_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/emails/oauth-apps/outlook").mock(
        return_value=httpx.Response(204)
    )
    await aclient.emails.delete_oauth_app("outlook")
    assert _last(route).method == "DELETE"


# -- client connect links -----------------------------------------------------


@respx.mock
def test_create_client_link_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/client-links").mock(
        return_value=httpx.Response(201, json=CLIENT_LINK_CREATED)
    )
    created = client.emails.create_client_link(
        providers=["gmail", "smtp_imap"],
        max_mailboxes=10,
        label="Acme onboarding",
        expires_in_days=7,
        tag_ids=["55555555-5555-5555-5555-555555555555"],
        warmup=True,
        options={"idempotency_key": "create-acme"},
    )
    _check_client_link_created(created)
    assert _last(route).headers["Idempotency-Key"] == "create-acme"
    assert _body(route) == {
        "label": "Acme onboarding",
        "providers": ["gmail", "smtp_imap"],
        "max_mailboxes": 10,
        "expires_in_days": 7,
        "tag_ids": ["55555555-5555-5555-5555-555555555555"],
        "warmup": True,
    }


@respx.mock
@pytest.mark.anyio
async def test_create_client_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/client-links").mock(
        return_value=httpx.Response(201, json=CLIENT_LINK_CREATED)
    )
    created = await aclient.emails.create_client_link(
        providers=["vendor"], max_mailboxes=5
    )
    _check_client_link_created(created)
    assert _last(route).method == "POST"
    assert _body(route) == {"providers": ["vendor"], "max_mailboxes": 5}


@respx.mock
def test_list_client_links_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/client-links").mock(
        return_value=httpx.Response(200, json=CLIENT_LINK_PAGE)
    )
    links = list(client.emails.list_client_links(limit=20, cursor="cur_1"))
    assert links[0].label == "Acme onboarding"
    assert links[0].allowed_providers == ["gmail", "smtp_imap"]
    params = _last(route).url.params
    assert params.get("limit") == "20"
    assert params.get("cursor") == "cur_1"


@respx.mock
@pytest.mark.anyio
async def test_list_client_links_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/client-links").mock(
        return_value=httpx.Response(200, json=CLIENT_LINK_PAGE)
    )
    links = [link async for link in aclient.emails.list_client_links()]
    assert links[0].max_mailboxes == 10
    assert links[0].status == "active"
    assert dict(_last(route).url.params) == {}


@respx.mock
def test_list_client_link_uses_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/client-links/{LINK_ID}/uses").mock(
        return_value=httpx.Response(200, json=CLIENT_LINK_USES)
    )
    uses = client.emails.list_client_link_uses(LINK_ID)
    assert uses.data[0].link_id == LINK_ID
    assert uses.data[0].email_account_id == MAILBOX_ID
    assert uses.data[0].email == "client@acme.example"
    assert uses.data[0].connected_at == "2026-11-15T02:00:00Z"
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_list_client_link_uses_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/client-links/{LINK_ID}/uses").mock(
        return_value=httpx.Response(200, json=CLIENT_LINK_USES)
    )
    uses = await aclient.emails.list_client_link_uses(LINK_ID)
    assert uses.data[0].provider == "gmail"
    assert uses.data[0].id == "66666666-6666-6666-6666-666666666666"
    assert _last(route).method == "GET"


@respx.mock
def test_revoke_client_link_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/client-links/{LINK_ID}/revoke").mock(
        return_value=httpx.Response(200, json=REVOKED_CLIENT_LINK)
    )
    link = client.emails.revoke_client_link(LINK_ID)
    assert link.status == "revoked"
    assert link.revoked_at == "2026-11-15T03:00:00Z"
    assert _last(route).method == "POST"
    assert _last(route).content == b""


@respx.mock
@pytest.mark.anyio
async def test_revoke_client_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/client-links/{LINK_ID}/revoke").mock(
        return_value=httpx.Response(200, json=REVOKED_CLIENT_LINK)
    )
    link = await aclient.emails.revoke_client_link(LINK_ID)
    assert link.status == "revoked"
    assert link.id == LINK_ID
    assert _last(route).method == "POST"


# -- warmup filter tag --------------------------------------------------------

TAG_PATH = f"{BASE_URL}/emails/{MAILBOX_ID}/warmup-filter-tag"


@respx.mock
def test_warmup_filter_tag_sync(client: Warmbly) -> None:
    route = respx.get(TAG_PATH).mock(
        return_value=httpx.Response(200, json={"tag": "abcd-efgh-jkmn"})
    )
    _check_filter_tag(client.emails.warmup_filter_tag(MAILBOX_ID), "abcd-efgh-jkmn")
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_warmup_filter_tag_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(TAG_PATH).mock(
        return_value=httpx.Response(200, json={"tag": None})
    )
    _check_filter_tag(await aclient.emails.warmup_filter_tag(MAILBOX_ID), None)
    assert _last(route).method == "GET"


@respx.mock
def test_set_warmup_filter_tag_sync(client: Warmbly) -> None:
    route = respx.put(TAG_PATH).mock(
        return_value=httpx.Response(200, json={"tag": "acme-filter"})
    )
    result = client.emails.set_warmup_filter_tag(MAILBOX_ID, tag="acme-filter")
    _check_filter_tag(result, "acme-filter")
    assert _body(route) == {"tag": "acme-filter"}
    assert "Idempotency-Key" not in _last(route).headers

    # A random code with a stable key, so a retry returns the first one.
    result = client.emails.set_warmup_filter_tag(
        MAILBOX_ID, options={"idempotency_key": "tag-once"}
    )
    assert _body(route) == {}
    assert _last(route).headers["Idempotency-Key"] == "tag-once"

    # A header the caller set already wins over the option.
    client.emails.set_warmup_filter_tag(
        MAILBOX_ID,
        options={
            "idempotency_key": "ignored",
            "headers": {"idempotency-key": "explicit"},
        },
    )
    assert _last(route).headers.get_list("Idempotency-Key") == ["explicit"]


@respx.mock
@pytest.mark.anyio
async def test_set_warmup_filter_tag_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(TAG_PATH).mock(
        return_value=httpx.Response(200, json={"tag": "abcd-efgh-jkmn"})
    )
    result = await aclient.emails.set_warmup_filter_tag(
        MAILBOX_ID, options={"idempotency_key": "tag-once", "headers": {"X-A": "b"}}
    )
    _check_filter_tag(result, "abcd-efgh-jkmn")
    request = _last(route)
    assert request.method == "PUT"
    assert request.headers["Idempotency-Key"] == "tag-once"
    assert request.headers["X-A"] == "b"
    assert _body(route) == {}


@respx.mock
def test_clear_warmup_filter_tag_sync(client: Warmbly) -> None:
    route = respx.delete(TAG_PATH).mock(
        return_value=httpx.Response(200, json={"tag": None})
    )
    _check_filter_tag(client.emails.clear_warmup_filter_tag(MAILBOX_ID), None)
    assert _last(route).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_clear_warmup_filter_tag_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(TAG_PATH).mock(
        return_value=httpx.Response(200, json={"tag": None})
    )
    _check_filter_tag(await aclient.emails.clear_warmup_filter_tag(MAILBOX_ID), None)
    assert _last(route).method == "DELETE"
