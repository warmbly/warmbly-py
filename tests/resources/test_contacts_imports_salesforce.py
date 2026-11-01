"""Tests for contact imports, Salesforce, lookup and bulk selections."""

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


MAPPING = [
    {"index": 0, "target": "email"},
    {"index": 1, "target": "custom", "custom_key": "plan"},
]

# Built from models.ContactImport (+ ContactImportPreview, ContactImportQuality).
IMPORT: dict[str, Any] = {
    "id": "imp_1",
    "organization_id": "org_1",
    "created_by": "usr_1",
    "filename": "leads.csv",
    "format": "csv",
    "status": "running",
    "has_header": True,
    "columns": ["Email", "Plan"],
    "total": 1200,
    "processed": 300,
    "imported": 250,
    "updated": 30,
    "skipped": 15,
    "failed": 5,
    "options": {"mapping": MAPPING, "dedup": "skip", "has_header": True},
    "quality": {
        "malformed": 2,
        "disposable": 1,
        "role": 7,
        "bad_share_pct": 0.8,
        "flagged": False,
        "summary": "Looks clean",
    },
    "segments_pinned": True,
    "notes": ["2 rows had no email"],
    "error": "",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:01:00Z",
    "started_at": "2026-01-01T00:00:30Z",
    "preview": {
        "filename": "leads.csv",
        "format": "csv",
        "total_rows": 1200,
        "columns": ["Email", "Plan"],
        "has_header": True,
        "sample_rows": [["a@example.com", "pro"]],
        "suggested_mapping": MAPPING,
        "inferred_columns": [1],
        "column_stats": [
            {"filled": 1200, "distinct": 1190, "samples": ["a@example.com"]},
            {"filled": 900, "distinct": 3, "samples": ["pro", "free"]},
        ],
        "mapping_source": "saved",
    },
    "failures": [
        {"line": 4, "email": "bad", "values": ["bad", "x"], "reason": "invalid"}
    ],
}


def _assert_import(imp: Any) -> None:
    assert imp.id == "imp_1"
    assert imp.status == "running"
    assert imp.filename == "leads.csv"
    assert imp.total == 1200 and imp.processed == 300
    assert imp.imported == 250 and imp.failed == 5
    assert imp.quality.role == 7 and imp.quality.summary == "Looks clean"
    assert imp.segments_pinned is True
    assert imp.notes == ["2 rows had no email"]
    assert imp.options["dedup"] == "skip"
    assert imp.preview.mapping_source == "saved"
    assert imp.preview.inferred_columns == [1]
    assert imp.preview.column_stats[1].distinct == 3
    assert imp.preview.suggested_mapping[1]["custom_key"] == "plan"
    assert imp.failures[0].line == 4 and imp.failures[0].reason == "invalid"
    assert imp.started_at == "2026-01-01T00:00:30Z"


# -- imports ---------------------------------------------------------------


@respx.mock
def test_list_imports_pages(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/imports").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [IMPORT],
                    "pagination": {
                        "total": None,
                        "next_cursor": "c2",
                        "has_more": True,
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**IMPORT, "id": "imp_2"}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )

    items = list(client.contacts.list_imports(limit=1))

    assert [i.id for i in items] == ["imp_1", "imp_2"]
    first, second = (c.request for c in route.calls)
    assert first.method == "GET"
    assert first.url.path == "/v1/contacts/imports"
    assert first.url.params["limit"] == "1"
    assert "cursor" not in first.url.params
    assert second.url.params["cursor"] == "c2"
    _assert_import(items[0])


@pytest.mark.anyio
@respx.mock
async def test_async_list_imports(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [IMPORT],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )

    items = [i async for i in aclient.contacts.list_imports(limit=5)]

    assert route.calls.last.request.url.params["limit"] == "5"
    _assert_import(items[0])


@respx.mock
def test_create_import_uploads_multipart(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json={**IMPORT, "status": "draft"})
    )

    imp = client.contacts.create_import(
        file=b"email\na@example.com\n", filename="leads.csv"
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="leads.csv"' in request.content
    assert b"a@example.com" in request.content
    assert imp.status == "draft"
    assert imp.preview.total_rows == 1200


@pytest.mark.anyio
@respx.mock
async def test_async_create_import(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json=IMPORT)
    )

    imp = await aclient.contacts.create_import(file=b"x", filename="a.csv")

    assert b'filename="a.csv"' in route.calls.last.request.content
    _assert_import(imp)


