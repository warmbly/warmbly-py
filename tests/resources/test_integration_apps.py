"""Tests for the provider sub-namespaces of ``client.integrations``.

Covers Apollo, Salesforce and Clay, the community directory, the inbound URL
and signing-key calls, and the selection form of ``push``. Payloads mirror the
server's Go structs and every test asserts decoded attributes are populated.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CONN = "5d1f0a1e-0000-4000-8000-000000000001"
SRC = "5d1f0a1e-0000-4000-8000-000000000002"
RUN = "5d1f0a1e-0000-4000-8000-000000000003"
CAMPAIGN = "5d1f0a1e-0000-4000-8000-000000000004"
CAT = "5d1f0a1e-0000-4000-8000-000000000005"
AP = f"{BASE_URL}/integrations/apollo/{CONN}"
SF = f"{BASE_URL}/integrations/salesforce/{CONN}"
CL = f"{BASE_URL}/integrations/clay/{CONN}"


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


def _data(items: list[dict]) -> dict:
    return {"data": items}


# ===========================================================================
# Apollo
# ===========================================================================
AP_OVERVIEW = {
    "connection_id": CONN,
    "label": "Apollo",
    "status": "connected",
    "health": "healthy",
    "health_detail": "ok",
    "account_name": "Rae Rep",
    "account_email": "rae@acme.com",
    "sources": 2,
    "total_imported": 310,
    "last_run_at": "2026-01-02T03:04:05Z",
}
AP_SOURCE = {
    "id": SRC,
    "organization_id": "org_1",
    "connection_id": CONN,
    "created_by_user_id": "usr_1",
    "name": "Webinar list",
    "list_id": "al_1",
    "list_name": "Webinar",
    "campaign_id": CAMPAIGN,
    "category_ids": [CAT],
    "verified_only": True,
    "recurring": False,
    "enabled": True,
    "status": "running",
    "last_run_at": "2026-01-02T03:04:05Z",
    "last_result": {
        "read": 100,
        "imported": 80,
        "updated": 2,
        "skipped": 3,
        "failed": 1,
        "no_email": 4,
        "unverified": 5,
        "suppressed": 6,
        "already_seen": 7,
        "next_page": 3,
        "truncated": True,
    },
    "last_error": "oops",
    "total_imported": 80,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}
AP_RUN = {
    "id": RUN,
    "organization_id": "org_1",
    "connection_id": CONN,
    "requested_by_user_id": "usr_1",
    "overwrite": False,
    "status": "running",
    "total": 50,
    "processed": 10,
    "enriched": 8,
    "not_found": 1,
    "failed": 1,
    "credits_consumed": 8,
    "last_error": "x",
    "started_at": "2026-01-02T03:04:05Z",
    "created_at": "2026-01-02T03:00:00Z",
    "updated_at": "2026-01-02T03:05:00Z",
}
AP_PREVIEW = {
    "total": 120,
    "sample": [
        {
            "apollo_id": "p1",
            "name": "Ann Lee",
            "email": "ann@globex.com",
            "email_status": "verified",
            "title": "CTO",
            "company": "Globex",
            "already_in_warmbly": True,
            "will_import": False,
        }
    ],
}


def _check_ap_overview(o) -> None:  # type: ignore[no-untyped-def]
    assert o.connection_id == CONN
    assert o.account_name == "Rae Rep"
    assert o.account_email == "rae@acme.com"
    assert (o.sources, o.total_imported) == (2, 310)
    assert o.last_run_at == "2026-01-02T03:04:05Z"
    assert o.health_detail == "ok"


def _check_ap_source(s) -> None:  # type: ignore[no-untyped-def]
    assert s.id == SRC
    assert s.list_id == "al_1"
    assert s.list_name == "Webinar"
    assert s.campaign_id == CAMPAIGN
    assert s.category_ids == [CAT]
    assert (s.verified_only, s.recurring, s.enabled) == (True, False, True)
    assert s.status == "running"
    assert s.last_result.imported == 80
    assert s.last_result.no_email == 4
    assert s.last_result.already_seen == 7
    assert s.last_result.next_page == 3
    assert s.last_result.truncated is True
    assert s.total_imported == 80


def _check_ap_run(r) -> None:  # type: ignore[no-untyped-def]
    assert r.id == RUN
    assert r.status == "running"
    assert (r.total, r.processed, r.enriched) == (50, 10, 8)
    assert (r.not_found, r.failed, r.credits_consumed) == (1, 1, 8)
    assert r.requested_by_user_id == "usr_1"
    assert r.started_at == "2026-01-02T03:04:05Z"


@respx.mock
def test_apollo_sync(client: Warmbly) -> None:
    ap = client.integrations.apollo
    respx.get(AP).mock(return_value=httpx.Response(200, json=AP_OVERVIEW))
    _check_ap_overview(ap.overview(CONN))

    key = respx.put(f"{AP}/key").mock(
        return_value=httpx.Response(200, json=AP_OVERVIEW)
    )
    _check_ap_overview(ap.replace_key(CONN, api_key="k"))
    assert _body(key) == {"api_key": "k"}

    respx.get(f"{AP}/lists").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "al_1", "name": "Webinar", "count": 120}])
        )
    )
    lists = list(ap.list_lists(CONN))
    assert (lists[0].id, lists[0].name, lists[0].count) == ("al_1", "Webinar", 120)

    prev = respx.post(f"{AP}/import/preview").mock(
        return_value=httpx.Response(200, json=AP_PREVIEW)
    )
    p = ap.preview_import(CONN, list_id="al_1", verified_only=False)
    assert p.total == 120
    row = p.sample[0]
    assert (row.apollo_id, row.email, row.email_status) == (
        "p1",
        "ann@globex.com",
        "verified",
    )
    assert (row.title, row.company) == ("CTO", "Globex")
    assert row.already_in_warmbly is True
    assert row.will_import is False
    assert _body(prev) == {"list_id": "al_1", "verified_only": False}

    respx.get(f"{AP}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([AP_SOURCE]))
    )
    _check_ap_source(next(iter(ap.list_import_sources(CONN))))

    create = respx.post(f"{AP}/import-sources").mock(
        return_value=httpx.Response(201, json=AP_SOURCE)
    )
    _check_ap_source(
        ap.create_import_source(
            CONN,
            list_id="al_1",
            list_name="Webinar",
            campaign_id=CAMPAIGN,
            category_ids=[CAT],
            recurring=True,
        )
    )
    assert _body(create) == {
        "list_id": "al_1",
        "list_name": "Webinar",
        "campaign_id": CAMPAIGN,
        "category_ids": [CAT],
        "recurring": True,
    }
    assert _last(create).headers["Idempotency-Key"]

    patch = respx.patch(f"{AP}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    _check_ap_source(
        ap.update_import_source(CONN, SRC, campaign_id=None, enabled=False)
    )
    assert _body(patch) == {"campaign_id": None, "enabled": False}
    ap.update_import_source(CONN, SRC, name="New")
    assert _body(patch) == {"name": "New"}

    run = respx.post(f"{AP}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    _check_ap_source(ap.run_import_source(CONN, SRC))
    assert _last(run).method == "POST"

    delete = respx.delete(f"{AP}/import-sources/{SRC}").mock(
        return_value=httpx.Response(204)
    )
    assert ap.delete_import_source(CONN, SRC) is None
    assert _last(delete).method == "DELETE"

    enrichments = respx.get(f"{AP}/enrichments").mock(
        return_value=httpx.Response(200, json=_data([AP_RUN]))
    )
    _check_ap_run(next(iter(ap.list_enrichments(CONN, limit=5))))
    assert dict(_last(enrichments).url.params) == {"limit": "5"}

    respx.get(f"{AP}/enrichments/{RUN}").mock(
        return_value=httpx.Response(200, json=AP_RUN)
    )
    _check_ap_run(ap.get_enrichment(CONN, RUN))

    start = respx.post(f"{AP}/enrichments").mock(
        return_value=httpx.Response(202, json=AP_RUN)
    )
    _check_ap_run(ap.start_enrichment(CONN, contacts=["c1", "c2"], overwrite=True))
    assert _body(start) == {"contacts": ["c1", "c2"], "overwrite": True}
    assert _last(start).headers["Idempotency-Key"]
    ap.start_enrichment(
        CONN, select_all=True, filters={"query": "acme"}, exclude=["c3"]
    )
    assert _body(start) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c3"],
    }
    ap.start_enrichment(CONN, contact_ids=["c9"])
    assert _body(start) == {"contact_ids": ["c9"]}


@respx.mock
@pytest.mark.anyio
async def test_apollo_async(aclient: AsyncWarmbly) -> None:
    ap = aclient.integrations.apollo
    respx.get(AP).mock(return_value=httpx.Response(200, json=AP_OVERVIEW))
    _check_ap_overview(await ap.overview(CONN))
    key = respx.put(f"{AP}/key").mock(
        return_value=httpx.Response(200, json=AP_OVERVIEW)
    )
    _check_ap_overview(await ap.replace_key(CONN, api_key="k"))
    assert _body(key) == {"api_key": "k"}
    respx.get(f"{AP}/lists").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "al_1", "name": "Webinar", "count": 120}])
        )
    )
    assert [x.count async for x in ap.list_lists(CONN)] == [120]
    prev = respx.post(f"{AP}/import/preview").mock(
        return_value=httpx.Response(200, json=AP_PREVIEW)
    )
    p = await ap.preview_import(CONN, list_id="al_1")
    assert p.sample[0].will_import is False
    assert _body(prev) == {"list_id": "al_1"}
    respx.get(f"{AP}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([AP_SOURCE]))
    )
    sources = [s async for s in ap.list_import_sources(CONN)]
    _check_ap_source(sources[0])
    create = respx.post(f"{AP}/import-sources").mock(
        return_value=httpx.Response(201, json=AP_SOURCE)
    )
    _check_ap_source(await ap.create_import_source(CONN, list_id="al_1"))
    assert _body(create) == {"list_id": "al_1"}
    patch = respx.patch(f"{AP}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    _check_ap_source(await ap.update_import_source(CONN, SRC, campaign_id=None))
    assert _body(patch) == {"campaign_id": None}
    respx.post(f"{AP}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    _check_ap_source(await ap.run_import_source(CONN, SRC))
    respx.delete(f"{AP}/import-sources/{SRC}").mock(return_value=httpx.Response(204))
    assert await ap.delete_import_source(CONN, SRC) is None
    respx.get(f"{AP}/enrichments").mock(
        return_value=httpx.Response(200, json=_data([AP_RUN]))
    )
    runs = [r async for r in ap.list_enrichments(CONN)]
    _check_ap_run(runs[0])
    respx.get(f"{AP}/enrichments/{RUN}").mock(
        return_value=httpx.Response(200, json=AP_RUN)
    )
    _check_ap_run(await ap.get_enrichment(CONN, RUN))
    start = respx.post(f"{AP}/enrichments").mock(
        return_value=httpx.Response(202, json=AP_RUN)
    )
    _check_ap_run(await ap.start_enrichment(CONN, contacts=["c1"]))
    assert _body(start) == {"contacts": ["c1"]}


# ===========================================================================
# Salesforce
# ===========================================================================
SF_SETTINGS = {
    "enabled": True,
    "matching": {
        "prefer": "contact",
        "create_when": "reply",
        "create_as": "lead",
        "lead_source": "Warmbly",
        "lead_status": "",
        "owner": "connected_user",
        "run_assignment_rules": False,
    },
    "activity": {"sent": True, "replied": True, "assign_to": "record_owner"},
    "writeback": {
        "lead_status_on_sent": "",
        "lead_status_on_reply": {"positive": "Working"},
        "lead_status_on_meeting": "",
        "never_move_backwards": True,
    },
    "inbound": {
        "opt_out": "both",
        "pause_on_converted": False,
        "pause_on_statuses": [],
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
    "daily_api_budget": 0,
}
SF_OVERVIEW = {
    "connection_id": CONN,
    "label": "Salesforce",
    "status": "connected",
    "health": "healthy",
    "org": {
        "id": "00D1",
        "instance_url": "https://acme.my.salesforce.com",
        "environment": "production",
        "login_host": "login.salesforce.com",
        "user_id": "005X",
        "account": "rae@acme.com",
    },
    "api": {"used": 10, "max": 15000, "calls_today": 4, "budget": 3000},
    "counts": {
        "pending": 2,
        "synced_24h": 30,
        "failed": 1,
        "skipped_24h": 4,
        "linked_records": 99,
    },
    "last_pull_at": "2026-01-02T03:04:05Z",
    "last_pull_error": "late",
    "settings_enabled": True,
    "checks": [{"key": "lead_read", "label": "Read Leads", "ok": True}],
}
SF_SOURCE = {
    "id": SRC,
    "organization_id": "org_1",
    "connection_id": CONN,
    "created_by_user_id": "usr_1",
    "name": "Hot leads",
    "source_kind": "list_view",
    "object": "Lead",
    "source_id": "00B000000000001AAA",
    "source_label": "Hot",
    "campaign_id": CAMPAIGN,
    "category_ids": [CAT],
    "recurring": True,
    "enabled": True,
    "status": "idle",
    "last_run_at": "2026-01-02T03:04:05Z",
    "last_result": {
        "read": 50,
        "imported": 40,
        "updated": 1,
        "linked": 30,
        "skipped": 2,
        "failed": 0,
        "no_email": 3,
        "opted_out": 4,
        "truncated": False,
    },
    "total_imported": 40,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}
SF_ACTIVITY = {
    "id": "act_1",
    "organization_id": "org_1",
    "connection_id": CONN,
    "contact_id": "ct_1",
    "contact_email": "ann@globex.com",
    "kind": "replied",
    "payload": {"subject": "Hi"},
    "status": "failed",
    "attempts": 3,
    "next_attempt_at": "2026-01-02T04:00:00Z",
    "record_id": "00Q1",
    "task_id": "00T1",
    "detail": "boom",
    "occurred_at": "2026-01-02T03:00:00Z",
    "created_at": "2026-01-02T03:00:01Z",
    "processed_at": "2026-01-02T03:00:05Z",
}


def _check_sf_source(s) -> None:  # type: ignore[no-untyped-def]
    assert s.id == SRC
    assert (s.source_kind, s.object) == ("list_view", "Lead")
    assert s.source_id == "00B000000000001AAA"
    assert s.source_label == "Hot"
    assert s.campaign_id == CAMPAIGN
    assert s.category_ids == [CAT]
    assert s.recurring is True
    assert s.last_result.linked == 30
    assert s.last_result.opted_out == 4
    assert s.total_imported == 40


def _check_sf_activity(a) -> None:  # type: ignore[no-untyped-def]
    assert a.id == "act_1"
    assert a.contact_email == "ann@globex.com"
    assert (a.kind, a.status, a.attempts) == ("replied", "failed", 3)
    assert a.payload == {"subject": "Hi"}
    assert (a.record_id, a.task_id, a.detail) == ("00Q1", "00T1", "boom")
    assert a.occurred_at == "2026-01-02T03:00:00Z"
    assert a.processed_at == "2026-01-02T03:00:05Z"


def _check_sf_overview(o) -> None:  # type: ignore[no-untyped-def]
    assert o.connection_id == CONN
    assert o.org["instance_url"] == "https://acme.my.salesforce.com"
    assert o.api["max"] == 15000
    assert o.counts.pending == 2
    assert o.counts.synced_24h == 30
    assert o.counts.linked_records == 99
    assert o.last_pull_error == "late"
    assert o.settings_enabled is True
    assert o.checks[0].key == "lead_read"
    assert o.checks[0].ok is True


@respx.mock
def test_salesforce_sync(client: Warmbly) -> None:
    sf = client.integrations.salesforce
    ov = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(200, json=SF_OVERVIEW)
    )
    _check_sf_overview(sf.overview(CONN, checks=True))
    assert dict(_last(ov).url.params) == {"checks": "1"}
    sf.overview(CONN)
    assert dict(_last(ov).url.params) == {}

    respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(
            200,
            json={
                "settings": SF_SETTINGS,
                "warmbly_fields": [{"key": "first_name", "label": "First name"}],
                "defaults": SF_SETTINGS,
            },
        )
    )
    got = sf.get_settings(CONN)
    assert got.settings.enabled is True
    assert got.settings.matching["create_as"] == "lead"
    assert got.settings.writeback["lead_status_on_reply"] == {"positive": "Working"}
    assert got.settings.field_map[0]["salesforce"] == "FirstName"
    assert got.warmbly_fields[0]["key"] == "first_name"
    assert got.defaults.daily_api_budget == 0

    put = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": SF_SETTINGS})
    )
    saved = sf.update_settings(CONN, settings=SF_SETTINGS)
    assert saved.settings.inbound["opt_out"] == "both"
    assert _body(put) == SF_SETTINGS

    respx.get(f"{SF}/metadata").mock(
        return_value=httpx.Response(
            200,
            json={
                "lead_fields": [
                    {
                        "name": "Status",
                        "label": "Lead Status",
                        "type": "picklist",
                        "createable": True,
                        "updateable": True,
                        "calculated": False,
                        "custom": False,
                        "picklist": [{"value": "Open", "label": "Open"}],
                    }
                ],
                "contact_fields": [],
                "lead_statuses": [{"value": "Open", "label": "Open"}],
                "lead_sources": [{"value": "Web", "label": "Web"}],
            },
        )
    )
    meta = sf.get_metadata(CONN)
    assert meta.lead_fields[0].name == "Status"
    assert meta.lead_fields[0].createable is True
    assert meta.lead_fields[0].picklist[0].value == "Open"
    assert meta.lead_statuses[0].label == "Open"
    assert meta.lead_sources[0].value == "Web"

    users = respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "005X", "name": "Rae", "email": "r@acme.com"}])
        )
    )
    u = next(iter(sf.list_users(CONN, q="ra")))
    assert (u.id, u.name, u.email) == ("005X", "Rae", "r@acme.com")
    assert dict(_last(users).url.params) == {"q": "ra"}

    views = respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "00B1", "label": "Hot", "object": "Lead"}])
        )
    )
    v = next(iter(sf.list_list_views(CONN, object="Lead")))
    assert (v.id, v.label, v.object) == ("00B1", "Hot", "Lead")
    assert dict(_last(views).url.params) == {"object": "Lead"}

    camps = respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json=_data(
                [
                    {
                        "id": "701X",
                        "name": "Spring",
                        "status": "Planned",
                        "type": "Email",
                        "member_count": 12,
                    }
                ]
            ),
        )
    )
    c = next(iter(sf.list_campaigns(CONN, q="sp")))
    assert (c.name, c.status, c.type, c.member_count) == (
        "Spring",
        "Planned",
        "Email",
        12,
    )
    assert dict(_last(camps).url.params) == {"q": "sp"}

    prev = respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 9,
                "sample": [
                    {
                        "record_id": "00Q1",
                        "object": "Lead",
                        "name": "Ann Lee",
                        "email": "ann@globex.com",
                        "company": "Globex",
                        "title": "CTO",
                        "owner_name": "Rae",
                        "status": "Open",
                        "already_linked": True,
                    }
                ],
            },
        )
    )
    p = sf.preview_import(
        CONN, source_kind="list_view", object="Lead", source_id="00B000000000001AAA"
    )
    assert p.total == 9
    row = p.sample[0]
    assert (row.record_id, row.owner_name, row.status) == ("00Q1", "Rae", "Open")
    assert row.already_linked is True
    assert _body(prev) == {
        "source_kind": "list_view",
        "source_id": "00B000000000001AAA",
        "object": "Lead",
    }

    respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([SF_SOURCE]))
    )
    _check_sf_source(next(iter(sf.list_import_sources(CONN))))

    create = respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SF_SOURCE)
    )
    _check_sf_source(
        sf.create_import_source(
            CONN,
            source_kind="campaign",
            source_id="701000000000001AAA",
            source_label="Spring",
            recurring=True,
        )
    )
    assert _body(create) == {
        "source_kind": "campaign",
        "source_id": "701000000000001AAA",
        "source_label": "Spring",
        "recurring": True,
    }

    patch = respx.patch(f"{SF}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(sf.update_import_source(CONN, SRC, campaign_id=None, enabled=True))
    assert _body(patch) == {"campaign_id": None, "enabled": True}

    respx.post(f"{SF}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(sf.run_import_source(CONN, SRC))
    respx.delete(f"{SF}/import-sources/{SRC}").mock(return_value=httpx.Response(204))
    assert sf.delete_import_source(CONN, SRC) is None

    act = respx.get(f"{SF}/activity").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [SF_ACTIVITY],
                    "pagination": {"next_cursor": "cur2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**SF_ACTIVITY, "id": "act_2"}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    rows = list(sf.list_activity(CONN, status="failed", contact_id="ct_1", limit=1))
    assert [r.id for r in rows] == ["act_1", "act_2"]
    _check_sf_activity(rows[0])
    first, second = (c.request for c in act.calls)
    assert dict(first.url.params) == {
        "status": "failed",
        "contact_id": "ct_1",
        "limit": "1",
    }
    assert second.url.params["cursor"] == "cur2"

    retry = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 3})
    )
    assert sf.retry_activity(CONN, ids=["act_1"]).requeued == 3
    assert _body(retry) == {"ids": ["act_1"]}
    sf.retry_activity(CONN)
    assert _body(retry) == {}

    now = respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert sf.sync_now(CONN).ok is True
    assert _last(now).headers["Idempotency-Key"]


@respx.mock
@pytest.mark.anyio
async def test_salesforce_async(aclient: AsyncWarmbly) -> None:
    sf = aclient.integrations.salesforce
    ov = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(200, json=SF_OVERVIEW)
    )
    _check_sf_overview(await sf.overview(CONN, checks=True))
    assert dict(_last(ov).url.params) == {"checks": "1"}
    respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(
            200,
            json={
                "settings": SF_SETTINGS,
                "warmbly_fields": [],
                "defaults": SF_SETTINGS,
            },
        )
    )
    assert (await sf.get_settings(CONN)).settings.matching["owner"] == "connected_user"
    put = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": SF_SETTINGS})
    )
    saved = await sf.update_settings(CONN, settings=SF_SETTINGS)
    assert saved.settings.enabled is True
    assert _body(put) == SF_SETTINGS
    respx.get(f"{SF}/metadata").mock(
        return_value=httpx.Response(
            200,
            json={
                "lead_fields": [],
                "contact_fields": [
                    {"name": "Email", "label": "Email", "type": "email"}
                ],
                "lead_statuses": [],
                "lead_sources": [],
            },
        )
    )
    assert (await sf.get_metadata(CONN)).contact_fields[0].name == "Email"
    respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(200, json=_data([{"id": "005X", "name": "Rae"}]))
    )
    assert [u.name async for u in sf.list_users(CONN)] == ["Rae"]
    views = respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "00B1", "label": "Hot", "object": "Contact"}])
        )
    )
    assert [v.object async for v in sf.list_list_views(CONN, object="Contact")] == [
        "Contact"
    ]
    assert dict(_last(views).url.params) == {"object": "Contact"}
    respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "701X", "name": "Spring", "member_count": 2}])
        )
    )
    assert [c.member_count async for c in sf.list_campaigns(CONN)] == [2]
    respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(200, json={"total": 1, "sample": []})
    )
    assert (
        await sf.preview_import(
            CONN, source_kind="campaign", source_id="701000000000001AAA"
        )
    ).total == 1
    respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([SF_SOURCE]))
    )
    listed = [s async for s in sf.list_import_sources(CONN)]
    _check_sf_source(listed[0])
    respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SF_SOURCE)
    )
    _check_sf_source(
        await sf.create_import_source(
            CONN, source_kind="list_view", object="Lead", source_id="00B000000000001AAA"
        )
    )
    patch = respx.patch(f"{SF}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(await sf.update_import_source(CONN, SRC, recurring=False))
    assert _body(patch) == {"recurring": False}
    respx.post(f"{SF}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(await sf.run_import_source(CONN, SRC))
    respx.delete(f"{SF}/import-sources/{SRC}").mock(return_value=httpx.Response(204))
    assert await sf.delete_import_source(CONN, SRC) is None
    respx.get(f"{SF}/activity").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [SF_ACTIVITY],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    acts = [a async for a in sf.list_activity(CONN)]
    _check_sf_activity(acts[0])
    retry = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 1})
    )
    assert (await sf.retry_activity(CONN, ids=["act_1"])).requeued == 1
    assert _body(retry) == {"ids": ["act_1"]}
    respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await sf.sync_now(CONN)).ok is True


# ===========================================================================
# Clay
# ===========================================================================
CLAY = {
    "connection_id": CONN,
    "label": "Clay",
    "status": "connected",
    "health": "healthy",
    "inbound_url_minted": True,
    "defaults": {
        "campaign_id": CAMPAIGN,
        "category_ids": [CAT],
        "segment_ids": [],
        "dedup": "update",
        "subscribed": True,
    },
    "outbound": {
        "webhook_url_set": True,
        "webhook_host": "app.clay.com",
        "auth_token_set": False,
        "events": ["reply.positive"],
    },
    "stats": {
        "received": 10,
        "created": 6,
        "updated": 2,
        "skipped": 1,
        "failed": 1,
        "last_received_at": "2026-01-02T03:04:05Z",
        "last_error": "bad row",
    },
    "available_events": ["reply.positive", "email.bounced"],
}


def _check_clay(c) -> None:  # type: ignore[no-untyped-def]
    assert c.connection_id == CONN
    assert c.inbound_url_minted is True
    assert c.defaults.campaign_id == CAMPAIGN
    assert c.defaults.category_ids == [CAT]
    assert c.defaults.dedup == "update"
    assert c.defaults.subscribed is True
    assert c.outbound.webhook_host == "app.clay.com"
    assert c.outbound.webhook_url_set is True
    assert c.outbound.events == ["reply.positive"]
    assert (c.stats.received, c.stats.created, c.stats.failed) == (10, 6, 1)
    assert c.stats.last_error == "bad row"
    assert c.available_events == ["reply.positive", "email.bounced"]


@respx.mock
def test_clay_sync(client: Warmbly) -> None:
    respx.get(CL).mock(return_value=httpx.Response(200, json=CLAY))
    _check_clay(client.integrations.clay.get_settings(CONN))
    patch = respx.patch(CL).mock(return_value=httpx.Response(200, json=CLAY))
    _check_clay(
        client.integrations.clay.update_settings(
            CONN,
            defaults={"dedup": "update", "subscribed": True},
            webhook_url="",
            events=["reply.positive"],
        )
    )
    assert _body(patch) == {
        "defaults": {"dedup": "update", "subscribed": True},
        "webhook_url": "",
        "events": ["reply.positive"],
    }


@respx.mock
@pytest.mark.anyio
async def test_clay_async(aclient: AsyncWarmbly) -> None:
    respx.get(CL).mock(return_value=httpx.Response(200, json=CLAY))
    _check_clay(await aclient.integrations.clay.get_settings(CONN))
    patch = respx.patch(CL).mock(return_value=httpx.Response(200, json=CLAY))
    _check_clay(await aclient.integrations.clay.update_settings(CONN, auth_token="t"))
    assert _body(patch) == {"auth_token": "t"}


# ===========================================================================
# community directory, inbound URL, signing key, push, catalog
# ===========================================================================
APP = {
    "application_id": "app_1",
    "slug": "acme-sync",
    "name": "Acme Sync",
    "tagline": "Sync things",
    "description": "Longer text",
    "category": "crm",
    "logo_url": "https://cdn.example.com/l.png",
    "website_url": "https://acme.example.com",
    "install_url": "https://acme.example.com/install",
    "support_url": "https://acme.example.com/help",
    "privacy_url": "https://acme.example.com/privacy",
    "developer": "Acme Inc",
    "scopes": 5,
    "permissions": [
        {
            "name": "READ_CONTACTS",
            "value": 1,
            "description": "View contacts",
            "category": "read",
        },
        {
            "name": "WRITE_CONTACTS",
            "value": 4,
            "description": "Edit contacts",
            "category": "write",
        },
    ],
    "status": "featured",
    "listed": True,
    "installs": 42,
    "installed": False,
    "published_at": "2026-01-02T03:04:05Z",
}


def _check_app(a) -> None:  # type: ignore[no-untyped-def]
    assert a.application_id == "app_1"
    assert (a.slug, a.name, a.tagline) == ("acme-sync", "Acme Sync", "Sync things")
    assert a.category == "crm"
    assert a.install_url.endswith("/install")
    assert a.developer == "Acme Inc"
    assert a.scopes == 5
    assert [p.name for p in a.permissions] == ["READ_CONTACTS", "WRITE_CONTACTS"]
    assert a.permissions[1].value == 4
    assert a.permissions[1].category == "write"
    assert (a.status, a.listed, a.installs, a.installed) == (
        "featured",
        True,
        42,
        False,
    )
    assert a.published_at == "2026-01-02T03:04:05Z"


CONNECTION = {
    "id": CONN,
    "provider": "calendly",
    "label": "Calendly",
    "status": "connected",
    "sync_direction": "pull",
}


@respx.mock
def test_community_and_inbound_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/integrations/community").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [APP],
                    "pagination": {"total": 2, "next_cursor": "o1", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**APP, "slug": "other", "status": "newstatus"}],
                    "pagination": {"total": 2, "next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    apps = list(client.integrations.list_community_apps(limit=1))
    assert [a.slug for a in apps] == ["acme-sync", "other"]
    _check_app(apps[0])
    assert apps[1].status == "newstatus"
    first, second = (c.request for c in route.calls)
    assert dict(first.url.params) == {"limit": "1"}
    assert second.url.params["cursor"] == "o1"

    respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=APP)
    )
    _check_app(client.integrations.get_community_app("acme-sync"))

    rotate = respx.post(
        f"{BASE_URL}/integrations/connections/{CONN}/rotate-inbound-url"
    ).mock(
        return_value=httpx.Response(
            200, json={"inbound_webhook_url": "https://api/x/inbound/calendly/s3cret"}
        )
    )
    out = client.integrations.rotate_inbound_url(CONN)
    assert out.inbound_webhook_url == "https://api/x/inbound/calendly/s3cret"
    assert _last(rotate).headers["Idempotency-Key"]

    key = respx.put(f"{BASE_URL}/integrations/connections/{CONN}/signing-key").mock(
        return_value=httpx.Response(200, json={"connection": CONNECTION})
    )
    detail = client.integrations.set_signing_key(CONN, signing_key="k" * 16)
    assert detail.connection.id == CONN
    assert detail.connection.provider == "calendly"
    assert _body(key) == {"signing_key": "k" * 16}
    client.integrations.set_signing_key(CONN, signing_key="")
    assert _body(key) == {"signing_key": ""}


@respx.mock
@pytest.mark.anyio
async def test_community_and_inbound_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/integrations/community").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [APP],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    apps = [a async for a in aclient.integrations.list_community_apps()]
    _check_app(apps[0])
    respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=APP)
    )
    _check_app(await aclient.integrations.get_community_app("acme-sync"))
    respx.post(f"{BASE_URL}/integrations/connections/{CONN}/rotate-inbound-url").mock(
        return_value=httpx.Response(200, json={"inbound_webhook_url": "https://u"})
    )
    assert (
        await aclient.integrations.rotate_inbound_url(CONN)
    ).inbound_webhook_url == ("https://u")
    key = respx.put(f"{BASE_URL}/integrations/connections/{CONN}/signing-key").mock(
        return_value=httpx.Response(200, json={"connection": CONNECTION})
    )
    detail = await aclient.integrations.set_signing_key(CONN, signing_key="k" * 16)
    assert detail.connection.label == "Calendly"
    assert _body(key) == {"signing_key": "k" * 16}


@respx.mock
def test_push_selection_and_catalog_rank(client: Warmbly) -> None:
    push = respx.post(f"{BASE_URL}/integrations/connections/{CONN}/push").mock(
        return_value=httpx.Response(
            200, json={"provider": "hubspot", "pushed": 2, "failed": 0, "results": []}
        )
    )
    res = client.integrations.push(CONN, contact_ids=["c1", "c2"])
    assert (res.provider, res.pushed) == ("hubspot", 2)
    assert _body(push) == {"contact_ids": ["c1", "c2"]}
    client.integrations.push(
        CONN, select_all=True, filters={"query": "acme"}, exclude=["c3"]
    )
    assert _body(push) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c3"],
    }
    client.integrations.push(CONN, contacts=["c1"])
    assert _body(push) == {"contacts": ["c1"]}

    respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(
            200,
            json={
                "catalog": [
                    {"provider": "apollo", "name": "Apollo", "rank": 3},
                    {"provider": "clay", "name": "Clay", "rank": 4},
                ]
            },
        )
    )
    entries = list(client.integrations.catalog())
    assert [(e.provider, e.rank) for e in entries] == [("apollo", 3), ("clay", 4)]


@respx.mock
@pytest.mark.anyio
async def test_push_selection_async(aclient: AsyncWarmbly) -> None:
    push = respx.post(f"{BASE_URL}/integrations/connections/{CONN}/push").mock(
        return_value=httpx.Response(200, json={"provider": "hubspot", "pushed": 1})
    )
    res = await aclient.integrations.push(CONN, select_all=True, filters={"query": "a"})
    assert res.pushed == 1
    assert _body(push) == {"all": True, "filters": {"query": "a"}}
    await aclient.integrations.push(CONN, contact_ids=["c1"])
    assert _body(push) == {"contact_ids": ["c1"]}


@respx.mock
def test_null_collections_and_unknown_fields(client: Warmbly) -> None:
    """Go marshals nil slices as null, and the server adds fields over time."""
    respx.get(f"{BASE_URL}/crm/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "pending": 0,
                "failed": 0,
                "done_24h": 0,
                "cursors": None,
                "failures": None,
                "counts": {
                    "contacts": 1,
                    "deals": 0,
                    "tasks": 0,
                    "pipelines": 0,
                    "owners": 0,
                },
                "new_field": "x",
            },
        )
    )
    health = client.crm.get_sync_health()
    assert health.cursors == []
    assert health.failures == []
    assert health.counts.contacts == 1
    assert health.new_field == "x"

    respx.get(f"{AP}/import-sources").mock(
        return_value=httpx.Response(
            200,
            json=_data(
                [{**AP_SOURCE, "category_ids": None, "status": "brand-new", "extra": 1}]
            ),
        )
    )
    src = next(iter(client.integrations.apollo.list_import_sources(CONN)))
    assert src.category_ids == []
    assert src.status == "brand-new"
    assert src.last_result.imported == 80
    assert src.extra == 1
