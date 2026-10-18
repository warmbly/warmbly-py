"""Tests for the emails resource additions synced from the server."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


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


def _body(route: respx.Route) -> dict:
    return json.loads(route.calls.last.request.content)


IDENTITY = {
    "supported": True,
    "provider": "gmail",
    "mailbox_email": "me@example.com",
    "send_as_email": "alias@example.com",
    "identities": [
        {
            "email": "me@example.com",
            "name": "Me",
            "is_primary": True,
            "is_default": False,
            "verified": True,
        },
        {
            "email": "alias@example.com",
            "name": "Alias",
            "is_primary": False,
            "is_default": True,
            "verified": True,
        },
    ],
    "synced_at": "2026-10-01T10:00:00Z",
    "signature_source": "provider",
    "signature_imported_at": "2026-10-01T10:00:01Z",
    "future_field": 1,
}

SYNC = {
    "state": {
        "backfill_status": "running",
        "backfill_synced": 120,
        "deferred": 3,
        "throttle_reason": "daily",
        "folders_skipped_cap": 2,
        "folders_skipped_conflict": 1,
    },
    "policy": {
        "backfill_days": 30,
        "backfill_messages": 5000,
        "daily_messages": 500,
        "org_daily_messages": 5000,
        "skip_folders": ["Archive"],
    },
    "skip_folders": ["Archive"],
    "folders": [
        {"name": "INBOX", "folder": "inbox"},
        {"name": "Archive", "folder": "archive"},
    ],
}


def _check_identity(identity) -> None:  # type: ignore[no-untyped-def]
    assert identity.supported is True
    assert identity.mailbox_email == "me@example.com"
    assert identity.send_as_email == "alias@example.com"
    assert [i.email for i in identity.identities] == [
        "me@example.com",
        "alias@example.com",
    ]
    assert identity.identities[0].is_primary is True
    assert identity.identities[1].is_default is True
    assert identity.identities[1].verified is True
    assert identity.signature_source == "provider"
    assert identity.signature_imported_at == "2026-10-01T10:00:01Z"
    assert identity.synced_at == "2026-10-01T10:00:00Z"


def _check_sync(sync) -> None:  # type: ignore[no-untyped-def]
    assert sync.state.backfill_status == "running"
    assert sync.state.folders_skipped_cap == 2
    assert sync.state.folders_skipped_conflict == 1
    assert sync.policy.skip_folders == ["Archive"]
    assert sync.skip_folders == ["Archive"]
    assert [f.name for f in sync.folders] == ["INBOX", "Archive"]
    assert sync.folders[1].folder == "archive"


@respx.mock
def test_direct_tracking_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": True})
    )
    result = client.emails.update_direct_tracking("em_1", enabled=True)
    assert result.track_direct_mail is True
    assert _body(route) == {"enabled": True}


@respx.mock
@pytest.mark.anyio
async def test_direct_tracking_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": False})
    )
    result = await aclient.emails.update_direct_tracking("em_1", enabled=False)
    assert result.track_direct_mail is False
    assert _body(route) == {"enabled": False}


@respx.mock
def test_identity_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/em_1/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(client.emails.identity("em_1"))
    assert route.calls.last.request.method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_identity_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(await aclient.emails.identity("em_1"))


@respx.mock
def test_unsupported_identity(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_2/identity").mock(
        return_value=httpx.Response(
            200, json={"supported": False, "provider": "outlook", "identities": []}
        )
    )
    identity = client.emails.identity("em_2")
    assert identity.supported is False
    assert identity.identities == []


@respx.mock
def test_refresh_identity_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/em_1/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(client.emails.refresh_identity("em_1"))
    assert not route.calls.last.request.content or _body(route) == {}
    _check_identity(client.emails.refresh_identity("em_1", import_signature=True))
    assert _body(route) == {"import_signature": True}


@respx.mock
@pytest.mark.anyio
async def test_refresh_identity_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/em_1/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(
        await aclient.emails.refresh_identity("em_1", import_signature=False)
    )
    assert _body(route) == {"import_signature": False}


@respx.mock
def test_sync_read_and_update_sync(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )
    _check_sync(client.emails.sync("em_1"))
    assert get.calls.last.request.method == "GET"

    put = respx.put(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": ["Archive", "Junk"]})
    )
    result = client.emails.update_sync("em_1", skip_folders=("Archive", "Junk"))
    assert result.skip_folders == ["Archive", "Junk"]
    assert _body(put) == {"skip_folders": ["Archive", "Junk"]}


@respx.mock
@pytest.mark.anyio
async def test_sync_read_and_update_sync_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )
    _check_sync(await aclient.emails.sync("em_1"))

    put = respx.put(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": []})
    )
    result = await aclient.emails.update_sync("em_1", skip_folders=[])
    assert result.skip_folders == []
    assert _body(put) == {"skip_folders": []}


ACCOUNT = {
    "id": "em_1",
    "email": "me@example.com",
    "send_as_email": "alias@example.com",
    "mail_host": "imap.example.com",
    "auth_method": "app_password",
    "domain_grant_id": "dg_1",
    "vendor_connection_id": "vc_1",
    "vendor": "acme",
    "avatar_url": "https://img.example.com/a.png",
    "last_id": 99,
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 40,
    "rolling_recipient_limit": 200,
    "track_direct_mail": True,
    "warmup_placement": "folder",
    "warmup_folder": "Warm",
    "warmup_retention_days": 14,
    "relay_folder_moves": True,
    "tags": ["a"],
}

UPDATE = {
    "send_as_email": "alias@example.com",
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 40,
    "rolling_recipient_limit": 200,
    "send_recovery_resolution": {
        "held_task_id": "t_1",
        "held_reason": "unknown",
        "evidence_type": "provider",
    },
    "warmup_placement": "folder",
    "warmup_folder": "Warm",
    "warmup_retention_days": 14,
    "relay_folder_moves": True,
}


def _check_account(acct) -> None:  # type: ignore[no-untyped-def]
    assert acct.send_as_email == "alias@example.com"
    assert acct.mail_host == "imap.example.com"
    assert acct.auth_method == "app_password"
    assert acct.domain_grant_id == "dg_1"
    assert acct.vendor_connection_id == "vc_1"
    assert acct.vendor == "acme"
    assert acct.avatar_url == "https://img.example.com/a.png"
    assert acct.last_id == 99
    assert acct.test_mode == "diagnostic"
    assert acct.test_send_enabled is True
    assert acct.test_receive_enabled is False
    assert acct.shared_daily_limit == 40
    assert acct.rolling_recipient_limit == 200
    assert acct.track_direct_mail is True
    assert acct.warmup_placement == "folder"
    assert acct.warmup_folder == "Warm"
    assert acct.warmup_retention_days == 14
    assert acct.relay_folder_moves is True


@respx.mock
def test_account_fields_and_update_body(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check_account(client.emails.retrieve("em_1"))

    route = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check_account(client.emails.update("em_1", **UPDATE))  # type: ignore[arg-type]
    assert _body(route) == UPDATE


@respx.mock
@pytest.mark.anyio
async def test_account_update_body_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check_account(await aclient.emails.update("em_1", **UPDATE))  # type: ignore[arg-type]
    assert _body(route) == UPDATE


VERIFY = {
    "email": "a@example.com",
    "status": "risky",
    "sub_status": "catch_all",
    "reason": "accepts all",
    "is_catch_all": True,
    "has_mx": True,
    "provider": "builtin",
    "confidence": 70,
    "checked_at": "2026-10-01T10:00:00Z",
}


@respx.mock
def test_verify_shape(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/verify").mock(
        return_value=httpx.Response(200, json=VERIFY)
    )
    res = client.emails.verify(email="a@example.com")
    assert _body(route) == {"email": "a@example.com"}
    assert res.status == "risky"
    assert res.sub_status == "catch_all"
    assert res.is_catch_all is True
    assert res.has_mx is True
    assert res.provider == "builtin"
    assert res.confidence == 70
    assert res.checked_at == "2026-10-01T10:00:00Z"


@respx.mock
@pytest.mark.anyio
async def test_verify_shape_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/emails/verify").mock(
        return_value=httpx.Response(200, json=VERIFY)
    )
    res = await aclient.emails.verify(email="a@example.com")
    assert res.reason == "accepts all"
    assert res.is_catch_all is True


@respx.mock
def test_routing_update_is_full_replace(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/warmup/routing/wr_1").mock(
        return_value=httpx.Response(200, json={"id": "wr_1", "name": "x"})
    )
    rule = client.warmup_routing.update(
        "wr_1",
        name="x",
        sender_match_type="any",
        recipient_match_type="provider",
        recipient_match_value="google",
        weight=2.0,
        enabled=True,
    )
    assert rule.name == "x"
    assert _body(route) == {
        "name": "x",
        "sender_match_type": "any",
        "recipient_match_type": "provider",
        "recipient_match_value": "google",
        "weight": 2.0,
        "enabled": True,
    }


@respx.mock
@pytest.mark.anyio
async def test_routing_update_is_full_replace_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/warmup/routing/wr_1").mock(
        return_value=httpx.Response(200, json={"id": "wr_1", "name": "x"})
    )
    rule = await aclient.warmup_routing.update(
        "wr_1", name="x", sender_match_type="any", recipient_match_type="any"
    )
    assert rule.id == "wr_1"
    assert _body(route) == {
        "name": "x",
        "sender_match_type": "any",
        "recipient_match_type": "any",
    }