@respx.mock
def test_retrieve_import(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )

    imp = client.contacts.retrieve_import("imp_1")

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/contacts/imports/imp_1"
    _assert_import(imp)


@pytest.mark.anyio
@respx.mock
async def test_async_retrieve_import(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _assert_import(await aclient.contacts.retrieve_import("imp_1"))


@respx.mock
def test_save_import_draft(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )

    imp = client.contacts.save_import_draft(
        "imp_1",
        mapping=MAPPING,
        dedup="update",
        has_header=True,
        category_ids=["cat_1"],
        campaign_ids=["cmp_1"],
        segment_ids=["seg_1"],
        subscribed_default=False,
    )

    request = route.calls.last.request
    assert request.method == "PATCH"
    assert request.url.path == "/v1/contacts/imports/imp_1"
    assert json.loads(request.content) == {
        "mapping": MAPPING,
        "dedup": "update",
        "has_header": True,
        "category_ids": ["cat_1"],
        "campaign_ids": ["cmp_1"],
        "segment_ids": ["seg_1"],
        "subscribed_default": False,
    }
    _assert_import(imp)


@pytest.mark.anyio
@respx.mock
async def test_async_save_import_draft_omits_unset(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )

    imp = await aclient.contacts.save_import_draft(
        "imp_1", mapping=MAPPING, dedup="skip", has_header=False
    )

    assert json.loads(route.calls.last.request.content) == {
        "mapping": MAPPING,
        "dedup": "skip",
        "has_header": False,
    }
    _assert_import(imp)


ANALYSIS = {
    "rows": 1200,
    "new": 1000,
    "existing": 150,
    "duplicates_in_file": 20,
    "invalid": 25,
    "conflicts": 5,
    "invalid_samples": [{"line": 9, "email": "nope", "reason": "not an address"}],
    "quality": {
        "malformed": 25,
        "disposable": 0,
        "role": 3,
        "bad_share_pct": 2.1,
        "flagged": True,
    },
    "problem": "Over the plan's contact limit",
}


def _assert_analysis(a: Any) -> None:
    assert a.rows == 1200 and a.new == 1000 and a.existing == 150
    assert a.duplicates_in_file == 20 and a.invalid == 25 and a.conflicts == 5
    assert a.invalid_samples[0].line == 9
    assert a.invalid_samples[0].reason == "not an address"
    assert a.quality.flagged is True and a.quality.bad_share_pct == 2.1
    assert a.problem == "Over the plan's contact limit"


@respx.mock
def test_analyze_import(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )

    a = client.contacts.analyze_import("imp_1", mapping=MAPPING, has_header=True)

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports/imp_1/analyze"
    assert json.loads(request.content) == {"mapping": MAPPING, "has_header": True}
    _assert_analysis(a)


@pytest.mark.anyio
@respx.mock
async def test_async_analyze_import(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )

    a = await aclient.contacts.analyze_import(
        "imp_1", mapping=MAPPING, has_header=False
    )

    assert json.loads(route.calls.last.request.content)["has_header"] is False
    _assert_analysis(a)


@respx.mock
def test_start_import(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )

    imp = client.contacts.start_import(
        "imp_1", mapping=MAPPING, dedup="skip", has_header=True, segment_ids=["seg_1"]
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports/imp_1/start"
    assert json.loads(request.content) == {
        "mapping": MAPPING,
        "dedup": "skip",
        "has_header": True,
        "segment_ids": ["seg_1"],
    }
    assert request.headers.get("idempotency-key")
    _assert_import(imp)


@pytest.mark.anyio
@respx.mock
async def test_async_start_import(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )

    imp = await aclient.contacts.start_import(
        "imp_1", mapping=MAPPING, dedup="create_duplicate", has_header=True
    )

    assert json.loads(route.calls.last.request.content)["dedup"] == "create_duplicate"
    _assert_import(imp)


@respx.mock
def test_cancel_import(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/imports/imp_1/cancel").mock(
        return_value=httpx.Response(200, json={**IMPORT, "status": "cancelled"})
    )

    imp = client.contacts.cancel_import("imp_1")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/imports/imp_1/cancel"
    assert request.content == b""
    assert imp.status == "cancelled"
    assert imp.imported == 250


@pytest.mark.anyio
@respx.mock
async def test_async_cancel_import(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/contacts/imports/imp_1/cancel").mock(
        return_value=httpx.Response(200, json={**IMPORT, "status": "cancelled"})
    )
    imp = await aclient.contacts.cancel_import("imp_1")
    assert imp.status == "cancelled"


@respx.mock
def test_download_import_failures_returns_bytes(client: Warmbly) -> None:
    csv = b"line,email,reason\n4,bad,invalid\n"
    route = respx.get(f"{BASE_URL}/contacts/imports/imp_1/failed.csv").mock(
        return_value=httpx.Response(
            200,
            content=csv,
            headers={
                "content-type": "text/csv; charset=utf-8",
                "content-disposition": 'attachment; filename="leads-failed.csv"',
            },
        )
    )

    data = client.contacts.download_import_failures("imp_1")

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/contacts/imports/imp_1/failed.csv"
    assert data == csv


@pytest.mark.anyio
@respx.mock
async def test_async_download_import_failures(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/imports/imp_1/failed.csv").mock(
        return_value=httpx.Response(
            200, content=b"a,b\n", headers={"content-type": "text/csv"}
        )
    )
    assert await aclient.contacts.download_import_failures("imp_1") == b"a,b\n"


def test_unknown_import_fields_and_status_do_not_raise(client: Warmbly) -> None:
    from warmbly.resources.contacts import ContactImport

    imp = ContactImport.model_validate(
        {
            "id": "i",
            "status": "paused_by_aliens",
            "brand_new": {"x": 1},
            "preview": None,
        }
    )
    assert imp.status == "paused_by_aliens"
    assert imp.preview is None
    assert imp.failures == []


# -- committed-import / preview models -------------------------------------


@respx.mock
def test_import_preview_decodes_new_fields(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(200, json=IMPORT["preview"])
    )
    p = client.contacts.import_preview(file=b"x", filename="a.csv")
    assert p.inferred_columns == [1]
    assert p.mapping_source == "saved"
    assert p.column_stats[0].filled == 1200


@respx.mock
def test_import_commit_decodes_segments_pinned_and_quality(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 3,
                "imported": 2,
                "updated": 1,
                "skipped": 0,
                "failed": 0,
                "started_at": "2026-01-01T00:00:00Z",
                "ended_at": "2026-01-01T00:00:01Z",
                "segments_pinned": False,
                "errors": [{"line": 2, "reason": "segment write failed"}],
                "quality": {
                    "malformed": 0,
                    "disposable": 1,
                    "role": 0,
                    "bad_share_pct": 0,
                    "flagged": False,
                },
            },
        )
    )
    r = client.contacts.import_commit(
        file=b"x", filename="a.csv", import_options={"mapping": []}
    )
    assert r.segments_pinned is False
    assert r.quality.disposable == 1


