"""Campaign placement monitor, send plan, per-lead hold and CC, plus new fields.

Each test runs against the sync and the async client; ``call`` awaits when the
method returned a coroutine.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture(params=["sync", "async"])
async def api(request: pytest.FixtureRequest) -> AsyncIterator[Any]:
    if request.param == "sync":
        c = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
        yield c
        c.close()
    else:
        async with AsyncWarmbly(
            api_key="wmbly_test", base_url=BASE_URL, max_retries=0
        ) as ac:
            yield ac


async def call(fn: Any, *args: Any, **kwargs: Any) -> Any:
    result = fn(*args, **kwargs)
    if inspect.isawaitable(result):
        result = await result
    return result


MONITOR = {
    "id": "pm_1",
    "campaign_id": "camp_1",
    "created_by": "user_1",
    "enabled": True,
    "interval_days": 7,
    "panel": "workspace",
    "alert_below": 60,
    "pause_on_alert": True,
    "next_run_at": "2026-10-05T00:00:00Z",
    "last_run_at": "2026-09-28T00:00:00Z",
    "last_test_id": "pt_1",
    "last_alert_at": None,
    "last_error": "seed unreachable",
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-09-28T00:00:00Z",
}


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_get(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/camp_1/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    result = await call(api.campaigns.placement_monitor, "camp_1")
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns/camp_1/placement-monitor"
    assert result.data is not None
    assert result.data.id == "pm_1"
    assert result.data.interval_days == 7
    assert result.data.panel == "workspace"
    assert result.data.pause_on_alert is True
    assert result.data.last_error == "seed unreachable"


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_get_none(api: Any) -> None:
    respx.get(f"{BASE_URL}/campaigns/camp_1/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": None})
    )
    result = await call(api.campaigns.placement_monitor, "camp_1")
    assert result.data is None


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_put(api: Any) -> None:
    route = respx.put(f"{BASE_URL}/campaigns/camp_1/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    result = await call(
        api.campaigns.set_placement_monitor,
        "camp_1",
        enabled=True,
        interval_days=7,
        panel="workspace",
        alert_below=60,
        pause_on_alert=True,
    )
    request = route.calls.last.request
    assert request.method == "PUT"
    assert request.url.path == "/v1/campaigns/camp_1/placement-monitor"
    assert json.loads(request.content) == {
        "enabled": True,
        "interval_days": 7,
        "panel": "workspace",
        "alert_below": 60,
        "pause_on_alert": True,
    }
    assert "idempotency-key" not in request.headers
    assert result.data is not None
    assert result.data.alert_below == 60


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_put_partial(api: Any) -> None:
    route = respx.put(f"{BASE_URL}/campaigns/camp_1/placement-monitor").mock(
        return_value=httpx.Response(200, json={"data": MONITOR})
    )
    await call(api.campaigns.set_placement_monitor, "camp_1", enabled=False)
    assert json.loads(route.calls.last.request.content) == {"enabled": False}


@pytest.mark.anyio
@respx.mock
async def test_placement_monitor_delete(api: Any) -> None:
    route = respx.delete(f"{BASE_URL}/campaigns/camp_1/placement-monitor").mock(
        return_value=httpx.Response(204)
    )
    result = await call(api.campaigns.delete_placement_monitor, "camp_1")
    request = route.calls.last.request
    assert request.method == "DELETE"
    assert request.url.path == "/v1/campaigns/camp_1/placement-monitor"
    assert result.id is None


PLAN = {
    "campaign_id": "camp_1",
    "status": "active",
    "day": "2026-10-04",
    "timezone": "Europe/Berlin",
    "computed_at": "2026-10-04T09:00:00Z",
    "stale": False,
    "configured_ceiling": 100,
    "projected_today": 60,
    "sent_today": 20,
    "expected_remaining": 40,
    "bottleneck": "warmup_graduation",
    "limits": [
        {"kind": "warmup_graduation", "emails": 30, "mailboxes": 2},
        {"kind": "campaign_daily_limit", "emails": 10},
    ],
    "window": {
        "sending_day": True,
        "open_now": True,
        "closes_at": "2026-10-04T16:00:00Z",
        "minutes_left": 300,
    },
    "leads": {
        "due_now": 12,
        "due_later_today": 5,
        "new_leads_due_today": 9,
        "waiting_on_step": 40,
        "waiting_on_condition": 2,
        "held": 1,
        "waiting_on_sender": 3,
        "new_leads_started_today": 4,
        "max_new_leads_per_day": 50,
        "next_due_at": "2026-10-04T10:00:00Z",
    },
    "mailboxes": [
        {
            "id": "ea_1",
            "email": "a@example.com",
            "provider": "google",
            "configured_cap": 50,
            "cap_today": 30,
            "limited_by": "warmup_graduation",
            "sent_today": 10,
            "sent_by_other_campaigns": 2,
            "expected_remaining": 18,
            "state": "sending",
            "min_gap_seconds": 90,
            "graduation": {
                "ceiling": 30,
                "mailbox_cap": 50,
                "days_to_full_cap": 4,
                "held": False,
            },
        }
    ],
    "organization": {"daily_limit": 500, "sent_today": 120, "remaining": 380},
    "next_wake_at": "2026-10-04T09:05:00Z",
}


@pytest.mark.anyio
@respx.mock
async def test_send_plan(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/camp_1/send-plan").mock(
        return_value=httpx.Response(200, json=PLAN)
    )
    plan = await call(api.campaigns.send_plan, "camp_1")
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns/camp_1/send-plan"
    assert plan.configured_ceiling == 100
    assert plan.projected_today == 60
    assert plan.bottleneck == "warmup_graduation"
    assert plan.stale is False
    assert [limit.kind for limit in plan.limits] == [
        "warmup_graduation",
        "campaign_daily_limit",
    ]
    assert plan.limits[0].mailboxes == 2
    assert plan.window is not None and plan.window.minutes_left == 300
    assert plan.leads is not None and plan.leads.due_now == 12
    assert plan.leads.max_new_leads_per_day == 50
    assert plan.mailboxes[0].cap_today == 30
    assert plan.mailboxes[0].graduation is not None
    assert plan.mailboxes[0].graduation.days_to_full_cap == 4
    assert plan.organization is not None and plan.organization.remaining == 380
    assert plan.next_wake_at == "2026-10-04T09:05:00Z"


HOLD = {
    "campaign_id": "camp_1",
    "contact_id": "c_1",
    "hold": {
        "since": "2026-10-04T08:00:00Z",
        "until": "2026-10-20T00:00:00Z",
        "reason": "on leave",
        "source": "manual",
    },
}


@pytest.mark.anyio
@respx.mock
async def test_lead_hold(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/camp_1/leads/c_1/hold").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    result = await call(api.campaigns.lead_hold, "camp_1", "c_1")
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns/camp_1/leads/c_1/hold"
    assert result.contact_id == "c_1"
    assert result.hold is not None
    assert result.hold.source == "manual"
    assert result.hold.until == "2026-10-20T00:00:00Z"
    assert result.hold.reason == "on leave"


@pytest.mark.anyio
@respx.mock
async def test_lead_hold_none(api: Any) -> None:
    respx.get(f"{BASE_URL}/campaigns/camp_1/leads/c_1/hold").mock(
        return_value=httpx.Response(
            200, json={"campaign_id": "camp_1", "contact_id": "c_1"}
        )
    )
    result = await call(api.campaigns.lead_hold, "camp_1", "c_1")
    assert result.hold is None


@pytest.mark.anyio
@respx.mock
async def test_pause_lead(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/leads/c_1/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    result = await call(
        api.campaigns.pause_lead,
        "camp_1",
        "c_1",
        until="2026-10-20T00:00:00Z",
        reason="on leave",
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/campaigns/camp_1/leads/c_1/pause"
    assert json.loads(request.content) == {
        "until": "2026-10-20T00:00:00Z",
        "reason": "on leave",
    }
    assert result.hold is not None and result.hold.reason == "on leave"


@pytest.mark.anyio
@respx.mock
async def test_pause_lead_no_end(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/leads/c_1/pause").mock(
        return_value=httpx.Response(200, json=HOLD)
    )
    await call(api.campaigns.pause_lead, "camp_1", "c_1", until=None)
    assert json.loads(route.calls.last.request.content) == {"until": None}
    await call(api.campaigns.pause_lead, "camp_1", "c_1")
    assert json.loads(route.calls.last.request.content) == {}


@pytest.mark.anyio
@respx.mock
async def test_resume_lead(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/leads/c_1/resume").mock(
        return_value=httpx.Response(
            200, json={"campaign_id": "camp_1", "contact_id": "c_1"}
        )
    )
    result = await call(api.campaigns.resume_lead, "camp_1", "c_1")
    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/campaigns/camp_1/leads/c_1/resume"
    assert result.hold is None


CC = {
    "campaign_id": "camp_1",
    "contact_id": "c_1",
    "cc": [
        {
            "contact_id": "c_2",
            "email": "boss@example.com",
            "first_name": "Bo",
            "last_name": "Ss",
            "company": "Acme",
            "status": "bounced",
            "bounced_at": "2026-10-01T00:00:00Z",
        }
    ],
}


@pytest.mark.anyio
@respx.mock
async def test_lead_cc(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/camp_1/leads/c_1/cc").mock(
        return_value=httpx.Response(200, json=CC)
    )
    result = await call(api.campaigns.lead_cc, "camp_1", "c_1")
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns/camp_1/leads/c_1/cc"
    assert result.cc[0].email == "boss@example.com"
    assert result.cc[0].status == "bounced"
    assert result.cc[0].bounced_at == "2026-10-01T00:00:00Z"


@pytest.mark.anyio
@respx.mock
async def test_set_lead_cc(api: Any) -> None:
    route = respx.put(f"{BASE_URL}/campaigns/camp_1/leads/c_1/cc").mock(
        return_value=httpx.Response(200, json=CC)
    )
    result = await call(api.campaigns.set_lead_cc, "camp_1", "c_1", contact_ids=["c_2"])
    request = route.calls.last.request
    assert request.method == "PUT"
    assert request.url.path == "/v1/campaigns/camp_1/leads/c_1/cc"
    assert json.loads(request.content) == {"contact_ids": ["c_2"]}
    assert result.cc[0].company == "Acme"


@pytest.mark.anyio
@respx.mock
async def test_suggest_lead_cc(api: Any) -> None:
    route = respx.get(f"{BASE_URL}/campaigns/camp_1/leads/c_1/cc/suggestions").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "contact_id": "c_3",
                        "email": "cto@example.com",
                        "first_name": "C",
                        "last_name": "To",
                        "company": "Acme",
                        "reason": "domain",
                    }
                ]
            },
        )
    )
    result = await call(api.campaigns.suggest_lead_cc, "camp_1", "c_1")
    request = route.calls.last.request
    assert request.method == "GET"
    assert request.url.path == "/v1/campaigns/camp_1/leads/c_1/cc/suggestions"
    assert result.data[0].reason == "domain"
    assert result.data[0].contact_id == "c_3"


@pytest.mark.anyio
@respx.mock
async def test_create_with_entry_delay_and_campaign_fields(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "camp_1",
                "timezone": "",
                "effective_timezone": "Europe/Berlin",
                "entry_delay_minutes": 30,
            },
        )
    )
    campaign = await call(api.campaigns.create, name="X", entry_delay_minutes=30)
    assert json.loads(route.calls.last.request.content) == {
        "name": "X",
        "entry_delay_minutes": 30,
    }
    assert campaign.effective_timezone == "Europe/Berlin"
    assert campaign.entry_delay_minutes == 30

    patch = respx.patch(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1"})
    )
    await call(api.campaigns.update, "camp_1", entry_delay_minutes=0)
    assert json.loads(patch.calls.last.request.content) == {"entry_delay_minutes": 0}


@pytest.mark.anyio
@respx.mock
async def test_estimate_new_fields(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(
            200,
            json={
                "recipients": 100,
                "mailboxes": 2,
                "daily_capacity": 40,
                "remaining_today": 30,
                "sending_days": 3,
                "estimated_finish_at": "2026-10-07T00:00:00Z",
                "steps": 3,
                "total_sends": 300,
                "first_touch_finish_at": "2026-10-06T00:00:00Z",
                "steady_capacity": 60,
                "full_capacity_at": None,
                "ramping": 1,
                "held": 0,
                "warmup": {"mailboxes": 2, "per_day": 10},
                "other_campaigns_per_day": 5,
                "bottleneck": "warmup_graduation",
                "timeline": [{"date": "2026-10-04", "sends": 30}],
                "senders": [{"id": "ea_1", "state": "ramping"}],
            },
        )
    )
    est = await call(
        api.campaigns.estimate,
        segment_ids=["s_1"],
        start_time="09:00",
        end_time="17:00",
        step_waits=[2, 3],
        campaign_id="camp_1",
    )
    assert json.loads(route.calls.last.request.content) == {
        "segment_ids": ["s_1"],
        "start_time": "09:00",
        "end_time": "17:00",
        "step_waits": [2, 3],
        "campaign_id": "camp_1",
    }
    assert est.total_sends == 300
    assert est.steady_capacity == 60
    assert est.bottleneck == "warmup_graduation"
    assert est.warmup == {"mailboxes": 2, "per_day": 10}
    assert est.timeline[0]["sends"] == 30
    assert est.senders[0]["state"] == "ramping"


@pytest.mark.anyio
@respx.mock
async def test_create_step_with_body_and_thread_reply(api: Any) -> None:
    route = respx.post(f"{BASE_URL}/campaigns/camp_1/steps").mock(
        return_value=httpx.Response(
            201, json={"id": "st_1", "subject": "Hi", "thread_reply": False}
        )
    )
    step = await call(
        api.campaigns.create_step,
        "camp_1",
        subject="Hi",
        wait_after=2,
        thread_reply=False,
    )
    assert json.loads(route.calls.last.request.content) == {
        "subject": "Hi",
        "wait_after": 2,
        "thread_reply": False,
    }
    assert step.thread_reply is False

    blank = await call(api.campaigns.create_step, "camp_1")
    assert route.calls.last.request.content == b""
    assert blank.id == "st_1"

    patch = respx.patch(f"{BASE_URL}/campaigns/camp_1/steps/st_1").mock(
        return_value=httpx.Response(200, json={"id": "st_1", "thread_reply": True})
    )
    updated = await call(api.campaigns.update_step, "camp_1", "st_1", thread_reply=True)
    assert json.loads(patch.calls.last.request.content) == {"thread_reply": True}
    assert updated.thread_reply is True
