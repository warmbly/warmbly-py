"""Background contact imports, selection-based bulk actions and lookup."""

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


IMPORT = {
    "id": "imp_1",
    "organization_id": "org_1",
    "created_by": "user_1",
    "filename": "leads.csv",
    "format": "csv",
    "status": "draft",
    "has_header": True,
    "columns": ["Email", "Name"],
    "total": 120,
    "processed": 0,
    "imported": 0,
    "updated": 0,
    "skipped": 0,
    "failed": 3,
    "options": {"dedup": "skip"},
    "quality": {"malformed": 1, "flagged": False},
    "segments_pinned": True,
    "notes": ["one note"],
    "error": "",
    "created_at": "2026-10-04T08:00:00Z",
    "updated_at": "2026-10-04T08:00:00Z",
    "started_at": None,
    "finished_at": "2026-10-04T08:05:00Z",
    "preview": {
        "filename": "leads.csv",
        "format": "csv",
        "total_rows": 120,
        "columns": ["Email", "Name"],
        "has_header": True,
        "sample_rows": [["a@example.com", "A"]],
        "suggested_mapping": [{"index": 0, "target": "email"}],
        "inferred_columns": [1],
        "column_stats": [
            {"filled": 120, "distinct": 118, "samples": ["a@example.com"]}
        ],
        "mapping_source": "saved",
    },
    "failures": [{"line": 4, "email": "bad", "reason": "invalid email"}],
}


def _check_import(imp: Any) -> None:
    assert imp.id == "imp_1"
    assert imp.status == "draft"
    assert imp.total == 120
    assert imp.failed == 3
    assert imp.segments_pinned is True
    assert list(imp.notes) == ["one note"]
    assert imp.finished_at == "2026-10-04T08:05:00Z"
    assert imp.preview is not None
    assert imp.preview.mapping_source == "saved"
    assert list(imp.preview.inferred_columns) == [1]
    assert imp.preview.column_stats[0]["distinct"] == 118
    assert imp.failures[0]["reason"] == "invalid email"


