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
# oauth_applications
# ===========================================================================
@pytest.mark.anyio
@respx.mock
async def test_oauth_applications_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(201, json={"id": "app_1", "name": "App"})
    )
    await aclient.oauth_applications.create(
        name="App", scopes=3, redirect_uris=["https://e/cb"]
    )
    assert _last(create).method == "POST"

    respx.get(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(200, json={"id": "app_1", "name": "App"})
    )
    assert (await aclient.oauth_applications.retrieve("app_1")).id == "app_1"

    update = respx.patch(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(200, json={"id": "app_1", "name": "New"})
    )
    await aclient.oauth_applications.update("app_1", name="New")
    assert json.loads(_last(update).content) == {"name": "New"}

    delete = respx.delete(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(204)
    )
    assert await aclient.oauth_applications.delete("app_1") is None
    assert _last(delete).method == "DELETE"

    rotate = respx.post(f"{BASE_URL}/oauth/applications/app_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"client_secret": "wmcs_new"})
    )
    res = await aclient.oauth_applications.rotate_secret("app_1")
    assert res.client_secret == "wmcs_new"
    assert _last(rotate).method == "POST"

    secret = respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "whsec_1"})
    )
    assert (
        await aclient.oauth_applications.webhook_secret("app_1")
    ).webhook_secret == ("whsec_1")
    assert _last(secret).method == "GET"

    rotate_wh = respx.post(
        f"{BASE_URL}/oauth/applications/app_1/webhook-secret/rotate"
    ).mock(return_value=httpx.Response(200, json={"webhook_secret": "whsec_2"}))
    res2 = await aclient.oauth_applications.rotate_webhook_secret("app_1")
    assert res2.webhook_secret == "whsec_2"
    assert _last(rotate_wh).method == "POST"


@pytest.mark.anyio
@respx.mock
async def test_oauth_applications_async_list(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(200, json=_page([{"id": "app_1", "name": "A"}]))
    )
    ids = [a.id async for a in aclient.oauth_applications.list()]
    assert ids == ["app_1"]
    assert route.called


def test_oauth_applications_sync_secrets(client: Warmbly) -> None:
    with respx.mock:
        rotate = respx.post(f"{BASE_URL}/oauth/applications/app_1/rotate-secret").mock(
            return_value=httpx.Response(200, json={"client_secret": "s"})
        )
        client.oauth_applications.rotate_secret("app_1")
        assert _last(rotate).method == "POST"

        secret = respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-secret").mock(
            return_value=httpx.Response(200, json={"webhook_secret": "w"})
        )
        client.oauth_applications.webhook_secret("app_1")
        assert _last(secret).method == "GET"

        rotate_wh = respx.post(
            f"{BASE_URL}/oauth/applications/app_1/webhook-secret/rotate"
        ).mock(return_value=httpx.Response(200, json={"webhook_secret": "w2"}))
        client.oauth_applications.rotate_webhook_secret("app_1")
        assert _last(rotate_wh).method == "POST"

        delete = respx.delete(f"{BASE_URL}/oauth/applications/app_1").mock(
            return_value=httpx.Response(204)
        )
        assert client.oauth_applications.delete("app_1") is None
        assert _last(delete).method == "DELETE"


# ===========================================================================
# campaigns
# ===========================================================================
CAMPAIGN_SIMPLE = {"id": "camp_1", "name": "C", "status": "draft"}


@respx.mock
def test_campaigns_sync_sweep(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(200, json=_page([CAMPAIGN_SIMPLE]))
    )
    assert [c.id for c in client.campaigns.list(status="active")] == ["camp_1"]
    assert _last(r).url.params.get("status") == "active"

    r = respx.get(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json=CAMPAIGN_SIMPLE)
    )
    assert client.campaigns.retrieve("camp_1").id == "camp_1"

    r = respx.patch(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json=CAMPAIGN_SIMPLE)
    )
    client.campaigns.update("camp_1", name="C2")
    assert json.loads(_last(r).content) == {"name": "C2"}

    r = respx.delete(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.campaigns.delete("camp_1")
    assert _last(r).method == "DELETE"

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(200, json={"daily_limit": 50})
    )
    client.campaigns.retrieve_advanced("camp_1")
    assert _last(r).url.path == "/v1/campaigns/camp_1/advanced"

    r = respx.patch(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(200, json={"daily_limit": 99})
    )
    client.campaigns.update_advanced("camp_1", daily_limit=99)
    assert json.loads(_last(r).content) == {"daily_limit": 99}

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(200, json=_page([{"id": "var_1"}]))
    )
    assert [v.id for v in client.campaigns.list_ab_variants("camp_1")] == ["var_1"]

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(201, json={"id": "var_1"})
    )
    client.campaigns.create_ab_variant("camp_1", name="A", subject="S")
    assert json.loads(_last(r).content) == {"name": "A", "subject": "S"}

    r = respx.patch(f"{BASE_URL}/campaigns/camp_1/ab-variants/var_1").mock(
        return_value=httpx.Response(200, json={"id": "var_1"})
    )
    client.campaigns.update_ab_variant("camp_1", "var_1", weight=2)
    assert json.loads(_last(r).content) == {"weight": 2}

    r = respx.delete(f"{BASE_URL}/campaigns/camp_1/ab-variants/var_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.campaigns.delete_ab_variant("camp_1", "var_1")
    assert _last(r).method == "DELETE"

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/ab-analysis").mock(
        return_value=httpx.Response(200, json={"winner": "var_1"})
    )
    client.campaigns.ab_analysis("camp_1")
    assert _last(r).url.path == "/v1/campaigns/camp_1/ab-analysis"


