"""Tests for the integrations, lead-sync and OAuth-application sync changes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CONN = "5d1c0b9e-3b0e-4a7c-9a55-0c3f6a1b2d10"
UUID = "0b2f3a54-6a49-4a64-9a02-1f0a0b6a7c11"
UUID2 = "9c1d2e3f-0a1b-4c5d-8e9f-a0b1c2d3e4f5"
TS = "2026-05-01T10:00:00Z"


class Api:
    """Drive one resource method against the sync or the async client alike."""

    def __init__(self, client: Any, is_async: bool) -> None:
        self.client = client
        self.is_async = is_async

    async def call(self, resource: str, name: str, /, *args: Any, **kwargs: Any) -> Any:
        result = getattr(getattr(self.client, resource), name)(*args, **kwargs)
        if self.is_async:
            return await result
        return result

    async def items(
        self, resource: str, name: str, /, *args: Any, **kw: Any
    ) -> list[Any]:
        result = getattr(getattr(self.client, resource), name)(*args, **kw)
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


def _data(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "data": rows,
        "pagination": {"total": None, "next_cursor": None, "has_more": False},
    }


# -- connections ---------------------------------------------------------------


@respx.mock
@pytest.mark.anyio
async def test_catalog_rank(api: Api) -> None:
    respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(
            200,
            json={"catalog": [{"provider": "apollo", "name": "Apollo", "rank": 3}]},
        )
    )
    entries = await api.items("integrations", "catalog")
    assert entries[0].provider == "apollo"
    assert entries[0].rank == 3


@respx.mock
@pytest.mark.anyio
async def test_push_selection(api: Api) -> None:
    route = respx.post(f"{BASE_URL}/integrations/connections/{CONN}/push").mock(
        return_value=httpx.Response(
            200,
            json={
                "provider": "hubspot",
                "pushed": 2,
                "failed": 0,
                "results": [{"contact_id": UUID, "status": "ok"}],
            },
        )
    )
    out = await api.call(
        "integrations",
        "push",
        CONN,
        select_all=True,
        filters={"query": "acme"},
        exclude=[UUID2],
    )
    assert (out.provider, out.pushed, out.failed) == ("hubspot", 2, 0)
    assert out.results[0]["contact_id"] == UUID
    assert _body(route) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": [UUID2],
    }
    assert _last(route).headers.get("idempotency-key")
    await api.call("integrations", "push", CONN, contact_ids=[UUID])
    assert _body(route) == {"contact_ids": [UUID]}


@respx.mock
@pytest.mark.anyio
async def test_signing_key_and_inbound_url(api: Api) -> None:
    key = respx.put(f"{BASE_URL}/integrations/connections/{CONN}/signing-key").mock(
        return_value=httpx.Response(
            200,
            json={
                "connection": {
                    "id": CONN,
                    "provider": "calendly",
                    "status": "connected",
                }
            },
        )
    )
    out = await api.call(
        "integrations", "set_connection_signing_key", CONN, signing_key="s3cret"
    )
    assert out.connection.id == CONN
    assert out.connection.provider == "calendly"
    assert _last(key).method == "PUT"
    assert _body(key) == {"signing_key": "s3cret"}

    rotate = respx.post(
        f"{BASE_URL}/integrations/connections/{CONN}/rotate-inbound-url"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"inbound_webhook_url": "https://api.warmbly.com/v1/x/new-secret"},
        )
    )
    url = await api.call("integrations", "rotate_inbound_url", CONN)
    assert url.inbound_webhook_url == "https://api.warmbly.com/v1/x/new-secret"
    assert _last(rotate).method == "POST"
    assert _last(rotate).headers.get("idempotency-key")


# -- community directory ---------------------------------------------------------

COMMUNITY_APP = {
    "application_id": UUID,
    "slug": "acme-sync",
    "name": "Acme Sync",
    "tagline": "Sync Acme",
    "description": "Keeps Acme in step.",
    "category": "crm",
    "logo_url": "https://cdn.example.com/logo.png",
    "website_url": "https://acme.example.com",
    "install_url": "https://acme.example.com/install",
    "support_url": "https://acme.example.com/help",
    "privacy_url": "https://acme.example.com/privacy",
    "developer": "Acme Inc",
    "scopes": 3,
    "permissions": [
        {
            "name": "READ_CONTACTS",
            "value": 1,
            "description": "View contacts",
            "category": "read",
        }
    ],
    "status": "featured",
    "listed": True,
    "installs": 42,
    "installed": False,
    "published_at": TS,
}


def _check_app(app: Any) -> None:
    assert app.application_id == UUID
    assert app.slug == "acme-sync"
    assert app.name == "Acme Sync"
    assert app.tagline == "Sync Acme"
    assert app.description == "Keeps Acme in step."
    assert app.category == "crm"
    assert app.logo_url == "https://cdn.example.com/logo.png"
    assert app.website_url == "https://acme.example.com"
    assert app.install_url == "https://acme.example.com/install"
    assert app.support_url == "https://acme.example.com/help"
    assert app.privacy_url == "https://acme.example.com/privacy"
    assert app.developer == "Acme Inc"
    assert app.scopes == 3
    assert app.permissions[0].name == "READ_CONTACTS"
    assert app.permissions[0].value == 1
    assert app.permissions[0].description == "View contacts"
    assert app.permissions[0].category == "read"
    assert app.status == "featured"
    assert app.listed is True
    assert app.installs == 42
    assert app.installed is False
    assert app.published_at == TS


@respx.mock
@pytest.mark.anyio
async def test_community_apps(api: Api) -> None:
    route = respx.get(f"{BASE_URL}/integrations/community").mock(
        return_value=httpx.Response(200, json=_data([COMMUNITY_APP]))
    )
    apps = await api.items("integrations", "community_apps", limit=50)
    assert dict(_last(route).url.params) == {"limit": "50"}
    _check_app(apps[0])

    one = respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=COMMUNITY_APP)
    )
    _check_app(await api.call("integrations", "community_app", "acme-sync"))
    assert _last(one).method == "GET"


# -- Apollo ------------------------------------------------------------------------

APOLLO_SOURCE = {
    "id": UUID,
    "organization_id": UUID2,
    "connection_id": CONN,
    "created_by_user_id": UUID2,
    "name": "Webinar",
    "list_id": "L1",
    "list_name": "Webinar list",
    "campaign_id": UUID2,
    "category_ids": [UUID],
    "verified_only": True,
    "recurring": False,
    "enabled": True,
    "status": "running",
    "last_run_at": TS,
    "last_result": {
        "read": 100,
        "imported": 80,
        "updated": 5,
        "skipped": 3,
        "failed": 1,
        "no_email": 4,
        "unverified": 6,
        "suppressed": 2,
        "truncated": True,
        "already_seen": 9,
        "next_page": 3,
    },
    "last_error": "boom",
    "total_imported": 80,
    "created_at": TS,
    "updated_at": TS,
}


def _check_source(src: Any) -> None:
    assert src.id == UUID
    assert src.organization_id == UUID2
    assert src.connection_id == CONN
    assert src.created_by_user_id == UUID2
    assert (src.name, src.list_id, src.list_name) == ("Webinar", "L1", "Webinar list")
    assert src.campaign_id == UUID2
    assert list(src.category_ids) == [UUID]
    assert src.verified_only is True
    assert src.recurring is False
    assert src.enabled is True
    assert src.status == "running"
    assert src.last_run_at == TS
    assert src.last_error == "boom"
    assert src.total_imported == 80
    assert (src.created_at, src.updated_at) == (TS, TS)
    result = src.last_result
    assert (result.read, result.imported, result.updated) == (100, 80, 5)
    assert (result.skipped, result.failed, result.no_email) == (3, 1, 4)
    assert (result.unverified, result.suppressed) == (6, 2)
    assert result.truncated is True
    assert (result.already_seen, result.next_page) == (9, 3)


@respx.mock
@pytest.mark.anyio
async def test_apollo_overview_and_key(api: Api) -> None:
    overview = {
        "connection_id": CONN,
        "label": "Apollo",
        "status": "connected",
        "health": "ok",
        "health_detail": "fine",
        "account_name": "Ada",
        "account_email": "ada@acme.com",
        "sources": 2,
        "total_imported": 160,
        "last_run_at": TS,
    }
    get = respx.get(f"{BASE_URL}/integrations/apollo/{CONN}").mock(
        return_value=httpx.Response(200, json=overview)
    )
    out = await api.call("integrations", "apollo_overview", CONN)
    assert _last(get).method == "GET"
    assert out.connection_id == CONN
    assert (out.label, out.status, out.health) == ("Apollo", "connected", "ok")
    assert out.health_detail == "fine"
    assert (out.account_name, out.account_email) == ("Ada", "ada@acme.com")
    assert (out.sources, out.total_imported, out.last_run_at) == (2, 160, TS)

    put = respx.put(f"{BASE_URL}/integrations/apollo/{CONN}/key").mock(
        return_value=httpx.Response(200, json=overview)
    )
    out = await api.call("integrations", "apollo_replace_key", CONN, api_key="k")
    assert out.account_email == "ada@acme.com"
    assert _last(put).method == "PUT"
    assert _body(put) == {"api_key": "k"}


@respx.mock
@pytest.mark.anyio
async def test_apollo_lists_and_preview(api: Api) -> None:
    respx.get(f"{BASE_URL}/integrations/apollo/{CONN}/lists").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "L1", "name": "Webinar", "count": 120}]}
        )
    )
    lists = await api.items("integrations", "apollo_lists", CONN)
    assert (lists[0].id, lists[0].name, lists[0].count) == ("L1", "Webinar", 120)

    route = respx.post(f"{BASE_URL}/integrations/apollo/{CONN}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 120,
                "sample": [
                    {
                        "apollo_id": "a1",
                        "name": "Ada Lovelace",
                        "email": "ada@acme.com",
                        "email_status": "verified",
                        "title": "CTO",
                        "company": "Acme",
                        "already_in_warmbly": True,
                        "will_import": False,
                    }
                ],
            },
        )
    )
    preview = await api.call(
        "integrations",
        "apollo_preview_import",
        CONN,
        list_id="L1",
        verified_only=False,
    )
    assert _body(route) == {"list_id": "L1", "verified_only": False}
    assert preview.total == 120
    row = preview.sample[0]
    assert (row.apollo_id, row.name, row.email) == (
        "a1",
        "Ada Lovelace",
        "ada@acme.com",
    )
    assert (row.email_status, row.title, row.company) == ("verified", "CTO", "Acme")
    assert row.already_in_warmbly is True
    assert row.will_import is False
    await api.call("integrations", "apollo_preview_import", CONN, list_id="L1")
    assert _body(route) == {"list_id": "L1"}


@respx.mock
@pytest.mark.anyio
async def test_apollo_import_sources(api: Api) -> None:
    base = f"{BASE_URL}/integrations/apollo/{CONN}/import-sources"
    respx.get(base).mock(
        return_value=httpx.Response(200, json={"data": [APOLLO_SOURCE]})
    )
    sources = await api.items("integrations", "apollo_import_sources", CONN)
    _check_source(sources[0])

    create = respx.post(base).mock(return_value=httpx.Response(201, json=APOLLO_SOURCE))
    _check_source(
        await api.call(
            "integrations",
            "apollo_create_import_source",
            CONN,
            list_id="L1",
            list_name="Webinar list",
            name="Webinar",
            campaign_id=UUID2,
            category_ids=[UUID],
            verified_only=True,
            recurring=False,
        )
    )
    assert _body(create) == {
        "name": "Webinar",
        "list_id": "L1",
        "list_name": "Webinar list",
        "campaign_id": UUID2,
        "category_ids": [UUID],
        "verified_only": True,
        "recurring": False,
    }
    assert _last(create).headers.get("idempotency-key")
    await api.call("integrations", "apollo_create_import_source", CONN, list_id="L1")
    assert _body(create) == {"list_id": "L1"}

    patch = respx.patch(f"{base}/{UUID}").mock(
        return_value=httpx.Response(200, json=APOLLO_SOURCE)
    )
    _check_source(
        await api.call(
            "integrations",
            "apollo_update_import_source",
            CONN,
            UUID,
            name="Renamed",
            campaign_id=None,
            category_ids=[],
            verified_only=False,
            recurring=True,
            enabled=False,
        )
    )
    assert _body(patch) == {
        "name": "Renamed",
        "campaign_id": None,
        "category_ids": [],
        "verified_only": False,
        "recurring": True,
        "enabled": False,
    }
    await api.call(
        "integrations", "apollo_update_import_source", CONN, UUID, enabled=True
    )
    assert _body(patch) == {"enabled": True}

    run = respx.post(f"{base}/{UUID}/run").mock(
        return_value=httpx.Response(200, json=APOLLO_SOURCE)
    )
    _check_source(
        await api.call("integrations", "apollo_run_import_source", CONN, UUID)
    )
    assert _last(run).method == "POST"

    delete = respx.delete(f"{base}/{UUID}").mock(return_value=httpx.Response(204))
    out = await api.call("integrations", "apollo_delete_import_source", CONN, UUID)
    assert _last(delete).method == "DELETE"
    assert out.deleted is None


APOLLO_RUN = {
    "id": UUID,
    "organization_id": UUID2,
    "connection_id": CONN,
    "requested_by_user_id": UUID2,
    "overwrite": True,
    "status": "running",
    "total": 50,
    "processed": 20,
    "enriched": 15,
    "not_found": 4,
    "failed": 1,
    "credits_consumed": 15,
    "last_error": "none",
    "started_at": TS,
    "finished_at": "2026-05-01T11:00:00Z",
    "created_at": TS,
    "updated_at": TS,
}


def _check_run(run: Any) -> None:
    assert (run.id, run.organization_id, run.connection_id) == (UUID, UUID2, CONN)
    assert run.requested_by_user_id == UUID2
    assert run.overwrite is True
    assert run.status == "running"
    assert (run.total, run.processed, run.enriched) == (50, 20, 15)
    assert (run.not_found, run.failed, run.credits_consumed) == (4, 1, 15)
    assert run.last_error == "none"
    assert run.started_at == TS
    assert run.finished_at == "2026-05-01T11:00:00Z"
    assert (run.created_at, run.updated_at) == (TS, TS)


@respx.mock
@pytest.mark.anyio
async def test_apollo_enrichments(api: Api) -> None:
    base = f"{BASE_URL}/integrations/apollo/{CONN}/enrichments"
    listing = respx.get(base).mock(
        return_value=httpx.Response(200, json={"data": [APOLLO_RUN]})
    )
    runs = await api.items("integrations", "apollo_enrichments", CONN, limit=5)
    assert dict(_last(listing).url.params) == {"limit": "5"}
    _check_run(runs[0])

    start = respx.post(base).mock(return_value=httpx.Response(202, json=APOLLO_RUN))
    _check_run(
        await api.call(
            "integrations",
            "apollo_start_enrichment",
            CONN,
            select_all=True,
            filters={"query": "acme"},
            exclude=[UUID2],
            overwrite=True,
        )
    )
    assert _body(start) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": [UUID2],
        "overwrite": True,
    }
    assert _last(start).headers.get("idempotency-key")
    await api.call("integrations", "apollo_start_enrichment", CONN, contact_ids=[UUID])
    assert _body(start) == {"contact_ids": [UUID]}

    get = respx.get(f"{base}/{UUID}").mock(
        return_value=httpx.Response(200, json=APOLLO_RUN)
    )
    _check_run(await api.call("integrations", "apollo_enrichment", CONN, UUID))
    assert _last(get).method == "GET"


# -- Clay ----------------------------------------------------------------------------

CLAY = {
    "connection_id": CONN,
    "label": "Clay",
    "status": "connected",
    "health": "ok",
    "inbound_url_minted": True,
    "defaults": {
        "campaign_id": UUID,
        "category_ids": [UUID2],
        "segment_ids": [UUID],
        "dedup": "update",
        "subscribed": True,
    },
    "outbound": {
        "webhook_url_set": True,
        "webhook_host": "api.clay.com",
        "auth_token_set": False,
        "events": ["reply.received"],
    },
    "stats": {
        "received": 10,
        "created": 6,
        "updated": 2,
        "skipped": 1,
        "failed": 1,
        "last_received_at": TS,
        "last_error": "bad row",
    },
    "available_events": ["reply.received", "email.bounced"],
}


def _check_clay(clay: Any) -> None:
    assert (clay.connection_id, clay.label, clay.status) == (CONN, "Clay", "connected")
    assert clay.health == "ok"
    assert clay.inbound_url_minted is True
    assert clay.defaults.campaign_id == UUID
    assert list(clay.defaults.category_ids) == [UUID2]
    assert list(clay.defaults.segment_ids) == [UUID]
    assert clay.defaults.dedup == "update"
    assert clay.defaults.subscribed is True
    assert clay.outbound.webhook_url_set is True
    assert clay.outbound.webhook_host == "api.clay.com"
    assert clay.outbound.auth_token_set is False
    assert list(clay.outbound.events) == ["reply.received"]
    stats = clay.stats
    assert (stats.received, stats.created, stats.updated) == (10, 6, 2)
    assert (stats.skipped, stats.failed) == (1, 1)
    assert stats.last_received_at == TS
    assert stats.last_error == "bad row"
    assert list(clay.available_events) == ["reply.received", "email.bounced"]


@respx.mock
@pytest.mark.anyio
async def test_clay_settings(api: Api) -> None:
    url = f"{BASE_URL}/integrations/clay/{CONN}"
    get = respx.get(url).mock(return_value=httpx.Response(200, json=CLAY))
    _check_clay(await api.call("integrations", "clay_settings", CONN))
    assert _last(get).method == "GET"

    patch = respx.patch(url).mock(return_value=httpx.Response(200, json=CLAY))
    _check_clay(
        await api.call(
            "integrations",
            "clay_update_settings",
            CONN,
            defaults={"dedup": "update"},
            webhook_url="https://api.clay.com/hook",
            auth_token="tok",
            events=["reply.received"],
        )
    )
    assert _last(patch).method == "PATCH"
    assert _body(patch) == {
        "defaults": {"dedup": "update"},
        "webhook_url": "https://api.clay.com/hook",
        "auth_token": "tok",
        "events": ["reply.received"],
    }
    await api.call("integrations", "clay_update_settings", CONN, webhook_url="")
    assert _body(patch) == {"webhook_url": ""}


# -- Salesforce ------------------------------------------------------------------------

SF_SETTINGS = {
    "enabled": True,
    "matching": {
        "prefer": "contact",
        "create_when": "reply",
        "create_as": "lead",
        "lead_source": "Warmbly",
        "lead_status": "Open",
        "owner": "fixed",
        "owner_id": "005xx",
        "run_assignment_rules": True,
    },
    "activity": {
        "sent": True,
        "replied": True,
        "opened": False,
        "clicked": False,
        "bounced": True,
        "unsubscribed": True,
        "meeting_booked": True,
        "include_body": True,
        "assign_to": "record_owner",
        "relate_to_opportunity": True,
    },
    "writeback": {
        "lead_status_on_sent": "Working",
        "lead_status_on_reply": {"positive": "Qualified"},
        "lead_status_on_meeting": "Meeting",
        "never_move_backwards": True,
    },
    "inbound": {
        "opt_out": "both",
        "pause_on_converted": True,
        "pause_on_statuses": ["Closed"],
        "pause_on_open_opportunity": False,
    },
    "field_map": [
        {
            "object": "Lead",
            "warmbly": "first_name",
            "salesforce": "FirstName",
            "direction": "both",
            "policy": "if_empty",
        }
    ],
    "daily_api_budget": 5000,
}


def _check_sf_settings(s: Any) -> None:
    assert s.enabled is True
    m = s.matching
    assert (m.prefer, m.create_when, m.create_as) == ("contact", "reply", "lead")
    assert (m.lead_source, m.lead_status) == ("Warmbly", "Open")
    assert (m.owner, m.owner_id, m.run_assignment_rules) == ("fixed", "005xx", True)
    a = s.activity
    assert (a.sent, a.replied, a.opened, a.clicked) == (True, True, False, False)
    assert (a.bounced, a.unsubscribed, a.meeting_booked) == (True, True, True)
    assert (a.include_body, a.assign_to) == (True, "record_owner")
    assert a.relate_to_opportunity is True
    w = s.writeback
    assert w.lead_status_on_sent == "Working"
    assert w.lead_status_on_reply == {"positive": "Qualified"}
    assert w.lead_status_on_meeting == "Meeting"
    assert w.never_move_backwards is True
    i = s.inbound
    assert i.opt_out == "both"
    assert i.pause_on_converted is True
    assert list(i.pause_on_statuses) == ["Closed"]
    assert i.pause_on_open_opportunity is False
    rule = s.field_map[0]
    assert (rule.object, rule.warmbly, rule.salesforce) == (
        "Lead",
        "first_name",
        "FirstName",
    )
    assert (rule.direction, rule.policy) == ("both", "if_empty")
    assert s.daily_api_budget == 5000


@respx.mock
@pytest.mark.anyio
async def test_salesforce_overview(api: Api) -> None:
    route = respx.get(f"{BASE_URL}/integrations/salesforce/{CONN}/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "connection_id": CONN,
                "label": "Prod",
                "status": "connected",
                "health": "ok",
                "health_detail": "fine",
                "org": {
                    "id": "00D1",
                    "instance_url": "https://acme.my.salesforce.com",
                    "environment": "production",
                    "login_host": "login.salesforce.com",
                    "user_id": "005xx",
                    "account": "ada@acme.com",
                },
                "api": {"used": 10, "max": 100000, "calls_today": 50, "budget": 20000},
                "counts": {
                    "pending": 1,
                    "synced_24h": 2,
                    "failed": 3,
                    "skipped_24h": 4,
                    "linked_records": 5,
                },
                "last_pull_at": TS,
                "last_pull_error": "timeout",
                "settings_enabled": True,
                "checks": [
                    {
                        "key": "lead_read",
                        "label": "Read Leads",
                        "ok": False,
                        "detail": "no",
                    }
                ],
            },
        )
    )
    out = await api.call("integrations", "salesforce_overview", CONN, checks=True)
    assert dict(_last(route).url.params) == {"checks": "1"}
    assert (out.connection_id, out.label, out.status) == (CONN, "Prod", "connected")
    assert (out.health, out.health_detail) == ("ok", "fine")
    assert out.org.instance_url == "https://acme.my.salesforce.com"
    assert (out.org.id, out.org.environment) == ("00D1", "production")
    assert (out.org.login_host, out.org.user_id) == ("login.salesforce.com", "005xx")
    assert out.org.account == "ada@acme.com"
    assert (out.api.used, out.api.max) == (10, 100000)
    assert (out.api.calls_today, out.api.budget) == (50, 20000)
    assert (out.counts.pending, out.counts.synced_24h, out.counts.failed) == (1, 2, 3)
    assert (out.counts.skipped_24h, out.counts.linked_records) == (4, 5)
    assert (out.last_pull_at, out.last_pull_error) == (TS, "timeout")
    assert out.settings_enabled is True
    check = out.checks[0]
    assert (check.key, check.label, check.ok, check.detail) == (
        "lead_read",
        "Read Leads",
        False,
        "no",
    )
    await api.call("integrations", "salesforce_overview", CONN)
    assert not _last(route).url.params


@respx.mock
@pytest.mark.anyio
async def test_salesforce_settings(api: Api) -> None:
    url = f"{BASE_URL}/integrations/salesforce/{CONN}/settings"
    get = respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "settings": SF_SETTINGS,
                "warmbly_fields": [{"key": "first_name", "label": "First name"}],
                "defaults": SF_SETTINGS,
            },
        )
    )
    out = await api.call("integrations", "get_salesforce_settings", CONN)
    assert _last(get).method == "GET"
    _check_sf_settings(out.settings)
    _check_sf_settings(out.defaults)
    assert out.warmbly_fields[0].key == "first_name"
    assert out.warmbly_fields[0].label == "First name"

    put = respx.put(url).mock(
        return_value=httpx.Response(200, json={"settings": SF_SETTINGS})
    )
    out = await api.call(
        "integrations", "set_salesforce_settings", CONN, settings=SF_SETTINGS
    )
    _check_sf_settings(out.settings)
    assert _last(put).method == "PUT"
    assert _body(put) == SF_SETTINGS


@respx.mock
@pytest.mark.anyio
async def test_salesforce_metadata_and_pickers(api: Api) -> None:
    base = f"{BASE_URL}/integrations/salesforce/{CONN}"
    field = {
        "name": "Status",
        "label": "Lead Status",
        "type": "picklist",
        "createable": True,
        "updateable": True,
        "calculated": False,
        "custom": False,
        "picklist": [{"value": "Open", "label": "Open - Not Contacted"}],
    }
    respx.get(f"{base}/metadata").mock(
        return_value=httpx.Response(
            200,
            json={
                "lead_fields": [field],
                "contact_fields": [field],
                "lead_statuses": [{"value": "Open", "label": "Open"}],
                "lead_sources": [{"value": "Web", "label": "Web"}],
            },
        )
    )
    meta = await api.call("integrations", "salesforce_metadata", CONN)
    f = meta.lead_fields[0]
    assert (f.name, f.label, f.type) == ("Status", "Lead Status", "picklist")
    assert (f.createable, f.updateable, f.calculated, f.custom) == (
        True,
        True,
        False,
        False,
    )
    assert f.picklist[0].label == "Open - Not Contacted"
    assert meta.contact_fields[0].name == "Status"
    assert meta.lead_statuses[0].value == "Open"
    assert meta.lead_sources[0].label == "Web"

    users = respx.get(f"{base}/users").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "005xx", "name": "Ada", "email": "ada@acme.com"}]},
        )
    )
    got = await api.items("integrations", "salesforce_users", CONN, q="ada")
    assert dict(_last(users).url.params) == {"q": "ada"}
    assert (got[0].id, got[0].name, got[0].email) == ("005xx", "Ada", "ada@acme.com")

    views = respx.get(f"{base}/list-views").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "00B1", "label": "Hot", "object": "Lead"}]}
        )
    )
    got = await api.items("integrations", "salesforce_list_views", CONN, object="Lead")
    assert dict(_last(views).url.params) == {"object": "Lead"}
    assert (got[0].id, got[0].label, got[0].object) == ("00B1", "Hot", "Lead")

    campaigns = respx.get(f"{base}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "701",
                        "name": "Webinar",
                        "status": "Planned",
                        "type": "Email",
                        "member_count": 40,
                    }
                ]
            },
        )
    )
    got = await api.items("integrations", "salesforce_campaigns", CONN, q="web")
    assert dict(_last(campaigns).url.params) == {"q": "web"}
    assert (got[0].id, got[0].name, got[0].status) == ("701", "Webinar", "Planned")
    assert (got[0].type, got[0].member_count) == ("Email", 40)


SF_SOURCE = {
    "id": UUID,
    "organization_id": UUID2,
    "connection_id": CONN,
    "created_by_user_id": UUID2,
    "name": "Hot leads",
    "source_kind": "list_view",
    "object": "Lead",
    "source_id": "00B1",
    "source_label": "Hot",
    "campaign_id": UUID2,
    "category_ids": [UUID],
    "recurring": True,
    "enabled": True,
    "status": "running",
    "last_run_at": TS,
    "last_result": {
        "read": 10,
        "imported": 6,
        "updated": 1,
        "linked": 2,
        "skipped": 3,
        "failed": 4,
        "no_email": 5,
        "opted_out": 7,
        "truncated": True,
    },
    "last_error": "boom",
    "total_imported": 6,
    "created_at": TS,
    "updated_at": TS,
}


def _check_sf_source(src: Any) -> None:
    assert (src.id, src.organization_id, src.connection_id) == (UUID, UUID2, CONN)
    assert src.created_by_user_id == UUID2
    assert (src.name, src.source_kind, src.object) == ("Hot leads", "list_view", "Lead")
    assert (src.source_id, src.source_label) == ("00B1", "Hot")
    assert src.campaign_id == UUID2
    assert list(src.category_ids) == [UUID]
    assert (src.recurring, src.enabled, src.status) == (True, True, "running")
    assert src.last_run_at == TS
    assert (src.last_error, src.total_imported) == ("boom", 6)
    assert (src.created_at, src.updated_at) == (TS, TS)
    r = src.last_result
    assert (r.read, r.imported, r.updated, r.linked) == (10, 6, 1, 2)
    assert (r.skipped, r.failed, r.no_email, r.opted_out) == (3, 4, 5, 7)
    assert r.truncated is True


@respx.mock
@pytest.mark.anyio
async def test_salesforce_preview_import(api: Api) -> None:
    route = respx.post(
        f"{BASE_URL}/integrations/salesforce/{CONN}/import/preview"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 90,
                "sample": [
                    {
                        "record_id": "00Q1",
                        "object": "Lead",
                        "name": "Ada Lovelace",
                        "email": "ada@acme.com",
                        "company": "Acme",
                        "title": "CTO",
                        "owner_name": "Grace",
                        "status": "Open",
                        "already_linked": True,
                    }
                ],
            },
        )
    )
    out = await api.call(
        "integrations",
        "salesforce_preview_import",
        CONN,
        source_kind="list_view",
        source_id="00B1",
        object="Lead",
    )
    assert _body(route) == {
        "source_kind": "list_view",
        "object": "Lead",
        "source_id": "00B1",
    }
    assert out.total == 90
    row = out.sample[0]
    assert (row.record_id, row.object, row.name) == ("00Q1", "Lead", "Ada Lovelace")
    assert (row.email, row.company, row.title) == ("ada@acme.com", "Acme", "CTO")
    assert (row.owner_name, row.status, row.already_linked) == ("Grace", "Open", True)
    await api.call(
        "integrations",
        "salesforce_preview_import",
        CONN,
        source_kind="campaign",
        source_id="701",
    )
    assert _body(route) == {"source_kind": "campaign", "source_id": "701"}


@respx.mock
@pytest.mark.anyio
async def test_salesforce_import_sources(api: Api) -> None:
    base = f"{BASE_URL}/integrations/salesforce/{CONN}/import-sources"
    respx.get(base).mock(return_value=httpx.Response(200, json={"data": [SF_SOURCE]}))
    _check_sf_source(
        (await api.items("integrations", "salesforce_import_sources", CONN))[0]
    )

    create = respx.post(base).mock(return_value=httpx.Response(201, json=SF_SOURCE))
    _check_sf_source(
        await api.call(
            "integrations",
            "salesforce_create_import_source",
            CONN,
            source_kind="list_view",
            source_id="00B1",
            object="Lead",
            source_label="Hot",
            name="Hot leads",
            campaign_id=UUID2,
            category_ids=[UUID],
            recurring=True,
        )
    )
    assert _body(create) == {
        "name": "Hot leads",
        "source_kind": "list_view",
        "object": "Lead",
        "source_id": "00B1",
        "source_label": "Hot",
        "campaign_id": UUID2,
        "category_ids": [UUID],
        "recurring": True,
    }
    assert _last(create).headers.get("idempotency-key")
    await api.call(
        "integrations",
        "salesforce_create_import_source",
        CONN,
        source_kind="campaign",
        source_id="701",
    )
    assert _body(create) == {"source_kind": "campaign", "source_id": "701"}

    patch = respx.patch(f"{base}/{UUID}").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(
        await api.call(
            "integrations",
            "salesforce_update_import_source",
            CONN,
            UUID,
            name="Renamed",
            campaign_id=None,
            category_ids=[UUID],
            recurring=False,
            enabled=False,
        )
    )
    assert _body(patch) == {
        "name": "Renamed",
        "campaign_id": None,
        "category_ids": [UUID],
        "recurring": False,
        "enabled": False,
    }

    run = respx.post(f"{base}/{UUID}/run").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(
        await api.call("integrations", "salesforce_run_import_source", CONN, UUID)
    )
    assert _last(run).method == "POST"

    delete = respx.delete(f"{base}/{UUID}").mock(return_value=httpx.Response(204))
    out = await api.call("integrations", "salesforce_delete_import_source", CONN, UUID)
    assert _last(delete).method == "DELETE"
    assert out.id is None


@respx.mock
@pytest.mark.anyio
async def test_salesforce_activity(api: Api) -> None:
    base = f"{BASE_URL}/integrations/salesforce/{CONN}"
    listing = respx.get(f"{base}/activity").mock(
        return_value=httpx.Response(
            200,
            json=_data(
                [
                    {
                        "id": UUID,
                        "organization_id": UUID2,
                        "connection_id": CONN,
                        "contact_id": UUID2,
                        "contact_email": "ada@acme.com",
                        "kind": "replied",
                        "payload": {"campaign": "Spring"},
                        "status": "failed",
                        "attempts": 3,
                        "next_attempt_at": TS,
                        "record_id": "00Q1",
                        "task_id": "00T1",
                        "detail": "locked",
                        "occurred_at": TS,
                        "created_at": TS,
                        "processed_at": TS,
                    }
                ]
            ),
        )
    )
    rows = await api.items(
        "integrations",
        "salesforce_activity",
        CONN,
        status="failed",
        contact_id=UUID2,
        limit=25,
    )
    assert dict(_last(listing).url.params) == {
        "status": "failed",
        "contact_id": UUID2,
        "limit": "25",
    }
    row = rows[0]
    assert (row.id, row.organization_id, row.connection_id) == (UUID, UUID2, CONN)
    assert (row.contact_id, row.contact_email) == (UUID2, "ada@acme.com")
    assert (row.kind, row.status, row.attempts) == ("replied", "failed", 3)
    assert row.payload == {"campaign": "Spring"}
    assert row.next_attempt_at == TS
    assert (row.record_id, row.task_id, row.detail) == ("00Q1", "00T1", "locked")
    assert (row.occurred_at, row.created_at, row.processed_at) == (TS, TS, TS)

    retry = respx.post(f"{base}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 2})
    )
    out = await api.call(
        "integrations", "salesforce_retry_activity", CONN, ids=[UUID, UUID2]
    )
    assert out.requeued == 2
    assert _body(retry) == {"ids": [UUID, UUID2]}

    now = respx.post(f"{base}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await api.call("integrations", "salesforce_sync_now", CONN)).ok is True
    assert _last(now).method == "POST"


# -- lead sync -------------------------------------------------------------------------


@respx.mock
@pytest.mark.anyio
async def test_lead_sync_spreadsheet_and_preview(api: Api) -> None:
    sheet = respx.post(f"{BASE_URL}/lead-sync/google/spreadsheet").mock(
        return_value=httpx.Response(
            200,
            json={
                "sheet_id": "abc",
                "title": "Leads",
                "tabs": [{"title": "Sheet1", "index": 0}],
            },
        )
    )
    out = await api.call("lead_sync", "spreadsheet", connection_id=CONN, sheet_id="abc")
    assert _body(sheet) == {"connection_id": CONN, "sheet_id": "abc"}
    assert out.sheet_id == "abc"
    assert out.title == "Leads"
    assert out.tabs[0]["title"] == "Sheet1"

    preview = respx.post(f"{BASE_URL}/lead-sync/google/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "filename": "Leads / Sheet1",
                "format": "sheet",
                "total_rows": 2,
                "columns": ["Email", "Name"],
                "has_header": True,
                "sample_rows": [["ada@acme.com", "Ada"]],
                "suggested_mapping": [{"column": 0, "field": "email"}],
                "inferred_columns": [1],
                "column_stats": [{"filled": 2, "distinct": 2, "samples": ["Ada"]}],
                "mapping_source": "saved",
            },
        )
    )
    got = await api.call(
        "lead_sync", "preview", connection_id=CONN, sheet_id="abc", tab_title="Sheet1"
    )
    assert _body(preview) == {
        "connection_id": CONN,
        "sheet_id": "abc",
        "tab_title": "Sheet1",
    }
    assert (got.filename, got.format, got.total_rows) == ("Leads / Sheet1", "sheet", 2)
    assert list(got.columns) == ["Email", "Name"]
    assert got.has_header is True
    assert [list(r) for r in got.sample_rows] == [["ada@acme.com", "Ada"]]
    assert got.suggested_mapping[0]["field"] == "email"
    assert list(got.inferred_columns) == [1]
    assert got.column_stats[0]["filled"] == 2
    assert got.mapping_source == "saved"


LEAD_SOURCE = {
    "id": UUID,
    "organization_id": UUID2,
    "created_by_user_id": UUID2,
    "provider": "google_sheets",
    "connection_id": CONN,
    "sheet_id": "abc",
    "sheet_title": "Leads",
    "tab_title": "Sheet1",
    "has_header": True,
    "column_mapping": [{"column": 0, "field": "email"}],
    "dedup": "update",
    "target_campaign_id": UUID2,
    "category_ids": [UUID],
    "segment_ids": [UUID2],
    "subscribed_default": True,
    "label": "Spring",
    "status": "idle",
}


@respx.mock
@pytest.mark.anyio
async def test_lead_sync_sources_with_segments(api: Api) -> None:
    listing = respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(200, json={"data": [LEAD_SOURCE]})
    )
    sources = await api.items("lead_sync", "list_sources", segment_id=UUID2)
    assert dict(_last(listing).url.params) == {"segment_id": UUID2}
    assert list(sources[0].segment_ids) == [UUID2]
    assert list(sources[0].category_ids) == [UUID]

    create = respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json=LEAD_SOURCE)
    )
    src = await api.call(
        "lead_sync",
        "create_source",
        connection_id=CONN,
        sheet_id="abc",
        column_mapping=[{"column": 0, "field": "email"}],
        segment_ids=[UUID2],
    )
    assert list(src.segment_ids) == [UUID2]
    assert _body(create) == {
        "connection_id": CONN,
        "sheet_id": "abc",
        "column_mapping": [{"column": 0, "field": "email"}],
        "segment_ids": [UUID2],
    }

    patch = respx.patch(f"{BASE_URL}/lead-sync/sources/{UUID}").mock(
        return_value=httpx.Response(200, json=LEAD_SOURCE)
    )
    src = await api.call("lead_sync", "update_source", UUID, segment_ids=[])
    assert list(src.segment_ids) == [UUID2]
    assert _body(patch) == {"segment_ids": []}


# -- oauth applications ------------------------------------------------------------------


@respx.mock
@pytest.mark.anyio
async def test_oauth_application_suspension_fields(api: Api) -> None:
    respx.get(f"{BASE_URL}/oauth/applications/{UUID}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": UUID,
                "name": "Acme",
                "status": "active",
                "suspended_at": TS,
                "suspended_reason": "policy",
            },
        )
    )
    app = await api.call("oauth_applications", "retrieve", UUID)
    assert app.suspended_at == TS
    assert app.suspended_reason == "policy"
