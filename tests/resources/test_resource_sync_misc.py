"""CRM bulk tasks, template analysis, the email image library, connection
signing keys, and field changes on forms, segments, lead sync and campaigns.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture(params=["sync", "async"])
async def api(request: pytest.FixtureRequest) -> AsyncIterator[Any]:
    if request.param == "sync":
        c = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
        yield c
        c.close()
    else:
        async with AsyncWarmbly(
            api_key="wmbly_test", base_url=BASE_URL, max_retries=0
        ) as ac:
            yield ac


async def call(fn: Any, *args: Any, **kwargs: Any) -> Any:
    result = fn(*args, **kwargs)
    if inspect.isawaitable(result):
        result = await result
    return result


async def collect(result: Any) -> list[Any]:
    if hasattr(result, "__aiter__"):
        return [item async for item in result]
    return list(result)


def _page(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {"data": data, "pagination": {"next_cursor": None, "has_more": False}}


# -- CRM bulk tasks ---------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_bulk_update_tasks(api: Any) -> None:
    route = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 3})
    )
    result = await call(
        api.crm.bulk_update_tasks,
        tasks=["t_1", "t_2", "t_3"],
        status="completed",
        priority="low",
    )
    request = route.calls.last.request
    assert request.method == "PATCH"
    assert request.url.path == "/v1/crm/tasks"
    assert json.loads(request.content) == {
        "tasks": ["t_1", "t_2", "t_3"],
        "status": "completed",
        "priority": "low",
    }
    assert result.affected == 3

    await call(
        api.crm.bulk_update_tasks,
        select_all=True,
        filters={"overdue": True},
        exclude=["t_9"],
        priority="urgent",
    )
    assert json.loads(route.calls.last.request.content) == {
        "all": True,
        "filters": {"overdue": True},
        "exclude": ["t_9"],
        "priority": "urgent",
    }


@pytest.mark.anyio
@respx.mock
async def test_bulk_delete_tasks(api: Any) -> None:
    route = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    result = await call(api.crm.bulk_delete_tasks, ["t_1", "t_2"])
    request = route.calls.last.request
    assert request.method == "DELETE"
    assert request.url.path == "/v1/crm/tasks"
    assert json.loads(request.content) == ["t_1", "t_2"]
    assert result.affected == 2

    await call(
        api.crm.bulk_delete_tasks,
        select_all=True,
        filters={"statuses": ["cancelled"]},
        exclude=["t_1"],
    )
    assert json.loads(route.calls.last.request.content) == {
        "all": True,
        "filters": {"statuses": ["cancelled"]},
        "exclude": ["t_1"],
    }

    with pytest.raises(ValueError, match="requires filters"):
        await call(api.crm.bulk_delete_tasks, select_all=True)
    await call(api.crm.bulk_delete_tasks, select_all=True, filters={})
    assert json.loads(route.calls.last.request.content) == {"all": True, "filters": {}}


# -- templates --------------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_templates_analyze(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(
            200,
            json={
                "score": 72,
                "verdict": "Likely lands in the inbox.",
                "findings": [
                    {
                        "severity": "warn",
                        "field": "subject",
                        "text": "FREE",
                        "line": 1,
                        "excerpt": "FREE audit",
                        "issue": "trigger word",
                        "suggestion": "Say what you offer.",
                        "category": "trigger_word",
                    }
                ],
                "suggested_subject": "A quick audit",
                "improvements": ["Add one clear ask."],
                "rules": {"score": 80, "issues": []},
                "judgment": {"reads_as": 0.2, "ask": "one"},
                "model": "m",
                "tokens_used": 321,
                "credits_remaining": 99,
                "credits_charged": 1,
            },
        )
    )
    result = await call(
        api.templates.analyze, subject="FREE audit", body_plain="Hello there"
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/templates/analyze"
    assert json.loads(request.content) == {
        "subject": "FREE audit",
        "body_plain": "Hello there",
    }
    assert request.headers["idempotency-key"]
    assert result.score == 72
    assert result.findings[0]["field"] == "subject"
    assert result.suggested_subject == "A quick audit"
    assert list(result.improvements) == ["Add one clear ask."]
    assert result.rules == {"score": 80, "issues": []}
    assert result.judgment == {"reads_as": 0.2, "ask": "one"}
    assert result.credits_charged == 1
    assert result.credits_remaining == 99
    assert result.tokens_used == 321


# -- email images -----------------------------------------------------------
IMAGE = {
    "id": "img_1",
    "organization_id": "org_1",
    "user_id": "user_1",
    "filename": "logo.png",
    "mime_type": "image/png",
    "size": 2048,
    "width": 200,
    "height": 100,
    "url": "https://cdn.example.com/email-images/abc.png",
    "created_at": "2026-10-04T08:00:00Z",
}


@pytest.mark.anyio
@respx.mock
async def test_email_images_list(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(200, json=_page([IMAGE]))
    )
    images = await collect(api.email_images.list(limit=20))
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/email-images"
    assert request.url.params.get("limit") == "20"
    assert images[0].url == "https://cdn.example.com/email-images/abc.png"
    assert images[0].width == 200
    assert images[0].mime_type == "image/png"
    assert images[0].size == 2048


@pytest.mark.anyio
@respx.mock
async def test_email_images_upload(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    image = await call(
        api.email_images.upload,
        file=b"\x89PNG\r\n\x1a\nrest",
        filename="logo.png",
        content_type="image/png",
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/email-images"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="logo.png"' in request.content
    assert b"Content-Type: image/png" in request.content
    assert image.id == "img_1"
    assert image.filename == "logo.png"
    assert image.height == 100


@pytest.mark.anyio
@respx.mock
async def test_email_images_delete(api: Any) -> None:
    route = respx.delete(f"{BASE_URL}/email-images/img_1").mock(
        return_value=httpx.Response(204)
    )
    result = await call(api.email_images.delete, "img_1")
    request = route.calls.last.request
    assert request.method == "DELETE"
    assert request.url.path == "/v1/email-images/img_1"
    assert result.id is None


# -- integrations -----------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_set_connection_signing_key(api: Any) -> None:
    route = respx.put(f"{BASE_URL}/integrations/connections/conn_1/signing-key").mock(
        return_value=httpx.Response(
            200,
            json={"connection": {"id": "conn_1", "provider": "calendly"}},
        )
    )
    result = await call(
        api.integrations.set_connection_signing_key,
        "conn_1",
        signing_key="whsec_12345678",
    )
    request = route.calls.last.request
    assert request.method == "PUT"
    assert request.url.path == "/v1/integrations/connections/conn_1/signing-key"
    assert json.loads(request.content) == {"signing_key": "whsec_12345678"}
    assert result.connection is not None
    assert result.connection.provider == "calendly"

    await call(api.integrations.set_connection_signing_key, "conn_1", signing_key="")
    assert json.loads(route.calls.last.request.content) == {"signing_key": ""}


@pytest.mark.anyio
@respx.mock
async def test_rotate_connection_inbound_url(api: Any) -> None:
    route = respx.post(
        f"{BASE_URL}/integrations/connections/conn_1/rotate-inbound-url"
    ).mock(
        return_value=httpx.Response(
            200, json={"inbound_webhook_url": "https://api.example.com/in/xyz"}
        )
    )
    result = await call(api.integrations.rotate_connection_inbound_url, "conn_1")
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/integrations/connections/conn_1/rotate-inbound-url"
    assert request.headers["idempotency-key"]
    assert result.inbound_webhook_url == "https://api.example.com/in/xyz"


@pytest.mark.anyio
@respx.mock
async def test_push_selection(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/integrations/connections/conn_1/push").mock(
        return_value=httpx.Response(200, json={"pushed": 2})
    )
    await call(api.integrations.push, "conn_1", contact_ids=["c_1"])
    assert json.loads(route.calls.last.request.content) == {"contact_ids": ["c_1"]}

    await call(
        api.integrations.push,
        "conn_1",
        select_all=True,
        filters={"query": "acme"},
        exclude=["c_2"],
    )
    assert json.loads(route.calls.last.request.content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c_2"],
    }


# -- forms ------------------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_forms_triage(api: Any) -> None:
    config = respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(
            200,
            json={
                "base_url": "https://f.example.com",
                "captcha_available": False,
                "triage_available": True,
            },
        )
    )
    cfg = await call(api.forms.config)
    assert config.calls.last.request.method == "GET"
    assert cfg.triage_available is True

    patch = respx.patch(f"{BASE_URL}/forms/form_1").mock(
        return_value=httpx.Response(200, json={"id": "form_1", "triage_enabled": True})
    )
    form = await call(api.forms.update, "form_1", triage_enabled=True)
    assert json.loads(patch.calls.last.request.content) == {"triage_enabled": True}
    assert form.triage_enabled is True

    subs = respx.get(f"{BASE_URL}/forms/form_1/submissions").mock(
        return_value=httpx.Response(
            200,
            json=_page([{"id": "sub_1", "triage": "junk", "triage_confidence": 0.93}]),
        )
    )
    items = await collect(api.forms.list_submissions("form_1"))
    assert subs.calls.last.request.method == "GET"
    assert items[0].triage == "junk"
    assert items[0].triage_confidence == 0.93


# -- segments ---------------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_segments_select_all_and_option_labels(api: Any) -> None:
    members = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 500})
    )
    result = await call(
        api.segments.set_members,
        "seg_1",
        mode="exclude",
        select_all=True,
        filters={"verification_status": "invalid"},
        exclude=["c_1"],
    )
    assert json.loads(members.calls.last.request.content) == {
        "all": True,
        "filters": {"verification_status": "invalid"},
        "exclude": ["c_1"],
        "mode": "exclude",
    }
    assert result.updated == 500

    await call(api.segments.set_members, "seg_1", mode="include", contacts=["c_1"])
    assert json.loads(members.calls.last.request.content) == {
        "contacts": ["c_1"],
        "mode": "include",
    }

    respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "field": "mail_host",
                        "label": "Email provider",
                        "group": "Contact",
                        "kind": "enum",
                        "options": ["gmail", "outlook"],
                        "option_labels": {"gmail": "Google"},
                    }
                ]
            },
        )
    )
    fields = await collect(api.segments.fields())
    assert fields[0].field == "mail_host"
    assert fields[0].option_labels == {"gmail": "Google"}


# -- lead sync --------------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_lead_sync_segment_ids(api: Any) -> None:
    listing = respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(
            200,
            json=_page([{"id": "src_1", "segment_ids": ["seg_1"]}]),
        )
    )
    sources = await collect(api.lead_sync.list_sources(segment_id="seg_1"))
    assert listing.calls.last.request.url.params.get("segment_id") == "seg_1"
    assert list(sources[0].segment_ids) == ["seg_1"]

    create = respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json={"id": "src_1", "segment_ids": ["seg_1"]})
    )
    await call(
        api.lead_sync.create_source,
        connection_id="conn_1",
        sheet_id="sheet_1",
        column_mapping=[{"index": 0, "target": "email"}],
        segment_ids=["seg_1"],
    )
    assert json.loads(create.calls.last.request.content)["segment_ids"] == ["seg_1"]

    patch = respx.patch(f"{BASE_URL}/lead-sync/sources/src_1").mock(
        return_value=httpx.Response(200, json={"id": "src_1", "segment_ids": []})
    )
    await call(api.lead_sync.update_source, "src_1", segment_ids=[])
    assert json.loads(patch.calls.last.request.content) == {"segment_ids": []}


# -- campaign segments ------------------------------------------------------
@pytest.mark.anyio
@respx.mock
async def test_campaign_set_segments_withdrawn(api: Any) -> None:
    route = respx.put(f"{BASE_URL}/campaigns/camp_1/segments").mock(
        return_value=httpx.Response(
            200, json={"data": [], "added": 0, "withdrawn": 12, "contacted": 3}
        )
    )
    result = await call(api.campaigns.set_segments, "camp_1", segment_ids=[])
    assert route.calls.last.request.method == "PUT"
    assert json.loads(route.calls.last.request.content) == {"segment_ids": []}
    assert result.withdrawn == 12
    assert result.contacted == 3