@respx.mock
def test_campaigns_sync_sweep_two(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(200, json=_page([{"id": "att_1"}]))
    )
    assert [a.id for a in client.campaigns.list_attachments("camp_1")] == ["att_1"]

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(201, json={"id": "att_1"})
    )
    client.campaigns.create_attachment("camp_1", filename="f.pdf")
    assert json.loads(_last(r).content) == {"filename": "f.pdf"}

    r = respx.delete(f"{BASE_URL}/campaigns/camp_1/attachments/att_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.campaigns.delete_attachment("camp_1", "att_1")
    assert _last(r).method == "DELETE"

    for action in ("preflight", "start", "stop"):
        r = respx.post(f"{BASE_URL}/campaigns/camp_1/{action}").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        getattr(client.campaigns, action)("camp_1")
        assert _last(r).method == "POST"

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/test-email").mock(
        return_value=httpx.Response(200, json={"status": "sent"})
    )
    client.campaigns.test_email("camp_1", to="x@e.com")
    assert json.loads(_last(r).content) == {"to": "x@e.com"}

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "log_1"}]))
    )
    assert [x.id for x in client.campaigns.logs("camp_1")] == ["log_1"]

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"sender_ids": ["s1"]})
    )
    client.campaigns.retrieve_senders("camp_1")
    assert _last(r).method == "GET"

    r = respx.put(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"sender_ids": ["s1"]})
    )
    client.campaigns.set_senders("camp_1", sender_ids=["s1"])
    assert _last(r).method == "PUT"
    assert json.loads(_last(r).content) == {"sender_ids": ["s1"]}

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/tracking-domain/verify").mock(
        return_value=httpx.Response(200, json={"verified": True})
    )
    client.campaigns.verify_tracking_domain("camp_1")
    assert _last(r).method == "POST"

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(200, json=_page([{"id": "step_1"}]))
    )
    assert [s.id for s in client.campaigns.list_steps("camp_1")] == ["step_1"]

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(201, json={"id": "step_1"})
    )
    client.campaigns.create_step("camp_1", type="email", order=1)
    assert json.loads(_last(r).content) == {"type": "email", "order": 1}

    r = respx.patch(f"{BASE_URL}/campaigns/camp_1/steps/step_1").mock(
        return_value=httpx.Response(200, json={"id": "step_1"})
    )
    client.campaigns.update_step("camp_1", "step_1", wait_days=2)
    assert json.loads(_last(r).content) == {"wait_days": 2}

    r = respx.delete(f"{BASE_URL}/campaigns/camp_1/steps/step_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.campaigns.delete_step("camp_1", "step_1")
    assert _last(r).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_campaigns_async_sweep(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN_SIMPLE)
    )
    await aclient.campaigns.create(name="C")
    assert _last(create).method == "POST"

    r = respx.get(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(200, json=_page([CAMPAIGN_SIMPLE]))
    )
    assert [c.id async for c in aclient.campaigns.list()] == ["camp_1"]
    page = await aclient.campaigns.list(limit=2)
    assert page.total == 1

    r = respx.get(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json=CAMPAIGN_SIMPLE)
    )
    assert (await aclient.campaigns.retrieve("camp_1")).id == "camp_1"

    r = respx.patch(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json=CAMPAIGN_SIMPLE)
    )
    await aclient.campaigns.update("camp_1", name="C2")
    assert json.loads(_last(r).content) == {"name": "C2"}

    r = respx.delete(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.campaigns.delete("camp_1")
    assert _last(r).method == "DELETE"

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(200, json={"daily_limit": 1})
    )
    await aclient.campaigns.retrieve_advanced("camp_1")
    r = respx.patch(f"{BASE_URL}/campaigns/camp_1/advanced").mock(
        return_value=httpx.Response(200, json={"daily_limit": 2})
    )
    await aclient.campaigns.update_advanced("camp_1", daily_limit=2)

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(200, json=_page([{"id": "var_1"}]))
    )
    assert [v.id async for v in aclient.campaigns.list_ab_variants("camp_1")] == [
        "var_1"
    ]
    r = respx.post(f"{BASE_URL}/campaigns/camp_1/ab-variants").mock(
        return_value=httpx.Response(201, json={"id": "var_1"})
    )
    await aclient.campaigns.create_ab_variant("camp_1", name="A")
    r = respx.patch(f"{BASE_URL}/campaigns/camp_1/ab-variants/var_1").mock(
        return_value=httpx.Response(200, json={"id": "var_1"})
    )
    await aclient.campaigns.update_ab_variant("camp_1", "var_1", weight=1)
    r = respx.delete(f"{BASE_URL}/campaigns/camp_1/ab-variants/var_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.campaigns.delete_ab_variant("camp_1", "var_1")
    r = respx.get(f"{BASE_URL}/campaigns/camp_1/ab-analysis").mock(
        return_value=httpx.Response(200, json={"winner": "var_1"})
    )
    await aclient.campaigns.ab_analysis("camp_1")


@pytest.mark.anyio
@respx.mock
async def test_campaigns_async_sweep_two(aclient: AsyncWarmbly) -> None:
    r = respx.get(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(200, json=_page([{"id": "att_1"}]))
    )
    assert [a.id async for a in aclient.campaigns.list_attachments("camp_1")] == [
        "att_1"
    ]
    r = respx.post(f"{BASE_URL}/campaigns/camp_1/attachments").mock(
        return_value=httpx.Response(201, json={"id": "att_1"})
    )
    await aclient.campaigns.create_attachment("camp_1", filename="f.pdf")
    r = respx.delete(f"{BASE_URL}/campaigns/camp_1/attachments/att_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.campaigns.delete_attachment("camp_1", "att_1")

    for action in ("preflight", "start", "stop"):
        r = respx.post(f"{BASE_URL}/campaigns/camp_1/{action}").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        await getattr(aclient.campaigns, action)("camp_1")
        assert _last(r).method == "POST"

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/test-email").mock(
        return_value=httpx.Response(200, json={"status": "sent"})
    )
    await aclient.campaigns.test_email("camp_1", to="x@e.com")

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/logs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "log_1"}]))
    )
    assert [x.id async for x in aclient.campaigns.logs("camp_1")] == ["log_1"]

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"sender_ids": []})
    )
    await aclient.campaigns.retrieve_senders("camp_1")
    r = respx.put(f"{BASE_URL}/campaigns/camp_1/senders").mock(
        return_value=httpx.Response(200, json={"sender_ids": ["s1"]})
    )
    await aclient.campaigns.set_senders("camp_1", sender_ids=["s1"])
    assert _last(r).method == "PUT"

    r = respx.post(f"{BASE_URL}/campaigns/camp_1/tracking-domain/verify").mock(
        return_value=httpx.Response(200, json={"verified": True})
    )
    await aclient.campaigns.verify_tracking_domain("camp_1")

    r = respx.get(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(200, json=_page([{"id": "step_1"}]))
    )
    assert [s.id async for s in aclient.campaigns.list_steps("camp_1")] == ["step_1"]
    r = respx.post(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(201, json={"id": "step_1"})
    )
    await aclient.campaigns.create_step("camp_1", type="email")
    r = respx.patch(f"{BASE_URL}/campaigns/camp_1/steps/step_1").mock(
        return_value=httpx.Response(200, json={"id": "step_1"})
    )
    await aclient.campaigns.update_step("camp_1", "step_1", wait_days=2)
    r = respx.delete(f"{BASE_URL}/campaigns/camp_1/steps/step_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.campaigns.delete_step("camp_1", "step_1")


# ===========================================================================
# emails
# ===========================================================================
EMAIL = {"id": "em_1", "email": "a@e.com"}


@respx.mock
def test_emails_sync_sweep(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/emails").mock(
        return_value=httpx.Response(200, json=_page([EMAIL]))
    )
    assert [e.id for e in client.emails.list()] == ["em_1"]

    r = respx.get(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=EMAIL)
    )
    assert client.emails.retrieve("em_1").id == "em_1"

    r = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=EMAIL)
    )
    client.emails.update("em_1", name="Acct")
    assert json.loads(_last(r).content) == {"name": "Acct"}

    r = respx.delete(f"{BASE_URL}/emails/em_1").mock(return_value=httpx.Response(204))
    assert client.emails.delete("em_1") is None

    r = respx.patch(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(200, json=EMAIL)
    )
    client.emails.track("em_1", tracking_domain="t.e.com")
    assert json.loads(_last(r).content) == {"tracking_domain": "t.e.com"}

    for action in ("start", "pause", "resume", "stop"):
        r = respx.post(f"{BASE_URL}/emails/em_1/warmup/{action}").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        getattr(client.emails, f"warmup_{action}")("em_1")
        assert _last(r).method == "POST"

    r = respx.get(f"{BASE_URL}/emails/em_1/warmup/ban-status").mock(
        return_value=httpx.Response(200, json={"banned": False})
    )
    client.emails.warmup_ban_status("em_1")
    assert _last(r).url.path == "/v1/emails/em_1/warmup/ban-status"

    r = respx.post(f"{BASE_URL}/emails/em_1/warmup/appeal").mock(
        return_value=httpx.Response(200, json={"status": "submitted"})
    )
    client.emails.warmup_appeal("em_1", message="please")
    assert json.loads(_last(r).content) == {"message": "please"}

    r = respx.get(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json={"spf": True})
    )
    client.emails.auth_check("em_1")
    assert _last(r).url.path == "/v1/emails/em_1/auth-check"

    r = respx.post(f"{BASE_URL}/emails/verify").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    client.emails.verify(email="x@e.com")
    assert json.loads(_last(r).content) == {"email": "x@e.com"}


