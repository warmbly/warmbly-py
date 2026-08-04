"""Broad sweep over every resource method on both the sync and async clients.

For each resource method this asserts the HTTP verb + path (and, where relevant,
the request body / query params) against a respx mock. The async variants are
exercised against :class:`~warmbly.AsyncWarmbly`, including paginated endpoints
iterated both with ``async for`` and ``await`` (which return an
``AsyncPaginator``).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


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


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


# ===========================================================================
# api_keys
# ===========================================================================
@respx.mock
def test_api_keys_sync_extra_methods(client: Warmbly) -> None:
    analytics = respx.get(f"{BASE_URL}/api-keys/usage/analytics").mock(
        return_value=httpx.Response(200, json={"total": 5})
    )
    client.api_keys.usage_analytics(from_="a", to="b", interval="day")
    req = _last(analytics)
    assert req.url.params.get("from") == "a"
    assert req.url.params.get("interval") == "day"

    per_key = respx.get(f"{BASE_URL}/api-keys/ak_1/analytics").mock(
        return_value=httpx.Response(200, json={"api_key_id": "ak_1"})
    )
    client.api_keys.analytics("ak_1")
    assert _last(per_key).url.path == "/v1/api-keys/ak_1/analytics"

    logs = respx.get(f"{BASE_URL}/api-keys/ak_1/logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "log_1"}]))
    )
    assert [x.id for x in client.api_keys.logs("ak_1")] == ["log_1"]
    assert _last(logs).url.path == "/v1/api-keys/ak_1/logs"


@pytest.mark.anyio
@respx.mock
async def test_api_keys_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            201, json={"id": "ak_1", "name": "k", "secret": "s"}
        )
    )
    key = await aclient.api_keys.create(name="k", permissions=7)
    assert key.secret == "s"
    assert _last(create).method == "POST"

    retrieve = respx.get(f"{BASE_URL}/api-keys/ak_1").mock(
        return_value=httpx.Response(200, json={"id": "ak_1", "name": "k"})
    )
    assert (await aclient.api_keys.retrieve("ak_1")).id == "ak_1"
    assert _last(retrieve).method == "GET"

    update = respx.patch(f"{BASE_URL}/api-keys/ak_1").mock(
        return_value=httpx.Response(200, json={"id": "ak_1", "name": "n"})
    )
    await aclient.api_keys.update("ak_1", name="n", permissions=3)
    assert json.loads(_last(update).content) == {"name": "n", "permissions": 3}

    delete = respx.delete(f"{BASE_URL}/api-keys/ak_1").mock(
        return_value=httpx.Response(200, json={"status": "revoked"})
    )
    res = await aclient.api_keys.delete("ak_1", reason="x")
    assert res.status == "revoked"
    assert _last(delete).url.params.get("reason") == "x"

    perms = respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(200, json={"permissions": [], "presets": {}})
    )
    await aclient.api_keys.permissions()
    assert _last(perms).url.path == "/v1/api-keys/permissions"

    summary = respx.get(f"{BASE_URL}/api-keys/usage/summary").mock(
        return_value=httpx.Response(200, json={"active_keys": 1})
    )
    assert (await aclient.api_keys.usage_summary()).active_keys == 1
    assert _last(summary).url.path == "/v1/api-keys/usage/summary"

    analytics = respx.get(f"{BASE_URL}/api-keys/usage/analytics").mock(
        return_value=httpx.Response(200, json={"total": 1})
    )
    await aclient.api_keys.usage_analytics(from_="a")
    assert _last(analytics).url.params.get("from") == "a"

    per_key = respx.get(f"{BASE_URL}/api-keys/ak_1/analytics").mock(
        return_value=httpx.Response(200, json={"api_key_id": "ak_1"})
    )
    await aclient.api_keys.analytics("ak_1")
    assert _last(per_key).url.path == "/v1/api-keys/ak_1/analytics"


@pytest.mark.anyio
@respx.mock
async def test_api_keys_async_list_both_styles(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(200, json=_page([{"id": "ak_1", "name": "k"}]))
    )
    ids = [k.id async for k in aclient.api_keys.list(limit=5)]
    assert ids == ["ak_1"]

    page = await aclient.api_keys.list()
    assert [k.id for k in page.data] == ["ak_1"]
    assert not page.has_next_page()

    logs = respx.get(f"{BASE_URL}/api-keys/ak_1/logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "log_1"}]))
    )
    got = [x.id async for x in aclient.api_keys.logs("ak_1")]
    assert got == ["log_1"]
    assert logs.called


# ===========================================================================
# me
# ===========================================================================
@respx.mock
def test_me_sync(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/me").mock(
        return_value=httpx.Response(
            200,
            json={
                "user_id": "u_1",
                "email": "dev@example.com",
                "auth_type": "api_key",
                "scopes": ["read_campaigns"],
            },
        )
    )
    me = client.me.retrieve()
    assert _last(r).url.path == "/v1/me"
    assert me.auth_type == "api_key"
    assert list(me.scopes) == ["read_campaigns"]


@pytest.mark.anyio
@respx.mock
async def test_me_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/me").mock(
        return_value=httpx.Response(200, json={"user_id": "u_1"})
    )
    assert (await aclient.me.retrieve()).user_id == "u_1"


# ===========================================================================
# oauth applications
# ===========================================================================
@respx.mock
def test_oauth_applications_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(200, json={"applications": [{"id": "app_1"}]})
    )
    assert [a.id for a in client.oauth_applications.list()] == ["app_1"]
    assert _last(listing).url.path == "/v1/oauth/applications"

    endpoints = respx.get(
        f"{BASE_URL}/oauth/applications/app_1/webhook-endpoints"
    ).mock(return_value=httpx.Response(200, json={"endpoints": [{"id": "ep_1"}]}))
    assert [e.id for e in client.oauth_applications.webhook_endpoints("app_1")] == [
        "ep_1"
    ]
    assert endpoints.called

    deliveries = respx.get(
        f"{BASE_URL}/oauth/applications/app_1/webhook-deliveries"
    ).mock(return_value=httpx.Response(200, json=_page([{"id": "dl_1"}])))
    got = list(client.oauth_applications.webhook_deliveries("app_1", status="failed"))
    assert [d.id for d in got] == ["dl_1"]
    assert _last(deliveries).url.params.get("status") == "failed"

    logo = respx.post(f"{BASE_URL}/oauth/application-logo").mock(
        return_value=httpx.Response(200, json={"logo_url": "https://cdn/logo.png"})
    )
    result = client.oauth_applications.upload_logo(file=b"\x89PNG")
    assert result.logo_url == "https://cdn/logo.png"
    req = _last(logo)
    assert req.headers["content-type"].startswith("multipart/form-data")
    # Multipart uploads must not carry an Idempotency-Key.
    assert "idempotency-key" not in req.headers


@pytest.mark.anyio
@respx.mock
async def test_oauth_applications_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-endpoints").mock(
        return_value=httpx.Response(200, json={"endpoints": [{"id": "ep_1"}]})
    )
    got = [e.id async for e in aclient.oauth_applications.webhook_endpoints("app_1")]
    assert got == ["ep_1"]

    respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    page = await aclient.oauth_applications.webhook_deliveries("app_1")
    assert [d.id for d in page.data] == ["dl_1"]

    logo = respx.post(f"{BASE_URL}/oauth/application-logo").mock(
        return_value=httpx.Response(200, json={"logo_url": "https://cdn/l.png"})
    )
    assert (await aclient.oauth_applications.upload_logo(file=b"x")).logo_url
    assert logo.called


# ===========================================================================
# campaigns
# ===========================================================================
@respx.mock
def test_campaigns_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(200, json=_page([{"id": "camp_1"}]))
    )
    assert [c.id for c in client.campaigns.list(q="q", status="active")] == ["camp_1"]
    assert _last(listing).url.params.get("status") == "active"

    overview = respx.get(f"{BASE_URL}/campaigns-overview").mock(
        return_value=httpx.Response(200, json={"total": 3, "active": 1})
    )
    assert client.campaigns.overview().total == 3
    assert _last(overview).url.path == "/v1/campaigns-overview"

    preview = respx.post(f"{BASE_URL}/campaign-template-preview").mock(
        return_value=httpx.Response(200, json={"subject": "Hi Alex"})
    )
    out = client.campaigns.preview_template(
        subject="Hi {{.FirstName}}", contact={"first_name": "Alex"}
    )
    assert out.subject == "Hi Alex"
    assert json.loads(_last(preview).content) == {
        "subject": "Hi {{.FirstName}}",
        "contact": {"first_name": "Alex"},
    }

    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(200, json={"id": "camp_1"})
    )
    client.campaigns.create(
        name="Q1", schedule_windows={"mon": [{"start": 9, "end": 17}]}
    )
    assert json.loads(_last(create).content) == {
        "name": "Q1",
        "schedule_windows": {"mon": [{"start": 9, "end": 17}]},
    }

    update = respx.patch(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1"})
    )
    client.campaigns.update("camp_1", ramp_enabled=True, esp_match_mode="strict")
    assert json.loads(_last(update).content) == {
        "ramp_enabled": True,
        "esp_match_mode": "strict",
    }

    get = respx.get(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1", "status": "draft"})
    )
    assert client.campaigns.retrieve("camp_1").status == "draft"
    assert get.called

    drop = respx.delete(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.campaigns.delete("camp_1").id is None
    assert drop.called

    advanced = respx.get(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(200, json={"campaign_id": "camp_1"})
    )
    assert client.campaigns.retrieve_advanced("camp_1").campaign_id == "camp_1"
    assert advanced.called

    set_advanced = respx.patch(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(204)
    )
    assert (
        client.campaigns.update_advanced("camp_1", settings={"preflight": {}}) is None
    )
    assert json.loads(_last(set_advanced).content) == {"settings": {"preflight": {}}}


@respx.mock
def test_campaigns_sync_steps_and_variants(client: Warmbly) -> None:
    steps = respx.get(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(200, json=_page([{"id": "st_1"}]))
    )
    assert [s.id for s in client.campaigns.list_steps("camp_1")] == ["st_1"]
    assert steps.called

    update_step = respx.patch(f"{BASE_URL}/campaigns/camp_1/steps/st_1").mock(
        return_value=httpx.Response(200, json={"id": "st_1"})
    )
    client.campaigns.update_step(
        "camp_1", "st_1", wait_after=3, kind="action", action={"type": "add_tag"}
    )
    assert json.loads(_last(update_step).content) == {
        "wait_after": 3,
        "kind": "action",
        "action": {"type": "add_tag"},
    }

    delete_step = respx.delete(f"{BASE_URL}/campaigns/camp_1/steps/st_1").mock(
        return_value=httpx.Response(204)
    )
    client.campaigns.delete_step("camp_1", "st_1")
    assert delete_step.called

    layout = respx.patch(f"{BASE_URL}/campaigns/camp_1/step-layout").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert client.campaigns.set_step_layout(
        "camp_1", positions=[{"id": "st_1", "x": 1.0, "y": 2.0}]
    ).ok
    assert json.loads(_last(layout).content) == {
        "positions": [{"id": "st_1", "x": 1.0, "y": 2.0}]
    }

    variants = respx.get(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "v_1"}]})
    )
    assert [v.id for v in client.campaigns.list_ab_variants("camp_1")] == ["v_1"]
    assert variants.called

    make_variant = respx.post(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(201, json={"id": "v_1"})
    )
    client.campaigns.create_ab_variant("camp_1", name="B", step_id="st_1", weight=50)
    assert json.loads(_last(make_variant).content) == {
        "name": "B",
        "step_id": "st_1",
        "weight": 50,
    }

    edit_variant = respx.patch(f"{BASE_URL}/campaigns/camp_1/ab-variants/v_1").mock(
        return_value=httpx.Response(200, json={"id": "v_1"})
    )
    client.campaigns.update_ab_variant("camp_1", "v_1", is_active=False)
    assert json.loads(_last(edit_variant).content) == {"is_active": False}

    drop_variant = respx.delete(f"{BASE_URL}/campaigns/camp_1/ab-variants/v_1").mock(
        return_value=httpx.Response(204)
    )
    client.campaigns.delete_ab_variant("camp_1", "v_1")
    assert drop_variant.called

    analysis = respx.get(f"{BASE_URL}/campaigns/camp_1/ab-analysis").mock(
        return_value=httpx.Response(200, json={"winner": "v_1"})
    )
    assert client.campaigns.ab_analysis("camp_1").winner == "v_1"
    assert analysis.called


@respx.mock
def test_campaigns_sync_run_and_attachments(client: Warmbly) -> None:
    attachments = respx.get(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "at_1"}]})
    )
    assert [a.id for a in client.campaigns.list_attachments("camp_1")] == ["at_1"]
    assert attachments.called

    upload = respx.post(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(201, json={"id": "at_1", "filename": "a.pdf"})
    )
    got = client.campaigns.upload_attachment(
        "camp_1", file=b"%PDF", filename="a.pdf", step_id="st_1"
    )
    assert got.filename == "a.pdf"
    req = _last(upload)
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b"st_1" in req.content

    drop = respx.delete(f"{BASE_URL}/campaigns/camp_1/attachments/at_1").mock(
        return_value=httpx.Response(204)
    )
    client.campaigns.delete_attachment("camp_1", "at_1")
    assert drop.called

    senders = respx.get(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"data": [{"email_account_id": "em_1"}]})
    )
    assert client.campaigns.senders("camp_1").data[0].email_account_id == "em_1"
    assert senders.called

    set_senders = respx.put(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    client.campaigns.set_senders(
        "camp_1", senders=[{"email_account_id": "em_1", "weight": 2}]
    )
    assert json.loads(_last(set_senders).content) == {
        "senders": [{"email_account_id": "em_1", "weight": 2}]
    }

    verify = respx.post(f"{BASE_URL}/campaigns/camp_1/tracking-domain/verify").mock(
        return_value=httpx.Response(200, json={"tracking_domain_verified": True})
    )
    assert client.campaigns.verify_tracking_domain("camp_1").tracking_domain_verified
    assert verify.called

    preflight = respx.post(f"{BASE_URL}/campaigns/camp_1/preflight").mock(
        return_value=httpx.Response(200, json={"ready": True})
    )
    assert client.campaigns.preflight("camp_1").ready is True
    assert preflight.called

    test_email = respx.post(f"{BASE_URL}/campaigns/camp_1/test-email").mock(
        return_value=httpx.Response(200, json={"message": "test email sent"})
    )
    client.campaigns.send_test_email(
        "camp_1", account_id="em_1", recipient="qa@example.com", step_id="st_1"
    )
    assert json.loads(_last(test_email).content) == {
        "account_id": "em_1",
        "recipient": "qa@example.com",
        "step_id": "st_1",
    }

    start = respx.post(f"{BASE_URL}/campaigns/camp_1/start").mock(
        return_value=httpx.Response(200, json={"status": "started"})
    )
    assert client.campaigns.start("camp_1").status == "started"
    assert start.called

    stop = respx.post(f"{BASE_URL}/campaigns/camp_1/stop").mock(
        return_value=httpx.Response(200, json={"status": "stopped"})
    )
    assert client.campaigns.stop("camp_1").status == "stopped"
    assert stop.called

    logs = respx.get(f"{BASE_URL}/campaigns/camp_1/logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "lg_1"}]))
    )
    assert [x.id for x in client.campaigns.logs("camp_1", limit=10)] == ["lg_1"]
    assert _last(logs).url.params.get("limit") == "10"


@pytest.mark.anyio
@respx.mock
async def test_campaigns_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(200, json=_page([{"id": "camp_1"}]))
    )
    assert [c.id async for c in aclient.campaigns.list()] == ["camp_1"]

    respx.get(f"{BASE_URL}/campaigns-overview").mock(
        return_value=httpx.Response(200, json={"total": 1})
    )
    assert (await aclient.campaigns.overview()).total == 1

    respx.post(f"{BASE_URL}/campaign-template-preview").mock(
        return_value=httpx.Response(200, json={"subject": "s"})
    )
    assert (await aclient.campaigns.preview_template(subject="s")).subject == "s"

    respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(200, json={"id": "camp_1"})
    )
    assert (await aclient.campaigns.create(name="Q1")).id == "camp_1"

    respx.get(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1"})
    )
    assert (await aclient.campaigns.retrieve("camp_1")).id == "camp_1"

    respx.patch(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1"})
    )
    assert (await aclient.campaigns.update("camp_1", name="New")).id == "camp_1"

    respx.delete(f"{BASE_URL}/campaigns/camp_1").mock(return_value=httpx.Response(204))
    assert (await aclient.campaigns.delete("camp_1")).id is None

    respx.get(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(200, json={"campaign_id": "camp_1"})
    )
    assert (await aclient.campaigns.retrieve_advanced("camp_1")).campaign_id

    respx.patch(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(204)
    )
    assert await aclient.campaigns.update_advanced("camp_1", settings={}) is None


@pytest.mark.anyio
@respx.mock
async def test_campaigns_async_sweep_two(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(200, json=_page([{"id": "st_1"}]))
    )
    assert [s.id async for s in aclient.campaigns.list_steps("camp_1")] == ["st_1"]

    respx.post(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(200, json={"id": "st_1"})
    )
    assert (await aclient.campaigns.create_step("camp_1")).id == "st_1"

    respx.patch(f"{BASE_URL}/campaigns/camp_1/steps/st_1").mock(
        return_value=httpx.Response(200, json={"id": "st_1"})
    )
    assert (await aclient.campaigns.update_step("camp_1", "st_1", subject="s")).id

    respx.delete(f"{BASE_URL}/campaigns/camp_1/steps/st_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.campaigns.delete_step("camp_1", "st_1")).id is None

    respx.patch(f"{BASE_URL}/campaigns/camp_1/step-layout").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await aclient.campaigns.set_step_layout("camp_1", positions=[])).ok

    respx.get(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "v_1"}]})
    )
    assert [v.id async for v in aclient.campaigns.list_ab_variants("camp_1")] == ["v_1"]

    respx.post(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(201, json={"id": "v_1"})
    )
    assert (await aclient.campaigns.create_ab_variant("camp_1", name="B")).id == "v_1"

    respx.patch(f"{BASE_URL}/campaigns/camp_1/ab-variants/v_1").mock(
        return_value=httpx.Response(200, json={"id": "v_1"})
    )
    assert (await aclient.campaigns.update_ab_variant("camp_1", "v_1", weight=1)).id

    respx.delete(f"{BASE_URL}/campaigns/camp_1/ab-variants/v_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.campaigns.delete_ab_variant("camp_1", "v_1")).id is None

    respx.get(f"{BASE_URL}/campaigns/camp_1/ab-analysis").mock(
        return_value=httpx.Response(200, json={"winner": "v_1"})
    )
    assert (await aclient.campaigns.ab_analysis("camp_1")).winner == "v_1"


@pytest.mark.anyio
@respx.mock
async def test_campaigns_async_run_and_attachments(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "at_1"}]})
    )
    got = [a.id async for a in aclient.campaigns.list_attachments("camp_1")]
    assert got == ["at_1"]

    respx.post(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(201, json={"id": "at_1"})
    )
    created = await aclient.campaigns.upload_attachment(
        "camp_1", file=b"x", filename="a.txt"
    )
    assert created.id == "at_1"

    respx.delete(f"{BASE_URL}/campaigns/camp_1/attachments/at_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.campaigns.delete_attachment("camp_1", "at_1")).id is None

    respx.get(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.campaigns.senders("camp_1")).data == []

    respx.put(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.campaigns.set_senders("camp_1", senders=[])).data == []

    respx.post(f"{BASE_URL}/campaigns/camp_1/tracking-domain/verify").mock(
        return_value=httpx.Response(200, json={"tracking_domain_verified": False})
    )
    verified = await aclient.campaigns.verify_tracking_domain("camp_1")
    assert verified.tracking_domain_verified is False

    respx.post(f"{BASE_URL}/campaigns/camp_1/preflight").mock(
        return_value=httpx.Response(200, json={"ready": False})
    )
    assert (await aclient.campaigns.preflight("camp_1")).ready is False

    respx.post(f"{BASE_URL}/campaigns/camp_1/test-email").mock(
        return_value=httpx.Response(200, json={"message": "sent"})
    )
    sent = await aclient.campaigns.send_test_email(
        "camp_1", account_id="em_1", recipient="qa@example.com"
    )
    assert sent.message == "sent"

    respx.post(f"{BASE_URL}/campaigns/camp_1/start").mock(
        return_value=httpx.Response(200, json={"status": "started"})
    )
    assert (await aclient.campaigns.start("camp_1")).status == "started"

    respx.post(f"{BASE_URL}/campaigns/camp_1/stop").mock(
        return_value=httpx.Response(200, json={"status": "stopped"})
    )
    assert (await aclient.campaigns.stop("camp_1")).status == "stopped"

    respx.get(f"{BASE_URL}/campaigns/camp_1/logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "lg_1"}]))
    )
    assert [x.id async for x in aclient.campaigns.logs("camp_1")] == ["lg_1"]


# ===========================================================================
# emails
# ===========================================================================
@respx.mock
def test_emails_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/emails").mock(
        return_value=httpx.Response(200, json=_page([{"id": "em_1"}]))
    )
    assert [e.id for e in client.emails.list(q="acme", tag="sales")] == ["em_1"]
    assert _last(listing).url.params.get("tag") == "sales"

    update = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1"})
    )
    client.emails.update("em_1", warmup=True, warmup_max=40, signature_html="<b>x</b>")
    assert json.loads(_last(update).content) == {
        "warmup": True,
        "warmup_max": 40,
        "signature_html": "<b>x</b>",
    }

    bulk = respx.patch(f"{BASE_URL}/emails/tags").mock(
        return_value=httpx.Response(200, json={"updated": 2})
    )
    assert client.emails.bulk_tag(email_ids=["a", "b"], add_tags=["x"]).updated == 2
    assert json.loads(_last(bulk).content) == {
        "email_ids": ["a", "b"],
        "add_tags": ["x"],
    }

    track = respx.patch(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(200, json={"tracking_domain": "t.example.com"})
    )
    result = client.emails.track("em_1", domain="t.example.com")
    assert result.tracking_domain == "t.example.com"
    # The domain rides the query string, not a JSON body.
    assert _last(track).url.params.get("domain") == "t.example.com"
    assert _last(track).content == b""

    appeal = respx.post(f"{BASE_URL}/emails/em_1/warmup/appeal").mock(
        return_value=httpx.Response(200, json={"appeal_id": "ap_1"})
    )
    assert client.emails.warmup_appeal("em_1", reason="fixed").appeal_id == "ap_1"
    assert json.loads(_last(appeal).content) == {"reason": "fixed"}

    delete = respx.delete(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.emails.delete("em_1").id is None
    assert delete.called


@respx.mock
def test_emails_sync_warmup_and_checks(client: Warmbly) -> None:
    for action in ("start", "pause", "resume", "stop"):
        route = respx.post(f"{BASE_URL}/emails/em_1/warmup/{action}").mock(
            return_value=httpx.Response(200, json={"id": "em_1"})
        )
        assert getattr(client.emails, f"warmup_{action}")("em_1").id == "em_1"
        assert route.called

    ban = respx.get(f"{BASE_URL}/emails/em_1/warmup/ban-status").mock(
        return_value=httpx.Response(200, json={"banned": False})
    )
    assert client.emails.warmup_ban_status("em_1").banned is False
    assert ban.called

    auth = respx.get(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json={"auth_state": "ok", "spf": True})
    )
    assert client.emails.auth_check("em_1").auth_state == "ok"
    assert auth.called

    verify = respx.post(f"{BASE_URL}/emails/verify").mock(
        return_value=httpx.Response(200, json={"email": "a@e.com", "valid": True})
    )
    assert client.emails.verify(email="a@e.com").valid is True
    assert json.loads(_last(verify).content) == {"email": "a@e.com"}

    retrieve = respx.get(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1"})
    )
    assert client.emails.retrieve("em_1").id == "em_1"
    assert retrieve.called


@pytest.mark.anyio
@respx.mock
async def test_emails_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails").mock(
        return_value=httpx.Response(200, json=_page([{"id": "em_1"}]))
    )
    assert [e.id async for e in aclient.emails.list()] == ["em_1"]

    respx.get(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1"})
    )
    assert (await aclient.emails.retrieve("em_1")).id == "em_1"

    respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1"})
    )
    assert (await aclient.emails.update("em_1", name="Sales")).id == "em_1"

    respx.patch(f"{BASE_URL}/emails/tags").mock(
        return_value=httpx.Response(200, json={"updated": 1})
    )
    assert (await aclient.emails.bulk_tag(email_ids=["a"], remove_tags=["x"])).updated

    respx.patch(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(200, json={"tracking_domain": "t"})
    )
    assert (await aclient.emails.track("em_1", domain="t")).tracking_domain == "t"

    for action in ("start", "pause", "resume", "stop"):
        respx.post(f"{BASE_URL}/emails/em_1/warmup/{action}").mock(
            return_value=httpx.Response(200, json={"id": "em_1"})
        )
        assert (await getattr(aclient.emails, f"warmup_{action}")("em_1")).id == "em_1"

    respx.get(f"{BASE_URL}/emails/em_1/warmup/ban-status").mock(
        return_value=httpx.Response(200, json={"banned": True})
    )
    assert (await aclient.emails.warmup_ban_status("em_1")).banned is True

    respx.post(f"{BASE_URL}/emails/em_1/warmup/appeal").mock(
        return_value=httpx.Response(200, json={"appeal_id": "ap_1"})
    )
    assert (await aclient.emails.warmup_appeal("em_1")).appeal_id == "ap_1"

    respx.get(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json={"auth_state": "ok"})
    )
    assert (await aclient.emails.auth_check("em_1")).auth_state == "ok"

    respx.post(f"{BASE_URL}/emails/verify").mock(
        return_value=httpx.Response(200, json={"valid": False})
    )
    assert (await aclient.emails.verify(email="a@e.com")).valid is False

    respx.delete(f"{BASE_URL}/emails/em_1").mock(return_value=httpx.Response(204))
    assert (await aclient.emails.delete("em_1")).id is None


# ===========================================================================
# contacts
# ===========================================================================
@respx.mock
def test_contacts_sync_sweep(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"created": 1})
    )
    assert client.contacts.create([{"email": "a@e.com"}]).created == 1
    # The endpoint takes a bare array, not an object.
    assert json.loads(_last(create).content) == [{"email": "a@e.com"}]

    search = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "ct_1"}]})
    )
    page = client.contacts.search(subscribed=True, limit=5, cursor="cur")
    assert [c.id for c in page.data] == ["ct_1"]
    assert json.loads(_last(search).content) == {"subscribed": True}
    assert _last(search).url.params.get("cursor") == "cur"

    lookup = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"contact": {"id": "ct_1"}})
    )
    assert client.contacts.lookup(email="a@e.com").contact.id == "ct_1"
    assert _last(lookup).url.params.get("email") == "a@e.com"

    fields = respx.get(f"{BASE_URL}/contacts/custom-fields").mock(
        return_value=httpx.Response(200, json={"data": ["role", "tier"]})
    )
    assert list(client.contacts.custom_fields().data) == ["role", "tier"]
    assert fields.called

    get = respx.get(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(
            200, json={"id": "ct_1", "engagement": {"total_sent": 4}}
        )
    )
    detail = client.contacts.retrieve("ct_1")
    assert detail.engagement["total_sent"] == 4
    assert get.called

    update = respx.patch(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    client.contacts.update("ct_1", first_name="Alex", add_categories=["cat_1"])
    assert json.loads(_last(update).content) == {
        "first_name": "Alex",
        "add_categories": ["cat_1"],
    }

    drop = respx.delete(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.contacts.delete("ct_1").id is None
    assert drop.called

    bulk_edit = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 2})
    )
    client.contacts.bulk_update(contacts=["a", "b"], subscribe=False)
    assert json.loads(_last(bulk_edit).content) == {
        "contacts": ["a", "b"],
        "subscribe": False,
    }

    bulk_delete = respx.delete(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(204)
    )
    client.contacts.bulk_delete(["a", "b"])
    assert json.loads(_last(bulk_delete).content) == ["a", "b"]


@respx.mock
def test_contacts_sync_subresources(client: Warmbly) -> None:
    notes = respx.get(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(200, json=_page([{"id": "n_1"}]))
    )
    assert [n.id for n in client.contacts.list_notes("ct_1")] == ["n_1"]
    assert notes.called

    make_note = respx.post(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(201, json={"id": "n_1"})
    )
    client.contacts.create_note("ct_1", content="hi")
    assert json.loads(_last(make_note).content) == {"content": "hi"}

    edit_note = respx.patch(f"{BASE_URL}/contacts/ct_1/notes/n_1").mock(
        return_value=httpx.Response(200, json={"id": "n_1"})
    )
    client.contacts.update_note("ct_1", "n_1", content="bye")
    assert json.loads(_last(edit_note).content) == {"content": "bye"}

    drop_note = respx.delete(f"{BASE_URL}/contacts/ct_1/notes/n_1").mock(
        return_value=httpx.Response(204)
    )
    client.contacts.delete_note("ct_1", "n_1")
    assert drop_note.called

    acts = respx.get(f"{BASE_URL}/contacts/ct_1/activities").mock(
        return_value=httpx.Response(200, json=_page([{"id": "ac_1"}]))
    )
    assert [a.id for a in client.contacts.list_activities("ct_1")] == ["ac_1"]
    assert acts.called

    emails = respx.get(f"{BASE_URL}/contacts/ct_1/emails").mock(
        return_value=httpx.Response(200, json=_page([{"task_id": "t_1"}]))
    )
    got = list(client.contacts.list_emails("ct_1", before_at="2026-01-01"))
    assert [e.task_id for e in got] == ["t_1"]
    assert _last(emails).url.params.get("before_at") == "2026-01-01"

    deals = respx.get(f"{BASE_URL}/contacts/ct_1/deals").mock(
        return_value=httpx.Response(200, json=[{"id": "d_1"}])
    )
    assert [d["id"] for d in client.contacts.list_deals("ct_1")] == ["d_1"]
    assert deals.called

    timeline = respx.get(f"{BASE_URL}/contacts/ct_1/timeline").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tl_1"}]))
    )
    assert [t.id for t in client.contacts.timeline("ct_1")] == ["tl_1"]
    assert timeline.called


@respx.mock
def test_contacts_sync_research_and_io(client: Warmbly) -> None:
    runs = respx.get(f"{BASE_URL}/contacts/ct_1/research").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "r_1"}]})
    )
    assert [r.id for r in client.contacts.list_research("ct_1")] == ["r_1"]
    assert runs.called

    run = respx.post(f"{BASE_URL}/contacts/ct_1/research").mock(
        return_value=httpx.Response(200, json={"id": "r_1"})
    )
    client.contacts.research("ct_1", objective="find funding")
    assert json.loads(_last(run).content) == {"objective": "find funding"}

    batch = respx.post(f"{BASE_URL}/contacts/research/batch").mock(
        return_value=httpx.Response(200, json={"queued": 2})
    )
    assert client.contacts.research_batch(contact_ids=["a", "b"]).queued == 2
    assert json.loads(_last(batch).content) == {"contact_ids": ["a", "b"]}

    preview = respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(200, json={"headers": ["email"], "total_rows": 3})
    )
    got = client.contacts.import_preview(file=b"email\na@e.com", filename="leads.csv")
    assert got.total_rows == 3
    assert _last(preview).headers["content-type"].startswith("multipart/form-data")

    commit = respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(200, json={"total": 3, "imported": 3})
    )
    result = client.contacts.import_commit(
        file=b"email", filename="leads.csv", import_options={"dedup": "update"}
    )
    assert result.imported == 3
    assert b"dedup" in _last(commit).content

    export = respx.post(f"{BASE_URL}/contacts/export").mock(
        return_value=httpx.Response(200, content=b"email\na@e.com")
    )
    blob = client.contacts.export(format="csv", scope="all")
    assert blob == b"email\na@e.com"
    assert json.loads(_last(export).content) == {"format": "csv", "scope": "all"}


@pytest.mark.anyio
@respx.mock
async def test_contacts_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"created": 1})
    )
    assert (await aclient.contacts.create([{"email": "a@e.com"}])).created == 1

    respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.contacts.search(query="q")).data == []

    respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"contact": None})
    )
    assert (await aclient.contacts.lookup(email="a@e.com")).contact is None

    respx.get(f"{BASE_URL}/contacts/custom-fields").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.contacts.custom_fields()).data == []

    respx.get(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    assert (await aclient.contacts.retrieve("ct_1")).id == "ct_1"

    respx.patch(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    assert (await aclient.contacts.update("ct_1", first_name="A")).id == "ct_1"

    respx.delete(f"{BASE_URL}/contacts/ct_1").mock(return_value=httpx.Response(204))
    assert (await aclient.contacts.delete("ct_1")).id is None

    respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 1})
    )
    assert (await aclient.contacts.bulk_update(contacts=["a"])).updated == 1

    respx.delete(f"{BASE_URL}/contacts").mock(return_value=httpx.Response(204))
    assert (await aclient.contacts.bulk_delete(["a"])).id is None


@pytest.mark.anyio
@respx.mock
async def test_contacts_async_subresources(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(200, json=_page([{"id": "n_1"}]))
    )
    assert [n.id async for n in aclient.contacts.list_notes("ct_1")] == ["n_1"]

    respx.post(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(201, json={"id": "n_1"})
    )
    assert (await aclient.contacts.create_note("ct_1", content="hi")).id == "n_1"

    respx.patch(f"{BASE_URL}/contacts/ct_1/notes/n_1").mock(
        return_value=httpx.Response(200, json={"id": "n_1"})
    )
    assert (await aclient.contacts.update_note("ct_1", "n_1", content="x")).id

    respx.delete(f"{BASE_URL}/contacts/ct_1/notes/n_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.contacts.delete_note("ct_1", "n_1")).id is None

    respx.get(f"{BASE_URL}/contacts/ct_1/activities").mock(
        return_value=httpx.Response(200, json=_page([{"id": "ac_1"}]))
    )
    assert [a.id async for a in aclient.contacts.list_activities("ct_1")] == ["ac_1"]

    respx.get(f"{BASE_URL}/contacts/ct_1/emails").mock(
        return_value=httpx.Response(200, json=_page([{"task_id": "t_1"}]))
    )
    got = [e.task_id async for e in aclient.contacts.list_emails("ct_1")]
    assert got == ["t_1"]

    respx.get(f"{BASE_URL}/contacts/ct_1/deals").mock(
        return_value=httpx.Response(200, json=[{"id": "d_1"}])
    )
    assert [d["id"] async for d in aclient.contacts.list_deals("ct_1")] == ["d_1"]

    respx.get(f"{BASE_URL}/contacts/ct_1/timeline").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tl_1"}]))
    )
    assert [t.id async for t in aclient.contacts.timeline("ct_1")] == ["tl_1"]

    respx.get(f"{BASE_URL}/contacts/ct_1/research").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "r_1"}]})
    )
    assert [r.id async for r in aclient.contacts.list_research("ct_1")] == ["r_1"]

    respx.post(f"{BASE_URL}/contacts/ct_1/research").mock(
        return_value=httpx.Response(200, json={"id": "r_1"})
    )
    assert (await aclient.contacts.research("ct_1")).id == "r_1"

    respx.post(f"{BASE_URL}/contacts/research/batch").mock(
        return_value=httpx.Response(200, json={"queued": 1})
    )
    assert (await aclient.contacts.research_batch(contact_ids=["a"])).queued == 1

    respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(200, json={"total_rows": 1})
    )
    preview = await aclient.contacts.import_preview(file=b"x", filename="a.csv")
    assert preview.total_rows == 1

    respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(200, json={"imported": 1})
    )
    committed = await aclient.contacts.import_commit(
        file=b"x", filename="a.csv", import_options={}
    )
    assert committed.imported == 1

    respx.post(f"{BASE_URL}/contacts/export").mock(
        return_value=httpx.Response(200, content=b"csv")
    )
    assert await aclient.contacts.export() == b"csv"


# ===========================================================================
# webhooks
# ===========================================================================
@respx.mock
def test_webhooks_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(200, json={"endpoints": [{"id": "wh_1"}]})
    )
    assert [w.id for w in client.webhooks.list()] == ["wh_1"]
    assert listing.called

    create = respx.post(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(201, json={"id": "wh_1", "secret": "whsec_1"})
    )
    made = client.webhooks.create(
        url="https://e/hook", event_types=["campaign.started"]
    )
    assert made.secret == "whsec_1"
    assert json.loads(_last(create).content) == {
        "url": "https://e/hook",
        "event_types": ["campaign.started"],
    }

    types = respx.get(f"{BASE_URL}/webhooks/event-types").mock(
        return_value=httpx.Response(
            200, json={"event_types": [{"type": "campaign.started"}]}
        )
    )
    assert [t.type for t in client.webhooks.event_types()] == ["campaign.started"]
    assert types.called

    deliveries = respx.get(f"{BASE_URL}/webhooks/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    got = list(client.webhooks.deliveries(status="failed", endpoint_id="wh_1"))
    assert [d.id for d in got] == ["dl_1"]
    assert _last(deliveries).url.params.get("endpoint_id") == "wh_1"

    redeliver = respx.post(f"{BASE_URL}/webhooks/deliveries/dl_1/redeliver").mock(
        return_value=httpx.Response(202, json={"status": "queued"})
    )
    assert client.webhooks.redeliver("dl_1").status == "queued"
    assert redeliver.called

    drops = respx.get(f"{BASE_URL}/webhooks/throttle-drops").mock(
        return_value=httpx.Response(200, json={"drops": [{"event_type": "e"}]})
    )
    assert [d.event_type for d in client.webhooks.throttle_drops()] == ["e"]
    assert drops.called

    rotate = respx.post(f"{BASE_URL}/webhooks/wh_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"secret": "whsec_2"})
    )
    assert client.webhooks.rotate_secret("wh_1").secret == "whsec_2"
    assert rotate.called

    verify = respx.post(f"{BASE_URL}/webhooks/wh_1/verify").mock(
        return_value=httpx.Response(202, json={"status": "challenge_sent"})
    )
    assert client.webhooks.verify("wh_1").status == "challenge_sent"
    assert verify.called

    per_endpoint = respx.get(f"{BASE_URL}/webhooks/wh_1/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_2"}]))
    )
    assert [d.id for d in client.webhooks.endpoint_deliveries("wh_1")] == ["dl_2"]
    assert per_endpoint.called

    update = respx.patch(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"id": "wh_1"})
    )
    client.webhooks.update("wh_1", enabled=False)
    assert json.loads(_last(update).content) == {"enabled": False}

    delete = respx.delete(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.webhooks.delete("wh_1").id is None
    assert delete.called


@pytest.mark.anyio
@respx.mock
async def test_webhooks_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(200, json={"endpoints": [{"id": "wh_1"}]})
    )
    assert [w.id async for w in aclient.webhooks.list()] == ["wh_1"]

    respx.post(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(201, json={"id": "wh_1"})
    )
    created = await aclient.webhooks.create(url="https://e/h", event_types=["a"])
    assert created.id == "wh_1"

    respx.get(f"{BASE_URL}/webhooks/event-types").mock(
        return_value=httpx.Response(200, json={"event_types": [{"type": "a"}]})
    )
    assert [t.type async for t in aclient.webhooks.event_types()] == ["a"]

    respx.get(f"{BASE_URL}/webhooks/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    assert [d.id async for d in aclient.webhooks.deliveries()] == ["dl_1"]

    respx.post(f"{BASE_URL}/webhooks/deliveries/dl_1/redeliver").mock(
        return_value=httpx.Response(202, json={"status": "queued"})
    )
    assert (await aclient.webhooks.redeliver("dl_1")).status == "queued"

    respx.get(f"{BASE_URL}/webhooks/throttle-drops").mock(
        return_value=httpx.Response(200, json={"drops": []})
    )
    assert [d async for d in aclient.webhooks.throttle_drops()] == []

    respx.patch(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"id": "wh_1"})
    )
    assert (await aclient.webhooks.update("wh_1", url="https://e/h2")).id == "wh_1"

    respx.post(f"{BASE_URL}/webhooks/wh_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"secret": "s"})
    )
    assert (await aclient.webhooks.rotate_secret("wh_1")).secret == "s"

    respx.post(f"{BASE_URL}/webhooks/wh_1/verify").mock(
        return_value=httpx.Response(202, json={"status": "challenge_sent"})
    )
    assert (await aclient.webhooks.verify("wh_1")).status == "challenge_sent"

    respx.get(f"{BASE_URL}/webhooks/wh_1/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_2"}]))
    )
    got = [d.id async for d in aclient.webhooks.endpoint_deliveries("wh_1")]
    assert got == ["dl_2"]

    respx.delete(f"{BASE_URL}/webhooks/wh_1").mock(return_value=httpx.Response(204))
    assert (await aclient.webhooks.delete("wh_1")).id is None


# ===========================================================================
# integrations
# ===========================================================================
@respx.mock
def test_integrations_sync_sweep(client: Warmbly) -> None:
    catalog = respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(200, json={"catalog": [{"provider": "hubspot"}]})
    )
    assert [e.provider for e in client.integrations.catalog()] == ["hubspot"]
    assert catalog.called

    conns = respx.get(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(200, json={"connections": [{"id": "cn_1"}]})
    )
    assert [c.id for c in client.integrations.list_connections()] == ["cn_1"]
    assert conns.called

    create = respx.post(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(201, json={"id": "cn_1"})
    )
    client.integrations.create_connection(
        provider="hubspot", label="Prod", config={"api_key": "k"}
    )
    assert json.loads(_last(create).content) == {
        "provider": "hubspot",
        "label": "Prod",
        "config": {"api_key": "k"},
    }

    detail = respx.get(f"{BASE_URL}/integrations/connections/cn_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "connection": {"id": "cn_1"},
                "events": [{"id": "ev_1"}],
                "runs": [{"id": "rn_1"}],
            },
        )
    )
    got = client.integrations.get_connection("cn_1")
    assert got.connection.id == "cn_1"
    assert [e.id for e in got.events] == ["ev_1"]
    assert [r.id for r in got.runs] == ["rn_1"]
    assert detail.called

    config = respx.patch(f"{BASE_URL}/integrations/connections/cn_1/config").mock(
        return_value=httpx.Response(200, json={"connection": {"id": "cn_1"}})
    )
    updated = client.integrations.update_connection_config(
        "cn_1", sync_direction="push"
    )
    assert updated.connection.id == "cn_1"
    assert json.loads(_last(config).content) == {"sync_direction": "push"}


@respx.mock
def test_integrations_sync_sub_sweep(client: Warmbly) -> None:
    events = respx.get(f"{BASE_URL}/integrations/connections/cn_1/events").mock(
        return_value=httpx.Response(200, json={"events": [{"id": "ev_1"}]})
    )
    assert [e.id for e in client.integrations.list_events("cn_1")] == ["ev_1"]
    assert events.called

    add = respx.post(f"{BASE_URL}/integrations/connections/cn_1/events").mock(
        return_value=httpx.Response(201, json={"id": "ev_1"})
    )
    client.integrations.add_event(
        "cn_1", event_type="campaign.reply_received", action="notify"
    )
    assert json.loads(_last(add).content) == {
        "event_type": "campaign.reply_received",
        "action": "notify",
    }

    drop = respx.delete(f"{BASE_URL}/integrations/connections/cn_1/events/ev_1").mock(
        return_value=httpx.Response(204)
    )
    client.integrations.remove_event("cn_1", "ev_1")
    assert drop.called

    maps = respx.get(f"{BASE_URL}/integrations/connections/cn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": [{"id": "fm_1"}]})
    )
    assert [m.id for m in client.integrations.get_field_mappings("cn_1").mappings] == [
        "fm_1"
    ]
    assert maps.called

    set_maps = respx.put(
        f"{BASE_URL}/integrations/connections/cn_1/field-mappings"
    ).mock(return_value=httpx.Response(200, json={"mappings": []}))
    client.integrations.set_field_mappings(
        "cn_1", object="contact", mappings=[{"warmbly_field": "email"}]
    )
    assert json.loads(_last(set_maps).content) == {
        "object": "contact",
        "mappings": [{"warmbly_field": "email"}],
    }

    runs = respx.get(f"{BASE_URL}/integrations/connections/cn_1/runs").mock(
        return_value=httpx.Response(200, json={"runs": [{"id": "rn_1"}]})
    )
    assert [r.id for r in client.integrations.runs("cn_1")] == ["rn_1"]
    assert runs.called

    secret = respx.get(f"{BASE_URL}/integrations/connections/cn_1/webhook-secret").mock(
        return_value=httpx.Response(
            200,
            json={"signing_secret": "s", "signature_header": "X-Warmbly-Signature"},
        )
    )
    assert client.integrations.connection_webhook_secret("cn_1").signing_secret == "s"
    assert secret.called

    test = respx.post(f"{BASE_URL}/integrations/connections/cn_1/test").mock(
        return_value=httpx.Response(200, json={"sent": 2})
    )
    assert client.integrations.test_connection("cn_1").sent == 2
    assert test.called

    push = respx.post(f"{BASE_URL}/integrations/connections/cn_1/push").mock(
        return_value=httpx.Response(200, json={"pushed": 1, "failed": 0})
    )
    assert client.integrations.push("cn_1", contact_ids=["ct_1"]).pushed == 1
    assert json.loads(_last(push).content) == {"contact_ids": ["ct_1"]}

    bookings = respx.get(f"{BASE_URL}/integrations/bookings").mock(
        return_value=httpx.Response(200, json={"bookings": [{"id": "bk_1"}]})
    )
    assert [b.id for b in client.integrations.bookings()] == ["bk_1"]
    assert bookings.called

    disconnect = respx.delete(f"{BASE_URL}/integrations/connections/cn_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.integrations.delete_connection("cn_1").id is None
    assert disconnect.called


@pytest.mark.anyio
@respx.mock
async def test_integrations_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(200, json={"catalog": [{"provider": "slack"}]})
    )
    assert [e.provider async for e in aclient.integrations.catalog()] == ["slack"]

    respx.get(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(200, json={"connections": [{"id": "cn_1"}]})
    )
    assert [c.id async for c in aclient.integrations.list_connections()] == ["cn_1"]

    respx.post(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(201, json={"id": "cn_1"})
    )
    assert (await aclient.integrations.create_connection(provider="slack")).id

    respx.get(f"{BASE_URL}/integrations/connections/cn_1").mock(
        return_value=httpx.Response(200, json={"connection": {"id": "cn_1"}})
    )
    assert (await aclient.integrations.get_connection("cn_1")).connection.id == "cn_1"

    respx.patch(f"{BASE_URL}/integrations/connections/cn_1/config").mock(
        return_value=httpx.Response(200, json={"connection": {"id": "cn_1"}})
    )
    cfg = await aclient.integrations.update_connection_config(
        "cn_1", sync_direction="a"
    )
    assert cfg.connection.id == "cn_1"

    respx.get(f"{BASE_URL}/integrations/connections/cn_1/events").mock(
        return_value=httpx.Response(200, json={"events": [{"id": "ev_1"}]})
    )
    assert [e.id async for e in aclient.integrations.list_events("cn_1")] == ["ev_1"]

    respx.post(f"{BASE_URL}/integrations/connections/cn_1/events").mock(
        return_value=httpx.Response(201, json={"id": "ev_1"})
    )
    assert (await aclient.integrations.add_event("cn_1", event_type="e")).id == "ev_1"

    respx.delete(f"{BASE_URL}/integrations/connections/cn_1/events/ev_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.integrations.remove_event("cn_1", "ev_1")).id is None

    respx.get(f"{BASE_URL}/integrations/connections/cn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": []})
    )
    assert (await aclient.integrations.get_field_mappings("cn_1")).mappings == []

    respx.put(f"{BASE_URL}/integrations/connections/cn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": []})
    )
    replaced = await aclient.integrations.set_field_mappings(
        "cn_1", object="contact", mappings=[]
    )
    assert replaced.mappings == []

    respx.get(f"{BASE_URL}/integrations/connections/cn_1/runs").mock(
        return_value=httpx.Response(200, json={"runs": [{"id": "rn_1"}]})
    )
    assert [r.id async for r in aclient.integrations.runs("cn_1")] == ["rn_1"]

    respx.get(f"{BASE_URL}/integrations/connections/cn_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"signing_secret": "s"})
    )
    secret = await aclient.integrations.connection_webhook_secret("cn_1")
    assert secret.signing_secret == "s"

    respx.post(f"{BASE_URL}/integrations/connections/cn_1/test").mock(
        return_value=httpx.Response(200, json={"sent": 0})
    )
    assert (await aclient.integrations.test_connection("cn_1")).sent == 0

    respx.post(f"{BASE_URL}/integrations/connections/cn_1/push").mock(
        return_value=httpx.Response(200, json={"pushed": 0})
    )
    assert (await aclient.integrations.push("cn_1", contact_ids=[])).pushed == 0

    respx.get(f"{BASE_URL}/integrations/bookings").mock(
        return_value=httpx.Response(200, json={"bookings": []})
    )
    assert [b async for b in aclient.integrations.bookings()] == []

    respx.delete(f"{BASE_URL}/integrations/connections/cn_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.integrations.delete_connection("cn_1")).id is None


# ===========================================================================
# automations
# ===========================================================================
@respx.mock
def test_automations_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(200, json={"automations": [{"id": "au_1"}]})
    )
    assert [a.id for a in client.automations.list()] == ["au_1"]
    assert listing.called

    create = respx.post(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(201, json={"automation": {"id": "au_1"}})
    )
    client.automations.create(
        name="Notify", trigger_event="campaign.reply_received", graph={"nodes": []}
    )
    assert json.loads(_last(create).content) == {
        "name": "Notify",
        "trigger_event": "campaign.reply_received",
        "graph": {"nodes": []},
    }

    get = respx.get(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": {"id": "au_1"}})
    )
    assert client.automations.retrieve("au_1").automation["id"] == "au_1"
    assert get.called

    update = respx.patch(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": {"id": "au_1"}})
    )
    client.automations.update("au_1", enabled=False)
    assert json.loads(_last(update).content) == {"enabled": False}

    layout = respx.patch(f"{BASE_URL}/automations/au_1/layout").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert client.automations.set_layout(
        "au_1", positions=[{"id": "n", "x": 0, "y": 0}]
    ).ok
    assert layout.called

    test = respx.post(f"{BASE_URL}/automations/au_1/test").mock(
        return_value=httpx.Response(200, json={"trace": [{"node_id": "n"}]})
    )
    assert client.automations.test("au_1", data={"a": 1}).trace[0]["node_id"] == "n"
    assert json.loads(_last(test).content) == {"data": {"a": 1}}

    runs = respx.get(f"{BASE_URL}/automations/au_1/runs").mock(
        return_value=httpx.Response(200, json={"runs": [{"id": "rn_1"}]})
    )
    assert [r.id for r in client.automations.runs("au_1", limit=5)] == ["rn_1"]
    assert _last(runs).url.params.get("limit") == "5"

    delete = respx.delete(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.automations.delete("au_1").deleted is True
    assert delete.called


@pytest.mark.anyio
@respx.mock
async def test_automations_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(200, json={"automations": [{"id": "au_1"}]})
    )
    assert [a.id async for a in aclient.automations.list()] == ["au_1"]

    respx.post(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(201, json={"automation": {"id": "au_1"}})
    )
    created = await aclient.automations.create(
        name="n", trigger_event="e", graph={}, enabled=True, filter={"x": 1}
    )
    assert created.automation["id"] == "au_1"

    respx.get(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": {"id": "au_1"}})
    )
    assert (await aclient.automations.retrieve("au_1")).automation["id"] == "au_1"

    respx.patch(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": {}})
    )
    assert (await aclient.automations.update("au_1", name="x")).automation == {}

    respx.patch(f"{BASE_URL}/automations/au_1/layout").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await aclient.automations.set_layout("au_1", positions=[])).ok

    respx.post(f"{BASE_URL}/automations/au_1/test").mock(
        return_value=httpx.Response(200, json={"trace": []})
    )
    assert (await aclient.automations.test("au_1", skip_node_ids=["n"])).trace == []

    respx.get(f"{BASE_URL}/automations/au_1/runs").mock(
        return_value=httpx.Response(200, json={"runs": []})
    )
    assert [r async for r in aclient.automations.runs("au_1")] == []

    respx.delete(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.automations.delete("au_1")).deleted is True


# ===========================================================================
# crm
# ===========================================================================
@respx.mock
def test_crm_sync_pipelines(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(200, json=[{"id": "pl_1"}])
    )
    # This endpoint answers with a bare array.
    assert [p.id for p in client.crm.list_pipelines()] == ["pl_1"]
    assert listing.called

    create = respx.post(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(201, json={"id": "pl_1"})
    )
    client.crm.create_pipeline(name="Sales", stages=[{"name": "New", "color": "#fff"}])
    assert json.loads(_last(create).content) == {
        "name": "Sales",
        "stages": [{"name": "New", "color": "#fff"}],
    }

    get = respx.get(f"{BASE_URL}/crm/pipelines/pl_1").mock(
        return_value=httpx.Response(200, json={"id": "pl_1"})
    )
    assert client.crm.retrieve_pipeline("pl_1").id == "pl_1"
    assert get.called

    update = respx.patch(f"{BASE_URL}/crm/pipelines/pl_1").mock(
        return_value=httpx.Response(200, json={"id": "pl_1"})
    )
    client.crm.update_pipeline("pl_1", name="New")
    assert json.loads(_last(update).content) == {"name": "New"}

    stage = respx.post(f"{BASE_URL}/crm/pipelines/pl_1/stages").mock(
        return_value=httpx.Response(201, json={"id": "sg_1"})
    )
    client.crm.create_stage("pl_1", name="Won", color="#0f0")
    assert json.loads(_last(stage).content) == {"name": "Won", "color": "#0f0"}

    edit_stage = respx.patch(f"{BASE_URL}/crm/pipelines/pl_1/stages/sg_1").mock(
        return_value=httpx.Response(200, json={"id": "sg_1"})
    )
    client.crm.update_stage("pl_1", "sg_1", color="#00f")
    assert json.loads(_last(edit_stage).content) == {"color": "#00f"}

    drop_stage = respx.delete(f"{BASE_URL}/crm/pipelines/pl_1/stages/sg_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.crm.delete_stage("pl_1", "sg_1").id is None
    assert drop_stage.called

    drop = respx.delete(f"{BASE_URL}/crm/pipelines/pl_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.crm.delete_pipeline("pl_1").id is None
    assert drop.called


@respx.mock
def test_crm_sync_deals(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    assert [d.id for d in client.crm.list_deals(status="open")] == ["dl_1"]
    assert _last(listing).url.params.get("status") == "open"

    create = respx.post(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(201, json={"id": "dl_1"})
    )
    client.crm.create_deal(
        name="Acme", pipeline_id="pl_1", stage_id="sg_1", value=1000.0, currency="USD"
    )
    assert json.loads(_last(create).content) == {
        "name": "Acme",
        "pipeline_id": "pl_1",
        "stage_id": "sg_1",
        "value": 1000.0,
        "currency": "USD",
    }

    update = respx.patch(f"{BASE_URL}/crm/deals/dl_1").mock(
        return_value=httpx.Response(200, json={"id": "dl_1"})
    )
    client.crm.update_deal("dl_1", stage_id="sg_2", status="won")
    assert json.loads(_last(update).content) == {"stage_id": "sg_2", "status": "won"}

    search = respx.post(f"{BASE_URL}/crm/deals/search").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "dl_1"}]})
    )
    page = client.crm.search_deals(statuses=["open"], min_value=100.0, limit=50)
    assert [d.id for d in page.data] == ["dl_1"]
    assert json.loads(_last(search).content) == {
        "statuses": ["open"],
        "min_value": 100.0,
    }
    assert _last(search).url.params.get("limit") == "50"

    summary = respx.post(f"{BASE_URL}/crm/deals/summary").mock(
        return_value=httpx.Response(200, json={"total": 3, "open_count": 2})
    )
    assert client.crm.deals_summary(statuses=["open"]).open_count == 2
    assert summary.called

    get = respx.get(f"{BASE_URL}/crm/deals/dl_1").mock(
        return_value=httpx.Response(200, json={"id": "dl_1"})
    )
    assert client.crm.retrieve_deal("dl_1").id == "dl_1"
    assert get.called

    drop = respx.delete(f"{BASE_URL}/crm/deals/dl_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.crm.delete_deal("dl_1").id is None
    assert drop.called


@respx.mock
def test_crm_sync_tasks(client: Warmbly) -> None:
    types = respx.get(f"{BASE_URL}/crm/task-types").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tt_1"}]})
    )
    assert [t.id for t in client.crm.list_task_types()] == ["tt_1"]
    assert types.called

    make_type = respx.post(f"{BASE_URL}/crm/task-types").mock(
        return_value=httpx.Response(201, json={"id": "tt_1"})
    )
    client.crm.create_task_type(name="Call", color="#8b5cf6")
    assert json.loads(_last(make_type).content) == {"name": "Call", "color": "#8b5cf6"}

    edit_type = respx.patch(f"{BASE_URL}/crm/task-types/tt_1").mock(
        return_value=httpx.Response(200, json={"id": "tt_1"})
    )
    client.crm.update_task_type("tt_1", position=2)
    assert json.loads(_last(edit_type).content) == {"position": 2}

    drop_type = respx.delete(f"{BASE_URL}/crm/task-types/tt_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.crm.delete_task_type("tt_1").id is None
    assert drop_type.called

    listing = respx.get(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tk_1"}]))
    )
    assert [t.id for t in client.crm.list_tasks(contact_id="ct_1")] == ["tk_1"]
    assert _last(listing).url.params.get("contact_id") == "ct_1"

    create = respx.post(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(201, json={"id": "tk_1"})
    )
    client.crm.create_task(
        title="Call back", due_date="2026-01-01T00:00:00Z", type="Call"
    )
    assert json.loads(_last(create).content) == {
        "title": "Call back",
        "due_date": "2026-01-01T00:00:00Z",
        "type": "Call",
    }

    get = respx.get(f"{BASE_URL}/crm/tasks/tk_1").mock(
        return_value=httpx.Response(200, json={"id": "tk_1"})
    )
    assert client.crm.retrieve_task("tk_1").id == "tk_1"
    assert get.called

    update = respx.patch(f"{BASE_URL}/crm/tasks/tk_1").mock(
        return_value=httpx.Response(200, json={"id": "tk_1"})
    )
    client.crm.update_task("tk_1", status="completed")
    assert json.loads(_last(update).content) == {"status": "completed"}

    search = respx.post(f"{BASE_URL}/crm/tasks/search").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert client.crm.search_tasks(overdue=True).data == []
    assert json.loads(_last(search).content) == {"overdue": True}

    summary = respx.post(f"{BASE_URL}/crm/tasks/summary").mock(
        return_value=httpx.Response(200, json={"overdue_count": 4})
    )
    assert client.crm.tasks_summary(overdue=True).overdue_count == 4
    assert summary.called

    drop = respx.delete(f"{BASE_URL}/crm/tasks/tk_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.crm.delete_task("tk_1").id is None
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_crm_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(200, json=[{"id": "pl_1"}])
    )
    assert [p.id async for p in aclient.crm.list_pipelines()] == ["pl_1"]

    respx.post(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(201, json={"id": "pl_1"})
    )
    assert (await aclient.crm.create_pipeline(name="S")).id == "pl_1"

    respx.get(f"{BASE_URL}/crm/pipelines/pl_1").mock(
        return_value=httpx.Response(200, json={"id": "pl_1"})
    )
    assert (await aclient.crm.retrieve_pipeline("pl_1")).id == "pl_1"

    respx.patch(f"{BASE_URL}/crm/pipelines/pl_1").mock(
        return_value=httpx.Response(200, json={"id": "pl_1"})
    )
    assert (await aclient.crm.update_pipeline("pl_1", name="n")).id == "pl_1"

    respx.post(f"{BASE_URL}/crm/pipelines/pl_1/stages").mock(
        return_value=httpx.Response(201, json={"id": "sg_1"})
    )
    assert (await aclient.crm.create_stage("pl_1", name="N", color="#f")).id == "sg_1"

    respx.patch(f"{BASE_URL}/crm/pipelines/pl_1/stages/sg_1").mock(
        return_value=httpx.Response(200, json={"id": "sg_1"})
    )
    assert (await aclient.crm.update_stage("pl_1", "sg_1", name="W")).id == "sg_1"

    respx.delete(f"{BASE_URL}/crm/pipelines/pl_1/stages/sg_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.crm.delete_stage("pl_1", "sg_1")).id is None

    respx.delete(f"{BASE_URL}/crm/pipelines/pl_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.crm.delete_pipeline("pl_1")).id is None


@pytest.mark.anyio
@respx.mock
async def test_crm_async_deals_and_tasks(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    assert [d.id async for d in aclient.crm.list_deals()] == ["dl_1"]

    respx.post(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(201, json={"id": "dl_1"})
    )
    made = await aclient.crm.create_deal(name="A", pipeline_id="p", stage_id="s")
    assert made.id == "dl_1"

    respx.get(f"{BASE_URL}/crm/deals/dl_1").mock(
        return_value=httpx.Response(200, json={"id": "dl_1"})
    )
    assert (await aclient.crm.retrieve_deal("dl_1")).id == "dl_1"

    respx.patch(f"{BASE_URL}/crm/deals/dl_1").mock(
        return_value=httpx.Response(200, json={"id": "dl_1"})
    )
    assert (await aclient.crm.update_deal("dl_1", value=1.0)).id == "dl_1"

    respx.post(f"{BASE_URL}/crm/deals/search").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.crm.search_deals(query="a")).data == []

    respx.post(f"{BASE_URL}/crm/deals/summary").mock(
        return_value=httpx.Response(200, json={"total": 0})
    )
    assert (await aclient.crm.deals_summary()).total == 0

    respx.delete(f"{BASE_URL}/crm/deals/dl_1").mock(return_value=httpx.Response(204))
    assert (await aclient.crm.delete_deal("dl_1")).id is None

    respx.get(f"{BASE_URL}/crm/task-types").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tt_1"}]})
    )
    assert [t.id async for t in aclient.crm.list_task_types()] == ["tt_1"]

    respx.post(f"{BASE_URL}/crm/task-types").mock(
        return_value=httpx.Response(201, json={"id": "tt_1"})
    )
    assert (await aclient.crm.create_task_type(name="Call")).id == "tt_1"

    respx.patch(f"{BASE_URL}/crm/task-types/tt_1").mock(
        return_value=httpx.Response(200, json={"id": "tt_1"})
    )
    assert (await aclient.crm.update_task_type("tt_1", name="C")).id == "tt_1"

    respx.delete(f"{BASE_URL}/crm/task-types/tt_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.crm.delete_task_type("tt_1")).id is None

    respx.get(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tk_1"}]))
    )
    assert [t.id async for t in aclient.crm.list_tasks()] == ["tk_1"]

    respx.post(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(201, json={"id": "tk_1"})
    )
    assert (await aclient.crm.create_task(title="T")).id == "tk_1"

    respx.get(f"{BASE_URL}/crm/tasks/tk_1").mock(
        return_value=httpx.Response(200, json={"id": "tk_1"})
    )
    assert (await aclient.crm.retrieve_task("tk_1")).id == "tk_1"

    respx.patch(f"{BASE_URL}/crm/tasks/tk_1").mock(
        return_value=httpx.Response(200, json={"id": "tk_1"})
    )
    assert (await aclient.crm.update_task("tk_1", priority="high")).id == "tk_1"

    respx.post(f"{BASE_URL}/crm/tasks/search").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.crm.search_tasks(types=["Call"])).data == []

    respx.post(f"{BASE_URL}/crm/tasks/summary").mock(
        return_value=httpx.Response(200, json={"total": 0})
    )
    assert (await aclient.crm.tasks_summary()).total == 0

    respx.delete(f"{BASE_URL}/crm/tasks/tk_1").mock(return_value=httpx.Response(204))
    assert (await aclient.crm.delete_task("tk_1")).id is None


# ===========================================================================
# templates
# ===========================================================================
@respx.mock
def test_templates_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tpl_1"}]})
    )
    assert [t.id for t in client.templates.list(q="welcome")] == ["tpl_1"]
    assert _last(listing).url.params.get("q") == "welcome"

    dup = respx.post(f"{BASE_URL}/templates/tpl_1/duplicate").mock(
        return_value=httpx.Response(200, json={"id": "tpl_2"})
    )
    assert client.templates.duplicate("tpl_1").id == "tpl_2"
    assert dup.called

    render = respx.post(f"{BASE_URL}/templates/tpl_1/render").mock(
        return_value=httpx.Response(200, json={"subject": "Hi Alex"})
    )
    out = client.templates.render("tpl_1", variables={"FirstName": "Alex"})
    assert out.subject == "Hi Alex"
    assert json.loads(_last(render).content) == {"variables": {"FirstName": "Alex"}}

    reorder = respx.patch(f"{BASE_URL}/templates/reorder").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tpl_1"}]})
    )
    assert [t.id for t in client.templates.reorder(ids=["tpl_1"]).data] == ["tpl_1"]
    assert json.loads(_last(reorder).content) == {"ids": ["tpl_1"]}

    score = respx.post(f"{BASE_URL}/templates/score").mock(
        return_value=httpx.Response(200, json={"score": 82})
    )
    assert client.templates.score(subject="Hi", body_html="<p>x</p>").score == 82
    assert json.loads(_last(score).content) == {
        "subject": "Hi",
        "body_html": "<p>x</p>",
    }

    update = respx.patch(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    client.templates.update("tpl_1", body_plain="hi")
    assert json.loads(_last(update).content) == {"body_plain": "hi"}

    get = respx.get(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    assert client.templates.retrieve("tpl_1").id == "tpl_1"
    assert get.called

    drop = respx.delete(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.templates.delete("tpl_1").id is None
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_templates_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tpl_1"}]})
    )
    assert [t.id async for t in aclient.templates.list()] == ["tpl_1"]

    respx.post(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    made = await aclient.templates.create(name="W", body_html="<p>x</p>")
    assert made.id == "tpl_1"

    respx.get(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    assert (await aclient.templates.retrieve("tpl_1")).id == "tpl_1"

    respx.patch(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    assert (await aclient.templates.update("tpl_1", subject="s")).id == "tpl_1"

    respx.post(f"{BASE_URL}/templates/tpl_1/duplicate").mock(
        return_value=httpx.Response(200, json={"id": "tpl_2"})
    )
    assert (await aclient.templates.duplicate("tpl_1")).id == "tpl_2"

    respx.post(f"{BASE_URL}/templates/tpl_1/render").mock(
        return_value=httpx.Response(200, json={"subject": "s"})
    )
    assert (await aclient.templates.render("tpl_1")).subject == "s"

    respx.patch(f"{BASE_URL}/templates/reorder").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.templates.reorder(ids=[])).data == []

    respx.post(f"{BASE_URL}/templates/score").mock(
        return_value=httpx.Response(200, json={"score": 1})
    )
    assert (await aclient.templates.score(subject="s")).score == 1

    respx.delete(f"{BASE_URL}/templates/tpl_1").mock(return_value=httpx.Response(204))
    assert (await aclient.templates.delete("tpl_1")).id is None


# ===========================================================================
# teams
# ===========================================================================
@respx.mock
def test_teams_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tm_1"}]})
    )
    assert [t.id for t in client.teams.list()] == ["tm_1"]
    assert listing.called

    create = respx.post(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(201, json={"id": "tm_1"})
    )
    client.teams.create(name="Sales", color="#0f0")
    assert json.loads(_last(create).content) == {"name": "Sales", "color": "#0f0"}

    get = respx.get(f"{BASE_URL}/teams/tm_1").mock(
        return_value=httpx.Response(200, json={"id": "tm_1", "members": []})
    )
    assert client.teams.retrieve("tm_1").members == []
    assert get.called

    update = respx.patch(f"{BASE_URL}/teams/tm_1").mock(
        return_value=httpx.Response(200, json={"id": "tm_1"})
    )
    client.teams.update("tm_1", description="d")
    assert json.loads(_last(update).content) == {"description": "d"}

    add = respx.post(f"{BASE_URL}/teams/tm_1/members").mock(
        return_value=httpx.Response(200, json={"id": "tm_1"})
    )
    client.teams.add_member("tm_1", user_id="u_1")
    assert json.loads(_last(add).content) == {"user_id": "u_1"}

    remove = respx.delete(f"{BASE_URL}/teams/tm_1/members/u_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.teams.remove_member("tm_1", "u_1").user_id is None
    assert remove.called

    drop = respx.delete(f"{BASE_URL}/teams/tm_1").mock(return_value=httpx.Response(204))
    assert client.teams.delete("tm_1").id is None
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_teams_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "tm_1"}]})
    )
    assert [t.id async for t in aclient.teams.list()] == ["tm_1"]

    respx.post(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(201, json={"id": "tm_1"})
    )
    assert (await aclient.teams.create(name="S", description="d")).id == "tm_1"

    respx.get(f"{BASE_URL}/teams/tm_1").mock(
        return_value=httpx.Response(200, json={"id": "tm_1"})
    )
    assert (await aclient.teams.retrieve("tm_1")).id == "tm_1"

    respx.patch(f"{BASE_URL}/teams/tm_1").mock(
        return_value=httpx.Response(200, json={"id": "tm_1"})
    )
    assert (await aclient.teams.update("tm_1", name="N")).id == "tm_1"

    respx.post(f"{BASE_URL}/teams/tm_1/members").mock(
        return_value=httpx.Response(200, json={"id": "tm_1"})
    )
    assert (await aclient.teams.add_member("tm_1", user_id="u_1")).id == "tm_1"

    respx.delete(f"{BASE_URL}/teams/tm_1/members/u_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.teams.remove_member("tm_1", "u_1")).user_id is None

    respx.delete(f"{BASE_URL}/teams/tm_1").mock(return_value=httpx.Response(204))
    assert (await aclient.teams.delete("tm_1")).id is None


# ===========================================================================
# plans
# ===========================================================================
@respx.mock
def test_plans_sync(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(200, json={"plans": [{"id": "pro"}]})
    )
    assert [p.id for p in client.plans.list()] == ["pro"]
    assert _last(r).url.path == "/v1/plans"


@pytest.mark.anyio
@respx.mock
async def test_plans_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(200, json={"plans": [{"id": "pro"}]})
    )
    page = await aclient.plans.list()
    assert [p.id for p in page.data] == ["pro"]


# ===========================================================================
# unibox
# ===========================================================================
@respx.mock
def test_unibox_sync_reads(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([{"id": "m_1"}]))
    )
    got = list(
        client.unibox.list(
            email_ids=["em_1", "em_2"],
            category_ids=["cat_1"],
            unseen=True,
            awaiting_reply=True,
            agent_drafts=True,
            uncategorized=True,
            direction="received",
            snoozed="exclude",
        )
    )
    assert [m.id for m in got] == ["m_1"]
    params = _last(listing).url.params
    assert params.get("email_ids") == "em_1,em_2"
    assert params.get("category_ids") == "cat_1"
    assert params.get("unseen") == "true"
    assert params.get("awaiting_reply") == "true"
    assert params.get("agent_drafts") == "true"
    assert params.get("uncategorized") == "true"
    assert params.get("snoozed") == "exclude"

    # Falsy booleans are omitted rather than sent as "false".
    plain = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([]))
    )
    list(client.unibox.list(unseen=False))
    assert "unseen" not in _last(plain).url.params

    get = respx.get(f"{BASE_URL}/unibox/m_1").mock(
        return_value=httpx.Response(200, json={"id": "m_1"})
    )
    assert client.unibox.retrieve("m_1").id == "m_1"
    assert get.called

    thread = respx.get(f"{BASE_URL}/unibox/thread").mock(
        return_value=httpx.Response(200, json=_page([{"id": "m_1"}]))
    )
    assert [m.id for m in client.unibox.thread(thread_id="th_1")] == ["m_1"]
    assert _last(thread).url.params.get("thread_id") == "th_1"

    count = respx.get(f"{BASE_URL}/unibox/count").mock(
        return_value=httpx.Response(200, json={"count": 7})
    )
    assert client.unibox.count(email_id="em_1").count == 7
    assert count.called

    overview = respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json={"unread": 3})
    )
    assert client.unibox.overview().unread == 3
    assert overview.called


@respx.mock
def test_unibox_sync_writes(client: Warmbly) -> None:
    labels = respx.get(f"{BASE_URL}/unibox/thread/labels").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "cat_1"}]})
    )
    assert client.unibox.list_thread_labels(thread_id="th_1").data[0]["id"] == "cat_1"
    assert _last(labels).url.params.get("thread_id") == "th_1"

    set_labels = respx.put(f"{BASE_URL}/unibox/thread/labels").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    client.unibox.set_thread_labels(thread_id="th_1", category_ids=["cat_1"])
    assert json.loads(_last(set_labels).content) == {
        "thread_id": "th_1",
        "category_ids": ["cat_1"],
    }

    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"email_ids": ["m_1"], "seen": True})
    )
    assert client.unibox.mark_seen(email_ids=["m_1"]).seen is True
    assert json.loads(_last(seen).content) == {"email_ids": ["m_1"], "seen": True}

    reply = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "tk_1"})
    )
    client.unibox.reply(
        email_account_id="em_1",
        to=["a@e.com"],
        subject="Re: hi",
        body_html="<p>y</p>",
        thread_id="th_1",
        send_mode="scheduled",
        scheduled_at="2026-01-01T00:00:00Z",
    )
    assert json.loads(_last(reply).content) == {
        "email_account_id": "em_1",
        "to": ["a@e.com"],
        "subject": "Re: hi",
        "body_html": "<p>y</p>",
        "thread_id": "th_1",
        "send_mode": "scheduled",
        "scheduled_at": "2026-01-01T00:00:00Z",
    }

    draft = respx.post(f"{BASE_URL}/unibox/reply/draft").mock(
        return_value=httpx.Response(200, json={"text": "hi", "credits_charged": 1})
    )
    assert client.unibox.draft_reply(thread_id="th_1").text == "hi"
    assert draft.called

    candidates = respx.get(f"{BASE_URL}/unibox/compose/candidates").mock(
        return_value=httpx.Response(
            200, json={"accounts": [], "recommended_account_id": "em_1"}
        )
    )
    got = client.unibox.compose_candidates(to="a@e.com")
    assert got.recommended_account_id == "em_1"
    assert _last(candidates).url.params.get("to") == "a@e.com"

    compose = respx.post(f"{BASE_URL}/unibox/compose").mock(
        return_value=httpx.Response(200, json={"task_id": "tk_1", "auto": True})
    )
    assert client.unibox.compose(to=["a@e.com"], subject="Hi").auto is True
    assert json.loads(_last(compose).content) == {
        "to": ["a@e.com"],
        "subject": "Hi",
    }

    compose_draft = respx.post(f"{BASE_URL}/unibox/compose/draft").mock(
        return_value=httpx.Response(200, json={"question": "Who is this for?"})
    )
    out = client.unibox.draft_compose(to="a@e.com", instruction="short")
    assert out.question == "Who is this for?"
    assert compose_draft.called


@respx.mock
def test_unibox_sync_drafts_and_queues(client: Warmbly) -> None:
    drafts = respx.get(f"{BASE_URL}/unibox/drafts").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "dr_1"}]})
    )
    assert [d.id for d in client.unibox.list_drafts()] == ["dr_1"]
    assert drafts.called

    save = respx.put(f"{BASE_URL}/unibox/drafts/dr_1").mock(
        return_value=httpx.Response(200, json={"id": "dr_1"})
    )
    client.unibox.save_draft("dr_1", to=["a@e.com"], subject="Hi", body="x")
    assert json.loads(_last(save).content) == {
        "to": ["a@e.com"],
        "subject": "Hi",
        "body": "x",
    }

    drop = respx.delete(f"{BASE_URL}/unibox/drafts/dr_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.unibox.delete_draft("dr_1").deleted is True
    assert drop.called

    agent = respx.get(f"{BASE_URL}/unibox/agent-drafts").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "ad_1"}]})
    )
    assert [d.id for d in client.unibox.list_agent_drafts()] == ["ad_1"]
    assert agent.called

    approve = respx.post(f"{BASE_URL}/unibox/agent-drafts/ad_1/approve").mock(
        return_value=httpx.Response(200, json={"task_id": "tk_1"})
    )
    client.unibox.approve_agent_draft("ad_1", body="edited")
    assert json.loads(_last(approve).content) == {"body": "edited"}

    discard = respx.post(f"{BASE_URL}/unibox/agent-drafts/ad_1/discard").mock(
        return_value=httpx.Response(200, json={"status": "discarded"})
    )
    assert client.unibox.discard_agent_draft("ad_1").status == "discarded"
    assert discard.called

    snoozes = respx.get(f"{BASE_URL}/unibox/snoozes").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "sn_1"}]})
    )
    assert [s.id for s in client.unibox.list_snoozes()] == ["sn_1"]
    assert snoozes.called

    snooze = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json={"id": "sn_1"})
    )
    client.unibox.snooze(thread_id="th_1", snoozed_until="2026-01-01T00:00:00Z")
    assert json.loads(_last(snooze).content) == {
        "thread_id": "th_1",
        "snoozed_until": "2026-01-01T00:00:00Z",
    }

    unsnooze = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    assert client.unibox.unsnooze(thread_id="th_1").thread_id is None
    assert _last(unsnooze).url.params.get("thread_id") == "th_1"

    scheduled = respx.get(f"{BASE_URL}/unibox/scheduled").mock(
        return_value=httpx.Response(200, json={"data": [{"task_id": "tk_1"}]})
    )
    got = list(client.unibox.list_scheduled(thread_id="th_1"))
    assert [s.task_id for s in got] == ["tk_1"]
    assert _last(scheduled).url.params.get("thread_id") == "th_1"

    cancel = respx.delete(f"{BASE_URL}/unibox/scheduled/tk_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.unibox.cancel_scheduled("tk_1").task_id is None
    assert cancel.called


@pytest.mark.anyio
@respx.mock
async def test_unibox_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([{"id": "m_1"}]))
    )
    assert [m.id async for m in aclient.unibox.list(subject="hi")] == ["m_1"]

    respx.get(f"{BASE_URL}/unibox/m_1").mock(
        return_value=httpx.Response(200, json={"id": "m_1"})
    )
    assert (await aclient.unibox.retrieve("m_1")).id == "m_1"

    respx.get(f"{BASE_URL}/unibox/thread").mock(
        return_value=httpx.Response(200, json=_page([{"id": "m_1"}]))
    )
    assert [m.id async for m in aclient.unibox.thread(email_id="em_1")] == ["m_1"]

    respx.get(f"{BASE_URL}/unibox/count").mock(
        return_value=httpx.Response(200, json={"count": 1})
    )
    assert (await aclient.unibox.count()).count == 1

    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json={"unread": 1})
    )
    assert (await aclient.unibox.overview()).unread == 1

    respx.get(f"{BASE_URL}/unibox/thread/labels").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert (await aclient.unibox.list_thread_labels(thread_id="th_1")).data == []

    respx.put(f"{BASE_URL}/unibox/thread/labels").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    set_labels = await aclient.unibox.set_thread_labels(
        thread_id="th_1", category_ids=[]
    )
    assert set_labels.data == []

    respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"seen": False})
    )
    assert (await aclient.unibox.mark_seen(email_ids=["m"], seen=False)).seen is False


@pytest.mark.anyio
@respx.mock
async def test_unibox_async_writes(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "tk_1"})
    )
    replied = await aclient.unibox.reply(
        email_account_id="em_1",
        to=["a@e.com"],
        subject="s",
        cc=["c@e.com"],
        bcc=["b@e.com"],
        in_reply_to=["<m@e>"],
        body_plain="p",
    )
    assert replied.task_id == "tk_1"

    respx.post(f"{BASE_URL}/unibox/reply/draft").mock(
        return_value=httpx.Response(200, json={"text": "t"})
    )
    assert (await aclient.unibox.draft_reply(thread_id="th_1")).text == "t"

    respx.get(f"{BASE_URL}/unibox/compose/candidates").mock(
        return_value=httpx.Response(200, json={"accounts": []})
    )
    assert (await aclient.unibox.compose_candidates()).accounts == []

    respx.post(f"{BASE_URL}/unibox/compose").mock(
        return_value=httpx.Response(200, json={"task_id": "tk_1"})
    )
    composed = await aclient.unibox.compose(
        to=["a@e.com"],
        subject="s",
        from_tag_id="tg_1",
        cc=[],
        bcc=[],
        body_html="<p>x</p>",
        send_mode="instant",
    )
    assert composed.task_id == "tk_1"

    respx.post(f"{BASE_URL}/unibox/compose/draft").mock(
        return_value=httpx.Response(200, json={"text": "t"})
    )
    assert (await aclient.unibox.draft_compose(subject="s")).text == "t"

    respx.get(f"{BASE_URL}/unibox/drafts").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "dr_1"}]})
    )
    assert [d.id async for d in aclient.unibox.list_drafts()] == ["dr_1"]

    respx.put(f"{BASE_URL}/unibox/drafts/dr_1").mock(
        return_value=httpx.Response(200, json={"id": "dr_1"})
    )
    saved = await aclient.unibox.save_draft(
        "dr_1", email_account_id="em_1", cc=["c@e.com"], bcc=[]
    )
    assert saved.id == "dr_1"

    respx.delete(f"{BASE_URL}/unibox/drafts/dr_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.unibox.delete_draft("dr_1")).deleted is True

    respx.get(f"{BASE_URL}/unibox/agent-drafts").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert [d async for d in aclient.unibox.list_agent_drafts()] == []

    respx.post(f"{BASE_URL}/unibox/agent-drafts/ad_1/approve").mock(
        return_value=httpx.Response(200, json={"task_id": "tk_1"})
    )
    assert (await aclient.unibox.approve_agent_draft("ad_1")).task_id == "tk_1"

    respx.post(f"{BASE_URL}/unibox/agent-drafts/ad_1/discard").mock(
        return_value=httpx.Response(200, json={"status": "discarded"})
    )
    assert (await aclient.unibox.discard_agent_draft("ad_1")).status == "discarded"

    respx.get(f"{BASE_URL}/unibox/snoozes").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert [s async for s in aclient.unibox.list_snoozes()] == []

    respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json={"id": "sn_1"})
    )
    snoozed = await aclient.unibox.snooze(thread_id="th_1", snoozed_until="t")
    assert snoozed.id == "sn_1"

    respx.delete(f"{BASE_URL}/unibox/snooze").mock(return_value=httpx.Response(204))
    assert (await aclient.unibox.unsnooze(thread_id="th_1")).thread_id is None

    respx.get(f"{BASE_URL}/unibox/scheduled").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert [s async for s in aclient.unibox.list_scheduled()] == []

    respx.delete(f"{BASE_URL}/unibox/scheduled/tk_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.unibox.cancel_scheduled("tk_1")).task_id is None


# ===========================================================================
# advisor
# ===========================================================================
@respx.mock
def test_advisor_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/advisor/recommendations").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "f_1"}]})
    )
    got = list(client.advisor.list(surface="mailbox", entity_id="em_1"))
    assert [f.id for f in got] == ["f_1"]
    assert _last(listing).url.params.get("surface") == "mailbox"

    summary = respx.get(f"{BASE_URL}/advisor/summary").mock(
        return_value=httpx.Response(200, json={"score": 88, "critical": 1})
    )
    assert client.advisor.summary().score == 88
    assert summary.called

    refresh = respx.post(f"{BASE_URL}/advisor/refresh").mock(
        return_value=httpx.Response(200, json={"score": 90})
    )
    assert client.advisor.refresh().score == 90
    assert refresh.called

    settings = respx.get(f"{BASE_URL}/advisor/settings").mock(
        return_value=httpx.Response(200, json={"enabled": True, "autopilot": False})
    )
    assert client.advisor.settings().autopilot is False
    assert settings.called

    apply = respx.post(f"{BASE_URL}/advisor/recommendations/f_1/apply").mock(
        return_value=httpx.Response(200, json={"id": "f_1", "status": "applied"})
    )
    assert client.advisor.apply("f_1").status == "applied"
    assert apply.called

    undo = respx.post(f"{BASE_URL}/advisor/recommendations/f_1/undo").mock(
        return_value=httpx.Response(200, json={"id": "f_1"})
    )
    assert client.advisor.undo("f_1").id == "f_1"
    assert undo.called

    snooze = respx.post(f"{BASE_URL}/advisor/recommendations/f_1/snooze").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert client.advisor.snooze("f_1", days=7).ok is True
    assert json.loads(_last(snooze).content) == {"days": 7}

    dismiss = respx.post(f"{BASE_URL}/advisor/recommendations/f_1/dismiss").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client.advisor.dismiss("f_1", reason="expected")
    assert json.loads(_last(dismiss).content) == {"reason": "expected"}

    feedback = respx.post(f"{BASE_URL}/advisor/recommendations/f_1/feedback").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client.advisor.feedback("f_1", helpful=False, reason="noisy")
    assert json.loads(_last(feedback).content) == {
        "helpful": False,
        "reason": "noisy",
    }


@pytest.mark.anyio
@respx.mock
async def test_advisor_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/advisor/recommendations").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "f_1"}]})
    )
    assert [f.id async for f in aclient.advisor.list(category="deliverability")] == [
        "f_1"
    ]

    respx.get(f"{BASE_URL}/advisor/summary").mock(
        return_value=httpx.Response(200, json={"score": 1})
    )
    assert (await aclient.advisor.summary()).score == 1

    respx.post(f"{BASE_URL}/advisor/refresh").mock(
        return_value=httpx.Response(200, json={"score": 2})
    )
    assert (await aclient.advisor.refresh()).score == 2

    respx.get(f"{BASE_URL}/advisor/settings").mock(
        return_value=httpx.Response(200, json={"enabled": False})
    )
    assert (await aclient.advisor.settings()).enabled is False

    respx.post(f"{BASE_URL}/advisor/recommendations/f_1/apply").mock(
        return_value=httpx.Response(200, json={"id": "f_1"})
    )
    assert (await aclient.advisor.apply("f_1")).id == "f_1"

    respx.post(f"{BASE_URL}/advisor/recommendations/f_1/undo").mock(
        return_value=httpx.Response(200, json={"id": "f_1"})
    )
    assert (await aclient.advisor.undo("f_1")).id == "f_1"

    respx.post(f"{BASE_URL}/advisor/recommendations/f_1/snooze").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await aclient.advisor.snooze("f_1", days=1)).ok is True

    respx.post(f"{BASE_URL}/advisor/recommendations/f_1/dismiss").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await aclient.advisor.dismiss("f_1")).ok is True

    respx.post(f"{BASE_URL}/advisor/recommendations/f_1/feedback").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert (await aclient.advisor.feedback("f_1", helpful=True)).ok is True


# ===========================================================================
# ai skills
# ===========================================================================
@respx.mock
def test_ai_skills_sync_sweep(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/ai/skills").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "sk_1"}]})
    )
    assert [s.id for s in client.ai_skills.list()] == ["sk_1"]
    assert listing.called

    create = respx.post(f"{BASE_URL}/ai/skills").mock(
        return_value=httpx.Response(200, json={"id": "sk_1"})
    )
    client.ai_skills.create(name="Voice", content="Be brief.", enabled=True)
    assert json.loads(_last(create).content) == {
        "name": "Voice",
        "content": "Be brief.",
        "enabled": True,
    }

    update = respx.patch(f"{BASE_URL}/ai/skills/sk_1").mock(
        return_value=httpx.Response(200, json={"id": "sk_1"})
    )
    client.ai_skills.update("sk_1", enabled=False)
    assert json.loads(_last(update).content) == {"enabled": False}

    drop = respx.delete(f"{BASE_URL}/ai/skills/sk_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.ai_skills.delete("sk_1").deleted is True
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_ai_skills_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/ai/skills").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert [s async for s in aclient.ai_skills.list()] == []

    respx.post(f"{BASE_URL}/ai/skills").mock(
        return_value=httpx.Response(200, json={"id": "sk_1"})
    )
    made = await aclient.ai_skills.create(name="V", description="d")
    assert made.id == "sk_1"

    respx.patch(f"{BASE_URL}/ai/skills/sk_1").mock(
        return_value=httpx.Response(200, json={"id": "sk_1"})
    )
    assert (await aclient.ai_skills.update("sk_1", name="V2")).id == "sk_1"

    respx.delete(f"{BASE_URL}/ai/skills/sk_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.ai_skills.delete("sk_1")).deleted is True


# ===========================================================================
# generation
# ===========================================================================
@respx.mock
def test_generation_sync_sweep(client: Warmbly) -> None:
    write = respx.post(f"{BASE_URL}/generation/write").mock(
        return_value=httpx.Response(
            200, json={"text": "Hello", "credits_charged": 2, "model": "m"}
        )
    )
    out = client.generation.write(prompt="intro email", tone="warm")
    assert out.text == "Hello"
    assert out.credits_charged == 2
    assert json.loads(_last(write).content) == {
        "prompt": "intro email",
        "tone": "warm",
    }

    edit = respx.post(f"{BASE_URL}/generation/edit").mock(
        return_value=httpx.Response(200, json={"text": "Shorter"})
    )
    client.generation.edit(text="long", instruction="shorten", context="draft")
    assert json.loads(_last(edit).content) == {
        "text": "long",
        "instruction": "shorten",
        "context": "draft",
    }

    var = respx.post(f"{BASE_URL}/generation/ai-variable").mock(
        return_value=httpx.Response(200, json={"text": "a fact"})
    )
    client.generation.ai_variable(
        prompt="one fact", mode="research", contact_id="ct_1", web_search=True
    )
    assert json.loads(_last(var).content) == {
        "prompt": "one fact",
        "mode": "research",
        "contact_id": "ct_1",
        "web_search": True,
    }


@pytest.mark.anyio
@respx.mock
async def test_generation_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/generation/write").mock(
        return_value=httpx.Response(200, json={"text": "t"})
    )
    assert (await aclient.generation.write(prompt="p")).text == "t"

    respx.post(f"{BASE_URL}/generation/edit").mock(
        return_value=httpx.Response(200, json={"text": "t"})
    )
    assert (await aclient.generation.edit(text="a", instruction="b", tone="c")).text

    respx.post(f"{BASE_URL}/generation/ai-variable").mock(
        return_value=httpx.Response(200, json={"text": "t"})
    )
    out = await aclient.generation.ai_variable(
        prompt="p", tone="t", context_before="b", context_after="a"
    )
    assert out.text == "t"


# ===========================================================================
# audit logs
# ===========================================================================
@respx.mock
def test_audit_logs_sync(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/audit-logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "al_1"}]))
    )
    got = list(
        client.audit_logs.list(
            actor_id="u_1",
            entity_type="campaign",
            entity_id="c_1",
            action="update",
            date="2026-01-01",
            start_date="2026-01-01",
            end_date="2026-01-31",
            limit=10,
        )
    )
    assert [x.id for x in got] == ["al_1"]
    params = _last(r).url.params
    assert params.get("actor_id") == "u_1"
    assert params.get("end_date") == "2026-01-31"


@pytest.mark.anyio
@respx.mock
async def test_audit_logs_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/audit-logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "al_1"}]))
    )
    assert [x.id async for x in aclient.audit_logs.list()] == ["al_1"]


# ===========================================================================
# outreach
# ===========================================================================
@respx.mock
def test_outreach_sync(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(200, json={"bounce_pipeline": {"enabled": True}})
    )
    assert client.outreach.settings().bounce_pipeline["enabled"] is True
    assert get.called

    patch = respx.patch(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(204)
    )
    assert client.outreach.update_settings(settings={"ab_testing": {}}) is None
    assert json.loads(_last(patch).content) == {"settings": {"ab_testing": {}}}


@pytest.mark.anyio
@respx.mock
async def test_outreach_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(200, json={"preflight": {}})
    )
    assert (await aclient.outreach.settings()).preflight == {}

    respx.patch(f"{BASE_URL}/outreach/settings").mock(return_value=httpx.Response(204))
    assert await aclient.outreach.update_settings(settings={}) is None


# ===========================================================================
# deliverability
# ===========================================================================
@respx.mock
def test_deliverability_sync(client: Warmbly) -> None:
    r = respx.post(f"{BASE_URL}/deliverability/events").mock(
        return_value=httpx.Response(202)
    )
    result = client.deliverability.ingest_event(
        event_type="bounce",
        recipient_email="a@e.com",
        campaign_id="c_1",
        reason="550 mailbox unavailable",
        idempotency_key="k_1",
        metadata={"raw": "x"},
    )
    assert result.accepted is None
    assert json.loads(_last(r).content) == {
        "event_type": "bounce",
        "recipient_email": "a@e.com",
        "campaign_id": "c_1",
        "reason": "550 mailbox unavailable",
        "idempotency_key": "k_1",
        "metadata": {"raw": "x"},
    }


@pytest.mark.anyio
@respx.mock
async def test_deliverability_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/deliverability/events").mock(
        return_value=httpx.Response(202)
    )
    out = await aclient.deliverability.ingest_event(
        event_type="complaint",
        recipient_email="a@e.com",
        task_id="t_1",
        contact_id="ct_1",
        provider="ses",
    )
    assert out.accepted is None


# ===========================================================================
# tasks (dead-letter queue)
# ===========================================================================
@respx.mock
def test_tasks_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/tasks/dlq").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "dlq_1"}]})
    )
    got = list(client.tasks.list_dead_letters(status="failed", limit=5))
    assert [d.id for d in got] == ["dlq_1"]
    assert _last(listing).url.params.get("status") == "failed"

    replay = respx.post(f"{BASE_URL}/tasks/dlq/dlq_1/replay").mock(
        return_value=httpx.Response(200, json={"status": "replayed"})
    )
    assert client.tasks.replay("dlq_1").status == "replayed"
    assert replay.called


@pytest.mark.anyio
@respx.mock
async def test_tasks_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/tasks/dlq").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert [d async for d in aclient.tasks.list_dead_letters()] == []

    respx.post(f"{BASE_URL}/tasks/dlq/dlq_1/replay").mock(
        return_value=httpx.Response(200, json={"status": "replayed"})
    )
    assert (await aclient.tasks.replay("dlq_1")).status == "replayed"


# ===========================================================================
# lead sync
# ===========================================================================
@respx.mock
def test_lead_sync_sync_sweep(client: Warmbly) -> None:
    conn = respx.get(f"{BASE_URL}/lead-sync/google/connection").mock(
        return_value=httpx.Response(200, json={"connected": True, "connection": {}})
    )
    assert client.lead_sync.connection().connected is True
    assert conn.called

    sheet = respx.post(f"{BASE_URL}/lead-sync/google/spreadsheet").mock(
        return_value=httpx.Response(200, json={"title": "Leads", "tabs": []})
    )
    client.lead_sync.spreadsheet(connection_id="cn_1", sheet_id="sh_1")
    assert json.loads(_last(sheet).content) == {
        "connection_id": "cn_1",
        "sheet_id": "sh_1",
    }

    preview = respx.post(f"{BASE_URL}/lead-sync/google/preview").mock(
        return_value=httpx.Response(200, json={"headers": ["email"]})
    )
    client.lead_sync.preview(connection_id="cn_1", sheet_id="sh_1", tab_title="Sheet1")
    assert json.loads(_last(preview).content) == {
        "connection_id": "cn_1",
        "sheet_id": "sh_1",
        "tab_title": "Sheet1",
    }

    sources = respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "ls_1"}]})
    )
    got = list(client.lead_sync.list_sources(campaign_id="camp_1"))
    assert [s.id for s in got] == ["ls_1"]
    assert _last(sources).url.params.get("campaign_id") == "camp_1"

    create = respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json={"id": "ls_1"})
    )
    client.lead_sync.create_source(
        connection_id="cn_1",
        sheet_id="sh_1",
        column_mapping=[{"column": "A", "field": "email"}],
        dedup="update",
        label="Weekly",
    )
    assert json.loads(_last(create).content) == {
        "connection_id": "cn_1",
        "sheet_id": "sh_1",
        "column_mapping": [{"column": "A", "field": "email"}],
        "dedup": "update",
        "label": "Weekly",
    }

    get = respx.get(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(200, json={"id": "ls_1"})
    )
    assert client.lead_sync.retrieve_source("ls_1").id == "ls_1"
    assert get.called

    update = respx.patch(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(200, json={"id": "ls_1"})
    )
    client.lead_sync.update_source("ls_1", clear_campaign=True, has_header=False)
    assert json.loads(_last(update).content) == {
        "has_header": False,
        "clear_campaign": True,
    }

    run = respx.post(f"{BASE_URL}/lead-sync/sources/ls_1/sync").mock(
        return_value=httpx.Response(200, json={"source_id": "ls_1"})
    )
    assert client.lead_sync.sync_now("ls_1").source_id == "ls_1"
    assert run.called

    drop = respx.delete(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.lead_sync.delete_source("ls_1").id is None
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_lead_sync_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/lead-sync/google/connection").mock(
        return_value=httpx.Response(200, json={"connected": False})
    )
    assert (await aclient.lead_sync.connection()).connected is False

    respx.post(f"{BASE_URL}/lead-sync/google/spreadsheet").mock(
        return_value=httpx.Response(200, json={"title": "t"})
    )
    sheet = await aclient.lead_sync.spreadsheet(connection_id="c", sheet_id="s")
    assert sheet.title == "t"

    respx.post(f"{BASE_URL}/lead-sync/google/preview").mock(
        return_value=httpx.Response(200, json={"total_rows": 1})
    )
    assert (await aclient.lead_sync.preview(connection_id="c", sheet_id="s")).total_rows

    respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert [s async for s in aclient.lead_sync.list_sources()] == []

    respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json={"id": "ls_1"})
    )
    made = await aclient.lead_sync.create_source(
        connection_id="c",
        sheet_id="s",
        column_mapping=[],
        sheet_title="t",
        tab_title="tab",
        has_header=True,
        target_campaign_id="camp_1",
        category_ids=["cat"],
        subscribed_default=True,
    )
    assert made.id == "ls_1"

    respx.get(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(200, json={"id": "ls_1"})
    )
    assert (await aclient.lead_sync.retrieve_source("ls_1")).id == "ls_1"

    respx.patch(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(200, json={"id": "ls_1"})
    )
    updated = await aclient.lead_sync.update_source(
        "ls_1",
        sheet_id="s2",
        sheet_title="t",
        tab_title="tab",
        column_mapping=[],
        dedup="skip",
        target_campaign_id="camp",
        category_ids=[],
        subscribed_default=False,
        label="L",
    )
    assert updated.id == "ls_1"

    respx.post(f"{BASE_URL}/lead-sync/sources/ls_1/sync").mock(
        return_value=httpx.Response(200, json={"source_id": "ls_1"})
    )
    assert (await aclient.lead_sync.sync_now("ls_1")).source_id == "ls_1"

    respx.delete(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.lead_sync.delete_source("ls_1")).id is None


# ===========================================================================
# meetings
# ===========================================================================
@respx.mock
def test_meetings_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/meetings").mock(
        return_value=httpx.Response(200, json=_page([{"id": "mt_1"}]))
    )
    got = list(client.meetings.list(timeframe="upcoming", status="booked", q="acme"))
    assert [m.id for m in got] == ["mt_1"]
    assert _last(listing).url.params.get("timeframe") == "upcoming"

    summary = respx.get(f"{BASE_URL}/meetings/summary").mock(
        return_value=httpx.Response(200, json={"upcoming": 2, "total": 5})
    )
    assert client.meetings.summary().upcoming == 2
    assert summary.called

    create = respx.post(f"{BASE_URL}/meetings").mock(
        return_value=httpx.Response(201, json={"meeting": {"id": "mt_1"}})
    )
    made = client.meetings.create(
        title="Intro",
        invitee_email="a@e.com",
        scheduled_for="2026-01-01T10:00:00Z",
        duration_minutes=30,
        contact_id="ct_1",
    )
    assert made.meeting.id == "mt_1"
    assert json.loads(_last(create).content) == {
        "title": "Intro",
        "invitee_email": "a@e.com",
        "scheduled_for": "2026-01-01T10:00:00Z",
        "duration_minutes": 30,
        "contact_id": "ct_1",
    }

    drop = respx.delete(f"{BASE_URL}/meetings/mt_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert client.meetings.delete("mt_1").deleted is True
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_meetings_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/meetings").mock(
        return_value=httpx.Response(200, json=_page([{"id": "mt_1"}]))
    )
    assert [m.id async for m in aclient.meetings.list()] == ["mt_1"]

    respx.get(f"{BASE_URL}/meetings/summary").mock(
        return_value=httpx.Response(200, json={"total": 0})
    )
    assert (await aclient.meetings.summary()).total == 0

    respx.post(f"{BASE_URL}/meetings").mock(
        return_value=httpx.Response(201, json={"meeting": {"id": "mt_1"}})
    )
    made = await aclient.meetings.create(
        title="t",
        invitee_email="a@e.com",
        scheduled_for="2026-01-01T10:00:00Z",
        invitee_name="A",
        location="Zoom",
        join_url="https://z",
    )
    assert made.meeting.id == "mt_1"

    respx.delete(f"{BASE_URL}/meetings/mt_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    assert (await aclient.meetings.delete("mt_1")).deleted is True


# ===========================================================================
# warmup routing
# ===========================================================================
@respx.mock
def test_warmup_routing_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/warmup/routing").mock(
        return_value=httpx.Response(200, json={"rules": [{"id": "wr_1"}]})
    )
    assert [r.id for r in client.warmup_routing.list()] == ["wr_1"]
    assert listing.called

    create = respx.post(f"{BASE_URL}/warmup/routing").mock(
        return_value=httpx.Response(201, json={"id": "wr_1"})
    )
    client.warmup_routing.create(
        name="Gmail to Google",
        sender_match_type="provider",
        sender_match_value="google",
        recipient_match_type="provider",
        recipient_match_value="google",
        priority=1,
        weight=2.5,
        enabled=True,
    )
    assert json.loads(_last(create).content) == {
        "name": "Gmail to Google",
        "sender_match_type": "provider",
        "sender_match_value": "google",
        "recipient_match_type": "provider",
        "recipient_match_value": "google",
        "priority": 1,
        "weight": 2.5,
        "enabled": True,
    }

    update = respx.patch(f"{BASE_URL}/warmup/routing/wr_1").mock(
        return_value=httpx.Response(200, json={"id": "wr_1"})
    )
    client.warmup_routing.update("wr_1", enabled=False)
    assert json.loads(_last(update).content) == {"enabled": False}

    drop = respx.delete(f"{BASE_URL}/warmup/routing/wr_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.warmup_routing.delete("wr_1").id is None
    assert drop.called


@pytest.mark.anyio
@respx.mock
async def test_warmup_routing_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/warmup/routing").mock(
        return_value=httpx.Response(200, json={"rules": []})
    )
    assert [r async for r in aclient.warmup_routing.list()] == []

    respx.post(f"{BASE_URL}/warmup/routing").mock(
        return_value=httpx.Response(201, json={"id": "wr_1"})
    )
    made = await aclient.warmup_routing.create(
        name="n",
        sender_match_type="a",
        sender_match_value="b",
        recipient_match_type="c",
        recipient_match_value="d",
    )
    assert made.id == "wr_1"

    respx.patch(f"{BASE_URL}/warmup/routing/wr_1").mock(
        return_value=httpx.Response(200, json={"id": "wr_1"})
    )
    updated = await aclient.warmup_routing.update(
        "wr_1",
        name="n2",
        sender_match_type="a",
        sender_match_value="b",
        recipient_match_type="c",
        recipient_match_value="d",
        priority=2,
        weight=1.0,
    )
    assert updated.id == "wr_1"

    respx.delete(f"{BASE_URL}/warmup/routing/wr_1").mock(
        return_value=httpx.Response(204)
    )
    assert (await aclient.warmup_routing.delete("wr_1")).id is None


# ===========================================================================
# folders / tags / categories
# ===========================================================================
@pytest.mark.parametrize("name", ["folders", "tags", "categories"])
@respx.mock
def test_groups_sync(client: Warmbly, name: str) -> None:
    group = getattr(client, name)

    create = respx.post(f"{BASE_URL}/{name}").mock(
        return_value=httpx.Response(200, json={"id": "g_1", "title": "T"})
    )
    assert group.create(title="T", color="#fff").id == "g_1"
    assert json.loads(_last(create).content) == {"title": "T", "color": "#fff"}

    update = respx.patch(f"{BASE_URL}/{name}/g_1").mock(
        return_value=httpx.Response(200, json={"id": "g_1"})
    )
    group.update("g_1", title="New")
    assert json.loads(_last(update).content) == {"title": "New"}

    move = respx.patch(f"{BASE_URL}/{name}/g_1/move").mock(
        return_value=httpx.Response(200, json=[{"id": "g_1", "position": 2}])
    )
    orders = group.move("g_1", position=2)
    assert [o.position for o in orders] == [2]
    assert json.loads(_last(move).content) == {"position": 2}

    drop = respx.delete(f"{BASE_URL}/{name}/g_1").mock(return_value=httpx.Response(204))
    assert group.delete("g_1").id is None
    assert drop.called


@pytest.mark.parametrize("name", ["folders", "tags", "categories"])
@pytest.mark.anyio
@respx.mock
async def test_groups_async(aclient: AsyncWarmbly, name: str) -> None:
    group = getattr(aclient, name)

    respx.post(f"{BASE_URL}/{name}").mock(
        return_value=httpx.Response(200, json={"id": "g_1"})
    )
    assert (await group.create(title="T")).id == "g_1"

    respx.patch(f"{BASE_URL}/{name}/g_1").mock(
        return_value=httpx.Response(200, json={"id": "g_1"})
    )
    assert (await group.update("g_1", color="#000")).id == "g_1"

    respx.patch(f"{BASE_URL}/{name}/g_1/move").mock(
        return_value=httpx.Response(200, json=[{"id": "g_1", "position": 0}])
    )
    assert [o.id for o in await group.move("g_1", position=0)] == ["g_1"]

    respx.delete(f"{BASE_URL}/{name}/g_1").mock(return_value=httpx.Response(204))
    assert (await group.delete("g_1")).id is None


# ===========================================================================
# timezones
# ===========================================================================
@pytest.mark.anyio
@respx.mock
async def test_timezones_async(aclient: AsyncWarmbly) -> None:
    r = respx.get(f"{BASE_URL}/timezones").mock(
        return_value=httpx.Response(200, json=[{"name": "UTC", "offset": "+00:00"}])
    )
    result = await aclient.timezones.list()
    assert {tz["name"] for tz in result.data} == {"UTC"}
    assert _last(r).url.path == "/v1/timezones"


# ===========================================================================
# analytics
# ===========================================================================
@respx.mock
def test_analytics_sync_sweep(client: Warmbly) -> None:
    for name, path in (
        ("deliverability", "deliverability"),
        ("warmup", "warmup"),
        ("compare_campaigns", "campaigns/compare"),
        ("accounts", "accounts"),
        ("usage", "usage"),
    ):
        r = respx.get(f"{BASE_URL}/analytics/{path}").mock(
            return_value=httpx.Response(200, json={"sent": 1})
        )
        getattr(client.analytics, name)(from_="a", to="b")
        assert _last(r).url.path == f"/v1/analytics/{path}"

    r = respx.get(f"{BASE_URL}/analytics/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    client.analytics.campaign("camp_1")
    r = respx.get(f"{BASE_URL}/analytics/campaigns/camp_1/daily").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    client.analytics.campaign_daily("camp_1")
    r = respx.get(f"{BASE_URL}/analytics/campaigns/camp_1/hourly").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    client.analytics.campaign_hourly("camp_1")
    r = respx.get(f"{BASE_URL}/analytics/accounts/acc_1").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    client.analytics.account("acc_1")
    assert _last(r).url.path == "/v1/analytics/accounts/acc_1"


@pytest.mark.anyio
@respx.mock
async def test_analytics_async_sweep(aclient: AsyncWarmbly) -> None:
    r = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    await aclient.analytics.dashboard(from_="a")
    assert _last(r).url.params.get("from") == "a"

    for name, path in (
        ("deliverability", "deliverability"),
        ("warmup", "warmup"),
        ("compare_campaigns", "campaigns/compare"),
        ("accounts", "accounts"),
        ("usage", "usage"),
    ):
        r = respx.get(f"{BASE_URL}/analytics/{path}").mock(
            return_value=httpx.Response(200, json={"sent": 1})
        )
        await getattr(aclient.analytics, name)()
        assert _last(r).url.path == f"/v1/analytics/{path}"

    r = respx.get(f"{BASE_URL}/analytics/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    await aclient.analytics.campaign("camp_1")
    r = respx.get(f"{BASE_URL}/analytics/campaigns/camp_1/daily").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    await aclient.analytics.campaign_daily("camp_1")
    r = respx.get(f"{BASE_URL}/analytics/campaigns/camp_1/hourly").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    await aclient.analytics.campaign_hourly("camp_1")
    r = respx.get(f"{BASE_URL}/analytics/accounts/acc_1").mock(
        return_value=httpx.Response(200, json={"sent": 1})
    )
    await aclient.analytics.account("acc_1")
