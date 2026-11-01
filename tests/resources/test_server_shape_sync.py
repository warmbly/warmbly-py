"""Tests for the response and request shapes the server added to existing routes.

Each test asserts the request method, path, query and body that reach the wire
and that the decoded response attributes are populated, on both the sync and
async clients.
"""

from __future__ import annotations

import json
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


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


FORM = {
    "id": "frm_1",
    "name": "Demo request",
    "status": "published",
    "redirect_url": "https://acme.com/thanks",
    "redirect_url_active": False,
    "captcha_enabled": True,
    "triage_enabled": True,
}


# -- forms ------------------------------------------------------------------


@respx.mock
def test_forms_triage_sync(client: Warmbly) -> None:
    update = respx.patch(f"{BASE_URL}/forms/frm_1").mock(
        return_value=httpx.Response(200, json=FORM)
    )
    form = client.forms.update("frm_1", triage_enabled=True)
    assert _last(update).method == "PATCH"
    assert json.loads(_last(update).content) == {"triage_enabled": True}
    assert form.triage_enabled is True
    assert form.redirect_url_active is False

    respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(
            200,
            json={
                "base_url": "https://forms.warmbly.com",
                "captcha_available": True,
                "triage_available": True,
            },
        )
    )
    assert client.forms.config().triage_available is True

    respx.get(f"{BASE_URL}/forms/domain").mock(
        return_value=httpx.Response(
            200,
            json={
                "forms_domain": "forms.acme.com",
                "forms_domain_verified": False,
                "cname_target": "forms.warmbly.com",
                "txt_name": "_warmbly.forms.acme.com",
                "txt_value": "warmbly-verify=abc",
                "status": "proof_missing",
                "message": "Add the TXT record.",
            },
        )
    )
    domain = client.forms.domain()
    assert domain.status == "proof_missing"
    assert domain.txt_name == "_warmbly.forms.acme.com"
    assert domain.txt_value == "warmbly-verify=abc"

    respx.get(f"{BASE_URL}/forms/frm_1/submissions").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "sub_1",
                        "form_id": "frm_1",
                        "data": {"email": "a@b.co"},
                        "triage": "buyer",
                        "triage_confidence": 0.93,
                    }
                ]
            ),
        )
    )
    sub = next(iter(client.forms.list_submissions("frm_1")))
    assert sub.triage == "buyer"
    assert sub.triage_confidence == pytest.approx(0.93)


@pytest.mark.anyio
@respx.mock
async def test_forms_triage_async(aclient: AsyncWarmbly) -> None:
    update = respx.patch(f"{BASE_URL}/forms/frm_1").mock(
        return_value=httpx.Response(200, json=FORM)
    )
    form = await aclient.forms.update("frm_1", triage_enabled=False)
    assert json.loads(_last(update).content) == {"triage_enabled": False}
    assert form.redirect_url_active is False

    respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(200, json={"triage_available": False})
    )
    assert (await aclient.forms.config()).triage_available is False


# -- segments ---------------------------------------------------------------


@respx.mock
def test_segments_select_all_and_option_labels_sync(client: Warmbly) -> None:
    members = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 42})
    )
    result = client.segments.set_members(
        "seg_1",
        mode="exclude",
        all=True,
        filters={"search": "acme"},
        exclude=["c_9"],
    )
    assert result.updated == 42
    assert json.loads(_last(members).content) == {
        "mode": "exclude",
        "all": True,
        "filters": {"search": "acme"},
        "exclude": ["c_9"],
    }

    client.segments.set_members("seg_1", mode="include", contacts=["c_1", "c_2"])
    assert json.loads(_last(members).content) == {
        "mode": "include",
        "contacts": ["c_1", "c_2"],
    }

    respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "field": "mail_host",
                        "label": "Email provider",
                        "group": "Contact",
                        "kind": "enum",
                        "options": ["google", "microsoft"],
                        "option_labels": {"google": "Google", "microsoft": "Microsoft"},
                    }
                ]
            ),
        )
    )
    field = next(iter(client.segments.fields()))
    assert field.option_labels == {"google": "Google", "microsoft": "Microsoft"}


@pytest.mark.anyio
@respx.mock
async def test_segments_select_all_async(aclient: AsyncWarmbly) -> None:
    members = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 7})
    )
    result = await aclient.segments.set_members("seg_1", mode="auto", all=True)
    assert result.updated == 7
    assert json.loads(_last(members).content) == {"mode": "auto", "all": True}


# -- lead sync --------------------------------------------------------------

SOURCE = {
    "id": "src_1",
    "provider": "google_sheets",
    "category_ids": ["cat_1"],
    "segment_ids": ["seg_1", "seg_2"],
    "subscribed_default": True,
    "status": "active",
}