@pytest.mark.anyio
@respx.mock
async def test_emails_async_sweep(aclient: AsyncWarmbly) -> None:
    r = respx.get(f"{BASE_URL}/emails").mock(
        return_value=httpx.Response(200, json=_page([EMAIL]))
    )
    assert [e.id async for e in aclient.emails.list()] == ["em_1"]

    r = respx.get(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=EMAIL)
    )
    await aclient.emails.retrieve("em_1")
    r = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=EMAIL)
    )
    await aclient.emails.update("em_1", name="A")
    r = respx.delete(f"{BASE_URL}/emails/em_1").mock(return_value=httpx.Response(204))
    assert await aclient.emails.delete("em_1") is None
    r = respx.patch(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(200, json=EMAIL)
    )
    await aclient.emails.track("em_1", tracking_domain="t")

    for action in ("start", "pause", "resume", "stop"):
        r = respx.post(f"{BASE_URL}/emails/em_1/warmup/{action}").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        await getattr(aclient.emails, f"warmup_{action}")("em_1")
        assert _last(r).method == "POST"

    r = respx.get(f"{BASE_URL}/emails/em_1/warmup/ban-status").mock(
        return_value=httpx.Response(200, json={"banned": False})
    )
    await aclient.emails.warmup_ban_status("em_1")
    r = respx.post(f"{BASE_URL}/emails/em_1/warmup/appeal").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    await aclient.emails.warmup_appeal("em_1")
    r = respx.get(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json={"spf": True})
    )
    await aclient.emails.auth_check("em_1")
    r = respx.post(f"{BASE_URL}/emails/verify").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    await aclient.emails.verify(email="x@e.com")


