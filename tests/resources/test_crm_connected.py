"""Tests for the connected-CRM calls on ``client.crm``, sync and async.

The payloads mirror the server's ``CRMSettings``, ``CRMContactView``,
``CRMSyncHealth`` and friends, and every test asserts the decoded attributes
are populated so a misspelt field cannot silently read ``None``.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CONTACT = "0b0c6f02-5c1e-4a49-8a5e-0c6f0d3a1111"

SETTINGS = {
    "organization_id": "org_1",
    "provider": "hubspot",
    "connection_id": "conn_1",
    "config": {
        "activity": {
            "sent": True,
            "replies": True,
            "bounces": True,
            "unsubscribes": True,
            "opens": False,
            "clicks": False,
            "meetings": True,
        },
        "create_contacts": True,
        "create_companies": True,
        "write_properties": True,
        "positive_reply": {
            "lead_status": "IN_PROGRESS",
            "lifecycle_stage": "",
            "create_deal": True,
            "deal_pipeline_id": "pipe_1",
            "deal_stage_id": "stage_1",
        },
        "exit_rules": {
            "deal_created": True,
            "lifecycle_stages": ["opportunity", "customer"],
            "opted_out": True,
        },
        "guards": {
            "skip_lifecycle_stages": ["customer"],
            "skip_open_deals": True,
            "skip_other_owners": False,
            "skip_opted_out": True,
        },
        "deal_pipelines": ["default"],
        "display_properties": ["jobtitle"],
        "field_map": {"first_name": "firstname"},
        "field_direction": {"first_name": "both"},
        "for": "hubspot",
        "future_key": 1,
    },
    "setup_completed_at": "2026-01-02T03:04:05Z",
    "updated_at": "2026-01-03T03:04:05Z",
    "account": {
        "external_id": "123",
        "name": "Acme Portal",
        "app_url": "https://app.hubspot.com/contacts/123",
        "status": "connected",
        "health": "healthy",
        "missing_scopes": ["crm.objects.deals.write"],
    },
}

CONTACT_VIEW = {
    "provider": "hubspot",
    "linked": True,
    "external_id": "501",
    "url": "https://app.hubspot.com/contacts/123/record/0-1/501",
    "owner": {
        "external_id": "77",
        "email": "rep@acme.com",
        "first_name": "Rae",
        "last_name": "Rep",
        "user_id": "usr_1",
        "user_pinned": True,
        "archived": False,
    },
    "lifecycle_stage": {"value": "lead", "label": "Lead"},
    "lead_status": {"value": "NEW", "label": "New"},
    "company": {
        "external_id": "900",
        "name": "Globex",
        "domain": "globex.com",
        "url": "https://app.hubspot.com/contacts/123/company/900",
    },
    "opted_out": False,
    "properties": [{"name": "jobtitle", "label": "Job title", "value": "CTO"}],
    "synced_at": "2026-01-02T03:04:05Z",
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


def _body(route: respx.Route) -> object:
    return json.loads(_last(route).content)


def _check_settings(s) -> None:  # type: ignore[no-untyped-def]
    assert s.provider == "hubspot"
    assert s.connection_id == "conn_1"
    assert s.setup_completed_at == "2026-01-02T03:04:05Z"
    assert s.config.activity.replies is True
    assert s.config.activity.opens is False
    assert s.config.positive_reply.lead_status == "IN_PROGRESS"
    assert s.config.positive_reply.deal_stage_id == "stage_1"
    assert s.config.exit_rules.lifecycle_stages == ["opportunity", "customer"]
    assert s.config.guards.skip_open_deals is True
    assert s.config.field_map == {"first_name": "firstname"}
    assert s.config.field_direction == {"first_name": "both"}
    assert s.config.for_provider == "hubspot"
    assert s.config.to_dict()["for"] == "hubspot"
    assert "for_provider" not in s.config.to_dict()
    assert s.config.future_key == 1
    assert s.account.name == "Acme Portal"
    assert s.account.missing_scopes == ["crm.objects.deals.write"]


def _check_view(v) -> None:  # type: ignore[no-untyped-def]
    assert v.provider == "hubspot"
    assert v.linked is True
    assert v.external_id == "501"
    assert v.owner.email == "rep@acme.com"
    assert v.owner.user_pinned is True
    assert v.lifecycle_stage.label == "Lead"
    assert v.lead_status.value == "NEW"
    assert v.company.domain == "globex.com"
    assert v.opted_out is False
    assert v.properties[0].value == "CTO"
    assert v.synced_at == "2026-01-02T03:04:05Z"


# -- settings ----------------------------------------------------------------
@respx.mock
def test_settings_sync(client: Warmbly) -> None:
    got = respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(client.crm.get_settings())
    assert _last(got).url.path == "/v1/crm/settings"

    put = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(
        client.crm.update_settings(
            provider="hubspot",
            connection_id="conn_1",
            config={"create_contacts": True},
            complete_setup=True,
        )
    )
    assert _last(put).method == "PUT"
    assert _body(put) == {
        "provider": "hubspot",
        "connection_id": "conn_1",
        "config": {"create_contacts": True},
        "complete_setup": True,
    }

    client.crm.update_settings(provider="native")
    assert _body(put) == {"provider": "native"}


@respx.mock
@pytest.mark.anyio
async def test_settings_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(await aclient.crm.get_settings())
    put = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(await aclient.crm.update_settings(complete_setup=True))
    assert _body(put) == {"complete_setup": True}


# -- metadata and owners -------------------------------------------------------
METADATA = {
    "lifecycle_stages": [{"value": "lead", "label": "Lead"}],
    "lead_statuses": [{"value": "NEW", "label": "New"}],
    "task_types": [{"value": "CALL", "label": "Call"}],
    "properties": [
        {
            "name": "jobtitle",
            "label": "Job title",
            "type": "string",
            "group_name": "contactinformation",
            "read_only": False,
        }
    ],
    "pipelines": [{"value": "default", "label": "Sales"}],
}
OWNERS = {
    "data": [
        {
            "external_id": "77",
            "email": "rep@acme.com",
            "first_name": "Rae",
            "last_name": "Rep",
            "user_id": "usr_1",
            "user_pinned": False,
            "archived": False,
        },
        {
            "external_id": "78",
            "email": "x@acme.com",
            "first_name": "",
            "last_name": "",
            "user_pinned": False,
            "archived": True,
        },
    ]
}


def _check_metadata(m) -> None:  # type: ignore[no-untyped-def]
    assert m.lifecycle_stages[0].label == "Lead"
    assert m.lead_statuses[0].value == "NEW"
    assert m.task_types[0].value == "CALL"
    assert m.properties[0].group_name == "contactinformation"
    assert m.properties[0].read_only is False
    assert m.pipelines[0].label == "Sales"


@respx.mock
def test_metadata_and_owners_sync(client: Warmbly) -> None:
    meta = respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    _check_metadata(client.crm.get_metadata())
    assert _last(meta).url.path == "/v1/crm/metadata"

    respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(200, json=OWNERS)
    )
    owners = list(client.crm.list_owners())
    assert [o.external_id for o in owners] == ["77", "78"]
    assert owners[0].email == "rep@acme.com"
    assert owners[0].user_id == "usr_1"
    assert owners[1].archived is True

    put = respx.put(f"{BASE_URL}/crm/owners/77").mock(return_value=httpx.Response(204))
    assert client.crm.map_owner("77", user_id="usr_1") is None
    assert _body(put) == {"user_id": "usr_1"}
    client.crm.map_owner("77", user_id=None)
    assert _body(put) == {"user_id": None}

    odd = respx.put(f"{BASE_URL}/crm/owners/a%2Fb").mock(
        return_value=httpx.Response(204)
    )
    client.crm.map_owner("a/b", user_id=None)
    assert odd.called


@respx.mock
@pytest.mark.anyio
async def test_metadata_and_owners_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    _check_metadata(await aclient.crm.get_metadata())
    respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(200, json=OWNERS)
    )
    owners = [o async for o in aclient.crm.list_owners()]
    assert [o.external_id for o in owners] == ["77", "78"]
    assert owners[0].first_name == "Rae"
    put = respx.put(f"{BASE_URL}/crm/owners/77").mock(return_value=httpx.Response(204))
    assert await aclient.crm.map_owner("77", user_id="usr_2") is None
    assert _body(put) == {"user_id": "usr_2"}


# -- sync health ---------------------------------------------------------------
HEALTH = {
    "pending": 3,
    "failed": 1,
    "done_24h": 40,
    "last_synced_at": "2026-01-02T03:04:05Z",
    "cursors": [
        {
            "object_type": "deal",
            "cursor_at": "2026-01-02T03:00:00Z",
            "last_run_at": "2026-01-02T03:04:05Z",
            "last_error": "rate limited",
        }
    ],
    "failures": [
        {
            "id": "job_1",
            "organization_id": "org_1",
            "provider": "hubspot",
            "kind": "push_deal",
            "subject": "deal 1",
            "status": "failed",
            "attempts": 5,
            "next_attempt_at": "2026-01-02T04:00:00Z",
            "last_error": "boom",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
        }
    ],
    "counts": {"contacts": 10, "deals": 4, "tasks": 3, "pipelines": 1, "owners": 2},
}


def _check_health(h) -> None:  # type: ignore[no-untyped-def]
    assert (h.pending, h.failed, h.done_24h) == (3, 1, 40)
    assert h.last_synced_at == "2026-01-02T03:04:05Z"
    assert h.cursors[0].object_type == "deal"
    assert h.cursors[0].last_error == "rate limited"
    assert h.failures[0].id == "job_1"
    assert h.failures[0].kind == "push_deal"
    assert h.failures[0].attempts == 5
    assert h.failures[0].last_error == "boom"
    assert h.counts.contacts == 10
    assert h.counts.owners == 2


@respx.mock
def test_sync_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(200, json=HEALTH)
    )
    _check_health(client.crm.get_sync_health())

    now = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    assert client.crm.sync_now() is None
    assert _last(now).method == "POST"
    assert _last(now).headers["Idempotency-Key"]

    retry = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert client.crm.retry_sync_failures(ids=["job_1", "job_2"]).affected == 2
    assert _body(retry) == {"ids": ["job_1", "job_2"]}
    assert client.crm.retry_sync_failures().affected == 2
    assert _body(retry) == {}

    discard = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 5})
    )
    assert client.crm.discard_sync_failures(ids=["job_1"]).affected == 5
    assert _body(discard) == {"ids": ["job_1"]}
    assert client.crm.discard_sync_failures().affected == 5
    assert _body(discard) == {}


@respx.mock
@pytest.mark.anyio
async def test_sync_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(200, json=HEALTH)
    )
    _check_health(await aclient.crm.get_sync_health())
    now = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    assert await aclient.crm.sync_now() is None
    assert now.called
    retry = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert (await aclient.crm.retry_sync_failures(ids=["job_1"])).affected == 2
    assert _body(retry) == {"ids": ["job_1"]}
    discard = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 1})
    )
    assert (await aclient.crm.discard_sync_failures()).affected == 1
    assert _body(discard) == {}


# -- backfill ------------------------------------------------------------------
@respx.mock
def test_backfill_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 4, "tasks": 3, "notes": 9})
    )
    preview = client.crm.get_backfill()
    assert (preview.deals, preview.tasks, preview.notes) == (4, 3, 9)

    start = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    assert client.crm.start_backfill(deals=True, tasks=False, notes=True) is None
    assert _body(start) == {"deals": True, "tasks": False, "notes": True}


@respx.mock
@pytest.mark.anyio
async def test_backfill_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 1, "tasks": 2, "notes": 3})
    )
    preview = await aclient.crm.get_backfill()
    assert (preview.deals, preview.tasks, preview.notes) == (1, 2, 3)
    start = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    assert await aclient.crm.start_backfill(deals=True) is None
    assert _body(start) == {"deals": True}


# -- contacts ------------------------------------------------------------------
@respx.mock
def test_contacts_sync(client: Warmbly) -> None:
    got = respx.get(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(client.crm.get_contact(CONTACT))
    assert _last(got).method == "GET"

    refresh = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/refresh").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(client.crm.refresh_contact(CONTACT))
    assert _last(refresh).headers["Idempotency-Key"]

    link = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/link").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(client.crm.link_contact(CONTACT))
    assert _last(link).method == "POST"

    patch = respx.patch(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(
        client.crm.update_contact(
            CONTACT, owner_external_id="77", lifecycle_stage="lead"
        )
    )
    assert _body(patch) == {"owner_external_id": "77", "lifecycle_stage": "lead"}


@respx.mock
@pytest.mark.anyio
async def test_contacts_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.get_contact(CONTACT))
    respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/refresh").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.refresh_contact(CONTACT))
    respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/link").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.link_contact(CONTACT))
    patch = respx.patch(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.update_contact(CONTACT, lead_status="NEW"))
    assert _body(patch) == {"lead_status": "NEW"}


# -- lists ---------------------------------------------------------------------
LISTS_P1 = {
    "data": [
        {
            "external_id": "l1",
            "name": "Webinar",
            "size": 120,
            "dynamic": False,
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ],
    "pagination": {"total": None, "next_cursor": "c2", "has_more": True},
}
LISTS_P2 = {
    "data": [{"external_id": "l2", "name": "Trial", "size": 5, "dynamic": True}],
    "pagination": {"total": None, "next_cursor": None, "has_more": False},
}
PREVIEW = {
    "list_name": "Webinar",
    "total": 120,
    "included": 100,
    "skipped": [{"reason": "opted_out", "label": "Opted out", "count": 20}],
    "sample": [
        {
            "email": "a@b.com",
            "first_name": "A",
            "last_name": "B",
            "company": "Acme",
        }
    ],
    "truncated": False,
}


def _check_preview(p) -> None:  # type: ignore[no-untyped-def]
    assert p.list_name == "Webinar"
    assert (p.total, p.included) == (120, 100)
    assert p.skipped[0].reason == "opted_out"
    assert p.skipped[0].count == 20
    assert p.sample[0].email == "a@b.com"
    assert p.sample[0].company == "Acme"
    assert p.truncated is False


@respx.mock
def test_lists_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/lists").mock(
        side_effect=[
            httpx.Response(200, json=LISTS_P1),
            httpx.Response(200, json=LISTS_P2),
        ]
    )
    lists = list(client.crm.list_lists(q="web", limit=1))
    assert [x.external_id for x in lists] == ["l1", "l2"]
    assert lists[0].name == "Webinar"
    assert lists[0].size == 120
    assert lists[1].dynamic is True
    first, second = (c.request for c in route.calls)
    assert dict(first.url.params) == {"q": "web", "limit": "1"}
    assert dict(second.url.params) == {"q": "web", "limit": "1", "cursor": "c2"}

    prev = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    _check_preview(client.crm.preview_import(list_id="l1", apply_guards=True))
    assert _body(prev) == {"list_id": "l1", "apply_guards": True}

    imp = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(
            201, json={"import_id": "imp_1", "preview": PREVIEW}
        )
    )
    result = client.crm.import_list(list_id="l1")
    assert result.import_id == "imp_1"
    _check_preview(result.preview)
    assert _body(imp) == {"list_id": "l1"}
    assert _last(imp).headers["Idempotency-Key"]


@respx.mock
@pytest.mark.anyio
async def test_lists_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/lists").mock(
        side_effect=[
            httpx.Response(200, json=LISTS_P1),
            httpx.Response(200, json=LISTS_P2),
        ]
    )
    lists = [x async for x in aclient.crm.list_lists()]
    assert [x.external_id for x in lists] == ["l1", "l2"]
    assert lists[0].size == 120
    prev = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    _check_preview(await aclient.crm.preview_import(list_id="l1"))
    assert _body(prev) == {"list_id": "l1"}
    respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(
            201, json={"import_id": "imp_1", "preview": PREVIEW}
        )
    )
    result = await aclient.crm.import_list(list_id="l1", apply_guards=False)
    assert result.import_id == "imp_1"
    assert result.preview.included == 100


# -- bulk tasks ----------------------------------------------------------------
@respx.mock
def test_bulk_tasks_sync(client: Warmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 7})
    )
    res = client.crm.bulk_update_tasks(tasks=["t1", "t2"], status="completed")
    assert res.affected == 7
    assert _body(patch) == {"tasks": ["t1", "t2"], "status": "completed"}

    client.crm.bulk_update_tasks(
        select_all=True,
        filters={"statuses": ["pending"], "overdue": True},
        exclude=["t3"],
        priority="high",
    )
    assert _body(patch) == {
        "all": True,
        "filters": {"statuses": ["pending"], "overdue": True},
        "exclude": ["t3"],
        "priority": "high",
    }

    delete = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert client.crm.bulk_delete_tasks(tasks=["t1", "t2"]).affected == 2
    assert _last(delete).method == "DELETE"
    assert _body(delete) == {"tasks": ["t1", "t2"]}
    client.crm.bulk_delete_tasks(select_all=True, filters={"query": "x"})
    assert _body(delete) == {"all": True, "filters": {"query": "x"}}


@respx.mock
@pytest.mark.anyio
async def test_bulk_tasks_async(aclient: AsyncWarmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 3})
    )
    res = await aclient.crm.bulk_update_tasks(tasks=["t1"], priority="low")
    assert res.affected == 3
    assert _body(patch) == {"tasks": ["t1"], "priority": "low"}
    delete = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 1})
    )
    assert (await aclient.crm.bulk_delete_tasks(tasks=["t1"])).affected == 1
    assert _body(delete) == {"tasks": ["t1"]}


# -- drift on existing models --------------------------------------------------
@respx.mock
def test_external_refs_decode(client: Warmbly) -> None:
    ext = {
        "provider": "pipedrive",
        "external_id": "42",
        "url": "https://x.pipedrive.com/deal/42",
        "synced_at": "2026-01-02T03:04:05Z",
        "owner_name": "Ext Owner",
    }
    respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "p1",
                        "name": "Sales",
                        "external": ext,
                        "stages": [
                            {
                                "id": "s1",
                                "name": "Won",
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
    assert pipeline.external.owner_name == "Ext Owner"
    stage = pipeline.stages[0]
    assert (stage.closed, stage.won, stage.probability) == (True, True, 100.0)

    respx.get(f"{BASE_URL}/crm/deals/d1").mock(
        return_value=httpx.Response(200, json={"id": "d1", "external": ext})
    )
    assert client.crm.retrieve_deal("d1").external.external_id == "42"
    respx.get(f"{BASE_URL}/crm/tasks/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "external": ext})
    )
    assert client.crm.retrieve_task("t1").external.url.endswith("/deal/42")
