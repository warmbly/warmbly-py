"""Tests for the templates, unibox, api_keys and email_images changes.

Each new or changed call is made on both the sync and the async client.
"""

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


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


def _page(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": None},
    }


# ---------------------------------------------------------------------------
# api_keys
# ---------------------------------------------------------------------------
KEY_ID = "77777777-7777-4777-8777-777777777777"


@respx.mock
def test_api_key_delete_permanently(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/{KEY_ID}/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    out = client.api_keys.delete_permanently(KEY_ID)
    assert _last(route).method == "DELETE"
    assert _last(route).url.path == f"/v1/api-keys/{KEY_ID}/permanent"
    assert out.status == "deleted"


@respx.mock
@pytest.mark.anyio
async def test_api_key_delete_permanently_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/{KEY_ID}/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    out = await aclient.api_keys.delete_permanently(KEY_ID)
    assert _last(route).url.path == f"/v1/api-keys/{KEY_ID}/permanent"
    assert out.status == "deleted"


PERMISSIONS = {
    "permissions": [
        {
            "name": "READ_EMAILS",
            "value": 1,
            "description": "View email accounts and settings",
            "category": "read",
        }
    ],
    "presets": {"read_only": 255, "full_access": 65535},
    "grantable": 4095,
    "app_scopes": 2047,
}


@respx.mock
def test_api_key_permissions_grantable(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(200, json=PERMISSIONS)
    )
    out = client.api_keys.permissions()
    assert out.grantable == 4095
    assert out.app_scopes == 2047
    assert out.permissions[0].name == "READ_EMAILS"
    assert out.presets["read_only"] == 255


@respx.mock
@pytest.mark.anyio
async def test_api_key_permissions_grantable_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(200, json=PERMISSIONS)
    )
    out = await aclient.api_keys.permissions()
    assert out.grantable == 4095
    assert out.app_scopes == 2047


# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------
ANALYSIS = {
    "score": 62,
    "verdict": "Likely to land in promotions.",
    "findings": [
        {
            "severity": "high",
            "field": "subject",
            "text": "FREE!!!",
            "line": 1,
            "excerpt": "FREE!!! offer",
            "issue": "Shouting reads as spam.",
            "suggestion": "Lowercase it.",
            "category": "tone",
        }
    ],
    "suggested_subject": "a quick question",
    "improvements": ["Add a clear ask."],
    "rules": {
        "score": 80,
        "issues": [
            {
                "severity": "warn",
                "code": "all_caps",
                "message": "ALL CAPS",
                "field": "subject",
                "spans": [{"field": "subject", "text": "FREE", "line": 1}],
            }
        ],
    },
    "judgment": {
        "reads_as": 0.7,
        "personalization": 0.4,
        "ask": "no_ask",
        "spam_claim": 0.1,
        "confidence": 0.9,
        "model": "judge-1",
        "input_tokens": 120,
    },
    "model": "m-1",
    "tokens_used": 900,
    "credits_remaining": 41,
    "credits_charged": 3,
}


def _check_analysis(out: Any) -> None:
    assert out.score == 62
    assert out.verdict == "Likely to land in promotions."
    assert out.findings[0].severity == "high"
    assert out.findings[0].field == "subject"
    assert out.findings[0].text == "FREE!!!"
    assert out.findings[0].suggestion == "Lowercase it."
    assert out.suggested_subject == "a quick question"
    assert out.improvements == ["Add a clear ask."]
    assert out.rules.score == 80
    assert out.rules.issues[0]["code"] == "all_caps"
    assert out.judgment.ask == "no_ask"
    assert out.judgment.reads_as == 0.7
    assert out.judgment.input_tokens == 120
    assert out.credits_remaining == 41
    assert out.credits_charged == 3
    assert out.tokens_used == 900


