"""Tests for the mailbox identity/sync/tracking routes and the unibox filing changes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"

IDENTITY = {
    "supported": True,
    "provider": "google",
    "mailbox_email": "sam@acme.io",
    "send_as_email": "hello@acme.io",
    "identities": [
        {
            "email": "sam@acme.io",
            "name": "Sam",
            "is_primary": True,
            "is_default": True,
            "verified": True,
        },
        {
            "email": "hello@acme.io",
            "name": "Acme",
            "is_primary": False,
            "is_default": False,
            "verified": True,
        },
    ],
    "synced_at": "2026-09-01T10:00:00Z",
    "signature_source": "provider",
    "signature_imported_at": "2026-09-01T10:00:00Z",
}

SYNC = {
    "state": {
        "backfill_status": "running",
        "backfill_synced": 12,
        "folders_skipped_cap": 3,
        "folders_skipped_conflict": 1,
        "deferred": 0,
    },
    "policy": {
        "backfill_days": 90,
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


def _body(route: respx.Route) -> dict:
    return json.loads(_last(route).content)


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def _check_identity(identity) -> None:
    assert identity.supported is True
    assert identity.mailbox_email == "sam@acme.io"
    assert identity.send_as_email == "hello@acme.io"
    assert [i.email for i in identity.identities] == ["sam@acme.io", "hello@acme.io"]
    assert identity.identities[0].is_primary is True
    assert identity.identities[1].verified is True
    assert identity.signature_source == "provider"
    assert identity.synced_at == "2026-09-01T10:00:00Z"


def _check_sync(sync) -> None:
    assert sync.state.folders_skipped_cap == 3
    assert sync.state.folders_skipped_conflict == 1
    assert list(sync.skip_folders) == ["Junk"]
    assert list(sync.policy.skip_folders) == ["Junk"]
    assert [(f.name, f.folder) for f in sync.folders] == [
        ("INBOX", "inbox"),
        ("Junk", "spam"),
    ]


ACCOUNT = {
    "id": "e1",
    "send_as_email": "hello@acme.io",
    "mail_host": "google_workspace",
    "auth_method": "oauth",
    "domain_grant_id": "g1",
    "vendor_connection_id": "v1",
    "vendor": "inboxkit",
    "avatar_url": "https://img/a.png",
    "track_direct_mail": True,
    "warmup_placement": "folder",
    "warmup_folder": "Warmup",
    "warmup_retention_days": 14,
    "relay_folder_moves": True,
}


# -- emails -----------------------------------------------------------------


@respx.mock
def test_emails_sync_routes(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/emails/e1/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )
    _check_sync(client.emails.sync("e1"))
    assert _last(get).method == "GET"

    put = respx.put(f"{BASE_URL}/emails/e1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": ["Junk", "Spam"]})
    )
    result = client.emails.update_sync("e1", skip_folders=["Junk", "Spam"])
    assert list(result.skip_folders) == ["Junk", "Spam"]
    assert _last(put).method == "PUT"
    assert _body(put) == {"skip_folders": ["Junk", "Spam"]}


@respx.mock
def test_emails_direct_tracking_and_identity(client: Warmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/emails/e1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": True})
    )
    assert client.emails.update_direct_tracking("e1", enabled=True).track_direct_mail
    assert _last(patch).method == "PATCH"
    assert _body(patch) == {"enabled": True}

    get = respx.get(f"{BASE_URL}/emails/e1/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(client.emails.identity("e1"))
    assert _last(get).method == "GET"

    refresh = respx.post(f"{BASE_URL}/emails/e1/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(client.emails.refresh_identity("e1"))
    assert _body(refresh) == {}
    _check_identity(client.emails.refresh_identity("e1", import_signature=True))
    assert _body(refresh) == {"import_signature": True}


@respx.mock
def test_emails_update_new_fields_and_account_shape(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/e1").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    account = client.emails.update(
        "e1",
        send_as_email="hello@acme.io",
        relay_folder_moves=True,
        warmup_placement="folder",
        warmup_folder="Warmup",
        warmup_retention_days=14,
    )
    assert _body(route) == {
        "send_as_email": "hello@acme.io",
        "relay_folder_moves": True,
        "warmup_placement": "folder",
        "warmup_folder": "Warmup",
        "warmup_retention_days": 14,
    }
    assert account.send_as_email == "hello@acme.io"
    assert account.mail_host == "google_workspace"
    assert account.auth_method == "oauth"
    assert account.domain_grant_id == "g1"
    assert account.vendor_connection_id == "v1"
    assert account.vendor == "inboxkit"
    assert account.avatar_url == "https://img/a.png"
    assert account.track_direct_mail is True
    assert account.warmup_placement == "folder"
    assert account.warmup_folder == "Warmup"
    assert account.warmup_retention_days == 14
    assert account.relay_folder_moves is True


@respx.mock
@pytest.mark.anyio
async def test_emails_async(aclient: AsyncWarmbly) -> None:
    get = respx.get(f"{BASE_URL}/emails/e1/sync").mock(
        return_value=httpx.Response(200, json=SYNC)
    )
    _check_sync(await aclient.emails.sync("e1"))
    assert _last(get).method == "GET"

    put = respx.put(f"{BASE_URL}/emails/e1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": []})
    )
    result = await aclient.emails.update_sync("e1", skip_folders=[])
    assert list(result.skip_folders) == []
    assert _body(put) == {"skip_folders": []}

    patch = respx.patch(f"{BASE_URL}/emails/e1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": False})
    )
    tracking = await aclient.emails.update_direct_tracking("e1", enabled=False)
    assert tracking.track_direct_mail is False
    assert _body(patch) == {"enabled": False}

    respx.get(f"{BASE_URL}/emails/e1/identity").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(await aclient.emails.identity("e1"))

    refresh = respx.post(f"{BASE_URL}/emails/e1/identity/refresh").mock(
        return_value=httpx.Response(200, json=IDENTITY)
    )
    _check_identity(await aclient.emails.refresh_identity("e1", import_signature=True))
    assert _body(refresh) == {"import_signature": True}

    upd = respx.patch(f"{BASE_URL}/emails/e1").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    account = await aclient.emails.update(
        "e1",
        send_as_email="",
        relay_folder_moves=False,
        warmup_placement="inbox",
        warmup_folder="",
        warmup_retention_days=0,
    )
    assert _body(upd) == {
        "send_as_email": "",
        "relay_folder_moves": False,
        "warmup_placement": "inbox",
        "warmup_folder": "",
        "warmup_retention_days": 0,
    }
    assert account.track_direct_mail is True


# -- api keys ---------------------------------------------------------------


@respx.mock
def test_api_keys_delete_permanently(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/k1/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    assert client.api_keys.delete_permanently("k1").status == "deleted"
    assert _last(route).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_api_keys_delete_permanently_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/k1/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    assert (await aclient.api_keys.delete_permanently("k1")).status == "deleted"
    assert _last(route).url.path == "/v1/api-keys/k1/permanent"


# -- unibox -----------------------------------------------------------------

PREVIEW = {
    "id": "m1",
    "email_id": "e1",
    "thread_id": "t1",
    "answers_mailbox_id": "e2",
}
MESSAGE = {"id": "m1", "email_id": "e1", "folder": "archive"}
OVERVIEW = {"total": 10, "automated": 4, "automated_unread": 2}


@respx.mock
def test_unibox_reads(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([PREVIEW]))
    )
    rows = list(client.unibox.list(include_archived=True, automated=False))
    assert rows[0].answers_mailbox_id == "e2"
    params = _last(listing).url.params
    assert params.get("include_archived") == "true"
    assert params.get("automated") == "false"

    list(client.unibox.list(automated=True))
    assert _last(listing).url.params.get("automated") == "true"
    assert "include_archived" not in _last(listing).url.params
    list(client.unibox.list())
    assert "automated" not in _last(listing).url.params

    respx.get(f"{BASE_URL}/unibox/m1").mock(
        return_value=httpx.Response(200, json=MESSAGE)
    )
    message = client.unibox.retrieve("m1")
    assert (message.email_id, message.folder) == ("e1", "archive")

    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    overview = client.unibox.overview()
    assert (overview.automated, overview.automated_unread) == (4, 2)


@respx.mock
def test_unibox_writes(client: Warmbly) -> None:
    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(
            200, json={"email_ids": None, "thread_ids": ["t1"], "seen": True}
        )
    )
    result = client.unibox.mark_seen(thread_ids=["t1"])
    assert _body(seen) == {"thread_ids": ["t1"], "seen": True}
    assert list(result.thread_ids or []) == ["t1"]

    move = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": ["m1"], "thread_ids": ["t1"], "folder": "trash"}
        )
    )
    moved = client.unibox.move_folder(
        folder="trash", email_ids=["m1"], thread_ids=["t1"]
    )
    assert _last(move).method == "PATCH"
    assert _body(move) == {"email_ids": ["m1"], "thread_ids": ["t1"], "folder": "trash"}
    assert (list(moved.email_ids or []), moved.folder) == (["m1"], "trash")
    client.unibox.move_folder(folder="inbox", email_ids=["m1"])
    assert _body(move) == {"email_ids": ["m1"], "folder": "inbox"}

    reply = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "tk1"})
    )
    sent = client.unibox.reply(
        email_account_id="e1",
        to=["a@b.co"],
        subject="Fwd: hi",
        forward_message_id="m1",
    )
    assert sent.task_id == "tk1"
    assert _body(reply)["forward_message_id"] == "m1"


@respx.mock
def test_unibox_snooze_variants(client: Warmbly) -> None:
    snooze = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(
            200, json={"data": [{"thread_id": "t1"}, {"thread_id": "t2"}]}
        )
    )
    result = client.unibox.snooze(
        thread_ids=["t1", "t2"], snoozed_until="2026-10-05T09:00:00Z"
    )
    assert [s.thread_id for s in result.data or []] == ["t1", "t2"]
    assert _body(snooze) == {
        "thread_ids": ["t1", "t2"],
        "snoozed_until": "2026-10-05T09:00:00Z",
    }
    with pytest.raises(ValueError):
        client.unibox.snooze(snoozed_until="2026-10-05T09:00:00Z")

    snooze.mock(return_value=httpx.Response(200, json={"thread_id": "t1"}))
    single = client.unibox.snooze(thread_id="t1", snoozed_until="2026-10-05T09:00:00Z")
    assert single.thread_id == "t1"
    assert _body(snooze)["thread_id"] == "t1"

    wake = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    client.unibox.unsnooze(thread_id="t1")
    assert _last(wake).url.params.get("thread_id") == "t1"
    client.unibox.unsnooze(thread_ids=["t1", "t2"])
    assert _last(wake).url.params.get("thread_id") == "t1,t2"
    with pytest.raises(ValueError):
        client.unibox.unsnooze()


@respx.mock
@pytest.mark.anyio
async def test_unibox_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([PREVIEW]))
    )
    rows = [m async for m in aclient.unibox.list(include_archived=True, automated=True)]
    assert rows[0].answers_mailbox_id == "e2"
    assert _last(listing).url.params.get("automated") == "true"
    assert _last(listing).url.params.get("include_archived") == "true"

    respx.get(f"{BASE_URL}/unibox/m1").mock(
        return_value=httpx.Response(200, json=MESSAGE)
    )
    assert (await aclient.unibox.retrieve("m1")).folder == "archive"
    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    assert (await aclient.unibox.overview()).automated == 4

    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"thread_ids": ["t1"], "seen": False})
    )
    await aclient.unibox.mark_seen(thread_ids=["t1"], seen=False)
    assert _body(seen) == {"thread_ids": ["t1"], "seen": False}

    move = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"thread_ids": ["t1"], "folder": "archive"}
        )
    )
    moved = await aclient.unibox.move_folder(folder="archive", thread_ids=["t1"])
    assert moved.folder == "archive"
    assert _body(move) == {"thread_ids": ["t1"], "folder": "archive"}
    await aclient.unibox.move_folder(folder="inbox", email_ids=["m1"])
    assert _body(move) == {"email_ids": ["m1"], "folder": "inbox"}

    reply = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "tk1"})
    )
    await aclient.unibox.reply(
        email_account_id="e1", to=["a@b.co"], subject="Fwd", forward_message_id="m1"
    )
    assert _body(reply)["forward_message_id"] == "m1"

    snooze = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json={"data": [{"thread_id": "t1"}]})
    )
    result = await aclient.unibox.snooze(
        thread_ids=["t1"], snoozed_until="2026-10-05T09:00:00Z"
    )
    assert [s.thread_id for s in result.data or []] == ["t1"]
    assert _body(snooze)["thread_ids"] == ["t1"]
    with pytest.raises(ValueError):
        await aclient.unibox.snooze(snoozed_until="2026-10-05T09:00:00Z")

    wake = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    await aclient.unibox.unsnooze(thread_id="t1")
    assert _last(wake).url.params.get("thread_id") == "t1"
    await aclient.unibox.unsnooze(thread_ids=["t1", "t2"])
    assert _last(wake).url.params.get("thread_id") == "t1,t2"
    with pytest.raises(ValueError):
        await aclient.unibox.unsnooze()
