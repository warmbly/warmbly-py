"""Tests for the campaign routes added by the 2026-10 server sync, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CAMPAIGN = "11111111-1111-4111-8111-111111111111"
CONTACT = "22222222-2222-4222-8222-222222222222"
MONITOR_ID = "33333333-3333-4333-8333-333333333333"


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


MONITOR: dict[str, Any] = {
    "id": MONITOR_ID,
    "campaign_id": CAMPAIGN,
    "created_by": CONTACT,
    "enabled": True,
    "interval_days": 7,
    "panel": "workspace",
    "alert_below": 60,
    "pause_on_alert": True,
    "next_run_at": "2026-10-26T09:00:00Z",
    "last_run_at": "2026-10-19T09:00:00Z",
    "last_test_id": CONTACT,
    "last_alert_at": None,
    "last_error": "no seed",
    "created_at": "2026-10-01T09:00:00Z",
    "updated_at": "2026-10-19T09:00:00Z",
}

SEND_PLAN: dict[str, Any] = {
    "campaign_id": CAMPAIGN,
    "status": "active",
    "day": "2026-10-25",
    "timezone": "Europe/Berlin",
    "computed_at": "2026-10-25T08:00:00Z",
    "stale": True,
    "configured_ceiling": 100,
    "projected_today": 70,
    "sent_today": 20,
    "expected_remaining": 50,
    "bottleneck": "warmup_graduation",
    "limits": [
        {"kind": "warmup_graduation", "emails": 30, "mailboxes": 2},
        {"kind": "campaign_daily_limit", "emails": 0},
    ],
    "window": {
        "sending_day": True,
        "open_now": False,
        "opens_at": "2026-10-25T09:00:00Z",
        "closes_at": "2026-10-25T17:00:00Z",
        "minutes_left": 480,
        "starts_at": "2026-10-20T00:00:00Z",
        "ends_at": "2026-11-20T00:00:00Z",
    },
    "leads": {
        "due_now": 5,
        "due_later_today": 6,
        "new_leads_due_today": 4,
        "waiting_on_step": 7,
        "waiting_on_condition": 1,
        "held": 2,
        "waiting_on_sender": 3,
        "new_leads_started_today": 9,
        "max_new_leads_per_day": 25,
        "next_due_at": "2026-10-26T09:00:00Z",
    },
    "mailboxes": [
        {
            "id": MONITOR_ID,
            "email": "ann@acme.test",
            "provider": "google",
            "configured_cap": 50,
            "cap_today": 20,
            "limited_by": "warmup_graduation",
            "sent_today": 10,
            "sent_by_other_campaigns": 2,
            "expected_remaining": 8,
            "state": "sending",
            "reopens_at": "2026-10-26T09:00:00Z",
            "health": "watch",
            "min_gap_seconds": 90,
            "graduation": {
                "ceiling": 20,
                "mailbox_cap": 50,
                "days_to_full_cap": 6,
                "held": False,
            },
        }
    ],
    "organization": {"daily_limit": 500, "sent_today": 120, "remaining": 380},
    "next_wake_at": "2026-10-25T08:05:00Z",
}

HOLD: dict[str, Any] = {
    "campaign_id": CAMPAIGN,
    "contact_id": CONTACT,
    "hold": {
        "since": "2026-10-25T08:00:00Z",
        "until": "2026-11-01T00:00:00Z",
        "reason": "on leave",
        "source": "manual",
    },
}

CC: dict[str, Any] = {
    "campaign_id": CAMPAIGN,
    "contact_id": CONTACT,
    "cc": [
        {
            "contact_id": MONITOR_ID,
            "email": "bob@acme.test",
            "first_name": "Bob",
            "last_name": "Ray",
            "company": "Acme",
            "status": "bounced",
            "bounced_at": "2026-10-20T00:00:00Z",
        }
    ],
}

SUGGESTIONS: dict[str, Any] = {
    "data": [
        {
            "contact_id": MONITOR_ID,
            "email": "cy@acme.test",
            "first_name": "Cy",
            "last_name": "Lu",
            "company": "Acme",
            "reason": "domain",
        }
    ]
}

IMAGE: dict[str, Any] = {
    "id": MONITOR_ID,
    "organization_id": CAMPAIGN,
    "user_id": CONTACT,
    "filename": "logo.png",
    "mime_type": "image/png",
    "size": 2048,
    "width": 640,
    "height": 480,
    "url": "https://api.warmbly.com/public/email-images/o/x.png",
    "created_at": "2026-10-25T08:00:00Z",
}

ESTIMATE: dict[str, Any] = {
    "recipients": 300,
    "mailboxes": 3,
    "daily_capacity": 90,
    "remaining_today": 60,
    "sending_days": 4,
    "estimated_finish_at": "2026-10-30T00:00:00Z",
    "steps": 3,
    "total_sends": 900,
    "first_touch_finish_at": "2026-10-29T00:00:00Z",
    "steady_capacity": 150,
    "full_capacity_at": "2026-11-05T00:00:00Z",
    "ramping": 2,
    "held": 1,
    "warmup": {"mailboxes": 3, "per_day": 15},
    "other_campaigns_per_day": 12,
    "bottleneck": "warmup_graduation",
    "timeline": [
        {
            "date": "2026-10-26",
            "sending_day": True,
            "capacity": 90,
            "sends": 80,
            "first_emails": 60,
            "follow_ups": 20,
            "warmup": 15,
        }
    ],
    "senders": [
        {
            "id": MONITOR_ID,
            "email": "ann@acme.test",
            "provider": "google",
            "state": "ramping",
            "first_day_cap": 10,
            "steady_cap": 50,
            "warmup_per_day": 5,
            "full_cap_at": "2026-11-05T00:00:00Z",
        }
    ],
}


def _check_monitor(result: Any) -> None:
    monitor = result.data
    assert monitor.id == MONITOR_ID
    assert monitor.campaign_id == CAMPAIGN
    assert monitor.enabled is True
    assert monitor.interval_days == 7
    assert monitor.panel == "workspace"
    assert monitor.alert_below == 60
    assert monitor.pause_on_alert is True
    assert monitor.next_run_at == "2026-10-26T09:00:00Z"
    assert monitor.last_test_id == CONTACT
    assert monitor.last_error == "no seed"


def _check_plan(plan: Any) -> None:
    assert plan.campaign_id == CAMPAIGN
    assert plan.stale is True
    assert plan.timezone == "Europe/Berlin"
    assert plan.configured_ceiling == 100
    assert plan.projected_today == 70
    assert plan.expected_remaining == 50
    assert plan.bottleneck == "warmup_graduation"
    assert [(i.kind, i.emails, i.mailboxes) for i in plan.limits] == [
        ("warmup_graduation", 30, 2),
        ("campaign_daily_limit", 0, None),
    ]
    assert plan.window.open_now is False
    assert plan.window.minutes_left == 480
    assert plan.window.ends_at == "2026-11-20T00:00:00Z"
    assert plan.leads.due_now == 5
    assert plan.leads.waiting_on_sender == 3
    assert plan.leads.max_new_leads_per_day == 25
    box = plan.mailboxes[0]
    assert box.limited_by == "warmup_graduation"
    assert box.sent_by_other_campaigns == 2
    assert box.min_gap_seconds == 90
    assert box.graduation.days_to_full_cap == 6
    assert plan.organization.remaining == 380
    assert plan.next_wake_at == "2026-10-25T08:05:00Z"


def _check_hold(result: Any) -> None:
    assert result.campaign_id == CAMPAIGN
    assert result.contact_id == CONTACT
    assert result.hold.source == "manual"
    assert result.hold.until == "2026-11-01T00:00:00Z"
    assert result.hold.reason == "on leave"


def _check_cc(result: Any) -> None:
    assert result.contact_id == CONTACT
    assert result.cc[0].email == "bob@acme.test"
    assert result.cc[0].status == "bounced"
    assert result.cc[0].bounced_at == "2026-10-20T00:00:00Z"


def _check_estimate(estimate: Any) -> None:
    assert estimate.steps == 3
    assert estimate.total_sends == 900
    assert estimate.first_touch_finish_at == "2026-10-29T00:00:00Z"
    assert estimate.steady_capacity == 150
    assert estimate.ramping == 2
    assert estimate.warmup.per_day == 15
    assert estimate.other_campaigns_per_day == 12
    assert estimate.bottleneck == "warmup_graduation"
    assert estimate.timeline[0].first_emails == 60
    assert estimate.senders[0].state == "ramping"
    assert estimate.senders[0].steady_cap == 50


# ---------------------------------------------------------------------------
# placement monitor
# ---------------------------------------------------------------------------
@respx.mock
def test_placement_monitor_sync(client: Warmbly) -> None:
    path = f"{BASE_URL}/campaigns/{CAMPAIGN}/placement-monitor"
    read = respx.get(path).mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    _check_monitor(client.campaigns.placement_monitor(CAMPAIGN))
    assert _last(read).method == "GET"

    respx.get(path).mock(return_value=httpx.Response(200, json={"data": None}))
    assert client.campaigns.placement_monitor(CAMPAIGN).data is None

    write = respx.put(path).mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    _check_monitor(
        client.campaigns.set_placement_monitor(
            CAMPAIGN,
            enabled=True,
            interval_days=7,
            panel="workspace",
            alert_below=60,
            pause_on_alert=True,
        )
    )
    assert _last(write).method == "PUT"
    assert json.loads(_last(write).content) == {
        "enabled": True,
        "interval_days": 7,
        "panel": "workspace",
        "alert_below": 60,
        "pause_on_alert": True,
    }
    client.campaigns.set_placement_monitor(CAMPAIGN, enabled=False)
    assert json.loads(_last(write).content) == {"enabled": False}

    gone = respx.delete(path).mock(return_value=httpx.Response(204))
    assert client.campaigns.delete_placement_monitor(CAMPAIGN).deleted is None
    assert _last(gone).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_async(aclient: AsyncWarmbly) -> None:
    path = f"{BASE_URL}/campaigns/{CAMPAIGN}/placement-monitor"
    respx.get(path).mock(return_value=httpx.Response(200, json={"data": MONITOR}))
    _check_monitor(await aclient.campaigns.placement_monitor(CAMPAIGN))
    write = respx.put(path).mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    _check_monitor(
        await aclient.campaigns.set_placement_monitor(
            CAMPAIGN, panel="cloud", alert_below=40, pause_on_alert=False
        )
    )
    assert json.loads(_last(write).content) == {
        "panel": "cloud",
        "alert_below": 40,
        "pause_on_alert": False,
    }
    gone = respx.delete(path).mock(return_value=httpx.Response(204))
    await aclient.campaigns.delete_placement_monitor(CAMPAIGN)
    assert _last(gone).method == "DELETE"


# ---------------------------------------------------------------------------
# send plan
# ---------------------------------------------------------------------------
@respx.mock
def test_send_plan_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/{CAMPAIGN}/send-plan").mock(
        return_value=httpx.Response(200, json=SEND_PLAN)
    )
    _check_plan(client.campaigns.send_plan(CAMPAIGN))
    assert _last(route).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_send_plan_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/{CAMPAIGN}/send-plan").mock(
        return_value=httpx.Response(200, json=SEND_PLAN)
    )
    _check_plan(await aclient.campaigns.send_plan(CAMPAIGN))


# ---------------------------------------------------------------------------
# per-lead hold
# ---------------------------------------------------------------------------
@respx.mock
def test_lead_hold_sync(client: Warmbly) -> None:
    base = f"{BASE_URL}/campaigns/{CAMPAIGN}/leads/{CONTACT}"
    read = respx.get(f"{base}/hold").mock(return_value=httpx.Response(200, json=HOLD))
    _check_hold(client.campaigns.lead_hold(CAMPAIGN, CONTACT))
    assert _last(read).method == "GET"

    pause = respx.post(f"{base}/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    _check_hold(
        client.campaigns.pause_lead(
            CAMPAIGN, CONTACT, until="2026-11-01T00:00:00Z", reason="on leave"
        )
    )
    assert _last(pause).method == "POST"
    assert json.loads(_last(pause).content) == {
        "until": "2026-11-01T00:00:00Z",
        "reason": "on leave",
    }
    assert _last(pause).headers.get("idempotency-key")

    # No arguments: an open-ended hold, sent with no body at all.
    client.campaigns.pause_lead(CAMPAIGN, CONTACT)
    assert _last(pause).content == b""

    resume = respx.post(f"{base}/resume").mock(
        return_value=httpx.Response(
            200, json={"campaign_id": CAMPAIGN, "contact_id": CONTACT}
        )
    )
    result = client.campaigns.resume_lead(CAMPAIGN, CONTACT)
    assert _last(resume).method == "POST"
    assert result.contact_id == CONTACT
    assert result.hold is None


@pytest.mark.anyio
@respx.mock
async def test_lead_hold_async(aclient: AsyncWarmbly) -> None:
    base = f"{BASE_URL}/campaigns/{CAMPAIGN}/leads/{CONTACT}"
    respx.get(f"{base}/hold").mock(return_value=httpx.Response(200, json=HOLD))
    _check_hold(await aclient.campaigns.lead_hold(CAMPAIGN, CONTACT))
    pause = respx.post(f"{base}/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    _check_hold(await aclient.campaigns.pause_lead(CAMPAIGN, CONTACT, reason="x"))
    assert json.loads(_last(pause).content) == {"reason": "x"}
    await aclient.campaigns.pause_lead(CAMPAIGN, CONTACT)
    assert _last(pause).content == b""
    respx.post(f"{base}/resume").mock(return_value=httpx.Response(200, json=HOLD))
    _check_hold(await aclient.campaigns.resume_lead(CAMPAIGN, CONTACT))


# ---------------------------------------------------------------------------
# per-lead CC
# ---------------------------------------------------------------------------
@respx.mock
def test_lead_cc_sync(client: Warmbly) -> None:
    base = f"{BASE_URL}/campaigns/{CAMPAIGN}/leads/{CONTACT}/cc"
    read = respx.get(base).mock(return_value=httpx.Response(200, json=CC))
    _check_cc(client.campaigns.lead_cc(CAMPAIGN, CONTACT))
    assert _last(read).method == "GET"

    write = respx.put(base).mock(return_value=httpx.Response(200, json=CC))
    _check_cc(client.campaigns.set_lead_cc(CAMPAIGN, CONTACT, contact_ids=[MONITOR_ID]))
    assert _last(write).method == "PUT"
    assert json.loads(_last(write).content) == {"contact_ids": [MONITOR_ID]}

    suggestions = respx.get(f"{base}/suggestions").mock(
        return_value=httpx.Response(200, json=SUGGESTIONS)
    )
    got = client.campaigns.lead_cc_suggestions(CAMPAIGN, CONTACT)
    assert _last(suggestions).method == "GET"
    assert got.data[0].email == "cy@acme.test"
    assert got.data[0].reason == "domain"
    assert got.data[0].first_name == "Cy"


@pytest.mark.anyio
@respx.mock
async def test_lead_cc_async(aclient: AsyncWarmbly) -> None:
    base = f"{BASE_URL}/campaigns/{CAMPAIGN}/leads/{CONTACT}/cc"
    respx.get(base).mock(return_value=httpx.Response(200, json=CC))
    _check_cc(await aclient.campaigns.lead_cc(CAMPAIGN, CONTACT))
    write = respx.put(base).mock(return_value=httpx.Response(200, json=CC))
    _check_cc(await aclient.campaigns.set_lead_cc(CAMPAIGN, CONTACT, contact_ids=[]))
    assert json.loads(_last(write).content) == {"contact_ids": []}
    respx.get(f"{base}/suggestions").mock(
        return_value=httpx.Response(200, json=SUGGESTIONS)
    )
    got = await aclient.campaigns.lead_cc_suggestions(CAMPAIGN, CONTACT)
    assert got.data[0].company == "Acme"


# ---------------------------------------------------------------------------
# email image library
# ---------------------------------------------------------------------------
def _page(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {"data": data, "pagination": {"next_cursor": None, "has_more": False}}


@respx.mock
def test_email_images_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(200, json=_page([IMAGE]))
    )
    images = list(client.campaigns.list_email_images(limit=10))
    assert _last(listing).url.params.get("limit") == "10"
    assert images[0].filename == "logo.png"
    assert images[0].mime_type == "image/png"
    assert images[0].width == 640
    assert images[0].height == 480
    assert images[0].url.endswith("x.png")

    upload = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    image = client.campaigns.upload_email_image(
        file=b"\x89PNG", filename="logo.png", content_type="image/png"
    )
    request = _last(upload)
    assert request.method == "POST"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="logo.png"' in request.content
    assert image.size == 2048

    gone = respx.delete(f"{BASE_URL}/email-images/{MONITOR_ID}").mock(
        return_value=httpx.Response(204)
    )
    client.campaigns.delete_email_image(MONITOR_ID)
    assert _last(gone).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_email_images_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(200, json=_page([IMAGE]))
    )
    assert [i.id async for i in aclient.campaigns.list_email_images()] == [MONITOR_ID]
    upload = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    image = await aclient.campaigns.upload_email_image(file=b"x", filename="a.png")
    assert b'filename="a.png"' in _last(upload).content
    assert image.height == 480
    gone = respx.delete(f"{BASE_URL}/email-images/{MONITOR_ID}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.campaigns.delete_email_image(MONITOR_ID)
    assert _last(gone).method == "DELETE"


# ---------------------------------------------------------------------------
# estimate, steps, campaign fields, segments
# ---------------------------------------------------------------------------
@respx.mock
def test_estimate_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    _check_estimate(
        client.campaigns.estimate(
            campaign_id=CAMPAIGN,
            start_time="09:00",
            end_time="17:00",
            step_waits=[2, 5],
        )
    )
    assert json.loads(_last(route).content) == {
        "campaign_id": CAMPAIGN,
        "start_time": "09:00",
        "end_time": "17:00",
        "step_waits": [2, 5],
    }
    client.campaigns.estimate(segment_ids=["seg_1"])
    assert json.loads(_last(route).content) == {"segment_ids": ["seg_1"]}


@pytest.mark.anyio
@respx.mock
async def test_estimate_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    _check_estimate(
        await aclient.campaigns.estimate(
            segment_ids=[], step_waits=[1], campaign_id=CAMPAIGN
        )
    )
    assert json.loads(_last(route).content) == {
        "segment_ids": [],
        "step_waits": [1],
        "campaign_id": CAMPAIGN,
    }
    await aclient.campaigns.estimate()
    assert json.loads(_last(route).content) == {}


STEP: dict[str, Any] = {
    "id": "st_1",
    "name": "Follow up",
    "subject": "Re: Hi",
    "wait_after": 3,
    "thread_reply": False,
    "kind": "email",
}


@respx.mock
def test_steps_thread_reply_sync(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns/{CAMPAIGN}/steps").mock(
        return_value=httpx.Response(201, json=STEP)
    )
    blank = client.campaigns.create_step(CAMPAIGN)
    assert _last(create).content == b""
    assert blank.thread_reply is False

    filled = client.campaigns.create_step(
        CAMPAIGN, name="Follow up", subject="Re: Hi", wait_after=3, thread_reply=False
    )
    assert json.loads(_last(create).content) == {
        "name": "Follow up",
        "subject": "Re: Hi",
        "wait_after": 3,
        "thread_reply": False,
    }
    assert filled.id == "st_1"

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMPAIGN}/steps/st_1").mock(
        return_value=httpx.Response(200, json=STEP)
    )
    client.campaigns.update_step(CAMPAIGN, "st_1", thread_reply=True)
    assert json.loads(_last(update).content) == {"thread_reply": True}


@pytest.mark.anyio
@respx.mock
async def test_steps_thread_reply_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns/{CAMPAIGN}/steps").mock(
        return_value=httpx.Response(201, json=STEP)
    )
    await aclient.campaigns.create_step(CAMPAIGN)
    assert _last(create).content == b""
    await aclient.campaigns.create_step(CAMPAIGN, body_html="<p>x</p>", kind="email")
    assert json.loads(_last(create).content) == {
        "body_html": "<p>x</p>",
        "kind": "email",
    }
    update = respx.patch(f"{BASE_URL}/campaigns/{CAMPAIGN}/steps/st_1").mock(
        return_value=httpx.Response(200, json=STEP)
    )
    await aclient.campaigns.update_step(CAMPAIGN, "st_1", thread_reply=False)
    assert json.loads(_last(update).content) == {"thread_reply": False}


@respx.mock
def test_campaign_entry_delay_and_timezone_sync(client: Warmbly) -> None:
    body = {
        "id": CAMPAIGN,
        "timezone": "",
        "effective_timezone": "Europe/Berlin",
        "entry_delay_minutes": 45,
    }
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=body)
    )
    campaign = client.campaigns.create(name="Q4", entry_delay_minutes=45)
    assert json.loads(_last(create).content) == {
        "name": "Q4",
        "entry_delay_minutes": 45,
    }
    assert campaign.effective_timezone == "Europe/Berlin"
    assert campaign.entry_delay_minutes == 45
    update = respx.patch(f"{BASE_URL}/campaigns/{CAMPAIGN}").mock(
        return_value=httpx.Response(200, json=body)
    )
    client.campaigns.update(CAMPAIGN, entry_delay_minutes=0)
    assert json.loads(_last(update).content) == {"entry_delay_minutes": 0}


@pytest.mark.anyio
@respx.mock
async def test_campaign_entry_delay_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json={"id": CAMPAIGN})
    )
    await aclient.campaigns.create(name="Q4", entry_delay_minutes=10)
    assert json.loads(_last(create).content) == {
        "name": "Q4",
        "entry_delay_minutes": 10,
    }
    update = respx.patch(f"{BASE_URL}/campaigns/{CAMPAIGN}").mock(
        return_value=httpx.Response(200, json={"id": CAMPAIGN})
    )
    await aclient.campaigns.update(CAMPAIGN, entry_delay_minutes=5)
    assert json.loads(_last(update).content) == {"entry_delay_minutes": 5}


@respx.mock
def test_overview_has_no_one_time_bucket(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns-overview").mock(
        return_value=httpx.Response(
            200, json={"total": 4, "active": 1, "paused": 1, "draft": 1, "completed": 1}
        )
    )
    overview = client.campaigns.overview()
    assert overview.total == 4
    assert not hasattr(overview, "one_time")


@respx.mock
def test_set_segments_reports_withdrawn_sync(client: Warmbly) -> None:
    respx.put(f"{BASE_URL}/campaigns/{CAMPAIGN}/segments").mock(
        return_value=httpx.Response(
            200, json={"data": [], "added": 0, "withdrawn": 12, "contacted": 3}
        )
    )
    result = client.campaigns.set_segments(CAMPAIGN, segment_ids=[])
    assert result.withdrawn == 12
    assert result.contacted == 3


@pytest.mark.anyio
@respx.mock
async def test_set_segments_reports_withdrawn_async(aclient: AsyncWarmbly) -> None:
    respx.put(f"{BASE_URL}/campaigns/{CAMPAIGN}/segments").mock(
        return_value=httpx.Response(
            200, json={"data": [], "added": 2, "withdrawn": 1, "contacted": 0}
        )
    )
    result = await aclient.campaigns.set_segments(CAMPAIGN, segment_ids=["s"])
    assert (result.added, result.withdrawn, result.contacted) == (2, 1, 0)