@respx.mock
def test_templates_analyze(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    out = client.templates.analyze(subject="FREE!!!", body_plain="hi")
    assert _last(route).method == "POST"
    assert _last(route).url.path == "/v1/templates/analyze"
    assert _body(route) == {"subject": "FREE!!!", "body_plain": "hi"}
    assert _last(route).headers.get("idempotency-key")
    _check_analysis(out)


@respx.mock
@pytest.mark.anyio
async def test_templates_analyze_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    out = await aclient.templates.analyze(body_html="<p>x</p>")
    assert _body(route) == {"body_html": "<p>x</p>"}
    _check_analysis(out)


@respx.mock
def test_templates_score_shape(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/templates/score").mock(
        return_value=httpx.Response(200, json=ANALYSIS["rules"])
    )
    out = client.templates.score(subject="FREE")
    assert out.score == 80
    assert out.issues[0]["spans"] == [{"field": "subject", "text": "FREE", "line": 1}]


# ---------------------------------------------------------------------------
# email_images
# ---------------------------------------------------------------------------
IMAGE_ID = "88888888-8888-4888-8888-888888888888"
IMAGE = {
    "id": IMAGE_ID,
    "organization_id": "99999999-9999-4999-8999-999999999999",
    "user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    "filename": "logo.png",
    "mime_type": "image/png",
    "size": 2048,
    "width": 200,
    "height": 80,
    "url": "https://cdn.example.com/email-images/o/x.png",
    "created_at": "2026-10-01T10:00:00Z",
}


def _check_image(img: Any) -> None:
    assert img.id == IMAGE_ID
    assert img.filename == "logo.png"
    assert img.mime_type == "image/png"
    assert img.size == 2048
    assert (img.width, img.height) == (200, 80)
    assert img.url == "https://cdn.example.com/email-images/o/x.png"


@respx.mock
def test_email_images_list_upload_delete(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(200, json=_page([IMAGE]))
    )
    images = list(client.email_images.list(limit=20))
    assert _last(listing).url.params["limit"] == "20"
    _check_image(images[0])

    upload = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    img = client.email_images.upload(
        file=b"\x89PNG-bytes", filename="logo.png", content_type="image/png"
    )
    request = _last(upload)
    assert request.method == "POST"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="logo.png"' in request.content
    assert b"Content-Type: image/png" in request.content
    assert b"\x89PNG-bytes" in request.content
    _check_image(img)

    delete = respx.delete(f"{BASE_URL}/email-images/{IMAGE_ID}").mock(
        return_value=httpx.Response(204)
    )
    out = client.email_images.delete(IMAGE_ID)
    assert _last(delete).method == "DELETE"
    assert out.deleted is None


@respx.mock
@pytest.mark.anyio
async def test_email_images_list_upload_delete_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(200, json=_page([IMAGE]))
    )
    images = [i async for i in aclient.email_images.list(limit=20)]
    assert _last(listing).url.params["limit"] == "20"
    _check_image(images[0])

    upload = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    img = await aclient.email_images.upload(file=b"bytes", filename="logo.png")
    assert b'name="file"; filename="logo.png"' in _last(upload).content
    _check_image(img)

    delete = respx.delete(f"{BASE_URL}/email-images/{IMAGE_ID}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.email_images.delete(IMAGE_ID)
    assert _last(delete).url.path == f"/v1/email-images/{IMAGE_ID}"


# ---------------------------------------------------------------------------
# unibox
# ---------------------------------------------------------------------------
MSG_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
MAILBOX_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


@respx.mock
def test_unibox_move_folder(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": [MSG_ID], "thread_ids": None, "folder": "archive"}
        )
    )
    out = client.unibox.move_folder(folder="archive", email_ids=[MSG_ID])
    assert _last(route).method == "PATCH"
    assert _last(route).url.path == "/v1/unibox/folder"
    assert _body(route) == {"folder": "archive", "email_ids": [MSG_ID]}
    assert out.folder == "archive"
    assert out.email_ids == [MSG_ID]
    assert out.thread_ids is None

    client.unibox.move_folder(folder="trash", thread_ids=["t1", "t2"])
    assert _body(route) == {"folder": "trash", "thread_ids": ["t1", "t2"]}


