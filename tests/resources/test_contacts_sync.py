"""Contacts: staged imports, Salesforce panel, selections, and changed shapes."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, page, v  # noqa: F401

IMPORT = {
    "id": "imp_1",
    "organization_id": "org_1",
    "created_by": "usr_1",
    "filename": "leads.csv",
    "format": "csv",
    "status": "running",
    "has_header": True,
    "columns": ["Email", "Name"],
    "total": 100,
    "processed": 40,
    "imported": 30,
    "updated": 5,
    "skipped": 3,
    "failed": 2,
    "options": {"dedup": "update"},
    "quality": {"malformed": 1},
    "segments_pinned": True,
    "notes": ["one note"],
    "created_at": "2026-10-01T00:00:00Z",
    "started_at": "2026-10-01T00:01:00Z",
    "preview": {
        "filename": "leads.csv",
        "columns": ["Email", "Name"],
        "inferred_columns": [1],
        "column_stats": [{"filled": 99, "distinct": 98, "samples": ["a@x.com"]}],
        "mapping_source": "saved",
    },
    "failures": [{"line": 7, "email": "bad", "reason": "invalid address"}],
}

PANEL = {
    "connections": [{"id": "conn_1", "label": "Prod", "environment": "production"}],
    "records": [{"link_id": "lnk_1", "object": "Lead", "name": "Ada"}],
    "can_sync": True,
}


def _check_import(imp: Any) -> None:
    assert imp.id == "imp_1"
    assert imp.status == "running"
    assert imp.total == 100
    assert imp.processed == 40
    assert imp.segments_pinned is True
    assert list(imp.notes) == ["one note"]
    assert imp.preview.inferred_columns == [1]
    assert imp.preview.column_stats[0]["filled"] == 99
    assert imp.preview.mapping_source == "saved"
    assert imp.failures[0]["line"] == 7
    assert imp.options == {"dedup": "update"}


@respx.mock
@pytest.mark.anyio
async def test_staged_imports(dual: Any) -> None:
    c = dual.contacts

    create = respx.post(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(201, json=IMPORT)
    )
    _check_import(
        await v(c.create_import(file=b"email\na@x.com\n", filename="leads.csv"))
    )
    req = last(create)
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b'filename="leads.csv"' in req.content
    assert b"a@x.com" in req.content
    # A file upload carries no idempotency key (see the base client).
    assert "idempotency-key" not in req.headers

    listing = respx.get(f"{BASE_URL}/contacts/imports").mock(
        return_value=httpx.Response(200, json=page([IMPORT]))
    )
    got = await items(c.list_imports(limit=20))
    _check_import(got[0])
    assert last(listing).url.params["limit"] == "20"

    get = respx.get(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await v(c.retrieve_import("imp_1")))
    assert last(get).method == "GET"

    save = respx.patch(f"{BASE_URL}/contacts/imports/imp_1").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(
        await v(c.save_import_draft("imp_1", import_options={"dedup": "update"}))
    )
    assert json.loads(last(save).content) == {"dedup": "update"}

    analyze = respx.post(f"{BASE_URL}/contacts/imports/imp_1/analyze").mock(
        return_value=httpx.Response(
            200,
            json={
                "rows": 100,
                "new": 60,
                "existing": 30,
                "duplicates_in_file": 4,
                "invalid": 5,
                "conflicts": 1,
                "invalid_samples": [{"line": 3, "reason": "no address"}],
                "quality": {"flagged": False},
                "problem": "plan limit",
            },
        )
    )
    an = await v(c.analyze_import("imp_1", mapping=[{"index": 0, "target": "email"}]))
    assert (an.rows, an.new, an.existing, an.duplicates_in_file) == (100, 60, 30, 4)
    assert (an.invalid, an.conflicts, an.problem) == (5, 1, "plan limit")
    assert an.invalid_samples[0]["line"] == 3
    assert an.quality == {"flagged": False}
    assert json.loads(last(analyze).content) == {
        "mapping": [{"index": 0, "target": "email"}],
        "has_header": True,
    }
    assert last(analyze).headers["idempotency-key"]

    start = respx.post(f"{BASE_URL}/contacts/imports/imp_1/start").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await v(c.start_import("imp_1", import_options={"dedup": "skip"})))
    assert json.loads(last(start).content) == {"dedup": "skip"}
    assert last(start).headers["idempotency-key"]

    cancel = respx.post(f"{BASE_URL}/contacts/imports/imp_1/cancel").mock(
        return_value=httpx.Response(200, json=IMPORT)
    )
    _check_import(await v(c.cancel_import("imp_1")))
    assert last(cancel).method == "POST"

    failed = respx.get(f"{BASE_URL}/contacts/imports/imp_1/failed.csv").mock(
        return_value=httpx.Response(
            200, content=b"line,reason\n7,bad\n", headers={"content-type": "text/csv"}
        )
    )
    assert await v(c.download_import_failures("imp_1")) == b"line,reason\n7,bad\n"
    assert last(failed).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_contact_salesforce(dual: Any) -> None:
    c = dual.contacts

    get = respx.get(f"{BASE_URL}/contacts/ct_1/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    panel = await v(c.get_salesforce("ct_1"))
    assert panel.can_sync is True
    assert panel.connections[0]["label"] == "Prod"
    assert panel.records[0]["object"] == "Lead"
    assert last(get).method == "GET"

    sync = respx.post(f"{BASE_URL}/contacts/ct_1/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    panel = await v(c.sync_salesforce("ct_1", connection_id="conn_1", create_as="lead"))
    assert panel.records[0]["link_id"] == "lnk_1"
    assert json.loads(last(sync).content) == {
        "connection_id": "conn_1",
        "create_as": "lead",
    }
    assert last(sync).headers["idempotency-key"]

    unlink = respx.delete(f"{BASE_URL}/contacts/ct_1/salesforce/links/lnk_1").mock(
        return_value=httpx.Response(204)
    )
    await v(c.unlink_salesforce("ct_1", "lnk_1"))
    assert last(unlink).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_contact_shapes_and_selection(dual: Any) -> None:
    c = dual.contacts

    contact = {
        "id": "ct_1",
        "email": "a@x.com",
        "verification_requested_at": "2026-10-02T00:00:00Z",
        "mail_host": "google_workspace",
        "esp_provider": "gmail",
        "outreach": {"sent": 3, "opened": 2, "last_sent_at": "2026-10-01T00:00:00Z"},
    }
    search = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json={**page([contact]), "counts": {}})
    )
    res = await v(c.search(mail_hosts=["google_workspace", ""], sort_by="custom:tier"))
    row = res.data[0]
    assert row.mail_host == "google_workspace"
    assert row.verification_requested_at == "2026-10-02T00:00:00Z"
    assert row.outreach["sent"] == 3
    assert json.loads(last(search).content) == {
        "mail_hosts": ["google_workspace", ""],
        "sort_by": "custom:tier",
    }

    lookup = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"contact": contact, "match": "thread"})
    )
    found = await v(c.lookup(thread_id="th_1", account_id="acc_1"))
    assert found.match == "thread"
    assert found.contact.id == "ct_1"
    params = last(lookup).url.params
    assert params["thread_id"] == "th_1"
    assert params["account_id"] == "acc_1"
    assert "email" not in params

    update = respx.patch(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json=contact)
    )
    await v(c.update("ct_1", email="b@x.com"))
    assert json.loads(last(update).content) == {"email": "b@x.com"}

    bulk = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 120})
    )
    out = await v(
        c.bulk_update(
            select_all=True,
            filters={"query": "acme"},
            exclude=["ct_9"],
            subscribe=False,
        )
    )
    assert out.updated == 120
    assert json.loads(last(bulk).content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["ct_9"],
        "subscribe": False,
    }

    delete = respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    await v(c.bulk_delete(select_all=True, filters={"query": "acme"}))
    assert json.loads(last(delete).content) == {
        "all": True,
        "filters": {"query": "acme"},
    }
    await v(c.bulk_delete(["a", "b"]))
    assert json.loads(last(delete).content) == ["a", "b"]
    await v(c.bulk_delete())
    assert json.loads(last(delete).content) == []

    verify = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200,
            json={
                "affected": 12,
                "action": "verify",
                "queued": True,
                "verifier": "builtin",
                "verifier_label": "Built-in",
                "verifier_error": "provider has no credits",
            },
        )
    )
    res2 = await v(c.request_verification(action="verify", select_all=True, filters={}))
    assert res2.verifier == "builtin"
    assert res2.verifier_label == "Built-in"
    assert res2.verifier_error == "provider has no credits"
    assert json.loads(last(verify).content) == {
        "action": "verify",
        "all": True,
        "filters": {},
    }

    states = respx.get(f"{BASE_URL}/contacts/ct_1/campaigns").mock(
        return_value=httpx.Response(
            200,
            json=page(
                [
                    {
                        "campaign_id": "cmp_1",
                        "lead_status": "paused",
                        "sender_id": "acc_1",
                        "sender_email": "me@x.com",
                        "hold": {"since": "2026-10-01T00:00:00Z", "source": "manual"},
                        "cc": [{"contact_id": "ct_2"}],
                    }
                ]
            ),
        )
    )
    state = (await items(c.list_campaigns("ct_1")))[0]
    assert state.lead_status == "paused"
    assert state.sender_email == "me@x.com"
    assert state.hold["source"] == "manual"
    assert state.cc[0]["contact_id"] == "ct_2"
    assert last(states).method == "GET"

    sent = respx.get(f"{BASE_URL}/contacts/ct_1/emails").mock(
        return_value=httpx.Response(
            200,
            json=page(
                [{"task_id": "t_1", "machine_opened_at": "2026-10-01T00:00:00Z"}]
            ),
        )
    )
    mail = (await items(c.list_emails("ct_1")))[0]
    assert mail.machine_opened_at == "2026-10-01T00:00:00Z"
    assert last(sent).method == "GET"

    commit = respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(200, json={"total": 1, "segments_pinned": False})
    )
    result = await v(
        c.import_commit(file=b"x", filename="f.csv", import_options={"dedup": "skip"})
    )
    assert result.segments_pinned is False
    assert last(commit).method == "POST"


@respx.mock
@pytest.mark.anyio
async def test_research_batch_selection(dual: Any) -> None:
    c = dual.contacts
    batch = respx.post(f"{BASE_URL}/contacts/research/batch").mock(
        return_value=httpx.Response(200, json={"queued": 12})
    )
    assert (await v(c.research_batch(contact_ids=["a", "b"]))).queued == 12
    assert json.loads(last(batch).content) == {"contact_ids": ["a", "b"]}
    await v(
        c.research_batch(
            select_all=True,
            filters={"query": "acme"},
            exclude=["z"],
            objective="find a hook",
        )
    )
    assert json.loads(last(batch).content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["z"],
        "objective": "find a hook",
    }
    assert last(batch).headers["idempotency-key"]