# ===========================================================================
# contacts
# ===========================================================================
@respx.mock
def test_contacts_sync_sweep(client: Warmbly) -> None:
    r = respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"created": 1})
    )
    client.contacts.create(contacts=[{"email": "a@e.com"}])
    assert json.loads(_last(r).content) == {"contacts": [{"email": "a@e.com"}]}

    r = respx.delete(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"deleted": 2})
    )
    client.contacts.bulk_delete(ids=["c1", "c2"])
    assert json.loads(_last(r).content) == {"ids": ["c1", "c2"]}

    r = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 1})
    )
    client.contacts.bulk_update(ids=["c1"], update={"status": "active"})
    assert json.loads(_last(r).content) == {
        "ids": ["c1"],
        "update": {"status": "active"},
    }

    r = respx.post(f"{BASE_URL}/contacts/export").mock(
        return_value=httpx.Response(200, json={"job_id": "j1"})
    )
    client.contacts.export(format="csv")
    assert json.loads(_last(r).content) == {"format": "csv"}

    r = respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(200, json={"token": "t1"})
    )
    client.contacts.import_preview(contacts=[{"email": "a@e.com"}])
    assert _last(r).url.path == "/v1/contacts/import/preview"

    r = respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(200, json={"imported": 1})
    )
    client.contacts.import_commit(token="t1")
    assert json.loads(_last(r).content) == {"token": "t1"}

    r = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    client.contacts.lookup(email="a@e.com")
    assert _last(r).url.params.get("email") == "a@e.com"

    r = respx.get(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    assert client.contacts.retrieve("ct_1").id == "ct_1"

    r = respx.patch(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    client.contacts.update("ct_1", first_name="Lee")
    assert json.loads(_last(r).content) == {"first_name": "Lee"}

    r = respx.delete(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.contacts.delete("ct_1")
    assert _last(r).method == "DELETE"


@respx.mock
def test_contacts_sync_subresources(client: Warmbly) -> None:
    for name, path in (
        ("emails", "emails"),
        ("timeline", "timeline"),
        ("activities", "activities"),
        ("deals", "deals"),
    ):
        r = respx.get(f"{BASE_URL}/contacts/ct_1/{path}").mock(
            return_value=httpx.Response(200, json=_page([{"id": f"{path}_1"}]))
        )
        items = list(getattr(client.contacts, name)("ct_1"))
        assert [i.id for i in items] == [f"{path}_1"]
        assert _last(r).url.path == f"/v1/contacts/ct_1/{path}"

    r = respx.get(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(200, json=_page([{"id": "note_1"}]))
    )
    assert [n.id for n in client.contacts.list_notes("ct_1")] == ["note_1"]

    r = respx.post(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(201, json={"id": "note_1"})
    )
    client.contacts.create_note("ct_1", body="hi")
    assert json.loads(_last(r).content) == {"body": "hi"}

    r = respx.patch(f"{BASE_URL}/contacts/ct_1/notes/note_1").mock(
        return_value=httpx.Response(200, json={"id": "note_1"})
    )
    client.contacts.update_note("ct_1", "note_1", body="edit")
    assert json.loads(_last(r).content) == {"body": "edit"}

    r = respx.delete(f"{BASE_URL}/contacts/ct_1/notes/note_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.contacts.delete_note("ct_1", "note_1")
    assert _last(r).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_contacts_async_sweep(aclient: AsyncWarmbly) -> None:
    r = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "ct_1"}], "total": 1, "has_more": False}
        )
    )
    res = await aclient.contacts.search(query="x")
    assert res.total == 1
    assert json.loads(_last(r).content) == {"query": "x"}

    r = respx.post(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"created": 1})
    )
    await aclient.contacts.create(contacts=[{"email": "a@e.com"}])
    r = respx.delete(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"deleted": 1})
    )
    await aclient.contacts.bulk_delete(ids=["c1"])
    r = respx.patch(f"{BASE_URL}/contacts").mock(
        return_value=httpx.Response(200, json={"updated": 1})
    )
    await aclient.contacts.bulk_update(ids=["c1"], update={"status": "x"})
    r = respx.post(f"{BASE_URL}/contacts/export").mock(
        return_value=httpx.Response(200, json={"job_id": "j"})
    )
    await aclient.contacts.export(format="csv")
    r = respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(200, json={"token": "t"})
    )
    await aclient.contacts.import_preview(file_url="https://e/f.csv")
    r = respx.post(f"{BASE_URL}/contacts/import/commit").mock(
        return_value=httpx.Response(200, json={"imported": 1})
    )
    await aclient.contacts.import_commit(token="t")
    r = respx.get(f"{BASE_URL}/contacts/lookup").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    await aclient.contacts.lookup(email="a@e.com")
    r = respx.get(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    await aclient.contacts.retrieve("ct_1")
    r = respx.patch(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"id": "ct_1"})
    )
    await aclient.contacts.update("ct_1", first_name="Lee")
    r = respx.delete(f"{BASE_URL}/contacts/ct_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.contacts.delete("ct_1")


@pytest.mark.anyio
@respx.mock
async def test_contacts_async_subresources(aclient: AsyncWarmbly) -> None:
    for name, path in (
        ("emails", "emails"),
        ("timeline", "timeline"),
        ("activities", "activities"),
        ("deals", "deals"),
    ):
        r = respx.get(f"{BASE_URL}/contacts/ct_1/{path}").mock(
            return_value=httpx.Response(200, json=_page([{"id": f"{path}_1"}]))
        )
        items = [i.id async for i in getattr(aclient.contacts, name)("ct_1")]
        assert items == [f"{path}_1"]
        assert r.called

    r = respx.get(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(200, json=_page([{"id": "note_1"}]))
    )
    assert [n.id async for n in aclient.contacts.list_notes("ct_1")] == ["note_1"]
    r = respx.post(f"{BASE_URL}/contacts/ct_1/notes").mock(
        return_value=httpx.Response(201, json={"id": "note_1"})
    )
    await aclient.contacts.create_note("ct_1", body="hi")
    r = respx.patch(f"{BASE_URL}/contacts/ct_1/notes/note_1").mock(
        return_value=httpx.Response(200, json={"id": "note_1"})
    )
    await aclient.contacts.update_note("ct_1", "note_1", body="edit")
    r = respx.delete(f"{BASE_URL}/contacts/ct_1/notes/note_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.contacts.delete_note("ct_1", "note_1")


# ===========================================================================
# webhooks
# ===========================================================================
@respx.mock
def test_webhooks_sync_sweep(client: Warmbly) -> None:
    r = respx.post(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(201, json={"id": "wh_1"})
    )
    client.webhooks.create(url="https://e/cb", event_types=["email.sent"])
    assert json.loads(_last(r).content) == {
        "url": "https://e/cb",
        "event_types": ["email.sent"],
    }

    r = respx.get(f"{BASE_URL}/webhooks/event-types").mock(
        return_value=httpx.Response(200, json=_page([{"id": "email.sent"}]))
    )
    assert [e.id for e in client.webhooks.event_types()] == ["email.sent"]

    r = respx.get(f"{BASE_URL}/webhooks/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    assert [d.id for d in client.webhooks.deliveries()] == ["dl_1"]

    r = respx.post(f"{BASE_URL}/webhooks/deliveries/dl_1/redeliver").mock(
        return_value=httpx.Response(200, json={"id": "dl_1"})
    )
    client.webhooks.redeliver("dl_1")
    assert _last(r).method == "POST"

    r = respx.get(f"{BASE_URL}/webhooks/throttle-drops").mock(
        return_value=httpx.Response(200, json=_page([{"id": "td_1"}]))
    )
    assert [t.id for t in client.webhooks.throttle_drops()] == ["td_1"]

    r = respx.patch(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"id": "wh_1"})
    )
    client.webhooks.update("wh_1", enabled=False)
    assert json.loads(_last(r).content) == {"enabled": False}

    r = respx.delete(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.webhooks.delete("wh_1")
    assert _last(r).method == "DELETE"

    r = respx.post(f"{BASE_URL}/webhooks/wh_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"id": "wh_1"})
    )
    client.webhooks.rotate_secret("wh_1")
    assert _last(r).method == "POST"

    r = respx.post(f"{BASE_URL}/webhooks/wh_1/verify").mock(
        return_value=httpx.Response(200, json={"verified": True})
    )
    client.webhooks.verify("wh_1")
    assert _last(r).method == "POST"

    r = respx.get(f"{BASE_URL}/webhooks/wh_1/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_2"}]))
    )
    assert [d.id for d in client.webhooks.endpoint_deliveries("wh_1")] == ["dl_2"]