@respx.mock
@pytest.mark.anyio
async def test_unibox_move_folder_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/folder").mock(
        return_value=httpx.Response(
            200, json={"email_ids": None, "thread_ids": ["t1"], "folder": "inbox"}
        )
    )
    out = await aclient.unibox.move_folder(folder="inbox", thread_ids=["t1"])
    assert _body(route) == {"folder": "inbox", "thread_ids": ["t1"]}
    assert out.thread_ids == ["t1"]
    assert out.folder == "inbox"


@respx.mock
def test_unibox_mark_seen_threads(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(
            200, json={"email_ids": None, "thread_ids": ["t1"], "seen": False}
        )
    )
    out = client.unibox.mark_seen(thread_ids=["t1"], seen=False)
    assert _body(route) == {"thread_ids": ["t1"], "seen": False}
    assert out.thread_ids == ["t1"]
    assert out.seen is False


@respx.mock
@pytest.mark.anyio
async def test_unibox_mark_seen_threads_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(
            200, json={"email_ids": [MSG_ID], "thread_ids": ["t1"], "seen": True}
        )
    )
    out = await aclient.unibox.mark_seen(email_ids=[MSG_ID], thread_ids=["t1"])
    assert _body(route) == {
        "email_ids": [MSG_ID],
        "thread_ids": ["t1"],
        "seen": True,
    }
    assert out.email_ids == [MSG_ID]


@respx.mock
def test_unibox_list_new_filters(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": MSG_ID,
                        "email_id": MAILBOX_ID,
                        "thread_id": "t1",
                        "from_addr": ["a@b.com"],
                        "to_addr": ["me@acme.com"],
                        "subject": "Hi",
                        "snippet": "hello",
                        "internal_date": "2026-10-01T10:00:00Z",
                        "seen": False,
                        "message_count": 2,
                        "has_unread": True,
                        "labels": [],
                        "answers_mailbox_id": MAILBOX_ID,
                    }
                ],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    rows = list(
        client.unibox.list(
            automated=False, include_archived=True, snoozed="any", since="2026-10-01"
        )
    )
    params = _last(route).url.params
    assert params["automated"] == "false"
    assert params["include_archived"] == "true"
    assert params["snoozed"] == "any"
    assert params["since"] == "2026-10-01"
    assert rows[0].answers_mailbox_id == MAILBOX_ID

    list(client.unibox.list(automated=True))
    assert _last(route).url.params["automated"] == "true"
    assert "include_archived" not in _last(route).url.params


@respx.mock
@pytest.mark.anyio
async def test_unibox_list_new_filters_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([{"id": MSG_ID}]))
    )
    rows = [m async for m in aclient.unibox.list(automated=True, include_archived=True)]
    params = _last(route).url.params
    assert params["automated"] == "true"
    assert params["include_archived"] == "true"
    assert rows[0].id == MSG_ID


@respx.mock
def test_unibox_retrieve_and_overview_fields(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/unibox/{MSG_ID}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": MSG_ID,
                "email_id": MAILBOX_ID,
                "folder": "archive",
                "thread_id": "t1",
                "subject": "Hi",
            },
        )
    )
    msg = client.unibox.retrieve(MSG_ID)
    assert msg.email_id == MAILBOX_ID
    assert msg.folder == "archive"

    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(
            200, json={"unread": 4, "automated": 9, "automated_unread": 2}
        )
    )
    overview = client.unibox.overview()
    assert overview.automated == 9
    assert overview.automated_unread == 2


@respx.mock
def test_unibox_reply_forward(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_id": "task1",
                "scheduled_at": "2026-10-01T10:00:00Z",
                "send_mode": "instant",
            },
        )
    )
    out = client.unibox.reply(
        email_account_id=MAILBOX_ID,
        to=["boss@acme.com"],
        subject="Fwd: Hi",
        body_html="<p>FYI</p>",
        forward_message_id=MSG_ID,
    )
    assert _body(route) == {
        "email_account_id": MAILBOX_ID,
        "to": ["boss@acme.com"],
        "subject": "Fwd: Hi",
        "body_html": "<p>FYI</p>",
        "forward_message_id": MSG_ID,
    }
    assert out.task_id == "task1"

    client.unibox.reply(email_account_id=MAILBOX_ID, to=["a@b.com"], subject="Re")
    assert "forward_message_id" not in _body(route)


