"""Tests for the contacts resource changes synced from the server.

Covers background imports, the Salesforce panel, bulk selections, the bare-list
create/edit responses, lookup by thread, and the fields added to the models.
Every call is made on both the sync and the async client.
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

CONTACT_ID = "11111111-1111-4111-8111-111111111111"
IMPORT_ID = "22222222-2222-4222-8222-222222222222"
LINK_ID = "33333333-3333-4333-8333-333333333333"
CONN_ID = "44444444-4444-4444-8444-444444444444"


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


CONTACT: dict[str, Any] = {
    "id": CONTACT_ID,
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "company": "Analytical",
    "phone": "",
    "custom_fields": {"plan": "pro"},
    "subscribed": True,
    "campaigns": [],
    "categories": [],
    "verification_status": "valid",
    "verification_reason": "",
    "is_catch_all": False,
    "verification_source": "probe",
    "verification_provider": "builtin",
    "verification_sub_status": "",
    "verification_confidence": 90,
    "verification_requested_at": "2026-10-01T10:00:00Z",
    "mail_host": "google",
    "esp_provider": "gmail",
    "outreach": {"sent": 3, "opened": 2, "clicked": 1, "replied": 0, "bounced": 0},
    "updated_at": "2026-10-01T10:00:00Z",
    "created_at": "2026-09-01T10:00:00Z",
}

PREVIEW: dict[str, Any] = {
    "filename": "leads.csv",
    "format": "csv",
    "total_rows": 1243,
    "columns": ["Email", "Name"],
    "has_header": True,
    "sample_rows": [["a@b.com", "A"]],
    "suggested_mapping": [{"index": 0, "target": "email"}],
    "inferred_columns": [1],
    "column_stats": [{"filled": 1200, "distinct": 1190, "samples": ["a@b.com"]}],
    "mapping_source": "saved",
}

IMPORT: dict[str, Any] = {
    "id": IMPORT_ID,
    "organization_id": "55555555-5555-4555-8555-555555555555",
    "created_by": "66666666-6666-4666-8666-666666666666",
    "filename": "leads.csv",
    "format": "csv",
    "status": "running",
    "has_header": True,
    "columns": ["Email", "Name"],
    "total": 1243,
    "processed": 600,
    "imported": 500,
    "updated": 50,
    "skipped": 40,
    "failed": 10,
    "options": {"dedup": "update"},
    "quality": {"malformed": 1, "flagged": False},
    "segments_pinned": True,
    "notes": ["one note"],
    "error": "",
    "created_at": "2026-10-01T10:00:00Z",
    "updated_at": "2026-10-01T10:05:00Z",
    "started_at": "2026-10-01T10:01:00Z",
    "finished_at": None,
    "preview": PREVIEW,
    "failures": [{"line": 4, "email": "bad", "reason": "invalid address"}],
}


def _check_import(imp: Any) -> None:
    assert imp.id == IMPORT_ID
    assert imp.status == "running"
    assert imp.total == 1243
    assert imp.processed == 600
    assert imp.imported == 500
    assert imp.segments_pinned is True
    assert imp.notes == ["one note"]
    assert imp.options == {"dedup": "update"}
    assert imp.preview is not None
    assert imp.preview.mapping_source == "saved"
    assert imp.preview.inferred_columns == [1]
    assert imp.preview.column_stats is not None
    assert imp.preview.column_stats[0]["filled"] == 1200
    assert imp.failures is not None
    assert imp.failures[0]["reason"] == "invalid address"


MAPPING = [{"index": 0, "target": "email"}, {"index": 1, "target": "first_name"}]

ANALYSIS: dict[str, Any] = {
    "rows": 100,
    "new": 80,
    "existing": 10,
    "duplicates_in_file": 4,
    "invalid": 5,
    "conflicts": 1,
    "invalid_samples": [{"line": 3, "email": "x", "reason": "bad"}],
    "quality": {"malformed": 5},
    "problem": "plan limit",
}

PANEL: dict[str, Any] = {
    "connections": [
        {
            "id": CONN_ID,
            "label": "Prod",
            "environment": "production",
            "instance_url": "https://acme.my.salesforce.com",
        }
    ],
    "records": [
        {
            "link_id": LINK_ID,
            "connection_id": CONN_ID,
            "connection_label": "Prod",
            "object": "Lead",
            "id": "00Q000000001",
            "url": "https://acme.my.salesforce.com/00Q000000001",
            "name": "Ada Lovelace",
            "title": "CTO",
            "company": "Analytical",
            "email": "ada@example.com",
            "status": "Open",
            "owner": {"id": "005", "name": "Owner"},
            "account": {"id": "001", "name": "Acme", "url": "https://x/001"},
            "is_converted": False,
            "opted_out": False,
            "lead_source": "Web",
            "opportunities": [
                {
                    "id": "006",
                    "name": "Big deal",
                    "stage": "Prospecting",
                    "amount": 1500.5,
                    "close_date": "2026-12-01",
                    "is_closed": False,
                    "is_won": False,
                    "url": "https://x/006",
                }
            ],
            "tasks": [
                {
                    "id": "00T",
                    "subject": "Email: Hi",
                    "date": "2026-10-01",
                    "status": "Completed",
                    "owner_name": "Owner",
                    "url": "https://x/00T",
                    "from_warmbly": True,
                }
            ],
            "linked_by": "auto",
            "last_synced_at": "2026-10-01T10:00:00Z",
            "sync": {"pending": 1, "failed": 0, "synced": 4, "last_error": ""},
            "stale": False,
        }
    ],
    "can_sync": True,
}


def _check_panel(panel: Any) -> None:
    assert panel.can_sync is True
    assert panel.connections[0].instance_url == "https://acme.my.salesforce.com"
    rec = panel.records[0]
    assert rec.link_id == LINK_ID
    assert rec.object == "Lead"
    assert rec.owner.name == "Owner"
    assert rec.account.name == "Acme"
    assert rec.opportunities[0].amount == 1500.5
    assert rec.opportunities[0].stage == "Prospecting"
    assert rec.tasks[0].from_warmbly is True
    assert rec.sync.synced == 4


def _page(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


# -- create / bulk edit return bare lists ------------------------------------
@respx.mock
def test_create_returns_contact_list(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json=[CONTACT])
    )
    out = client.contacts.create([{"email": "ada@example.com"}])
    assert _last(route).method == "POST"
    assert _last(route).url.path == "/v1/contacts"
    assert _body(route) == [{"email": "ada@example.com"}]
    assert [c.id for c in out] == [CONTACT_ID]
    assert out[0].mail_host == "google"
    assert out[0].verification_requested_at == "2026-10-01T10:00:00Z"
    assert out[0].outreach == CONTACT["outreach"]


@respx.mock
@pytest.mark.anyio
async def test_create_returns_contact_list_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json=[CONTACT])
    )
    out = await aclient.contacts.create([{"email": "ada@example.com"}])
    assert _body(route) == [{"email": "ada@example.com"}]
    assert out[0].mail_host == "google"
    assert out[0].outreach == CONTACT["outreach"]


@respx.mock
def test_bulk_update_ids_and_select_all(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json=[CONTACT])
    )
    out = client.contacts.bulk_update(contacts=[CONTACT_ID], subscribe=False)
    assert _body(route) == {"contacts": [CONTACT_ID], "subscribe": False}
    assert out[0].id == CONTACT_ID

    # A select-all edit answers with JSON null; it reads as an empty list.
    route.mock(return_value=httpx.Response(200, json=None))
    out = client.contacts.bulk_update(
        select_all=True,
        filters={"query": "acme"},
        exclude=["x"],
        add_categories=["c1"],
    )
    assert _body(route) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["x"],
        "add_categories": ["c1"],
    }
    assert out == []


@respx.mock
@pytest.mark.anyio
async def test_bulk_update_ids_and_select_all_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json=[CONTACT])
    )
    out = await aclient.contacts.bulk_update(contacts=[CONTACT_ID], subscribe=False)
    assert _body(route) == {"contacts": [CONTACT_ID], "subscribe": False}
    assert out[0].id == CONTACT_ID

    route.mock(return_value=httpx.Response(200, json=None))
    out = await aclient.contacts.bulk_update(
        select_all=True, filters={"query": "acme"}, exclude=["x"]
    )
    assert _body(route) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["x"],
    }
    assert out == []


@respx.mock
def test_bulk_delete_array_and_selection(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    client.contacts.bulk_delete(["a", "b"])
    assert _last(route).method == "DELETE"
    assert _body(route) == ["a", "b"]

    client.contacts.bulk_delete(select_all=True, filters={"query": "x"}, exclude=["a"])
    assert _body(route) == {"all": True, "filters": {"query": "x"}, "exclude": ["a"]}

    client.contacts.bulk_delete()
    assert _body(route) == []


@respx.mock
@pytest.mark.anyio
async def test_bulk_delete_array_and_selection_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    await aclient.contacts.bulk_delete(["a", "b"])
    assert _body(route) == ["a", "b"]

    await aclient.contacts.bulk_delete(select_all=True, filters={"query": "x"})
    assert _body(route) == {"all": True, "filters": {"query": "x"}}


# -- search / update / lookup -------------------------------------------------
@respx.mock
def test_search_sends_mail_hosts_and_decodes_outreach(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(
            200,
            json={
                **_page([CONTACT]),
                "lead_counts": {"total": 3, "paused": 1, "providers": {"gmail": 2}},
            },
        )
    )
    page = client.contacts.search(
        mail_hosts=["google", ""], sort_by="custom:plan", reverse=True, limit=5
    )
    assert _body(route) == {
        "mail_hosts": ["google", ""],
        "sort_by": "custom:plan",
        "reverse": True,
    }
    assert _last(route).url.params["limit"] == "5"
    assert page.data[0].outreach is not None
    assert page.data[0].outreach["sent"] == 3
    assert page.lead_counts is not None
    assert page.lead_counts["paused"] == 1


@respx.mock
@pytest.mark.anyio
async def test_search_sends_mail_hosts_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json=_page([CONTACT]))
    )
    page = await aclient.contacts.search(mail_hosts=["google"])
    assert _body(route) == {"mail_hosts": ["google"]}
    assert page.data[0].mail_host == "google"


@respx.mock
def test_update_can_change_email(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json=CONTACT)
    )
    out = client.contacts.update(CONTACT_ID, email="new@example.com")
    assert _last(route).method == "PATCH"
    assert _body(route) == {"email": "new@example.com"}
    assert out.email == "ada@example.com"


@respx.mock
@pytest.mark.anyio
async def test_update_can_change_email_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json=CONTACT)
    )
    await aclient.contacts.update(CONTACT_ID, email="new@example.com")
    assert _body(route) == {"email": "new@example.com"}


@respx.mock
def test_lookup_by_thread(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"contact": CONTACT, "match": "thread"})
    )
    out = client.contacts.lookup(thread_id="t1", account_id="acc1")
    params = _last(route).url.params
    assert dict(params) == {"thread_id": "t1", "account_id": "acc1"}
    assert out.match == "thread"
    assert out.contact is not None
    assert out.contact.id == CONTACT_ID

    route.mock(return_value=httpx.Response(200, json={"contact": None}))
    empty = client.contacts.lookup(email="x@y.com")
    assert dict(_last(route).url.params) == {"email": "x@y.com"}
    assert empty.contact is None


@respx.mock
@pytest.mark.anyio
async def test_lookup_by_thread_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"contact": CONTACT, "match": "email"})
    )
    out = await aclient.contacts.lookup(email="ada@example.com", thread_id="t1")
    assert dict(_last(route).url.params) == {
        "email": "ada@example.com",
        "thread_id": "t1",
    }
    assert out.match == "email"


# -- verification / research selections ---------------------------------------
@respx.mock
def test_request_verification_selection(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200,
            json={
                "affected": 12,
                "action": "verify",
                "queued": True,
                "verifier": "cleanmylist",
                "verifier_label": "CleanMyList",
                "verifier_error": "",
            },
        )
    )
    out = client.contacts.request_verification(
        action="verify", select_all=True, filters={"query": "a"}, exclude=["z"]
    )
    assert _body(route) == {
        "action": "verify",
        "all": True,
        "filters": {"query": "a"},
        "exclude": ["z"],
    }
    assert out.affected == 12
    assert out.verifier == "cleanmylist"
    assert out.verifier_label == "CleanMyList"

    client.contacts.request_verification(action="verify", contacts=["a"])
    assert _body(route) == {"action": "verify", "contacts": ["a"]}


@respx.mock
@pytest.mark.anyio
async def test_request_verification_selection_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200, json={"affected": 1, "action": "verify", "verifier": "builtin"}
        )
    )
    out = await aclient.contacts.request_verification(
        action="verify", campaign_id="camp1"
    )
    assert _body(route) == {"action": "verify", "campaign_id": "camp1"}
    assert out.verifier == "builtin"


@respx.mock
def test_research_batch_selection(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/research/batch").mock(
        return_value=httpx.Response(200, json={"queued": 7})
    )
    out = client.contacts.research_batch(
        select_all=True, filters={"query": "a"}, exclude=["z"], objective="funding"
    )
    assert _body(route) == {
        "all": True,
        "filters": {"query": "a"},
        "exclude": ["z"],
        "objective": "funding",
    }
    assert out.queued == 7

    client.contacts.research_batch(contact_ids=["a", "b"])
    assert _body(route) == {"contact_ids": ["a", "b"]}


@respx.mock
@pytest.mark.anyio
async def test_research_batch_selection_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/research/batch").mock(
        return_value=httpx.Response(200, json={"queued": 2})
    )
    out = await aclient.contacts.research_batch(contact_ids=["a", "b"])
    assert _body(route) == {"contact_ids": ["a", "b"]}
    assert out.queued == 2


# -- model fields added by the server ------------------------------------------
@respx.mock
def test_detail_campaigns_emails_and_commit_fields(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "campaign_id": "c1",
                        "lead_status": "paused",
                        "sender_id": "s1",
                        "sender_email": "me@acme.com",
                        "hold": {"since": "2026-10-01T00:00:00Z", "source": "manual"},
                        "cc": [{"email": "boss@acme.com"}],
                    }
                ]
            },
        )
    )
    state = next(iter(client.contacts.list_campaigns(CONTACT_ID)))
    assert state.lead_status == "paused"
    assert state.sender_email == "me@acme.com"
    assert state.hold is not None
    assert state.hold["source"] == "manual"
    assert state.cc is not None
    assert state.cc[0]["email"] == "boss@acme.com"

    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/emails").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "task_id": "t1",
                        "opened_at": "2026-10-01T10:00:00Z",
                        "machine_opened_at": "2026-10-01T09:00:00Z",
                    }
                ]
            ),
        )
    )
    sent = next(iter(client.contacts.list_emails(CONTACT_ID)))
    assert sent.machine_opened_at == "2026-10-01T09:00:00Z"

    respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(
            200, json={"total": 1, "imported": 1, "segments_pinned": False}
        )
    )
    result = client.contacts.import_commit(
        file=b"email\na@b.com\n", filename="x.csv", import_options={"mapping": []}
    )
    assert result.segments_pinned is False

    respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    prev = client.contacts.import_preview(file=b"email\n", filename="x.csv")
    assert prev.mapping_source == "saved"
    assert prev.inferred_columns == [1]


# -- background imports ---------------------------------------------------------
@respx.mock
def test_imports_lifecycle(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(200, json=_page([IMPORT]))
    )
    items = list(client.contacts.list_imports(limit=10))
    assert _last(listing).url.params["limit"] == "10"
    _check_import(items[0])

    create = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json={**IMPORT, "status": "draft"})
    )
    draft = client.contacts.create_import(file=b"email\na@b.com\n", filename="x.csv")
    request = _last(create)
    assert request.method == "POST"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="x.csv"' in request.content
    assert b"a@b.com" in request.content
    assert draft.status == "draft"

    get = respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(client.contacts.retrieve_import(IMPORT_ID))
    assert _last(get).method == "GET"

    save = respx.patch(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        client.contacts.save_import_draft(
            IMPORT_ID, mapping=MAPPING, dedup="skip", has_header=True
        )
    )
    assert _body(save) == {"mapping": MAPPING, "dedup": "skip", "has_header": True}

    analyze = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    analysis = client.contacts.analyze_import(
        IMPORT_ID, mapping=MAPPING, has_header=True
    )
    assert _body(analyze) == {"mapping": MAPPING, "has_header": True}
    assert analysis.rows == 100
    assert analysis.new == 80
    assert analysis.duplicates_in_file == 4
    assert analysis.conflicts == 1
    assert analysis.problem == "plan limit"
    assert analysis.invalid_samples is not None
    assert analysis.invalid_samples[0]["reason"] == "bad"

    start = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        client.contacts.start_import(
            IMPORT_ID,
            mapping=MAPPING,
            has_header=True,
            dedup="update",
            category_ids=["cat"],
            campaign_ids=["camp"],
            segment_ids=["seg"],
            subscribed_default=False,
        )
    )
    assert _body(start) == {
        "mapping": MAPPING,
        "dedup": "update",
        "has_header": True,
        "category_ids": ["cat"],
        "campaign_ids": ["camp"],
        "segment_ids": ["seg"],
        "subscribed_default": False,
    }
    assert _last(start).headers.get("idempotency-key")

    cancel = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/cancel").mock(
        return_value=httpx.Response(200, json={**IMPORT, "status": "cancelled"})
    )
    assert client.contacts.cancel_import(IMPORT_ID).status == "cancelled"
    assert _last(cancel).method == "POST"

    failed = respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/failed.csv").mock(
        return_value=httpx.Response(
            200,
            content=b"line,email,reason\n4,bad,invalid\n",
            headers={"content-type": "text/csv"},
        )
    )
    assert client.contacts.download_import_failures(IMPORT_ID).startswith(b"line,email")
    assert _last(failed).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_imports_lifecycle_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(200, json=_page([IMPORT]))
    )
    items = [i async for i in aclient.contacts.list_imports(limit=10)]
    assert _last(listing).url.params["limit"] == "10"
    _check_import(items[0])

    create = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json={**IMPORT, "status": "draft"})
    )
    draft = await aclient.contacts.create_import(
        file=b"email\na@b.com\n", filename="x.csv"
    )
    assert b'name="file"; filename="x.csv"' in _last(create).content
    assert draft.status == "draft"

    respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await aclient.contacts.retrieve_import(IMPORT_ID))

    save = respx.patch(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await aclient.contacts.save_import_draft(IMPORT_ID, mapping=MAPPING))
    assert _body(save) == {"mapping": MAPPING}

    analyze = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    analysis = await aclient.contacts.analyze_import(
        IMPORT_ID, mapping=MAPPING, has_header=False
    )
    assert _body(analyze) == {"mapping": MAPPING, "has_header": False}
    assert analysis.existing == 10
    assert analysis.invalid == 5

    start = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        await aclient.contacts.start_import(IMPORT_ID, mapping=MAPPING, has_header=True)
    )
    assert _body(start) == {"mapping": MAPPING, "has_header": True}

    respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/cancel").mock(
        return_value=httpx.Response(200, json={**IMPORT, "status": "cancelled"})
    )
    assert (await aclient.contacts.cancel_import(IMPORT_ID)).status == "cancelled"

    respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/failed.csv").mock(
        return_value=httpx.Response(200, content=b"line,email,reason\n")
    )
    assert (await aclient.contacts.download_import_failures(IMPORT_ID)).startswith(
        b"line"
    )


# -- Salesforce -------------------------------------------------------------------
@respx.mock
def test_salesforce_panel_sync_unlink(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(client.contacts.salesforce(CONTACT_ID))
    assert _last(get).method == "GET"

    sync = respx.post(f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(
        client.contacts.sync_salesforce(
            CONTACT_ID, connection_id=CONN_ID, create_as="contact"
        )
    )
    assert _body(sync) == {"connection_id": CONN_ID, "create_as": "contact"}
    assert _last(sync).headers.get("idempotency-key")

    client.contacts.sync_salesforce(CONTACT_ID)
    assert _body(sync) == {}

    unlink = respx.delete(
        f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/links/{LINK_ID}"
    ).mock(return_value=httpx.Response(204))
    out = client.contacts.unlink_salesforce(CONTACT_ID, LINK_ID)
    assert _last(unlink).method == "DELETE"
    assert out.deleted is None


@respx.mock
@pytest.mark.anyio
async def test_salesforce_panel_sync_unlink_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(await aclient.contacts.salesforce(CONTACT_ID))

    sync = respx.post(f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(await aclient.contacts.sync_salesforce(CONTACT_ID, create_as="lead"))
    assert _body(sync) == {"create_as": "lead"}

    unlink = respx.delete(
        f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/links/{LINK_ID}"
    ).mock(return_value=httpx.Response(204))
    await aclient.contacts.unlink_salesforce(CONTACT_ID, LINK_ID)
    assert _last(unlink).method == "DELETE"
