"""Tests for mailbox certificates, send identity, direct tracking and sync."""

from __future__ import annotations

import json
from typing import Any

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


# Built from models.MailboxCertificates.
CERTS = {
    "smtp": {
        "host": "smtp.example.com",
        "port": 587,
        "tls_unverified": True,
        "tls_pin": "ab" * 32,
        "observed": {
            "fingerprint": "cd" * 32,
            "subject": "CN=smtp.example.com",
            "issuer": "CN=Example CA",
            "not_after": "2027-01-01T00:00:00Z",
            "self_signed": True,
            "trusted": False,
        },
    },
    "imap": {"host": "imap.example.com", "port": 993, "tls_unverified": False},
}


def _assert_certs(c: Any) -> None:
    assert c.smtp.host == "smtp.example.com" and c.smtp.port == 587
    assert c.smtp.tls_unverified is True
    assert c.smtp.tls_pin == "ab" * 32
    assert c.smtp.observed.fingerprint == "cd" * 32
    assert c.smtp.observed.issuer == "CN=Example CA"
    assert c.smtp.observed.not_after == "2027-01-01T00:00:00Z"
    assert c.smtp.observed.self_signed is True
    assert c.imap.host == "imap.example.com" and c.imap.port == 993
    assert c.imap.tls_unverified is False
    assert c.imap.observed is None


@respx.mock
def test_certificates(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/em_1/certificates").mock(
        return_value=httpx.Response(200, json=CERTS)
    )

    _assert_certs(client.emails.certificates("em_1"))

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/emails/em_1/certificates"


@pytest.mark.anyio
@respx.mock
async def test_async_certificates(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/certificates").mock(
        return_value=httpx.Response(200, json=CERTS)
    )
    _assert_certs(await aclient.emails.certificates("em_1"))


# Built from models.SendIdentity / SendAsIdentity.
IDENTITY = {
    "supported": True,
    "provider": "google",
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
            "name": "Sales",
            "is_primary": False,
            "is_default": True,
            "verified": False,
        },
    ],
    "synced_at": "2026-01-01T00:00:00Z",
    "signature_source": "provider",
    "signature_imported_at": "2026-01-01T00:00:01Z",
}


def _assert_identity(i: Any) -> None:
    assert i.supported is True
    assert i.provider == "google"
    assert i.mailbox_email == "me@example.com"
    assert i.send_as_email == "alias@example.com"
    assert [x.email for x in i.identities] == ["me@example.com", "alias@example.com"]
    assert i.identities[0].is_primary is True
    assert i.identities[1].is_default is True
    assert i.identities[1].verified is False
    assert i.synced_at == "2026-01-01T00:00:00Z"
    assert i.signature_source == "provider"
    assert i.signature_imported_at == "2026-01-01T00:00:01Z"


@respx.mock
def test_send_identity(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/emails/em_1/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )

    _assert_identity(client.emails.send_identity("em_1"))

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/emails/em_1/identity"


@pytest.mark.anyio
@respx.mock
async def test_async_send_identity_unsupported(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/identity").mock(
        return_value=httpx.Response(
            200,
            json={
                "supported": False,
                "provider": "outlook",
                "mailbox_email": "me@example.com",
                "send_as_email": "",
                "identities": [],
                "signature_source": "manual",
            },
        )
    )
    i = await aclient.emails.send_identity("em_1")
    assert i.supported is False and i.identities == []
    assert i.synced_at is None


@respx.mock
def test_refresh_send_identity_with_body(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/em_1/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )

    _assert_identity(client.emails.refresh_send_identity("em_1", import_signature=True))

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/emails/em_1/identity/refresh"
    assert json.loads(request.content) == {"import_signature": True}
    assert request.headers.get("idempotency-key")


@pytest.mark.anyio
@respx.mock
async def test_async_refresh_send_identity_without_body(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/em_1/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )

    _assert_identity(await aclient.emails.refresh_send_identity("em_1"))

    assert json.loads(route.calls.last.request.content or b"{}") == {}


@respx.mock
def test_update_direct_tracking(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": True})
    )

    result = client.emails.update_direct_tracking("em_1", enabled=True)

    request = route.calls.last.request
    assert request.method == "PATCH"
    assert request.url.path == "/v1/emails/em_1/direct-tracking"
    assert json.loads(request.content) == {"enabled": True}
    assert result.track_direct_mail is True


@pytest.mark.anyio
@respx.mock
async def test_async_update_direct_tracking(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": False})
    )

    result = await aclient.emails.update_direct_tracking("em_1", enabled=False)

    assert json.loads(route.calls.last.request.content) == {"enabled": False}
    assert result.track_direct_mail is False


SYNC = {
    "state": {
        "backfill_status": "running",
        "backfill_synced": 120,
        "throttle_reason": "daily",
        "deferred": 3,
        "folders_skipped_cap": 2,
        "folders_skipped_conflict": 1,
        "last_synced_at": "2026-01-01T00:00:00Z",
    },
    "policy": {
        "backfill_days": 30,
        "backfill_messages": 1000,
        "daily_messages": 500,
        "org_daily_messages": 5000,
        "skip_folders": ["Junk"],
    },
    "skip_folders": ["Junk"],
    "folders": [
        {"name": "INBOX", "folder": "inbox"},
        {"name": "Junk", "folder": "spam"},
    ],
}