# -- Salesforce -------------------------------------------------------------

PANEL = {
    "connections": [
        {
            "id": "con_1",
            "label": "Prod",
            "environment": "production",
            "instance_url": "https://acme.my.salesforce.com",
        }
    ],
    "records": [
        {
            "link_id": "lnk_1",
            "connection_id": "con_1",
            "connection_label": "Prod",
            "object": "Lead",
            "id": "00Q123",
            "url": "https://acme.my.salesforce.com/00Q123",
            "name": "Ada Lovelace",
            "title": "CTO",
            "company": "Analytical",
            "email": "ada@example.com",
            "status": "Open",
            "owner": {"id": "005", "name": "Sam"},
            "account": {"id": "001", "name": "Analytical", "url": "https://x/001"},
            "is_converted": False,
            "opted_out": False,
            "lead_source": "Web",
            "opportunities": [
                {
                    "id": "006",
                    "name": "Deal",
                    "stage": "Prospecting",
                    "is_closed": False,
                }
            ],
            "tasks": [
                {
                    "id": "00T",
                    "subject": "Email",
                    "status": "Completed",
                    "from_warmbly": True,
                }
            ],
            "linked_by": "email",
            "last_synced_at": "2026-01-01T00:00:00Z",
            "sync": {"pending": 1, "failed": 0, "synced": 4},
            "stale": False,
        }
    ],
    "can_sync": True,
}


