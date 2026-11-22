"""Campaign ``timezone_mode`` and ``warmup_graduation``, and the estimate's ramp inputs."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CAMPAIGN_ID = "6b1f7f0e-2a0c-4c8e-9a51-1d2b3c4d5e6f"

CAMPAIGN: dict[str, Any] = {
    "id": CAMPAIGN_ID,
    "name": "Regional",
    "status": "draft",
    "timezone": "America/New_York",
    "effective_timezone": "America/New_York",
    "timezone_mode": "recipient",
    "ramp_enabled": True,
    "ramp_start": 10,
    "ramp_increment": 5,
    "ramp_ceiling": 50,
    "warmup_graduation": False,
}

ESTIMATE: dict[str, Any] = {
    "recipients": 1200,
    "mailboxes": 4,
    "bottleneck": "campaign_ramp",
}


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


def _body(route: respx.Route) -> Any:
    return json.loads(route.calls.last.request.content)


@respx.mock
def test_timezone_mode_and_graduation_sync(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN)
    )
    campaign = client.campaigns.create(
        name="Regional", timezone_mode="recipient", warmup_graduation=False
    )
    assert _body(create) == {
        "name": "Regional",
        "timezone_mode": "recipient",
        "warmup_graduation": False,
    }
    assert campaign.timezone_mode == "recipient"
    assert campaign.warmup_graduation is False

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMPAIGN_ID}").mock(
        return_value=httpx.Response(200, json=CAMPAIGN)
    )
    client.campaigns.update(
        CAMPAIGN_ID, timezone_mode="campaign", warmup_graduation=True
    )
    assert update.calls.last.request.method == "PATCH"
    assert _body(update) == {"timezone_mode": "campaign", "warmup_graduation": True}

    estimate = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    result = client.campaigns.estimate(
        campaign_id=CAMPAIGN_ID,
        warmup_graduation=False,
        ramp_enabled=True,
        ramp_start=10,
        ramp_increment=5,
        ramp_ceiling=50,
    )
    assert _body(estimate) == {
        "segment_ids": [],
        "campaign_id": CAMPAIGN_ID,
        "warmup_graduation": False,
        "ramp_enabled": True,
        "ramp_start": 10,
        "ramp_increment": 5,
        "ramp_ceiling": 50,
    }
    assert result.bottleneck == "campaign_ramp"
    assert result.recipients == 1200


@pytest.mark.anyio
@respx.mock
async def test_timezone_mode_and_graduation_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN)
    )
    campaign = await aclient.campaigns.create(
        name="Regional", timezone_mode="recipient", warmup_graduation=False
    )
    assert _body(create)["timezone_mode"] == "recipient"
    assert _body(create)["warmup_graduation"] is False
    assert campaign.timezone_mode == "recipient"

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMPAIGN_ID}").mock(
        return_value=httpx.Response(200, json=CAMPAIGN)
    )
    updated = await aclient.campaigns.update(CAMPAIGN_ID, timezone_mode="campaign")
    assert _body(update) == {"timezone_mode": "campaign"}
    assert updated.ramp_ceiling == 50

    estimate = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    result = await aclient.campaigns.estimate(
        segment_ids=["seg_1"], warmup_graduation=True, ramp_ceiling=80
    )
    assert _body(estimate) == {
        "segment_ids": ["seg_1"],
        "warmup_graduation": True,
        "ramp_ceiling": 80,
    }
    assert result.mailboxes == 4
