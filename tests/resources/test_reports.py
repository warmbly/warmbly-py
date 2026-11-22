"""Tests for the ``reports`` resource (client reports), sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.reports import (
    Report,
    ReportDeleted,
    ReportLinkCreated,
    ReportPreview,
)

BASE_URL = "https://api.warmbly.com/v1"
RID = "7d1f0c4e-2b8a-4a51-9a51-3c0c9a1f6b20"


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


def _report(**overrides: Any) -> dict[str, Any]:
    """A ``models.ClientReport`` as the server encodes it."""
    data: dict[str, Any] = {
        "id": RID,
        "created_by": "0b6a8d6e-6f0a-4d0e-8f37-1c2d3e4f5a6b",
        "name": "Acme monthly",
        "access": {
            "scope": "restricted",
            "campaign_folder_ids": [],
            "campaign_ids": ["c1a2b3c4-0000-4000-8000-000000000001"],
            "email_account_ids": [],
        },
        "sections": {
            "overview": True,
            "campaigns": True,
            "replies": True,
            "positive_replies": False,
            "mailboxes": True,
            "daily_chart": True,
        },
        "show_reply_snippets": False,
        "date_range": "last_30_days",
        "link": {
            "hint": "r7Kq",
            "created_at": "2026-11-01T10:00:00Z",
            "expires_at": "2027-01-30T10:00:00Z",
            "expired": False,
        },
        "schedule": {
            "recipients": ["client@acme.test"],
            "cadence": "monthly",
            "weekday": 0,
            "month_day": 1,
            "hour": 9,
            "timezone": "Europe/London",
            "paused": False,
            "last_sent_at": None,
            "next_run_at": "2026-12-01T09:00:00Z",
        },
        "created_at": "2026-11-01T09:00:00Z",
        "updated_at": "2026-11-02T09:00:00Z",
    }
    data.update(overrides)
    return data


PREVIEW: dict[str, Any] = {
    "name": "Acme monthly",
    "date_range": "last_7_days",
    "from": "2026-11-09",
    "to": "2026-11-15",
    "generated_at": "2026-11-15T12:00:00Z",
    "sections": {
        "overview": True,
        "campaigns": True,
        "replies": True,
        "positive_replies": True,
        "mailboxes": True,
        "daily_chart": True,
    },
    "show_reply_snippets": True,
    "overview": {
        "sent": 1200,
        "opened": 540,
        "open_tracked_sent": 1000,
        "open_rate": 54.0,
        "clicked": 31,
        "replied": 48,
        "reply_rate": 4.0,
        "positive": 12,
        "positive_rate": 1.0,
        "bounced": 6,
        "bounce_rate": 0.5,
    },
    "daily": [{"date": "2026-11-09", "sent": 170, "opens": 80, "replies": 7}],
    "campaigns": [
        {
            "name": "Q4 outbound",
            "status": "active",
            "sent": 1200,
            "opens": 540,
            "open_tracked_sent": 1000,
            "open_rate": 54.0,
            "clicks": 31,
            "replies": 48,
            "reply_rate": 4.0,
            "positive": 12,
            "bounces": 6,
            "bounce_rate": 0.5,
        }
    ],
    "replies": [
        {
            "name": "Jane Roe",
            "email": "jane@prospect.test",
            "campaign": "Q4 outbound",
            "subject": "Re: quick question",
            "replied_at": "2026-11-14T15:30:00Z",
            "classification": "interested",
            "snippet": "Sounds good, let's talk Tuesday.",
        }
    ],
    "mailboxes": {
        "total": 5,
        "healthy": 4,
        "warning": 1,
        "error": 0,
        "warmup_sent": 300,
        "warmup_received": 290,
        "warmup_replied": 80,
    },
}

LINK: dict[str, Any] = {
    "url": "https://portal.warmbly.test/r/r7KqSecretToken",
    "token": "r7KqSecretToken",
    "link": {
        "hint": "r7Kq",
        "created_at": "2026-11-15T12:00:00Z",
        "expires_at": "2026-12-15T12:00:00Z",
        "expired": False,
    },
    "report": _report(),
}

PAGE: dict[str, Any] = {
    "data": [_report()],
    "pagination": {"next_cursor": None, "has_more": False},
}

CREATE_BODY: dict[str, Any] = {
    "name": "Acme monthly",
    "access": {"scope": "restricted", "campaign_ids": ["c1"]},
    "sections": {"overview": True, "replies": True},
    "show_reply_snippets": True,
    "date_range": "this_month",
}

SCHEDULE_BODY: dict[str, Any] = {
    "recipients": ["client@acme.test"],
    "cadence": "weekly",
    "weekday": 1,
    "month_day": 1,
    "hour": 9,
    "timezone": "Europe/London",
    "paused": False,
}


def _body(route: respx.Route) -> Any:
    return json.loads(route.calls.last.request.content)


def _assert_report(report: Report) -> None:
    assert isinstance(report, Report)
    assert report.id == RID
    assert report.name == "Acme monthly"
    assert report.created_by is not None
    assert report.access is not None
    assert report.access.scope == "restricted"
    assert report.access.campaign_ids == ["c1a2b3c4-0000-4000-8000-000000000001"]
    assert report.access.campaign_folder_ids == []
    assert report.sections is not None
    assert report.sections.overview is True
    assert report.sections.positive_replies is False
    assert report.sections.daily_chart is True
    assert report.show_reply_snippets is False
    assert report.date_range == "last_30_days"
    assert report.link is not None
    assert report.link.hint == "r7Kq"
    assert report.link.expires_at == "2027-01-30T10:00:00Z"
    assert report.link.expired is False
    assert report.schedule is not None
    assert report.schedule.cadence == "monthly"
    assert report.schedule.recipients == ["client@acme.test"]
    assert report.schedule.month_day == 1
    assert report.schedule.hour == 9
    assert report.schedule.timezone == "Europe/London"
    assert report.schedule.last_sent_at is None
    assert report.schedule.next_run_at == "2026-12-01T09:00:00Z"
    assert report.created_at and report.updated_at


def _assert_preview(view: ReportPreview) -> None:
    assert isinstance(view, ReportPreview)
    assert view.name == "Acme monthly"
    assert view.from_ == "2026-11-09"
    assert view.to == "2026-11-15"
    assert view.generated_at == "2026-11-15T12:00:00Z"
    assert view.sections is not None and view.sections.mailboxes is True
    assert view.overview is not None
    assert view.overview.open_tracked_sent == 1000
    assert view.overview.positive_rate == 1.0
    assert view.overview.bounce_rate == 0.5
    assert view.daily is not None and view.daily[0].opens == 80
    assert view.campaigns is not None
    assert view.campaigns[0].status == "active"
    assert view.campaigns[0].positive == 12
    assert view.replies is not None
    assert view.replies[0].classification == "interested"
    assert view.replies[0].snippet
    assert view.mailboxes is not None and view.mailboxes.warmup_replied == 80


def _assert_link(created: ReportLinkCreated) -> None:
    assert isinstance(created, ReportLinkCreated)
    assert created.url == LINK["url"]
    assert created.token == LINK["token"]
    assert created.link is not None and created.link.hint == "r7Kq"
    assert created.report is not None and created.report.id == RID
    # Bearer secrets stay out of repr.
    assert "r7KqSecretToken" not in repr(created)


# -- list -------------------------------------------------------------------


@respx.mock
def test_list_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/reports").mock(
        return_value=httpx.Response(200, json=PAGE)
    )
    reports = list(client.reports.list(limit=10, cursor="abc"))
    assert len(reports) == 1
    _assert_report(reports[0])
    params = route.calls.last.request.url.params
    assert params["limit"] == "10"
    assert params["cursor"] == "abc"


@respx.mock
@pytest.mark.anyio
async def test_list_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/reports").mock(
        return_value=httpx.Response(200, json=PAGE)
    )
    reports = [r async for r in aclient.reports.list(limit=10)]
    assert len(reports) == 1
    _assert_report(reports[0])
    params = route.calls.last.request.url.params
    assert params["limit"] == "10"
    assert "cursor" not in params


# -- create -----------------------------------------------------------------


@respx.mock
def test_create_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/reports").mock(
        return_value=httpx.Response(201, json=_report())
    )
    report = client.reports.create(**CREATE_BODY)
    _assert_report(report)
    assert _body(route) == CREATE_BODY
    assert route.calls.last.request.headers.get("idempotency-key")


@respx.mock
@pytest.mark.anyio
async def test_create_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/reports").mock(
        return_value=httpx.Response(201, json=_report())
    )
    report = await aclient.reports.create(name="Acme monthly")
    _assert_report(report)
    assert _body(route) == {"name": "Acme monthly"}
    assert route.calls.last.request.headers.get("idempotency-key")


# -- retrieve ---------------------------------------------------------------


@respx.mock
def test_retrieve_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/reports/{RID}").mock(
        return_value=httpx.Response(200, json=_report())
    )
    _assert_report(client.reports.retrieve(RID))
    assert route.calls.last.request.method == "GET"


@respx.mock
@pytest.mark.anyio
async def test_retrieve_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/reports/{RID}").mock(
        return_value=httpx.Response(200, json=_report())
    )
    _assert_report(await aclient.reports.retrieve(RID))
    assert route.calls.last.request.method == "GET"


# -- preview ----------------------------------------------------------------


@respx.mock
def test_preview_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/reports/{RID}/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    _assert_preview(client.reports.preview(RID, range="last_7_days"))
    assert route.calls.last.request.url.params["range"] == "last_7_days"


@respx.mock
@pytest.mark.anyio
async def test_preview_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/reports/{RID}/preview").mock(
        return_value=httpx.Response(200, json=PREVIEW)
    )
    _assert_preview(await aclient.reports.preview(RID))
    assert "range" not in route.calls.last.request.url.params


# -- update -----------------------------------------------------------------


@respx.mock
def test_update_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/reports/{RID}").mock(
        return_value=httpx.Response(200, json=_report())
    )
    report = client.reports.update(RID, name="Renamed", date_range="last_month")
    _assert_report(report)
    assert _body(route) == {"name": "Renamed", "date_range": "last_month"}


@respx.mock
@pytest.mark.anyio
async def test_update_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/reports/{RID}").mock(
        return_value=httpx.Response(200, json=_report())
    )
    report = await aclient.reports.update(RID, **CREATE_BODY)
    _assert_report(report)
    assert _body(route) == CREATE_BODY


# -- delete -----------------------------------------------------------------


@respx.mock
def test_delete_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/reports/{RID}").mock(
        return_value=httpx.Response(204)
    )
    result = client.reports.delete(RID)
    assert isinstance(result, ReportDeleted)
    assert result.id is None
    assert route.calls.last.request.method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_delete_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/reports/{RID}").mock(
        return_value=httpx.Response(204)
    )
    result = await aclient.reports.delete(RID)
    assert isinstance(result, ReportDeleted)
    assert result.deleted is None
    assert route.calls.last.request.method == "DELETE"


# -- share link -------------------------------------------------------------


@respx.mock
def test_create_link_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/reports/{RID}/link").mock(
        return_value=httpx.Response(201, json=LINK)
    )
    _assert_link(client.reports.create_link(RID, expires_in_days=30))
    assert _body(route) == {"expires_in_days": 30}
    assert route.calls.last.request.headers.get("idempotency-key")


@respx.mock
@pytest.mark.anyio
async def test_create_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/reports/{RID}/link").mock(
        return_value=httpx.Response(201, json=LINK)
    )
    _assert_link(await aclient.reports.create_link(RID))
    assert _body(route) == {}


@respx.mock
def test_revoke_link_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/reports/{RID}/link").mock(
        return_value=httpx.Response(200, json=_report())
    )
    _assert_report(client.reports.revoke_link(RID))
    assert route.calls.last.request.method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_revoke_link_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/reports/{RID}/link").mock(
        return_value=httpx.Response(200, json=_report())
    )
    _assert_report(await aclient.reports.revoke_link(RID))
    assert route.calls.last.request.method == "DELETE"


# -- schedule ---------------------------------------------------------------


@respx.mock
def test_set_schedule_sync(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/reports/{RID}/schedule").mock(
        return_value=httpx.Response(200, json=_report())
    )
    _assert_report(client.reports.set_schedule(RID, **SCHEDULE_BODY))
    assert route.calls.last.request.method == "PUT"
    assert _body(route) == SCHEDULE_BODY


@respx.mock
@pytest.mark.anyio
async def test_set_schedule_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/reports/{RID}/schedule").mock(
        return_value=httpx.Response(200, json=_report())
    )
    report = await aclient.reports.set_schedule(
        RID, recipients=("client@acme.test",), cadence="monthly"
    )
    _assert_report(report)
    assert route.calls.last.request.method == "PUT"
    assert _body(route) == {"recipients": ["client@acme.test"], "cadence": "monthly"}


@respx.mock
def test_delete_schedule_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/reports/{RID}/schedule").mock(
        return_value=httpx.Response(200, json=_report(schedule=None))
    )
    report = client.reports.delete_schedule(RID)
    assert report.id == RID
    assert report.schedule is None
    assert report.link is not None
    assert route.calls.last.request.method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_delete_schedule_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/reports/{RID}/schedule").mock(
        return_value=httpx.Response(200, json=_report(schedule=None))
    )
    report = await aclient.reports.delete_schedule(RID)
    assert report.id == RID
    assert report.schedule is None
    assert report.name == "Acme monthly"
    assert route.calls.last.request.method == "DELETE"
