"""Tests for the campaign placement monitor, send plan and per-lead routes,
plus the campaign shape changes that came with them. Sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CAMP = "5b0b3c1e-4444-4a6e-9d11-000000000004"
CONTACT = "5b0b3c1e-5555-4a6e-9d11-000000000005"
LEAD = f"/campaigns/{CAMP}/leads/{CONTACT}"


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


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


# ------------------------------------------------------- placement monitor

MONITOR = {
    "id": "mon-1",
    "campaign_id": CAMP,
    "created_by": None,
    "enabled": True,
    "interval_days": 7,
    "panel": "instance",
    "alert_below": 70,
    "pause_on_alert": False,
    "next_run_at": "2026-11-02T09:00:00Z",
    "last_run_at": "2026-10-26T09:00:00Z",
    "last_test_id": "t-1",
    "last_alert_at": None,
    "last_error": "The campaign is not running, so nothing was tested.",
    "created_at": "2026-10-01T09:00:00Z",
    "updated_at": "2026-10-26T09:00:00Z",
}


def _check_monitor(m: Any) -> None:
    assert m.id == "mon-1"
    assert m.campaign_id == CAMP
    assert m.created_by is None
    assert m.enabled is True
    assert m.interval_days == 7
    assert m.panel == "instance"
    assert m.alert_below == 70
    assert m.pause_on_alert is False
    assert m.next_run_at == "2026-11-02T09:00:00Z"
    assert m.last_run_at == "2026-10-26T09:00:00Z"
    assert m.last_test_id == "t-1"
    assert m.last_alert_at is None
    assert m.last_error.startswith("The campaign is not running")
    assert m.updated_at == "2026-10-26T09:00:00Z"


@respx.mock
def test_placement_monitor(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/campaigns/{CAMP}/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    _check_monitor(client.campaigns.get_placement_monitor(CAMP).data)
    assert _last(get).method == "GET"

    get.mock(return_value=httpx.Response(200, json={"data": None}))
    assert client.campaigns.get_placement_monitor(CAMP).data is None

    put = respx.put(f"{BASE_URL}/campaigns/{CAMP}/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    out = client.campaigns.set_placement_monitor(
        CAMP,
        enabled=True,
        interval_days=7,
        panel="instance",
        alert_below=70,
        pause_on_alert=False,
    )
    assert _last(put).method == "PUT"
    assert _body(put) == {
        "enabled": True,
        "interval_days": 7,
        "panel": "instance",
        "alert_below": 70,
        "pause_on_alert": False,
    }
    _check_monitor(out.data)

    client.campaigns.set_placement_monitor(CAMP, alert_below=0)
    assert _body(put) == {"alert_below": 0}

    delete = respx.delete(f"{BASE_URL}/campaigns/{CAMP}/placement-monitor").mock(
        return_value=httpx.Response(204)
    )
    result = client.campaigns.delete_placement_monitor(CAMP)
    assert _last(delete).method == "DELETE"
    assert result.deleted is None


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/{CAMP}/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    _check_monitor((await aclient.campaigns.get_placement_monitor(CAMP)).data)

    put = respx.put(f"{BASE_URL}/campaigns/{CAMP}/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    out = await aclient.campaigns.set_placement_monitor(
        CAMP, enabled=False, pause_on_alert=True
    )
    assert _body(put) == {"enabled": False, "pause_on_alert": True}
    _check_monitor(out.data)

    delete = respx.delete(f"{BASE_URL}/campaigns/{CAMP}/placement-monitor").mock(
        return_value=httpx.Response(204)
    )
    await aclient.campaigns.delete_placement_monitor(CAMP)
    assert _last(delete).method == "DELETE"


# ---------------------------------------------------------------- send plan

PLAN = {
    "campaign_id": CAMP,
    "status": "active",
    "day": "2026-10-31",
    "timezone": "Europe/Berlin",
    "computed_at": "2026-10-31T10:00:00Z",
    "stale": False,
    "configured_ceiling": 200,
    "projected_today": 120,
    "sent_today": 40,
    "expected_remaining": 80,
    "bottleneck": "warmup_graduation",
    "limits": [
        {"kind": "warmup_graduation", "emails": 60, "mailboxes": 3},
        {"kind": "leads", "emails": 40},
    ],
    "window": {
        "sending_day": True,
        "open_now": True,
        "closes_at": "2026-10-31T17:00:00Z",
        "minutes_left": 420,
    },
    "leads": {
        "due_now": 30,
        "due_later_today": 10,
        "new_leads_due_today": 25,
        "waiting_on_step": 100,
        "waiting_on_condition": 5,
        "held": 2,
        "waiting_on_sender": 1,
        "new_leads_started_today": 12,
        "max_new_leads_per_day": 0,
    },
    "mailboxes": [
        {
            "id": "mb-1",
            "email": "sam@acme.io",
            "provider": "google",
            "configured_cap": 50,
            "cap_today": 30,
            "limited_by": "warmup_graduation",
            "sent_today": 10,
            "sent_by_other_campaigns": 2,
            "expected_remaining": 18,
            "state": "sending",
            "health": "watch",
            "min_gap_seconds": 60,
            "graduation": {
                "ceiling": 30,
                "mailbox_cap": 50,
                "days_to_full_cap": 4,
                "held": False,
            },
        }
    ],
    "organization": {"daily_limit": 500, "sent_today": 100, "remaining": 400},
}


def _check_plan(p: Any) -> None:
    assert p.campaign_id == CAMP
    assert p.status == "active"
    assert p.day == "2026-10-31"
    assert p.timezone == "Europe/Berlin"
    assert p.computed_at == "2026-10-31T10:00:00Z"
    assert p.stale is False
    assert p.configured_ceiling == 200
    assert p.projected_today == 120
    assert p.sent_today == 40
    assert p.expected_remaining == 80
    assert p.bottleneck == "warmup_graduation"
    assert [limit.kind for limit in p.limits] == ["warmup_graduation", "leads"]
    assert p.limits[0].emails == 60
    assert p.limits[0].mailboxes == 3
    assert p.limits[1].mailboxes is None
    assert p.window.sending_day is True
    assert p.window.open_now is True
    assert p.window.closes_at == "2026-10-31T17:00:00Z"
    assert p.window.minutes_left == 420
    assert p.window.opens_at is None
    assert p.leads.due_now == 30
    assert p.leads.held == 2
    assert p.leads.waiting_on_sender == 1
    assert p.leads.max_new_leads_per_day == 0
    mb = p.mailboxes[0]
    assert (mb.id, mb.email, mb.provider) == ("mb-1", "sam@acme.io", "google")
    assert (mb.configured_cap, mb.cap_today) == (50, 30)
    assert mb.limited_by == "warmup_graduation"
    assert mb.sent_by_other_campaigns == 2
    assert mb.state == "sending"
    assert mb.graduation["days_to_full_cap"] == 4
    assert p.organization.remaining == 400
    assert p.next_wake_at is None


@respx.mock
def test_send_plan(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/{CAMP}/send-plan").mock(
        return_value=httpx.Response(200, json=PLAN)
    )
    _check_plan(client.campaigns.send_plan(CAMP))
    assert _last(route).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_send_plan_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/{CAMP}/send-plan").mock(
        return_value=httpx.Response(200, json=PLAN)
    )
    _check_plan(await aclient.campaigns.send_plan(CAMP))


# ---------------------------------------------------------------- lead hold

HOLD = {
    "campaign_id": CAMP,
    "contact_id": CONTACT,
    "hold": {
        "since": "2026-10-31T09:00:00Z",
        "until": "2026-11-15T00:00:00Z",
        "reason": "On leave",
        "source": "manual",
    },
}
NOT_HELD = {"campaign_id": CAMP, "contact_id": CONTACT}


def _check_hold(h: Any) -> None:
    assert h.campaign_id == CAMP
    assert h.contact_id == CONTACT
    assert h.hold["since"] == "2026-10-31T09:00:00Z"
    assert h.hold["until"] == "2026-11-15T00:00:00Z"
    assert h.hold["reason"] == "On leave"
    assert h.hold["source"] == "manual"


@respx.mock
def test_lead_hold(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}{LEAD}/hold").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    _check_hold(client.campaigns.get_lead_hold(CAMP, CONTACT))
    assert _last(get).method == "GET"

    get.mock(return_value=httpx.Response(200, json=NOT_HELD))
    assert client.campaigns.get_lead_hold(CAMP, CONTACT).hold is None

    pause = respx.post(f"{BASE_URL}{LEAD}/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    out = client.campaigns.pause_lead(
        CAMP, CONTACT, until="2026-11-15T00:00:00Z", reason="On leave"
    )
    assert _last(pause).method == "POST"
    assert _body(pause) == {"until": "2026-11-15T00:00:00Z", "reason": "On leave"}
    _check_hold(out)

    client.campaigns.pause_lead(CAMP, CONTACT)
    assert _last(pause).content == b""

    client.campaigns.pause_lead(CAMP, CONTACT, until=None)
    assert _body(pause) == {"until": None}

    resume = respx.post(f"{BASE_URL}{LEAD}/resume").mock(
        return_value=httpx.Response(200, json=NOT_HELD)
    )
    resumed = client.campaigns.resume_lead(CAMP, CONTACT)
    assert _last(resume).method == "POST"
    assert resumed.contact_id == CONTACT
    assert resumed.hold is None


@pytest.mark.anyio
@respx.mock
async def test_lead_hold_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}{LEAD}/hold").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    _check_hold(await aclient.campaigns.get_lead_hold(CAMP, CONTACT))

    pause = respx.post(f"{BASE_URL}{LEAD}/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    _check_hold(await aclient.campaigns.pause_lead(CAMP, CONTACT, reason="On leave"))
    assert _body(pause) == {"reason": "On leave"}

    resume = respx.post(f"{BASE_URL}{LEAD}/resume").mock(
        return_value=httpx.Response(200, json=NOT_HELD)
    )
    assert (await aclient.campaigns.resume_lead(CAMP, CONTACT)).hold is None
    assert _last(resume).method == "POST"


# ------------------------------------------------------------------ lead cc

CC = {
    "campaign_id": CAMP,
    "contact_id": CONTACT,
    "cc": [
        {
            "contact_id": "c-2",
            "email": "pat@acme.io",
            "first_name": "Pat",
            "last_name": "Lee",
            "company": "Acme",
            "status": "active",
        },
        {
            "contact_id": "c-3",
            "email": "old@acme.io",
            "first_name": "Old",
            "last_name": "Box",
            "status": "bounced",
            "bounced_at": "2026-10-20T08:00:00Z",
        },
    ],
}


def _check_cc(cc: Any) -> None:
    assert cc.campaign_id == CAMP
    assert cc.contact_id == CONTACT
    first, second = cc.cc
    assert first.contact_id == "c-2"
    assert first.email == "pat@acme.io"
    assert (first.first_name, first.last_name) == ("Pat", "Lee")
    assert first.company == "Acme"
    assert first.status == "active"
    assert first.bounced_at is None
    assert second.company is None
    assert second.status == "bounced"
    assert second.bounced_at == "2026-10-20T08:00:00Z"


SUGGESTION = {
    "contact_id": "c-4",
    "email": "kim@acme.io",
    "first_name": "Kim",
    "last_name": "Ng",
    "company": "Acme",
    "reason": "company",
}


@respx.mock
def test_lead_cc(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json=CC)
    )
    _check_cc(client.campaigns.get_lead_cc(CAMP, CONTACT))
    assert _last(get).method == "GET"

    put = respx.put(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json=CC)
    )
    _check_cc(client.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=("c-2", "c-3")))
    assert _last(put).method == "PUT"
    assert _body(put) == {"contact_ids": ["c-2", "c-3"]}

    put.mock(return_value=httpx.Response(200, json={**CC, "cc": []}))
    assert client.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=[]).cc == []
    assert _body(put) == {"contact_ids": []}

    sugg = respx.get(f"{BASE_URL}{LEAD}/cc/suggestions").mock(
        return_value=httpx.Response(200, json={"data": [SUGGESTION]})
    )
    items = list(client.campaigns.suggest_lead_cc(CAMP, CONTACT))
    assert _last(sugg).method == "GET"
    assert items[0].contact_id == "c-4"
    assert items[0].email == "kim@acme.io"
    assert (items[0].first_name, items[0].last_name) == ("Kim", "Ng")
    assert items[0].company == "Acme"
    assert items[0].reason == "company"


@pytest.mark.anyio
@respx.mock
async def test_lead_cc_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}{LEAD}/cc").mock(return_value=httpx.Response(200, json=CC))
    _check_cc(await aclient.campaigns.get_lead_cc(CAMP, CONTACT))

    put = respx.put(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json=CC)
    )
    _check_cc(await aclient.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=["c-2"]))
    assert _body(put) == {"contact_ids": ["c-2"]}

    respx.get(f"{BASE_URL}{LEAD}/cc/suggestions").mock(
        return_value=httpx.Response(200, json={"data": [SUGGESTION]})
    )
    items = [s async for s in aclient.campaigns.suggest_lead_cc(CAMP, CONTACT)]
    assert items[0].reason == "company"
    assert items[0].email == "kim@acme.io"


# ---------------------------------------------- campaign shape and drift


@respx.mock
def test_campaign_shape_changes(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/{CAMP}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": CAMP,
                "status": "draft",
                "timezone": "",
                "effective_timezone": "Europe/Berlin",
                "entry_delay_minutes": 90,
            },
        )
    )
    c = client.campaigns.retrieve(CAMP)
    assert c.timezone == ""
    assert c.effective_timezone == "Europe/Berlin"
    assert c.entry_delay_minutes == 90

    upd = respx.patch(f"{BASE_URL}/campaigns/{CAMP}").mock(
        return_value=httpx.Response(200, json={"id": CAMP, "entry_delay_minutes": 15})
    )
    assert (
        client.campaigns.update(CAMP, entry_delay_minutes=15).entry_delay_minutes == 15
    )
    assert _body(upd) == {"entry_delay_minutes": 15}

    respx.get(f"{BASE_URL}/campaigns-overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 4,
                "active": 1,
                "paused": 1,
                "draft": 1,
                "completed": 1,
                "folders": [{"id": "f1", "name": "Q4", "count": 2}],
            },
        )
    )
    overview = client.campaigns.overview()
    assert overview.total == 4
    assert overview.folders[0]["name"] == "Q4"


@respx.mock
def test_step_thread_reply(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/campaigns/{CAMP}/steps/st-1").mock(
        return_value=httpx.Response(
            200, json={"id": "st-1", "thread_reply": False, "wait_after": 2}
        )
    )
    step = client.campaigns.update_step(CAMP, "st-1", thread_reply=False)
    assert _body(route) == {"thread_reply": False}
    assert step.thread_reply is False


ESTIMATE = {
    "recipients": 300,
    "mailboxes": 3,
    "daily_capacity": 90,
    "remaining_today": 70,
    "sending_days": 7,
    "estimated_finish_at": "2026-11-09T00:00:00Z",
    "steps": 3,
    "total_sends": 900,
    "first_touch_finish_at": "2026-11-04T00:00:00Z",
    "steady_capacity": 120,
    "full_capacity_at": "2026-11-06T00:00:00Z",
    "ramping": 2,
    "held": 0,
    "warmup": {
        "mailboxes": 3,
        "per_day": 20,
        "per_day_without": 40,
        "reply_rate": 30,
    },
    "other_campaigns_per_day": 10,
    "bottleneck": "warmup_graduation",
    "timeline": [
        {
            "date": "2026-11-01",
            "sending_day": True,
            "capacity": 90,
            "sends": 80,
            "first_emails": 80,
            "follow_ups": 0,
            "warmup": 20,
        }
    ],
    "senders": [
        {
            "id": "mb-1",
            "email": "sam@acme.io",
            "provider": "google",
            "state": "ramping",
            "first_day_cap": 20,
            "steady_cap": 50,
            "warmup_per_day": 10,
            "warmup_without": 20,
            "full_cap_at": None,
        }
    ],
    "scenarios": [{"kind": "more_mailboxes", "value": 2, "finish_at": None}],
}


def _check_estimate(e: Any) -> None:
    assert (e.recipients, e.mailboxes) == (300, 3)
    assert (e.daily_capacity, e.remaining_today, e.sending_days) == (90, 70, 7)
    assert e.steps == 3
    assert e.total_sends == 900
    assert e.first_touch_finish_at == "2026-11-04T00:00:00Z"
    assert e.steady_capacity == 120
    assert e.full_capacity_at == "2026-11-06T00:00:00Z"
    assert (e.ramping, e.held) == (2, 0)
    assert e.warmup["per_day_without"] == 40
    assert e.other_campaigns_per_day == 10
    assert e.bottleneck == "warmup_graduation"
    assert e.timeline[0]["first_emails"] == 80
    assert e.senders[0]["steady_cap"] == 50
    assert e.scenarios[0]["kind"] == "more_mailboxes"


@respx.mock
def test_estimate_new_inputs_and_result(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    out = client.campaigns.estimate(
        segment_ids=["seg-1"],
        start_time="09:00",
        end_time="17:00",
        step_waits=(2, 3),
        campaign_id=CAMP,
    )
    assert _body(route) == {
        "segment_ids": ["seg-1"],
        "start_time": "09:00",
        "end_time": "17:00",
        "step_waits": [2, 3],
        "campaign_id": CAMP,
    }
    _check_estimate(out)

    client.campaigns.estimate(campaign_id=CAMP)
    assert _body(route) == {"campaign_id": CAMP}


@pytest.mark.anyio
@respx.mock
async def test_campaign_drift_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    _check_estimate(await aclient.campaigns.estimate(segment_ids=["s"], step_waits=[1]))
    assert _body(route) == {"segment_ids": ["s"], "step_waits": [1]}

    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(
            201,
            json={"id": CAMP, "entry_delay_minutes": 30, "effective_timezone": "UTC"},
        )
    )
    made = await aclient.campaigns.create(name="Q4", entry_delay_minutes=30)
    assert _body(create) == {"name": "Q4", "entry_delay_minutes": 30}
    assert made.entry_delay_minutes == 30
    assert made.effective_timezone == "UTC"

    step = respx.patch(f"{BASE_URL}/campaigns/{CAMP}/steps/st-1").mock(
        return_value=httpx.Response(200, json={"id": "st-1", "thread_reply": True})
    )
    out = await aclient.campaigns.update_step(CAMP, "st-1", thread_reply=True)
    assert _body(step) == {"thread_reply": True}
    assert out.thread_reply is True
