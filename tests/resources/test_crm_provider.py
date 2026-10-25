"""CRM mode routes (settings, owners, sync, backfill, contacts, lists, bulk tasks)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, page, v  # noqa: F401

VIEW = {
    "provider": "hubspot",
    "linked": True,
    "external_id": "501",
    "url": "https://app.hubspot.com/contacts/1/record/0-1/501",
    "owner": {"external_id": "9", "email": "o@x.com", "user_id": "usr_1"},
    "lifecycle_stage": {"value": "lead", "label": "Lead"},
    "lead_status": {"value": "NEW", "label": "New"},
    "company": {"external_id": "7", "name": "Acme", "domain": "acme.com"},
    "opted_out": False,
    "properties": [{"name": "jobtitle", "label": "Job title", "value": "CTO"}],
    "synced_at": "2026-10-01T00:00:00Z",
}


def _check_view(view: Any) -> None:
    assert view.provider == "hubspot"
    assert view.linked is True
    assert view.external_id == "501"
    assert view.owner["user_id"] == "usr_1"
    assert view.lifecycle_stage["label"] == "Lead"
    assert view.lead_status["value"] == "NEW"
    assert view.company["name"] == "Acme"
    assert view.opted_out is False
    assert view.properties[0]["value"] == "CTO"
    assert view.synced_at == "2026-10-01T00:00:00Z"
    assert view.url.endswith("/501")


@respx.mock
@pytest.mark.anyio
async def test_crm_settings_metadata_owners(dual: Any) -> None:
    c = dual.crm

    settings = {
        "organization_id": "org_1",
        "provider": "pipedrive",
        "connection_id": "conn_1",
        "config": {"create_contacts": True},
        "setup_completed_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-02T00:00:00Z",
        "account": {"name": "Acme", "missing_scopes": ["deals:read"]},
    }
    get = respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=settings)
    )
    got = await v(c.get_settings())
    assert got.provider == "pipedrive"
    assert got.connection_id == "conn_1"
    assert got.config == {"create_contacts": True}
    assert got.account["missing_scopes"] == ["deals:read"]
    assert got.setup_completed_at == "2026-10-01T00:00:00Z"
    assert last(get).method == "GET"

    put = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=settings)
    )
    await v(
        c.update_settings(
            provider="pipedrive",
            connection_id="conn_1",
            config={"create_contacts": True},
            complete_setup=True,
        )
    )
    assert json.loads(last(put).content) == {
        "provider": "pipedrive",
        "connection_id": "conn_1",
        "config": {"create_contacts": True},
        "complete_setup": True,
    }

    meta = respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(
            200,
            json={
                "lifecycle_stages": [{"value": "lead", "label": "Lead"}],
                "lead_statuses": [{"value": "NEW", "label": "New"}],
                "task_types": [{"value": "CALL", "label": "Call"}],
                "properties": [{"name": "jobtitle", "type": "string"}],
                "pipelines": [{"value": "p1", "label": "Sales"}],
            },
        )
    )
    md = await v(c.metadata())
    assert md.lifecycle_stages[0]["label"] == "Lead"
    assert md.lead_statuses[0]["value"] == "NEW"
    assert md.task_types[0]["value"] == "CALL"
    assert md.properties[0]["name"] == "jobtitle"
    assert md.pipelines[0]["label"] == "Sales"
    assert last(meta).url.path == "/v1/crm/metadata"

    owners = respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "external_id": "9",
                        "email": "o@x.com",
                        "first_name": "Olly",
                        "last_name": "Owner",
                        "user_id": "usr_1",
                        "user_pinned": True,
                        "archived": False,
                    }
                ]
            },
        )
    )
    owner = (await items(c.list_owners()))[0]
    assert owner.external_id == "9"
    assert owner.first_name == "Olly"
    assert owner.user_pinned is True
    assert owner.archived is False
    assert last(owners).method == "GET"

    mapped = respx.put(f"{BASE_URL}/crm/owners/9").mock(
        return_value=httpx.Response(204)
    )
    await v(c.map_owner("9", user_id="usr_2"))
    assert json.loads(last(mapped).content) == {"user_id": "usr_2"}
    await v(c.map_owner("9", user_id=None))
    assert json.loads(last(mapped).content) == {"user_id": None}


@respx.mock
@pytest.mark.anyio
async def test_crm_sync_and_backfill(dual: Any) -> None:
    c = dual.crm

    health = respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "pending": 3,
                "failed": 1,
                "done_24h": 40,
                "last_synced_at": "2026-10-01T00:00:00Z",
                "cursors": [{"object_type": "deal", "last_error": ""}],
                "failures": [{"id": "job_1", "kind": "push_deal"}],
                "counts": {"contacts": 10, "deals": 4},
            },
        )
    )
    h = await v(c.sync_health())
    assert (h.pending, h.failed, h.done_24h) == (3, 1, 40)
    assert h.last_synced_at == "2026-10-01T00:00:00Z"
    assert h.cursors[0]["object_type"] == "deal"
    assert h.failures[0]["id"] == "job_1"
    assert h.counts["deals"] == 4
    assert last(health).method == "GET"

    sync = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    await v(c.sync_now())
    assert last(sync).headers["idempotency-key"]

    retry = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert (await v(c.retry_sync_failures(ids=["job_1"]))).affected == 2
    assert json.loads(last(retry).content) == {"ids": ["job_1"]}
    await v(c.retry_sync_failures())
    assert last(retry).content in (b"", b"{}", b"null")

    discard = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 5})
    )
    assert (await v(c.discard_sync_failures(ids=["job_2"]))).affected == 5
    assert json.loads(last(discard).content) == {"ids": ["job_2"]}

    preview = respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 4, "tasks": 6, "notes": 8})
    )
    bp = await v(c.backfill_preview())
    assert (bp.deals, bp.tasks, bp.notes) == (4, 6, 8)
    assert last(preview).method == "GET"

    start = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    await v(c.start_backfill(deals=True, notes=True))
    assert json.loads(last(start).content) == {
        "deals": True,
        "tasks": False,
        "notes": True,
    }
    assert last(start).headers["idempotency-key"]


@respx.mock
@pytest.mark.anyio
async def test_crm_contacts_and_lists(dual: Any) -> None:
    c = dual.crm

    get = respx.get(f"{BASE_URL}/crm/contacts/ct_1").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await v(c.get_contact("ct_1")))
    assert last(get).method == "GET"

    refresh = respx.post(f"{BASE_URL}/crm/contacts/ct_1/refresh").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await v(c.refresh_contact("ct_1")))
    assert last(refresh).headers["idempotency-key"]

    link = respx.post(f"{BASE_URL}/crm/contacts/ct_1/link").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await v(c.link_contact("ct_1")))
    assert last(link).method == "POST"

    update = respx.patch(f"{BASE_URL}/crm/contacts/ct_1").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(
        await v(
            c.update_contact(
                "ct_1",
                owner_external_id="9",
                lifecycle_stage="lead",
                lead_status="NEW",
            )
        )
    )
    assert json.loads(last(update).content) == {
        "owner_external_id": "9",
        "lifecycle_stage": "lead",
        "lead_status": "NEW",
    }

    lists = respx.get(f"{BASE_URL}/crm/lists").mock(
        return_value=httpx.Response(
            200,
            json=page(
                [
                    {
                        "external_id": "l1",
                        "name": "Webinar",
                        "size": 120,
                        "dynamic": True,
                        "updated_at": "2026-10-01",
                    }
                ]
            ),
        )
    )
    crm_list = (await items(c.list_lists(q="web", limit=10)))[0]
    assert (crm_list.external_id, crm_list.name) == ("l1", "Webinar")
    assert crm_list.size == 120
    assert crm_list.dynamic is True
    assert crm_list.updated_at == "2026-10-01"
    params = last(lists).url.params
    assert params["q"] == "web"
    assert params["limit"] == "10"

    pv = {
        "list_name": "Webinar",
        "total": 120,
        "included": 100,
        "skipped": [{"reason": "opted_out", "label": "Opted out", "count": 20}],
        "sample": [{"email": "a@x.com", "first_name": "A", "last_name": "B"}],
        "truncated": True,
    }
    prev = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=pv)
    )
    got = await v(c.preview_list_import(list_id="l1", apply_guards=True))
    assert (got.list_name, got.total, got.included) == ("Webinar", 120, 100)
    assert got.skipped[0]["count"] == 20
    assert got.sample[0]["email"] == "a@x.com"
    assert got.truncated is True
    assert json.loads(last(prev).content) == {"list_id": "l1", "apply_guards": True}

    imp = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(201, json={"import_id": "imp_1", "preview": pv})
    )
    res = await v(c.import_list(list_id="l1"))
    assert res.import_id == "imp_1"
    assert res.preview.included == 100
    assert json.loads(last(imp).content) == {"list_id": "l1", "apply_guards": False}
    assert last(imp).headers["idempotency-key"]


@respx.mock
@pytest.mark.anyio
async def test_crm_bulk_tasks_and_external(dual: Any) -> None:
    c = dual.crm

    patch = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 7})
    )
    assert (
        await v(c.bulk_update_tasks(tasks=["t1", "t2"], status="completed"))
    ).affected == 7
    assert json.loads(last(patch).content) == {
        "tasks": ["t1", "t2"],
        "status": "completed",
    }
    await v(
        c.bulk_update_tasks(
            select_all=True,
            filters={"overdue": True},
            exclude=["t9"],
            priority="high",
        )
    )
    assert json.loads(last(patch).content) == {
        "all": True,
        "filters": {"overdue": True},
        "exclude": ["t9"],
        "priority": "high",
    }

    delete = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 3})
    )
    assert (await v(c.bulk_delete_tasks(["t1"]))).affected == 3
    assert json.loads(last(delete).content) == ["t1"]
    await v(c.bulk_delete_tasks(select_all=True, filters={"statuses": ["pending"]}))
    assert json.loads(last(delete).content) == {
        "all": True,
        "filters": {"statuses": ["pending"]},
    }
    await v(c.bulk_delete_tasks())
    assert json.loads(last(delete).content) == []

    ext = {"provider": "hubspot", "external_id": "55", "url": "https://x/55"}
    respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(
            200,
            json=page(
                [
                    {
                        "id": "pl_1",
                        "external": ext,
                        "stages": [
                            {
                                "id": "st_1",
                                "closed": True,
                                "won": True,
                                "probability": 0.9,
                            }
                        ],
                    }
                ]
            ),
        )
    )
    pipeline = (await items(c.list_pipelines()))[0]
    assert pipeline.external["external_id"] == "55"
    stage = pipeline.stages[0]
    assert (stage.closed, stage.won, stage.probability) == (True, True, 0.9)

    respx.get(f"{BASE_URL}/crm/deals/d_1").mock(
        return_value=httpx.Response(200, json={"id": "d_1", "external": ext})
    )
    assert (await v(c.retrieve_deal("d_1"))).external["provider"] == "hubspot"

    respx.get(f"{BASE_URL}/crm/tasks/t_1").mock(
        return_value=httpx.Response(200, json={"id": "t_1", "external": ext})
    )
    assert (await v(c.retrieve_task("t_1"))).external["url"] == "https://x/55"

    respx.get(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(200, json=page([{"id": "n_1", "external": ext}]))
    )
    note = (await items(dual.contacts.list_notes("ct_1")))[0]
    assert note.external["external_id"] == "55"
