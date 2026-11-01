"""Tests for the analytics reports and the query params the server reads.
Sync and async."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

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
        "replied": 18,
        "reply_rate": 0.3,
        "bounced": 2,
        "median_reply_minutes": 95,
    },
    "tracking": {
        "mailboxes_opted_in": 1,
        "mailboxes_total": 3,
        "tracked_sent": 40,
        "opened": 22,
        "machine_opened": 5,
        "clicked": 4,
        "open_rate": 0.55,
        "click_rate": 0.1,
    },
    "daily_trend": [{"date": "2026-10-30T00:00:00Z", "sent": 5, "received": 3}],
    "mailboxes": [
        {
            "email_account_id": "mb-1",
            "email": "sam@acme.io",
            "track_direct_mail": True,
            "sent": 70,
            "received": 50,
        }
    ],
    "top_contacts": [
        {
            "email": "pat@globex.com",
            "sent": 9,
            "received": 6,
            "last_at": "2026-10-30T12:00:00Z",
        }
    ],
}


def _check_direct(d: Any) -> None:
    assert d.period == "30d"
    assert d.volume.sent == 120
    assert d.volume.threads_started == 60
    assert d.volume.reply_rate == 0.3
    assert d.volume.median_reply_minutes == 95
    assert d.tracking.mailboxes_opted_in == 1
    assert d.tracking.machine_opened == 5
    assert d.tracking.click_rate == 0.1
    assert d.daily_trend[0].date == "2026-10-30T00:00:00Z"
    assert d.daily_trend[0].received == 3
    assert d.mailboxes[0].email_account_id == "mb-1"
    assert d.mailboxes[0].track_direct_mail is True
    assert d.top_contacts[0].email == "pat@globex.com"
    assert d.top_contacts[0].last_at == "2026-10-30T12:00:00Z"


TAG = {
    "id": "tag-1",
    "message_id": "m-1",
    "thread_id": "th-1",
    "kind": "reply",
    "kind_confidence": 0.93,
    "kind_source": "model",
    "intent": "out_of_office",
    "intent_confidence": 0.88,
    "relevance": 4,
    "priority": "low",
    "needs_review": True,
    "review_reason": "low confidence",
    "labels": ["ooo"],
    "answers": {"returns": "2026-11-10"},
    "model": "small-1",
    "input_tokens": 312,
    "actions": ["hold"],
    "return_date": "2026-11-10",
    "created_at": "2026-10-30T12:00:00Z",
}


def _tag_page(rows: list[dict[str, Any]], cursor: str | None) -> dict[str, Any]:
    return {
        "enabled": True,
        "data": rows,
        "total": 3,
        "summary": {"total": 3, "needs_review": 2, "from_offline": 1, "acted": 0},
        "pagination": {"next_cursor": cursor, "has_more": cursor is not None},
    }


def _check_tag(t: Any) -> None:
    assert t.id == "tag-1"
    assert (t.message_id, t.thread_id) == ("m-1", "th-1")
    assert (t.kind, t.kind_confidence, t.kind_source) == ("reply", 0.93, "model")
    assert (t.intent, t.intent_confidence) == ("out_of_office", 0.88)
    assert t.relevance == 4
    assert t.priority == "low"
    assert t.needs_review is True
    assert t.review_reason == "low confidence"
    assert t.labels == ["ooo"]
    assert t.answers == {"returns": "2026-11-10"}
    assert t.model == "small-1"
    assert t.input_tokens == 312
    assert t.actions == ["hold"]
    assert t.return_date == "2026-11-10"


def _counts(**over: Any) -> dict[str, Any]:
    base = {
        "sent": 100,
        "delivered": 90,
        "inbox": 70,
        "tabs": 10,
        "spam": 10,
        "unknown": 0,
        "archived": 0,
        "custom": 0,
        "instrumented_receipts": 88,
        "observed_receipts": 90,
        "legacy_uninstrumented_receipts": 2,
        "rescue_requested": 4,
        "non_spam_metric": {"numerator": 80, "denominator": 90, "value": 88.89},
        "rescued": 4,
        "rescue_confirmed": 3,
        "rescue_missing": 0,
        "rescue_failed": 0,
        "rescue_unreported": 1,
        "unconfirmed": 10,
        "inbox_rate": 88.89,
        "spam_rate": 11.11,
    }
    base.update(over)
    return base


RATE = {
    "window_days": 7,
    "min_sample": 20,
    "scope": "major",
    "delivered": 60,
    "inbox": 45,
    "tabs": 5,
    "spam": 10,
    "inbox_rate": 83.33,
    "band": "fair",
    "metric": {"numerator": 50, "denominator": 60, "value": 83.33, "window_days": 7},
    "other_delivered": 5,
    "other_inbox_rate": None,
}

WARMUP_PLACEMENT = {
    "email_account_id": "mb-1",
    "date_range": {"from": "2026-10-02T00:00:00Z", "to": "2026-10-31T00:00:00Z"},
    "summary": _counts(),
    "rate": RATE,
    "daily": [
        {
            "date": "2026-10-30",
            **_counts(sent=5),
            "rolling_inbox_rate": None,
            "groups": [{"group": "google", "inbox": 3, "tabs": 1, "spam": 0}],
        }
    ],
    "providers": [
        {
            "group": "google",
            **_counts(),
            "hosts": [{"host": "gmail", **_counts()}],
        }
    ],
    "mailboxes": [
        {
            "email_account_id": "mb-1",
            "email": "sam@acme.io",
            **_counts(),
            "rate": RATE,
            "daily_inbox_rate": [None, 90.5],
        }
    ],
}


def _check_warmup_placement(r: Any) -> None:
    assert r.email_account_id == "mb-1"
    assert r.date_range["to"] == "2026-10-31T00:00:00Z"
    assert r.summary.sent == 100
    assert r.summary.delivered == 90
    assert r.summary.tabs == 10
    assert r.summary.instrumented_receipts == 88
    assert r.summary.rescue_unreported == 1
    assert r.summary.inbox_rate == 88.89
    assert r.summary.non_spam_metric.numerator == 80
    assert r.rate.window_days == 7
    assert r.rate.min_sample == 20
    assert r.rate.scope == "major"
    assert r.rate.band == "fair"
    assert r.rate.metric.window_days == 7
    assert r.rate.other_inbox_rate is None
    assert r.daily[0].date == "2026-10-30"
    assert r.daily[0].sent == 5
    assert r.daily[0].rolling_inbox_rate is None
    assert r.daily[0].groups[0]["group"] == "google"
    assert r.providers[0].group == "google"
    assert r.providers[0].spam == 10
    assert r.providers[0].hosts[0]["host"] == "gmail"
    assert r.mailboxes[0].email == "sam@acme.io"
    assert r.mailboxes[0].rate.inbox_rate == 83.33
    assert r.mailboxes[0].daily_inbox_rate == [None, 90.5]


@respx.mock
def test_direct(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(200, json=DIRECT)
    )
    _check_direct(client.analytics.direct(period="30d"))
    req = _last(route)
    assert req.method == "GET"
    assert req.url.params["period"] == "30d"

    client.analytics.direct()
    assert dict(_last(route).url.params) == {}


@respx.mock
def test_inbox_tagging(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        side_effect=[
            httpx.Response(200, json=_tag_page([TAG], "50")),
            httpx.Response(200, json=_tag_page([{**TAG, "id": "tag-2"}], None)),
        ]
    )
    rows = list(client.analytics.list_inbox_tagging(needs_review=True, limit=1))
    assert [r.id for r in rows] == ["tag-1", "tag-2"]
    _check_tag(rows[0])
    first, second = (c.request for c in route.calls)
    assert first.url.params["needs_review"] == "true"
    assert first.url.params["limit"] == "1"
    assert second.url.params["cursor"] == "50"
    assert second.url.params["needs_review"] == "true"

    route.mock(return_value=httpx.Response(200, json=_tag_page([TAG], "50")))
    page = client.analytics.inbox_tagging(cursor="10")
    assert _last(route).url.params["cursor"] == "10"
    assert page.enabled is True
    assert page.total == 3
    assert page.summary.needs_review == 2
    assert page.summary.from_offline == 1
    assert page.pagination["next_cursor"] == "50"
    _check_tag(page.data[0])


@respx.mock
def test_inbox_tagging_disabled(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(
            200,
            json={
                "enabled": False,
                "data": [],
                "total": 0,
                "summary": {},
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    page = client.analytics.inbox_tagging()
    assert page.enabled is False
    assert page.data == []
    assert list(client.analytics.list_inbox_tagging()) == []


@respx.mock
def test_warmup_placement(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(200, json=WARMUP_PLACEMENT)
    )
    out = client.analytics.warmup_placement(
        email_id="mb-1", from_="2026-10-02", to="2026-10-31"
    )
    params = _last(route).url.params
    assert params["email_id"] == "mb-1"
    assert params["from"] == "2026-10-02"
    assert params["to"] == "2026-10-31"
    _check_warmup_placement(out)

    client.analytics.warmup_placement()
    assert dict(_last(route).url.params) == {}


@pytest.mark.anyio
@respx.mock
async def test_new_reports_async(aclient: AsyncWarmbly) -> None:
    direct = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(200, json=DIRECT)
    )
    _check_direct(await aclient.analytics.direct(period="90d"))
    assert _last(direct).url.params["period"] == "90d"

    tags = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        side_effect=[
            httpx.Response(200, json=_tag_page([TAG], "50")),
            httpx.Response(200, json=_tag_page([{**TAG, "id": "tag-2"}], None)),
        ]
    )
    rows = [r async for r in aclient.analytics.list_inbox_tagging(needs_review=False)]
    assert [r.id for r in rows] == ["tag-1", "tag-2"]
    _check_tag(rows[0])
    assert tags.calls[0].request.url.params["needs_review"] == "false"
    assert tags.calls[1].request.url.params["cursor"] == "50"

    tags.mock(return_value=httpx.Response(200, json=_tag_page([TAG], None)))
    page = await aclient.analytics.inbox_tagging(limit=5)
    assert _last(tags).url.params["limit"] == "5"
    assert page.summary.total == 3
    _check_tag(page.data[0])

    wp = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(200, json=WARMUP_PLACEMENT)
    )
    _check_warmup_placement(await aclient.analytics.warmup_placement(to="2026-10-31"))
    assert _last(wp).url.params["to"] == "2026-10-31"


# ----------------------------------------- params of the existing reports


@respx.mock
def test_existing_reports_send_the_params_the_server_reads(client: Warmbly) -> None:
    dash = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json={"totals": {"sent": 1}})
    )
    client.analytics.dashboard(period="30d", campaign_ids=["a", "b"], folder_ids=["f"])
    params = _last(dash).url.params
    assert params["period"] == "30d"
    assert params["campaign_ids"] == "a,b"
    assert params["folder_ids"] == "f"

    warmup = respx.get(f"{BASE_URL}/analytics/warmup").mock(
        return_value=httpx.Response(200, json={"summary": {}})
    )
    client.analytics.warmup(email_id="mb-1", from_="2026-10-01", to="2026-10-31")
    assert _last(warmup).url.params["email_id"] == "mb-1"

    compare = respx.get(f"{BASE_URL}/analytics/campaigns/compare").mock(
        return_value=httpx.Response(200, json={})
    )
    client.analytics.compare_campaigns(
        ids=["c1", "c2"], from_="2026-10-01", to="2026-10-31"
    )
    assert _last(compare).url.params["ids"] == "c1,c2"

    hourly = respx.get(f"{BASE_URL}/analytics/campaigns/c1/hourly").mock(
        return_value=httpx.Response(200, json={"date": "2026-10-30", "data": []})
    )
    assert client.analytics.campaign_hourly("c1", date="2026-10-30").data == []
    assert _last(hourly).url.params["date"] == "2026-10-30"

    usage = respx.get(f"{BASE_URL}/analytics/usage").mock(
        return_value=httpx.Response(200, json={})
    )
    client.analytics.usage(period="week")
    assert _last(usage).url.params["period"] == "week"


ACCOUNT = {
    "id": "mb-1",
    "email": "sam@acme.io",
    "provider": "google",
    "status": "active",
    "last_synced_at": None,
    "health": {"score": 91},
    "errors": [],
    "daily_usage": {"sent": 12, "limit": 50},
    "in_campaign": True,
    "cold_ramp": {
        "ceiling": 30,
        "mailbox_cap": 50,
        "days_to_full_cap": 4,
        "held": False,
    },
    "send_recovery_reason": "authentication",
}


def _check_account(a: Any) -> None:
    assert a.id == "mb-1"
    assert (a.email, a.provider, a.status) == ("sam@acme.io", "google", "active")
    assert a.last_synced_at is None
    assert a.health == {"score": 91}
    assert a.daily_usage["sent"] == 12
    assert a.in_campaign is True
    assert a.cold_ramp["days_to_full_cap"] == 4
    assert a.send_recovery_reason == "authentication"
    assert a.warmup_health is None


@respx.mock
def test_accounts_are_paged(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/accounts").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [ACCOUNT],
                    "pagination": {
                        "total": None,
                        "next_cursor": "k2",
                        "has_more": True,
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**ACCOUNT, "id": "mb-2"}],
                    "pagination": {
                        "total": None,
                        "next_cursor": None,
                        "has_more": False,
                    },
                },
            ),
        ]
    )
    rows = list(client.analytics.list_accounts(email_ids=["mb-1", "mb-2"], limit=1))
    assert [r.id for r in rows] == ["mb-1", "mb-2"]
    _check_account(rows[0])
    first, second = (c.request for c in route.calls)
    assert first.url.params["email_ids"] == "mb-1,mb-2"
    assert first.url.params["limit"] == "1"
    assert second.url.params["cursor"] == "k2"

    route.mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [ACCOUNT],
                "pagination": {"total": None, "next_cursor": "k2", "has_more": True},
            },
        )
    )
    one = client.analytics.accounts(limit=1, cursor="k1")
    assert _last(route).url.params["cursor"] == "k1"
    assert one.data[0]["id"] == "mb-1"
    assert one.pagination["next_cursor"] == "k2"


@pytest.mark.anyio
@respx.mock
async def test_accounts_are_paged_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/accounts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [ACCOUNT],
                "pagination": {"total": None, "next_cursor": None, "has_more": False},
            },
        )
    )
    rows = [r async for r in aclient.analytics.list_accounts(email_ids=["mb-1"])]
    _check_account(rows[0])
    assert _last(route).url.params["email_ids"] == "mb-1"

    dash = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json={})
    )
    await aclient.analytics.dashboard(period="90d", folder_ids=["f1", "f2"])
    assert _last(dash).url.params["folder_ids"] == "f1,f2"
