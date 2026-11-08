"""Tests for the analytics routes added in the second API sync."""

from __future__ import annotations

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


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


DIRECT = {
    "period": "30d",
    "volume": {
        "sent": 120,
        "received": 80,
        "threads_started": 60,
        "replied": 20,
        "reply_rate": 0.33,
        "bounced": 3,
        "median_reply_minutes": 95,
    },
    "tracking": {
        "mailboxes_opted_in": 2,
        "mailboxes_total": 5,
        "tracked_sent": 40,
        "opened": 22,
        "machine_opened": 4,
        "clicked": 6,
        "open_rate": 0.55,
        "click_rate": 0.15,
    },
    "daily_trend": [{"date": "2026-09-24T00:00:00Z", "sent": 10, "received": 6}],
    "mailboxes": [
        {
            "email_account_id": "a1",
            "email": "me@yourdomain.com",
            "track_direct_mail": True,
            "sent": 70,
            "received": 40,
        }
    ],
    "top_contacts": [
        {
            "email": "lead@acme.com",
            "sent": 5,
            "received": 3,
            "last_at": "2026-09-24T09:00:00Z",
        }
    ],
}

TAG_ROW = {
    "id": "t1",
    "message_id": "<m@x>",
    "thread_id": "th1",
    "kind": "reply",
    "kind_confidence": 0.93,
    "kind_source": "model",
    "intent": "interested",
    "intent_confidence": 0.8,
    "relevance": 4,
    "priority": "high",
    "needs_review": True,
    "review_reason": "low confidence",
    "labels": ["hot"],
    "answers": {"q1": "yes"},
    "model": "m-1",
    "input_tokens": 410,
    "actions": ["label"],
    "return_date": "2026-10-05",
    "created_at": "2026-09-24T09:00:00Z",
}


def _check_direct(out: object) -> None:
    from warmbly.resources.analytics import DirectMailAnalytics

    assert isinstance(out, DirectMailAnalytics)
    assert out.period == "30d"
    assert out.volume is not None
    assert out.volume.median_reply_minutes == 95
    assert out.tracking is not None
    assert out.tracking.machine_opened == 4
    assert out.daily_trend[0].received == 6
    assert out.mailboxes[0].track_direct_mail is True
    assert out.top_contacts[0].last_at == "2026-09-24T09:00:00Z"


@respx.mock
def test_analytics_sync2_sync(client: Warmbly) -> None:
    direct = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(200, json=DIRECT)
    )
    _check_direct(client.analytics.direct(period="30d"))
    assert _last(direct).url.params["period"] == "30d"

    tagging = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "enabled": True,
                    "data": [TAG_ROW],
                    "total": 2,
                    "summary": {
                        "total": 2,
                        "needs_review": 1,
                        "from_offline": 0,
                        "acted": 1,
                    },
                    "pagination": {"next_cursor": "c2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "enabled": True,
                    "data": [{"id": "t2"}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    rows = list(client.analytics.inbox_tagging(needs_review=True, limit=1))
    assert [r.id for r in rows] == ["t1", "t2"]
    assert rows[0].kind_confidence == 0.93
    assert rows[0].return_date == "2026-10-05"
    assert rows[0].answers == {"q1": "yes"}
    assert rows[0].actions == ["label"]
    first = tagging.calls[0].request
    assert first.url.params["needs_review"] == "true"
    assert first.url.params["limit"] == "1"
    assert tagging.calls[1].request.url.params["cursor"] == "c2"

    summary_route = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(
            200,
            json={
                "enabled": False,
                "data": [],
                "total": 0,
                "summary": {
                    "total": 9,
                    "needs_review": 3,
                    "from_offline": 1,
                    "acted": 2,
                },
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    summary = client.analytics.inbox_tagging_summary()
    assert _last(summary_route).url.params["limit"] == "1"
    assert summary.enabled is False
    assert summary.summary is not None
    assert summary.summary.needs_review == 3

    placement = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(200, json={"days": []})
    )
    out = client.analytics.warmup_placement(
        email_id="e1", from_="2026-09-01", to="2026-09-30"
    )
    params = _last(placement).url.params
    assert (params["email_id"], params["from"], params["to"]) == (
        "e1",
        "2026-09-01",
        "2026-09-30",
    )
    assert out.to_dict()["days"] == []


@respx.mock
@pytest.mark.anyio
async def test_analytics_sync2_async(aclient: AsyncWarmbly) -> None:
    direct = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(200, json=DIRECT)
    )
    _check_direct(await aclient.analytics.direct())
    assert "period" not in _last(direct).url.params

    tagging = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(
            200,
            json={
                "enabled": True,
                "data": [TAG_ROW],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    rows = [r async for r in aclient.analytics.inbox_tagging(cursor="c0")]
    assert rows[0].needs_review is True
    assert _last(tagging).url.params["cursor"] == "c0"

    summary_route = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(
            200, json={"enabled": True, "data": [], "summary": {"total": 1}}
        )
    )
    summary = await aclient.analytics.inbox_tagging_summary()
    assert _last(summary_route).url.params["limit"] == "1"
    assert summary.summary is not None
    assert summary.summary.total == 1

    placement = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(200, json={"days": [1]})
    )
    out = await aclient.analytics.warmup_placement()
    assert _last(placement).method == "GET"
    assert out.to_dict()["days"] == [1]
