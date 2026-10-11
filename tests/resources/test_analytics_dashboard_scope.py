"""Dashboard campaign and folder filters, sync and async."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
C1 = "11111111-1111-1111-1111-111111111111"
C2 = "22222222-2222-2222-2222-222222222222"
F1 = "33333333-3333-3333-3333-333333333333"

DASHBOARD: dict[str, Any] = {
    "period": "7d",
    "scope": {
        "campaigns": [{"id": C1, "name": "Launch"}],
        "folders": [{"id": F1, "name": "Q4"}],
        "campaign_count": 3,
    },
    "positive_replies": 4,
    "positive_reply_rate": 1.5,
    "reply_breakdown": {"positive": 4, "neutral": 2, "unclassified": 1},
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


@respx.mock
def test_dashboard_scope_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    result = client.analytics.dashboard(
        period="30d", campaign_ids=[C1, C2], folder_ids=[F1]
    )
    params = route.calls.last.request.url.params
    assert params["period"] == "30d"
    assert params["campaign_ids"] == f"{C1},{C2}"
    assert params["folder_ids"] == F1
    assert result.scope["campaign_count"] == 3  # type: ignore[attr-defined]
    assert result.positive_replies == 4  # type: ignore[attr-defined]


@respx.mock
def test_dashboard_unscoped_sends_no_filters_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    client.analytics.dashboard()
    params = route.calls.last.request.url.params
    assert "campaign_ids" not in params
    assert "folder_ids" not in params


@respx.mock
@pytest.mark.anyio
async def test_dashboard_scope_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    result = await aclient.analytics.dashboard(campaign_ids=C1, folder_ids=[F1])
    params = route.calls.last.request.url.params
    assert params["campaign_ids"] == C1
    assert params["folder_ids"] == F1
    assert result.reply_breakdown["positive"] == 4  # type: ignore[attr-defined]