@pytest.mark.anyio
@respx.mock
async def test_webhooks_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(201, json={"id": "wh_1"})
    )
    await aclient.webhooks.create(url="https://e/cb", event_types=["email.sent"])
    respx.get(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(200, json=_page([{"id": "wh_1"}]))
    )
    assert [w.id async for w in aclient.webhooks.list()] == ["wh_1"]
    respx.get(f"{BASE_URL}/webhooks/event-types").mock(
        return_value=httpx.Response(200, json=_page([{"id": "email.sent"}]))
    )
    assert [e.id async for e in aclient.webhooks.event_types()] == ["email.sent"]
    respx.get(f"{BASE_URL}/webhooks/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_1"}]))
    )
    assert [d.id async for d in aclient.webhooks.deliveries()] == ["dl_1"]
    respx.post(f"{BASE_URL}/webhooks/deliveries/dl_1/redeliver").mock(
        return_value=httpx.Response(200, json={"id": "dl_1"})
    )
    await aclient.webhooks.redeliver("dl_1")
    respx.get(f"{BASE_URL}/webhooks/throttle-drops").mock(
        return_value=httpx.Response(200, json=_page([{"id": "td_1"}]))
    )
    assert [t.id async for t in aclient.webhooks.throttle_drops()] == ["td_1"]
    respx.patch(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"id": "wh_1"})
    )
    await aclient.webhooks.update("wh_1", enabled=True)
    respx.delete(f"{BASE_URL}/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.webhooks.delete("wh_1")
    respx.post(f"{BASE_URL}/webhooks/wh_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"id": "wh_1"})
    )
    await aclient.webhooks.rotate_secret("wh_1")
    respx.post(f"{BASE_URL}/webhooks/wh_1/verify").mock(
        return_value=httpx.Response(200, json={"verified": True})
    )
    await aclient.webhooks.verify("wh_1")
    respx.get(f"{BASE_URL}/webhooks/wh_1/deliveries").mock(
        return_value=httpx.Response(200, json=_page([{"id": "dl_2"}]))
    )
    assert [d.id async for d in aclient.webhooks.endpoint_deliveries("wh_1")] == [
        "dl_2"
    ]


# ===========================================================================
# integrations
# ===========================================================================
@respx.mock
def test_integrations_sync_sweep(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(200, json=_page([{"id": "conn_1"}]))
    )
    assert [c.id for c in client.integrations.list_connections(provider="hubspot")] == [
        "conn_1"
    ]
    assert _last(r).url.params.get("provider") == "hubspot"

    r = respx.post(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(201, json={"id": "conn_1"})
    )
    client.integrations.create_connection(provider="hubspot")
    assert json.loads(_last(r).content) == {"provider": "hubspot"}

    r = respx.get(f"{BASE_URL}/integrations/connections/conn_1").mock(
        return_value=httpx.Response(200, json={"id": "conn_1"})
    )
    client.integrations.get_connection("conn_1")

    r = respx.patch(f"{BASE_URL}/integrations/connections/conn_1/config").mock(
        return_value=httpx.Response(200, json={"id": "conn_1"})
    )
    client.integrations.update_connection_config("conn_1", config={"k": "v"})
    assert json.loads(_last(r).content) == {"config": {"k": "v"}}

    r = respx.delete(f"{BASE_URL}/integrations/connections/conn_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.integrations.delete_connection("conn_1")

    r = respx.get(f"{BASE_URL}/integrations/connections/conn_1/events").mock(
        return_value=httpx.Response(200, json=_page([{"id": "ev_1"}]))
    )
    assert [e.id for e in client.integrations.list_events("conn_1")] == ["ev_1"]

    r = respx.post(f"{BASE_URL}/integrations/connections/conn_1/events").mock(
        return_value=httpx.Response(201, json={"id": "ev_1"})
    )
    client.integrations.add_event("conn_1", event_type="contact.created")
    assert json.loads(_last(r).content) == {"event_type": "contact.created"}

    r = respx.delete(f"{BASE_URL}/integrations/connections/conn_1/events/ev_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.integrations.remove_event("conn_1", "ev_1")

    r = respx.get(f"{BASE_URL}/integrations/connections/conn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": []})
    )
    client.integrations.get_field_mappings("conn_1")

    r = respx.put(f"{BASE_URL}/integrations/connections/conn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": []})
    )
    client.integrations.set_field_mappings("conn_1", mappings=[{"from": "a"}])
    assert _last(r).method == "PUT"

    r = respx.get(f"{BASE_URL}/integrations/connections/conn_1/runs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "run_1"}]))
    )
    assert [x.id for x in client.integrations.runs("conn_1")] == ["run_1"]

    r = respx.get(f"{BASE_URL}/integrations/connections/conn_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "w"})
    )
    client.integrations.connection_webhook_secret("conn_1")

    r = respx.post(f"{BASE_URL}/integrations/connections/conn_1/test").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client.integrations.test_connection("conn_1")

    r = respx.post(f"{BASE_URL}/integrations/connections/conn_1/push").mock(
        return_value=httpx.Response(200, json={"run_id": "r1"})
    )
    client.integrations.push("conn_1", records=[{"x": 1}])
    assert json.loads(_last(r).content) == {"records": [{"x": 1}]}

    r = respx.get(f"{BASE_URL}/integrations/bookings").mock(
        return_value=httpx.Response(200, json=_page([{"id": "bk_1"}]))
    )
    assert [b.id for b in client.integrations.bookings(from_="2026-01-01")] == ["bk_1"]
    assert _last(r).url.params.get("from") == "2026-01-01"