@respx.mock
@pytest.mark.anyio
async def test_unibox_reply_forward_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "task1"})
    )
    out = await aclient.unibox.reply(
        email_account_id=MAILBOX_ID,
        to=["boss@acme.com"],
        subject="Fwd: Hi",
        forward_message_id=MSG_ID,
    )
    assert _body(route)["forward_message_id"] == MSG_ID
    assert out.task_id == "task1"


@respx.mock
def test_unibox_snooze_one_and_many(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "s1",
                "user_id": "u1",
                "thread_id": "t1",
                "snoozed_until": "2026-10-05T10:00:00Z",
            },
        )
    )
    one = client.unibox.snooze(thread_id="t1", snoozed_until="2026-10-05T10:00:00Z")
    assert _body(route) == {"thread_id": "t1", "snoozed_until": "2026-10-05T10:00:00Z"}
    assert one.thread_id == "t1"
    assert one.data is None

    route.mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": "s1", "thread_id": "t1"},
                    {"id": "s2", "thread_id": "t2"},
                ]
            },
        )
    )
    many = client.unibox.snooze(
        thread_ids=["t1", "t2"], snoozed_until="2026-10-05T10:00:00Z"
    )
    assert _body(route) == {
        "thread_ids": ["t1", "t2"],
        "snoozed_until": "2026-10-05T10:00:00Z",
    }
    assert many.data is not None
    assert [s.thread_id for s in many.data] == ["t1", "t2"]


@respx.mock
@pytest.mark.anyio
async def test_unibox_snooze_many_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "s1", "thread_id": "t1"}]}
        )
    )
    many = await aclient.unibox.snooze(
        thread_id="t0", thread_ids=["t1"], snoozed_until="2026-10-05T10:00:00Z"
    )
    assert _body(route) == {
        "thread_id": "t0",
        "thread_ids": ["t1"],
        "snoozed_until": "2026-10-05T10:00:00Z",
    }
    assert many.data is not None
    assert many.data[0].id == "s1"


@respx.mock
def test_unibox_unsnooze_many(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    client.unibox.unsnooze(thread_id="t1")
    assert _last(route).url.params["thread_id"] == "t1"

    client.unibox.unsnooze(thread_ids=["t1", "t2"])
    assert _last(route).url.params["thread_id"] == "t1,t2"

    client.unibox.unsnooze(thread_id="t0", thread_ids=["t1"])
    assert _last(route).url.params["thread_id"] == "t0,t1"

    client.unibox.unsnooze()
    assert "thread_id" not in _last(route).url.params


@respx.mock
@pytest.mark.anyio
async def test_unibox_unsnooze_many_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    await aclient.unibox.unsnooze(thread_ids=["t1", "t2"])
    assert _last(route).url.params["thread_id"] == "t1,t2"


@respx.mock
def test_unibox_draft_body_html(client: Warmbly) -> None:
    save = respx.put(f"{BASE_URL}/unibox/drafts/d1").mock(
        return_value=httpx.Response(200, json={"id": "d1"})
    )
    out = client.unibox.save_draft("d1", body="plain", body_html="<p>plain</p>")
    assert _body(save) == {"body": "plain", "body_html": "<p>plain</p>"}
    assert out.id == "d1"

    respx.get(f"{BASE_URL}/unibox/drafts").mock(
        return_value=httpx.Response(
            200,
            json=_page([{"id": "d1", "body": "plain", "body_html": "<p>plain</p>"}]),
        )
    )
    drafts = list(client.unibox.list_drafts())
    assert drafts[0].body_html == "<p>plain</p>"


@respx.mock
@pytest.mark.anyio
async def test_unibox_draft_body_html_async(aclient: AsyncWarmbly) -> None:
    save = respx.put(f"{BASE_URL}/unibox/drafts/d1").mock(
        return_value=httpx.Response(200, json={"id": "d1"})
    )
    await aclient.unibox.save_draft("d1", body_html="<p>x</p>")
    assert _body(save) == {"body_html": "<p>x</p>"}