@pytest.mark.anyio
@respx.mock
async def test_create_import(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json=IMPORT)
    )
    imp = await call(
        api.contacts.create_import,
        file=b"email,name\na@example.com,A\n",
        filename="leads.csv",
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="leads.csv"' in request.content
    assert b"a@example.com,A" in request.content
    _check_import(imp)


@pytest.mark.anyio
@respx.mock
async def test_list_imports(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [IMPORT],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    items = await collect(api.contacts.list_imports(limit=10))
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/contacts/imports"
    assert request.url.params.get("limit") == "10"
    assert [i.id for i in items] == ["imp_1"]
    _check_import(items[0])


@pytest.mark.anyio
@respx.mock
async def test_retrieve_import(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    imp = await call(api.contacts.retrieve_import, "imp_1")
    assert route.calls.last.request.method == "GET"
    _check_import(imp)


MAPPING = [
    {"index": 0, "target": "email"},
    {"index": 1, "target": "custom", "custom_key": "nickname"},
]


@pytest.mark.anyio
@respx.mock
async def test_save_import_draft(api: Any) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    imp = await call(
        api.contacts.save_import_draft,
        "imp_1",
        mapping=MAPPING,
        dedup="update",
        has_header=True,
        category_ids=["cat_1"],
        campaign_ids=["camp_1"],
        segment_ids=["seg_1"],
        subscribed_default=False,
    )
    request = route.calls.last.request
    assert request.method == "PATCH"
    assert json.loads(request.content) == {
        "mapping": MAPPING,
        "dedup": "update",
        "has_header": True,
        "category_ids": ["cat_1"],
        "campaign_ids": ["camp_1"],
        "segment_ids": ["seg_1"],
        "subscribed_default": False,
    }
    _check_import(imp)

    await call(api.contacts.save_import_draft, "imp_1", has_header=False)
    assert json.loads(route.calls.last.request.content) == {"has_header": False}


@pytest.mark.anyio
@respx.mock
async def test_analyze_import(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/analyze").mock(
        return_value=httpx.Response(
            200,
            json={
                "rows": 120,
                "new": 100,
                "existing": 10,
                "duplicates_in_file": 4,
                "invalid": 5,
                "conflicts": 1,
                "invalid_samples": [{"line": 7, "reason": "no address"}],
                "quality": {"malformed": 5, "flagged": False},
                "problem": "plan limit",
            },
        )
    )
    analysis = await call(
        api.contacts.analyze_import, "imp_1", mapping=MAPPING, has_header=True
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports/imp_1/analyze"
    assert json.loads(request.content) == {"mapping": MAPPING, "has_header": True}
    assert analysis.rows == 120
    assert analysis.new == 100
    assert analysis.existing == 10
    assert analysis.duplicates_in_file == 4
    assert analysis.invalid == 5
    assert analysis.conflicts == 1
    assert analysis.invalid_samples[0]["line"] == 7
    assert analysis.quality == {"malformed": 5, "flagged": False}
    assert analysis.problem == "plan limit"


@pytest.mark.anyio
@respx.mock
async def test_start_import(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/start").mock(
        return_value=httpx.Response(200, json={**IMPORT, "status": "queued"})
    )
    imp = await call(
        api.contacts.start_import,
        "imp_1",
        mapping=MAPPING,
        dedup="skip",
        has_header=True,
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports/imp_1/start"
    assert json.loads(request.content) == {
        "mapping": MAPPING,
        "dedup": "skip",
        "has_header": True,
    }
    assert request.headers["idempotency-key"]
    assert imp.status == "queued"


@pytest.mark.anyio
@respx.mock
async def test_cancel_import(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/cancel").mock(
        return_value=httpx.Response(200, json={**IMPORT, "status": "cancelled"})
    )
    imp = await call(api.contacts.cancel_import, "imp_1")
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports/imp_1/cancel"
    assert imp.status == "cancelled"


@pytest.mark.anyio
@respx.mock
async def test_download_import_failures(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/contacts/imports/imp_1/failed.csv").mock(
        return_value=httpx.Response(
            200,
            content=b"line,email,reason\n4,bad,invalid email\n",
            headers={"content-type": "text/csv; charset=utf-8"},
        )
    )
    data = await call(api.contacts.download_import_failures, "imp_1")
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/contacts/imports/imp_1/failed.csv"
    assert data == b"line,email,reason\n4,bad,invalid email\n"


@pytest.mark.anyio
@respx.mock
async def test_lookup_by_email_and_thread(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(
            200,
            json={
                "contact": {
                    "id": "c_1",
                    "email": "lead@example.com",
                    "mail_host": "gmail",
                },
                "match": "thread",
            },
        )
    )
    result = await call(
        api.contacts.lookup,
        email="alias@example.com",
        thread_id="th_1",
        account_id="ea_1",
    )
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/contacts/lookup"
    assert dict(request.url.params) == {
        "email": "alias@example.com",
        "thread_id": "th_1",
        "account_id": "ea_1",
    }
    assert result.match == "thread"
    assert result.contact is not None
    assert result.contact.mail_host == "gmail"

    await call(api.contacts.lookup, thread_id="th_2")
    assert dict(route.calls.last.request.url.params) == {"thread_id": "th_2"}


@pytest.mark.anyio
@respx.mock
async def test_bulk_update_selection(api: Any) -> None:
    route = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 250})
    )
    result = await call(
        api.contacts.bulk_update,
        select_all=True,
        filters={"verification_status": "valid"},
        exclude=["c_9"],
        subscribe=False,
    )
    assert json.loads(route.calls.last.request.content) == {
        "all": True,
        "filters": {"verification_status": "valid"},
        "exclude": ["c_9"],
        "subscribe": False,
    }
    assert result.updated == 250

    await call(api.contacts.bulk_update, contacts=["c_1"], subscribe=True)
    assert json.loads(route.calls.last.request.content) == {
        "contacts": ["c_1"],
        "subscribe": True,
    }


@pytest.mark.anyio
@respx.mock
async def test_bulk_delete_selection(api: Any) -> None:
    route = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    await call(api.contacts.bulk_delete, ["c_1", "c_2"])
    assert json.loads(route.calls.last.request.content) == ["c_1", "c_2"]

    await call(
        api.contacts.bulk_delete,
        select_all=True,
        filters={"query": "acme"},
        exclude=["c_1"],
    )
    assert json.loads(route.calls.last.request.content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c_1"],
    }


@pytest.mark.anyio
@respx.mock
async def test_request_verification_selection(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200,
            json={
                "affected": 12,
                "action": "verify",
                "queued": True,
                "verifier": "cleanmylist",
                "verifier_label": "CleanMyList",
                "verifier_error": "out of credits",
            },
        )
    )
    result = await call(
        api.contacts.request_verification,
        action="verify",
        select_all=True,
        filters={"verification_status": "unknown"},
        exclude=["c_3"],
    )
    assert json.loads(route.calls.last.request.content) == {
        "action": "verify",
        "all": True,
        "filters": {"verification_status": "unknown"},
        "exclude": ["c_3"],
    }
    assert result.verifier == "cleanmylist"
    assert result.verifier_label == "CleanMyList"
    assert result.verifier_error == "out of credits"


@pytest.mark.anyio
@respx.mock
async def test_research_batch_selection(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/contacts/research/batch").mock(
        return_value=httpx.Response(200, json={"queued": 40})
    )
    result = await call(
        api.contacts.research_batch,
        select_all=True,
        filters={"query": "cto"},
        exclude=["c_1"],
        objective="find hooks",
    )
    assert json.loads(route.calls.last.request.content) == {
        "objective": "find hooks",
        "all": True,
        "filters": {"query": "cto"},
        "exclude": ["c_1"],
    }
    assert result.queued == 40

    await call(api.contacts.research_batch, contact_ids=["c_1"])
    assert json.loads(route.calls.last.request.content) == {"contact_ids": ["c_1"]}


@pytest.mark.anyio
@respx.mock
async def test_update_email_and_search_mail_hosts(api: Any) -> None:
    patch = respx.patch(f"{BASE_URL}/contacts/c_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c_1",
                "email": "new@example.com",
                "mail_host": "microsoft365",
                "verification_requested_at": "2026-10-04T08:00:00Z",
            },
        )
    )
    contact = await call(api.contacts.update, "c_1", email="new@example.com")
    assert json.loads(patch.calls.last.request.content) == {"email": "new@example.com"}
    assert contact.mail_host == "microsoft365"
    assert contact.verification_requested_at == "2026-10-04T08:00:00Z"

    search = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await call(api.contacts.search, mail_hosts=["gmail", ""], sort_by="custom:tier")
    assert json.loads(search.calls.last.request.content) == {
        "mail_hosts": ["gmail", ""],
        "sort_by": "custom:tier",
    }


