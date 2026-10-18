"""Regression tests for the server-drift audit of the older resources."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly._exceptions import RateLimitError, make_status_error

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


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


# -- segments ----------------------------------------------------------------

FIELD = {
    "field": "mail_host",
    "label": "Email provider",
    "group": "Contact",
    "kind": "enum",
    "options": ["gmail", "outlook"],
    "option_labels": {"gmail": "Google", "outlook": "Microsoft"},
}


@respx.mock
def test_segment_fields_and_selection_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(200, json=_page([FIELD]))
    )
    field = next(iter(client.segments.fields()))
    assert field.option_labels == {"gmail": "Google", "outlook": "Microsoft"}
    assert field.options == ["gmail", "outlook"]

    members = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 4})
    )
    by_ids = client.segments.set_members("seg_1", mode="include", contacts=["c1"])
    assert by_ids.updated == 4
    assert json.loads(_last(members).content) == {"contacts": ["c1"], "mode": "include"}

    by_filter = client.segments.set_members(
        "seg_1",
        mode="exclude",
        select_all=True,
        filters={"query": "acme"},
        exclude=["c9"],
    )
    assert by_filter.updated == 4
    assert json.loads(_last(members).content) == {
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c9"],
        "mode": "exclude",
    }


@respx.mock
@pytest.mark.anyio
async def test_segment_fields_and_selection_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(200, json=_page([FIELD]))
    )
    fields = [f async for f in aclient.segments.fields()]
    assert fields[0].option_labels["gmail"] == "Google"

    members = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 2})
    )
    result = await aclient.segments.set_members(
        "seg_1", mode="auto", contacts=["c1", "c2"], select_all=False
    )
    assert result.updated == 2
    assert json.loads(_last(members).content) == {
        "contacts": ["c1", "c2"],
        "all": False,
        "mode": "auto",
    }


# -- forms -------------------------------------------------------------------

FORM = {
    "id": "f1",
    "organization_id": "o1",
    "public_id": "pub",
    "name": "Contact",
    "status": "published",
    "fields": [],
    "design": {},
    "category_ids": [],
    "allowed_domains": [],
    "captcha_enabled": True,
    "triage_enabled": True,
    "share_url": "https://forms.example/pub",
}
SUBMISSION = {
    "id": "s1",
    "form_id": "f1",
    "data": {"email": "a@b.co"},
    "source_url": "https://x",
    "triage": "buyer",
    "triage_confidence": 0.93,
}


@respx.mock
def test_forms_triage_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(
            200,
            json={
                "base_url": "https://forms.example",
                "captcha_available": True,
                "triage_available": True,
            },
        )
    )
    assert client.forms.config().triage_available is True

    update = respx.patch(f"{BASE_URL}/forms/f1").mock(
        return_value=httpx.Response(200, json=FORM)
    )
    form = client.forms.update("f1", triage_enabled=True)
    assert form.triage_enabled is True
    assert json.loads(_last(update).content) == {"triage_enabled": True}

    respx.get(f"{BASE_URL}/forms/f1/submissions").mock(
        return_value=httpx.Response(200, json=_page([SUBMISSION]))
    )
    sub = next(iter(client.forms.list_submissions("f1")))
    assert (sub.triage, sub.triage_confidence) == ("buyer", 0.93)


@respx.mock
@pytest.mark.anyio
async def test_forms_triage_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(
            200, json={"base_url": "u", "triage_available": False}
        )
    )
    assert (await aclient.forms.config()).triage_available is False

    update = respx.patch(f"{BASE_URL}/forms/f1").mock(
        return_value=httpx.Response(200, json=FORM)
    )
    form = await aclient.forms.update("f1", triage_enabled=False)
    assert form.triage_enabled is True
    assert json.loads(_last(update).content) == {"triage_enabled": False}

    respx.get(f"{BASE_URL}/forms/f1/submissions").mock(
        return_value=httpx.Response(200, json=_page([SUBMISSION]))
    )
    subs = [s async for s in aclient.forms.list_submissions("f1")]
    assert subs[0].triage == "buyer"


# -- outreach ----------------------------------------------------------------

TAGGING = {
    "hold_on_not_now": True,
    "not_now_hold_days": 30,
    "stop_on_declined": True,
    "questions": [],
    "languages": ["en"],
}


@respx.mock
def test_outreach_inbox_tagging_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(200, json={"inbox_tagging": TAGGING})
    )
    settings = client.outreach.settings()
    assert settings.inbox_tagging is not None
    assert settings.inbox_tagging["not_now_hold_days"] == 30


@respx.mock
@pytest.mark.anyio
async def test_outreach_inbox_tagging_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(200, json={"inbox_tagging": TAGGING})
    )
    settings = await aclient.outreach.settings()
    assert settings.inbox_tagging == TAGGING


# -- advisor -----------------------------------------------------------------


@respx.mock
def test_advisor_status_filter_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/advisor/recommendations").mock(
        return_value=httpx.Response(
            200, json=_page([{"id": "a1", "status": "snoozed", "severity": "high"}])
        )
    )
    found = list(client.advisor.list(status=["snoozed", "dismissed"]))
    assert found[0].status == "snoozed"
    assert _last(route).url.params.get_list("status") == ["snoozed", "dismissed"]


@respx.mock
@pytest.mark.anyio
async def test_advisor_status_filter_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/advisor/recommendations").mock(
        return_value=httpx.Response(200, json=_page([{"id": "a1"}]))
    )
    found = [f async for f in aclient.advisor.list(status=["applied"])]
    assert found[0].id == "a1"
    assert _last(route).url.params.get_list("status") == ["applied"]


# -- plans -------------------------------------------------------------------


@respx.mock
def test_plans_price_yearly_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(
            200,
            json={
                "plans": [
                    {
                        "id": "p1",
                        "name": "Pro",
                        "price": 99.0,
                        "price_yearly": 990.0,
                        "duration": "month",
                    }
                ]
            },
        )
    )
    plan = next(iter(client.plans.list()))
    assert plan.price_yearly == 990.0


@respx.mock
@pytest.mark.anyio
async def test_plans_price_yearly_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(
            200, json={"plans": [{"id": "p1", "price_yearly": 10.5}]}
        )
    )
    plans = [p async for p in aclient.plans.list()]
    assert plans[0].price_yearly == 10.5


# -- teams -------------------------------------------------------------------

TEAM = {
    "id": "t1",
    "organization_id": "o1",
    "name": "Sales",
    "color": "#94a3b8",
    "members": [{"user_id": "u1", "email": "a@b.co", "name": "A B"}],
}


@respx.mock
def test_teams_bodies_sync(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(201, json=TEAM)
    )
    team = client.teams.create(name="Sales", color="#94a3b8")
    assert team.members[0].email == "a@b.co"
    assert json.loads(_last(create).content) == {"name": "Sales", "color": "#94a3b8"}

    update = respx.patch(f"{BASE_URL}/teams/t1").mock(
        return_value=httpx.Response(200, json=TEAM)
    )
    client.teams.update("t1", name="Sales EU")
    assert json.loads(_last(update).content) == {"name": "Sales EU"}


@respx.mock
@pytest.mark.anyio
async def test_teams_bodies_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(201, json=TEAM)
    )
    team = await aclient.teams.create(name="Sales")
    assert team.name == "Sales"
    assert json.loads(_last(create).content) == {"name": "Sales"}

    update = respx.patch(f"{BASE_URL}/teams/t1").mock(
        return_value=httpx.Response(200, json=TEAM)
    )
    await aclient.teams.update("t1", color="#fff")
    assert json.loads(_last(update).content) == {"color": "#fff"}


# -- meetings ----------------------------------------------------------------


@respx.mock
def test_meetings_raw_payload_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/meetings").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [{"id": "m1", "source": "calendly", "raw_payload": {"event": "x"}}]
            ),
        )
    )
    meeting = next(iter(client.meetings.list()))
    assert meeting.raw_payload == {"event": "x"}


@respx.mock
@pytest.mark.anyio
async def test_meetings_raw_payload_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/meetings").mock(
        return_value=httpx.Response(
            200, json=_page([{"id": "m1", "raw_payload": {"a": 1}}])
        )
    )
    meetings = [m async for m in aclient.meetings.list()]
    assert meetings[0].raw_payload == {"a": 1}


# -- automations -------------------------------------------------------------

GRAPH = {"nodes": [{"id": "trigger", "type": "trigger", "x": 0, "y": 0}], "edges": []}
STORED = {
    "id": "au_1",
    "organization_id": "o1",
    "name": "Notify",
    "enabled": True,
    "trigger_event": "reply.received",
    "filter": {"min_confidence": 0.5},
    "graph": GRAPH,
    "inbound_url": "https://hooks/x",
}


@respx.mock
def test_automation_wrapper_and_update_sync(client: Warmbly) -> None:
    get = respx.get(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": STORED})
    )
    auto = client.automations.retrieve("au_1")
    assert auto.id == "au_1"
    assert auto.trigger_event == "reply.received"
    assert auto.graph == GRAPH
    assert auto.inbound_url == "https://hooks/x"
    assert auto.automation == STORED

    patch = respx.patch(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": STORED})
    )
    client.automations.update("au_1", enabled=False)
    assert get.call_count == 2
    assert json.loads(_last(patch).content) == {
        "name": "Notify",
        "trigger_event": "reply.received",
        "graph": GRAPH,
        "enabled": False,
        "filter": {"min_confidence": 0.5},
    }

    client.automations.update(
        "au_1",
        name="N",
        trigger_event="reply.received",
        graph=GRAPH,
        enabled=True,
        filter={},
    )
    assert get.call_count == 2
    assert json.loads(_last(patch).content) == {
        "name": "N",
        "trigger_event": "reply.received",
        "graph": GRAPH,
        "enabled": True,
        "filter": {},
    }


@respx.mock
@pytest.mark.anyio
async def test_automation_wrapper_and_update_async(aclient: AsyncWarmbly) -> None:
    get = respx.get(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": STORED})
    )
    patch = respx.patch(f"{BASE_URL}/automations/au_1").mock(
        return_value=httpx.Response(200, json={"automation": STORED})
    )
    updated = await aclient.automations.update("au_1", name="Renamed")
    assert updated.id == "au_1"
    assert get.call_count == 1
    assert json.loads(_last(patch).content) == {
        "name": "Renamed",
        "trigger_event": "reply.received",
        "graph": GRAPH,
        "enabled": True,
        "filter": {"min_confidence": 0.5},
    }

    await aclient.automations.update(
        "au_1",
        name="N",
        trigger_event="reply.received",
        graph=GRAPH,
        enabled=False,
        filter={},
    )
    assert get.call_count == 1
    assert json.loads(_last(patch).content)["enabled"] is False


@respx.mock
def test_automation_list_items_are_not_wrapped(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(200, json={"automations": [STORED]})
    )
    auto = next(iter(client.automations.list()))
    assert auto.id == "au_1"
    assert auto.model_extra is not None and "automation" not in auto.model_extra


# -- error envelope ----------------------------------------------------------


def test_error_request_id_falls_back_to_body() -> None:
    err = make_status_error(
        status_code=400,
        request_id=None,
        headers={},
        body={
            "error": "Bad Request",
            "message": "nope",
            "code": "bad_request",
            "request_id": "req-1",
        },
    )
    assert err.request_id == "req-1"
    assert err.code == "bad_request"

    kept = make_status_error(
        status_code=400,
        request_id="hdr",
        headers={},
        body={"message": "x", "request_id": "req-1"},
    )
    assert kept.request_id == "hdr"

    blank = make_status_error(
        status_code=500, request_id=None, headers={}, body={"request_id": 7}
    )
    assert blank.request_id is None


def test_rate_limit_envelope_uses_milliseconds_and_error_code() -> None:
    err = make_status_error(
        status_code=429,
        request_id=None,
        headers={"Retry-After": "0"},
        body={
            "error": "rate_limit_exceeded",
            "message": "Rate limit exceeded for write operations",
            "retry_after_ms": 1500,
        },
        retry_after=0.0,
    )
    assert isinstance(err, RateLimitError)
    assert err.retry_after == 1.5
    assert err.code == "rate_limit_exceeded"

    plain = make_status_error(
        status_code=429,
        request_id=None,
        headers={},
        body={"message": "slow down", "code": "too_many"},
        retry_after=2.0,
    )
    assert isinstance(plain, RateLimitError)
    assert plain.retry_after == 2.0
    assert plain.code == "too_many"

    bare = make_status_error(
        status_code=429, request_id=None, headers={}, body="busy", retry_after=None
    )
    assert isinstance(bare, RateLimitError)
    assert bare.retry_after is None
    assert bare.code is None
