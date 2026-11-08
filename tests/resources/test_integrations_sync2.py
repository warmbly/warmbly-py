"""Tests for the ``salesforce`` and ``apollo`` resources and the Clay,
community and inbound-secret methods on ``integrations``, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CONN = "c1c1c1c1-0000-4000-8000-000000000001"
SF = f"{BASE_URL}/integrations/salesforce/{CONN}"
AP = f"{BASE_URL}/integrations/apollo/{CONN}"
SRC = "a2a2a2a2-0000-4000-8000-000000000002"


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


def _data(rows: list[dict]) -> dict:
    return {"data": rows}


# -- Salesforce ---------------------------------------------------------------

SF_OVERVIEW = {
    "connection_id": CONN,
    "label": "Prod org",
    "status": "connected",
    "health": "ok",
    "health_detail": "",
    "org": {
        "id": "00D5e0000012345",
        "instance_url": "https://acme.my.salesforce.com",
        "environment": "production",
        "login_host": "login.salesforce.com",
    },
    "api": {"used": 1200, "max": 100000, "calls_today": 310, "budget": 20000},
    "counts": {
        "pending": 2,
        "synced_24h": 40,
        "failed": 1,
        "skipped_24h": 3,
        "linked_records": 90,
    },
    "last_pull_at": "2026-11-08T08:00:00Z",
    "settings_enabled": True,
    "checks": [
        {"key": "task_create", "label": "Create Tasks", "ok": False, "detail": "no"}
    ],
}

SF_SETTINGS = {
    "enabled": True,
    "matching": {"prefer": "lead", "create_when": "reply", "create_as": "lead"},
    "activity": {"sent": True, "replied": True},
    "writeback": {"lead_status_on_sent": "Working", "never_move_backwards": True},
    "inbound": {"opt_out": "sync", "pause_on_converted": True},
    "field_map": [
        {
            "object": "Lead",
            "warmbly": "company",
            "salesforce": "Company",
            "direction": "both",
            "policy": "if_empty",
        }
    ],
    "daily_api_budget": 0,
}

SF_SETTINGS_DOC = {
    "settings": SF_SETTINGS,
    "warmbly_fields": [{"key": "first_name", "label": "First name"}],
    "defaults": {"enabled": True, "daily_api_budget": 0},
}

SF_METADATA = {
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
    "contact_fields": [{"name": "Title", "label": "Title", "type": "string"}],
    "lead_statuses": [{"value": "Open", "label": "Open"}],
    "lead_sources": [{"value": "Web", "label": "Web"}],
}

SF_SOURCE = {
    "id": SRC,
    "organization_id": "0f0f0f0f-0000-4000-8000-000000000009",
    "connection_id": CONN,
    "created_by_user_id": "7d7d7d7d-0000-4000-8000-000000000003",
    "name": "Open leads",
    "source_kind": "list_view",
    "object": "Lead",
    "source_id": "00B5e00000AbCdE",
    "source_label": "All Open Leads",
    "campaign_id": "camp1",
    "category_ids": ["cat1"],
    "recurring": True,
    "enabled": True,
    "status": "idle",
    "last_run_at": "2026-11-08T07:00:00Z",
    "last_result": {
        "read": 100,
        "imported": 60,
        "updated": 10,
        "linked": 30,
        "skipped": 5,
        "failed": 1,
        "no_email": 4,
        "opted_out": 2,
        "truncated": True,
    },
    "last_error": "",
    "total_imported": 60,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-11-08T07:00:00Z",
}

SF_ACTIVITY = {
    "id": "act1",
    "organization_id": "0f0f0f0f-0000-4000-8000-000000000009",
    "connection_id": CONN,
    "contact_id": "5d1c7e0a-35f5-4e7e-8a1b-2f43c0a3d001",
    "contact_email": "ada@example.com",
    "kind": "replied",
    "payload": {"subject": "Re: Hello"},
    "status": "failed",
    "attempts": 3,
    "next_attempt_at": "2026-11-08T09:00:00Z",
    "record_id": "00Q5e00000AbCdE",
    "task_id": "",
    "detail": "FIELD_CUSTOM_VALIDATION_EXCEPTION",
    "occurred_at": "2026-11-08T06:00:00Z",
    "created_at": "2026-11-08T06:00:01Z",
    "processed_at": "2026-11-08T06:05:00Z",
}


def _check_sf_overview(o: Any) -> None:
    assert o.connection_id == CONN
    assert o.org["login_host"] == "login.salesforce.com"
    assert o.api["budget"] == 20000
    assert o.counts["linked_records"] == 90
    assert o.settings_enabled is True
    assert o.checks[0].key == "task_create"
    assert o.checks[0].ok is False


def _check_sf_settings(s: Any) -> None:
    assert s.enabled is True
    assert s.matching["create_as"] == "lead"
    assert s.writeback["never_move_backwards"] is True
    assert s.field_map[0]["policy"] == "if_empty"
    assert s.daily_api_budget == 0


def _check_sf_source(src: Any) -> None:
    assert src.id == SRC
    assert src.source_kind == "list_view"
    assert src.object == "Lead"
    assert src.category_ids == ["cat1"]
    assert src.last_result.opted_out == 2
    assert src.last_result.truncated is True
    assert src.total_imported == 60


def _check_sf_activity(a: Any) -> None:
    assert a.kind == "replied"
    assert a.status == "failed"
    assert a.payload == {"subject": "Re: Hello"}
    assert a.detail == "FIELD_CUSTOM_VALIDATION_EXCEPTION"


@respx.mock
def test_salesforce_sync(client: Warmbly) -> None:
    ov = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(200, json=SF_OVERVIEW)
    )
    _check_sf_overview(client.salesforce.overview(CONN, checks=True))
    assert _last(ov).url.params["checks"] == "1"
    client.salesforce.overview(CONN)
    assert "checks" not in _last(ov).url.params

    respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json=SF_SETTINGS_DOC)
    )
    doc = client.salesforce.settings(CONN)
    _check_sf_settings(doc.settings)
    assert doc.warmbly_fields[0]["key"] == "first_name"
    assert doc.defaults.enabled is True

    put = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": SF_SETTINGS})
    )
    _check_sf_settings(
        client.salesforce.update_settings(CONN, settings=SF_SETTINGS).settings
    )
    assert _body(put) == SF_SETTINGS

    respx.get(f"{SF}/metadata").mock(return_value=httpx.Response(200, json=SF_METADATA))
    meta = client.salesforce.metadata(CONN)
    assert meta.lead_fields[0].picklist[0].value == "Open"
    assert meta.lead_fields[0].createable is True
    assert meta.contact_fields[0].name == "Title"
    assert meta.lead_statuses[0].label == "Open"
    assert meta.lead_sources[0].value == "Web"

    users = respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "005", "name": "Sam", "email": "sam@acme.test"}])
        )
    )
    found = list(client.salesforce.users(CONN, q="sam"))
    assert found[0].email == "sam@acme.test"
    assert _last(users).url.params["q"] == "sam"

    views = respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "00B", "label": "Open", "object": "Lead"}])
        )
    )
    assert next(iter(client.salesforce.list_views(CONN, object="Lead"))).label == "Open"
    assert _last(views).url.params["object"] == "Lead"

    camps = respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json=_data(
                [
                    {
                        "id": "701",
                        "name": "Webinar",
                        "status": "Planned",
                        "type": "Webinar",
                        "member_count": 55,
                    }
                ]
            ),
        )
    )
    camp = next(iter(client.salesforce.campaigns(CONN, q="web")))
    assert (camp.name, camp.member_count) == ("Webinar", 55)
    assert _last(camps).url.params["q"] == "web"

    prev = respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 40,
                "sample": [
                    {
                        "record_id": "00Q",
                        "object": "Lead",
                        "name": "Ada Lovelace",
                        "email": "ada@example.com",
                        "already_linked": True,
                    }
                ],
            },
        )
    )
    preview = client.salesforce.preview_import(
        CONN, source_kind="list_view", source_id="00B", object="Lead"
    )
    assert preview.total == 40
    assert preview.sample[0]["already_linked"] is True
    assert _body(prev) == {
        "source_kind": "list_view",
        "source_id": "00B",
        "object": "Lead",
    }

    respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([SF_SOURCE]))
    )
    _check_sf_source(next(iter(client.salesforce.list_import_sources(CONN))))

    create = respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SF_SOURCE)
    )
    _check_sf_source(
        client.salesforce.create_import_source(
            CONN,
            source_kind="list_view",
            source_id="00B",
            object="Lead",
            name="Open leads",
            source_label="All Open Leads",
            campaign_id="camp1",
            category_ids=("cat1",),
            recurring=True,
            enabled=True,
        )
    )
    assert _body(create) == {
        "name": "Open leads",
        "source_kind": "list_view",
        "object": "Lead",
        "source_id": "00B",
        "source_label": "All Open Leads",
        "campaign_id": "camp1",
        "category_ids": ["cat1"],
        "recurring": True,
        "enabled": True,
    }
    assert "idempotency-key" in _last(create).headers

    patch = respx.patch(f"{SF}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(
        client.salesforce.update_import_source(
            CONN,
            SRC,
            name="Renamed",
            source_label="x",
            campaign_id=None,
            category_ids=["cat2"],
            recurring=False,
            enabled=False,
        )
    )
    assert _body(patch) == {
        "name": "Renamed",
        "source_label": "x",
        "campaign_id": None,
        "category_ids": ["cat2"],
        "recurring": False,
        "enabled": False,
    }
    client.salesforce.update_import_source(CONN, SRC, enabled=True)
    assert _body(patch) == {"enabled": True}

    run = respx.post(f"{SF}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(client.salesforce.run_import_source(CONN, SRC))
    assert _last(run).method == "POST"

    delete = respx.delete(f"{SF}/import-sources/{SRC}").mock(
        return_value=httpx.Response(204)
    )
    assert client.salesforce.delete_import_source(CONN, SRC).deleted is None
    assert _last(delete).method == "DELETE"

    activity = respx.get(f"{SF}/activity").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [SF_ACTIVITY],
                    "pagination": {"next_cursor": "n2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"id": "act2"}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    rows = list(
        client.salesforce.list_activity(CONN, status="failed", contact_id="c1", limit=1)
    )
    assert [r.id for r in rows] == ["act1", "act2"]
    _check_sf_activity(rows[0])
    first = activity.calls[0].request.url.params
    assert (first["status"], first["contact_id"], first["limit"]) == (
        "failed",
        "c1",
        "1",
    )
    assert activity.calls[1].request.url.params["cursor"] == "n2"

    retry = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 2})
    )
    assert client.salesforce.retry_activity(CONN, ids=["act1", "act2"]).requeued == 2
    assert _body(retry) == {"ids": ["act1", "act2"]}

    now = respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert client.salesforce.sync_now(CONN).ok is True
    assert _last(now).method == "POST"


@respx.mock
@pytest.mark.anyio
async def test_salesforce_async(aclient: AsyncWarmbly) -> None:
    sf = aclient.salesforce
    ov = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(200, json=SF_OVERVIEW)
    )
    _check_sf_overview(await sf.overview(CONN, checks=True))
    assert _last(ov).url.params["checks"] == "1"

    respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json=SF_SETTINGS_DOC)
    )
    _check_sf_settings((await sf.settings(CONN)).settings)

    put = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": SF_SETTINGS})
    )
    _check_sf_settings((await sf.update_settings(CONN, settings=SF_SETTINGS)).settings)
    assert _body(put) == SF_SETTINGS

    respx.get(f"{SF}/metadata").mock(return_value=httpx.Response(200, json=SF_METADATA))
    assert (await sf.metadata(CONN)).lead_sources[0].label == "Web"

    respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(200, json=_data([{"id": "005", "name": "Sam"}]))
    )
    assert [u.name async for u in sf.users(CONN, q="sam")] == ["Sam"]

    respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(200, json=_data([{"id": "00B", "label": "Open"}]))
    )
    assert [v.id async for v in sf.list_views(CONN, object="Contact")] == ["00B"]

    respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(200, json=_data([{"id": "701", "name": "W"}]))
    )
    assert [c.name async for c in sf.campaigns(CONN)] == ["W"]

    prev = respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(200, json={"total": 1, "sample": []})
    )
    assert (
        await sf.preview_import(CONN, source_kind="campaign", source_id="701")
    ).total == 1
    assert _body(prev) == {"source_kind": "campaign", "source_id": "701"}

    respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([SF_SOURCE]))
    )
    _check_sf_source(await anext(aiter(sf.list_import_sources(CONN))))

    create = respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SF_SOURCE)
    )
    _check_sf_source(
        await sf.create_import_source(CONN, source_kind="campaign", source_id="701")
    )
    assert _body(create) == {"source_kind": "campaign", "source_id": "701"}

    patch = respx.patch(f"{SF}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(
        await sf.update_import_source(CONN, SRC, campaign_id=None, category_ids=["c"])
    )
    assert _body(patch) == {"campaign_id": None, "category_ids": ["c"]}

    respx.post(f"{SF}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    _check_sf_source(await sf.run_import_source(CONN, SRC))

    respx.delete(f"{SF}/import-sources/{SRC}").mock(return_value=httpx.Response(204))
    assert (await sf.delete_import_source(CONN, SRC)).deleted is None

    activity = respx.get(f"{SF}/activity").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [SF_ACTIVITY],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    rows = [a async for a in sf.list_activity(CONN, status="failed")]
    _check_sf_activity(rows[0])
    assert _last(activity).url.params["status"] == "failed"

    retry = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 1})
    )
    assert (await sf.retry_activity(CONN, ids=["act1"])).requeued == 1
    assert _body(retry) == {"ids": ["act1"]}

    respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await sf.sync_now(CONN)).ok is True


# -- Apollo -------------------------------------------------------------------

AP_OVERVIEW = {
    "connection_id": CONN,
    "label": "Apollo",
    "status": "connected",
    "health": "ok",
    "account_name": "Acme",
    "account_email": "ops@acme.test",
    "sources": 2,
    "total_imported": 540,
    "last_run_at": "2026-11-08T07:00:00Z",
}

AP_SOURCE = {
    "id": SRC,
    "organization_id": "0f0f0f0f-0000-4000-8000-000000000009",
    "connection_id": CONN,
    "name": "VPs",
    "list_id": "list1",
    "list_name": "VP Sales",
    "campaign_id": "camp1",
    "category_ids": ["cat1"],
    "verified_only": True,
    "recurring": True,
    "enabled": True,
    "status": "idle",
    "last_result": {
        "read": 200,
        "imported": 150,
        "updated": 5,
        "skipped": 20,
        "failed": 0,
        "no_email": 10,
        "unverified": 12,
        "suppressed": 3,
        "truncated": True,
        "already_seen": 40,
        "next_page": 3,
    },
    "total_imported": 150,
}

AP_RUN = {
    "id": "run1",
    "organization_id": "0f0f0f0f-0000-4000-8000-000000000009",
    "connection_id": CONN,
    "requested_by_user_id": "7d7d7d7d-0000-4000-8000-000000000003",
    "overwrite": False,
    "status": "running",
    "total": 100,
    "processed": 40,
    "enriched": 30,
    "not_found": 8,
    "failed": 2,
    "credits_consumed": 30,
    "started_at": "2026-11-08T08:00:00Z",
}


def _check_ap_source(s: Any) -> None:
    assert s.list_name == "VP Sales"
    assert s.verified_only is True
    assert s.last_result.unverified == 12
    assert s.last_result.next_page == 3
    assert s.last_result.already_seen == 40


def _check_ap_run(r: Any) -> None:
    assert r.id == "run1"
    assert r.status == "running"
    assert (r.total, r.processed, r.enriched, r.not_found) == (100, 40, 30, 8)
    assert r.credits_consumed == 30


@respx.mock
def test_apollo_sync(client: Warmbly) -> None:
    respx.get(AP).mock(return_value=httpx.Response(200, json=AP_OVERVIEW))
    ov = client.apollo.overview(CONN)
    assert (ov.account_name, ov.sources, ov.total_imported) == ("Acme", 2, 540)

    key = respx.put(f"{AP}/key").mock(
        return_value=httpx.Response(200, json=AP_OVERVIEW)
    )
    assert client.apollo.replace_key(CONN, api_key="apollo-secret").health == "ok"
    assert _body(key) == {"api_key": "apollo-secret"}
    assert "apollo-secret" not in repr(client.apollo.replace_key(CONN, api_key="k"))

    respx.get(f"{AP}/lists").mock(
        return_value=httpx.Response(
            200, json=_data([{"id": "list1", "name": "VP Sales", "count": 321}])
        )
    )
    assert next(iter(client.apollo.lists(CONN))).count == 321

    prev = respx.post(f"{AP}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 321,
                "sample": [
                    {
                        "apollo_id": "a1",
                        "email": "ada@example.com",
                        "email_status": "verified",
                        "already_in_warmbly": False,
                        "will_import": True,
                    }
                ],
            },
        )
    )
    preview = client.apollo.preview_import(CONN, list_id="list1", verified_only=False)
    assert preview.total == 321
    assert preview.sample[0]["will_import"] is True
    assert _body(prev) == {"list_id": "list1", "verified_only": False}
    client.apollo.preview_import(CONN, list_id="list1")
    assert _body(prev) == {"list_id": "list1"}

    respx.get(f"{AP}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([AP_SOURCE]))
    )
    _check_ap_source(next(iter(client.apollo.list_import_sources(CONN))))

    create = respx.post(f"{AP}/import-sources").mock(
        return_value=httpx.Response(201, json=AP_SOURCE)
    )
    _check_ap_source(
        client.apollo.create_import_source(
            CONN,
            list_id="list1",
            list_name="VP Sales",
            name="VPs",
            campaign_id="camp1",
            category_ids=["cat1"],
            verified_only=True,
            recurring=True,
            enabled=True,
        )
    )
    assert _body(create) == {
        "name": "VPs",
        "list_id": "list1",
        "list_name": "VP Sales",
        "campaign_id": "camp1",
        "category_ids": ["cat1"],
        "verified_only": True,
        "recurring": True,
        "enabled": True,
    }

    patch = respx.patch(f"{AP}/import-sources/{SRC}").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    _check_ap_source(
        client.apollo.update_import_source(
            CONN,
            SRC,
            name="n",
            campaign_id=None,
            category_ids=[],
            verified_only=False,
            recurring=False,
            enabled=False,
        )
    )
    assert _body(patch) == {
        "name": "n",
        "campaign_id": None,
        "category_ids": [],
        "verified_only": False,
        "recurring": False,
        "enabled": False,
    }
    client.apollo.update_import_source(CONN, SRC, enabled=True)
    assert _body(patch) == {"enabled": True}

    respx.post(f"{AP}/import-sources/{SRC}/run").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    _check_ap_source(client.apollo.run_import_source(CONN, SRC))

    respx.delete(f"{AP}/import-sources/{SRC}").mock(return_value=httpx.Response(204))
    assert client.apollo.delete_import_source(CONN, SRC).deleted is None

    runs = respx.get(f"{AP}/enrichments").mock(
        return_value=httpx.Response(200, json=_data([AP_RUN]))
    )
    _check_ap_run(next(iter(client.apollo.list_enrichments(CONN, limit=5))))
    assert _last(runs).url.params["limit"] == "5"

    start = respx.post(f"{AP}/enrichments").mock(
        return_value=httpx.Response(202, json=AP_RUN)
    )
    _check_ap_run(
        client.apollo.start_enrichment(
            CONN,
            contact_ids=["c1", "c2"],
            overwrite=True,
            options={"idempotency_key": "enrich-1"},
        )
    )
    assert _body(start) == {"contact_ids": ["c1", "c2"], "overwrite": True}
    assert _last(start).headers["idempotency-key"] == "enrich-1"
    client.apollo.start_enrichment(
        CONN, select_all=True, filters={"query": "vp"}, exclude=["c9"]
    )
    assert _body(start) == {"all": True, "filters": {"query": "vp"}, "exclude": ["c9"]}

    respx.get(f"{AP}/enrichments/run1").mock(
        return_value=httpx.Response(200, json=AP_RUN)
    )
    _check_ap_run(client.apollo.retrieve_enrichment(CONN, "run1"))


@respx.mock
@pytest.mark.anyio
async def test_apollo_async(aclient: AsyncWarmbly) -> None:
    ap = aclient.apollo
    respx.get(AP).mock(return_value=httpx.Response(200, json=AP_OVERVIEW))
    assert (await ap.overview(CONN)).account_email == "ops@acme.test"

    key = respx.put(f"{AP}/key").mock(
        return_value=httpx.Response(200, json=AP_OVERVIEW)
    )
    await ap.replace_key(CONN, api_key="apollo-secret")
    assert _body(key) == {"api_key": "apollo-secret"}

    respx.get(f"{AP}/lists").mock(
        return_value=httpx.Response(200, json=_data([{"id": "list1", "count": 3}]))
    )
    assert [item.id async for item in ap.lists(CONN)] == ["list1"]

    prev = respx.post(f"{AP}/import/preview").mock(
        return_value=httpx.Response(200, json={"total": 3, "sample": []})
    )
    assert (await ap.preview_import(CONN, list_id="list1")).total == 3
    assert _body(prev) == {"list_id": "list1"}

    respx.get(f"{AP}/import-sources").mock(
        return_value=httpx.Response(200, json=_data([AP_SOURCE]))
    )
    _check_ap_source(await anext(aiter(ap.list_import_sources(CONN))))

    create = respx.post(f"{AP}/import-sources").mock(
        return_value=httpx.Response(201, json=AP_SOURCE)
    )
    _check_ap_source(await ap.create_import_source(CONN, list_id="list1"))
    assert _body(create) == {"list_id": "list1"}

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
    assert (await ap.delete_import_source(CONN, SRC)).deleted is None

    respx.get(f"{AP}/enrichments").mock(
        return_value=httpx.Response(200, json=_data([AP_RUN]))
    )
    _check_ap_run(await anext(aiter(ap.list_enrichments(CONN))))

    start = respx.post(f"{AP}/enrichments").mock(
        return_value=httpx.Response(202, json=AP_RUN)
    )
    _check_ap_run(await ap.start_enrichment(CONN, contact_ids=["c1"], overwrite=False))
    assert _body(start) == {"contact_ids": ["c1"], "overwrite": False}
    await ap.start_enrichment(CONN, select_all=True, exclude=["c2"])
    assert _body(start) == {"all": True, "exclude": ["c2"]}

    respx.get(f"{AP}/enrichments/run1").mock(
        return_value=httpx.Response(200, json=AP_RUN)
    )
    _check_ap_run(await ap.retrieve_enrichment(CONN, "run1"))


# -- Clay, community, inbound secrets ----------------------------------------

CLAY = {
    "connection_id": CONN,
    "label": "Clay",
    "status": "connected",
    "health": "ok",
    "inbound_url_minted": True,
    "defaults": {
        "campaign_id": "camp1",
        "category_ids": [],
        "segment_ids": ["seg1"],
        "dedup": "update",
        "subscribed": True,
    },
    "outbound": {
        "webhook_url_set": True,
        "webhook_host": "clay.com",
        "auth_token_set": True,
        "events": ["reply"],
    },
    "stats": {"received": 10, "created": 6, "updated": 2, "skipped": 1, "failed": 1},
    "available_events": ["reply", "bounce"],
}

COMMUNITY = {
    "application_id": "app1",
    "slug": "acme-sync",
    "name": "Acme Sync",
    "tagline": "Sync Acme",
    "description": "Long text",
    "category": "crm",
    "logo_url": "https://cdn.test/logo.png",
    "website_url": "https://acme.test",
    "install_url": "https://acme.test/install",
    "support_url": "https://acme.test/help",
    "privacy_url": "https://acme.test/privacy",
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
    "status": "published",
    "listed": True,
    "installs": 17,
    "installed": False,
    "published_at": "2026-09-01T00:00:00Z",
}


def _check_clay(c: Any) -> None:
    assert c.inbound_url_minted is True
    assert c.defaults["dedup"] == "update"
    assert c.outbound["webhook_host"] == "clay.com"
    assert c.stats["received"] == 10
    assert list(c.available_events) == ["reply", "bounce"]


def _check_community(a: Any) -> None:
    assert a.slug == "acme-sync"
    assert a.scopes == 5
    assert a.permissions[0]["name"] == "READ_CONTACTS"
    assert (a.listed, a.installs, a.installed) == (True, 17, False)


@respx.mock
def test_integrations_extras_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/integrations/clay/{CONN}").mock(
        return_value=httpx.Response(200, json=CLAY)
    )
    _check_clay(client.integrations.clay_settings(CONN))

    patch = respx.patch(f"{BASE_URL}/integrations/clay/{CONN}").mock(
        return_value=httpx.Response(200, json=CLAY)
    )
    clay = client.integrations.update_clay_settings(
        CONN,
        defaults={"dedup": "skip"},
        webhook_url="https://api.clay.com/v3/sources/webhook/xyz",
        auth_token="clay-token",
        events=["reply"],
    )
    _check_clay(clay)
    assert _body(patch) == {
        "defaults": {"dedup": "skip"},
        "webhook_url": "https://api.clay.com/v3/sources/webhook/xyz",
        "auth_token": "clay-token",
        "events": ["reply"],
    }
    client.integrations.update_clay_settings(CONN, events=[])
    assert _body(patch) == {"events": []}

    apps = respx.get(f"{BASE_URL}/integrations/community").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [COMMUNITY],
                    "pagination": {"total": 2, "next_cursor": "o1", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"application_id": "app2"}],
                    "pagination": {"total": 2, "next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    listed = list(client.integrations.list_community_apps(limit=1))
    assert [a.application_id for a in listed] == ["app1", "app2"]
    _check_community(listed[0])
    assert apps.calls[0].request.url.params["limit"] == "1"
    assert apps.calls[1].request.url.params["cursor"] == "o1"

    respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=COMMUNITY)
    )
    _check_community(client.integrations.retrieve_community_app("acme-sync"))

    rotate = respx.post(
        f"{BASE_URL}/integrations/connections/{CONN}/rotate-inbound-url"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"inbound_webhook_url": "https://api.warmbly.com/in/calendly/s3cr3t"},
        )
    )
    rotated = client.integrations.rotate_inbound_url(CONN)
    assert rotated.inbound_webhook_url == "https://api.warmbly.com/in/calendly/s3cr3t"
    assert "s3cr3t" not in repr(rotated)
    assert _last(rotate).method == "POST"

    key = respx.put(f"{BASE_URL}/integrations/connections/{CONN}/signing-key").mock(
        return_value=httpx.Response(
            200, json={"connection": {"id": CONN, "provider": "calendly"}}
        )
    )
    detail = client.integrations.set_signing_key(CONN, signing_key="k" * 32)
    assert detail.connection.provider == "calendly"
    assert _body(key) == {"signing_key": "k" * 32}
    client.integrations.set_signing_key(CONN, signing_key="")
    assert _body(key) == {"signing_key": ""}


@respx.mock
@pytest.mark.anyio
async def test_integrations_extras_async(aclient: AsyncWarmbly) -> None:
    ig = aclient.integrations
    respx.get(f"{BASE_URL}/integrations/clay/{CONN}").mock(
        return_value=httpx.Response(200, json=CLAY)
    )
    _check_clay(await ig.clay_settings(CONN))

    patch = respx.patch(f"{BASE_URL}/integrations/clay/{CONN}").mock(
        return_value=httpx.Response(200, json=CLAY)
    )
    _check_clay(
        await ig.update_clay_settings(
            CONN,
            defaults={"dedup": "skip"},
            webhook_url="https://x.test",
            auth_token="t",
        )
    )
    assert _body(patch) == {
        "defaults": {"dedup": "skip"},
        "webhook_url": "https://x.test",
        "auth_token": "t",
    }
    await ig.update_clay_settings(CONN, events=["reply"])
    assert _body(patch) == {"events": ["reply"]}

    respx.get(f"{BASE_URL}/integrations/community").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [COMMUNITY],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    apps = [a async for a in ig.list_community_apps()]
    _check_community(apps[0])

    respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=COMMUNITY)
    )
    _check_community(await ig.retrieve_community_app("acme-sync"))

    respx.post(f"{BASE_URL}/integrations/connections/{CONN}/rotate-inbound-url").mock(
        return_value=httpx.Response(
            200, json={"inbound_webhook_url": "https://api.warmbly.com/in/cal/s3cr3t"}
        )
    )
    rotated = await ig.rotate_inbound_url(CONN)
    assert rotated.inbound_webhook_url.endswith("s3cr3t")
    assert "s3cr3t" not in repr(rotated)

    key = respx.put(f"{BASE_URL}/integrations/connections/{CONN}/signing-key").mock(
        return_value=httpx.Response(
            200, json={"connection": {"id": CONN, "provider": "cal_com"}}
        )
    )
    detail = await ig.set_signing_key(CONN, signing_key="k" * 32)
    assert detail.connection.provider == "cal_com"
    assert _body(key) == {"signing_key": "k" * 32}


@respx.mock
def test_integrations_shape_changes_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(
            200, json={"catalog": [{"provider": "apollo", "rank": 3}]}
        )
    )
    assert next(iter(client.integrations.catalog())).rank == 3

    respx.get(f"{BASE_URL}/integrations/connections/{CONN}/webhook-secret").mock(
        return_value=httpx.Response(
            200,
            json={
                "signing_secret": "whsec_live_value",
                "signature_header": "X-Warmbly-Signature",
                "scheme": "HMAC-SHA256",
            },
        )
    )
    secret = client.integrations.connection_webhook_secret(CONN)
    assert secret.signing_secret == "whsec_live_value"
    assert "whsec_live_value" not in repr(secret)
    assert "whsec_live_value" not in str(secret)

    respx.get(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(
            200,
            json={
                "connections": [
                    {"id": CONN, "inbound_webhook_url": "https://x.test/in/s3cr3t"}
                ]
            },
        )
    )
    conn = next(iter(client.integrations.list_connections()))
    assert conn.inbound_webhook_url == "https://x.test/in/s3cr3t"
    assert "s3cr3t" not in repr(conn)