def _assert_panel(p: Any) -> None:
    assert p.can_sync is True
    assert p.connections[0].id == "con_1"
    assert p.connections[0].instance_url == "https://acme.my.salesforce.com"
    rec = p.records[0]
    assert rec.link_id == "lnk_1"
    assert rec.object == "Lead"
    assert rec.name == "Ada Lovelace"
    assert rec.owner["name"] == "Sam"
    assert rec.opportunities[0]["stage"] == "Prospecting"
    assert rec.tasks[0]["from_warmbly"] is True
    assert rec.sync["pending"] == 1
    assert rec.stale is False


@respx.mock
def test_salesforce_panel(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/c_1/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )

    panel = client.contacts.salesforce("c_1")

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/contacts/c_1/salesforce"
    _assert_panel(panel)


@pytest.mark.anyio
@respx.mock
async def test_async_salesforce_panel(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/c_1/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _assert_panel(await aclient.contacts.salesforce("c_1"))


@respx.mock
def test_sync_salesforce_sends_body_and_idempotency_key(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/c_1/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )

    panel = client.contacts.sync_salesforce(
        "c_1", connection_id="con_1", create_as="contact"
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/c_1/salesforce/sync"
    assert json.loads(request.content) == {
        "connection_id": "con_1",
        "create_as": "contact",
    }
    assert request.headers.get("idempotency-key")
    _assert_panel(panel)


@pytest.mark.anyio
@respx.mock
async def test_async_sync_salesforce_without_body(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/c_1/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )

    panel = await aclient.contacts.sync_salesforce("c_1")

    assert route.calls.last.request.url.path == "/v1/contacts/c_1/salesforce/sync"
    assert json.loads(route.calls.last.request.content or b"{}") == {}
    _assert_panel(panel)


@respx.mock
def test_unlink_salesforce_handles_204(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/contacts/c_1/salesforce/links/lnk_1").mock(
        return_value=httpx.Response(204)
    )

    result = client.contacts.unlink_salesforce("c_1", "lnk_1")

    assert route.calls.last.request.method == "DELETE"
    assert (
        route.calls.last.request.url.path == "/v1/contacts/c_1/salesforce/links/lnk_1"
    )
    assert result is not None


@pytest.mark.anyio
@respx.mock
async def test_async_unlink_salesforce(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/contacts/c_1/salesforce/links/lnk_1").mock(
        return_value=httpx.Response(204)
    )
    await aclient.contacts.unlink_salesforce("c_1", "lnk_1")
    assert route.called


# -- lookup ----------------------------------------------------------------

LOOKUP = {
    "contact": {
        "id": "c_1",
        "email": "ada@example.com",
        "mail_host": "google_workspace",
    },
    "match": "thread",
}


@respx.mock
def test_lookup_by_thread(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json=LOOKUP)
    )

    result = client.contacts.lookup(thread_id="th_1", account_id="em_1")

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/contacts/lookup"
    assert dict(request.url.params) == {"thread_id": "th_1", "account_id": "em_1"}
    assert result.match == "thread"
    assert result.contact.id == "c_1"
    assert result.contact.mail_host == "google_workspace"


@pytest.mark.anyio
@respx.mock
async def test_async_lookup_by_email_and_unmatched(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        side_effect=[
            httpx.Response(200, json={"contact": {"id": "c_1"}, "match": "email"}),
            httpx.Response(200, json={"contact": None}),
        ]
    )

    found = await aclient.contacts.lookup(email="Ada <ada@example.com>")
    missing = await aclient.contacts.lookup(email="nobody@example.com")

    assert route.calls[0].request.url.params["email"] == "Ada <ada@example.com>"
    assert "thread_id" not in route.calls[0].request.url.params
    assert found.match == "email"
    assert missing.contact is None
    assert missing.match is None


# -- bulk selections / update / search --------------------------------------


@respx.mock
def test_bulk_update_select_all(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 120})
    )

    result = client.contacts.bulk_update(
        select_all=True,
        filters={"query": "acme"},
        exclude=["c_9"],
        subscribe=False,
    )

    assert json.loads(route.calls.last.request.content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c_9"],
        "subscribe": False,
    }
    assert result.updated == 120


