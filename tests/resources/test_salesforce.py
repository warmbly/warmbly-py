"""Tests for the Salesforce sync routes and the community directory, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CONN = "6f1d0c52-3b7a-4a55-9d57-0c4f8a0e1111"
SF = f"{BASE_URL}/integrations/salesforce/{CONN}"
SOURCE = "0a1b2c3d-0000-4000-8000-00000000aaaa"
CONTACT = "c0ffee00-0000-4000-8000-000000000001"
LINK = "11111111-2222-4333-8444-555555555555"


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


def _page(data: list[dict], next_cursor: str | None = None) -> dict:
    return {
        "data": data,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
            "total": len(data),
        },
    }


# -- realistic payloads (built from the Go structs) -------------------------
SETTINGS = {
    "enabled": True,
    "matching": {
        "prefer": "contact",
        "create_when": "reply",
        "create_as": "Lead",
        "lead_source": "Warmbly",
        "lead_status": "Open",
        "owner": "connected_user",
        "owner_id": "005xx0000012345AAA",
        "run_assignment_rules": False,
    },
    "activity": {
        "sent": True,
        "replied": True,
        "opened": False,
        "clicked": False,
        "bounced": True,
        "unsubscribed": True,
        "meeting_booked": True,
        "include_body": False,
        "assign_to": "record_owner",
        "relate_to_opportunity": True,
    },
    "writeback": {
        "lead_status_on_sent": "Working",
        "lead_status_on_reply": {"positive": "Qualified", "any": "Working"},
        "lead_status_on_meeting": "Meeting Booked",
        "never_move_backwards": True,
    },
    "inbound": {
        "opt_out": "both",
        "pause_on_converted": True,
        "pause_on_statuses": ["Closed Lost"],
        "pause_on_open_opportunity": False,
    },
    "field_map": [
        {
            "object": "Lead",
            "warmbly": "phone",
            "salesforce": "Phone",
            "direction": "both",
            "policy": "prefer_salesforce",
        }
    ],
    "daily_api_budget": 5000,
}

OVERVIEW = {
    "connection_id": CONN,
    "label": "Production",
    "status": "connected",
    "health": "healthy",
    "health_detail": "all good",
    "org": {
        "id": "00D000000000001",
        "instance_url": "https://acme.my.salesforce.com",
        "environment": "production",
        "login_host": "login.salesforce.com",
        "user_id": "005xx0000012345AAA",
        "account": "Acme",
    },
    "api": {"used": 120, "max": 15000, "calls_today": 40, "budget": 3000},
    "counts": {
        "pending": 3,
        "synced_24h": 40,
        "failed": 1,
        "skipped_24h": 2,
        "linked_records": 310,
    },
    "last_pull_at": "2026-10-01T10:00:00Z",
    "last_pull_error": "timeout",
    "settings_enabled": True,
    "checks": [
        {"key": "task_subtype", "label": "Email icon", "ok": False, "detail": "x"}
    ],
}

SOURCE_JSON = {
    "id": SOURCE,
    "organization_id": "0a1b2c3d-0000-4000-8000-0000000000ff",
    "connection_id": CONN,
    "created_by_user_id": "0a1b2c3d-0000-4000-8000-0000000000ee",
    "name": "Hot leads",
    "source_kind": "list_view",
    "object": "Lead",
    "source_id": "00B000000000001AAA",
    "source_label": "Hot leads view",
    "campaign_id": "0a1b2c3d-0000-4000-8000-0000000000cc",
    "category_ids": ["0a1b2c3d-0000-4000-8000-0000000000dd"],
    "recurring": True,
    "enabled": True,
    "status": "idle",
    "last_run_at": "2026-10-01T10:00:00Z",
    "last_result": {
        "read": 10,
        "imported": 6,
        "updated": 1,
        "linked": 2,
        "skipped": 1,
        "failed": 0,
        "no_email": 1,
        "opted_out": 1,
        "truncated": True,
    },
    "last_error": "none",
    "total_imported": 6,
    "created_at": "2026-09-01T10:00:00Z",
    "updated_at": "2026-10-01T10:00:00Z",
}

PANEL = {
    "connections": [
        {
            "id": CONN,
            "label": "Production",
            "environment": "production",
            "instance_url": "https://acme.my.salesforce.com",
        }
    ],
    "records": [
        {
            "link_id": LINK,
            "connection_id": CONN,
            "connection_label": "Production",
            "object": "Lead",
            "id": "00Qxx0000012345AAA",
            "url": "https://acme.my.salesforce.com/00Q",
            "name": "Ada Lovelace",
            "title": "CTO",
            "company": "Analytical",
            "email": "ada@example.com",
            "phone": "+15550100",
            "status": "Working",
            "owner": {"id": "005xx", "name": "Sam Seller"},
            "account": {"id": "001xx", "name": "Analytical", "url": "https://x/001"},
            "is_converted": False,
            "opted_out": False,
            "lead_source": "Web",
            "opportunities": [
                {
                    "id": "006xx",
                    "name": "Big deal",
                    "stage": "Prospecting",
                    "amount": 12000.5,
                    "close_date": "2026-12-01",
                    "is_closed": False,
                    "is_won": False,
                    "url": "https://x/006",
                }
            ],
            "tasks": [
                {
                    "id": "00Txx",
                    "subject": "Email: Hello",
                    "date": "2026-10-01",
                    "status": "Completed",
                    "owner_name": "Sam Seller",
                    "url": "https://x/00T",
                    "from_warmbly": True,
                }
            ],
            "linked_by": "auto",
            "last_synced_at": "2026-10-01T10:00:00Z",
            "last_pushed_at": "2026-10-01T09:00:00Z",
            "sync": {"pending": 1, "failed": 2, "synced": 3, "last_error": "boom"},
            "stale": True,
            "error": "refresh failed",
        }
    ],
    "can_sync": True,
}

ACTIVITY = {
    "id": "0a1b2c3d-0000-4000-8000-0000000000a1",
    "organization_id": "0a1b2c3d-0000-4000-8000-0000000000ff",
    "connection_id": CONN,
    "contact_id": CONTACT,
    "contact_email": "ada@example.com",
    "kind": "sent",
    "payload": {"campaign": "Q4"},
    "status": "failed",
    "attempts": 3,
    "next_attempt_at": "2026-10-01T11:00:00Z",
    "record_id": "00Qxx",
    "task_id": "00Txx",
    "detail": "INVALID_FIELD",
    "occurred_at": "2026-10-01T09:00:00Z",
    "created_at": "2026-10-01T09:00:01Z",
    "processed_at": "2026-10-01T09:05:00Z",
}

COMMUNITY_APP = {
    "application_id": "0a1b2c3d-0000-4000-8000-0000000000b1",
    "slug": "acme-sync",
    "name": "Acme Sync",
    "tagline": "Sync things",
    "description": "Longer text",
    "category": "crm",
    "logo_url": "https://x/logo.png",
    "website_url": "https://acme.example",
    "install_url": "https://acme.example/install",
    "support_url": "https://acme.example/support",
    "privacy_url": "https://acme.example/privacy",
    "developer": "Acme Inc",
    "scopes": 5,
    "permissions": [
        {
            "name": "READ_CONTACTS",
            "value": 4,
            "description": "View contact lists",
            "category": "read",
        }
    ],
    "status": "featured",
    "listed": True,
    "installs": 42,
    "installed": False,
    "published_at": "2026-09-01T10:00:00Z",
}


def _check_settings(s: Any) -> None:
    assert s.enabled is True
    assert s.matching.prefer == "contact"
    assert s.matching.create_when == "reply"
    assert s.matching.create_as == "Lead"
    assert s.matching.lead_source == "Warmbly"
    assert s.matching.lead_status == "Open"
    assert s.matching.owner == "connected_user"
    assert s.matching.owner_id == "005xx0000012345AAA"
    assert s.matching.run_assignment_rules is False
    assert s.activity.sent is True
    assert s.activity.opened is False
    assert s.activity.assign_to == "record_owner"
    assert s.activity.relate_to_opportunity is True
    assert s.activity.include_body is False
    assert s.activity.meeting_booked is True
    assert s.activity.bounced is True
    assert s.activity.unsubscribed is True
    assert s.activity.replied is True
    assert s.activity.clicked is False
    assert s.writeback.lead_status_on_sent == "Working"
    assert s.writeback.lead_status_on_reply == {
        "positive": "Qualified",
        "any": "Working",
    }
    assert s.writeback.lead_status_on_meeting == "Meeting Booked"
    assert s.writeback.never_move_backwards is True
    assert s.inbound.opt_out == "both"
    assert s.inbound.pause_on_converted is True
    assert list(s.inbound.pause_on_statuses) == ["Closed Lost"]
    assert s.inbound.pause_on_open_opportunity is False
    rule = s.field_map[0]
    assert (rule.object, rule.warmbly, rule.salesforce) == ("Lead", "phone", "Phone")
    assert (rule.direction, rule.policy) == ("both", "prefer_salesforce")
    assert s.daily_api_budget == 5000


def _check_source(src: Any) -> None:
    assert src.id == SOURCE
    assert src.organization_id and src.created_by_user_id
    assert src.connection_id == CONN
    assert src.name == "Hot leads"
    assert src.source_kind == "list_view"
    assert src.object == "Lead"
    assert src.source_id == "00B000000000001AAA"
    assert src.source_label == "Hot leads view"
    assert src.campaign_id
    assert list(src.category_ids) == ["0a1b2c3d-0000-4000-8000-0000000000dd"]
    assert src.recurring is True
    assert src.enabled is True
    assert src.status == "idle"
    assert src.last_run_at and src.last_error == "none"
    assert src.total_imported == 6
    assert src.created_at and src.updated_at
    r = src.last_result
    assert (r.read, r.imported, r.updated, r.linked) == (10, 6, 1, 2)
    assert (r.skipped, r.failed, r.no_email, r.opted_out) == (1, 0, 1, 1)
    assert r.truncated is True


def _check_panel(p: Any) -> None:
    assert p.can_sync is True
    conn = p.connections[0]
    assert (conn.id, conn.label, conn.environment) == (CONN, "Production", "production")
    assert conn.instance_url
    rec = p.records[0]
    assert rec.link_id == LINK
    assert rec.connection_id == CONN
    assert rec.connection_label == "Production"
    assert rec.object == "Lead"
    assert rec.id == "00Qxx0000012345AAA"
    assert rec.url and rec.name == "Ada Lovelace" and rec.title == "CTO"
    assert rec.company and rec.email and rec.phone and rec.status == "Working"
    assert rec.owner.name == "Sam Seller" and rec.owner.id == "005xx"
    assert rec.account.name == "Analytical" and rec.account.id and rec.account.url
    assert rec.is_converted is False and rec.opted_out is False
    assert rec.lead_source == "Web"
    opp = rec.opportunities[0]
    assert (opp.id, opp.name, opp.stage, opp.amount) == (
        "006xx",
        "Big deal",
        "Prospecting",
        12000.5,
    )
    assert opp.close_date == "2026-12-01" and opp.url
    assert opp.is_closed is False and opp.is_won is False
    task = rec.tasks[0]
    assert (task.id, task.subject, task.date, task.status) == (
        "00Txx",
        "Email: Hello",
        "2026-10-01",
        "Completed",
    )
    assert task.owner_name and task.url and task.from_warmbly is True
    assert rec.linked_by == "auto"
    assert rec.last_synced_at and rec.last_pushed_at
    assert (rec.sync.pending, rec.sync.failed, rec.sync.synced) == (1, 2, 3)
    assert rec.sync.last_error == "boom"
    assert rec.stale is True and rec.error == "refresh failed"


def _check_activity(a: Any) -> None:
    assert a.id and a.organization_id and a.connection_id == CONN
    assert a.contact_id == CONTACT and a.contact_email == "ada@example.com"
    assert a.kind == "sent" and a.payload == {"campaign": "Q4"}
    assert a.status == "failed" and a.attempts == 3
    assert a.next_attempt_at and a.record_id and a.task_id
    assert a.detail == "INVALID_FIELD"
    assert a.occurred_at and a.created_at and a.processed_at


def _check_app(app: Any) -> None:
    assert app.application_id and app.slug == "acme-sync"
    assert app.name == "Acme Sync" and app.tagline == "Sync things"
    assert app.description and app.category == "crm"
    assert app.logo_url and app.website_url and app.install_url
    assert app.support_url and app.privacy_url
    assert app.developer == "Acme Inc" and app.scopes == 5
    perm = app.permissions[0]
    assert (perm.name, perm.value, perm.category) == ("READ_CONTACTS", 4, "read")
    assert perm.description
    assert app.status == "featured" and app.listed is True
    assert app.installs == 42 and app.installed is False
    assert app.published_at


def _check_overview(o: Any) -> None:
    assert o.connection_id == CONN and o.label == "Production"
    assert o.status == "connected" and o.health == "healthy"
    assert o.health_detail == "all good"
    assert o.org.id and o.org.instance_url and o.org.environment == "production"
    assert o.org.login_host and o.org.user_id and o.org.account == "Acme"
    assert (o.api.used, o.api.max, o.api.calls_today, o.api.budget) == (
        120,
        15000,
        40,
        3000,
    )
    c = o.counts
    assert (c.pending, c.synced_24h, c.failed, c.skipped_24h, c.linked_records) == (
        3,
        40,
        1,
        2,
        310,
    )
    assert o.last_pull_at and o.last_pull_error == "timeout"
    assert o.settings_enabled is True
    chk = o.checks[0]
    assert (chk.key, chk.label, chk.ok, chk.detail) == (
        "task_subtype",
        "Email icon",
        False,
        "x",
    )


METADATA = {
    "lead_fields": [
        {
            "name": "Status",
            "label": "Lead Status",
            "type": "picklist",
            "createable": True,
            "updateable": True,
            "calculated": False,
            "custom": False,
            "picklist": [{"value": "Open", "label": "Open - Not Contacted"}],
        }
    ],
    "contact_fields": [{"name": "Email", "label": "Email", "type": "email"}],
    "lead_statuses": [{"value": "Open", "label": "Open"}],
    "lead_sources": [{"value": "Web", "label": "Web"}],
}


# -- salesforce: reads ------------------------------------------------------
@respx.mock
def test_salesforce_reads_sync(client: Warmbly) -> None:
    route = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    _check_overview(client.salesforce.overview(CONN, checks=True))
    assert _last(route).method == "GET"
    assert _last(route).url.params.get("checks") == "1"
    client.salesforce.overview(CONN)
    assert "checks" not in _last(route).url.params

    route = respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(
            200,
            json={
                "settings": SETTINGS,
                "warmbly_fields": [{"key": "first_name", "label": "First name"}],
                "defaults": SETTINGS,
            },
        )
    )
    doc = client.salesforce.get_settings(CONN)
    _check_settings(doc.settings)
    _check_settings(doc.defaults)
    assert doc.warmbly_fields[0].key == "first_name"
    assert doc.warmbly_fields[0].label == "First name"
    assert _last(route).url.path == f"/v1/integrations/salesforce/{CONN}/settings"

    route = respx.get(f"{SF}/metadata").mock(
        return_value=httpx.Response(200, json=METADATA)
    )
    meta = client.salesforce.metadata(CONN)
    f = meta.lead_fields[0]
    assert (f.name, f.label, f.type) == ("Status", "Lead Status", "picklist")
    assert f.createable is True and f.updateable is True
    assert f.calculated is False and f.custom is False
    assert f.picklist[0].value == "Open"
    assert f.picklist[0].label == "Open - Not Contacted"
    assert meta.contact_fields[0].name == "Email"
    assert meta.lead_statuses[0].value == "Open"
    assert meta.lead_sources[0].label == "Web"
    assert _last(route).method == "GET"

    route = respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "005xx", "name": "Sam", "email": "sam@x.com"}]}
        )
    )
    users = list(client.salesforce.users(CONN, q="sam"))
    assert (users[0].id, users[0].name, users[0].email) == ("005xx", "Sam", "sam@x.com")
    assert _last(route).url.params.get("q") == "sam"

    route = respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "00B", "label": "Hot", "object": "Lead"}]}
        )
    )
    views = list(client.salesforce.list_views(CONN, object="Lead"))
    assert (views[0].id, views[0].label, views[0].object) == ("00B", "Hot", "Lead")
    assert _last(route).url.params.get("object") == "Lead"

    route = respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "701",
                        "name": "Webinar",
                        "status": "Planned",
                        "type": "Event",
                        "member_count": 12,
                    }
                ]
            },
        )
    )
    camps = list(client.salesforce.campaigns(CONN, q="web"))
    c = camps[0]
    assert (c.id, c.name, c.status, c.type, c.member_count) == (
        "701",
        "Webinar",
        "Planned",
        "Event",
        12,
    )
    assert _last(route).url.params.get("q") == "web"

    route = respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json={"data": [SOURCE_JSON]})
    )
    _check_source(next(iter(client.salesforce.list_import_sources(CONN))))
    assert _last(route).method == "GET"

    route = respx.get(f"{SF}/activity").mock(
        return_value=httpx.Response(200, json=_page([ACTIVITY], next_cursor="c2"))
    )
    page = client.salesforce.list_activity(
        CONN, status="failed", contact_id=CONTACT, limit=25, cursor="c1"
    )
    _check_activity(page.data[0])
    assert page.has_more is True
    q = _last(route).url.params
    assert (q.get("status"), q.get("contact_id"), q.get("limit"), q.get("cursor")) == (
        "failed",
        CONTACT,
        "25",
        "c1",
    )


@respx.mock
@pytest.mark.anyio
async def test_salesforce_reads_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    _check_overview(await aclient.salesforce.overview(CONN, checks=True))
    assert _last(route).url.params.get("checks") == "1"

    respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(
            200, json={"settings": SETTINGS, "warmbly_fields": [], "defaults": SETTINGS}
        )
    )
    doc = await aclient.salesforce.get_settings(CONN)
    _check_settings(doc.settings)
    assert list(doc.warmbly_fields) == []

    respx.get(f"{SF}/metadata").mock(return_value=httpx.Response(200, json=METADATA))
    meta = await aclient.salesforce.metadata(CONN)
    assert meta.lead_fields[0].picklist[0].value == "Open"

    route = respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "005xx", "name": "Sam"}]}
        )
    )
    assert [u.name async for u in aclient.salesforce.users(CONN, q="s")] == ["Sam"]
    assert _last(route).url.params.get("q") == "s"

    route = respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "00B", "object": "Contact"}]}
        )
    )
    assert [
        v.object async for v in aclient.salesforce.list_views(CONN, object="Contact")
    ] == ["Contact"]
    assert _last(route).url.params.get("object") == "Contact"

    route = respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "701", "member_count": 3}]}
        )
    )
    assert [
        c.member_count async for c in aclient.salesforce.campaigns(CONN, q="x")
    ] == [3]
    assert _last(route).url.params.get("q") == "x"

    respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json={"data": [SOURCE_JSON]})
    )
    _check_source((await aclient.salesforce.list_import_sources(CONN)).data[0])

    route = respx.get(f"{SF}/activity").mock(
        return_value=httpx.Response(200, json=_page([ACTIVITY]))
    )
    items = [
        a
        async for a in aclient.salesforce.list_activity(CONN, status="failed", limit=5)
    ]
    _check_activity(items[0])
    assert _last(route).url.params.get("status") == "failed"
    assert _last(route).url.params.get("limit") == "5"


# -- salesforce: writes -----------------------------------------------------
@respx.mock
def test_salesforce_writes_sync(client: Warmbly) -> None:
    route = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": SETTINGS})
    )
    saved = client.salesforce.update_settings(CONN, settings=SETTINGS)
    _check_settings(saved.settings)
    assert _last(route).method == "PUT"
    assert _body(route) == SETTINGS

    route = respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 120,
                "sample": [
                    {
                        "record_id": "00Qxx",
                        "object": "Lead",
                        "name": "Ada Lovelace",
                        "email": "ada@example.com",
                        "company": "Analytical",
                        "title": "CTO",
                        "owner_name": "Sam",
                        "status": "Open",
                        "already_linked": True,
                    }
                ],
            },
        )
    )
    prev = client.salesforce.preview_import(
        CONN, source_kind="list_view", object="Lead", source_id="00B000000000001AAA"
    )
    assert prev.total == 120
    row = prev.sample[0]
    assert (row.record_id, row.object, row.name) == ("00Qxx", "Lead", "Ada Lovelace")
    assert (row.email, row.company, row.title) == (
        "ada@example.com",
        "Analytical",
        "CTO",
    )
    assert (row.owner_name, row.status, row.already_linked) == ("Sam", "Open", True)
    assert _body(route) == {
        "source_kind": "list_view",
        "object": "Lead",
        "source_id": "00B000000000001AAA",
    }

    route = respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SOURCE_JSON)
    )
    _check_source(
        client.salesforce.create_import_source(
            CONN,
            source_kind="list_view",
            object="Lead",
            source_id="00B000000000001AAA",
            name="Hot leads",
            source_label="Hot leads view",
            campaign_id="cmp_1",
            category_ids=["cat_1"],
            recurring=True,
            enabled=True,
        )
    )
    assert _last(route).method == "POST"
    assert _body(route) == {
        "name": "Hot leads",
        "source_kind": "list_view",
        "object": "Lead",
        "source_id": "00B000000000001AAA",
        "source_label": "Hot leads view",
        "campaign_id": "cmp_1",
        "category_ids": ["cat_1"],
        "recurring": True,
        "enabled": True,
    }
    assert _last(route).headers.get("idempotency-key")

    route = respx.patch(f"{SF}/import-sources/{SOURCE}").mock(
        return_value=httpx.Response(200, json=SOURCE_JSON)
    )
    _check_source(
        client.salesforce.update_import_source(
            CONN, SOURCE, name="Renamed", campaign_id=None, enabled=False
        )
    )
    assert _body(route) == {"name": "Renamed", "campaign_id": None, "enabled": False}
    client.salesforce.update_import_source(CONN, SOURCE, recurring=False)
    assert _body(route) == {"recurring": False}

    route = respx.post(f"{SF}/import-sources/{SOURCE}/run").mock(
        return_value=httpx.Response(200, json=SOURCE_JSON)
    )
    _check_source(client.salesforce.run_import_source(CONN, SOURCE))
    assert _last(route).method == "POST"
    assert _last(route).headers.get("idempotency-key")

    route = respx.delete(f"{SF}/import-sources/{SOURCE}").mock(
        return_value=httpx.Response(204)
    )
    assert client.salesforce.delete_import_source(CONN, SOURCE).deleted is None
    assert _last(route).method == "DELETE"

    route = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 2})
    )
    assert client.salesforce.retry_activity(CONN, ids=["a", "b"]).requeued == 2
    assert _body(route) == {"ids": ["a", "b"]}

    route = respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert client.salesforce.sync_now(CONN).ok is True
    assert _last(route).method == "POST"


@respx.mock
@pytest.mark.anyio
async def test_salesforce_writes_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": SETTINGS})
    )
    _check_settings(
        (await aclient.salesforce.update_settings(CONN, settings=SETTINGS)).settings
    )
    assert _last(route).method == "PUT"
    assert _body(route) == SETTINGS

    route = respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 1,
                "sample": [{"record_id": "003xx", "already_linked": False}],
            },
        )
    )
    prev = await aclient.salesforce.preview_import(
        CONN, source_kind="campaign", object="Contact", source_id="701000000000001AAA"
    )
    assert prev.sample[0].record_id == "003xx"
    assert prev.sample[0].already_linked is False
    assert _body(route)["source_kind"] == "campaign"

    route = respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SOURCE_JSON)
    )
    _check_source(
        await aclient.salesforce.create_import_source(
            CONN, source_kind="campaign", source_id="701000000000001AAA"
        )
    )
    assert _body(route) == {
        "source_kind": "campaign",
        "source_id": "701000000000001AAA",
    }

    route = respx.patch(f"{SF}/import-sources/{SOURCE}").mock(
        return_value=httpx.Response(200, json=SOURCE_JSON)
    )
    _check_source(
        await aclient.salesforce.update_import_source(
            CONN, SOURCE, campaign_id=None, category_ids=["c"], source_label="L"
        )
    )
    assert _body(route) == {
        "campaign_id": None,
        "category_ids": ["c"],
        "source_label": "L",
    }

    route = respx.post(f"{SF}/import-sources/{SOURCE}/run").mock(
        return_value=httpx.Response(200, json=SOURCE_JSON)
    )
    _check_source(await aclient.salesforce.run_import_source(CONN, SOURCE))
    assert _last(route).method == "POST"

    route = respx.delete(f"{SF}/import-sources/{SOURCE}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.salesforce.delete_import_source(CONN, SOURCE)
    assert _last(route).method == "DELETE"

    route = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 1})
    )
    assert (await aclient.salesforce.retry_activity(CONN, ids=["a"])).requeued == 1
    assert _body(route) == {"ids": ["a"]}

    route = respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await aclient.salesforce.sync_now(CONN)).ok is True
    assert _last(route).url.path == f"/v1/integrations/salesforce/{CONN}/sync-now"


# -- contacts ---------------------------------------------------------------
@respx.mock
def test_contact_salesforce_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/contacts/{CONTACT}/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(client.contacts.salesforce(CONTACT))
    assert _last(route).method == "GET"

    route = respx.post(f"{BASE_URL}/contacts/{CONTACT}/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(client.contacts.sync_salesforce(CONTACT))
    assert _last(route).content == b""
    _check_panel(
        client.contacts.sync_salesforce(CONTACT, connection_id=CONN, create_as="Lead")
    )
    assert _body(route) == {"connection_id": CONN, "create_as": "Lead"}
    assert _last(route).headers.get("idempotency-key")

    route = respx.delete(f"{BASE_URL}/contacts/{CONTACT}/salesforce/links/{LINK}").mock(
        return_value=httpx.Response(204)
    )
    assert client.contacts.unlink_salesforce(CONTACT, LINK).deleted is None
    assert _last(route).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_contact_salesforce_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/{CONTACT}/salesforce").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(await aclient.contacts.salesforce(CONTACT))

    route = respx.post(f"{BASE_URL}/contacts/{CONTACT}/salesforce/sync").mock(
        return_value=httpx.Response(200, json=PANEL)
    )
    _check_panel(await aclient.contacts.sync_salesforce(CONTACT))
    assert _last(route).content == b""
    _check_panel(await aclient.contacts.sync_salesforce(CONTACT, create_as="Contact"))
    assert _body(route) == {"create_as": "Contact"}

    route = respx.delete(f"{BASE_URL}/contacts/{CONTACT}/salesforce/links/{LINK}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.contacts.unlink_salesforce(CONTACT, LINK)
    assert _last(route).method == "DELETE"


# -- community directory ----------------------------------------------------
@respx.mock
def test_community_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/integrations/community").mock(
        return_value=httpx.Response(
            200, json=_page([COMMUNITY_APP], next_cursor="o100")
        )
    )
    page = client.integrations.community(limit=100, cursor="o0")
    _check_app(page.data[0])
    assert page.has_more is True
    assert _last(route).url.params.get("limit") == "100"
    assert _last(route).url.params.get("cursor") == "o0"

    route = respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=COMMUNITY_APP)
    )
    _check_app(client.integrations.get_community_app("acme-sync"))
    assert _last(route).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_community_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/integrations/community").mock(
        return_value=httpx.Response(200, json=_page([COMMUNITY_APP]))
    )
    apps = [a async for a in aclient.integrations.community(limit=5)]
    _check_app(apps[0])
    assert _last(route).url.params.get("limit") == "5"

    route = respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=COMMUNITY_APP)
    )
    _check_app(await aclient.integrations.get_community_app("acme-sync"))
    assert _last(route).url.path == "/v1/integrations/community/acme-sync"
