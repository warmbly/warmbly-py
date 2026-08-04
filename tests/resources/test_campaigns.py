"""Tests for the ``campaigns`` resource (representative subset)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from warmbly import Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture
def client() -> Warmbly:
    return Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


@respx.mock
def test_create(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(
            201, json={"id": "camp_1", "name": "Q3 Outreach", "status": "draft"}
        )
    )

    campaign = client.campaigns.create(name="Q3 Outreach", open_tracking=True)

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/campaigns"
    assert json.loads(request.content) == {
        "name": "Q3 Outreach",
        "open_tracking": True,
    }
    assert campaign.id == "camp_1"
    assert campaign.status == "draft"


@respx.mock
def test_list_with_status_filter(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "camp_1", "name": "One", "status": "active"}],
                "pagination": {"next_cursor": None, "has_more": False, "total": 1},
            },
        )
    )

    campaigns = list(client.campaigns.list(status="active"))

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns"
    assert request.url.params.get("status") == "active"
    assert [c.id for c in campaigns] == ["camp_1"]


@respx.mock
def test_start(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/start").mock(
        return_value=httpx.Response(
            200, json={"id": "camp_1", "name": "One", "status": "active"}
        )
    )

    campaign = client.campaigns.start("camp_1")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/campaigns/camp_1/start"
    assert campaign.status == "active"


@respx.mock
def test_stop(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/stop").mock(
        return_value=httpx.Response(
            200, json={"id": "camp_1", "name": "One", "status": "paused"}
        )
    )

    campaign = client.campaigns.stop("camp_1")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/campaigns/camp_1/stop"
    assert campaign.status == "paused"


@respx.mock
def test_list_steps(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "step_1", "campaign_id": "camp_1", "order": 1}],
                "pagination": {"next_cursor": None, "has_more": False, "total": 1},
            },
        )
    )

    steps = list(client.campaigns.list_steps("camp_1"))

    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns/camp_1/steps"
    assert [s.id for s in steps] == ["step_1"]


@respx.mock
def test_create_step(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "step_1",
                "campaign_id": "camp_1",
                "order": 1,
                "subject": "Hello",
            },
        )
    )

    # The endpoint takes no body: a step is created blank, then filled in.
    step = client.campaigns.create_step("camp_1")

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/campaigns/camp_1/steps"
    assert request.content == b""
    assert step.id == "step_1"


@respx.mock
def test_delete(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1", "status": "deleted"})
    )

    result = client.campaigns.delete("camp_1")

    request = route.calls.last.request
    assert request.method == "DELETE"
    assert request.url.path == "/v1/campaigns/camp_1"
    assert result.status == "deleted"
