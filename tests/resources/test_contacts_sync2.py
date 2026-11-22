"""Tests for background imports, the Salesforce panel and the contact-shape
changes on the ``contacts`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
IMPORT_ID = "0b6c1f4e-6f5c-4a43-9d58-0e2b8c8f0a11"
CONTACT_ID = "5d1c7e0a-35f5-4e7e-8a1b-2f43c0a3d001"
LINK_ID = "9a1f7c33-5a0e-4f3b-9d0c-77a1e2c4b002"
CONN_ID = "c1c1c1c1-0000-4000-8000-000000000001"

MAPPING = [
    {"index": 0, "target": "email"},
    {"index": 1, "target": "custom", "custom_key": "plan"},
]

IMPORT: dict[str, Any] = {
    "id": IMPORT_ID,
    "organization_id": "0f0f0f0f-0000-4000-8000-000000000009",
    "created_by": "7d7d7d7d-0000-4000-8000-000000000003",
    "filename": "leads.csv",
    "format": "csv",
    "status": "running",
    "has_header": True,
    "columns": ["Email", "Plan"],
    "total": 1200,
    "processed": 300,
    "imported": 250,
    "updated": 20,
    "skipped": 20,
    "failed": 10,
    "options": {"mapping": MAPPING, "dedup": "update", "has_header": True},
    "quality": {
        "malformed": 3,
        "disposable": 4,
        "role": 12,
        "bad_share_pct": 1.5,
        "flagged": False,
        "summary": "Looks clean",
    },
    "segments_pinned": True,
    "notes": ["2 rows had no email"],
    "created_at": "2026-11-01T10:00:00Z",
    "updated_at": "2026-11-01T10:05:00Z",
    "started_at": "2026-11-01T10:01:00Z",
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
            {"filled": 1200, "distinct": 1200, "samples": ["a@example.com"]},
            {"filled": 900, "distinct": 3, "samples": ["pro", "free"]},
        ],
        "mapping_source": "saved",
    },
    "failures": [
        {
            "line": 7,
            "email": "bad",
            "values": ["bad", "pro"],
            "reason": "not an email address",
        }
    ],
}

ANALYSIS = {
    "rows": 1200,
    "new": 1000,
    "existing": 150,
    "duplicates_in_file": 20,
    "invalid": 25,
    "conflicts": 5,
    "invalid_samples": [{"line": 7, "email": "bad", "reason": "not an email"}],
    "quality": {"malformed": 3, "disposable": 4, "role": 12, "flagged": False},
    "problem": "Your plan allows 1,000 more contacts",
}

PANEL = {
    "connections": [
        {
            "id": CONN_ID,
            "label": "Prod org",
            "environment": "production",
            "instance_url": "https://acme.my.salesforce.com",
        }
    ],
    "records": [
        {
            "link_id": LINK_ID,
            "connection_id": CONN_ID,
            "connection_label": "Prod org",
            "object": "Lead",
            "id": "00Q5e00000AbCdEFGH",
            "url": "https://acme.my.salesforce.com/00Q5e00000AbCdEFGH",
            "name": "Ada Lovelace",
            "company": "Analytical Engines",
            "email": "ada@example.com",
            "status": "Working",
            "owner": {"id": "0055e00000XyZ", "name": "Sam Rep"},
            "is_converted": False,
            "opted_out": False,
            "opportunities": [
                {"id": "0065e1", "name": "Big deal", "stage": "Prospecting"}
            ],
            "tasks": [
                {"id": "00T5e1", "subject": "Email: Hello", "from_warmbly": True}
            ],
            "linked_by": "email",
            "last_synced_at": "2026-11-01T10:00:00Z",
            "sync": {"pending": 0, "failed": 1, "synced": 4},
            "stale": False,
        }
    ],
    "can_sync": True,
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


def _page(data: list[dict], cursor: str | None = None) -> dict:
    return {
        "data": data,
        "pagination": {
            "next_cursor": cursor,
            "has_more": cursor is not None,
            "total": len(data),
        },
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _check_import(imp: Any) -> None:
    assert imp.id == IMPORT_ID
    assert imp.status == "running"
    assert imp.total == 1200
    assert imp.quality.bad_share_pct == 1.5
    assert imp.segments_pinned is True
    assert imp.notes == ["2 rows had no email"]
    assert imp.options["dedup"] == "update"
    assert imp.preview.mapping_source == "saved"
    assert list(imp.preview.inferred_columns) == [1]
    assert imp.preview.column_stats[1].distinct == 3
    assert imp.preview.column_stats[1].samples == ["pro", "free"]
    assert imp.failures[0].line == 7
    assert imp.failures[0].values == ["bad", "pro"]


def _check_analysis(a: Any) -> None:
    assert (a.rows, a.new, a.existing, a.duplicates_in_file) == (1200, 1000, 150, 20)
    assert (a.invalid, a.conflicts) == (25, 5)
    assert a.invalid_samples[0].reason == "not an email"
    assert a.quality.role == 12
    assert a.problem == "Your plan allows 1,000 more contacts"


def _check_panel(p: Any) -> None:
    assert p.can_sync is True
    assert p.connections[0].instance_url == "https://acme.my.salesforce.com"
    rec = p.records[0]
    assert rec.link_id == LINK_ID
    assert rec.object == "Lead"
    assert rec.owner["name"] == "Sam Rep"
    assert rec.opportunities[0]["stage"] == "Prospecting"
    assert rec.tasks[0]["from_warmbly"] is True
    assert rec.sync["failed"] == 1


START_BODY = {
    "mapping": MAPPING,
    "dedup": "update",
    "has_header": True,
    "category_ids": ["cat1"],
    "campaign_ids": ["camp1"],
    "segment_ids": ["seg1"],
    "skip_active_in_other_campaigns": True,
    "subscribed_default": False,
}


# -- background imports -------------------------------------------------------


@respx.mock
def test_imports_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/contacts/imports").mock(
        side_effect=[
            httpx.Response(200, json=_page([IMPORT], cursor="c2")),
            httpx.Response(200, json=_page([{"id": "second"}])),
        ]
    )
    assert [i.id for i in client.contacts.list_imports(limit=1)] == [
        IMPORT_ID,
        "second",
    ]
    assert listing.calls[0].request.url.params["limit"] == "1"
    assert listing.calls[1].request.url.params["cursor"] == "c2"

    create = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json=IMPORT)
    )
    _check_import(client.contacts.create_import(file=b"Email,Plan\n", filename="l.csv"))
    request = _last(create)
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'filename="l.csv"' in request.content
    assert b"Email,Plan" in request.content

    get = respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(client.contacts.retrieve_import(IMPORT_ID))
    assert _last(get).method == "GET"

    patch = respx.patch(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        client.contacts.save_import_draft(
            IMPORT_ID,
            mapping=MAPPING,
            dedup="update",
            has_header=True,
            category_ids=["cat1"],
            campaign_ids=["camp1"],
            segment_ids=["seg1"],
            skip_active_in_other_campaigns=True,
            subscribed_default=False,
        )
    )
    assert json.loads(_last(patch).content) == START_BODY

    analyze = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    _check_analysis(
        client.contacts.analyze_import(IMPORT_ID, mapping=MAPPING, has_header=True)
    )
    assert json.loads(_last(analyze).content) == {
        "mapping": MAPPING,
        "has_header": True,
    }

    start = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        client.contacts.start_import(
            IMPORT_ID,
            mapping=MAPPING,
            dedup="update",
            has_header=True,
            category_ids=["cat1"],
            campaign_ids=["camp1"],
            segment_ids=["seg1"],
            skip_active_in_other_campaigns=True,
            subscribed_default=False,
        )
    )
    assert json.loads(_last(start).content) == START_BODY
    assert "idempotency-key" in _last(start).headers
    client.contacts.start_import(IMPORT_ID)
    assert json.loads(_last(start).content) == {}

    cancel = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/cancel").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(client.contacts.cancel_import(IMPORT_ID))
    assert _last(cancel).method == "POST"

    failed = respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/failed.csv").mock(
        return_value=httpx.Response(
            200,
            content=b"line,email,reason\n7,bad,not an email\n",
            headers={"content-type": "text/csv; charset=utf-8"},
        )
    )
    assert client.contacts.import_failures(IMPORT_ID).startswith(b"line,email")
    assert _last(failed).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_imports_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/contacts/imports").mock(
        side_effect=[
            httpx.Response(200, json=_page([IMPORT], cursor="c2")),
            httpx.Response(200, json=_page([{"id": "second"}])),
        ]
    )
    ids = [i.id async for i in aclient.contacts.list_imports(limit=1)]
    assert ids == [IMPORT_ID, "second"]
    assert listing.calls[1].request.url.params["cursor"] == "c2"

    create = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json=IMPORT)
    )
    _check_import(
        await aclient.contacts.create_import(file=b"Email,Plan\n", filename="l.csv")
    )
    assert _last(create).headers["content-type"].startswith("multipart/form-data")

    respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await aclient.contacts.retrieve_import(IMPORT_ID))

    patch = respx.patch(f"{BASE_URL}/contacts/imports/{IMPORT_ID}").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        await aclient.contacts.save_import_draft(
            IMPORT_ID,
            mapping=MAPPING,
            dedup="update",
            has_header=True,
            category_ids=["cat1"],
            campaign_ids=["camp1"],
            segment_ids=["seg1"],
            skip_active_in_other_campaigns=True,
            subscribed_default=False,
        )
    )
    assert json.loads(_last(patch).content) == START_BODY

    analyze = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    _check_analysis(
        await aclient.contacts.analyze_import(
            IMPORT_ID, mapping=MAPPING, has_header=True
        )
    )
    assert json.loads(_last(analyze).content)["has_header"] is True

    start = respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        await aclient.contacts.start_import(
            IMPORT_ID,
            mapping=MAPPING,
            dedup="update",
            has_header=True,
            category_ids=["cat1"],
            campaign_ids=["camp1"],
            segment_ids=["seg1"],
            skip_active_in_other_campaigns=True,
            subscribed_default=False,
        )
    )
    assert json.loads(_last(start).content) == START_BODY
    await aclient.contacts.start_import(IMPORT_ID)
    assert json.loads(_last(start).content) == {}

    respx.post(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/cancel").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await aclient.contacts.cancel_import(IMPORT_ID))

    respx.get(f"{BASE_URL}/contacts/imports/{IMPORT_ID}/failed.csv").mock(
        return_value=httpx.Response(200, content=b"line,email,reason\n")
    )
    assert await aclient.contacts.import_failures(IMPORT_ID) == b"line,email,reason\n"


# -- Salesforce panel ---------------------------------------------------------


@respx.mock
def test_contact_salesforce_sync(client: Warmbly) -> None:
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
            CONTACT_ID, connection_id=CONN_ID, create_as="lead"
        )
    )
    assert json.loads(_last(sync).content) == {
        "connection_id": CONN_ID,
        "create_as": "lead",
    }
    assert "idempotency-key" in _last(sync).headers
    client.contacts.sync_salesforce(CONTACT_ID)
    assert json.loads(_last(sync).content) == {}

    unlink = respx.delete(
        f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/links/{LINK_ID}"
    ).mock(return_value=httpx.Response(204))
    assert client.contacts.unlink_salesforce(CONTACT_ID, LINK_ID).deleted is None
    assert _last(unlink).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_contact_salesforce_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(await aclient.contacts.salesforce(CONTACT_ID))

    sync = respx.post(f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(
        await aclient.contacts.sync_salesforce(
            CONTACT_ID, connection_id=CONN_ID, create_as="contact"
        )
    )
    assert json.loads(_last(sync).content) == {
        "connection_id": CONN_ID,
        "create_as": "contact",
    }

    unlink = respx.delete(
        f"{BASE_URL}/contacts/{CONTACT_ID}/salesforce/links/{LINK_ID}"
    ).mock(return_value=httpx.Response(204))
    result = await aclient.contacts.unlink_salesforce(CONTACT_ID, LINK_ID)
    assert result.deleted is None
    assert _last(unlink).url.path.endswith(f"/links/{LINK_ID}")


# -- lookup, selections, update, search --------------------------------------

LOOKUP = {
    "contact": {
        "id": CONTACT_ID,
        "email": "ada@example.com",
        "mail_host": "google_workspace",
        "esp_provider": "gmail",
        "verification_requested_at": "2026-11-01T09:00:00Z",
        "outreach": {
            "sent": 4,
            "opened": 2,
            "clicked": 1,
            "replied": 1,
            "bounced": 0,
            "last_sent_at": "2026-11-01T09:30:00Z",
            "last_replied_at": "2026-11-02T09:30:00Z",
        },
    },
    "match": "thread",
}


@respx.mock
def test_lookup_and_selection_sync(client: Warmbly) -> None:
    lookup = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json=LOOKUP)
    )
    result = client.contacts.lookup(thread_id="t-1", account_id="acc-1")
    assert result.match == "thread"
    assert result.contact is not None
    assert result.contact.mail_host == "google_workspace"
    assert result.contact.verification_requested_at == "2026-11-01T09:00:00Z"
    assert result.contact.outreach.replied == 1
    assert result.contact.outreach.last_replied_at == "2026-11-02T09:30:00Z"
    params = _last(lookup).url.params
    assert params["thread_id"] == "t-1"
    assert params["account_id"] == "acc-1"
    assert "email" not in params
    client.contacts.lookup(email="Ada <ada@example.com>")
    assert _last(lookup).url.params["email"] == "Ada <ada@example.com>"

    bulk = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 3})
    )
    client.contacts.bulk_update(
        select_all=True,
        filters={"query": "acme"},
        exclude=["c9"],
        add_campaigns=["camp1"],
        skip_active_in_other_campaigns=True,
    )
    assert json.loads(_last(bulk).content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c9"],
        "skip_active_in_other_campaigns": True,
        "add_campaigns": ["camp1"],
    }
    client.contacts.bulk_update(contacts=("c1", "c2"), subscribe=False)
    assert json.loads(_last(bulk).content) == {
        "contacts": ["c1", "c2"],
        "subscribe": False,
    }

    delete = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    client.contacts.bulk_delete(["c1"])
    assert json.loads(_last(delete).content) == ["c1"]
    client.contacts.bulk_delete(select_all=True, filters={"query": "x"}, exclude=["c2"])
    assert json.loads(_last(delete).content) == {
        "contacts": [],
        "all": True,
        "filters": {"query": "x"},
        "exclude": ["c2"],
    }
    client.contacts.bulk_delete(["c1", "c2"], exclude=["c2"])
    assert json.loads(_last(delete).content) == {
        "contacts": ["c1", "c2"],
        "exclude": ["c2"],
    }
    client.contacts.bulk_delete(["c1"], select_all=True)
    assert json.loads(_last(delete).content) == {"contacts": ["c1"], "all": True}

    update = respx.patch(f"{BASE_URL}/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json={"id": CONTACT_ID})
    )
    client.contacts.update(CONTACT_ID, email="new@example.com")
    assert json.loads(_last(update).content) == {"email": "new@example.com"}

    search = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    client.contacts.search(mail_hosts=["", "google_workspace"], sort_by="custom:plan")
    assert json.loads(_last(search).content) == {
        "mail_hosts": ["", "google_workspace"],
        "sort_by": "custom:plan",
    }


@respx.mock
@pytest.mark.anyio
async def test_lookup_and_selection_async(aclient: AsyncWarmbly) -> None:
    lookup = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json=LOOKUP)
    )
    result = await aclient.contacts.lookup(thread_id="t-1", account_id="acc-1")
    assert result.match == "thread"
    assert result.contact is not None
    assert result.contact.outreach.sent == 4
    assert _last(lookup).url.params["account_id"] == "acc-1"

    bulk = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 3})
    )
    await aclient.contacts.bulk_update(
        select_all=True, filters={"query": "acme"}, exclude=["c9"]
    )
    assert json.loads(_last(bulk).content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c9"],
    }
    await aclient.contacts.bulk_update(contacts=["c1"])
    assert json.loads(_last(bulk).content) == {"contacts": ["c1"]}

    delete = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    await aclient.contacts.bulk_delete(["c1"])
    assert json.loads(_last(delete).content) == ["c1"]
    await aclient.contacts.bulk_delete(select_all=True, filters={"query": "x"})
    assert json.loads(_last(delete).content) == {
        "contacts": [],
        "all": True,
        "filters": {"query": "x"},
    }

    update = respx.patch(f"{BASE_URL}/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json={"id": CONTACT_ID})
    )
    await aclient.contacts.update(CONTACT_ID, email="new@example.com")
    assert json.loads(_last(update).content) == {"email": "new@example.com"}

    search = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    await aclient.contacts.search(mail_hosts=["outlook"])
    assert json.loads(_last(search).content) == {"mail_hosts": ["outlook"]}


# -- changed read shapes ------------------------------------------------------


@respx.mock
def test_changed_shapes_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "campaign_id": "camp1",
                        "sender_id": "mb1",
                        "sender_email": "me@acme.test",
                        "follow_up_sender": "same_domain",
                        "hold": {
                            "since": "2026-11-01T00:00:00Z",
                            "until": "2026-11-09T00:00:00Z",
                            "reason": "On leave",
                            "source": "out_of_office",
                        },
                        "cc": [{"contact_id": "c2", "email": "boss@example.com"}],
                    }
                ]
            ),
        )
    )
    state = next(iter(client.contacts.list_campaigns(CONTACT_ID)))
    assert state.sender_email == "me@acme.test"
    assert state.follow_up_sender == "same_domain"
    assert state.hold.source == "out_of_office"
    assert state.hold.until == "2026-11-09T00:00:00Z"
    assert state.cc[0]["email"] == "boss@example.com"

    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/emails").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [{"task_id": "t1", "machine_opened_at": "2026-11-01T01:00:00Z"}]
            ),
        )
    )
    sent = next(iter(client.contacts.list_emails(CONTACT_ID)))
    assert sent.machine_opened_at == "2026-11-01T01:00:00Z"

    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/timeline").mock(
        return_value=httpx.Response(
            200,
            json=_page([{"type": "email_bounced", "bounce_cause": "mailbox_full"}]),
        )
    )
    entry = next(iter(client.contacts.timeline(CONTACT_ID)))
    assert entry.bounce_cause == "mailbox_full"

    respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200,
            json={
                "affected": 3,
                "action": "verify",
                "queued": True,
                "verifier": "millionverifier",
                "verifier_label": "MillionVerifier",
                "verifier_error": "out of credits",
            },
        )
    )
    verdict = client.contacts.request_verification(action="verify", contacts=["c1"])
    assert verdict.verifier_label == "MillionVerifier"
    assert verdict.verifier_error == "out of credits"

    respx.get(f"{BASE_URL}/contacts/{CONTACT_ID}/notes").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "n1",
                        "external": {
                            "provider": "hubspot",
                            "external_id": "991",
                            "url": "https://app.hubspot.com/n/991",
                            "synced_at": "2026-11-01T00:00:00Z",
                        },
                    }
                ]
            ),
        )
    )
    note = next(iter(client.contacts.list_notes(CONTACT_ID)))
    assert note.external.provider == "hubspot"
    assert note.external.external_id == "991"

    respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "filename": "a.csv",
                "inferred_columns": [2],
                "column_stats": [{"filled": 1, "distinct": 1, "samples": ["x"]}],
                "mapping_source": "suggested",
            },
        )
    )
    preview = client.contacts.import_preview(file=b"a", filename="a.csv")
    assert list(preview.inferred_columns) == [2]
    assert preview.column_stats[0].filled == 1
    assert preview.mapping_source == "suggested"

    respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(200, json={"imported": 2, "segments_pinned": False})
    )
    done = client.contacts.import_commit(file=b"a", filename="a.csv", import_options={})
    assert done.segments_pinned is False