@respx.mock
def test_sync_decodes_folders_and_skip_list(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )

    s = client.emails.sync("em_1")

    assert s.skip_folders == ["Junk"]
    assert [(f.name, f.folder) for f in s.folders] == [
        ("INBOX", "inbox"),
        ("Junk", "spam"),
    ]
    assert s.policy.skip_folders == ["Junk"]
    assert s.policy.daily_messages == 500
    assert s.state.folders_skipped_cap == 2
    assert s.state.folders_skipped_conflict == 1
    assert s.state.deferred == 3


@respx.mock
def test_update_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": ["Junk", "Spam"]})
    )

    result = client.emails.update_sync("em_1", skip_folders=["Junk", "Spam"])

    request = route.calls.last.request
    assert request.method == "PUT"
    assert request.url.path == "/v1/emails/em_1/sync"
    assert json.loads(request.content) == {"skip_folders": ["Junk", "Spam"]}
    assert result.skip_folders == ["Junk", "Spam"]


@pytest.mark.anyio
@respx.mock
async def test_async_update_sync_empty_clears(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": []})
    )

    result = await aclient.emails.update_sync("em_1", skip_folders=[])

    assert json.loads(route.calls.last.request.content) == {"skip_folders": []}
    assert result.skip_folders == []


# -- update body and account model -------------------------------------------


@respx.mock
def test_update_new_fields_are_sent(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "em_1",
                "send_as_email": "alias@example.com",
                "mail_host": "google_workspace",
                "auth_method": "oauth",
                "avatar_url": "https://x/a.png",
                "test_mode": "diagnostic",
                "test_send_enabled": True,
                "test_receive_enabled": False,
                "shared_daily_limit": 10,
                "rolling_recipient_limit": 50,
                "track_direct_mail": True,
                "warmup_placement": "folder",
                "warmup_folder": "Warmup",
                "warmup_retention_days": 14,
                "relay_folder_moves": True,
            },
        )
    )

    acct = client.emails.update(
        "em_1",
        send_as_email="alias@example.com",
        test_mode="diagnostic",
        test_send_enabled=True,
        test_receive_enabled=False,
        shared_daily_limit=10,
        rolling_recipient_limit=50,
        send_recovery_resolution={
            "held_task_id": "t1",
            "held_reason": "r",
            "evidence_type": "e",
        },
        warmup_placement="folder",
        warmup_folder="Warmup",
        warmup_retention_days=14,
        relay_folder_moves=True,
    )

    assert json.loads(route.calls.last.request.content) == {
        "send_as_email": "alias@example.com",
        "test_mode": "diagnostic",
        "test_send_enabled": True,
        "test_receive_enabled": False,
        "shared_daily_limit": 10,
        "rolling_recipient_limit": 50,
        "send_recovery_resolution": {
            "held_task_id": "t1",
            "held_reason": "r",
            "evidence_type": "e",
        },
        "warmup_placement": "folder",
        "warmup_folder": "Warmup",
        "warmup_retention_days": 14,
        "relay_folder_moves": True,
    }
    assert acct.send_as_email == "alias@example.com"
    assert acct.mail_host == "google_workspace"
    assert acct.auth_method == "oauth"
    assert acct.avatar_url == "https://x/a.png"
    assert acct.test_mode == "diagnostic"
    assert acct.test_send_enabled is True and acct.test_receive_enabled is False
    assert acct.shared_daily_limit == 10 and acct.rolling_recipient_limit == 50
    assert acct.track_direct_mail is True
    assert acct.warmup_placement == "folder" and acct.warmup_folder == "Warmup"
    assert acct.warmup_retention_days == 14
    assert acct.relay_folder_moves is True


@pytest.mark.anyio
@respx.mock
async def test_async_update_new_fields(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1"})
    )
    await aclient.emails.update("em_1", warmup_retention_days=0, warmup_folder="")
    assert json.loads(route.calls.last.request.content) == {
        "warmup_folder": "",
        "warmup_retention_days": 0,
    }


# Built from dnsauth.Result.
AUTH = {
    "domain": "example.com",
    "spf_found": True,
    "spf_record": "v=spf1 include:_spf.google.com ~all",
    "dkim_found": False,
    "dkim_status": "undetermined",
    "dmarc_found": True,
    "dmarc_policy": "none",
    "dmarc_domain": "example.com",
    "dmarc_inherited": False,
    "reserved": False,
    "all_aligned": False,
    "lookup_error": False,
    "summary": "SPF and DMARC found",
}


@respx.mock
def test_auth_check_decodes_real_fields(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json=AUTH)
    )

    a = client.emails.auth_check("em_1")

    assert a.domain == "example.com"
    assert a.spf_found is True and a.spf_record.startswith("v=spf1")
    assert a.dkim_found is False and a.dkim_status == "undetermined"
    assert a.dkim_selectors == []
    assert a.dmarc_found is True and a.dmarc_policy == "none"
    assert a.dmarc_domain == "example.com" and a.dmarc_inherited is False
    assert a.summary == "SPF and DMARC found"


@respx.mock
def test_tracking_domain_txt_proof(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracking_domain": "t.example.com",
                "cname_target": "track.warmbly.com",
                "txt_name": "_warmbly.t.example.com",
                "txt_value": "warmbly-verify=abc",
                "status": "proof_missing",
            },
        )
    )

    t = client.emails.tracking_domain("em_1")

    assert t.txt_name == "_warmbly.t.example.com"
    assert t.txt_value == "warmbly-verify=abc"
    assert t.status == "proof_missing"
