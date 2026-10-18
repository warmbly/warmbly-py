"""Tests for the connected-CRM surface of the ``crm`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
UUID = "0b2f3a54-6a49-4a64-9a02-1f0a0b6a7c11"
UUID2 = "9c1d2e3f-0a1b-4c5d-8e9f-a0b1c2d3e4f5"


class Api:
    """Drive one resource method against the sync or the async client alike."""

    def __init__(self, client: Any, is_async: bool) -> None:
        self.crm = client.crm
        self.is_async = is_async

    async def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        result = getattr(self.crm, name)(*args, **kwargs)
        if self.is_async:
            return await result
        return result

    async def items(self, name: str, *args: Any, **kwargs: Any) -> list[Any]:
        result = getattr(self.crm, name)(*args, **kwargs)
        if self.is_async:
            return [item async for item in result]
        return list(result)


@pytest.fixture(params=["sync", "async"])
async def api(request: pytest.FixtureRequest) -> AsyncIterator[Api]:
    if request.param == "sync":
        client = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
        yield Api(client, False)
        client.close()
    else:
        async with AsyncWarmbly(
            api_key="wmbly_test", base_url=BASE_URL, max_retries=0
        ) as aclient:
            yield Api(aclient, True)


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


CONTACT_VIEW = {
    "provider": "hubspot",
    "linked": True,
    "external_id": "801",
    "url": "https://app.hubspot.com/contacts/1/contact/801",
    "owner": {
        "external_id": "77",
        "email": "rep@acme.com",
        "first_name": "Ada",
        "last_name": "Rep",
        "user_id": UUID,
        "user_pinned": True,
        "archived": False,
    },
    "lifecycle_stage": {"value": "lead", "label": "Lead"},
    "lead_status": {"value": "NEW", "label": "New"},
    "company": {
        "external_id": "55",
        "name": "Acme",
        "domain": "acme.com",
        "url": "https://app.hubspot.com/contacts/1/company/55",
    },
    "opted_out": False,
    "properties": [{"name": "jobtitle", "label": "Job title", "value": "CTO"}],
    "synced_at": "2026-05-01T10:00:00Z",
}


def _check_contact_view(view: Any) -> None:
    assert view.provider == "hubspot"
    assert view.linked is True
    assert view.external_id == "801"
    assert view.owner.email == "rep@acme.com"
    assert view.owner.user_pinned is True
    assert view.lifecycle_stage.label == "Lead"
    assert view.lead_status.value == "NEW"
    assert view.company.domain == "acme.com"
    assert view.opted_out is False
    assert view.properties[0].value == "CTO"
    assert view.synced_at == "2026-05-01T10:00:00Z"


SETTINGS = {
    "organization_id": UUID,
    "provider": "hubspot",
    "connection_id": UUID2,
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
            "deal_pipeline_id": UUID,
            "deal_stage_id": UUID2,
        },
        "exit_rules": {
            "deal_created": True,
            "lifecycle_stages": ["customer"],
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
    },
    "setup_completed_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-02T10:00:00Z",
    "account": {
        "external_id": "1234",
        "name": "Acme Portal",
        "app_url": "https://app.hubspot.com/contacts/1234",
        "status": "connected",
        "health": "ok",
        "missing_scopes": ["crm.objects.deals.write"],
    },
}


def _check_settings(s: Any) -> None:
    assert s.provider == "hubspot"
    assert s.connection_id == UUID2
    assert s.config.activity.replies is True
    assert s.config.activity.opens is False
    assert s.config.positive_reply.deal_stage_id == UUID2
    assert s.config.exit_rules.lifecycle_stages == ["customer"]
    assert s.config.guards.skip_open_deals is True
    assert s.config.field_map == {"first_name": "firstname"}
    assert s.config.for_ == "hubspot"
    assert s.account.name == "Acme Portal"
    assert list(s.account.missing_scopes) == ["crm.objects.deals.write"]
    assert s.setup_completed_at == "2026-05-01T10:00:00Z"


@respx.mock
@pytest.mark.anyio
async def test_settings(api: Api) -> None:
    route = respx.get(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    _check_settings(await api.call("settings"))
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_update_settings(api: Api) -> None:
    route = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json=SETTINGS)
    )
    out = await api.call(
        "update_settings",
        provider="hubspot",
        connection_id=UUID2,
        config={"create_contacts": True, "for": "hubspot"},
        complete_setup=True,
    )
    _check_settings(out)
    assert _last(route).method == "PUT"
    assert _body(route) == {
        "provider": "hubspot",
        "connection_id": UUID2,
        "config": {"create_contacts": True, "for": "hubspot"},
        "complete_setup": True,
    }


@respx.mock
@pytest.mark.anyio
async def test_update_settings_sends_only_given_keys(api: Api) -> None:
    route = respx.put(f"{BASE_URL}/crm/settings").mock(
        return_value=httpx.Response(200, json={"provider": "native"})
    )
    out = await api.call("update_settings", provider="native")
    assert out.provider == "native"
    assert _body(route) == {"provider": "native"}


@respx.mock
@pytest.mark.anyio
async def test_metadata(api: Api) -> None:
    route = respx.get(f"{BASE_URL}/crm/metadata").mock(
        return_value=httpx.Response(
            200,
            json={
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
            },
        )
    )
    meta = await api.call("metadata")
    assert _last(route).url.path == "/v1/crm/metadata"
    assert meta.lifecycle_stages[0].label == "Lead"
    assert meta.lead_statuses[0].value == "NEW"
    assert meta.task_types[0].value == "CALL"
    assert meta.properties[0].group_name == "contactinformation"
    assert meta.properties[0].read_only is False
    assert meta.properties[0].type == "string"
    assert meta.pipelines[0].label == "Sales"


@respx.mock
@pytest.mark.anyio
async def test_owners_and_map_owner(api: Api) -> None:
    listing = respx.get(f"{BASE_URL}/crm/owners").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "external_id": "77",
                        "email": "rep@acme.com",
                        "first_name": "Ada",
                        "last_name": "Rep",
                        "user_id": UUID,
                        "user_pinned": False,
                        "archived": True,
                    }
                ]
            },
        )
    )
    owners = await api.items("owners")
    assert _last(listing).url.path == "/v1/crm/owners"
    assert owners[0].external_id == "77"
    assert owners[0].user_id == UUID
    assert owners[0].archived is True

    mapping = respx.put(f"{BASE_URL}/crm/owners/77").mock(
        return_value=httpx.Response(204)
    )
    assert await api.call("map_owner", "77", user_id=UUID) is None
    assert _last(mapping).method == "PUT"
    assert _body(mapping) == {"user_id": UUID}
    assert await api.call("map_owner", "77", user_id=None) is None
    assert _body(mapping) == {"user_id": None}


@respx.mock
@pytest.mark.anyio
async def test_map_owner_quotes_the_external_id(api: Api) -> None:
    route = respx.put(f"{BASE_URL}/crm/owners/a%2Fb").mock(
        return_value=httpx.Response(204)
    )
    await api.call("map_owner", "a/b", user_id=UUID)
    assert _last(route).url.raw_path.endswith(b"/crm/owners/a%2Fb")


@respx.mock
@pytest.mark.anyio
async def test_sync_health(api: Api) -> None:
    route = respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "pending": 3,
                "failed": 1,
                "done_24h": 120,
                "last_synced_at": "2026-05-01T10:00:00Z",
                "cursors": [
                    {
                        "object_type": "deal",
                        "cursor_at": "2026-05-01T09:00:00Z",
                        "last_run_at": "2026-05-01T10:00:00Z",
                        "last_error": "rate limited",
                    }
                ],
                "failures": [
                    {
                        "id": UUID,
                        "organization_id": UUID2,
                        "provider": "hubspot",
                        "kind": "push_deal",
                        "subject": "deal 9",
                        "status": "failed",
                        "attempts": 5,
                        "next_attempt_at": "2026-05-01T11:00:00Z",
                        "last_error": "403",
                        "created_at": "2026-05-01T08:00:00Z",
                        "updated_at": "2026-05-01T09:00:00Z",
                        "finished_at": "2026-05-01T09:30:00Z",
                    }
                ],
                "counts": {
                    "contacts": 10,
                    "deals": 4,
                    "tasks": 2,
                    "pipelines": 1,
                    "owners": 3,
                },
            },
        )
    )
    health = await api.call("sync_health")
    assert _last(route).method == "GET"
    assert (health.pending, health.failed, health.done_24h) == (3, 1, 120)
    assert health.last_synced_at == "2026-05-01T10:00:00Z"
    assert health.cursors[0].object_type == "deal"
    assert health.cursors[0].cursor_at == "2026-05-01T09:00:00Z"
    assert health.cursors[0].last_run_at == "2026-05-01T10:00:00Z"
    assert health.cursors[0].last_error == "rate limited"
    job = health.failures[0]
    assert (job.id, job.kind, job.attempts) == (UUID, "push_deal", 5)
    assert job.provider == "hubspot"
    assert job.organization_id == UUID2
    assert job.subject == "deal 9"
    assert job.status == "failed"
    assert job.next_attempt_at == "2026-05-01T11:00:00Z"
    assert job.last_error == "403"
    assert job.created_at == "2026-05-01T08:00:00Z"
    assert job.updated_at == "2026-05-01T09:00:00Z"
    assert job.finished_at == "2026-05-01T09:30:00Z"
    assert health.counts.deals == 4
    assert (health.counts.contacts, health.counts.tasks) == (10, 2)
    assert (health.counts.pipelines, health.counts.owners) == (1, 3)


@respx.mock
@pytest.mark.anyio
async def test_sync_now(api: Api) -> None:
    route = respx.post(f"{BASE_URL}/crm/sync").mock(return_value=httpx.Response(202))
    assert await api.call("sync_now") is None
    assert _last(route).method == "POST"
    assert _last(route).headers.get("idempotency-key")


@respx.mock
@pytest.mark.anyio
async def test_retry_and_discard_sync_failures(api: Api) -> None:
    retry = respx.post(f"{BASE_URL}/crm/sync/retry").mock(
        return_value=httpx.Response(200, json={"affected": 2})
    )
    out = await api.call("retry_sync_failures", ids=[UUID, UUID2])
    assert out.affected == 2
    assert _body(retry) == {"ids": [UUID, UUID2]}
    await api.call("retry_sync_failures")
    assert _body(retry) == {}

    discard = respx.post(f"{BASE_URL}/crm/sync/discard").mock(
        return_value=httpx.Response(200, json={"affected": 5})
    )
    out = await api.call("discard_sync_failures", ids=[UUID])
    assert out.affected == 5
    assert _body(discard) == {"ids": [UUID]}
    await api.call("discard_sync_failures")
    assert _body(discard) == {}


@respx.mock
@pytest.mark.anyio
async def test_backfill(api: Api) -> None:
    preview = respx.get(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(200, json={"deals": 12, "tasks": 4, "notes": 30})
    )
    counts = await api.call("backfill_preview")
    assert _last(preview).method == "GET"
    assert (counts.deals, counts.tasks, counts.notes) == (12, 4, 30)

    start = respx.post(f"{BASE_URL}/crm/backfill").mock(
        return_value=httpx.Response(202)
    )
    assert await api.call("start_backfill", deals=True, notes=True) is None
    assert _body(start) == {"deals": True, "tasks": False, "notes": True}
    assert _last(start).headers.get("idempotency-key")
    await api.call("start_backfill")
    assert _body(start) == {"deals": False, "tasks": False, "notes": False}


@respx.mock
@pytest.mark.anyio
async def test_contact_record_routes(api: Api) -> None:
    get = respx.get(f"{BASE_URL}/crm/contacts/{UUID}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_contact_view(await api.call("retrieve_contact", UUID))
    assert _last(get).method == "GET"

    refresh = respx.post(f"{BASE_URL}/crm/contacts/{UUID}/refresh").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_contact_view(await api.call("refresh_contact", UUID))
    assert _last(refresh).method == "POST"

    link = respx.post(f"{BASE_URL}/crm/contacts/{UUID}/link").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_contact_view(await api.call("link_contact", UUID))
    assert _last(link).method == "POST"

    patch = respx.patch(f"{BASE_URL}/crm/contacts/{UUID}").mock(
        return_value=httpx.Response(200, json=CONTACT_VIEW)
    )
    _check_contact_view(
        await api.call(
            "update_contact",
            UUID,
            owner_external_id="77",
            lifecycle_stage="lead",
            lead_status="NEW",
        )
    )
    assert _last(patch).method == "PATCH"
    assert _body(patch) == {
        "owner_external_id": "77",
        "lifecycle_stage": "lead",
        "lead_status": "NEW",
    }
    await api.call("update_contact", UUID, lead_status="OPEN")
    assert _body(patch) == {"lead_status": "OPEN"}


@respx.mock
@pytest.mark.anyio
async def test_lists(api: Api) -> None:
    route = respx.get(f"{BASE_URL}/crm/lists").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "external_id": "12",
                        "name": "Webinar leads",
                        "size": 250,
                        "dynamic": True,
                        "updated_at": "2026-05-01T10:00:00Z",
                    }
                ],
                "pagination": {"total": None, "next_cursor": None, "has_more": False},
            },
        )
    )
    lists = await api.items("lists", q="web", limit=10, cursor="abc")
    query = dict(_last(route).url.params)
    assert query == {"q": "web", "limit": "10", "cursor": "abc"}
    assert lists[0].external_id == "12"
    assert lists[0].name == "Webinar leads"
    assert lists[0].size == 250
    assert lists[0].dynamic is True
    assert lists[0].updated_at == "2026-05-01T10:00:00Z"


IMPORT_PREVIEW = {
    "list_name": "Webinar leads",
    "total": 250,
    "included": 200,
    "skipped": [{"reason": "customer", "label": "Already customers", "count": 50}],
    "sample": [
        {
            "email": "a@acme.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "company": "Acme",
        }
    ],
    "truncated": True,
}


def _check_preview(p: Any) -> None:
    assert p.list_name == "Webinar leads"
    assert (p.total, p.included) == (250, 200)
    assert p.skipped[0].reason == "customer"
    assert p.skipped[0].label == "Already customers"
    assert p.skipped[0].count == 50
    assert p.sample[0].email == "a@acme.com"
    assert p.sample[0].first_name == "Ada"
    assert p.sample[0].last_name == "Lovelace"
    assert p.sample[0].company == "Acme"
    assert p.truncated is True


@respx.mock
@pytest.mark.anyio
async def test_list_import_preview_and_import(api: Api) -> None:
    preview = respx.post(f"{BASE_URL}/crm/lists/preview").mock(
        return_value=httpx.Response(200, json=IMPORT_PREVIEW)
    )
    _check_preview(await api.call("preview_list_import", list_id="12"))
    assert _body(preview) == {"list_id": "12"}
    await api.call("preview_list_import", list_id="12", apply_guards=True)
    assert _body(preview) == {"list_id": "12", "apply_guards": True}

    imported = respx.post(f"{BASE_URL}/crm/lists/import").mock(
        return_value=httpx.Response(
            201, json={"import_id": UUID, "preview": IMPORT_PREVIEW}
        )
    )
    out = await api.call("import_list", list_id="12", apply_guards=False)
    assert out.import_id == UUID
    _check_preview(out.preview)
    assert _body(imported) == {"list_id": "12", "apply_guards": False}
    assert _last(imported).headers.get("idempotency-key")
    await api.call("import_list", list_id="12")
    assert _body(imported) == {"list_id": "12"}


@respx.mock
@pytest.mark.anyio
async def test_bulk_update_tasks(api: Api) -> None:
    route = respx.patch(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 7})
    )
    out = await api.call(
        "bulk_update_tasks",
        select_all=True,
        filters={"statuses": ["pending"], "overdue": True},
        exclude=[UUID],
        status="completed",
        priority="high",
    )
    assert out.affected == 7
    assert _last(route).method == "PATCH"
    assert _body(route) == {
        "all": True,
        "filters": {"statuses": ["pending"], "overdue": True},
        "exclude": [UUID],
        "status": "completed",
        "priority": "high",
    }
    await api.call("bulk_update_tasks", tasks=[UUID, UUID2], priority="low")
    assert _body(route) == {"tasks": [UUID, UUID2], "priority": "low"}


@respx.mock
@pytest.mark.anyio
async def test_bulk_delete_tasks(api: Api) -> None:
    route = respx.delete(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json={"affected": 3})
    )
    out = await api.call("bulk_delete_tasks", tasks=[UUID, UUID2])
    assert out.affected == 3
    assert _last(route).method == "DELETE"
    assert _body(route) == {"tasks": [UUID, UUID2]}
    await api.call(
        "bulk_delete_tasks",
        select_all=True,
        filters={"query": "call"},
        exclude=[UUID],
    )
    assert _body(route) == {
        "all": True,
        "filters": {"query": "call"},
        "exclude": [UUID],
    }


@respx.mock
@pytest.mark.anyio
async def test_external_refs_and_stage_flags(api: Api) -> None:
    external = {
        "provider": "pipedrive",
        "external_id": "42",
        "url": "https://acme.pipedrive.com/deal/42",
        "synced_at": "2026-05-01T10:00:00Z",
        "owner_name": "Grace Hopper",
    }
    stage = {
        "id": UUID2,
        "pipeline_id": UUID,
        "name": "Closed won",
        "color": "#22c55e",
        "position": 5,
        "closed": True,
        "won": True,
        "probability": 100.0,
    }
    respx.get(f"{BASE_URL}/crm/pipelines/{UUID}").mock(
        return_value=httpx.Response(
            200,
            json={"id": UUID, "name": "Sales", "stages": [stage], "external": external},
        )
    )
    pipeline = await api.call("retrieve_pipeline", UUID)
    assert pipeline.external.provider == "pipedrive"
    assert pipeline.external.owner_name == "Grace Hopper"
    assert pipeline.external.synced_at == "2026-05-01T10:00:00Z"
    assert pipeline.stages[0].closed is True
    assert pipeline.stages[0].won is True
    assert pipeline.stages[0].probability == 100.0

    respx.get(f"{BASE_URL}/crm/deals/{UUID}").mock(
        return_value=httpx.Response(
            200, json={"id": UUID, "name": "Big deal", "external": external}
        )
    )
    deal = await api.call("retrieve_deal", UUID)
    assert deal.external.external_id == "42"
    assert deal.external.url == "https://acme.pipedrive.com/deal/42"

    respx.get(f"{BASE_URL}/crm/tasks/{UUID}").mock(
        return_value=httpx.Response(
            200, json={"id": UUID, "title": "Call", "external": external}
        )
    )
    task = await api.call("retrieve_task", UUID)
    assert task.external.provider == "pipedrive"
