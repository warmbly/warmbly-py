"""Tests for the mailbox routes added to ``emails`` (identity, sync, bulk, ...)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
EID = "7c1d2e3f-0000-4000-8000-00000000aaaa"
EID2 = "7c1d2e3f-0000-4000-8000-00000000bbbb"


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


ACCOUNT: dict[str, Any] = {
    "id": EID,
    "user_id": "u1",
    "organization_id": "o1",
    "worker_id": None,
    "email": "sam@acme.example",
    "name": "Sam",
    "signature_plain": "",
    "signature_html": "",
    "signature_sync": False,
    "signature_code": False,
    "send_as_email": "sales@acme.example",
    "provider": "gmail",
    "status": "active",
    "mail_host": "google_workspace",
    "auth_method": "oauth",
    "domain_grant_id": "g1",
    "vendor_connection_id": "v1",
    "vendor": "inboxkit",
    "avatar_url": "https://img.example/a.png",
    "last_synced_at": "2026-11-01T09:00:00Z",
    "last_id": 42,
    "campaign_limit": 40,
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 100,
    "rolling_recipient_limit": None,
    "min_wait_time": 5,
    "reply_to": "",
    "tracking_domain": "",
    "tracking_domain_verified": False,
    "tracking_domain_verified_at": None,
    "track_direct_mail": True,
    "auth_state": "passing",
    "warmup": "2026-10-01T00:00:00Z",
    "warmup_placement": "folder",
    "warmup_folder": "Warmup",
    "warmup_retention_days": 14,
    "timezone": "Europe/Berlin",
    "save_to_sent": True,
    "relay_folder_moves": True,
    "tags": ["t1"],
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-11-01T00:00:00Z",
}


def _check_account(acct: Any) -> None:
    assert acct.send_as_email == "sales@acme.example"
    assert acct.mail_host == "google_workspace"
    assert acct.auth_method == "oauth"
    assert acct.domain_grant_id == "g1"
    assert acct.vendor_connection_id == "v1"
    assert acct.vendor == "inboxkit"
    assert acct.avatar_url == "https://img.example/a.png"
    assert acct.last_id == 42
    assert acct.test_mode == "diagnostic"
    assert acct.test_send_enabled is True
    assert acct.test_receive_enabled is False
    assert acct.shared_daily_limit == 100
    assert acct.rolling_recipient_limit is None
    assert acct.track_direct_mail is True
    assert acct.warmup_placement == "folder"
    assert acct.warmup_folder == "Warmup"
    assert acct.warmup_retention_days == 14
    assert acct.relay_folder_moves is True


UPDATE_KWARGS: dict[str, Any] = {
    "send_as_email": "sales@acme.example",
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 100,
    "rolling_recipient_limit": 50,
    "send_recovery_resolution": {
        "held_task_id": "t1",
        "held_reason": "unknown",
        "evidence_type": "provider_confirmation",
    },
    "warmup_placement": "folder",
    "warmup_folder": "Warmup",
    "warmup_retention_days": 14,
    "relay_folder_moves": True,
}

SYNC: dict[str, Any] = {
    "state": {
        "backfill_status": "running",
        "backfill_synced": 120,
        "throttled_until": "2026-11-01T12:00:00Z",
        "throttle_reason": "daily",
        "deferred": 3,
        "folders_skipped_cap": 1,
        "folders_skipped_conflict": 2,
        "folder_coverage_observed_at": "2026-11-01T11:00:00Z",
        "last_synced_at": "2026-11-01T11:00:00Z",
    },
    "policy": {
        "backfill_days": 30,
        "backfill_messages": 5000,
        "daily_messages": 2000,
        "org_daily_messages": 20000,
        "skip_folders": ["Promotions"],
    },
    "skip_folders": ["Promotions"],
    "folders": [
        {"name": "INBOX", "folder": "inbox"},
        {"name": "Promotions", "folder": ""},
    ],
}

CERTS: dict[str, Any] = {
    "smtp": {
        "host": "smtp.acme.example",
        "port": 465,
        "tls_unverified": True,
        "tls_pin": "ab" * 32,
        "observed": {
            "fingerprint": "ab" * 32,
            "subject": "CN=smtp.acme.example",
            "issuer": "CN=smtp.acme.example",
            "not_after": "2027-01-01T00:00:00Z",
            "self_signed": True,
            "trusted": False,
        },
    },
    "imap": {
        "host": "imap.acme.example",
        "port": 993,
        "tls_unverified": False,
    },
}

IDENTITY: dict[str, Any] = {
    "supported": True,
    "provider": "gmail",
    "mailbox_email": "sam@acme.example",
    "send_as_email": "sales@acme.example",
    "identities": [
        {
            "email": "sam@acme.example",
            "name": "Sam",
            "is_primary": True,
            "is_default": True,
            "verified": True,
        },
        {
            "email": "sales@acme.example",
            "name": "Sales",
            "is_primary": False,
            "is_default": False,
            "verified": True,
        },
    ],
    "synced_at": "2026-11-01T09:00:00Z",
    "signature_source": "provider",
    "signature_imported_at": "2026-11-01T09:00:00Z",
}

BULK: dict[str, Any] = {
    "succeeded": 1,
    "failed": 1,
    "results": [
        {"id": EID, "ok": True},
        {"id": EID2, "ok": False, "code": "not_found", "message": "No such mailbox."},
    ],
}


def _check_bulk(out: Any) -> None:
    assert out.succeeded == 1
    assert out.failed == 1
    assert out.results[0].ok is True
    assert out.results[0].code is None
    assert out.results[1].id == EID2
    assert out.results[1].code == "not_found"
    assert out.results[1].message == "No such mailbox."


def _check_identity(out: Any) -> None:
    assert out.supported is True
    assert out.provider == "gmail"
    assert out.mailbox_email == "sam@acme.example"
    assert out.send_as_email == "sales@acme.example"
    assert out.identities[0].is_primary is True
    assert out.identities[1].name == "Sales"
    assert out.identities[1].verified is True
    assert out.synced_at == "2026-11-01T09:00:00Z"
    assert out.signature_source == "provider"
    assert out.signature_imported_at == "2026-11-01T09:00:00Z"


def _check_sync(out: Any) -> None:
    assert out.state is not None
    assert out.state.folders_skipped_cap == 1
    assert out.state.folders_skipped_conflict == 2
    assert out.state.folder_coverage_observed_at == "2026-11-01T11:00:00Z"
    assert out.policy is not None
    assert out.policy.skip_folders == ["Promotions"]
    assert out.skip_folders == ["Promotions"]
    assert out.folders[0].name == "INBOX"
    assert out.folders[0].folder == "inbox"


def _check_certs(out: Any) -> None:
    assert out.smtp is not None
    assert out.smtp.tls_unverified is True
    assert out.smtp.tls_pin == "ab" * 32
    assert out.smtp.observed is not None
    assert out.smtp.observed.self_signed is True
    assert out.smtp.observed.not_after == "2027-01-01T00:00:00Z"
    assert out.imap is not None
    assert out.imap.port == 993
    assert out.imap.observed is None


@respx.mock
def test_update_new_fields_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/{EID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    out = client.emails.update(EID, **UPDATE_KWARGS)
    assert _body(route) == UPDATE_KWARGS
    _check_account(out)


@respx.mock
@pytest.mark.anyio
async def test_update_new_fields_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/{EID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    out = await aclient.emails.update(EID, **UPDATE_KWARGS)
    assert _body(route) == UPDATE_KWARGS
    _check_account(out)


@respx.mock
def test_tracking_domain_proof_fields(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EID}/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracking_domain": "t.acme.example",
                "tracking_domain_verified": False,
                "tracking_domain_verified_at": None,
                "cname_target": "track.warmbly.example",
                "txt_name": "_warmbly.t.acme.example",
                "txt_value": "proof123",
                "status": "proof_missing",
                "message": "Add the TXT record.",
                "tracking_host_unresolvable": False,
            },
        )
    )
    out = client.emails.tracking_domain(EID)
    assert out.txt_name == "_warmbly.t.acme.example"
    assert out.txt_value == "proof123"
    assert out.status == "proof_missing"


@respx.mock
def test_sync_and_certificates_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EID}/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )
    _check_sync(client.emails.sync(EID))

    put = respx.put(f"{BASE_URL}/emails/{EID}/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": ["Promotions"]})
    )
    out = client.emails.update_sync(EID, skip_folders=["Promotions"])
    assert _last(put).method == "PUT"
    assert _body(put) == {"skip_folders": ["Promotions"]}
    assert out.skip_folders == ["Promotions"]
    client.emails.update_sync(EID, skip_folders=[])
    assert _body(put) == {"skip_folders": []}

    certs = respx.get(f"{BASE_URL}/emails/{EID}/certificates").mock(
        return_value=httpx.Response(200, json=CERTS)
    )
    _check_certs(client.emails.certificates(EID))
    assert _last(certs).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_sync_and_certificates_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EID}/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )
    _check_sync(await aclient.emails.sync(EID))

    put = respx.put(f"{BASE_URL}/emails/{EID}/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": ["A", "B"]})
    )
    out = await aclient.emails.update_sync(EID, skip_folders=("A", "B"))
    assert _body(put) == {"skip_folders": ["A", "B"]}
    assert out.skip_folders == ["A", "B"]

    respx.get(f"{BASE_URL}/emails/{EID}/certificates").mock(
        return_value=httpx.Response(200, json=CERTS)
    )
    _check_certs(await aclient.emails.certificates(EID))


@respx.mock
def test_identity_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EID}/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(client.emails.identity(EID))

    refresh = respx.post(f"{BASE_URL}/emails/{EID}/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(client.emails.refresh_identity(EID, import_signature=True))
    assert _body(refresh) == {"import_signature": True}
    client.emails.refresh_identity(EID)
    assert _body(refresh) == {}


@respx.mock
@pytest.mark.anyio
async def test_identity_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EID}/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(await aclient.emails.identity(EID))

    refresh = respx.post(f"{BASE_URL}/emails/{EID}/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(await aclient.emails.refresh_identity(EID, import_signature=False))
    assert _body(refresh) == {"import_signature": False}


@respx.mock
def test_resume_and_direct_tracking_sync(client: Warmbly) -> None:
    resume = respx.post(f"{BASE_URL}/emails/{EID}/resume-sending").mock(
        return_value=httpx.Response(
            200, json={"hold_released": True, "cooldown_cleared": False}
        )
    )
    out = client.emails.resume_sending(EID)
    assert _last(resume).method == "POST"
    assert out.hold_released is True
    assert out.cooldown_cleared is False

    direct = respx.patch(f"{BASE_URL}/emails/{EID}/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": True})
    )
    tracking = client.emails.update_direct_tracking(EID, enabled=True)
    assert _body(direct) == {"enabled": True}
    assert tracking.track_direct_mail is True


@respx.mock
@pytest.mark.anyio
async def test_resume_and_direct_tracking_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/emails/{EID}/resume-sending").mock(
        return_value=httpx.Response(
            200, json={"hold_released": False, "cooldown_cleared": True}
        )
    )
    out = await aclient.emails.resume_sending(EID)
    assert out.cooldown_cleared is True
    assert out.hold_released is False

    direct = respx.patch(f"{BASE_URL}/emails/{EID}/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": False})
    )
    tracking = await aclient.emails.update_direct_tracking(EID, enabled=False)
    assert _body(direct) == {"enabled": False}
    assert tracking.track_direct_mail is False


def test_send_pause_info_model() -> None:
    from warmbly.resources.emails import SendPauseInfo

    pause = SendPauseInfo.model_validate(
        {
            "reason": "rate_limited",
            "held": False,
            "until": "2026-11-01T12:00:00Z",
            "provider_message": "421 try later",
            "resumable": True,
        }
    )
    assert pause.reason == "rate_limited"
    assert pause.held is False
    assert pause.until == "2026-11-01T12:00:00Z"
    assert pause.retry_at is None
    assert pause.resumable is True


@respx.mock
def test_bulk_sync(client: Warmbly) -> None:
    delete = respx.post(f"{BASE_URL}/emails/bulk/delete").mock(
        return_value=httpx.Response(200, json=BULK)
    )
    _check_bulk(client.emails.bulk_delete(email_ids=[EID, EID2]))
    assert _body(delete) == {"email_ids": [EID, EID2]}
    assert _last(delete).headers["Idempotency-Key"]

    status = respx.post(f"{BASE_URL}/emails/bulk/status").mock(
        return_value=httpx.Response(200, json=BULK)
    )
    _check_bulk(client.emails.bulk_status(email_ids=[EID], status="inactive"))
    assert _body(status) == {"email_ids": [EID], "status": "inactive"}

    warmup = respx.post(f"{BASE_URL}/emails/bulk/warmup").mock(
        return_value=httpx.Response(200, json=BULK)
    )
    _check_bulk(client.emails.bulk_warmup(email_ids=[EID], action="pause"))
    assert _body(warmup) == {"email_ids": [EID], "action": "pause"}


@respx.mock
@pytest.mark.anyio
async def test_bulk_async(aclient: AsyncWarmbly) -> None:
    delete = respx.post(f"{BASE_URL}/emails/bulk/delete").mock(
        return_value=httpx.Response(200, json=BULK)
    )
    _check_bulk(await aclient.emails.bulk_delete(email_ids=[EID]))
    assert _body(delete) == {"email_ids": [EID]}

    status = respx.post(f"{BASE_URL}/emails/bulk/status").mock(
        return_value=httpx.Response(200, json=BULK)
    )
    _check_bulk(await aclient.emails.bulk_status(email_ids=[EID], status="active"))
    assert _body(status) == {"email_ids": [EID], "status": "active"}

    warmup = respx.post(f"{BASE_URL}/emails/bulk/warmup").mock(
        return_value=httpx.Response(200, json=BULK)
    )
    _check_bulk(await aclient.emails.bulk_warmup(email_ids=[EID], action="start"))
    assert _body(warmup) == {"email_ids": [EID], "action": "start"}
