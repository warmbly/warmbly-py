"""Tests for copying campaigns and templates into other workspaces, and for
``campaigns.lead_timezones``, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.campaigns import CampaignLeadTimezones
from warmbly.resources.templates import WorkspaceCopyResponse

BASE_URL = "https://api.warmbly.com/v1"
CAMPAIGN_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
ORG_A = "0b8c1d2e-3f40-4a5b-8c6d-7e8f9a0b1c2d"
ORG_B = "4d5e6f70-8192-4a3b-9c4d-5e6f7a8b9c0d"
TPL_1 = "6f708192-a3b4-4c5d-8e6f-708192a3b4c5"
COPY_ID = "8192a3b4-c5d6-4e7f-9081-92a3b4c5d6e7"
STEP_ID = "92a3b4c5-d6e7-4f80-9192-a3b4c5d6e7f8"


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


# Shaped like Go's models.WorkspaceCopyResponse.
COPY_RESPONSE: dict[str, Any] = {
    "data": [
        {
            "organization_id": ORG_A,
            "organization_name": "Acme",
            "status": "partial",
            "campaign": {"id": COPY_ID, "name": "Q3 outbound (copy)"},
            "templates": [{"id": TPL_1, "name": "Follow-up"}],
            "review": [
                {
                    "step_id": STEP_ID,
                    "step_name": "Step 2",
                    "fields": ["tag_ids", "form_id"],
                }
            ],
            "warnings": ["1 attachment was too large to copy."],
        },
        {
            "organization_id": ORG_B,
            "organization_name": "Client B",
            "status": "failed",
            "templates": [],
            "review": [],
            "warnings": [],
            "error": {
                "code": "copy_destination_forbidden",
                "message": "You need permission to manage campaigns in this workspace.",
            },
        },
    ]
}

LEAD_TIMEZONES: dict[str, Any] = {
    "campaign_id": CAMPAIGN_ID,
    "timezone_mode": "recipient",
    "timezone": "America/New_York",
    "total": 120,
    "unknown": 20,
    "resolving": 3,
    "zones": [
        {"timezone": "Europe/Berlin", "country": "DE", "leads": 70},
        {"timezone": "UTC", "country": "", "leads": 30},
    ],
}


def _assert_copy(out: WorkspaceCopyResponse) -> None:
    assert isinstance(out, WorkspaceCopyResponse)
    first, second = out.data
    assert first.organization_id == ORG_A
    assert first.organization_name == "Acme"
    assert first.status == "partial"
    assert first.campaign is not None and first.campaign.id == COPY_ID
    assert first.templates[0].name == "Follow-up"
    assert first.review[0].step_id == STEP_ID
    assert first.review[0].fields == ["tag_ids", "form_id"]
    assert first.warnings == ["1 attachment was too large to copy."]
    assert first.error is None
    assert second.status == "failed"
    assert second.campaign is None
    assert second.error is not None
    assert second.error.code == "copy_destination_forbidden"


def _assert_zones(out: CampaignLeadTimezones) -> None:
    assert isinstance(out, CampaignLeadTimezones)
    assert out.campaign_id == CAMPAIGN_ID
    assert out.timezone_mode == "recipient"
    assert out.timezone == "America/New_York"
    assert (out.total, out.unknown, out.resolving) == (120, 20, 3)
    assert out.zones[0].country == "DE"
    assert out.zones[0].leads == 70
    assert out.zones[1].timezone == "UTC"


# -- campaigns.copy_to ---------------------------------------------------------


@respx.mock
def test_campaign_copy_to_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/{CAMPAIGN_ID}/copy-to").mock(
        return_value=httpx.Response(200, json=COPY_RESPONSE)
    )
    out = client.campaigns.copy_to(
        CAMPAIGN_ID, organization_ids=(ORG_A, ORG_B), template_ids=[TPL_1]
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "organization_ids": [ORG_A, ORG_B],
        "template_ids": [TPL_1],
    }
    assert request.headers.get("idempotency-key")
    _assert_copy(out)

    client.campaigns.copy_to(CAMPAIGN_ID, organization_ids=[ORG_A])
    assert json.loads(route.calls.last.request.content) == {"organization_ids": [ORG_A]}


@pytest.mark.anyio
@respx.mock
async def test_campaign_copy_to_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/{CAMPAIGN_ID}/copy-to").mock(
        return_value=httpx.Response(200, json=COPY_RESPONSE)
    )
    out = await aclient.campaigns.copy_to(
        CAMPAIGN_ID, organization_ids=[ORG_A, ORG_B], template_ids=(TPL_1,)
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "organization_ids": [ORG_A, ORG_B],
        "template_ids": [TPL_1],
    }
    _assert_copy(out)

    await aclient.campaigns.copy_to(CAMPAIGN_ID, organization_ids=[ORG_A])
    assert json.loads(route.calls.last.request.content) == {"organization_ids": [ORG_A]}


# -- campaigns.lead_timezones --------------------------------------------------


@respx.mock
def test_campaign_lead_timezones_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/{CAMPAIGN_ID}/lead-timezones").mock(
        return_value=httpx.Response(200, json=LEAD_TIMEZONES)
    )
    out = client.campaigns.lead_timezones(CAMPAIGN_ID)
    request = route.calls.last.request
    assert request.method == "GET"
    assert not request.url.params
    _assert_zones(out)


@pytest.mark.anyio
@respx.mock
async def test_campaign_lead_timezones_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/{CAMPAIGN_ID}/lead-timezones").mock(
        return_value=httpx.Response(200, json=LEAD_TIMEZONES)
    )
    out = await aclient.campaigns.lead_timezones(CAMPAIGN_ID)
    assert route.calls.last.request.method == "GET"
    _assert_zones(out)


# -- templates.copy_to ---------------------------------------------------------


TEMPLATE_COPY: dict[str, Any] = {
    "data": [
        {
            "organization_id": ORG_A,
            "organization_name": "Acme",
            "status": "copied",
            "templates": [{"id": COPY_ID, "name": "Follow-up"}],
            "review": [],
            "warnings": [],
        }
    ]
}


@respx.mock
def test_template_copy_to_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/copy-to").mock(
        return_value=httpx.Response(200, json=TEMPLATE_COPY)
    )
    out = client.templates.copy_to(template_ids=[TPL_1], organization_ids=(ORG_A,))
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "template_ids": [TPL_1],
        "organization_ids": [ORG_A],
    }
    result = out.data[0]
    assert result.status == "copied"
    assert result.campaign is None
    assert result.templates[0].id == COPY_ID


@pytest.mark.anyio
@respx.mock
async def test_template_copy_to_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/copy-to").mock(
        return_value=httpx.Response(200, json=COPY_RESPONSE)
    )
    out = await aclient.templates.copy_to(
        template_ids=(TPL_1,), organization_ids=[ORG_A, ORG_B]
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "template_ids": [TPL_1],
        "organization_ids": [ORG_A, ORG_B],
    }
    _assert_copy(out)
