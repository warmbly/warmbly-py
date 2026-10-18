"""Server sync for the ``campaigns`` and ``analytics`` resources, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
CAMP = "11111111-1111-1111-1111-111111111111"
CONTACT = "22222222-2222-2222-2222-222222222222"
LEAD = f"{BASE_URL}/campaigns/{CAMP}/leads/{CONTACT}"


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


def _qp(route: respx.Route) -> dict[str, str]:
    return dict(_last(route).url.params)


# ===========================================================================
# campaign record: new fields, removed fields
# ===========================================================================
CAMPAIGN: dict[str, Any] = {
    "id": CAMP,
    "name": "Q4",
    "status": "draft",
    "timezone": "",
    "effective_timezone": "Europe/Berlin",
    "entry_delay_minutes": 90,
    "continuous": True,
}


@respx.mock
def test_campaign_entry_delay_and_effective_timezone(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN)
    )
    created = client.campaigns.create(name="Q4", entry_delay_minutes=90)
    assert created.entry_delay_minutes == 90
    assert created.effective_timezone == "Europe/Berlin"
    assert created.timezone == ""
    assert _body(create) == {"name": "Q4", "entry_delay_minutes": 90}

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMP}").mock(
        return_value=httpx.Response(200, json=CAMPAIGN)
    )
    updated = client.campaigns.update(CAMP, entry_delay_minutes=0)
    assert updated.entry_delay_minutes == 90
    assert _body(update) == {"entry_delay_minutes": 0}


@pytest.mark.anyio
@respx.mock
async def test_campaign_entry_delay_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json=CAMPAIGN)
    )
    created = await aclient.campaigns.create(name="Q4", entry_delay_minutes=90)
    assert created.entry_delay_minutes == 90
    assert created.effective_timezone == "Europe/Berlin"
    assert _body(create) == {"name": "Q4", "entry_delay_minutes": 90}

    update = respx.patch(f"{BASE_URL}/campaigns/{CAMP}").mock(
        return_value=httpx.Response(200, json=CAMPAIGN)
    )
    updated = await aclient.campaigns.update(CAMP, entry_delay_minutes=0)
    assert updated.id == CAMP
    assert _body(update) == {"entry_delay_minutes": 0}


@respx.mock
def test_overview_without_one_time(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns-overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 5,
                "active": 2,
                "paused": 1,
                "draft": 1,
                "completed": 1,
                "folders": [],
            },
        )
    )
    overview = client.campaigns.overview()
    assert overview.total == 5
    assert not hasattr(overview, "one_time")


# ===========================================================================
# estimate
# ===========================================================================
ESTIMATE: dict[str, Any] = {
    "recipients": 600,
    "mailboxes": 3,
    "daily_capacity": 90,
    "remaining_today": 80,
    "sending_days": 7,
    "estimated_finish_at": "2026-11-01T00:00:00Z",
    "steps": 3,
    "total_sends": 1800,
    "first_touch_finish_at": "2026-10-25T00:00:00Z",
    "steady_capacity": 120,
    "full_capacity_at": None,
    "ramping": 1,
    "held": 0,
    "warmup": {"mailboxes": 3, "per_day": 18},
    "other_campaigns_per_day": 12,
    "bottleneck": "warmup_graduation",
    "timeline": [
        {
            "date": "2026-10-19",
            "sending_day": True,
            "capacity": 80,
            "sends": 80,
            "first_emails": 60,
            "follow_ups": 20,
            "warmup": 18,
        }
    ],
    "senders": [
        {
            "id": "acc_1",
            "email": "a@acme.test",
            "provider": "google",
            "state": "ramping",
            "first_day_cap": 20,
            "steady_cap": 40,
            "warmup_per_day": 6,
            "full_cap_at": "2026-10-30T00:00:00Z",
        }
    ],
}
ESTIMATE_BODY = {
    "segment_ids": ["seg_1"],
    "campaign_id": CAMP,
    "email_tag_ids": ["tag_1"],
    "daily_limit": 30,
    "days": 62,
    "timezone": "UTC",
    "start_date": "2026-10-19T00:00:00Z",
    "start_time": "09:00",
    "end_time": "17:00",
    "step_waits": [2, 5],
}


def _check_estimate(e: Any) -> None:
    assert e.recipients == 600
    assert e.steps == 3
    assert e.total_sends == 1800
    assert e.first_touch_finish_at == "2026-10-25T00:00:00Z"
    assert e.steady_capacity == 120
    assert e.ramping == 1
    assert e.warmup is not None and e.warmup.per_day == 18
    assert e.other_campaigns_per_day == 12
    assert e.bottleneck == "warmup_graduation"
    assert e.timeline[0].first_emails == 60
    assert e.timeline[0].sending_day is True
    assert e.senders[0].state == "ramping"
    assert e.senders[0].steady_cap == 40


@respx.mock
def test_estimate_full(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    est = client.campaigns.estimate(
        segment_ids=["seg_1"],
        campaign_id=CAMP,
        email_tag_ids=["tag_1"],
        daily_limit=30,
        days=62,
        timezone="UTC",
        start_date="2026-10-19T00:00:00Z",
        start_time="09:00",
        end_time="17:00",
        step_waits=[2, 5],
    )
    _check_estimate(est)
    assert _body(route) == ESTIMATE_BODY


@respx.mock
def test_estimate_saved_campaign_only(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json={"recipients": 4})
    )
    est = client.campaigns.estimate(campaign_id=CAMP)
    assert est.recipients == 4
    assert est.timeline == []
    assert _body(route) == {"campaign_id": CAMP}


@pytest.mark.anyio
@respx.mock
async def test_estimate_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json=ESTIMATE)
    )
    est = await aclient.campaigns.estimate(
        segment_ids=["seg_1"],
        campaign_id=CAMP,
        email_tag_ids=["tag_1"],
        daily_limit=30,
        days=62,
        timezone="UTC",
        start_date="2026-10-19T00:00:00Z",
        start_time="09:00",
        end_time="17:00",
        step_waits=[2, 5],
    )
    _check_estimate(est)
    assert _body(route) == ESTIMATE_BODY


# ===========================================================================
# steps: thread_reply, optional create body
# ===========================================================================
STEP = {"id": "st_1", "subject": "Hi", "thread_reply": False, "wait_after": 3}


@respx.mock
def test_create_step_blank_and_filled(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/{CAMP}/steps").mock(
        return_value=httpx.Response(201, json={"id": "st_1", "thread_reply": True})
    )
    blank = client.campaigns.create_step(CAMP)
    assert blank.thread_reply is True
    assert _last(route).content == b""

    route = respx.post(f"{BASE_URL}/campaigns/{CAMP}/steps").mock(
        return_value=httpx.Response(201, json=STEP)
    )
    step = client.campaigns.create_step(
        CAMP, subject="Hi", wait_after=3, thread_reply=False
    )
    assert step.thread_reply is False
    assert step.wait_after == 3
    assert _body(route) == {"subject": "Hi", "wait_after": 3, "thread_reply": False}


@respx.mock
def test_update_step_thread_reply(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/campaigns/{CAMP}/steps/st_1").mock(
        return_value=httpx.Response(200, json=STEP)
    )
    step = client.campaigns.update_step(CAMP, "st_1", thread_reply=False)
    assert step.thread_reply is False
    assert _body(route) == {"thread_reply": False}


@pytest.mark.anyio
@respx.mock
async def test_steps_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/{CAMP}/steps").mock(
        return_value=httpx.Response(201, json=STEP)
    )
    step = await aclient.campaigns.create_step(CAMP, subject="Hi", thread_reply=False)
    assert step.thread_reply is False
    assert _body(route) == {"subject": "Hi", "thread_reply": False}

    route = respx.post(f"{BASE_URL}/campaigns/{CAMP}/steps").mock(
        return_value=httpx.Response(201, json={"id": "st_2"})
    )
    blank = await aclient.campaigns.create_step(CAMP)
    assert blank.id == "st_2"
    assert _last(route).content == b""

    upd = respx.patch(f"{BASE_URL}/campaigns/{CAMP}/steps/st_1").mock(
        return_value=httpx.Response(200, json=STEP)
    )
    updated = await aclient.campaigns.update_step(CAMP, "st_1", thread_reply=True)
    assert updated.id == "st_1"
    assert _body(upd) == {"thread_reply": True}


# ===========================================================================
# start options, segments replace
# ===========================================================================
@respx.mock
def test_start_acknowledge_list_risk(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/{CAMP}/start").mock(
        return_value=httpx.Response(
            200, json={"status": "started", "waiting_for_leads": True}
        )
    )
    state = client.campaigns.start(CAMP, acknowledge_list_risk=True)
    assert state.status == "started"
    assert state.waiting_for_leads is True
    assert _body(route) == {"acknowledge_list_risk": True}

    client.campaigns.start(CAMP)
    assert _last(route).content == b""


@pytest.mark.anyio
@respx.mock
async def test_start_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/{CAMP}/start").mock(
        return_value=httpx.Response(200, json={"status": "started"})
    )
    state = await aclient.campaigns.start(CAMP, acknowledge_list_risk=True)
    assert state.status == "started"
    assert _body(route) == {"acknowledge_list_risk": True}
    await aclient.campaigns.start(CAMP)
    assert _last(route).content == b""


SEGMENTS = {
    "data": [{"segment_id": "seg_1", "name": "Acme", "lead_count": 4}],
    "added": 2,
    "withdrawn": 5,
    "contacted": 1,
}


@respx.mock
def test_set_segments_reports_withdrawn(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/campaigns/{CAMP}/segments").mock(
        return_value=httpx.Response(200, json=SEGMENTS)
    )
    out = client.campaigns.set_segments(CAMP, segment_ids=["seg_1"])
    assert (out.added, out.withdrawn, out.contacted) == (2, 5, 1)
    assert out.data[0].lead_count == 4
    assert _body(route) == {"segment_ids": ["seg_1"]}


@pytest.mark.anyio
@respx.mock
async def test_set_segments_async(aclient: AsyncWarmbly) -> None:
    respx.put(f"{BASE_URL}/campaigns/{CAMP}/segments").mock(
        return_value=httpx.Response(200, json=SEGMENTS)
    )
    out = await aclient.campaigns.set_segments(CAMP, segment_ids=["seg_1"])
    assert (out.added, out.withdrawn, out.contacted) == (2, 5, 1)


# ===========================================================================
# per-lead hold
# ===========================================================================
HELD = {
    "campaign_id": CAMP,
    "contact_id": CONTACT,
    "hold": {
        "since": "2026-10-18T10:00:00Z",
        "until": "2026-10-25T00:00:00Z",
        "reason": "on leave",
        "source": "manual",
    },
}
NOT_HELD = {"campaign_id": CAMP, "contact_id": CONTACT}


@respx.mock
def test_lead_hold_pause_resume(client: Warmbly) -> None:
    get = respx.get(f"{LEAD}/hold").mock(return_value=httpx.Response(200, json=HELD))
    state = client.campaigns.lead_hold(CAMP, CONTACT)
    assert state.campaign_id == CAMP
    assert state.contact_id == CONTACT
    assert state.hold is not None
    assert state.hold.source == "manual"
    assert state.hold.until == "2026-10-25T00:00:00Z"
    assert state.hold.reason == "on leave"
    assert state.hold.since == "2026-10-18T10:00:00Z"
    assert _last(get).method == "GET"

    pause = respx.post(f"{LEAD}/pause").mock(
        return_value=httpx.Response(200, json=HELD)
    )
    paused = client.campaigns.pause_lead(
        CAMP, CONTACT, until="2026-10-25T00:00:00Z", reason="on leave"
    )
    assert paused.hold is not None and paused.hold.reason == "on leave"
    assert _last(pause).method == "POST"
    assert _body(pause) == {"until": "2026-10-25T00:00:00Z", "reason": "on leave"}
    assert _last(pause).headers.get("idempotency-key")

    client.campaigns.pause_lead(CAMP, CONTACT, until=None)
    assert _body(pause) == {"until": None}

    client.campaigns.pause_lead(CAMP, CONTACT)
    assert _body(pause) == {}

    resume = respx.post(f"{LEAD}/resume").mock(
        return_value=httpx.Response(200, json=NOT_HELD)
    )
    resumed = client.campaigns.resume_lead(CAMP, CONTACT)
    assert resumed.hold is None
    assert resumed.contact_id == CONTACT
    assert _last(resume).method == "POST"


@pytest.mark.anyio
@respx.mock
async def test_lead_hold_pause_resume_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{LEAD}/hold").mock(return_value=httpx.Response(200, json=HELD))
    state = await aclient.campaigns.lead_hold(CAMP, CONTACT)
    assert state.hold is not None and state.hold.source == "manual"

    pause = respx.post(f"{LEAD}/pause").mock(
        return_value=httpx.Response(200, json=HELD)
    )
    paused = await aclient.campaigns.pause_lead(
        CAMP, CONTACT, until="2026-10-25T00:00:00Z", reason="on leave"
    )
    assert paused.hold is not None and paused.hold.until == "2026-10-25T00:00:00Z"
    assert _body(pause) == {"until": "2026-10-25T00:00:00Z", "reason": "on leave"}

    resume = respx.post(f"{LEAD}/resume").mock(
        return_value=httpx.Response(200, json=NOT_HELD)
    )
    resumed = await aclient.campaigns.resume_lead(CAMP, CONTACT)
    assert resumed.hold is None
    assert _last(resume).method == "POST"


# ===========================================================================
# per-lead CC
# ===========================================================================
CC = {
    "campaign_id": CAMP,
    "contact_id": CONTACT,
    "cc": [
        {
            "contact_id": "c_2",
            "email": "boss@acme.test",
            "first_name": "Bo",
            "last_name": "Ss",
            "company": "Acme",
            "status": "bounced",
            "bounced_at": "2026-10-01T00:00:00Z",
        }
    ],
}
SUGGESTIONS = {
    "data": [
        {
            "contact_id": "c_3",
            "email": "pat@acme.test",
            "first_name": "Pat",
            "last_name": "Lee",
            "company": "Acme",
            "reason": "company",
        }
    ]
}


def _check_cc(out: Any) -> None:
    assert out.campaign_id == CAMP
    assert out.contact_id == CONTACT
    assert out.cc[0].contact_id == "c_2"
    assert out.cc[0].email == "boss@acme.test"
    assert out.cc[0].first_name == "Bo"
    assert out.cc[0].last_name == "Ss"
    assert out.cc[0].company == "Acme"
    assert out.cc[0].status == "bounced"
    assert out.cc[0].bounced_at == "2026-10-01T00:00:00Z"


def _check_suggestions(out: Any) -> None:
    s = out.data[0]
    assert (s.contact_id, s.email, s.reason) == ("c_3", "pat@acme.test", "company")
    assert (s.first_name, s.last_name, s.company) == ("Pat", "Lee", "Acme")


@respx.mock
def test_lead_cc(client: Warmbly) -> None:
    get = respx.get(f"{LEAD}/cc").mock(return_value=httpx.Response(200, json=CC))
    _check_cc(client.campaigns.lead_cc(CAMP, CONTACT))
    assert _last(get).method == "GET"

    put = respx.put(f"{LEAD}/cc").mock(return_value=httpx.Response(200, json=CC))
    _check_cc(client.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=["c_2"]))
    assert _last(put).method == "PUT"
    assert _body(put) == {"contact_ids": ["c_2"]}

    sug = respx.get(f"{LEAD}/cc/suggestions").mock(
        return_value=httpx.Response(200, json=SUGGESTIONS)
    )
    _check_suggestions(client.campaigns.suggest_lead_cc(CAMP, CONTACT))
    assert _last(sug).url.path.endswith("/cc/suggestions")


@pytest.mark.anyio
@respx.mock
async def test_lead_cc_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{LEAD}/cc").mock(return_value=httpx.Response(200, json=CC))
    _check_cc(await aclient.campaigns.lead_cc(CAMP, CONTACT))

    put = respx.put(f"{LEAD}/cc").mock(return_value=httpx.Response(200, json=CC))
    _check_cc(await aclient.campaigns.set_lead_cc(CAMP, CONTACT, contact_ids=["c_2"]))
    assert _body(put) == {"contact_ids": ["c_2"]}

    respx.get(f"{LEAD}/cc/suggestions").mock(
        return_value=httpx.Response(200, json=SUGGESTIONS)
    )
    _check_suggestions(await aclient.campaigns.suggest_lead_cc(CAMP, CONTACT))


# ===========================================================================
# placement monitor
# ===========================================================================
MONITOR_URL = f"{BASE_URL}/campaigns/{CAMP}/placement-monitor"
MONITOR = {
    "data": {
        "id": "mon_1",
        "campaign_id": CAMP,
        "created_by": "user_1",
        "enabled": True,
        "interval_days": 7,
        "panel": "workspace",
        "alert_below": 80,
        "pause_on_alert": True,
        "next_run_at": "2026-10-18T10:05:00Z",
        "last_run_at": None,
        "last_test_id": "test_1",
        "last_alert_at": "2026-10-10T00:00:00Z",
        "last_error": "no seeds",
        "created_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-02T00:00:00Z",
    }
}


def _check_monitor(out: Any) -> None:
    m = out.data
    assert m is not None
    assert m.id == "mon_1"
    assert m.campaign_id == CAMP
    assert m.created_by == "user_1"
    assert m.enabled is True
    assert m.interval_days == 7
    assert m.panel == "workspace"
    assert m.alert_below == 80
    assert m.pause_on_alert is True
    assert m.next_run_at == "2026-10-18T10:05:00Z"
    assert m.last_run_at is None
    assert m.last_test_id == "test_1"
    assert m.last_alert_at == "2026-10-10T00:00:00Z"
    assert m.last_error == "no seeds"


@respx.mock
def test_placement_monitor(client: Warmbly) -> None:
    get = respx.get(MONITOR_URL).mock(return_value=httpx.Response(200, json=MONITOR))
    _check_monitor(client.campaigns.placement_monitor(CAMP))
    assert _last(get).method == "GET"

    get.mock(return_value=httpx.Response(200, json={"data": None}))
    assert client.campaigns.placement_monitor(CAMP).data is None

    put = respx.put(MONITOR_URL).mock(return_value=httpx.Response(200, json=MONITOR))
    _check_monitor(
        client.campaigns.put_placement_monitor(
            CAMP,
            enabled=True,
            interval_days=7,
            panel="workspace",
            alert_below=80,
            pause_on_alert=True,
        )
    )
    assert _last(put).method == "PUT"
    assert _body(put) == {
        "enabled": True,
        "interval_days": 7,
        "panel": "workspace",
        "alert_below": 80,
        "pause_on_alert": True,
    }
    client.campaigns.put_placement_monitor(CAMP, enabled=False)
    assert _body(put) == {"enabled": False}

    delete = respx.delete(MONITOR_URL).mock(return_value=httpx.Response(204))
    out = client.campaigns.delete_placement_monitor(CAMP)
    assert _last(delete).method == "DELETE"
    assert out.deleted is None


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_async(aclient: AsyncWarmbly) -> None:
    respx.get(MONITOR_URL).mock(return_value=httpx.Response(200, json=MONITOR))
    _check_monitor(await aclient.campaigns.placement_monitor(CAMP))

    put = respx.put(MONITOR_URL).mock(return_value=httpx.Response(200, json=MONITOR))
    _check_monitor(
        await aclient.campaigns.put_placement_monitor(
            CAMP, interval_days=7, alert_below=80
        )
    )
    assert _body(put) == {"interval_days": 7, "alert_below": 80}

    delete = respx.delete(MONITOR_URL).mock(return_value=httpx.Response(204))
    await aclient.campaigns.delete_placement_monitor(CAMP)
    assert _last(delete).method == "DELETE"


# ===========================================================================
# send plan
# ===========================================================================
PLAN: dict[str, Any] = {
    "campaign_id": CAMP,
    "status": "active",
    "day": "2026-10-18",
    "timezone": "Europe/Berlin",
    "computed_at": "2026-10-18T09:00:00Z",
    "stale": True,
    "configured_ceiling": 100,
    "projected_today": 70,
    "sent_today": 20,
    "expected_remaining": 50,
    "bottleneck": "warmup_graduation",
    "limits": [{"kind": "warmup_graduation", "emails": 30, "mailboxes": 2}],
    "window": {
        "sending_day": True,
        "open_now": False,
        "opens_at": "2026-10-19T07:00:00Z",
        "closes_at": "2026-10-18T16:00:00Z",
        "minutes_left": 0,
        "starts_at": "2026-10-01T00:00:00Z",
        "ends_at": "2026-12-01T00:00:00Z",
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
        "max_new_leads_per_day": 50,
        "next_due_at": "2026-10-19T08:00:00Z",
    },
    "mailboxes": [
        {
            "id": "acc_1",
            "email": "a@acme.test",
            "provider": "google",
            "configured_cap": 50,
            "cap_today": 20,
            "limited_by": "warmup_graduation",
            "sent_today": 10,
            "sent_by_other_campaigns": 2,
            "expected_remaining": 8,
            "state": "budget_spent",
            "reopens_at": "2026-10-19T07:00:00Z",
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
    "organization": {"daily_limit": 500, "sent_today": 200, "remaining": 300},
    "next_wake_at": "2026-10-18T09:30:00Z",
}


def _check_plan(p: Any) -> None:
    assert p.campaign_id == CAMP
    assert (p.status, p.day, p.timezone) == ("active", "2026-10-18", "Europe/Berlin")
    assert p.computed_at == "2026-10-18T09:00:00Z"
    assert p.stale is True
    assert (p.configured_ceiling, p.projected_today) == (100, 70)
    assert (p.sent_today, p.expected_remaining) == (20, 50)
    assert p.bottleneck == "warmup_graduation"
    assert p.limits[0].kind == "warmup_graduation"
    assert (p.limits[0].emails, p.limits[0].mailboxes) == (30, 2)
    w = p.window
    assert (w.sending_day, w.open_now, w.minutes_left) == (True, False, 0)
    assert w.opens_at == "2026-10-19T07:00:00Z"
    assert w.closes_at == "2026-10-18T16:00:00Z"
    assert w.starts_at == "2026-10-01T00:00:00Z"
    assert w.ends_at == "2026-12-01T00:00:00Z"
    lead = p.leads
    assert (lead.due_now, lead.due_later_today, lead.new_leads_due_today) == (5, 6, 4)
    assert (lead.waiting_on_step, lead.waiting_on_condition) == (7, 1)
    assert (lead.held, lead.waiting_on_sender) == (2, 3)
    assert (lead.new_leads_started_today, lead.max_new_leads_per_day) == (9, 50)
    assert lead.next_due_at == "2026-10-19T08:00:00Z"
    mb = p.mailboxes[0]
    assert (mb.id, mb.email, mb.provider) == ("acc_1", "a@acme.test", "google")
    assert (mb.configured_cap, mb.cap_today, mb.limited_by) == (
        50,
        20,
        "warmup_graduation",
    )
    assert (mb.sent_today, mb.sent_by_other_campaigns) == (10, 2)
    assert (mb.expected_remaining, mb.state) == (8, "budget_spent")
    assert (mb.reopens_at, mb.health, mb.min_gap_seconds) == (
        "2026-10-19T07:00:00Z",
        "watch",
        90,
    )
    assert mb.graduation is not None
    assert (mb.graduation.ceiling, mb.graduation.mailbox_cap) == (20, 50)
    assert (mb.graduation.days_to_full_cap, mb.graduation.held) == (6, False)
    assert p.organization.daily_limit == 500
    assert (p.organization.sent_today, p.organization.remaining) == (200, 300)
    assert p.next_wake_at == "2026-10-18T09:30:00Z"


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


# ===========================================================================
# analytics: query params the server reads
# ===========================================================================
EMPTY: dict[str, Any] = {"sent": 1}


@respx.mock
def test_analytics_query_params(client: Warmbly) -> None:
    a = client.analytics
    route = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    a.dashboard(period="30d", campaign_ids=["c1", "c2"], folder_ids=["f1"])
    assert _qp(route) == {
        "period": "30d",
        "campaign_ids": "c1,c2",
        "folder_ids": "f1",
    }
    a.dashboard()
    assert _qp(route) == {}

    route = respx.get(f"{BASE_URL}/analytics/warmup").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    a.warmup(email_id="acc_1", from_="2026-10-01", to="2026-10-10")
    assert _qp(route) == {
        "email_id": "acc_1",
        "from": "2026-10-01",
        "to": "2026-10-10",
    }

    route = respx.get(f"{BASE_URL}/analytics/campaigns/compare").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    a.compare_campaigns(campaign_ids=["c1", "c2"], from_="2026-10-01", to="2026-10-10")
    assert _qp(route) == {"ids": "c1,c2", "from": "2026-10-01", "to": "2026-10-10"}

    route = respx.get(f"{BASE_URL}/analytics/campaigns/c1/hourly").mock(
        return_value=httpx.Response(
            200, json={"data": [{"hour": 9, "sent": 3}], "date": "2026-10-10"}
        )
    )
    hourly = a.campaign_hourly("c1", date="2026-10-10")
    assert _qp(route) == {"date": "2026-10-10"}
    assert hourly.date == "2026-10-10"
    assert hourly.data == [{"hour": 9, "sent": 3}]

    route = respx.get(f"{BASE_URL}/analytics/accounts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "acc_1"}],
                "pagination": {"next_cursor": "n1", "has_more": True},
            },
        )
    )
    accounts = a.accounts(email_ids=["acc_1", "acc_2"], limit=10, cursor="c0")
    assert _qp(route) == {"email_ids": "acc_1,acc_2", "limit": "10", "cursor": "c0"}
    assert accounts.pagination == {"next_cursor": "n1", "has_more": True}

    route = respx.get(f"{BASE_URL}/analytics/usage").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    a.usage(period="week")
    assert _qp(route) == {"period": "week"}


@pytest.mark.anyio
@respx.mock
async def test_analytics_query_params_async(aclient: AsyncWarmbly) -> None:
    a = aclient.analytics
    route = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    await a.dashboard(period="90d", campaign_ids=["c1"], folder_ids=["f1", "f2"])
    assert _qp(route) == {
        "period": "90d",
        "campaign_ids": "c1",
        "folder_ids": "f1,f2",
    }

    route = respx.get(f"{BASE_URL}/analytics/warmup").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    await a.warmup(email_id="acc_1", from_="2026-10-01", to="2026-10-10")
    assert _qp(route)["email_id"] == "acc_1"

    route = respx.get(f"{BASE_URL}/analytics/campaigns/compare").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    await a.compare_campaigns(campaign_ids=["c1", "c2"], from_="a", to="b")
    assert _qp(route) == {"ids": "c1,c2", "from": "a", "to": "b"}

    route = respx.get(f"{BASE_URL}/analytics/campaigns/c1/hourly").mock(
        return_value=httpx.Response(200, json={"date": "2026-10-10"})
    )
    assert (await a.campaign_hourly("c1", date="2026-10-10")).date == "2026-10-10"
    assert _qp(route) == {"date": "2026-10-10"}

    route = respx.get(f"{BASE_URL}/analytics/accounts").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await a.accounts(email_ids=["acc_1"], limit=5, cursor="c0")
    assert _qp(route) == {"email_ids": "acc_1", "limit": "5", "cursor": "c0"}

    route = respx.get(f"{BASE_URL}/analytics/usage").mock(
        return_value=httpx.Response(200, json=EMPTY)
    )
    await a.usage(period="month")
    assert _qp(route) == {"period": "month"}


# ===========================================================================
# analytics: direct mail
# ===========================================================================
DIRECT = {
    "period": "30d",
    "volume": {
        "sent": 40,
        "received": 25,
        "threads_started": 30,
        "replied": 12,
        "reply_rate": 40.0,
        "bounced": 2,
        "median_reply_minutes": 95,
    },
    "tracking": {
        "mailboxes_opted_in": 1,
        "mailboxes_total": 3,
        "tracked_sent": 20,
        "opened": 9,
        "machine_opened": 3,
        "clicked": 2,
        "open_rate": 45.0,
        "click_rate": 10.0,
    },
    "daily_trend": [{"date": "2026-10-17T00:00:00Z", "sent": 4, "received": 2}],
    "mailboxes": [
        {
            "email_account_id": "acc_1",
            "email": "me@acme.test",
            "track_direct_mail": True,
            "sent": 40,
            "received": 25,
        }
    ],
    "top_contacts": [
        {
            "email": "x@y.test",
            "sent": 6,
            "received": 3,
            "last_at": "2026-10-17T12:00:00Z",
        }
    ],
}


def _check_direct(d: Any) -> None:
    assert d.period == "30d"
    v = d.volume
    assert (v.sent, v.received, v.threads_started) == (40, 25, 30)
    assert (v.replied, v.reply_rate, v.bounced) == (12, 40.0, 2)
    assert v.median_reply_minutes == 95
    t = d.tracking
    assert (t.mailboxes_opted_in, t.mailboxes_total, t.tracked_sent) == (1, 3, 20)
    assert (t.opened, t.machine_opened, t.clicked) == (9, 3, 2)
    assert (t.open_rate, t.click_rate) == (45.0, 10.0)
    assert d.daily_trend[0].date == "2026-10-17T00:00:00Z"
    assert (d.daily_trend[0].sent, d.daily_trend[0].received) == (4, 2)
    mb = d.mailboxes[0]
    assert (mb.email_account_id, mb.email, mb.track_direct_mail) == (
        "acc_1",
        "me@acme.test",
        True,
    )
    assert (mb.sent, mb.received) == (40, 25)
    c = d.top_contacts[0]
    assert (c.email, c.sent, c.received) == ("x@y.test", 6, 3)
    assert c.last_at == "2026-10-17T12:00:00Z"


@respx.mock
def test_analytics_direct(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(200, json=DIRECT)
    )
    _check_direct(client.analytics.direct(period="30d"))
    assert _qp(route) == {"period": "30d"}
    client.analytics.direct()
    assert _qp(route) == {}


@pytest.mark.anyio
@respx.mock
async def test_analytics_direct_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(200, json=DIRECT)
    )
    _check_direct(await aclient.analytics.direct(period="30d"))
    assert _qp(route) == {"period": "30d"}


# ===========================================================================
# analytics: inbox tagging review
# ===========================================================================
TAGGING = {
    "enabled": True,
    "data": [
        {
            "id": "tag_1",
            "message_id": "<m@x>",
            "thread_id": "th_1",
            "kind": "human",
            "kind_confidence": 0.9,
            "kind_source": "model",
            "intent": "not_now",
            "intent_confidence": 0.8,
            "relevance": 70,
            "priority": "high",
            "needs_review": True,
            "review_reason": "low confidence",
            "labels": ["interested"],
            "answers": {"q1": "yes"},
            "model": "m-1",
            "input_tokens": 120,
            "actions": ["hold"],
            "return_date": "2026-11-02",
            "created_at": "2026-10-17T10:00:00Z",
        }
    ],
    "total": 41,
    "summary": {"total": 41, "needs_review": 5, "from_offline": 1, "acted": 7},
    "pagination": {"next_cursor": "off50", "has_more": True},
}


def _check_tagging(r: Any) -> None:
    assert r.enabled is True
    assert r.total == 41
    assert r.pagination == {"next_cursor": "off50", "has_more": True}
    s = r.summary
    assert (s.total, s.needs_review, s.from_offline, s.acted) == (41, 5, 1, 7)
    row = r.data[0]
    assert (row.id, row.message_id, row.thread_id) == ("tag_1", "<m@x>", "th_1")
    assert (row.kind, row.kind_confidence, row.kind_source) == ("human", 0.9, "model")
    assert (row.intent, row.intent_confidence) == ("not_now", 0.8)
    assert (row.relevance, row.priority) == (70, "high")
    assert (row.needs_review, row.review_reason) == (True, "low confidence")
    assert row.labels == ["interested"]
    assert row.answers == {"q1": "yes"}
    assert (row.model, row.input_tokens) == ("m-1", 120)
    assert row.actions == ["hold"]
    assert row.return_date == "2026-11-02"
    assert row.created_at == "2026-10-17T10:00:00Z"


@respx.mock
def test_analytics_inbox_tagging(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(200, json=TAGGING)
    )
    _check_tagging(
        client.analytics.inbox_tagging(limit=50, cursor="off0", needs_review=True)
    )
    assert _qp(route) == {"limit": "50", "cursor": "off0", "needs_review": "true"}
    client.analytics.inbox_tagging()
    assert _qp(route) == {}


@pytest.mark.anyio
@respx.mock
async def test_analytics_inbox_tagging_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(200, json=TAGGING)
    )
    _check_tagging(await aclient.analytics.inbox_tagging(needs_review=False))
    assert _qp(route) == {"needs_review": "false"}


# ===========================================================================
# analytics: warmup placement
# ===========================================================================
METRIC = {
    "version": "observed-v2",
    "population": "warmup_pool",
    "denominator_kind": "classified_observed_receipts",
    "unit": "percent",
    "source": "mailbox_observation",
    "classification_policy": "first_folder_v2_with_legacy_classifications",
    "numerator": 9,
    "denominator": 10,
    "unresolved": 1,
    "window_days": 7,
    "window_basis": "trailing_utc_days",
    "missingness_basis": "unclassified_observed_receipts",
    "value": 90.0,
    "wilson_95_independence_interval": {"lower": 60.0, "upper": 98.0},
}
COUNTS = {
    "sent": 12,
    "delivered": 10,
    "inbox": 7,
    "tabs": 2,
    "spam": 1,
    "unknown": 1,
    "archived": 0,
    "custom": 0,
    "instrumented_receipts": 9,
    "observed_receipts": 11,
    "legacy_uninstrumented_receipts": 2,
    "rescue_requested": 1,
    "rescue_confirmed": None,
    "non_spam_metric": METRIC,
    "rescued": 1,
    "unconfirmed": 1,
    "inbox_rate": 90.0,
    "spam_rate": 10.0,
}
RATE = {
    "window_days": 7,
    "min_sample": 20,
    "scope": "major",
    "delivered": 10,
    "inbox": 7,
    "tabs": 2,
    "spam": 1,
    "inbox_rate": None,
    "band": "collecting",
    "metric": METRIC,
    "other_delivered": 4,
    "other_inbox_rate": 75.0,
}
PLACEMENT = {
    "email_account_id": "acc_1",
    "date_range": {"from": "2026-10-01T00:00:00Z", "to": "2026-10-02T00:00:00Z"},
    "summary": COUNTS,
    "rate": RATE,
    "daily": [
        {
            **COUNTS,
            "date": "2026-10-01",
            "rolling_inbox_rate": 88.5,
            "groups": [
                {
                    "group": "google",
                    "inbox": 5,
                    "tabs": 1,
                    "spam": 0,
                    "rescued": 0,
                    "unknown": 0,
                    "archived": 0,
                    "custom": 0,
                }
            ],
        }
    ],
    "providers": [
        {**COUNTS, "group": "google", "hosts": [{**COUNTS, "host": "gmail"}]}
    ],
    "mailboxes": [
        {
            **COUNTS,
            "email_account_id": "acc_1",
            "email": "a@acme.test",
            "rate": RATE,
            "daily_inbox_rate": [88.5, None],
        }
    ],
}


def _check_counts(c: Any) -> None:
    assert (c.sent, c.delivered, c.inbox, c.tabs, c.spam) == (12, 10, 7, 2, 1)
    assert (c.unknown, c.archived, c.custom) == (1, 0, 0)
    assert (c.instrumented_receipts, c.observed_receipts) == (9, 11)
    assert c.legacy_uninstrumented_receipts == 2
    assert (c.rescue_requested, c.rescue_confirmed) == (1, None)
    assert (c.rescued, c.unconfirmed) == (1, 1)
    assert (c.inbox_rate, c.spam_rate) == (90.0, 10.0)
    m = c.non_spam_metric
    assert m is not None
    assert (m.version, m.population, m.unit) == (
        "observed-v2",
        "warmup_pool",
        "percent",
    )
    assert (m.numerator, m.denominator, m.unresolved, m.value) == (9, 10, 1, 90.0)
    assert m.wilson_95_independence_interval == {"lower": 60.0, "upper": 98.0}
    assert m.window_days == 7


def _check_rate(r: Any) -> None:
    assert (r.window_days, r.min_sample, r.scope) == (7, 20, "major")
    assert (r.delivered, r.inbox, r.tabs, r.spam) == (10, 7, 2, 1)
    assert r.inbox_rate is None
    assert r.band == "collecting"
    assert r.metric is not None and r.metric.numerator == 9
    assert (r.other_delivered, r.other_inbox_rate) == (4, 75.0)


def _check_placement(r: Any) -> None:
    assert r.email_account_id == "acc_1"
    assert r.date_range == {
        "from": "2026-10-01T00:00:00Z",
        "to": "2026-10-02T00:00:00Z",
    }
    _check_counts(r.summary)
    _check_rate(r.rate)
    day = r.daily[0]
    _check_counts(day)
    assert (day.date, day.rolling_inbox_rate) == ("2026-10-01", 88.5)
    g = day.groups[0]
    assert (g.group, g.inbox, g.tabs, g.spam, g.rescued) == ("google", 5, 1, 0, 0)
    assert (g.unknown, g.archived, g.custom) == (0, 0, 0)
    prov = r.providers[0]
    _check_counts(prov)
    assert prov.group == "google"
    assert prov.hosts[0].host == "gmail"
    _check_counts(prov.hosts[0])
    mb = r.mailboxes[0]
    _check_counts(mb)
    assert (mb.email_account_id, mb.email) == ("acc_1", "a@acme.test")
    _check_rate(mb.rate)
    assert mb.daily_inbox_rate == [88.5, None]


@respx.mock
def test_analytics_warmup_placement(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(200, json=PLACEMENT)
    )
    _check_placement(
        client.analytics.warmup_placement(
            email_id="acc_1", from_="2026-10-01", to="2026-10-02"
        )
    )
    assert _qp(route) == {
        "email_id": "acc_1",
        "from": "2026-10-01",
        "to": "2026-10-02",
    }
    client.analytics.warmup_placement()
    assert _qp(route) == {}


@pytest.mark.anyio
@respx.mock
async def test_analytics_warmup_placement_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(200, json=PLACEMENT)
    )
    _check_placement(
        await aclient.analytics.warmup_placement(
            email_id="acc_1", from_="2026-10-01", to="2026-10-02"
        )
    )
    assert _qp(route)["email_id"] == "acc_1"
