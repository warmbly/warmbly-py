"""Tests for the unibox changes of the 2026-10 server sync, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

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


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _page(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {"data": data, "pagination": {"next_cursor": None, "has_more": False}}


PREVIEW = {
    "id": "m_1",
    "email_id": "em_1",
    "answers_mailbox_id": "em_2",
    "thread_id": "th_1",
    "from_addr": ["a@x.test"],
    "to_addr": ["b@y.test"],
    "subject": "Hi",
    "snippet": "hello",
    "internal_date": "2026-10-25T08:00:00Z",
    "seen": False,
    "message_count": 2,
    "has_unread": True,
    "labels": [],
}

OVERVIEW = {
    "total": 10,
    "unread": 3,
    "today": 2,
    "week": 5,
    "snoozed": 1,
    "awaiting_reply": 2,
    "automated": 4,
    "automated_unread": 1,
    "awaiting_agent_draft": 0,
    "scheduled_pending": 1,
    "scheduled_pending_max": 50,
    "folders": [{"folder": "inbox", "unread": 3, "total": 10}],
}

MESSAGE = {
    "id": "m_1",
    "email_id": "em_1",
    "folder": "archive",
    "thread_id": "th_1",
    "subject": "Hi",
}


@respx.mock
def test_reads_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([PREVIEW]))
    )
    rows = list(client.unibox.list(automated=True, include_archived=True))
    params = _last(listing).url.params
    assert params.get("automated") == "true"
    assert params.get("include_archived") == "true"
    assert rows[0].answers_mailbox_id == "em_2"
    assert rows[0].email_id == "em_1"

    list(client.unibox.list(automated=False, include_archived=False))
    params = _last(listing).url.params
    assert params.get("automated") == "false"
    assert "include_archived" not in params

    list(client.unibox.list())
    assert "automated" not in _last(listing).url.params

    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    overview = client.unibox.overview()
    assert overview.automated == 4
    assert overview.automated_unread == 1

    respx.get(f"{BASE_URL}/unibox/m_1").mock(
        return_value=httpx.Response(200, json=MESSAGE)
    )
    message = client.unibox.retrieve("m_1")
    assert message.email_id == "em_1"
    assert message.folder == "archive"


@pytest.mark.anyio
@respx.mock
async def test_reads_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([PREVIEW]))
    )
    rows = [m async for m in aclient.unibox.list(automated=False)]
    assert _last(listing).url.params.get("automated") == "false"
    assert rows[0].answers_mailbox_id == "em_2"
    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    assert (await aclient.unibox.overview()).automated == 4
    respx.get(f"{BASE_URL}/unibox/m_1").mock(
        return_value=httpx.Response(200, json=MESSAGE)
    )
    assert (await aclient.unibox.retrieve("m_1")).folder == "archive"


@respx.mock
def test_mark_seen_threads_and_move_folder_sync(client: Warmbly) -> None:
    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(
            200,
            json={
                "email_ids": ["m_1"],
                "thread_ids": ["th_1"],
                "folder": "",
                "seen": True,
            },
        )
    )
    result = client.unibox.mark_seen(email_ids=["m_1"], thread_ids=["th_1"])
    assert json.loads(_last(seen).content) == {
        "email_ids": ["m_1"],
        "thread_ids": ["th_1"],
        "seen": True,
    }
    assert list(result.thread_ids) == ["th_1"]
    client.unibox.mark_seen(folder="inbox")
    assert json.loads(_last(seen).content) == {"folder": "inbox", "seen": True}

    move = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200,
            json={"email_ids": ["m_1"], "thread_ids": ["th_1"], "folder": "archive"},
        )
    )
    moved = client.unibox.move_folder(
        folder="archive", email_ids=["m_1"], thread_ids=["th_1"]
    )
    assert _last(move).method == "PATCH"
    assert json.loads(_last(move).content) == {
        "folder": "archive",
        "email_ids": ["m_1"],
        "thread_ids": ["th_1"],
    }
    assert moved.folder == "archive"
    assert list(moved.email_ids) == ["m_1"]
    assert list(moved.thread_ids) == ["th_1"]
    client.unibox.move_folder(folder="trash", thread_ids=["th_2"])
    assert json.loads(_last(move).content) == {
        "folder": "trash",
        "thread_ids": ["th_2"],
    }


@pytest.mark.anyio
@respx.mock
async def test_mark_seen_threads_and_move_folder_async(aclient: AsyncWarmbly) -> None:
    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"thread_ids": ["th_1"], "seen": False})
    )
    result = await aclient.unibox.mark_seen(thread_ids=["th_1"], seen=False)
    assert json.loads(_last(seen).content) == {"thread_ids": ["th_1"], "seen": False}
    assert list(result.thread_ids) == ["th_1"]
    move = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(200, json={"email_ids": ["m_1"], "folder": "inbox"})
    )
    moved = await aclient.unibox.move_folder(folder="inbox", email_ids=["m_1"])
    assert json.loads(_last(move).content) == {
        "folder": "inbox",
        "email_ids": ["m_1"],
    }
    assert moved.folder == "inbox"
    await aclient.unibox.move_folder(folder="archive", thread_ids=["t"])
    assert json.loads(_last(move).content) == {"folder": "archive", "thread_ids": ["t"]}


@respx.mock
def test_forward_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(
            200, json={"task_id": "t_1", "scheduled_at": "x", "send_mode": "instant"}
        )
    )
    sent = client.unibox.reply(
        email_account_id="em_1",
        to=["c@z.test"],
        subject="Fwd: Hi",
        body_plain="fyi",
        forward_message_id="m_1",
    )
    request = _last(route)
    assert json.loads(request.content) == {
        "email_account_id": "em_1",
        "to": ["c@z.test"],
        "subject": "Fwd: Hi",
        "body_plain": "fyi",
        "forward_message_id": "m_1",
    }
    assert request.headers.get("idempotency-key")
    assert sent.task_id == "t_1"


@pytest.mark.anyio
@respx.mock
async def test_forward_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "t_2"})
    )
    sent = await aclient.unibox.reply(
        email_account_id="em_1",
        to=["c@z.test"],
        subject="Fwd: Hi",
        forward_message_id="m_9",
    )
    assert json.loads(_last(route).content)["forward_message_id"] == "m_9"
    assert sent.task_id == "t_2"


ROW_1 = {"id": "sn_1", "thread_id": "th_1", "snoozed_until": "2026-11-01T00:00:00Z"}
ROW_2 = {"id": "sn_2", "thread_id": "th_2", "snoozed_until": "2026-11-01T00:00:00Z"}


@respx.mock
def test_snooze_many_sync(client: Warmbly) -> None:
    snooze = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json={"data": [ROW_1, ROW_2]})
    )
    many = client.unibox.snooze_many(
        thread_ids=["th_1", "th_2"], snoozed_until="2026-11-01T00:00:00Z"
    )
    assert json.loads(_last(snooze).content) == {
        "thread_ids": ["th_1", "th_2"],
        "snoozed_until": "2026-11-01T00:00:00Z",
    }
    assert [s.thread_id for s in many.data] == ["th_1", "th_2"]
    assert many.data[1].snoozed_until == "2026-11-01T00:00:00Z"

    # One thread comes back as a bare row; it still lands in ``data``.
    respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json=ROW_1)
    )
    single = client.unibox.snooze_many(
        thread_ids=["th_1"], snoozed_until="2026-11-01T00:00:00Z"
    )
    assert [s.id for s in single.data] == ["sn_1"]

    gone = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    client.unibox.unsnooze_many(thread_ids=["th_1", "th_2"])
    assert _last(gone).url.params.get("thread_id") == "th_1,th_2"


@pytest.mark.anyio
@respx.mock
async def test_snooze_many_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json={"data": [ROW_1, ROW_2]})
    )
    many = await aclient.unibox.snooze_many(thread_ids=["a", "b"], snoozed_until="t")
    assert [s.id for s in many.data] == ["sn_1", "sn_2"]
    respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json=ROW_2)
    )
    single = await aclient.unibox.snooze_many(thread_ids=["b"], snoozed_until="t")
    assert single.data[0].thread_id == "th_2"
    gone = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    await aclient.unibox.unsnooze_many(thread_ids=["a", "b"])
    assert _last(gone).url.params.get("thread_id") == "a,b"
