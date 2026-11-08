"""Tests for CRM mode (HubSpot, Pipedrive) and the bulk task actions on the
``crm`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CONTACT_ID = "5d1c7e0a-35f5-4e7e-8a1b-2f43c0a3d001"
USER_ID = "7d7d7d7d-0000-4000-8000-000000000003"

SETTINGS = {
    "organization_id": "0f0f0f0f-0000-4000-8000-000000000009",
    "provider": "hubspot",
    "connection_id": "c1c1c1c1-0000-4000-8000-000000000001",
    "config": {
        "activity": {"sent": True, "replies": True, "opens": False},
        "create_contacts": True,
        "field_map": {"first_name": "firstname"},
        "field_direction": {"first_name": "both"},
        "for": "hubspot",
    },
    "setup_completed_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-02T00:00:00Z",
    "account": {
        "external_id": "4421",
        "name": "Acme Portal",
        "app_url": "https://app.hubspot.com/contacts/4421",
        "status": "connected",
        "health": "ok",
        "missing_scopes": ["crm.objects.deals.write"],
    },
}

METADATA = {
    "lifecycle_stages": [{"value": "lead", "label": "Lead"}],
    "lead_statuses": [{"value": "NEW", "label": "New"}],
    "task_types": [{"value": "CALL", "label": "Call"}],
    "properties": [
        {
            "name": "firstname",
            "label": "First name",
            "type": "string",
            "group_name": "contactinformation",
            "read_only": False,
        }
    ],
    "pipelines": [{"value": "default", "label": "Sales"}],
}

OWNER = {
    "external_id": "1234",
    "email": "sam@acme.test",
    "first_name": "Sam",
    "last_name": "Rep",
    "user_id": USER_ID,
    "user_pinned": True,
    "archived": False,
}

HEALTH = {
    "pending": 3,
    "failed": 1,
    "done_24h": 120,
    "last_synced_at": "2026-11-08T08:00:00Z",
    "cursors": [
        {"object_type": "deal", "cursor_at": "2026-11-08T07:00:00Z", "last_error": ""}
    ],
    "failures": [
        {
            "id": "j1",
            "provider": "hubspot",
            "kind": "push_deal",
            "subject": "deal 9",
            "status": "failed",
            "attempts": 5,
            "last_error": "rate limited",
        }
    ],
    "counts": {"contacts": 10, "deals": 4, "tasks": 2, "pipelines": 1, "owners": 3},
}

VIEW = {
    "provider": "hubspot",
    "linked": True,
    "external_id": "551",
    "url": "https://app.hubspot.com/contacts/4421/record/0-1/551",
    "owner": OWNER,
    "lifecycle_stage": {"value": "lead", "label": "Lead"},
    "lead_status": {"value": "NEW", "label": "New"},
    "company": {"external_id": "77", "name": "Analytical Engines", "domain": "ae.test"},
    "opted_out": False,
    "properties": [{"name": "firstname", "label": "First name", "value": "Ada"}],
    "synced_at": "2026-11-08T08:00:00Z",
}

LIST = {
    "external_id": "42",
    "name": "Warm leads",
    "size": 311,
    "dynamic": True,
    "updated_at": "2026-11-01T00:00:00Z",
}

IMPORT_PREVIEW = {
    "list_name": "Warm leads",
    "total": 311,
    "included": 280,
    "skipped": [{"reason": "customer", "label": "Already a customer", "count": 31}],
    "sample": [
        {
            "email": "ada@example.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "company": "Analytical Engines",
        }
    ],
    "truncated": False,
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


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


def _check_settings(s: Any) -> None:
    assert s.provider == "hubspot"
    assert s.config["field_map"] == {"first_name": "firstname"}
    assert s.account.name == "Acme Portal"
    assert list(s.account.missing_scopes) == ["crm.objects.deals.write"]
    assert s.setup_completed_at == "2026-10-01T00:00:00Z"


def _check_metadata(m: Any) -> None:
    assert m.lifecycle_stages[0]["label"] == "Lead"
    assert m.properties[0]["group_name"] == "contactinformation"
    assert m.pipelines[0]["value"] == "default"


def _check_health(h: Any) -> None:
    assert (h.pending, h.failed, h.done_24h) == (3, 1, 120)
    assert h.cursors[0]["object_type"] == "deal"
    assert h.failures[0]["last_error"] == "rate limited"
    assert h.counts["owners"] == 3


def _check_view(v: Any) -> None:
    assert v.linked is True
    assert v.owner["email"] == "sam@acme.test"
    assert v.lead_status["value"] == "NEW"
    assert v.company["domain"] == "ae.test"
    assert v.properties[0]["value"] == "Ada"


def _check_preview(p: Any) -> None:
    assert (p.total, p.included) == (311, 280)
    assert p.skipped[0]["count"] == 31
    assert p.sample[0]["email"] == "ada@example.com"
    assert p.truncated is False


def _check_owner(o: Any) -> None:
    assert o.external_id == "1234"
    assert o.user_pinned is True
    assert o.user_id == USER_ID


# -- CRM mode -----------------------------------------------------------------


@respx.mock
def test_crm_mode_sync(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(client.crm.settings())
    assert _last(get).method == "GET"

    put = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(
        client.crm.update_settings(
            provider="hubspot",
            connection_id="conn1",
            config={"create_contacts": True},
            complete_setup=True,
        )
    )
    assert _body(put) == {
        "provider": "hubspot",
        "connection_id": "conn1",
        "config": {"create_contacts": True},
        "complete_setup": True,
    }
    client.crm.update_settings(provider="native")
    assert _body(put) == {"provider": "native"}

    respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    _check_metadata(client.crm.metadata())

    respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(200, json={"data": [OWNER]})
    )
    _check_owner(next(iter(client.crm.list_owners())))

    owner = respx.put(f"{BASE_URL}/crm/owners/1234").mock(
        return_value=httpx.Response(204)
    )
    assert client.crm.map_owner("1234", user_id=USER_ID) is None
    assert _body(owner) == {"user_id": USER_ID}
    client.crm.map_owner("1234", user_id=None)
    assert _body(owner) == {"user_id": None}

    respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(200, json=HEALTH)
    )
    _check_health(client.crm.sync_health())

    sync = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    assert client.crm.sync_now() is None
    assert _last(sync).method == "POST"

    retry = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert client.crm.retry_sync_failures(ids=["j1", "j2"]).affected == 2
    assert _body(retry) == {"ids": ["j1", "j2"]}
    assert client.crm.retry_sync_failures().affected == 2
    assert _body(retry) == {}

    discard = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 1})
    )
    assert client.crm.discard_sync_failures(ids=["j1"]).affected == 1
    assert _body(discard) == {"ids": ["j1"]}
    assert client.crm.discard_sync_failures().affected == 1
    assert _body(discard) == {}

    respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 5, "tasks": 6, "notes": 7})
    )
    preview = client.crm.backfill_preview()
    assert (preview.deals, preview.tasks, preview.notes) == (5, 6, 7)

    backfill = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    assert client.crm.start_backfill(deals=True, tasks=False, notes=True) is None
    assert _body(backfill) == {"deals": True, "tasks": False, "notes": True}


@respx.mock
@pytest.mark.anyio
async def test_crm_mode_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(await aclient.crm.settings())

    put = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(
        await aclient.crm.update_settings(
            provider="pipedrive",
            connection_id="conn1",
            config={"create_contacts": False},
            complete_setup=True,
        )
    )
    assert _body(put) == {
        "provider": "pipedrive",
        "connection_id": "conn1",
        "config": {"create_contacts": False},
        "complete_setup": True,
    }
    await aclient.crm.update_settings()
    assert _body(put) == {}

    respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    _check_metadata(await aclient.crm.metadata())

    respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(200, json={"data": [OWNER]})
    )
    owners = [o async for o in aclient.crm.list_owners()]
    _check_owner(owners[0])

    owner = respx.put(f"{BASE_URL}/crm/owners/1234").mock(
        return_value=httpx.Response(204)
    )
    assert await aclient.crm.map_owner("1234", user_id=USER_ID) is None
    assert _body(owner) == {"user_id": USER_ID}

    respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(200, json=HEALTH)
    )
    _check_health(await aclient.crm.sync_health())

    sync = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    assert await aclient.crm.sync_now() is None
    assert _last(sync).method == "POST"

    retry = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert (await aclient.crm.retry_sync_failures(ids=["j1"])).affected == 2
    assert _body(retry) == {"ids": ["j1"]}
    await aclient.crm.retry_sync_failures()
    assert _body(retry) == {}

    discard = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 1})
    )
    assert (await aclient.crm.discard_sync_failures(ids=["j1"])).affected == 1
    assert _body(discard) == {"ids": ["j1"]}
    await aclient.crm.discard_sync_failures()
    assert _body(discard) == {}

    respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 5, "tasks": 6, "notes": 7})
    )
    assert (await aclient.crm.backfill_preview()).tasks == 6

    backfill = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    assert await aclient.crm.start_backfill(deals=True) is None
    assert _body(backfill) == {"deals": True}


# -- provider-side contact record and lists ----------------------------------


@respx.mock
def test_crm_contact_and_lists_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/crm/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(client.crm.retrieve_contact(CONTACT_ID))

    refresh = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT_ID}/refresh").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(client.crm.refresh_contact(CONTACT_ID))
    assert _last(refresh).method == "POST"

    link = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT_ID}/link").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(client.crm.link_contact(CONTACT_ID))
    assert _last(link).method == "POST"

    patch = respx.patch(f"{BASE_URL}/crm/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(
        client.crm.update_contact(
            CONTACT_ID,
            owner_external_id="1234",
            lifecycle_stage="opportunity",
            lead_status="OPEN",
        )
    )
    assert _body(patch) == {
        "owner_external_id": "1234",
        "lifecycle_stage": "opportunity",
        "lead_status": "OPEN",
    }

    lists = respx.get(f"{BASE_URL}/crm/lists").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [LIST],
                    "pagination": {"next_cursor": "n2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"external_id": "43"}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    found = list(client.crm.list_lists(q="warm", limit=1))
    assert [item.external_id for item in found] == ["42", "43"]
    assert found[0].size == 311
    assert found[0].dynamic is True
    assert lists.calls[0].request.url.params["q"] == "warm"
    assert lists.calls[1].request.url.params["cursor"] == "n2"

    prev = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=IMPORT_PREVIEW)
    )
    _check_preview(client.crm.preview_list_import(list_id="42", apply_guards=True))
    assert _body(prev) == {"list_id": "42", "apply_guards": True}

    imp = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(
            201, json={"import_id": "imp1", "preview": IMPORT_PREVIEW}
        )
    )
    result = client.crm.import_list(list_id="42")
    assert result.import_id == "imp1"
    _check_preview(result.preview)
    assert _body(imp) == {"list_id": "42"}


@respx.mock
@pytest.mark.anyio
async def test_crm_contact_and_lists_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await aclient.crm.retrieve_contact(CONTACT_ID))

    respx.post(f"{BASE_URL}/crm/contacts/{CONTACT_ID}/refresh").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await aclient.crm.refresh_contact(CONTACT_ID))

    respx.post(f"{BASE_URL}/crm/contacts/{CONTACT_ID}/link").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await aclient.crm.link_contact(CONTACT_ID))

    patch = respx.patch(f"{BASE_URL}/crm/contacts/{CONTACT_ID}").mock(
        return_value=httpx.Response(200, json=VIEW)
    )
    _check_view(await aclient.crm.update_contact(CONTACT_ID, lead_status="OPEN"))
    assert _body(patch) == {"lead_status": "OPEN"}

    lists = respx.get(f"{BASE_URL}/crm/lists").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [LIST],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    found = [item async for item in aclient.crm.list_lists(q="warm")]
    assert found[0].name == "Warm leads"
    assert lists.calls.last.request.url.params["q"] == "warm"

    prev = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=IMPORT_PREVIEW)
    )
    _check_preview(await aclient.crm.preview_list_import(list_id="42"))
    assert _body(prev) == {"list_id": "42"}

    imp = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(
            201, json={"import_id": "imp1", "preview": IMPORT_PREVIEW}
        )
    )
    result = await aclient.crm.import_list(list_id="42", apply_guards=False)
    assert result.import_id == "imp1"
    assert _body(imp) == {"list_id": "42", "apply_guards": False}


# -- bulk task actions --------------------------------------------------------


@respx.mock
def test_crm_bulk_tasks_sync(client: Warmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 12})
    )
    assert client.crm.bulk_update_tasks(tasks=["t1", "t2"], status="completed").affected == 12
    assert _body(patch) == {"tasks": ["t1", "t2"], "status": "completed"}
    client.crm.bulk_update_tasks(
        select_all=True,
        filters={"overdue": True},
        exclude=["t9"],
        priority="urgent",
    )
    assert _body(patch) == {
        "all": True,
        "filters": {"overdue": True},
        "exclude": ["t9"],
        "priority": "urgent",
    }

    delete = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert client.crm.bulk_delete_tasks(["t1", "t2"]).affected == 2
    assert _body(delete) == ["t1", "t2"]
    client.crm.bulk_delete_tasks(
        select_all=True, filters={"statuses": ["pending"]}, exclude=["t3"]
    )
    assert _body(delete) == {
        "tasks": [],
        "all": True,
        "filters": {"statuses": ["pending"]},
        "exclude": ["t3"],
    }


@respx.mock
@pytest.mark.anyio
async def test_crm_bulk_tasks_async(aclient: AsyncWarmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 12})
    )
    result = await aclient.crm.bulk_update_tasks(tasks=["t1"], priority="low")
    assert result.affected == 12
    assert _body(patch) == {"tasks": ["t1"], "priority": "low"}

    delete = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert (await aclient.crm.bulk_delete_tasks(["t1"])).affected == 2
    assert _body(delete) == ["t1"]
    await aclient.crm.bulk_delete_tasks(
        ["t5"], select_all=True, filters={"query": "call"}
    )
    assert _body(delete) == {
        "tasks": ["t5"],
        "all": True,
        "filters": {"query": "call"},
    }


# -- external references on existing shapes ----------------------------------

EXTERNAL = {
    "provider": "pipedrive",
    "external_id": "88",
    "url": "https://acme.pipedrive.com/deal/88",
    "synced_at": "2026-11-08T08:00:00Z",
    "owner_name": "Sam Rep",
}


@respx.mock
def test_external_refs_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "p1",
                        "external": EXTERNAL,
                        "stages": [
                            {
                                "id": "s1",
                                "closed": True,
                                "won": True,
                                "probability": 100.0,
                            }
                        ],
                    }
                ]
            },
        )
    )
    pipeline = next(iter(client.crm.list_pipelines()))
    assert pipeline.external.provider == "pipedrive"
    assert pipeline.external.owner_name == "Sam Rep"
    stage = pipeline.stages[0]
    assert (stage.closed, stage.won, stage.probability) == (True, True, 100.0)

    respx.get(f"{BASE_URL}/crm/deals/d1").mock(
        return_value=httpx.Response(200, json={"id": "d1", "external": EXTERNAL})
    )
    assert client.crm.retrieve_deal("d1").external.url.endswith("/deal/88")

    respx.get(f"{BASE_URL}/crm/tasks/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "external": EXTERNAL})
    )
    assert client.crm.retrieve_task("t1").external.external_id == "88"