@pytest.mark.anyio
@respx.mock
async def test_integrations_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(200, json=_page([{"id": "hubspot"}]))
    )
    assert [c.id async for c in aclient.integrations.catalog()] == ["hubspot"]
    respx.get(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(200, json=_page([{"id": "conn_1"}]))
    )
    assert [c.id async for c in aclient.integrations.list_connections()] == ["conn_1"]
    respx.post(f"{BASE_URL}/integrations/connections").mock(
        return_value=httpx.Response(201, json={"id": "conn_1"})
    )
    await aclient.integrations.create_connection(provider="hubspot")
    respx.get(f"{BASE_URL}/integrations/connections/conn_1").mock(
        return_value=httpx.Response(200, json={"id": "conn_1"})
    )
    await aclient.integrations.get_connection("conn_1")
    respx.patch(f"{BASE_URL}/integrations/connections/conn_1/config").mock(
        return_value=httpx.Response(200, json={"id": "conn_1"})
    )
    await aclient.integrations.update_connection_config("conn_1", config={"k": "v"})
    respx.delete(f"{BASE_URL}/integrations/connections/conn_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.integrations.delete_connection("conn_1")
    respx.get(f"{BASE_URL}/integrations/connections/conn_1/events").mock(
        return_value=httpx.Response(200, json=_page([{"id": "ev_1"}]))
    )
    assert [e.id async for e in aclient.integrations.list_events("conn_1")] == ["ev_1"]
    respx.post(f"{BASE_URL}/integrations/connections/conn_1/events").mock(
        return_value=httpx.Response(201, json={"id": "ev_1"})
    )
    await aclient.integrations.add_event("conn_1", event_type="x")
    respx.delete(f"{BASE_URL}/integrations/connections/conn_1/events/ev_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.integrations.remove_event("conn_1", "ev_1")
    respx.get(f"{BASE_URL}/integrations/connections/conn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": []})
    )
    await aclient.integrations.get_field_mappings("conn_1")
    respx.put(f"{BASE_URL}/integrations/connections/conn_1/field-mappings").mock(
        return_value=httpx.Response(200, json={"mappings": []})
    )
    await aclient.integrations.set_field_mappings("conn_1", mappings=[])
    respx.get(f"{BASE_URL}/integrations/connections/conn_1/runs").mock(
        return_value=httpx.Response(200, json=_page([{"id": "run_1"}]))
    )
    assert [x.id async for x in aclient.integrations.runs("conn_1")] == ["run_1"]
    respx.get(f"{BASE_URL}/integrations/connections/conn_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "w"})
    )
    await aclient.integrations.connection_webhook_secret("conn_1")
    respx.post(f"{BASE_URL}/integrations/connections/conn_1/test").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    await aclient.integrations.test_connection("conn_1")
    respx.post(f"{BASE_URL}/integrations/connections/conn_1/push").mock(
        return_value=httpx.Response(200, json={"run_id": "r"})
    )
    await aclient.integrations.push("conn_1", records=[{"x": 1}])
    respx.get(f"{BASE_URL}/integrations/bookings").mock(
        return_value=httpx.Response(200, json=_page([{"id": "bk_1"}]))
    )
    assert [b.id async for b in aclient.integrations.bookings()] == ["bk_1"]