@respx.mock
def test_lead_sync_segment_ids_sync(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json=SOURCE)
    )
    source = client.lead_sync.create_source(
        connection_id="conn_1",
        sheet_id="sheet_1",
        column_mapping=[{"column": 0, "field": "email"}],
        segment_ids=["seg_1", "seg_2"],
    )
    assert json.loads(_last(create).content)["segment_ids"] == ["seg_1", "seg_2"]
    assert list(source.segment_ids) == ["seg_1", "seg_2"]

    update = respx.patch(f"{BASE_URL}/lead-sync/sources/src_1").mock(
        return_value=httpx.Response(200, json=SOURCE)
    )
    client.lead_sync.update_source("src_1", segment_ids=[])
    assert json.loads(_last(update).content) == {"segment_ids": []}

    listing = respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(200, json=_page([SOURCE]))
    )
    rows = list(client.lead_sync.list_sources(segment_id="seg_1"))
    assert dict(_last(listing).url.params) == {"segment_id": "seg_1"}
    assert list(rows[0].segment_ids) == ["seg_1", "seg_2"]


@pytest.mark.anyio
@respx.mock
async def test_lead_sync_segment_ids_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json=SOURCE)
    )
    source = await aclient.lead_sync.create_source(
        connection_id="conn_1",
        sheet_id="sheet_1",
        column_mapping=[],
        segment_ids=["seg_1"],
    )
    assert json.loads(_last(create).content)["segment_ids"] == ["seg_1"]
    assert list(source.segment_ids) == ["seg_1", "seg_2"]

    listing = respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(200, json=_page([SOURCE]))
    )
    rows = [s async for s in aclient.lead_sync.list_sources(segment_id="seg_2")]
    assert dict(_last(listing).url.params) == {"segment_id": "seg_2"}
    assert rows[0].id == "src_1"


# -- plans, outreach, teams -------------------------------------------------


@respx.mock
def test_plan_price_yearly_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(
            200,
            json={
                "plans": [
                    {
                        "id": "plan_1",
                        "name": "Pro",
                        "price": 99.0,
                        "price_yearly": 990.0,
                        "duration": "month",
                        "dedicated_workers": 1,
                    },
                    {"id": "plan_2", "name": "Lite", "price": 19.0},
                ]
            },
        )
    )
    plans = list(client.plans.list())
    assert plans[0].price_yearly == pytest.approx(990.0)
    assert plans[1].price_yearly is None


@pytest.mark.anyio
@respx.mock
async def test_plan_price_yearly_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(
            200, json={"plans": [{"id": "plan_1", "price_yearly": 990.0}]}
        )
    )
    plans = [p async for p in aclient.plans.list()]
    assert plans[0].price_yearly == pytest.approx(990.0)


OUTREACH = {
    "bounce_pipeline": {"enabled": True},
    "reply_intent": {"enabled": True, "hold_on_out_of_office": True},
    "inbox_tagging": {"hold_on_not_now": True, "not_now_hold_days": 14},
}


@respx.mock
def test_outreach_inbox_tagging_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(200, json=OUTREACH)
    )
    settings = client.outreach.settings()
    assert settings.inbox_tagging == {"hold_on_not_now": True, "not_now_hold_days": 14}

    patch = respx.patch(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(204)
    )
    client.outreach.update_settings(settings=OUTREACH)
    assert json.loads(_last(patch).content) == {"settings": OUTREACH}


@pytest.mark.anyio
@respx.mock
async def test_outreach_inbox_tagging_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(200, json=OUTREACH)
    )
    settings = await aclient.outreach.settings()
    assert settings.inbox_tagging is not None
    assert settings.inbox_tagging["not_now_hold_days"] == 14


TEAM = {
    "id": "tm_1",
    "organization_id": "org_1",
    "name": "Sales",
    "color": "#94a3b8",
    "members": [
        {
            "user_id": "u_1",
            "email": "a@acme.com",
            "name": "Ada",
            "added_at": "2026-01-01T00:00:00Z",
        }
    ],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}


@respx.mock
def test_team_shape_sync(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(201, json=TEAM)
    )
    team = client.teams.create(name="Sales", color="#94a3b8")
    assert json.loads(_last(create).content) == {"name": "Sales", "color": "#94a3b8"}
    assert team.name == "Sales"
    assert team.members[0].email == "a@acme.com"
    assert not hasattr(team, "member_count")


@pytest.mark.anyio
@respx.mock
async def test_team_shape_async(aclient: AsyncWarmbly) -> None:
    update = respx.patch(f"{BASE_URL}/teams/tm_1").mock(
        return_value=httpx.Response(200, json=TEAM)
    )
    team = await aclient.teams.update("tm_1", name="Sales")
    assert json.loads(_last(update).content) == {"name": "Sales"}
    assert team.color == "#94a3b8"


# -- unibox -----------------------------------------------------------------

PREVIEW = {
    "id": "msg_1",
    "email_id": "mbx_1",
    "answers_mailbox_id": "mbx_2",
    "thread_id": "thr_1",
    "subject": "Re: hello",
    "seen": False,
}


