"""Tests for the endpoints added to existing resources.

Covers the campaign estimate/duplicate/segment/form calls, the contact campaign,
segment and verification reads, the mailbox allowance, sync, hold/release,
tracking-domain and sending-behaviour calls, self-revocation of an API key, and
the unibox folder scope.
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


# ===========================================================================
# campaigns
# ===========================================================================
@respx.mock
def test_campaign_create_names_the_id_lists(client: Warmbly) -> None:
    """Create takes ``email_tag_ids``/``folder_ids``; update takes the plain names."""
    create = respx.post(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(201, json={"id": "camp_1"})
    )
    client.campaigns.create(
        name="Q4",
        kind="one_time",
        email_tags=["tag_1"],
        folders=["fol_1"],
        continuous=True,
        unsubscribe_mode="link",
        utm_tracking=True,
        utm_source="warmbly",
        guardrail_enabled=True,
        guardrail_bounce_rate_max=0.03,
        steps=[{"name": "Step 1", "subject": "Hi"}],
    )
    assert json.loads(_last(create).content) == {
        "name": "Q4",
        "kind": "one_time",
        "email_tag_ids": ["tag_1"],
        "folder_ids": ["fol_1"],
        "continuous": True,
        "unsubscribe_mode": "link",
        "utm_tracking": True,
        "utm_source": "warmbly",
        "guardrail_enabled": True,
        "guardrail_bounce_rate_max": 0.03,
        "steps": [{"name": "Step 1", "subject": "Hi"}],
    }

    update = respx.patch(f"{BASE_URL}/campaigns/camp_1").mock(
        return_value=httpx.Response(200, json={"id": "camp_1", "continuous": False})
    )
    campaign = client.campaigns.update(
        "camp_1", email_tags=["tag_2"], folders=["fol_2"], continuous=False
    )
    assert campaign.continuous is False
    assert json.loads(_last(update).content) == {
        "email_tags": ["tag_2"],
        "folders": ["fol_2"],
        "continuous": False,
    }


@respx.mock
def test_campaign_estimate_duplicate_segments_forms(client: Warmbly) -> None:
    estimate = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(
            200,
            json={
                "recipients": 1200,
                "mailboxes": 4,
                "daily_capacity": 120,
                "remaining_today": 80,
                "sending_days": 10,
                "estimated_finish_at": "2026-09-20T00:00:00Z",
            },
        )
    )
    projection = client.campaigns.estimate(
        segment_ids=["seg_1"], email_tag_ids=["tag_1"], daily_limit=30
    )
    assert projection.recipients == 1200
    assert projection.sending_days == 10
    assert json.loads(_last(estimate).content) == {
        "segment_ids": ["seg_1"],
        "email_tag_ids": ["tag_1"],
        "daily_limit": 30,
    }

    duplicate = respx.post(f"{BASE_URL}/campaigns/camp_1/duplicate").mock(
        return_value=httpx.Response(
            201, json={"id": "camp_2", "name": "Q4 copy", "status": "draft"}
        )
    )
    copy = client.campaigns.duplicate("camp_1", name="Q4 copy")
    assert copy.id == "camp_2"
    assert json.loads(_last(duplicate).content) == {"name": "Q4 copy"}

    read = respx.get(f"{BASE_URL}/campaigns/camp_1/segments").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "segment_id": "seg_1",
                        "name": "Acme",
                        "contact_count": 40,
                        "lead_count": 38,
                        "held_out_count": 2,
                    }
                ]
            },
        )
    )
    linked = client.campaigns.list_segments("camp_1")
    assert linked.data[0].held_out_count == 2
    assert _last(read).method == "GET"

    write = respx.put(f"{BASE_URL}/campaigns/camp_1/segments").mock(
        return_value=httpx.Response(
            200, json={"data": [{"segment_id": "seg_1"}], "added": 5}
        )
    )
    replaced = client.campaigns.set_segments("camp_1", segment_ids=["seg_1"])
    assert replaced.added == 5
    assert json.loads(_last(write).content) == {"segment_ids": ["seg_1"]}

    forms = respx.get(f"{BASE_URL}/campaigns/camp_1/forms").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"form_id": "frm_1", "links_sent": 100, "submissions": 9}]},
        )
    )
    performance = client.campaigns.list_forms("camp_1")
    assert performance.data[0].submissions == 9
    assert _last(forms).url.path == "/v1/campaigns/camp_1/forms"


@respx.mock
def test_campaign_preview_template_scoping(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/campaign-template-preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "subject": "Hi Ada",
                "from": {"name": "Ada", "email": "sales@acme.com"},
                "attachments": [{"id": "att_1", "filename": "deck.pdf"}],
            },
        )
    )
    preview = client.campaigns.preview_template(
        subject="Hi {{first_name}}",
        contact_id="con_1",
        campaign_id="camp_1",
        account_id="em_1",
        step_id="step_1",
    )
    assert preview.from_ == {"name": "Ada", "email": "sales@acme.com"}
    assert preview.attachments[0]["filename"] == "deck.pdf"
    assert json.loads(_last(route).content) == {
        "subject": "Hi {{first_name}}",
        "contact_id": "con_1",
        "campaign_id": "camp_1",
        "account_id": "em_1",
        "step_id": "step_1",
    }


@respx.mock
@pytest.mark.anyio
async def test_campaigns_async(aclient: AsyncWarmbly) -> None:
    estimate = respx.post(f"{BASE_URL}/campaigns-estimate").mock(
        return_value=httpx.Response(200, json={"recipients": 3, "sending_days": None})
    )
    projection = await aclient.campaigns.estimate(segment_ids=["seg_1"])
    assert projection.recipients == 3
    assert projection.sending_days is None
    assert _last(estimate).url.path == "/v1/campaigns-estimate"

    duplicate = respx.post(f"{BASE_URL}/campaigns/camp_1/duplicate").mock(
        return_value=httpx.Response(201, json={"id": "camp_2"})
    )
    assert (await aclient.campaigns.duplicate("camp_1")).id == "camp_2"
    assert json.loads(_last(duplicate).content) == {}

    read = respx.get(f"{BASE_URL}/campaigns/camp_1/segments").mock(
        return_value=httpx.Response(200, json={"data": [{"segment_id": "seg_1"}]})
    )
    assert (await aclient.campaigns.list_segments("camp_1")).data[
        0
    ].segment_id == "seg_1"
    assert _last(read).method == "GET"

    write = respx.put(f"{BASE_URL}/campaigns/camp_1/segments").mock(
        return_value=httpx.Response(200, json={"data": [], "added": 0})
    )
    detached = await aclient.campaigns.set_segments("camp_1", segment_ids=[])
    assert list(detached.data) == []
    assert json.loads(_last(write).content) == {"segment_ids": []}

    forms = respx.get(f"{BASE_URL}/campaigns/camp_1/forms").mock(
        return_value=httpx.Response(200, json={"data": [{"form_id": "frm_1"}]})
    )
    assert (await aclient.campaigns.list_forms("camp_1")).data[0].form_id == "frm_1"
    assert _last(forms).method == "GET"

    preview = respx.post(f"{BASE_URL}/campaign-template-preview").mock(
        return_value=httpx.Response(200, json={"subject": "s"})
    )
    assert (await aclient.campaigns.preview_template(subject="s")).subject == "s"
    assert _last(preview).method == "POST"


# ===========================================================================
# contacts
# ===========================================================================
@respx.mock
def test_contact_campaigns_segments_and_verification(client: Warmbly) -> None:
    campaigns = respx.get(f"{BASE_URL}/contacts/con_1/campaigns").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "campaign_id": "camp_1",
                        "lead_status": "active",
                        "completed_steps": 2,
                        "total_steps": 4,
                        "next": {"state": "waiting", "step_label": "Follow-up"},
                    }
                ]
            ),
        )
    )
    states = list(client.contacts.list_campaigns("con_1"))
    assert states[0].lead_status == "active"
    assert states[0].next == {"state": "waiting", "step_label": "Follow-up"}
    assert _last(campaigns).url.path == "/v1/contacts/con_1/campaigns"

    segments = respx.get(f"{BASE_URL}/contacts/con_1/segments").mock(
        return_value=httpx.Response(
            200, json=_page([{"id": "seg_1", "member": True, "mode": "include"}])
        )
    )
    memberships = list(client.contacts.list_segments("con_1"))
    assert memberships[0].member is True
    assert _last(segments).method == "GET"

    overview = respx.get(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200,
            json={
                "provider": "millionverifier",
                "credits": 4200,
                "builtin_ready": True,
                "counts": {"valid": 10, "risky": 1, "invalid": 2, "unknown": 0},
            },
        )
    )
    report = client.contacts.verification()
    assert report.credits == 4200
    assert report.counts == {"valid": 10, "risky": 1, "invalid": 2, "unknown": 0}
    assert _last(overview).url.path == "/v1/contacts/verification"

    request = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(
            200, json={"affected": 3, "action": "verify", "queued": True}
        )
    )
    result = client.contacts.request_verification(action="verify", contacts=["con_1"])
    assert result.queued is True
    assert json.loads(_last(request).content) == {
        "action": "verify",
        "contacts": ["con_1"],
    }


@respx.mock
def test_contact_timeline_cursor_and_search_facets(client: Warmbly) -> None:
    timeline = respx.get(f"{BASE_URL}/contacts/con_1/timeline").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "type": "email_clicked",
                        "at": "2026-09-01T10:00:00Z",
                        "machine": True,
                        "machine_reason": "security_gateway",
                        "link": {"id": "lnk_1", "url": "https://acme.com/pricing"},
                    }
                ]
            ),
        )
    )
    events = list(client.contacts.timeline("con_1", cursor="cur_1", limit=20))
    assert events[0].type == "email_clicked"
    assert events[0].machine is True
    assert events[0].link == {"id": "lnk_1", "url": "https://acme.com/pricing"}
    params = _last(timeline).url.params
    assert params.get("cursor") == "cur_1"
    assert params.get("limit") == "20"

    search = respx.post(f"{BASE_URL}/contacts/search").mock(
        return_value=httpx.Response(200, json=_page([{"id": "con_1"}]))
    )
    client.contacts.search(
        campaign_ids=["camp_1"],
        lead_status="active",
        engagement="opened",
        segment_ids=["seg_1"],
        verification_status="valid",
    )
    assert json.loads(_last(search).content) == {
        "campaign_ids": ["camp_1"],
        "lead_status": "active",
        "engagement": "opened",
        "segment_ids": ["seg_1"],
        "verification_status": "valid",
    }


@respx.mock
@pytest.mark.anyio
async def test_contacts_async(aclient: AsyncWarmbly) -> None:
    campaigns = respx.get(f"{BASE_URL}/contacts/con_1/campaigns").mock(
        return_value=httpx.Response(200, json=_page([{"campaign_id": "camp_1"}]))
    )
    assert [s.campaign_id async for s in aclient.contacts.list_campaigns("con_1")] == [
        "camp_1"
    ]
    assert _last(campaigns).method == "GET"

    segments = respx.get(f"{BASE_URL}/contacts/con_1/segments").mock(
        return_value=httpx.Response(200, json=_page([{"id": "seg_1"}]))
    )
    assert [s.id async for s in aclient.contacts.list_segments("con_1")] == ["seg_1"]
    assert _last(segments).method == "GET"

    overview = respx.get(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(200, json={"provider": "builtin"})
    )
    assert (await aclient.contacts.verification()).provider == "builtin"
    assert _last(overview).method == "GET"

    request = respx.post(f"{BASE_URL}/contacts/verification").mock(
        return_value=httpx.Response(200, json={"affected": 7, "queued": False})
    )
    result = await aclient.contacts.request_verification(
        action="mark_deliverable", campaign_id="camp_1"
    )
    assert result.affected == 7
    assert json.loads(_last(request).content) == {
        "action": "mark_deliverable",
        "campaign_id": "camp_1",
    }


# ===========================================================================
# emails
# ===========================================================================
@respx.mock
def test_mailbox_lifecycle_sync_and_allowance(client: Warmbly) -> None:
    allowance = respx.get(f"{BASE_URL}/emails/allowance").mock(
        return_value=httpx.Response(
            200,
            json={
                "used": 12,
                "allowance": 15,
                "remaining": 3,
                "basis": "fair_use",
                "sends_per_mailbox": 1000,
                "paid": True,
            },
        )
    )
    quota = client.emails.allowance()
    assert (quota.remaining, quota.basis) == (3, "fair_use")
    assert _last(allowance).url.path == "/v1/emails/allowance"

    hold = respx.post(f"{BASE_URL}/emails/em_1/hold").mock(
        return_value=httpx.Response(
            200, json={"state": "reserve", "since": "2026-09-01T00:00:00Z"}
        )
    )
    assert client.emails.hold("em_1").state == "reserve"
    assert _last(hold).method == "POST"

    release = respx.post(f"{BASE_URL}/emails/em_1/release").mock(
        return_value=httpx.Response(200, json={"state": "resting", "reason": "health"})
    )
    released = client.emails.release("em_1")
    assert (released.state, released.reason) == ("resting", "health")
    assert _last(release).url.path == "/v1/emails/em_1/release"

    sync = respx.get(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "state": {
                    "backfill_status": "running",
                    "backfill_synced": 400,
                    "deferred": 12,
                    "throttle_reason": "daily",
                },
                "policy": {"backfill_days": 30, "daily_messages": 500},
            },
        )
    )
    progress = client.emails.sync("em_1")
    assert progress.state is not None
    assert progress.state.throttle_reason == "daily"
    assert progress.policy is not None
    assert progress.policy.daily_messages == 500
    assert _last(sync).url.path == "/v1/emails/em_1/sync"

    unreported = respx.get(f"{BASE_URL}/emails/em_2/sync").mock(
        return_value=httpx.Response(200, json={"state": None, "policy": {}})
    )
    assert client.emails.sync("em_2").state is None
    assert _last(unreported).method == "GET"


@respx.mock
def test_tracking_domain_and_auth_check(client: Warmbly) -> None:
    read = respx.get(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracking_domain": "t.acme.com",
                "tracking_domain_verified": False,
                "status": "wrong_target",
                "observed": "other.host.",
                "cname_target": "track.warmbly.com",
            },
        )
    )
    status = client.emails.tracking_domain("em_1")
    assert status.status == "wrong_target"
    assert status.observed == "other.host."
    assert _last(read).method == "GET"

    verify = respx.post(f"{BASE_URL}/emails/em_1/track/verify").mock(
        return_value=httpx.Response(
            200, json={"tracking_domain_verified": True, "status": "verified"}
        )
    )
    assert client.emails.verify_tracking_domain("em_1").tracking_domain_verified is True
    assert _last(verify).url.path == "/v1/emails/em_1/track/verify"

    refresh = respx.post(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json={"auth_state": "pass", "spf": True})
    )
    assert client.emails.refresh_auth_check("em_1").auth_state == "pass"
    assert _last(refresh).method == "POST"

    update = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1", "save_to_sent": True})
    )
    assert client.emails.update("em_1", save_to_sent=True).save_to_sent is True
    assert json.loads(_last(update).content) == {"save_to_sent": True}


@respx.mock
def test_sending_behavior(client: Warmbly) -> None:
    read = respx.get(f"{BASE_URL}/emails/em_1/behavior").mock(
        return_value=httpx.Response(
            200,
            json={
                "email_account_id": "em_1",
                "enabled": False,
                "daily_limit_min": 30,
                "daily_limit_max": 45,
                "weekdays": 31,
                "timezone": "Europe/Budapest",
            },
        )
    )
    profile = client.emails.behavior("em_1")
    assert profile.weekdays == 31
    assert profile.timezone == "Europe/Budapest"
    assert _last(read).url.path == "/v1/emails/em_1/behavior"

    write = respx.put(f"{BASE_URL}/emails/em_1/behavior").mock(
        return_value=httpx.Response(
            200, json={"email_account_id": "em_1", "enabled": True}
        )
    )
    updated = client.emails.update_behavior(
        "em_1",
        enabled=True,
        daily_limit_min=20,
        daily_limit_max=35,
        hourly_limit_min=3,
        hourly_limit_max=7,
        gap_min_seconds=120,
        gap_max_seconds=600,
        work_start_min=540,
        work_start_max=570,
        work_end_min=1020,
        work_end_max=1080,
        lunch_enabled=True,
        lunch_earliest=720,
        lunch_latest=810,
        lunch_min_minutes=30,
        lunch_max_minutes=60,
        weekdays=31,
    )
    assert updated.enabled is True
    assert json.loads(_last(write).content) == {
        "enabled": True,
        "daily_limit_min": 20,
        "daily_limit_max": 35,
        "hourly_limit_min": 3,
        "hourly_limit_max": 7,
        "gap_min_seconds": 120,
        "gap_max_seconds": 600,
        "work_start_min": 540,
        "work_start_max": 570,
        "work_end_min": 1020,
        "work_end_max": 1080,
        "lunch_enabled": True,
        "lunch_earliest": 720,
        "lunch_latest": 810,
        "lunch_min_minutes": 30,
        "lunch_max_minutes": 60,
        "weekdays": 31,
    }

    plan = respx.get(f"{BASE_URL}/emails/em_1/behavior/plan").mock(
        return_value=httpx.Response(
            200,
            json={
                "plan_date": "2026-09-07",
                "is_working_day": True,
                "daily_limit": 38,
                "sent_today": 12,
                "remaining_today": 26,
                "lunch_start_minute": None,
                "lunch_end_minute": None,
                "behavior": {"enabled": True},
            },
        )
    )
    today = client.emails.behavior_plan("em_1")
    assert today.remaining_today == 26
    assert today.lunch_start_minute is None
    assert today.behavior is not None
    assert today.behavior.enabled is True
    assert _last(plan).url.path == "/v1/emails/em_1/behavior/plan"


@respx.mock
@pytest.mark.anyio
async def test_emails_async(aclient: AsyncWarmbly) -> None:
    allowance = respx.get(f"{BASE_URL}/emails/allowance").mock(
        return_value=httpx.Response(
            200, json={"used": 1, "allowance": None, "basis": "unlimited"}
        )
    )
    quota = await aclient.emails.allowance()
    assert quota.allowance is None
    assert _last(allowance).method == "GET"

    hold = respx.post(f"{BASE_URL}/emails/em_1/hold").mock(
        return_value=httpx.Response(200, json={"state": "reserve"})
    )
    assert (await aclient.emails.hold("em_1")).state == "reserve"
    assert _last(hold).method == "POST"

    release = respx.post(f"{BASE_URL}/emails/em_1/release").mock(
        return_value=httpx.Response(200, json={"state": "active"})
    )
    assert (await aclient.emails.release("em_1")).state == "active"
    assert _last(release).method == "POST"

    sync = respx.get(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json={"state": None, "policy": {}})
    )
    assert (await aclient.emails.sync("em_1")).state is None
    assert _last(sync).method == "GET"

    read = respx.get(f"{BASE_URL}/emails/em_1/track").mock(
        return_value=httpx.Response(200, json={"status": "unset"})
    )
    assert (await aclient.emails.tracking_domain("em_1")).status == "unset"
    assert _last(read).method == "GET"

    verify = respx.post(f"{BASE_URL}/emails/em_1/track/verify").mock(
        return_value=httpx.Response(200, json={"status": "not_found"})
    )
    assert (await aclient.emails.verify_tracking_domain("em_1")).status == "not_found"
    assert _last(verify).method == "POST"

    refresh = respx.post(f"{BASE_URL}/emails/em_1/auth-check").mock(
        return_value=httpx.Response(200, json={"auth_state": "fail"})
    )
    assert (await aclient.emails.refresh_auth_check("em_1")).auth_state == "fail"
    assert _last(refresh).method == "POST"

    behavior = respx.get(f"{BASE_URL}/emails/em_1/behavior").mock(
        return_value=httpx.Response(200, json={"enabled": True})
    )
    assert (await aclient.emails.behavior("em_1")).enabled is True
    assert _last(behavior).method == "GET"

    write = respx.put(f"{BASE_URL}/emails/em_1/behavior").mock(
        return_value=httpx.Response(200, json={"enabled": False})
    )
    assert (
        await aclient.emails.update_behavior("em_1", enabled=False)
    ).enabled is False
    assert json.loads(_last(write).content) == {"enabled": False}

    plan = respx.get(f"{BASE_URL}/emails/em_1/behavior/plan").mock(
        return_value=httpx.Response(200, json={"is_working_day": False})
    )
    assert (await aclient.emails.behavior_plan("em_1")).is_working_day is False
    assert _last(plan).method == "GET"


# ===========================================================================
# api_keys + unibox
# ===========================================================================
@respx.mock
def test_revoke_self(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/api-keys/self").mock(
        return_value=httpx.Response(200, json={"status": "revoked"})
    )
    assert client.api_keys.revoke_self(reason="laptop returned").status == "revoked"
    request = _last(route)
    assert request.url.path == "/v1/api-keys/self"
    assert request.url.params.get("reason") == "laptop returned"


@respx.mock
def test_unibox_folder_scope(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(
            200, json=_page([{"id": "msg_1", "folder": "spam"}])
        )
    )
    messages = list(client.unibox.list(folder="spam"))
    assert messages[0].folder == "spam"
    assert _last(listing).url.params.get("folder") == "spam"

    overview = respx.get(f"{BASE_URL}/unibox/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 10,
                "folders": [{"folder": "inbox", "unread": 3, "total": 10}],
            },
        )
    )
    rollup = client.unibox.overview()
    assert rollup.folders[0]["unread"] == 3
    assert _last(overview).method == "GET"

    by_ids = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"email_ids": ["m1"], "seen": True})
    )
    client.unibox.mark_seen(email_ids=["m1"])
    assert json.loads(_last(by_ids).content) == {"email_ids": ["m1"], "seen": True}

    by_folder = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"seen": True})
    )
    client.unibox.mark_seen(folder="archive")
    assert json.loads(_last(by_folder).content) == {"folder": "archive", "seen": True}


@respx.mock
@pytest.mark.anyio
async def test_api_keys_and_unibox_async(aclient: AsyncWarmbly) -> None:
    revoke = respx.delete(f"{BASE_URL}/api-keys/self").mock(
        return_value=httpx.Response(200, json={"status": "revoked"})
    )
    assert (await aclient.api_keys.revoke_self()).status == "revoked"
    assert "reason" not in _last(revoke).url.params

    listing = respx.get(f"{BASE_URL}/unibox").mock(
        return_value=httpx.Response(200, json=_page([{"id": "msg_1"}]))
    )
    assert [m.id async for m in aclient.unibox.list(folder="trash")] == ["msg_1"]
    assert _last(listing).url.params.get("folder") == "trash"

    seen = respx.patch(f"{BASE_URL}/unibox/seen").mock(
        return_value=httpx.Response(200, json={"seen": False})
    )
    await aclient.unibox.mark_seen(folder="inbox", seen=False)
    assert json.loads(_last(seen).content) == {"folder": "inbox", "seen": False}


# ===========================================================================
# response shapes that used to be modelled wrong
# ===========================================================================
@respx.mock
def test_unibox_message_shape(client: Warmbly) -> None:
    """`retrieve` returns header-named addresses and a body; `thread` returns rows."""
    message = respx.get(f"{BASE_URL}/unibox/msg_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_1",
                "thread_id": "th_1",
                "from": ["ada@example.com"],
                "to": ["sales@acme.com"],
                "cc": [],
                "ReplyTo": ["ada+reply@example.com"],
                "in_reply_to": ["<prev@example.com>"],
                "subject": "Re: Demo",
                "date": "2026-09-05T09:00:00Z",
                "body_plain": "Sounds good.",
                "body_html": "<p>Sounds good.</p>",
                "body_truncated": False,
            },
        )
    )
    full = client.unibox.retrieve("msg_1")
    assert list(full.from_) == ["ada@example.com"]
    assert list(full.reply_to) == ["ada+reply@example.com"]
    assert full.body_plain == "Sounds good."
    assert full.body_truncated is False
    assert _last(message).url.path == "/v1/unibox/msg_1"

    thread = respx.get(f"{BASE_URL}/unibox/thread").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "msg_1",
                        "from_addr": ["ada@example.com"],
                        "to_addr": ["sales@acme.com"],
                        "snippet": "Sounds good.",
                        "seen": True,
                    }
                ]
            ),
        )
    )
    rows = list(client.unibox.thread(thread_id="th_1"))
    assert list(rows[0].from_addr) == ["ada@example.com"]
    assert rows[0].snippet == "Sounds good."
    assert _last(thread).url.params.get("thread_id") == "th_1"


@respx.mock
def test_corrected_model_shapes(client: Warmbly) -> None:
    logs = respx.get(f"{BASE_URL}/campaigns/camp_1/logs").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "log_1",
                        "event_type": "guardrail_tripped",
                        "message": "Paused: bounce rate above 3%.",
                        "metadata": {"bounce_rate": 0.042},
                    }
                ]
            ),
        )
    )
    entries = list(client.campaigns.logs("camp_1"))
    assert entries[0].event_type == "guardrail_tripped"
    assert entries[0].metadata == {"bounce_rate": 0.042}
    assert _last(logs).method == "GET"

    ban = respx.get(f"{BASE_URL}/emails/em_1/warmup/ban-status").mock(
        return_value=httpx.Response(
            200,
            json={
                "email_account_id": "em_1",
                "blocked": True,
                "health_state": "at_risk",
                "blocked_until": "2026-09-10T00:00:00Z",
                "can_appeal": True,
                "pending_appeal": False,
            },
        )
    )
    status = client.emails.warmup_ban_status("em_1")
    assert status.health_state == "at_risk"
    assert status.blocked_until == "2026-09-10T00:00:00Z"
    assert status.pending_appeal is False
    assert _last(ban).method == "GET"

    plans = respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(
            200,
            json={
                "plans": [
                    {
                        "id": "plan_1",
                        "name": "Business",
                        "price": 199.0,
                        "duration": "monthly",
                        "daily_emails": 15000,
                        "max_email_accounts": None,
                        "monthly_credits": 5000,
                    }
                ]
            },
        )
    )
    plan = next(iter(client.plans.list()))
    assert (plan.duration, plan.daily_emails) == ("monthly", 15000)
    assert plan.max_email_accounts is None
    assert _last(plans).method == "GET"

    preview = respx.post(f"{BASE_URL}/contacts/import/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "filename": "leads.csv",
                "format": "csv",
                "columns": ["Email", "First"],
                "has_header": True,
                "sample_rows": [["ada@example.com", "Ada"]],
                "total_rows": 1,
                "suggested_mapping": [{"column": "Email", "field": "email"}],
            },
        )
    )
    parsed = client.contacts.import_preview(file=b"Email,First\n", filename="leads.csv")
    assert list(parsed.columns) == ["Email", "First"]
    assert parsed.sample_rows[0][0] == "ada@example.com"
    assert parsed.has_header is True
    assert _last(preview).method == "POST"

    teams = respx.get(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "team_1",
                        "name": "Sales",
                        "members": [
                            {
                                "user_id": "usr_1",
                                "email": "ada@acme.com",
                                "added_at": "2026-08-01T00:00:00Z",
                            }
                        ],
                    }
                ]
            ),
        )
    )
    team = next(iter(client.teams.list()))
    assert team.members[0].added_at == "2026-08-01T00:00:00Z"
    assert _last(teams).method == "GET"
