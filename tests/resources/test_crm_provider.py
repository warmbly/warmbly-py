"""Tests for the CRM provider routes of the ``crm`` resource, sync and async.

Response payloads are built from the Go structs in ``internal/models/crm_provider.go``.
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
CONTACT = "9d2b1c55-6f0a-4a43-9c52-0d1d6a1d3a11"
USER = "5c0f4f6e-8f43-4e0e-8a87-2d6f64a7f001"

SETTINGS: dict[str, Any] = {
    "organization_id": "0b6e5d62-6c43-4d8b-b8d4-6f7f6b8d1111",
    "provider": "hubspot",
    "connection_id": "7a1f0d36-2b34-4a9b-8d10-3c9f5e5e2222",
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
            "deal_pipeline_id": "1e1e1e1e-0000-4000-8000-000000000001",
            "deal_stage_id": "1e1e1e1e-0000-4000-8000-000000000002",
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
        "field_map": {"first_name": "firstname", "company": "company"},
        "field_direction": {"first_name": "both", "company": "pull"},
        "for": "hubspot",
    },
    "setup_completed_at": "2026-09-30T10:00:00Z",
    "updated_at": "2026-10-01T08:30:00Z",
    "account": {
        "external_id": "12345678",
        "name": "Acme Portal",
        "app_url": "https://app.hubspot.com/contacts/12345678",
        "status": "connected",
        "health": "ok",
        "missing_scopes": ["crm.lists.read"],
    },
}

CONTACT_VIEW: dict[str, Any] = {
    "provider": "hubspot",
    "linked": True,
    "external_id": "501",
    "url": "https://app.hubspot.com/contacts/12345678/record/0-1/501",
    "owner": {
        "external_id": "77",
        "email": "sam@acme.test",
        "first_name": "Sam",
        "last_name": "Seller",
        "user_id": USER,
        "user_pinned": True,
        "archived": False,
    },
    "lifecycle_stage": {"value": "lead", "label": "Lead"},
    "lead_status": {"value": "NEW", "label": "New"},
    "company": {
        "external_id": "900",
        "name": "Globex",
        "domain": "globex.test",
        "url": "https://app.hubspot.com/contacts/12345678/record/0-2/900",
    },
    "opted_out": False,
    "properties": [{"name": "jobtitle", "label": "Job title", "value": "CTO"}],
    "synced_at": "2026-10-01T09:00:00Z",
}

SYNC_HEALTH: dict[str, Any] = {
    "pending": 3,
    "failed": 1,
    "done_24h": 412,
    "last_synced_at": "2026-10-01T09:05:00Z",
    "cursors": [
        {
            "object_type": "deal",
            "cursor_at": "2026-10-01T09:00:00Z",
            "last_run_at": "2026-10-01T09:05:00Z",
        },
        {"object_type": "task", "last_error": "rate limited"},
    ],
    "failures": [
        {
            "id": "c1c1c1c1-0000-4000-8000-000000000009",
            "organization_id": SETTINGS["organization_id"],
            "provider": "hubspot",
            "kind": "push_deal",
            "subject": "Deal: Globex renewal",
            "status": "failed",
            "attempts": 5,
            "next_attempt_at": "2026-10-01T10:00:00Z",
            "last_error": "property does not exist",
            "created_at": "2026-10-01T07:00:00Z",
            "updated_at": "2026-10-01T09:00:00Z",
            "finished_at": "2026-10-01T09:00:00Z",
        }
    ],
    "counts": {
        "contacts": 1200,
        "deals": 40,
        "tasks": 85,
        "pipelines": 2,
        "owners": 6,
    },
}

PREVIEW: dict[str, Any] = {
    "list_name": "Webinar attendees",
    "total": 120,
    "included": 100,
    "skipped": [{"reason": "customer", "label": "Already customers", "count": 20}],
    "sample": [
        {
            "email": "ada@globex.test",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "company": "Globex",
        }
    ],
    "truncated": True,
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
    assert s.connection_id == SETTINGS["connection_id"]
    assert s.setup_completed_at == "2026-09-30T10:00:00Z"
    assert s.config.activity.replies is True
    assert s.config.activity.opens is False
    assert s.config.positive_reply.lead_status == "IN_PROGRESS"
    assert s.config.positive_reply.create_deal is True
    assert s.config.positive_reply.deal_stage_id.endswith("0002")
    assert list(s.config.exit_rules.lifecycle_stages) == ["opportunity", "customer"]
    assert s.config.guards.skip_open_deals is True
    assert s.config.field_map == {"first_name": "firstname", "company": "company"}
    assert s.config.field_direction["company"] == "pull"
    assert s.config.for_ == "hubspot"
    assert s.account.name == "Acme Portal"
    assert list(s.account.missing_scopes) == ["crm.lists.read"]


def _check_view(v: Any) -> None:
    assert v.provider == "hubspot"
    assert v.linked is True
    assert v.external_id == "501"
    assert v.owner.email == "sam@acme.test"
    assert v.owner.user_pinned is True
    assert v.lifecycle_stage.label == "Lead"
    assert v.lead_status.value == "NEW"
    assert v.company.domain == "globex.test"
    assert v.opted_out is False
    assert v.properties[0].value == "CTO"
    assert v.synced_at == "2026-10-01T09:00:00Z"


def _check_health(h: Any) -> None:
    assert (h.pending, h.failed, h.done_24h) == (3, 1, 412)
    assert h.cursors[0].object_type == "deal"
    assert h.cursors[1].last_error == "rate limited"
    assert h.failures[0].kind == "push_deal"
    assert h.failures[0].attempts == 5
    assert h.counts.contacts == 1200
    assert h.counts.owners == 6


def _check_preview(p: Any) -> None:
    assert p.list_name == "Webinar attendees"
    assert (p.total, p.included, p.truncated) == (120, 100, True)
    assert p.skipped[0].count == 20
    assert p.sample[0].first_name == "Ada"


# -- settings ---------------------------------------------------------------


@respx.mock
def test_get_settings_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(client.crm.get_settings())
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_get_settings_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(await aclient.crm.get_settings())
    assert _last(route).method == "GET"


@respx.mock
def test_update_settings_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    config = {"create_contacts": False}
    _check_settings(
        client.crm.update_settings(
            provider="hubspot",
            connection_id=SETTINGS["connection_id"],
            config=config,
            complete_setup=True,
        )
    )
    assert _last(route).method == "PUT"
    assert _body(route) == {
        "provider": "hubspot",
        "connection_id": SETTINGS["connection_id"],
        "config": config,
        "complete_setup": True,
    }
    client.crm.update_settings(provider="native")
    assert _body(route) == {"provider": "native"}


@respx.mock
@pytest.mark.anyio
async def test_update_settings_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(
        await aclient.crm.update_settings(provider="pipedrive", complete_setup=True)
    )
    assert _last(route).method == "PUT"
    assert _body(route) == {"provider": "pipedrive", "complete_setup": True}


# -- metadata and owners ----------------------------------------------------

METADATA: dict[str, Any] = {
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
    "pipelines": [{"value": "default", "label": "Sales pipeline"}],
}


def _check_metadata(m: Any) -> None:
    assert m.lifecycle_stages[0].label == "Lead"
    assert m.lead_statuses[0].value == "NEW"
    assert m.task_types[0].label == "Call"
    assert m.properties[0].name == "jobtitle"
    assert m.properties[0].group_name == "contactinformation"
    assert m.properties[0].read_only is False
    assert m.pipelines[0].label == "Sales pipeline"


@respx.mock
def test_get_metadata_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    _check_metadata(client.crm.get_metadata())
    assert _last(route).url.path == "/v1/crm/metadata"


@respx.mock
@pytest.mark.anyio
async def test_get_metadata_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    _check_metadata(await aclient.crm.get_metadata())
    assert _last(route).method == "GET"


OWNERS = {"data": [CONTACT_VIEW["owner"]]}


@respx.mock
def test_list_owners_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(200, json=OWNERS)
    )
    owners = list(client.crm.list_owners())
    assert _last(route).method == "GET"
    assert owners[0].external_id == "77"
    assert owners[0].first_name == "Sam"
    assert owners[0].user_id == USER
    assert owners[0].archived is False


@respx.mock
@pytest.mark.anyio
async def test_list_owners_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(200, json=OWNERS)
    )
    owners = [o async for o in aclient.crm.list_owners()]
    assert _last(route).url.path == "/v1/crm/owners"
    assert owners[0].email == "sam@acme.test"
    assert owners[0].user_pinned is True


@respx.mock
def test_map_owner_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/crm/owners/77").mock(
        return_value=httpx.Response(204)
    )
    client.crm.map_owner("77", user_id=USER)
    assert _last(route).method == "PUT"
    assert _body(route) == {"user_id": USER}
    client.crm.map_owner("77", user_id=None)
    assert _body(route) == {"user_id": None}


@respx.mock
@pytest.mark.anyio
async def test_map_owner_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/crm/owners/77").mock(
        return_value=httpx.Response(204)
    )
    await aclient.crm.map_owner("77", user_id=USER)
    assert _last(route).url.path == "/v1/crm/owners/77"
    assert _body(route) == {"user_id": USER}


# -- sync -------------------------------------------------------------------


@respx.mock
def test_get_sync_health_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(200, json=SYNC_HEALTH)
    )
    _check_health(client.crm.get_sync_health())
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_get_sync_health_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(200, json=SYNC_HEALTH)
    )
    _check_health(await aclient.crm.get_sync_health())
    assert _last(route).method == "GET"


@respx.mock
def test_sync_now_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    client.crm.sync_now()
    request = _last(route)
    assert request.method == "POST"
    assert request.headers.get("idempotency-key")


@respx.mock
@pytest.mark.anyio
async def test_sync_now_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    await aclient.crm.sync_now()
    request = _last(route)
    assert request.url.path == "/v1/crm/sync"
    assert request.headers.get("idempotency-key")


@respx.mock
def test_retry_sync_failures_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    assert client.crm.retry_sync_failures().affected == 2
    assert _body(route) == {}
    assert _last(route).headers.get("idempotency-key")
    assert client.crm.retry_sync_failures(["j1", "j2"]).affected == 2
    assert _body(route) == {"ids": ["j1", "j2"]}
    with pytest.raises(ValueError, match="every failed sync job"):
        client.crm.retry_sync_failures([])


@respx.mock
@pytest.mark.anyio
async def test_retry_sync_failures_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 1})
    )
    assert (await aclient.crm.retry_sync_failures(["j1"])).affected == 1
    assert _body(route) == {"ids": ["j1"]}
    assert (await aclient.crm.retry_sync_failures()).affected == 1
    assert _body(route) == {}
    with pytest.raises(ValueError, match="every failed sync job"):
        await aclient.crm.retry_sync_failures([])


@respx.mock
def test_discard_sync_failures_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 4})
    )
    assert client.crm.discard_sync_failures().affected == 4
    assert _body(route) == {}
    assert client.crm.discard_sync_failures(["j9"]).affected == 4
    assert _body(route) == {"ids": ["j9"]}
    with pytest.raises(ValueError):
        client.crm.discard_sync_failures([])


@respx.mock
@pytest.mark.anyio
async def test_discard_sync_failures_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 3})
    )
    assert (await aclient.crm.discard_sync_failures(["a", "b", "c"])).affected == 3
    assert _last(route).url.path == "/v1/crm/sync/discard"
    assert _body(route) == {"ids": ["a", "b", "c"]}
    assert (await aclient.crm.discard_sync_failures()).affected == 3
    with pytest.raises(ValueError):
        await aclient.crm.discard_sync_failures([])


# -- backfill ---------------------------------------------------------------


@respx.mock
def test_get_backfill_preview_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 40, "tasks": 85, "notes": 12})
    )
    preview = client.crm.get_backfill_preview()
    assert _last(route).method == "GET"
    assert (preview.deals, preview.tasks, preview.notes) == (40, 85, 12)


@respx.mock
@pytest.mark.anyio
async def test_get_backfill_preview_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 1, "tasks": 2, "notes": 3})
    )
    preview = await aclient.crm.get_backfill_preview()
    assert _last(route).url.path == "/v1/crm/backfill"
    assert (preview.deals, preview.tasks, preview.notes) == (1, 2, 3)


@respx.mock
def test_start_backfill_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    client.crm.start_backfill(deals=True, notes=True)
    request = _last(route)
    assert request.method == "POST"
    assert request.headers.get("idempotency-key")
    assert _body(route) == {"deals": True, "tasks": False, "notes": True}


@respx.mock
@pytest.mark.anyio
async def test_start_backfill_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    await aclient.crm.start_backfill(tasks=True)
    assert _last(route).headers.get("idempotency-key")
    assert _body(route) == {"deals": False, "tasks": True, "notes": False}


# -- contacts ---------------------------------------------------------------


@respx.mock
def test_retrieve_contact_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(client.crm.retrieve_contact(CONTACT))
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_retrieve_contact_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.retrieve_contact(CONTACT))
    assert _last(route).url.path == f"/v1/crm/contacts/{CONTACT}"


@respx.mock
def test_refresh_contact_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/refresh").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(client.crm.refresh_contact(CONTACT))
    request = _last(route)
    assert request.method == "POST"
    assert request.headers.get("idempotency-key")


@respx.mock
@pytest.mark.anyio
async def test_refresh_contact_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/refresh").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.refresh_contact(CONTACT))
    assert _last(route).headers.get("idempotency-key")


@respx.mock
def test_link_contact_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/link").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(client.crm.link_contact(CONTACT))
    request = _last(route)
    assert request.method == "POST"
    assert request.headers.get("idempotency-key")


@respx.mock
@pytest.mark.anyio
async def test_link_contact_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/contacts/{CONTACT}/link").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.link_contact(CONTACT))
    assert _last(route).headers.get("idempotency-key")


@respx.mock
def test_update_contact_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(
        client.crm.update_contact(
            CONTACT, owner_external_id="77", lifecycle_stage="lead", lead_status="NEW"
        )
    )
    assert _last(route).method == "PATCH"
    assert _body(route) == {
        "owner_external_id": "77",
        "lifecycle_stage": "lead",
        "lead_status": "NEW",
    }
    client.crm.update_contact(CONTACT, lead_status="OPEN")
    assert _body(route) == {"lead_status": "OPEN"}


@respx.mock
@pytest.mark.anyio
async def test_update_contact_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/crm/contacts/{CONTACT}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_view(await aclient.crm.update_contact(CONTACT, owner_external_id="77"))
    assert _last(route).url.path == f"/v1/crm/contacts/{CONTACT}"
    assert _body(route) == {"owner_external_id": "77"}


# -- lists ------------------------------------------------------------------


def _lists_page(more: bool) -> dict[str, Any]:
    if more:
        return {
            "data": [
                {
                    "external_id": "11",
                    "name": "Webinar attendees",
                    "size": 120,
                    "dynamic": False,
                    "updated_at": "2026-09-29T12:00:00Z",
                }
            ],
            "pagination": {"total": None, "next_cursor": "bGlzdDoy", "has_more": True},
        }
    return {
        "data": [
            {"external_id": "12", "name": "Customers", "size": 7, "dynamic": True}
        ],
        "pagination": {"total": None, "next_cursor": None, "has_more": False},
    }


@respx.mock
def test_list_lists_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/lists").mock(
        side_effect=[
            httpx.Response(200, json=_lists_page(True)),
            httpx.Response(200, json=_lists_page(False)),
        ]
    )
    lists = list(client.crm.list_lists(q="web", limit=1))
    assert [item.external_id for item in lists] == ["11", "12"]
    assert lists[0].size == 120
    assert lists[0].dynamic is False
    assert lists[0].updated_at == "2026-09-29T12:00:00Z"
    assert lists[1].dynamic is True
    first, second = (call.request for call in route.calls)
    assert first.url.params.get("q") == "web"
    assert first.url.params.get("limit") == "1"
    assert first.url.params.get("cursor") is None
    assert second.url.params.get("cursor") == "bGlzdDoy"
    assert second.url.params.get("q") == "web"


@respx.mock
@pytest.mark.anyio
async def test_list_lists_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/lists").mock(
        side_effect=[
            httpx.Response(200, json=_lists_page(True)),
            httpx.Response(200, json=_lists_page(False)),
        ]
    )
    lists = [item async for item in aclient.crm.list_lists(cursor="c0")]
    assert [item.name for item in lists] == ["Webinar attendees", "Customers"]
    first, second = (call.request for call in route.calls)
    assert first.url.params.get("cursor") == "c0"
    assert second.url.params.get("cursor") == "bGlzdDoy"


@respx.mock
def test_preview_list_import_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    _check_preview(client.crm.preview_list_import(list_id="11", apply_guards=True))
    request = _last(route)
    assert request.method == "POST"
    assert request.headers.get("idempotency-key")
    assert _body(route) == {"list_id": "11", "apply_guards": True}
    client.crm.preview_list_import(list_id="11")
    assert _body(route) == {"list_id": "11", "apply_guards": False}


@respx.mock
@pytest.mark.anyio
async def test_preview_list_import_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    _check_preview(await aclient.crm.preview_list_import(list_id="12"))
    assert _last(route).url.path == "/v1/crm/lists/preview"
    assert _body(route) == {"list_id": "12", "apply_guards": False}


IMPORT_RESULT = {
    "import_id": "3f3f3f3f-0000-4000-8000-0000000000aa",
    "preview": PREVIEW,
}


@respx.mock
def test_import_list_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(201, json=IMPORT_RESULT)
    )
    result = client.crm.import_list(list_id="11", apply_guards=True)
    request = _last(route)
    assert request.method == "POST"
    assert request.headers.get("idempotency-key")
    assert _body(route) == {"list_id": "11", "apply_guards": True}
    assert result.import_id == IMPORT_RESULT["import_id"]
    _check_preview(result.preview)


@respx.mock
@pytest.mark.anyio
async def test_import_list_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(201, json=IMPORT_RESULT)
    )
    result = await aclient.crm.import_list(list_id="12")
    assert _last(route).url.path == "/v1/crm/lists/import"
    assert _body(route) == {"list_id": "12", "apply_guards": False}
    assert result.import_id == IMPORT_RESULT["import_id"]
    _check_preview(result.preview)
