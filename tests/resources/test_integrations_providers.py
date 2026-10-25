"""Integrations: community directory, signing keys, push, and provider sub-resources."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, page, v  # noqa: F401

SF = f"{BASE_URL}/integrations/salesforce/conn_1"
AP = f"{BASE_URL}/integrations/apollo/conn_1"

SF_SOURCE: dict[str, Any] = {
    "id": "src_1",
    "organization_id": "org_1",
    "connection_id": "conn_1",
    "created_by_user_id": "usr_1",
    "name": "Hot leads",
    "source_kind": "list_view",
    "object": "Lead",
    "source_id": "00B000000000001",
    "source_label": "Hot",
    "campaign_id": "cmp_1",
    "category_ids": ["cat_1"],
    "recurring": True,
    "enabled": True,
    "status": "idle",
    "last_run_at": "2026-10-01T00:00:00Z",
    "last_result": {"read": 10, "imported": 7, "opted_out": 1},
    "last_error": "",
    "total_imported": 7,
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-10-01T00:00:00Z",
}

AP_SOURCE: dict[str, Any] = {
    "id": "src_2",
    "organization_id": "org_1",
    "connection_id": "conn_1",
    "created_by_user_id": "usr_1",
    "name": "Webinar list",
    "list_id": "l_1",
    "list_name": "Webinar",
    "campaign_id": None,
    "category_ids": [],
    "verified_only": True,
    "recurring": False,
    "enabled": True,
    "status": "idle",
    "last_run_at": "2026-10-01T00:00:00Z",
    "last_result": {"read": 5, "unverified": 2, "next_page": 3},
    "last_error": "",
    "total_imported": 3,
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-10-01T00:00:00Z",
}

RUN: dict[str, Any] = {
    "id": "run_1",
    "organization_id": "org_1",
    "connection_id": "conn_1",
    "requested_by_user_id": "usr_1",
    "overwrite": True,
    "status": "running",
    "total": 50,
    "processed": 20,
    "enriched": 15,
    "not_found": 3,
    "failed": 2,
    "credits_consumed": 15,
    "last_error": "",
    "started_at": "2026-10-01T00:00:00Z",
    "finished_at": None,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-01T00:01:00Z",
}


@respx.mock
@pytest.mark.anyio
async def test_community_signing_key_and_push(dual: Any) -> None:
    c = dual.integrations

    app = {
        "application_id": "app_1",
        "slug": "acme-sync",
        "name": "Acme Sync",
        "tagline": "Sync",
        "description": "Syncs things",
        "category": "crm",
        "logo_url": "https://x/logo.png",
        "website_url": "https://acme.com",
        "install_url": "https://acme.com/install",
        "support_url": "https://acme.com/help",
        "privacy_url": "https://acme.com/privacy",
        "developer": "Acme",
        "scopes": 5,
        "permissions": [{"name": "read_contacts", "value": 4}],
        "status": "featured",
        "listed": True,
        "installs": 12,
        "installed": False,
        "published_at": "2026-09-01T00:00:00Z",
    }

    def check(a: Any) -> None:
        assert a.application_id == "app_1"
        assert a.slug == "acme-sync"
        assert a.name == "Acme Sync"
        assert a.category == "crm"
        assert a.logo_url.endswith("logo.png")
        assert a.install_url == "https://acme.com/install"
        assert a.developer == "Acme"
        assert a.scopes == 5
        assert a.permissions[0]["name"] == "read_contacts"
        assert a.status == "featured"
        assert a.listed is True
        assert a.installs == 12
        assert a.installed is False
        assert a.published_at == "2026-09-01T00:00:00Z"

    listing = respx.get(f"{BASE_URL}/integrations/community").mock(
        return_value=httpx.Response(200, json=page([app]))
    )
    check((await items(c.list_community_apps(limit=50, cursor="c1")))[0])
    assert last(listing).url.params["limit"] == "50"
    assert last(listing).url.params["cursor"] == "c1"

    respx.get(f"{BASE_URL}/integrations/community/acme-sync").mock(
        return_value=httpx.Response(200, json=app)
    )
    check(await v(c.get_community_app("acme-sync")))

    key = respx.put(f"{BASE_URL}/integrations/connections/conn_1/signing-key").mock(
        return_value=httpx.Response(
            200, json={"connection": {"id": "conn_1", "provider": "calendly"}}
        )
    )
    detail = await v(c.set_signing_key("conn_1", signing_key="k" * 32))
    assert detail.connection.id == "conn_1"
    assert detail.connection.provider == "calendly"
    assert json.loads(last(key).content) == {"signing_key": "k" * 32}

    rotate = respx.post(
        f"{BASE_URL}/integrations/connections/conn_1/rotate-inbound-url"
    ).mock(
        return_value=httpx.Response(
            200, json={"inbound_webhook_url": "https://api.warmbly.com/in/abc"}
        )
    )
    rot = await v(c.rotate_inbound_url("conn_1"))
    assert rot.inbound_webhook_url == "https://api.warmbly.com/in/abc"
    assert last(rotate).headers["idempotency-key"]

    push = respx.post(f"{BASE_URL}/integrations/connections/conn_1/push").mock(
        return_value=httpx.Response(
            200,
            json={"provider": "hubspot", "pushed": 2, "failed": 0, "results": [{}]},
        )
    )
    res = await v(c.push("conn_1", contact_ids=["a", "b"]))
    assert (res.provider, res.pushed, res.failed) == ("hubspot", 2, 0)
    assert json.loads(last(push).content) == {"contact_ids": ["a", "b"]}
    await v(
        c.push(
            "conn_1",
            contacts=["a"],
            select_all=True,
            filters={"query": "x"},
            exclude=["z"],
        )
    )
    assert json.loads(last(push).content) == {
        "contacts": ["a"],
        "all": True,
        "filters": {"query": "x"},
        "exclude": ["z"],
    }

    cat = respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(
            200, json={"catalog": [{"provider": "apollo", "name": "Apollo", "rank": 3}]}
        )
    )
    entry = (await items(c.catalog()))[0]
    assert entry.rank == 3
    assert last(cat).method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_salesforce_sync(dual: Any) -> None:
    sf = dual.integrations.salesforce

    def check_source(src: Any) -> None:
        assert src.id == "src_1"
        assert src.connection_id == "conn_1"
        assert src.name == "Hot leads"
        assert src.source_kind == "list_view"
        assert src.object == "Lead"
        assert src.source_id == "00B000000000001"
        assert src.source_label == "Hot"
        assert src.campaign_id == "cmp_1"
        assert list(src.category_ids) == ["cat_1"]
        assert src.recurring is True
        assert src.enabled is True
        assert src.last_result["imported"] == 7
        assert src.total_imported == 7

    overview = respx.get(f"{SF}/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "connection_id": "conn_1",
                "label": "Prod",
                "status": "active",
                "health": "ok",
                "health_detail": "",
                "org": {"environment": "production", "instance_url": "https://x"},
                "api": {"used": 10, "max": 100, "calls_today": 4, "budget": 20},
                "counts": {"pending": 1, "synced_24h": 5},
                "last_pull_at": "2026-10-01T00:00:00Z",
                "last_pull_error": "",
                "settings_enabled": True,
                "checks": [{"key": "read_lead", "label": "Read Lead", "ok": True}],
            },
        )
    )
    ov = await v(sf.overview("conn_1", checks=True))
    assert ov.connection_id == "conn_1"
    assert ov.org["environment"] == "production"
    assert ov.api["max"] == 100
    assert ov.counts["synced_24h"] == 5
    assert ov.settings_enabled is True
    assert ov.checks[0]["ok"] is True
    assert ov.last_pull_at == "2026-10-01T00:00:00Z"
    assert last(overview).url.params["checks"] == "1"
    await v(sf.overview("conn_1"))
    assert "checks" not in last(overview).url.params

    respx.get(f"{SF}/settings").mock(
        return_value=httpx.Response(
            200,
            json={
                "settings": {"enabled": True},
                "warmbly_fields": [{"key": "first_name", "label": "First name"}],
                "defaults": {"enabled": True, "daily_api_budget": 0},
            },
        )
    )
    st = await v(sf.get_settings("conn_1"))
    assert st.settings == {"enabled": True}
    assert st.warmbly_fields[0]["key"] == "first_name"
    assert st.defaults["daily_api_budget"] == 0

    put = respx.put(f"{SF}/settings").mock(
        return_value=httpx.Response(200, json={"settings": {"enabled": False}})
    )
    saved = await v(sf.update_settings("conn_1", settings={"enabled": False}))
    assert saved.settings == {"enabled": False}
    assert json.loads(last(put).content) == {"enabled": False}

    respx.get(f"{SF}/metadata").mock(
        return_value=httpx.Response(
            200,
            json={
                "lead_fields": [{"name": "Email", "label": "Email", "type": "email"}],
                "contact_fields": [{"name": "Phone"}],
                "lead_statuses": [{"value": "Open", "label": "Open"}],
                "lead_sources": [{"value": "Web", "label": "Web"}],
            },
        )
    )
    md = await v(sf.metadata("conn_1"))
    assert md.lead_fields[0]["name"] == "Email"
    assert md.contact_fields[0]["name"] == "Phone"
    assert md.lead_statuses[0]["value"] == "Open"
    assert md.lead_sources[0]["label"] == "Web"

    users = respx.get(f"{SF}/users").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "005", "name": "Sam", "email": "sam@x.com"}]},
        )
    )
    user = (await items(sf.list_users("conn_1", q="sam")))[0]
    assert (user.id, user.name, user.email) == ("005", "Sam", "sam@x.com")
    assert last(users).url.params["q"] == "sam"

    views = respx.get(f"{SF}/list-views").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "00B", "label": "Hot", "object": "Lead"}]}
        )
    )
    view = (await items(sf.list_views("conn_1", object="Lead")))[0]
    assert (view.id, view.label, view.object) == ("00B", "Hot", "Lead")
    assert last(views).url.params["object"] == "Lead"

    camps = respx.get(f"{SF}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "701",
                        "name": "Webinar",
                        "status": "Planned",
                        "type": "Event",
                        "member_count": 30,
                    }
                ]
            },
        )
    )
    camp = (await items(sf.list_campaigns("conn_1", q="web")))[0]
    assert (camp.name, camp.status, camp.type, camp.member_count) == (
        "Webinar",
        "Planned",
        "Event",
        30,
    )
    assert last(camps).url.params["q"] == "web"

    prev = respx.post(f"{SF}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={"total": 40, "sample": [{"record_id": "00Q", "email": "a@x.com"}]},
        )
    )
    pv = await v(
        sf.preview_import(
            "conn_1", source_kind="list_view", source_id="00B", object="Lead"
        )
    )
    assert pv.total == 40
    assert pv.sample[0]["email"] == "a@x.com"
    assert json.loads(last(prev).content) == {
        "source_kind": "list_view",
        "source_id": "00B",
        "object": "Lead",
    }

    respx.get(f"{SF}/import-sources").mock(
        return_value=httpx.Response(200, json={"data": [SF_SOURCE]})
    )
    check_source((await items(sf.list_import_sources("conn_1")))[0])

    create = respx.post(f"{SF}/import-sources").mock(
        return_value=httpx.Response(201, json=SF_SOURCE)
    )
    check_source(
        await v(
            sf.create_import_source(
                "conn_1",
                source_kind="list_view",
                source_id="00B",
                object="Lead",
                source_label="Hot",
                name="Hot leads",
                campaign_id="cmp_1",
                category_ids=["cat_1"],
                recurring=True,
                enabled=True,
            )
        )
    )
    assert json.loads(last(create).content) == {
        "source_kind": "list_view",
        "source_id": "00B",
        "object": "Lead",
        "source_label": "Hot",
        "name": "Hot leads",
        "campaign_id": "cmp_1",
        "category_ids": ["cat_1"],
        "recurring": True,
        "enabled": True,
    }
    assert last(create).headers["idempotency-key"]

    patch = respx.patch(f"{SF}/import-sources/src_1").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    check_source(await v(sf.update_import_source("conn_1", "src_1", campaign_id=None)))
    assert json.loads(last(patch).content) == {"campaign_id": None}

    run = respx.post(f"{SF}/import-sources/src_1/run").mock(
        return_value=httpx.Response(200, json=SF_SOURCE)
    )
    check_source(await v(sf.run_import_source("conn_1", "src_1")))
    assert last(run).headers["idempotency-key"]

    drop = respx.delete(f"{SF}/import-sources/src_1").mock(
        return_value=httpx.Response(204)
    )
    await v(sf.delete_import_source("conn_1", "src_1"))
    assert last(drop).method == "DELETE"

    act = {
        "id": "act_1",
        "organization_id": "org_1",
        "connection_id": "conn_1",
        "contact_id": "ct_1",
        "contact_email": "a@x.com",
        "kind": "sent",
        "payload": {"subject": "Hi"},
        "status": "failed",
        "attempts": 2,
        "next_attempt_at": "2026-10-01T00:00:00Z",
        "record_id": "00Q",
        "task_id": "00T",
        "detail": "boom",
        "occurred_at": "2026-10-01T00:00:00Z",
        "created_at": "2026-10-01T00:00:00Z",
        "processed_at": "2026-10-01T00:01:00Z",
    }
    activity = respx.get(f"{SF}/activity").mock(
        return_value=httpx.Response(200, json=page([act]))
    )
    row = (
        await items(
            sf.list_activity(
                "conn_1", status="failed", contact_id="ct_1", limit=10, cursor="cc"
            )
        )
    )[0]
    assert row.id == "act_1"
    assert row.contact_email == "a@x.com"
    assert row.kind == "sent"
    assert row.payload == {"subject": "Hi"}
    assert (row.status, row.attempts, row.detail) == ("failed", 2, "boom")
    assert (row.record_id, row.task_id) == ("00Q", "00T")
    assert row.processed_at == "2026-10-01T00:01:00Z"
    params = last(activity).url.params
    assert params["status"] == "failed"
    assert params["contact_id"] == "ct_1"
    assert params["limit"] == "10"
    assert params["cursor"] == "cc"

    retry = respx.post(f"{SF}/activity/retry").mock(
        return_value=httpx.Response(200, json={"requeued": 2})
    )
    assert (await v(sf.retry_activity("conn_1", ids=["a", "b"]))).requeued == 2
    assert json.loads(last(retry).content) == {"ids": ["a", "b"]}

    sync = respx.post(f"{SF}/sync-now").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await v(sf.sync_now("conn_1"))).ok is True
    assert last(sync).headers["idempotency-key"]


@respx.mock
@pytest.mark.anyio
async def test_apollo_and_clay(dual: Any) -> None:
    ap = dual.integrations.apollo

    overview = {
        "connection_id": "conn_1",
        "label": "Apollo",
        "status": "active",
        "health": "ok",
        "health_detail": "fine",
        "account_name": "Acme",
        "account_email": "me@acme.com",
        "sources": 2,
        "total_imported": 9,
        "last_run_at": "2026-10-01T00:00:00Z",
    }

    def check_overview(o: Any) -> None:
        assert o.connection_id == "conn_1"
        assert (o.label, o.status, o.health) == ("Apollo", "active", "ok")
        assert o.health_detail == "fine"
        assert (o.account_name, o.account_email) == ("Acme", "me@acme.com")
        assert (o.sources, o.total_imported) == (2, 9)
        assert o.last_run_at == "2026-10-01T00:00:00Z"

    respx.get(AP).mock(return_value=httpx.Response(200, json=overview))
    check_overview(await v(ap.overview("conn_1")))

    key = respx.put(f"{AP}/key").mock(return_value=httpx.Response(200, json=overview))
    check_overview(await v(ap.replace_key("conn_1", api_key="k")))
    assert json.loads(last(key).content) == {"api_key": "k"}

    respx.get(f"{AP}/lists").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "l_1", "name": "Webinar", "count": 40}]}
        )
    )
    lst = (await items(ap.list_lists("conn_1")))[0]
    assert (lst.id, lst.name, lst.count) == ("l_1", "Webinar", 40)

    prev = respx.post(f"{AP}/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 40,
                "sample": [
                    {"apollo_id": "a1", "email": "a@x.com", "will_import": True}
                ],
            },
        )
    )
    pv = await v(ap.preview_import("conn_1", list_id="l_1", verified_only=False))
    assert pv.total == 40
    assert pv.sample[0]["will_import"] is True
    assert json.loads(last(prev).content) == {
        "list_id": "l_1",
        "verified_only": False,
    }

    def check_source(src: Any) -> None:
        assert src.id == "src_2"
        assert src.connection_id == "conn_1"
        assert (src.name, src.list_id, src.list_name) == (
            "Webinar list",
            "l_1",
            "Webinar",
        )
        assert src.verified_only is True
        assert src.recurring is False
        assert src.last_result["next_page"] == 3
        assert src.total_imported == 3

    respx.get(f"{AP}/import-sources").mock(
        return_value=httpx.Response(200, json={"data": [AP_SOURCE]})
    )
    check_source((await items(ap.list_import_sources("conn_1")))[0])

    create = respx.post(f"{AP}/import-sources").mock(
        return_value=httpx.Response(201, json=AP_SOURCE)
    )
    check_source(
        await v(
            ap.create_import_source(
                "conn_1",
                list_id="l_1",
                list_name="Webinar",
                name="Webinar list",
                campaign_id="cmp_1",
                category_ids=["cat_1"],
                verified_only=True,
                recurring=False,
                enabled=True,
            )
        )
    )
    assert json.loads(last(create).content) == {
        "list_id": "l_1",
        "list_name": "Webinar",
        "name": "Webinar list",
        "campaign_id": "cmp_1",
        "category_ids": ["cat_1"],
        "verified_only": True,
        "recurring": False,
        "enabled": True,
    }

    patch = respx.patch(f"{AP}/import-sources/src_2").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    check_source(
        await v(
            ap.update_import_source("conn_1", "src_2", campaign_id=None, enabled=False)
        )
    )
    assert json.loads(last(patch).content) == {"campaign_id": None, "enabled": False}

    run = respx.post(f"{AP}/import-sources/src_2/run").mock(
        return_value=httpx.Response(200, json=AP_SOURCE)
    )
    check_source(await v(ap.run_import_source("conn_1", "src_2")))
    assert last(run).headers["idempotency-key"]

    drop = respx.delete(f"{AP}/import-sources/src_2").mock(
        return_value=httpx.Response(204)
    )
    await v(ap.delete_import_source("conn_1", "src_2"))
    assert last(drop).method == "DELETE"

    def check_run(r: Any) -> None:
        assert r.id == "run_1"
        assert r.connection_id == "conn_1"
        assert r.requested_by_user_id == "usr_1"
        assert r.overwrite is True
        assert (r.status, r.total, r.processed) == ("running", 50, 20)
        assert (r.enriched, r.not_found, r.failed) == (15, 3, 2)
        assert r.credits_consumed == 15
        assert r.started_at == "2026-10-01T00:00:00Z"
        assert r.finished_at is None

    runs = respx.get(f"{AP}/enrichments").mock(
        return_value=httpx.Response(200, json={"data": [RUN]})
    )
    check_run((await items(ap.list_enrichments("conn_1", limit=5)))[0])
    assert last(runs).url.params["limit"] == "5"

    start = respx.post(f"{AP}/enrichments").mock(
        return_value=httpx.Response(202, json=RUN)
    )
    check_run(
        await v(
            ap.start_enrichment(
                "conn_1",
                contact_ids=["a"],
                select_all=True,
                filters={"query": "x"},
                exclude=["z"],
                overwrite=True,
            )
        )
    )
    assert json.loads(last(start).content) == {
        "contact_ids": ["a"],
        "all": True,
        "filters": {"query": "x"},
        "exclude": ["z"],
        "overwrite": True,
    }
    assert last(start).headers["idempotency-key"]
    await v(ap.start_enrichment("conn_1", contact_ids=["a"]))
    assert json.loads(last(start).content) == {"contact_ids": ["a"]}

    respx.get(f"{AP}/enrichments/run_1").mock(
        return_value=httpx.Response(200, json=RUN)
    )
    check_run(await v(ap.get_enrichment("conn_1", "run_1")))

    clay = dual.integrations.clay
    settings = {
        "connection_id": "conn_1",
        "label": "Clay",
        "status": "active",
        "health": "ok",
        "inbound_url_minted": True,
        "defaults": {"campaign_id": "cmp_1", "dedup": "update", "subscribed": True},
        "outbound": {"webhook_url_set": True, "webhook_host": "clay.com"},
        "stats": {"received": 9, "created": 5},
        "available_events": ["email.replied"],
    }

    def check_clay(cs: Any) -> None:
        assert cs.connection_id == "conn_1"
        assert (cs.label, cs.status, cs.health) == ("Clay", "active", "ok")
        assert cs.inbound_url_minted is True
        assert cs.defaults["campaign_id"] == "cmp_1"
        assert cs.outbound["webhook_host"] == "clay.com"
        assert cs.stats["received"] == 9
        assert list(cs.available_events) == ["email.replied"]

    respx.get(f"{BASE_URL}/integrations/clay/conn_1").mock(
        return_value=httpx.Response(200, json=settings)
    )
    check_clay(await v(clay.get_settings("conn_1")))

    upd = respx.patch(f"{BASE_URL}/integrations/clay/conn_1").mock(
        return_value=httpx.Response(200, json=settings)
    )
    check_clay(
        await v(
            clay.update_settings(
                "conn_1",
                defaults={"dedup": "update"},
                webhook_url="https://clay.com/hook",
                auth_token="",
                events=["email.replied"],
            )
        )
    )
    assert json.loads(last(upd).content) == {
        "defaults": {"dedup": "update"},
        "webhook_url": "https://clay.com/hook",
        "auth_token": "",
        "events": ["email.replied"],
    }
    await v(clay.update_settings("conn_1"))
    assert json.loads(last(upd).content) == {}
