"""Tests for the analytics routes added or reshaped on the server."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"

DIRECT = {
    "period": "30d",
    "volume": {
        "sent": 40,
        "received": 22,
        "threads_started": 15,
        "replied": 6,
        "reply_rate": 0.4,
        "bounced": 1,
        "median_reply_minutes": 95,
    },
    "tracking": {"mailboxes_opted_in": 1, "mailboxes_total": 3, "tracked_sent": 12},
    "daily_trend": [{"date": "2026-10-01T00:00:00Z", "sent": 3, "received": 2}],
    "mailboxes": [{"email": "a@example.com", "sent": 40, "received": 22}],
    "top_contacts": [{"email": "b@example.com", "sent": 5, "received": 4}],
}

PLACEMENT = {
    "email_account_id": "11111111-1111-1111-1111-111111111111",
    "date_range": {"from": "2026-09-05T00:00:00Z", "to": "2026-10-04T00:00:00Z"},
    "summary": {"sent": 100, "delivered": 90, "inbox": 70, "tabs": 10, "spam": 10},
    "rate": {"window_days": 7, "scope": "major", "inbox_rate": 88.5, "band": "good"},
    "daily": [{"date": "2026-10-03", "sent": 10, "rolling_inbox_rate": None}],
    "providers": [{"group": "google", "inbox": 50, "hosts": []}],
    "mailboxes": [{"email": "a@example.com", "daily_inbox_rate": [None, 90.0]}],
}

TAGGING = {
    "enabled": True,
    "data": [
        {
            "id": "row1",
            "message_id": "m1",
            "thread_id": "t1",
            "kind": "ooo",
            "kind_confidence": 0.9,
            "kind_source": "header",
            "intent": "none",
            "intent_confidence": 0.5,
            "relevance": 3,
            "priority": "low",
            "needs_review": True,
            "review_reason": "low confidence",
            "labels": ["auto"],
            "answers": {"q": "a"},
            "model": "m",
            "input_tokens": 120,
            "actions": ["hold"],
            "return_date": "2026-10-20",
            "created_at": "2026-10-01T10:00:00Z",
        }
    ],
    "total": 1,
    "summary": {"total": 1, "needs_review": 1, "from_offline": 0, "acted": 0},
    "pagination": {"next_cursor": "abc", "has_more": True},
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


def _ok(path: str, payload: dict | None = None) -> respx.Route:
    return respx.get(f"{BASE_URL}{path}").mock(
        return_value=httpx.Response(200, json=payload or {})
    )


@respx.mock
def test_analytics_new_sync(client: Warmbly) -> None:
    route = _ok("/analytics/direct", DIRECT)
    direct = client.analytics.direct(period="30d")
    assert route.calls.last.request.url.params["period"] == "30d"
    assert direct.volume["reply_rate"] == 0.4
    assert direct.tracking["mailboxes_opted_in"] == 1
    assert direct.top_contacts[0]["email"] == "b@example.com"

    route = _ok("/analytics/warmup/placement", PLACEMENT)
    report = client.analytics.warmup_placement(
        from_="2026-09-05", to="2026-10-04", email_id="e1"
    )
    params = route.calls.last.request.url.params
    assert params["from"] == "2026-09-05"
    assert params["to"] == "2026-10-04"
    assert params["email_id"] == "e1"
    assert report.rate["band"] == "good"
    assert report.summary["spam"] == 10
    assert report.mailboxes[0]["daily_inbox_rate"] == [None, 90.0]

    route = _ok("/analytics/inbox-tagging", TAGGING)
    review = client.analytics.inbox_tagging(limit=10, cursor="c", needs_review=True)
    params = route.calls.last.request.url.params
    assert params["limit"] == "10"
    assert params["cursor"] == "c"
    assert params["needs_review"] == "true"
    assert review.enabled is True
    assert review.data[0].return_date == "2026-10-20"
    assert review.data[0].labels == ["auto"]
    assert review.summary["needs_review"] == 1
    assert review.pagination["next_cursor"] == "abc"

    route = _ok("/analytics/dashboard")
    client.analytics.dashboard(period="90d")
    assert route.calls.last.request.url.params["period"] == "90d"

    route = _ok("/analytics/warmup")
    client.analytics.warmup(from_="2026-09-01", to="2026-09-30", email_id="e1")
    assert route.calls.last.request.url.params["email_id"] == "e1"

    route = _ok("/analytics/campaigns/compare")
    client.analytics.compare_campaigns(
        ids=["a", "b"], from_="2026-09-01", to="2026-09-30"
    )
    assert route.calls.last.request.url.params["ids"] == "a,b"

    route = _ok("/analytics/campaigns/c1/hourly")
    client.analytics.campaign_hourly("c1", date="2026-10-01")
    assert route.calls.last.request.url.params["date"] == "2026-10-01"

    route = _ok("/analytics/accounts", {"data": [], "pagination": {}})
    result = client.analytics.accounts(email_ids=["e1", "e2"], limit=5, cursor="n")
    params = route.calls.last.request.url.params
    assert params["email_ids"] == "e1,e2"
    assert params["limit"] == "5"
    assert params["cursor"] == "n"

    route = _ok("/analytics/accounts", {"data": [], "pagination": {}})
    client.analytics.accounts(email_ids="e1")
    assert route.calls.last.request.url.params["email_ids"] == "e1"
    assert result.to_dict()["pagination"] == {}

    route = _ok("/analytics/usage")
    client.analytics.usage(period="month")
    assert route.calls.last.request.url.params["period"] == "month"

    route = _ok("/analytics/campaigns/c1")
    client.analytics.campaign("c1")
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
@pytest.mark.anyio
async def test_analytics_new_async(aclient: AsyncWarmbly) -> None:
    route = _ok("/analytics/direct", DIRECT)
    direct = await aclient.analytics.direct()
    assert dict(route.calls.last.request.url.params) == {}
    assert direct.period == "30d"

    route = _ok("/analytics/warmup/placement", PLACEMENT)
    report = await aclient.analytics.warmup_placement(email_id="e1")
    assert route.calls.last.request.url.params["email_id"] == "e1"
    assert report.date_range["to"] == "2026-10-04T00:00:00Z"

    route = _ok("/analytics/inbox-tagging", TAGGING)
    review = await aclient.analytics.inbox_tagging(needs_review=False)
    assert route.calls.last.request.url.params["needs_review"] == "false"
    assert review.data[0].id == "row1"

    route = _ok("/analytics/dashboard")
    await aclient.analytics.dashboard(period="7d")
    assert route.calls.last.request.url.params["period"] == "7d"

    route = _ok("/analytics/warmup")
    await aclient.analytics.warmup(email_id="e1")
    assert route.calls.last.request.url.params["email_id"] == "e1"

    route = _ok("/analytics/campaigns/compare")
    await aclient.analytics.compare_campaigns(ids=["a"])
    assert route.calls.last.request.url.params["ids"] == "a"

    route = _ok("/analytics/campaigns/c1/hourly")
    await aclient.analytics.campaign_hourly("c1", date="2026-10-01")
    assert route.calls.last.request.url.params["date"] == "2026-10-01"

    route = _ok("/analytics/accounts")
    await aclient.analytics.accounts(email_ids=["e1"], limit=2)
    assert route.calls.last.request.url.params["email_ids"] == "e1"

    route = _ok("/analytics/usage")
    await aclient.analytics.usage(period="month")
    assert route.calls.last.request.url.params["period"] == "month"

    _ok("/analytics/deliverability")
    await aclient.analytics.deliverability()
    _ok("/analytics/campaigns/c1")
    await aclient.analytics.campaign("c1")
    _ok("/analytics/campaigns/c1/daily")
    await aclient.analytics.campaign_daily("c1", from_="2026-09-01", to="2026-09-30")
    _ok("/analytics/accounts/e1")
    await aclient.analytics.account("e1")