@pytest.mark.anyio
@respx.mock
async def test_campaign_state_hold_and_cc(api: Any) -> None:
    respx.get(f"{BASE_URL}/contacts/c_1/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "campaign_id": "camp_1",
                        "lead_status": "paused",
                        "sender_id": "ea_1",
                        "sender_email": "me@example.com",
                        "hold": {"since": "2026-10-04T00:00:00Z", "source": "manual"},
                        "cc": [{"contact_id": "c_2", "status": "active"}],
                    }
                ],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    states = await collect(api.contacts.list_campaigns("c_1"))
    assert states[0].lead_status == "paused"
    assert states[0].sender_email == "me@example.com"
    assert states[0].hold == {"since": "2026-10-04T00:00:00Z", "source": "manual"}
    assert states[0].cc[0]["contact_id"] == "c_2"


@pytest.mark.anyio
@respx.mock
async def test_bulk_delete_rejects_empty_or_mixed_selection(api: Any) -> None:
    with pytest.raises(ValueError, match="required"):
        await call(api.contacts.bulk_delete)
    with pytest.raises(ValueError, match="not both"):
        await call(api.contacts.bulk_delete, ["c_1"], select_all=True)


@pytest.mark.anyio
@respx.mock
async def test_integrations_push_requires_a_selection(api: Any) -> None:
    with pytest.raises(ValueError, match="requires contact_ids"):
        await call(api.integrations.push, "conn_1")


@pytest.mark.anyio
@respx.mock
async def test_bulk_update_tasks_select_all_requires_filters(api: Any) -> None:
    with pytest.raises(ValueError, match="requires filters"):
        await call(api.crm.bulk_update_tasks, select_all=True, status="done")