# ===========================================================================
# crm
# ===========================================================================
@respx.mock
def test_crm_sync_sweep(client: Warmbly) -> None:
    r = respx.post(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(201, json={"id": "deal_1"})
    )
    client.crm.create_deal(name="Big deal", amount=1000)
    assert json.loads(_last(r).content) == {"name": "Big deal", "amount": 1000}

    r = respx.get(f"{BASE_URL}/crm/deals/deal_1").mock(
        return_value=httpx.Response(200, json={"id": "deal_1"})
    )
    assert client.crm.retrieve_deal("deal_1").id == "deal_1"

    r = respx.patch(f"{BASE_URL}/crm/deals/deal_1").mock(
        return_value=httpx.Response(200, json={"id": "deal_1"})
    )
    client.crm.update_deal("deal_1", stage="won")
    assert json.loads(_last(r).content) == {"stage": "won"}

    r = respx.delete(f"{BASE_URL}/crm/deals/deal_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.crm.delete_deal("deal_1")

    r = respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(200, json=_page([{"id": "pl_1"}]))
    )
    assert [p.id for p in client.crm.list_pipelines()] == ["pl_1"]

    r = respx.get(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tk_1"}]))
    )
    assert [t.id for t in client.crm.list_tasks()] == ["tk_1"]

    r = respx.post(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(201, json={"id": "tk_1"})
    )
    client.crm.create_task(title="Call")
    assert json.loads(_last(r).content) == {"title": "Call"}


