"""Tests for the campaign routes added in the second API sync, sync and async.

Covers per-lead CC and hold, the placement monitor, the send plan, warmup
placement, and the new campaign fields (follow-up sender, stop on meeting,
entry delay, thread reply, richer estimates).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CAMP = "b1f2c3d4-0000-0000-0000-000000000001"
CONTACT = "c0c1c2c3-0000-0000-0000-000000000002"
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


CC = {
    "contact_id": "d0d1d2d3-0000-0000-0000-000000000003",
    "email": "colleague@acme.com",
    "first_name": "Sam",
    "last_name": "Lee",
    "company": "Acme",
    "status": "bounced",
    "bounced_at": "2026-09-20T10:00:00Z",
}
CC_LIST = {"campaign_id": CAMP, "contact_id": CONTACT, "cc": [CC]}
HOLD = {
    "campaign_id": CAMP,
    "contact_id": CONTACT,
    "hold": {
        "since": "2026-09-25T14:00:00Z",
        "until": "2026-10-01T00:00:00Z",
        "reason": "On leave",
        "source": "manual",
    },
}
MONITOR = {
    "id": "e0e1e2e3-0000-0000-0000-000000000004",
    "campaign_id": CAMP,
    "created_by": None,
    "enabled": True,
    "interval_days": 7,
    "panel": "instance",
    "alert_below": 70,
    "pause_on_alert": True,
    "next_run_at": "2026-10-02T00:00:00Z",
    "last_run_at": None,
    "last_test_id": None,
    "last_alert_at": None,
    "last_error": "no sender",
    "created_at": "2026-09-25T14:00:00Z",
    "updated_at": "2026-09-25T14:00:00Z",
}
PLAN = {
    "campaign_id": CAMP,
    "status": "active",
    "day": "2026-09-25",
    "timezone": "Europe/London",
    "computed_at": "2026-09-25T14:00:00Z",
    "stale": True,
    "configured_ceiling": 200,
    "projected_today": 120,
    "sent_today": 40,
    "expected_remaining": 80,
    "bottleneck": "warmup_graduation",
    "limits": [
        {"kind": "warmup_graduation", "emails": 50, "mailboxes": 3},
        {"kind": "campaign_daily_limit", "emails": 30},
    ],
    "window": {
        "sending_day": True,
        "open_now": True,
        "closes_at": "2026-09-25T17:00:00Z",
        "minutes_left": 180,
    },
    "leads": {
        "due_now": 10,
        "due_later_today": 5,
        "new_leads_due_today": 8,
        "waiting_on_step": 100,
        "waiting_on_condition": 2,
        "held": 1,
        "waiting_on_sender": 0,
        "new_leads_started_today": 4,
        "max_new_leads_per_day": 50,
        "next_due_at": "2026-09-25T15:00:00Z",
    },
    "mailboxes": [
        {
            "id": "f0f1f2f3-0000-0000-0000-000000000005",
            "email": "a@yourdomain.com",
            "provider": "google_workspace",
            "configured_cap": 50,
            "cap_today": 30,
            "limited_by": "warmup_graduation",
            "sent_today": 10,
            "sent_by_other_campaigns": 2,
            "expected_remaining": 20,
            "state": "sending",
            "reopens_at": "2026-09-26T08:00:00Z",
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
    "organization": {"daily_limit": 1000, "sent_today": 400, "remaining": 600},
    "next_wake_at": "2026-09-25T14:05:00Z",
}
WARMUP = {
    "data": [
        {
            "sequence_id": "a1a2a3a4-0000-0000-0000-000000000006",
            "variant_id": None,
            "placement": {
                "sent": 20,
                "reported": 18,
                "inbox": 15,
                "tabs": 2,
                "spam": 1,
                "rescued": 1,
            },
            "by_group": [
                {
                    "group": "google",
                    "sent": 10,
                    "reported": 9,
                    "inbox": 8,
                    "tabs": 1,
                    "spam": 0,
                    "rescued": 0,
                }
            ],
        }
    ],
    "days": 30,
}


# -- per-lead CC and hold ---------------------------------------------------


@respx.mock
def test_lead_cc_and_hold_sync(client: Warmbly) -> None:
    get_cc = respx.get(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json=CC_LIST)
    )
    cc = client.campaigns.lead_cc(CAMP, CONTACT)
    assert _last(get_cc).method == "GET"
    assert cc.campaign_id == CAMP
    assert cc.cc[0].email == "colleague@acme.com"
    assert cc.cc[0].status == "bounced"
    assert cc.cc[0].bounced_at == "2026-09-20T10:00:00Z"
    assert cc.cc[0].company == "Acme"

    put_cc = respx.put(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json=CC_LIST)
    )
    out = client.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=["x", "y"])
    assert json.loads(_last(put_cc).content) == {"contact_ids": ["x", "y"]}
    assert out.cc[0].first_name == "Sam"

    suggestions = respx.get(f"{BASE_URL}{LEAD}/cc/suggestions").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "contact_id": "s1",
                        "email": "pat@acme.com",
                        "first_name": "Pat",
                        "last_name": "Kim",
                        "company": "Acme",
                        "reason": "company",
                    }
                ]
            },
        )
    )
    found = list(client.campaigns.lead_cc_suggestions(CAMP, CONTACT))
    assert _last(suggestions).url.path == f"/v1{LEAD}/cc/suggestions"
    assert found[0].reason == "company"
    assert found[0].last_name == "Kim"

    hold = respx.get(f"{BASE_URL}{LEAD}/hold").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    held = client.campaigns.lead_hold(CAMP, CONTACT)
    assert _last(hold).method == "GET"
    assert held.hold is not None
    assert held.hold.source == "manual"
    assert held.hold.until == "2026-10-01T00:00:00Z"
    assert held.hold.reason == "On leave"

    pause = respx.post(f"{BASE_URL}{LEAD}/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    paused = client.campaigns.pause_lead(
        CAMP, CONTACT, until="2026-10-01T00:00:00Z", reason="On leave"
    )
    assert json.loads(_last(pause).content) == {
        "until": "2026-10-01T00:00:00Z",
        "reason": "On leave",
    }
    assert paused.hold is not None
    assert paused.hold.since == "2026-09-25T14:00:00Z"

    client.campaigns.pause_lead(CAMP, CONTACT)
    assert _last(pause).content == b""

    resume = respx.post(f"{BASE_URL}{LEAD}/resume").mock(
        return_value=httpx.Response(
            200, json={"campaign_id": CAMP, "contact_id": CONTACT}
        )
    )
    resumed = client.campaigns.resume_lead(CAMP, CONTACT)
    assert _last(resume).method == "POST"
    assert resumed.hold is None
    assert resumed.contact_id == CONTACT


@respx.mock
@pytest.mark.anyio
async def test_lead_cc_and_hold_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json=CC_LIST)
    )
    cc = await aclient.campaigns.lead_cc(CAMP, CONTACT)
    assert cc.cc[0].contact_id == CC["contact_id"]

    put_cc = respx.put(f"{BASE_URL}{LEAD}/cc").mock(
        return_value=httpx.Response(200, json={**CC_LIST, "cc": []})
    )
    out = await aclient.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=[])
    assert json.loads(_last(put_cc).content) == {"contact_ids": []}
    assert out.cc == []

    respx.get(f"{BASE_URL}{LEAD}/cc/suggestions").mock(
        return_value=httpx.Response(
            200, json={"data": [{"contact_id": "s1", "reason": "domain"}]}
        )
    )
    found = [s async for s in aclient.campaigns.lead_cc_suggestions(CAMP, CONTACT)]
    assert found[0].reason == "domain"

    respx.get(f"{BASE_URL}{LEAD}/hold").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    held = await aclient.campaigns.lead_hold(CAMP, CONTACT)
    assert held.hold is not None
    assert held.hold.reason == "On leave"

    pause = respx.post(f"{BASE_URL}{LEAD}/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    await aclient.campaigns.pause_lead(CAMP, CONTACT, reason="Vacation")
    assert json.loads(_last(pause).content) == {"reason": "Vacation"}
    await aclient.campaigns.pause_lead(CAMP, CONTACT)
    assert _last(pause).content == b""

    resume = respx.post(f"{BASE_URL}{LEAD}/resume").mock(
        return_value=httpx.Response(200, json={"campaign_id": CAMP})
    )
    resumed = await aclient.campaigns.resume_lead(CAMP, CONTACT)
    assert _last(resume).method == "POST"
    assert resumed.hold is None


# -- placement monitor ------------------------------------------------------


@respx.mock
def test_placement_monitor_sync(client: Warmbly) -> None:
    path = f"{BASE_URL}/campaigns/{CAMP}/placement-monitor"
    route = respx.get(path).mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    got = client.campaigns.placement_monitor(CAMP)
    assert _last(route).method == "GET"
    assert got.data is not None
    assert got.data.interval_days == 7
    assert got.data.pause_on_alert is True
    assert got.data.last_error == "no sender"
    assert got.data.last_run_at is None

    respx.get(path).mock(return_value=httpx.Response(200, json={"data": None}))
    assert client.campaigns.placement_monitor(CAMP).data is None

    put = respx.put(path).mock(return_value=httpx.Response(200, json={"data": MONITOR}))
    saved = client.campaigns.put_placement_monitor(
        CAMP,
        enabled=True,
        interval_days=7,
        panel="instance",
        alert_below=70,
        pause_on_alert=True,
    )
    assert json.loads(_last(put).content) == {
        "enabled": True,
        "interval_days": 7,
        "panel": "instance",
        "alert_below": 70,
        "pause_on_alert": True,
    }
    assert saved.data is not None
    assert saved.data.next_run_at == "2026-10-02T00:00:00Z"

    client.campaigns.put_placement_monitor(CAMP)
    assert json.loads(_last(put).content) == {}

    delete = respx.delete(path).mock(return_value=httpx.Response(204))
    removed = client.campaigns.delete_placement_monitor(CAMP)
    assert _last(delete).method == "DELETE"
    assert removed.deleted is None


@respx.mock
@pytest.mark.anyio
async def test_placement_monitor_async(aclient: AsyncWarmbly) -> None:
    path = f"{BASE_URL}/campaigns/{CAMP}/placement-monitor"
    respx.get(path).mock(return_value=httpx.Response(200, json={"data": MONITOR}))
    got = await aclient.campaigns.placement_monitor(CAMP)
    assert got.data is not None
    assert got.data.alert_below == 70

    put = respx.put(path).mock(return_value=httpx.Response(200, json={"data": MONITOR}))
    saved = await aclient.campaigns.put_placement_monitor(
        CAMP, interval_days=3, alert_below=50
    )
    assert json.loads(_last(put).content) == {"interval_days": 3, "alert_below": 50}
    assert saved.data is not None
    assert saved.data.enabled is True

    delete = respx.delete(path).mock(return_value=httpx.Response(204))
    await aclient.campaigns.delete_placement_monitor(CAMP)
    assert _last(delete).method == "DELETE"


# -- send plan and warmup placement -----------------------------------------


@respx.mock
def test_send_plan_and_warmup_placement_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/{CAMP}/send-plan").mock(
        return_value=httpx.Response(200, json=PLAN)
    )
    plan = client.campaigns.send_plan(CAMP)
    assert _last(route).method == "GET"
    assert plan.projected_today == 120
    assert plan.stale is True
    assert plan.bottleneck == "warmup_graduation"
    assert plan.limits[0].mailboxes == 3
    assert plan.limits[1].mailboxes is None
    assert plan.window is not None
    assert plan.window.minutes_left == 180
    assert plan.leads is not None
    assert plan.leads.max_new_leads_per_day == 50
    assert plan.mailboxes[0].cap_today == 30
    assert plan.mailboxes[0].graduation == PLAN["mailboxes"][0]["graduation"]  # type: ignore[index]
    assert plan.organization is not None
    assert plan.organization.remaining == 600
    assert plan.next_wake_at == "2026-09-25T14:05:00Z"

    warm = respx.get(f"{BASE_URL}/campaigns/{CAMP}/warmup-placement").mock(
        return_value=httpx.Response(200, json=WARMUP)
    )
    placement = client.campaigns.warmup_placement(CAMP)
    assert _last(warm).url.path == f"/v1/campaigns/{CAMP}/warmup-placement"
    assert placement.days == 30
    step = placement.data[0]
    assert step.variant_id is None
    assert step.placement is not None
    assert step.placement.rescued == 1
    assert step.by_group[0].group == "google"
    assert step.by_group[0].inbox == 8


@respx.mock
@pytest.mark.anyio
async def test_send_plan_and_warmup_placement_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/{CAMP}/send-plan").mock(
        return_value=httpx.Response(200, json=PLAN)
    )
    plan = await aclient.campaigns.send_plan(CAMP)
    assert plan.sent_today == 40
    assert plan.mailboxes[0].state == "sending"

    warm = respx.get(f"{BASE_URL}/campaigns/{CAMP}/warmup-placement").mock(
        return_value=httpx.Response(200, json={"data": [], "days": 30})
    )
    placement = await aclient.campaigns.warmup_placement(CAMP)
    assert _last(warm).method == "GET"
    assert placement.data == []
    assert placement.days == 30


# -- new campaign fields ----------------------------------------------------

CAMPAIGN: dict[str, Any] = {
    "id": CAMP,
    "name": "Q4 outbound",
    "status": "draft",
    "stop_on_reply": True,
    "stop_on_meeting": True,
    "timezone": "",
    "effective_timezone": "Europe/London",
    "follow_up_sender": "same_domain",
    "entry_delay_minutes": 15,
}

NEW_FIELDS = {
    "stop_on_meeting": False,
    "follow_up_sender": "rotate",
    "entry_delay_minutes": 30,
}


@respx.mock
def test_campaign_new_fields_sync(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN)
    )
    made = client.campaigns.create(name="Q4 outbound", **NEW_FIELDS)  # type: ignore[arg-type]
    assert json.loads(_last(create).content) == {"name": "Q4 outbound", **NEW_FIELDS}
    assert made.stop_on_meeting is True
    assert made.effective_timezone == "Europe/London"
    assert made.follow_up_sender == "same_domain"
    assert made.entry_delay_minutes == 15

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMP}").mock(
        return_value=httpx.Response(200, json=CAMPAIGN)
    )
    client.campaigns.update(CAMP, **NEW_FIELDS)  # type: ignore[arg-type]
    assert json.loads(_last(update).content) == NEW_FIELDS

    step = respx.patch(f"{BASE_URL}/campaigns/{CAMP}/steps/st1").mock(
        return_value=httpx.Response(200, json={"id": "st1", "thread_reply": False})
    )
    updated = client.campaigns.update_step(CAMP, "st1", thread_reply=False)
    assert json.loads(_last(step).content) == {"thread_reply": False}
    assert updated.thread_reply is False


@respx.mock
@pytest.mark.anyio
async def test_campaign_new_fields_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN)
    )
    made = await aclient.campaigns.create(name="Q4 outbound", **NEW_FIELDS)  # type: ignore[arg-type]
    assert json.loads(_last(create).content) == {"name": "Q4 outbound", **NEW_FIELDS}
    assert made.follow_up_sender == "same_domain"

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMP}").mock(
        return_value=httpx.Response(200, json=CAMPAIGN)
    )
    await aclient.campaigns.update(CAMP, **NEW_FIELDS)  # type: ignore[arg-type]
    assert json.loads(_last(update).content) == NEW_FIELDS

    step = respx.patch(f"{BASE_URL}/campaigns/{CAMP}/steps/st1").mock(
        return_value=httpx.Response(200, json={"id": "st1", "thread_reply": True})
    )
    updated = await aclient.campaigns.update_step(CAMP, "st1", thread_reply=True)
    assert json.loads(_last(step).content) == {"thread_reply": True}
    assert updated.thread_reply is True


ESTIMATE = {
    "recipients": 500,
    "mailboxes": 4,
    "daily_capacity": 120,
    "remaining_today": 100,
    "sending_days": 5,
    "estimated_finish_at": "2026-10-01T00:00:00Z",
    "steps": 3,
    "total_sends": 1500,
    "first_touch_finish_at": "2026-09-29T00:00:00Z",
    "steady_capacity": 200,
    "full_capacity_at": "2026-09-30T00:00:00Z",
    "ramping": 2,
    "held": 1,
    "warmup": {"mailboxes": 4, "per_day": 40, "per_day_without": 80, "reply_rate": 35},
    "other_campaigns_per_day": 10,
    "bottleneck": "warmup_graduation",
    "timeline": [
        {
            "date": "2026-09-25",
            "sending_day": True,
            "capacity": 120,
            "sends": 100,
            "first_emails": 80,
            "follow_ups": 20,
            "warmup": 40,
        }
    ],
    "senders": [
        {
            "id": "m1",
            "email": "a@yourdomain.com",
            "provider": "gmail",
            "state": "ramping",
            "first_day_cap": 10,
            "steady_cap": 40,
            "warmup_per_day": 10,
            "warmup_without": 20,
            "full_cap_at": "2026-09-30T00:00:00Z",
        }
    ],
    "scenarios": [
        {"kind": "every_day", "value": 7, "finish_at": "2026-09-28T00:00:00Z"}
    ],
}


def _check_estimate(est: Any) -> None:
    assert est.steps == 3
    assert est.total_sends == 1500
    assert est.bottleneck == "warmup_graduation"
    assert est.warmup.reply_rate == 35
    assert est.timeline[0].first_emails == 80
    assert est.senders[0].state == "ramping"
    assert est.senders[0].full_cap_at == "2026-09-30T00:00:00Z"
    assert est.scenarios[0].kind == "every_day"
    assert est.scenarios[0].value == 7
    assert est.full_capacity_at == "2026-09-30T00:00:00Z"


@respx.mock
def test_estimate_new_fields_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    est = client.campaigns.estimate(
        start_time="08:00",
        end_time="18:00",
        step_waits=[2, 3],
        campaign_id=CAMP,
    )
    assert json.loads(_last(route).content) == {
        "segment_ids": [],
        "start_time": "08:00",
        "end_time": "18:00",
        "step_waits": [2, 3],
        "campaign_id": CAMP,
    }
    _check_estimate(est)


@respx.mock
@pytest.mark.anyio
async def test_estimate_new_fields_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    est = await aclient.campaigns.estimate(
        segment_ids=["seg1"], start_time="09:00", campaign_id=CAMP
    )
    assert json.loads(_last(route).content) == {
        "segment_ids": ["seg1"],
        "start_time": "09:00",
        "campaign_id": CAMP,
    }
    _check_estimate(est)
