"""Tests for the unibox additions: filing, thread drafts and new filters."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import (
    AsyncWarmbly,
    ConflictError,
    NotFoundError,
    Warmbly,
)

BASE_URL = "https://api.warmbly.com/v1"
TID = "<thread-1@mail.example>"
DRAFT_ID = "d4d4d4d4-0000-4000-8000-000000000001"
MSG_ID = "a1a1a1a1-0000-4000-8000-000000000002"


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


EMPTY_PAGE = {
    "data": [],
    "pagination": {"next_cursor": None, "has_more": False, "total": 0},
}

FILTERS: dict[str, Any] = {
    "tag_ids": ["t1", "t2"],
    "automated": False,
    "include_archived": True,
    "campaign_id": "c1",
    "contact_id": "k1",
}


@respx.mock
def test_list_new_filters_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=EMPTY_PAGE)
    )
    list(client.unibox.list(**FILTERS))
    params = _last(route).url.params
    assert params["tag_ids"] == "t1,t2"
    assert params["automated"] == "false"
    assert params["include_archived"] == "true"
    assert params["campaign_id"] == "c1"
    assert params["contact_id"] == "k1"

    list(client.unibox.list(automated=True))
    assert _last(route).url.params["automated"] == "true"
    list(client.unibox.list())
    params = _last(route).url.params
    for key in ("tag_ids", "automated", "include_archived", "campaign_id"):
        assert key not in params


@respx.mock
@pytest.mark.anyio
async def test_list_new_filters_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=EMPTY_PAGE)
    )
    assert [m async for m in aclient.unibox.list(**FILTERS)] == []
    params = _last(route).url.params
    assert params["tag_ids"] == "t1,t2"
    assert params["automated"] == "false"
    assert params["include_archived"] == "true"
    assert params["contact_id"] == "k1"


OVERVIEW: dict[str, Any] = {
    "total": 10,
    "unread": 3,
    "today": 1,
    "week": 4,
    "snoozed": 0,
    "awaiting_reply": 2,
    "automated": 5,
    "automated_unread": 2,
    "awaiting_agent_draft": 1,
    "drafts": 2,
    "scheduled_pending": 0,
    "scheduled_pending_max": 100,
    "folders": [{"folder": "inbox", "unread": 3, "total": 8}],
    "mailboxes": [],
    "tags": [],
    "categories": [],
    "generated_at": "2026-11-01T09:00:00Z",
    "window_today_start": "2026-11-01T00:00:00Z",
    "window_week_start": "2026-10-26T00:00:00Z",
}

DRAFT: dict[str, Any] = {
    "id": DRAFT_ID,
    "organization_id": "o1",
    "email_account_id": "e1",
    "owner_user_id": "u1",
    "thread_id": TID,
    "source_message_id": MSG_ID,
    "contact_id": None,
    "campaign_id": "c1",
    "to_addr": "lead@example.com",
    "subject": "Re: Hello",
    "in_reply_to": "<m1@mail.example>",
    "body": "Thanks, Tuesday works.",
    "intent_class": "meeting_request",
    "confidence": 0.82,
    "model": "my-agent",
    "status": "pending",
    "created_at": "2026-11-01T09:00:00Z",
    "updated_at": "2026-11-01T09:00:00Z",
}


def _check_draft(d: Any) -> None:
    assert d.owner_user_id == "u1"
    assert d.source_message_id == MSG_ID
    assert d.contact_id is None
    assert d.campaign_id == "c1"
    assert d.to_addr == "lead@example.com"
    assert d.in_reply_to == "<m1@mail.example>"
    assert d.intent_class == "meeting_request"
    assert d.confidence == 0.82
    assert d.model == "my-agent"
    assert d.status == "pending"


@respx.mock
def test_overview_and_agent_drafts_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    overview = client.unibox.overview()
    assert overview.automated == 5
    assert overview.automated_unread == 2
    assert overview.drafts == 2
    assert overview.awaiting_agent_draft == 1

    respx.get(f"{BASE_URL}/unibox/agent-drafts").mock(
        return_value=httpx.Response(200, json={"data": [DRAFT]})
    )
    _check_draft(next(iter(client.unibox.list_agent_drafts())))


@respx.mock
@pytest.mark.anyio
async def test_overview_and_agent_drafts_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    overview = await aclient.unibox.overview()
    assert overview.automated_unread == 2
    assert overview.drafts == 2

    respx.get(f"{BASE_URL}/unibox/agent-drafts").mock(
        return_value=httpx.Response(200, json={"data": [DRAFT]})
    )
    drafts = [d async for d in aclient.unibox.list_agent_drafts()]
    _check_draft(drafts[0])


@respx.mock
def test_move_folder_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": [MSG_ID], "thread_ids": [TID], "folder": "archive"}
        )
    )
    out = client.unibox.move_folder(
        folder="archive", email_ids=[MSG_ID], thread_ids=[TID]
    )
    assert _last(route).method == "PATCH"
    assert _body(route) == {
        "email_ids": [MSG_ID],
        "thread_ids": [TID],
        "folder": "archive",
    }
    assert out.folder == "archive"
    assert out.email_ids == [MSG_ID]
    assert out.thread_ids == [TID]

    client.unibox.move_folder(folder="trash", thread_ids=[TID])
    assert _body(route) == {"thread_ids": [TID], "folder": "trash"}


@respx.mock
@pytest.mark.anyio
async def test_move_folder_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": [MSG_ID], "folder": "inbox"}
        )
    )
    out = await aclient.unibox.move_folder(folder="inbox", email_ids=[MSG_ID])
    assert _body(route) == {"email_ids": [MSG_ID], "folder": "inbox"}
    assert out.thread_ids == []
    assert out.folder == "inbox"


@respx.mock
def test_upsert_thread_draft_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/unibox/ai-drafts/by-thread").mock(
        return_value=httpx.Response(
            200, json={"id": DRAFT_ID, "status": "pending", "created": True}
        )
    )
    out = client.unibox.upsert_thread_draft(
        thread_id=TID,
        body="Thanks, Tuesday works.",
        source="my-agent",
        intent_class="meeting_request",
        confidence=0.82,
    )
    assert _last(route).method == "PUT"
    assert _body(route) == {
        "thread_id": TID,
        "body": "Thanks, Tuesday works.",
        "source": "my-agent",
        "intent_class": "meeting_request",
        "confidence": 0.82,
    }
    assert out.id == DRAFT_ID
    assert out.status == "pending"
    assert out.created is True

    client.unibox.upsert_thread_draft(thread_id=TID, body="b", source="s")
    assert _body(route) == {"thread_id": TID, "body": "b", "source": "s"}

    respx.put(f"{BASE_URL}/unibox/ai-drafts/by-thread").mock(
        return_value=httpx.Response(
            409,
            json={
                "code": "already_sent",
                "message": "The newest inbound message on this thread already has "
                "an approved reply.",
            },
        )
    )
    with pytest.raises(ConflictError) as exc:
        client.unibox.upsert_thread_draft(thread_id=TID, body="b", source="s")
    assert exc.value.code == "already_sent"

    respx.put(f"{BASE_URL}/unibox/ai-drafts/by-thread").mock(
        return_value=httpx.Response(
            404, json={"code": "thread_not_found", "message": "No inbound message."}
        )
    )
    with pytest.raises(NotFoundError):
        client.unibox.upsert_thread_draft(thread_id=TID, body="b", source="s")


@respx.mock
@pytest.mark.anyio
async def test_upsert_thread_draft_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/unibox/ai-drafts/by-thread").mock(
        return_value=httpx.Response(
            200, json={"id": DRAFT_ID, "status": "pending", "created": False}
        )
    )
    out = await aclient.unibox.upsert_thread_draft(
        thread_id=TID, body="b", source="s", confidence=0.0
    )
    assert _body(route) == {
        "thread_id": TID,
        "body": "b",
        "source": "s",
        "confidence": 0.0,
    }
    assert out.created is False
    assert out.id == DRAFT_ID

    respx.put(f"{BASE_URL}/unibox/ai-drafts/by-thread").mock(
        return_value=httpx.Response(
            409, json={"code": "draft_discarded", "message": "Discarded."}
        )
    )
    with pytest.raises(ConflictError) as exc:
        await aclient.unibox.upsert_thread_draft(thread_id=TID, body="b", source="s")
    assert exc.value.code == "draft_discarded"