@respx.mock
def test_unibox_list_and_reads_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([PREVIEW]))
    )
    rows = list(client.unibox.list(automated=False, include_archived=True))
    params = dict(_last(listing).url.params)
    assert params == {"automated": "false", "include_archived": "true"}
    assert rows[0].answers_mailbox_id == "mbx_2"

    client.unibox.list(automated=True)
    assert dict(_last(listing).url.params) == {"automated": "true"}

    client.unibox.list()
    assert dict(_last(listing).url.params) == {}

    respx.get(f"{BASE_URL}/unibox/msg_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_1",
                "email_id": "mbx_1",
                "folder": "archive",
                "subject": "hello",
                "from": ["a@b.co"],
            },
        )
    )
    message = client.unibox.retrieve("msg_1")
    assert message.email_id == "mbx_1"
    assert message.folder == "archive"

    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "unread": 3,
                "automated": 12,
                "automated_unread": 5,
                "drafts": 2,
                "awaiting_agent_draft": 1,
            },
        )
    )
    overview = client.unibox.overview()
    assert (overview.automated, overview.automated_unread, overview.drafts) == (
        12,
        5,
        2,
    )


@respx.mock
def test_unibox_writes_sync(client: Warmbly) -> None:
    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(
            200, json={"email_ids": None, "thread_ids": ["thr_1"], "seen": True}
        )
    )
    result = client.unibox.mark_seen(thread_ids=["thr_1"])
    assert json.loads(_last(seen).content) == {"thread_ids": ["thr_1"], "seen": True}
    assert list(result.thread_ids) == ["thr_1"]

    reply = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(
            200, json={"task_id": "t_1", "scheduled_at": "2026-01-01T00:00:00Z"}
        )
    )
    sent = client.unibox.reply(
        email_account_id="mbx_1",
        to=["x@y.co"],
        subject="Fwd: hello",
        body_html="<p>FYI</p>",
        forward_message_id="msg_1",
    )
    assert json.loads(_last(reply).content)["forward_message_id"] == "msg_1"
    assert sent.task_id == "t_1"


@respx.mock
def test_unibox_snooze_many_sync(client: Warmbly) -> None:
    rows = [
        {"id": "s_1", "thread_id": "thr_1", "snoozed_until": "2026-02-01T00:00:00Z"},
        {"id": "s_2", "thread_id": "thr_2", "snoozed_until": "2026-02-01T00:00:00Z"},
    ]
    route = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(200, json={"data": rows})
    )
    batch = client.unibox.snooze_many(
        thread_ids=["thr_1", "thr_2"], snoozed_until="2026-02-01T00:00:00Z"
    )
    assert json.loads(_last(route).content) == {
        "thread_ids": ["thr_1", "thr_2"],
        "snoozed_until": "2026-02-01T00:00:00Z",
    }
    assert [s.thread_id for s in batch.data] == ["thr_1", "thr_2"]

    # One thread comes back as the bare row; the batch still holds it.
    route.mock(return_value=httpx.Response(200, json=rows[0]))
    single = client.unibox.snooze_many(
        thread_ids=["thr_1"], snoozed_until="2026-02-01T00:00:00Z"
    )
    assert [s.id for s in single.data] == ["s_1"]

    gone = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    client.unibox.unsnooze(thread_ids=["thr_1", "thr_2"])
    assert dict(_last(gone).url.params) == {"thread_id": "thr_1,thr_2"}
    client.unibox.unsnooze(thread_id="thr_1")
    assert dict(_last(gone).url.params) == {"thread_id": "thr_1"}


@pytest.mark.anyio
@respx.mock
async def test_unibox_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([PREVIEW]))
    )
    rows = [m async for m in aclient.unibox.list(automated=True, include_archived=True)]
    assert dict(_last(listing).url.params) == {
        "automated": "true",
        "include_archived": "true",
    }
    assert rows[0].answers_mailbox_id == "mbx_2"

    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"thread_ids": ["thr_1"], "seen": False})
    )
    result = await aclient.unibox.mark_seen(
        email_ids=["msg_1"], thread_ids=["thr_1"], seen=False
    )
    assert json.loads(_last(seen).content) == {
        "email_ids": ["msg_1"],
        "thread_ids": ["thr_1"],
        "seen": False,
    }
    assert result.seen is False

    reply = respx.post(f"{BASE_URL}/unibox/reply").mock(
        return_value=httpx.Response(200, json={"task_id": "t_2"})
    )
    sent = await aclient.unibox.reply(
        email_account_id="mbx_1",
        to=["x@y.co"],
        subject="Fwd: hello",
        forward_message_id="msg_1",
    )
    assert json.loads(_last(reply).content)["forward_message_id"] == "msg_1"
    assert sent.task_id == "t_2"

    snooze = respx.post(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "s_1", "thread_id": "thr_1"}]},
        )
    )
    batch = await aclient.unibox.snooze_many(
        thread_ids=["thr_1"], snoozed_until="2026-02-01T00:00:00Z"
    )
    assert json.loads(_last(snooze).content)["thread_ids"] == ["thr_1"]
    assert batch.data[0].thread_id == "thr_1"

    gone = respx.delete(f"{BASE_URL}/unibox/snooze").mock(
        return_value=httpx.Response(204)
    )
    await aclient.unibox.unsnooze(thread_ids=["a", "b"])
    assert dict(_last(gone).url.params) == {"thread_id": "a,b"}

    respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(200, json={"automated": 4, "drafts": 1})
    )
    overview = await aclient.unibox.overview()
    assert (overview.automated, overview.drafts) == (4, 1)