@respx.mock
def test_bulk_update_with_ids_still_sends_contacts(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 1})
    )
    client.contacts.bulk_update(contacts=["c_1"], add_categories=["cat"])
    assert json.loads(route.calls.last.request.content) == {
        "contacts": ["c_1"],
        "add_categories": ["cat"],
    }


@respx.mock
def test_bulk_delete_array_and_selection(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))

    client.contacts.bulk_delete(["c_1", "c_2"])
    client.contacts.bulk_delete(
        select_all=True, filters={"subscribed": False}, exclude=["c_3"]
    )

    assert json.loads(route.calls[0].request.content) == ["c_1", "c_2"]
    assert json.loads(route.calls[1].request.content) == {
        "all": True,
        "filters": {"subscribed": False},
        "exclude": ["c_3"],
    }


@pytest.mark.anyio
@respx.mock
async def test_async_bulk_delete_selection(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    await aclient.contacts.bulk_delete(select_all=True, filters={})
    assert json.loads(route.calls.last.request.content) == {"all": True, "filters": {}}


@respx.mock
def test_request_verification_select_all_and_response(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200,
            json={
                "affected": 40,
                "action": "verify",
                "queued": True,
                "verifier": "builtin",
                "verifier_label": "Built-in",
                "verifier_error": "key rejected",
            },
        )
    )

    result = client.contacts.request_verification(
        action="verify", select_all=True, filters={"verification_status": "unknown"}
    )

    assert json.loads(route.calls.last.request.content) == {
        "action": "verify",
        "all": True,
        "filters": {"verification_status": "unknown"},
    }
    assert result.affected == 40 and result.queued is True
    assert result.verifier == "builtin"
    assert result.verifier_label == "Built-in"
    assert result.verifier_error == "key rejected"


@pytest.mark.anyio
@respx.mock
async def test_async_request_verification_campaign(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200, json={"affected": 1, "action": "verify", "queued": True}
        )
    )
    await aclient.contacts.request_verification(action="verify", campaign_id="cmp_1")
    assert json.loads(route.calls.last.request.content) == {
        "action": "verify",
        "campaign_id": "cmp_1",
    }


@respx.mock
def test_update_contact_sends_email(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/c_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c_1",
                "email": "new@example.com",
                "mail_host": "microsoft365",
                "verification_requested_at": "2026-01-01T00:00:00Z",
                "outreach": {
                    "sent": 3,
                    "opened": 2,
                    "last_sent_at": "2026-01-01T00:00:00Z",
                },
            },
        )
    )

    c = client.contacts.update("c_1", email="new@example.com")

    assert json.loads(route.calls.last.request.content) == {"email": "new@example.com"}
    assert c.email == "new@example.com"
    assert c.mail_host == "microsoft365"
    assert c.verification_requested_at == "2026-01-01T00:00:00Z"
    assert c.outreach.sent == 3 and c.outreach.opened == 2
    assert c.outreach.last_sent_at == "2026-01-01T00:00:00Z"
    assert c.outreach.clicked is None


@pytest.mark.anyio
@respx.mock
async def test_async_search_mail_hosts(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(
            200,
            json={"data": [], "pagination": {"next_cursor": None, "has_more": False}},
        )
    )

    await aclient.contacts.search(
        mail_hosts=["google_workspace", ""], sort_by="custom:plan"
    )

    assert json.loads(route.calls.last.request.content) == {
        "mail_hosts": ["google_workspace", ""],
        "sort_by": "custom:plan",
    }


@respx.mock
def test_sent_email_machine_opened_at(client: Warmbly) -> None:
    from warmbly.resources.contacts import ContactSentEmail

    e = ContactSentEmail.model_validate(
        {"task_id": "t", "machine_opened_at": "2026-01-01T00:00:00Z"}
    )
    assert e.machine_opened_at == "2026-01-01T00:00:00Z"
