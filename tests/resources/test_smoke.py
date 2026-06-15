"""Broad, light smoke tests: one representative call per remaining resource.

Each test asserts the HTTP method + path via respx. Mostly synchronous, with a
couple of async examples to exercise the async client wiring.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture
def client() -> Warmbly:
    return Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


# -- emails -----------------------------------------------------------------


@respx.mock
def test_emails_send(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/emails/em_1/send").mock(
        return_value=httpx.Response(
            200, json={"id": "msg_1", "status": "sent", "email_account_id": "em_1"}
        )
    )

    result = client.emails.send(
        "em_1", to="dest@example.com", subject="Hi", text="Hello"
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/emails/em_1/send"
    assert json.loads(request.content) == {
        "to": "dest@example.com",
        "subject": "Hi",
        "text": "Hello",
    }
    assert result.id == "msg_1"


# -- contacts ---------------------------------------------------------------


@respx.mock
def test_contacts_search(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "ct_1", "email": "lead@example.com"}],
                "total": 1,
                "has_more": False,
            },
        )
    )

    result = client.contacts.search(query="lead", limit=10)

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/contacts/search"
    assert json.loads(request.content) == {"query": "lead", "limit": 10}
    assert result.total == 1
    assert result.data[0].id == "ct_1"


# -- webhooks ---------------------------------------------------------------


@respx.mock
def test_webhooks_list(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/webhooks").mock(
        return_value=httpx.Response(200, json=_page([{"id": "wh_1"}]))
    )

    hooks = list(client.webhooks.list())

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/webhooks"
    assert [h.id for h in hooks] == ["wh_1"]


# -- analytics --------------------------------------------------------------


@respx.mock
def test_analytics_dashboard(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json={"sent": 100, "opened": 42})
    )

    result = client.analytics.dashboard(from_="2026-01-01", to="2026-02-01")

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/analytics/dashboard"
    assert request.url.params.get("from") == "2026-01-01"
    assert request.url.params.get("to") == "2026-02-01"
    assert result.sent == 100


# -- integrations -----------------------------------------------------------


@respx.mock
def test_integrations_catalog(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/integrations/catalog").mock(
        return_value=httpx.Response(200, json=_page([{"id": "salesforce"}]))
    )

    entries = list(client.integrations.catalog())

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/integrations/catalog"
    assert [e.id for e in entries] == ["salesforce"]


# -- templates --------------------------------------------------------------


@respx.mock
def test_templates_create(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates").mock(
        return_value=httpx.Response(
            201, json={"id": "tpl_1", "name": "Welcome", "subject": "Hi"}
        )
    )

    template = client.templates.create(
        name="Welcome", subject="Hi", body="<p>Hello</p>"
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/templates"
    assert json.loads(request.content) == {
        "name": "Welcome",
        "subject": "Hi",
        "body": "<p>Hello</p>",
    }
    assert template.id == "tpl_1"


# -- crm --------------------------------------------------------------------


@respx.mock
def test_crm_list_deals(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/crm/deals").mock(
        return_value=httpx.Response(200, json=_page([{"id": "deal_1"}]))
    )

    deals = list(client.crm.list_deals())

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/crm/deals"
    assert [d.id for d in deals] == ["deal_1"]


# -- teams ------------------------------------------------------------------


@respx.mock
def test_teams_list_members(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/teams/members").mock(
        return_value=httpx.Response(200, json=_page([{"id": "tm_1"}]))
    )

    members = list(client.teams.list_members())

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/teams/members"
    assert [m.id for m in members] == ["tm_1"]


# -- plans ------------------------------------------------------------------


@respx.mock
def test_plans_list(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(200, json=_page([{"id": "pro"}]))
    )

    plans = list(client.plans.list())

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/plans"
    assert [p.id for p in plans] == ["pro"]


# -- timezones --------------------------------------------------------------


@respx.mock
def test_timezones_list(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/timezones").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"name": "America/New_York", "offset": "-05:00"},
                {"name": "UTC", "offset": "+00:00"},
            ],
        )
    )

    result = client.timezones.list()

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/timezones"
    assert {tz["name"] for tz in result.data} == {"America/New_York", "UTC"}


# -- unibox -----------------------------------------------------------------


@respx.mock
def test_unibox_list_threads(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/unibox/threads").mock(
        return_value=httpx.Response(200, json=_page([{"id": "th_1"}]))
    )

    threads = list(client.unibox.list_threads())

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/unibox/threads"
    assert [t.id for t in threads] == ["th_1"]


# -- async examples ---------------------------------------------------------


@pytest.mark.anyio
@respx.mock
async def test_async_plans_list() -> None:
    route = respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(200, json=_page([{"id": "pro"}]))
    )

    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as client:
        plans = [p async for p in client.plans.list()]

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/plans"
    assert [p.id for p in plans] == ["pro"]


@pytest.mark.anyio
@respx.mock
async def test_async_emails_send() -> None:
    route = respx.post(f"{BASE_URL}/emails/em_1/send").mock(
        return_value=httpx.Response(200, json={"id": "msg_1", "status": "sent"})
    )

    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as client:
        result = await client.emails.send(
            "em_1", to="dest@example.com", subject="Hi", text="Hello"
        )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/emails/em_1/send"
    assert result.id == "msg_1"