@pytest.mark.anyio
@respx.mock
async def test_crm_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(200, json=_page([{"id": "deal_1"}]))
    )
    assert [d.id async for d in aclient.crm.list_deals()] == ["deal_1"]
    respx.post(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(201, json={"id": "deal_1"})
    )
    await aclient.crm.create_deal(name="D")
    respx.get(f"{BASE_URL}/crm/deals/deal_1").mock(
        return_value=httpx.Response(200, json={"id": "deal_1"})
    )
    await aclient.crm.retrieve_deal("deal_1")
    respx.patch(f"{BASE_URL}/crm/deals/deal_1").mock(
        return_value=httpx.Response(200, json={"id": "deal_1"})
    )
    await aclient.crm.update_deal("deal_1", stage="won")
    respx.delete(f"{BASE_URL}/crm/deals/deal_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.crm.delete_deal("deal_1")
    respx.get(f"{BASE_URL}/crm/pipelines").mock(
        return_value=httpx.Response(200, json=_page([{"id": "pl_1"}]))
    )
    assert [p.id async for p in aclient.crm.list_pipelines()] == ["pl_1"]
    respx.get(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tk_1"}]))
    )
    assert [t.id async for t in aclient.crm.list_tasks()] == ["tk_1"]
    respx.post(f"{BASE_URL}/crm/tasks").mock(
        return_value=httpx.Response(201, json={"id": "tk_1"})
    )
    await aclient.crm.create_task(title="Call")


# ===========================================================================
# templates
# ===========================================================================
@respx.mock
def test_templates_sync_sweep(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tpl_1"}]))
    )
    assert [t.id for t in client.templates.list()] == ["tpl_1"]

    r = respx.get(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    assert client.templates.retrieve("tpl_1").id == "tpl_1"

    r = respx.patch(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    client.templates.update("tpl_1", name="New")
    assert json.loads(_last(r).content) == {"name": "New"}

    r = respx.delete(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    client.templates.delete("tpl_1")
    assert _last(r).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_templates_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(201, json={"id": "tpl_1"})
    )
    await aclient.templates.create(name="N", subject="S", body="B")
    respx.get(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tpl_1"}]))
    )
    assert [t.id async for t in aclient.templates.list()] == ["tpl_1"]
    respx.get(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    await aclient.templates.retrieve("tpl_1")
    respx.patch(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"id": "tpl_1"})
    )
    await aclient.templates.update("tpl_1", name="New")
    respx.delete(f"{BASE_URL}/templates/tpl_1").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    await aclient.templates.delete("tpl_1")


# ===========================================================================
# teams
# ===========================================================================
@respx.mock
def test_teams_sync_sweep(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/teams/roles").mock(
        return_value=httpx.Response(200, json=_page([{"id": "role_1"}]))
    )
    assert [x.id for x in client.teams.list_roles()] == ["role_1"]

    r = respx.post(f"{BASE_URL}/teams/invitations").mock(
        return_value=httpx.Response(201, json={"id": "inv_1"})
    )
    client.teams.invite(email="a@e.com", role="member")
    assert json.loads(_last(r).content) == {"email": "a@e.com", "role": "member"}

    r = respx.delete(f"{BASE_URL}/teams/members/tm_1").mock(
        return_value=httpx.Response(200, json={"status": "removed"})
    )
    client.teams.remove_member("tm_1")
    assert _last(r).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_teams_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/teams/members").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tm_1"}]))
    )
    assert [m.id async for m in aclient.teams.list_members()] == ["tm_1"]
    respx.get(f"{BASE_URL}/teams/roles").mock(
        return_value=httpx.Response(200, json=_page([{"id": "role_1"}]))
    )
    assert [x.id async for x in aclient.teams.list_roles()] == ["role_1"]
    respx.post(f"{BASE_URL}/teams/invitations").mock(
        return_value=httpx.Response(201, json={"id": "inv_1"})
    )
    await aclient.teams.invite(email="a@e.com", role="member")
    respx.delete(f"{BASE_URL}/teams/members/tm_1").mock(
        return_value=httpx.Response(200, json={"status": "removed"})
    )
    await aclient.teams.remove_member("tm_1")


# ===========================================================================
# plans
# ===========================================================================
@respx.mock
def test_plans_sync_retrieve(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/plans/pro").mock(
        return_value=httpx.Response(200, json={"id": "pro"})
    )
    assert client.plans.retrieve("pro").id == "pro"
    assert _last(r).url.path == "/v1/plans/pro"


@pytest.mark.anyio
@respx.mock
async def test_plans_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(200, json=_page([{"id": "pro"}]))
    )
    assert [p.id async for p in aclient.plans.list()] == ["pro"]
    respx.get(f"{BASE_URL}/plans/pro").mock(
        return_value=httpx.Response(200, json={"id": "pro"})
    )
    assert (await aclient.plans.retrieve("pro")).id == "pro"


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
# unibox
# ===========================================================================
@respx.mock
def test_unibox_sync_sweep(client: Warmbly) -> None:
    r = respx.get(f"{BASE_URL}/unibox/threads/th_1").mock(
        return_value=httpx.Response(200, json={"id": "th_1"})
    )
    assert client.unibox.retrieve_thread("th_1").id == "th_1"

    r = respx.post(f"{BASE_URL}/unibox/threads/th_1/reply").mock(
        return_value=httpx.Response(200, json={"id": "msg_1"})
    )
    client.unibox.reply("th_1", body="hello")
    assert json.loads(_last(r).content) == {"body": "hello"}

    r = respx.post(f"{BASE_URL}/unibox/threads/th_1/read").mock(
        return_value=httpx.Response(200, json={"id": "th_1"})
    )
    client.unibox.mark_read("th_1")
    assert _last(r).method == "POST"


@pytest.mark.anyio
@respx.mock
async def test_unibox_async_sweep(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/unibox/threads").mock(
        return_value=httpx.Response(200, json=_page([{"id": "th_1"}]))
    )
    assert [t.id async for t in aclient.unibox.list_threads()] == ["th_1"]
    respx.get(f"{BASE_URL}/unibox/threads/th_1").mock(
        return_value=httpx.Response(200, json={"id": "th_1"})
    )
    await aclient.unibox.retrieve_thread("th_1")
    respx.post(f"{BASE_URL}/unibox/threads/th_1/reply").mock(
        return_value=httpx.Response(200, json={"id": "msg_1"})
    )
    await aclient.unibox.reply("th_1", body="hi")
    respx.post(f"{BASE_URL}/unibox/threads/th_1/read").mock(
        return_value=httpx.Response(200, json={"id": "th_1"})
    )
    await aclient.unibox.mark_read("th_1")


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
