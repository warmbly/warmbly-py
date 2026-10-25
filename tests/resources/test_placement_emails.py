"""Placement, analytics and the mailbox routes added to ``emails``."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, page, v  # noqa: F401

# -- emails -----------------------------------------------------------------

MAILBOX = {
    "id": "em_1",
    "email": "ann@example.com",
    "send_as_email": "sales@example.com",
    "mail_host": "google_workspace",
    "auth_method": "delegated",
    "domain_grant_id": "gr_1",
    "vendor_connection_id": "vc_1",
    "vendor": "acme",
    "avatar_url": "https://img.example/a.png",
    "last_id": 41,
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 20,
    "rolling_recipient_limit": 90,
    "track_direct_mail": True,
    "warmup_placement": "folder",
    "warmup_folder": "Warmbly",
    "warmup_retention_days": 14,
    "relay_folder_moves": True,
}


def _check_mailbox(m: Any) -> None:
    assert (m.send_as_email, m.mail_host, m.auth_method) == (
        "sales@example.com",
        "google_workspace",
        "delegated",
    )
    assert (m.domain_grant_id, m.vendor_connection_id, m.vendor) == (
        "gr_1",
        "vc_1",
        "acme",
    )
    assert (m.avatar_url, m.last_id) == ("https://img.example/a.png", 41)
    assert (m.test_mode, m.test_send_enabled, m.test_receive_enabled) == (
        "diagnostic",
        True,
        False,
    )
    assert (m.shared_daily_limit, m.rolling_recipient_limit) == (20, 90)
    assert m.track_direct_mail is True
    assert (m.warmup_placement, m.warmup_folder, m.warmup_retention_days) == (
        "folder",
        "Warmbly",
        14,
    )
    assert m.relay_folder_moves is True


@pytest.mark.anyio
@respx.mock
async def test_email_update_new_fields(dual: Any) -> None:
    route = respx.patch(f"{BASE_URL}/emails/em_1").mock(
        return_value=httpx.Response(200, json=MAILBOX)
    )
    got = await v(
        dual.emails.update(
            "em_1",
            send_as_email="sales@example.com",
            test_mode="diagnostic",
            test_send_enabled=True,
            test_receive_enabled=False,
            shared_daily_limit=20,
            rolling_recipient_limit=90,
            send_recovery_resolution={"held_task_id": "t_1", "held_reason": "auth"},
            warmup_placement="folder",
            warmup_folder="Warmbly",
            warmup_retention_days=14,
            relay_folder_moves=True,
        )
    )
    _check_mailbox(got)
    assert json.loads(last(route).content) == {
        "send_as_email": "sales@example.com",
        "test_mode": "diagnostic",
        "test_send_enabled": True,
        "test_receive_enabled": False,
        "shared_daily_limit": 20,
        "rolling_recipient_limit": 90,
        "send_recovery_resolution": {"held_task_id": "t_1", "held_reason": "auth"},
        "warmup_placement": "folder",
        "warmup_folder": "Warmbly",
        "warmup_retention_days": 14,
        "relay_folder_moves": True,
    }


@pytest.mark.anyio
@respx.mock
async def test_email_direct_tracking_and_sync(dual: Any) -> None:
    patch = respx.patch(f"{BASE_URL}/emails/em_1/direct-tracking").mock(
        return_value=httpx.Response(200, json={"track_direct_mail": True})
    )
    got = await v(dual.emails.direct_tracking("em_1", enabled=True))
    assert got.track_direct_mail is True
    assert last(patch).method == "PATCH"
    assert json.loads(last(patch).content) == {"enabled": True}

    put = respx.put(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(200, json={"skip_folders": ["Junk", "Archive"]})
    )
    saved = await v(dual.emails.update_sync("em_1", skip_folders=["Junk", "Archive"]))
    assert list(saved.skip_folders) == ["Junk", "Archive"]
    assert last(put).method == "PUT"
    assert json.loads(last(put).content) == {"skip_folders": ["Junk", "Archive"]}

    get = respx.get(f"{BASE_URL}/emails/em_1/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "state": {
                    "backfill_status": "running",
                    "folders_skipped_cap": 2,
                    "folders_skipped_conflict": 1,
                },
                "policy": {"backfill_days": 30, "skip_folders": ["Junk"]},
                "skip_folders": ["Junk"],
                "folders": [{"name": "INBOX", "folder": "inbox"}],
            },
        )
    )
    sync = await v(dual.emails.sync("em_1"))
    assert last(get).method == "GET"
    assert (sync.state.folders_skipped_cap, sync.state.folders_skipped_conflict) == (
        2,
        1,
    )
    assert list(sync.policy.skip_folders) == ["Junk"]
    assert list(sync.skip_folders) == ["Junk"]
    assert (sync.folders[0].name, sync.folders[0].folder) == ("INBOX", "inbox")


@pytest.mark.anyio
@respx.mock
async def test_email_certificates_and_identity(dual: Any) -> None:
    certs = respx.get(f"{BASE_URL}/emails/em_1/certificates").mock(
        return_value=httpx.Response(
            200,
            json={
                "smtp": {
                    "host": "smtp.example.com",
                    "port": 587,
                    "tls_unverified": True,
                    "tls_pin": "ab" * 32,
                    "observed": {
                        "fingerprint": "cd" * 32,
                        "subject": "CN=smtp",
                        "issuer": "CN=ca",
                        "not_after": "2027-01-01T00:00:00Z",
                        "self_signed": True,
                        "trusted": False,
                    },
                },
                "imap": {
                    "host": "imap.example.com",
                    "port": 993,
                    "tls_unverified": False,
                },
            },
        )
    )
    got = await v(dual.emails.certificates("em_1"))
    assert last(certs).method == "GET"
    assert (got.smtp.host, got.smtp.port, got.smtp.tls_unverified) == (
        "smtp.example.com",
        587,
        True,
    )
    assert got.smtp.tls_pin == "ab" * 32
    obs = got.smtp.observed
    assert (obs.fingerprint, obs.subject, obs.issuer) == (
        "cd" * 32,
        "CN=smtp",
        "CN=ca",
    )
    assert (obs.not_after, obs.self_signed, obs.trusted) == (
        "2027-01-01T00:00:00Z",
        True,
        False,
    )
    assert (got.imap.host, got.imap.observed) == ("imap.example.com", None)

    identity_json = {
        "supported": True,
        "provider": "gmail",
        "mailbox_email": "ann@example.com",
        "send_as_email": "sales@example.com",
        "identities": [
            {
                "email": "sales@example.com",
                "name": "Sales",
                "is_primary": False,
                "is_default": True,
                "verified": True,
            }
        ],
        "synced_at": "2026-10-01T00:00:00Z",
        "signature_source": "provider",
        "signature_imported_at": "2026-10-02T00:00:00Z",
    }
    ident = respx.get(f"{BASE_URL}/emails/em_1/identity").mock(
        return_value=httpx.Response(200, json=identity_json)
    )
    read = await v(dual.emails.identity("em_1"))
    assert last(ident).method == "GET"
    assert (read.supported, read.provider, read.mailbox_email) == (
        True,
        "gmail",
        "ann@example.com",
    )
    assert read.send_as_email == "sales@example.com"
    first = read.identities[0]
    assert (first.email, first.name, first.is_primary) == (
        "sales@example.com",
        "Sales",
        False,
    )
    assert (first.is_default, first.verified) == (True, True)
    assert (read.synced_at, read.signature_source) == (
        "2026-10-01T00:00:00Z",
        "provider",
    )
    assert read.signature_imported_at == "2026-10-02T00:00:00Z"

    refresh = respx.post(f"{BASE_URL}/emails/em_1/identity/refresh").mock(
        return_value=httpx.Response(200, json=identity_json)
    )
    again = await v(dual.emails.refresh_identity("em_1", import_signature=True))
    assert again.supported is True
    assert last(refresh).method == "POST"
    assert json.loads(last(refresh).content) == {"import_signature": True}
    assert last(refresh).headers["idempotency-key"]
    await v(dual.emails.refresh_identity("em_1"))
    assert json.loads(last(refresh).content) == {}


# -- analytics --------------------------------------------------------------


@pytest.mark.anyio
@respx.mock
async def test_analytics_param_names(dual: Any) -> None:
    a = dual.analytics
    dash = respx.get(f"{BASE_URL}/analytics/dashboard").mock(
        return_value=httpx.Response(200, json={"totals": {"sent": 1}})
    )
    await v(a.dashboard(period="90d", campaign_ids=["c1", "c2"], folder_ids=["f1"]))
    params = last(dash).url.params
    assert params["period"] == "90d"
    assert params["campaign_ids"] == "c1,c2"
    assert params["folder_ids"] == "f1"

    warm = respx.get(f"{BASE_URL}/analytics/warmup").mock(
        return_value=httpx.Response(200, json={"summary": {}})
    )
    await v(a.warmup(from_="2026-10-01", to="2026-10-07", email_id="em_1"))
    params = last(warm).url.params
    assert (params["from"], params["to"], params["email_id"]) == (
        "2026-10-01",
        "2026-10-07",
        "em_1",
    )

    cmp_ = respx.get(f"{BASE_URL}/analytics/campaigns/compare").mock(
        return_value=httpx.Response(200, json={"campaigns": []})
    )
    await v(a.compare_campaigns(ids=["c1", "c2"], from_="2026-10-01", to="2026-10-07"))
    assert last(cmp_).url.params["ids"] == "c1,c2"

    camp = respx.get(f"{BASE_URL}/analytics/campaigns/c1").mock(
        return_value=httpx.Response(200, json={})
    )
    await v(a.campaign("c1", from_="2026-10-01", to="2026-10-07"))
    assert last(camp).url.params["from"] == "2026-10-01"

    daily = respx.get(f"{BASE_URL}/analytics/campaigns/c1/daily").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await v(a.campaign_daily("c1", from_="2026-10-01", to="2026-10-07"))
    assert last(daily).url.params["to"] == "2026-10-07"

    hourly = respx.get(f"{BASE_URL}/analytics/campaigns/c1/hourly").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await v(a.campaign_hourly("c1", date="2026-10-02"))
    assert last(hourly).url.params["date"] == "2026-10-02"

    accounts = respx.get(f"{BASE_URL}/analytics/accounts").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "em_1"}], "pagination": {"has_more": False}},
        )
    )
    res = await v(a.accounts(email_ids=["em_1", "em_2"], limit=50, cursor="cur"))
    params = last(accounts).url.params
    assert (params["email_ids"], params["limit"], params["cursor"]) == (
        "em_1,em_2",
        "50",
        "cur",
    )
    assert res.data[0]["id"] == "em_1"

    acct = respx.get(f"{BASE_URL}/analytics/accounts/em_1").mock(
        return_value=httpx.Response(200, json={"id": "em_1"})
    )
    await v(a.account("em_1"))
    assert last(acct).url.query == b""

    usage = respx.get(f"{BASE_URL}/analytics/usage").mock(
        return_value=httpx.Response(200, json={})
    )
    await v(a.usage(period="month"))
    assert last(usage).url.params["period"] == "month"

    deliv = respx.get(f"{BASE_URL}/analytics/deliverability").mock(
        return_value=httpx.Response(200, json={})
    )
    await v(a.deliverability(from_="2026-10-01T00:00:00Z"))
    assert last(deliv).url.params["from"] == "2026-10-01T00:00:00Z"


@pytest.mark.anyio
@respx.mock
async def test_analytics_direct(dual: Any) -> None:
    route = respx.get(f"{BASE_URL}/analytics/direct").mock(
        return_value=httpx.Response(
            200,
            json={
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
                    "tracked_sent": 10,
                    "opened": 6,
                    "machine_opened": 1,
                    "clicked": 2,
                    "open_rate": 60.0,
                    "click_rate": 20.0,
                },
                "daily_trend": [
                    {"date": "2026-10-01T00:00:00Z", "sent": 3, "received": 1}
                ],
                "mailboxes": [
                    {
                        "email_account_id": "em_1",
                        "email": "ann@example.com",
                        "track_direct_mail": True,
                        "sent": 20,
                        "received": 9,
                    }
                ],
                "top_contacts": [
                    {
                        "email": "bob@example.org",
                        "sent": 4,
                        "received": 3,
                        "last_at": "2026-10-03T00:00:00Z",
                    }
                ],
            },
        )
    )
    got = await v(dual.analytics.direct(period="30d"))
    assert last(route).url.params["period"] == "30d"
    assert got.period == "30d"
    vol = got.volume
    assert (vol.sent, vol.received, vol.threads_started, vol.replied) == (
        40,
        25,
        30,
        12,
    )
    assert (vol.reply_rate, vol.bounced, vol.median_reply_minutes) == (40.0, 2, 95)
    trk = got.tracking
    assert (trk.mailboxes_opted_in, trk.mailboxes_total, trk.tracked_sent) == (1, 3, 10)
    assert (trk.opened, trk.machine_opened, trk.clicked) == (6, 1, 2)
    assert (trk.open_rate, trk.click_rate) == (60.0, 20.0)
    day = got.daily_trend[0]
    assert (day.date, day.sent, day.received) == ("2026-10-01T00:00:00Z", 3, 1)
    box = got.mailboxes[0]
    assert (box.email_account_id, box.email, box.track_direct_mail) == (
        "em_1",
        "ann@example.com",
        True,
    )
    assert (box.sent, box.received) == (20, 9)
    top = got.top_contacts[0]
    assert (top.email, top.sent, top.received, top.last_at) == (
        "bob@example.org",
        4,
        3,
        "2026-10-03T00:00:00Z",
    )


@pytest.mark.anyio
@respx.mock
async def test_analytics_inbox_tagging(dual: Any) -> None:
    row = {
        "id": "tag_1",
        "message_id": "m_1",
        "thread_id": "th_1",
        "kind": "human",
        "kind_confidence": 0.91,
        "kind_source": "model",
        "intent": "call_request",
        "intent_confidence": 0.8,
        "relevance": 70,
        "priority": "high",
        "needs_review": True,
        "review_reason": "low confidence",
        "labels": ["hot"],
        "answers": {"q1": "yes"},
        "model": "m",
        "input_tokens": 120,
        "actions": ["task"],
        "return_date": "2026-11-02",
        "created_at": "2026-10-05T00:00:00Z",
    }
    route = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "enabled": True,
                    "data": [row],
                    "total": 2,
                    "summary": {
                        "total": 2,
                        "needs_review": 1,
                        "from_offline": 0,
                        "acted": 1,
                    },
                    "pagination": {"next_cursor": "c2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "enabled": True,
                    "data": [{**row, "id": "tag_2"}],
                    "total": 2,
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    rows = await items(
        dual.analytics.inbox_tagging(needs_review=True, limit=1, cursor="c1")
    )
    assert [r.id for r in rows] == ["tag_1", "tag_2"]
    first = route.calls[0].request.url.params
    assert (first["needs_review"], first["limit"], first["cursor"]) == (
        "true",
        "1",
        "c1",
    )
    assert route.calls[1].request.url.params["cursor"] == "c2"
    r = rows[0]
    assert (r.message_id, r.thread_id, r.kind, r.kind_confidence) == (
        "m_1",
        "th_1",
        "human",
        0.91,
    )
    assert (r.kind_source, r.intent, r.intent_confidence) == (
        "model",
        "call_request",
        0.8,
    )
    assert (r.relevance, r.priority, r.needs_review, r.review_reason) == (
        70,
        "high",
        True,
        "low confidence",
    )
    assert (r.labels, r.answers, r.model, r.input_tokens) == (
        ["hot"],
        {"q1": "yes"},
        "m",
        120,
    )
    assert (r.actions, r.return_date, r.created_at) == (
        ["task"],
        "2026-11-02",
        "2026-10-05T00:00:00Z",
    )

    overview = respx.get(f"{BASE_URL}/analytics/inbox-tagging").mock(
        return_value=httpx.Response(
            200,
            json={
                "enabled": True,
                "data": [],
                "total": 9,
                "summary": {
                    "total": 9,
                    "needs_review": 3,
                    "from_offline": 2,
                    "acted": 4,
                },
            },
        )
    )
    head = await v(dual.analytics.inbox_tagging_overview(needs_review=False))
    params = last(overview).url.params
    assert (params["limit"], params["needs_review"]) == ("1", "false")
    assert (head.enabled, head.total) == (True, 9)
    s = head.summary
    assert (s.total, s.needs_review, s.from_offline, s.acted) == (9, 3, 2, 4)


METRIC = {
    "version": "observed-v2",
    "population": "warmup_pool_major_providers",
    "denominator_kind": "classified_observed_receipts",
    "unit": "percent",
    "source": "mailbox_observation",
    "classification_policy": "first_folder_v2",
    "numerator": 18,
    "denominator": 20,
    "unresolved": 1,
    "window_days": 7,
    "window_basis": "trailing_utc_days",
    "missingness_basis": "unclassified",
    "value": 90.0,
    "wilson_95_independence_interval": {"lower": 69.9, "upper": 97.2},
}

COUNTS = {
    "sent": 30,
    "delivered": 20,
    "inbox": 15,
    "tabs": 3,
    "spam": 2,
    "unknown": 1,
    "archived": 0,
    "custom": 0,
    "instrumented_receipts": 20,
    "observed_receipts": 21,
    "legacy_uninstrumented_receipts": 1,
    "rescue_requested": 2,
    "non_spam_metric": METRIC,
    "rescued": 2,
    "rescue_confirmed": 1,
    "rescue_missing": 0,
    "rescue_failed": 0,
    "rescue_unreported": 1,
    "unconfirmed": 4,
    "inbox_rate": 90.0,
    "spam_rate": 10.0,
}

RATE = {
    "window_days": 7,
    "min_sample": 20,
    "scope": "major",
    "delivered": 20,
    "inbox": 15,
    "tabs": 3,
    "spam": 2,
    "inbox_rate": 90.0,
    "band": "good",
    "metric": METRIC,
    "other_delivered": 5,
    "other_inbox_rate": 80.0,
}


def _check_counts(c: Any) -> None:
    assert (c.sent, c.delivered, c.inbox, c.tabs, c.spam) == (30, 20, 15, 3, 2)
    assert (c.unknown, c.archived, c.custom) == (1, 0, 0)
    assert (c.instrumented_receipts, c.observed_receipts) == (20, 21)
    assert (c.legacy_uninstrumented_receipts, c.rescue_requested) == (1, 2)
    assert (c.rescued, c.rescue_confirmed, c.rescue_missing) == (2, 1, 0)
    assert (c.rescue_failed, c.rescue_unreported, c.unconfirmed) == (0, 1, 4)
    assert (c.inbox_rate, c.spam_rate) == (90.0, 10.0)
    m = c.non_spam_metric
    assert (m.version, m.population, m.denominator_kind, m.unit) == (
        "observed-v2",
        "warmup_pool_major_providers",
        "classified_observed_receipts",
        "percent",
    )
    assert (m.source, m.classification_policy) == (
        "mailbox_observation",
        "first_folder_v2",
    )
    assert (m.numerator, m.denominator, m.unresolved, m.window_days) == (18, 20, 1, 7)
    assert (m.window_basis, m.missingness_basis, m.value) == (
        "trailing_utc_days",
        "unclassified",
        90.0,
    )
    assert m.wilson_95_independence_interval.lower == 69.9
    assert m.wilson_95_independence_interval.upper == 97.2


def _check_rate(r: Any) -> None:
    assert (r.window_days, r.min_sample, r.scope) == (7, 20, "major")
    assert (r.delivered, r.inbox, r.tabs, r.spam) == (20, 15, 3, 2)
    assert (r.inbox_rate, r.band, r.other_delivered, r.other_inbox_rate) == (
        90.0,
        "good",
        5,
        80.0,
    )
    assert r.metric.numerator == 18


@pytest.mark.anyio
@respx.mock
async def test_analytics_warmup_placement(dual: Any) -> None:
    group = {
        "group": "google",
        "inbox": 9,
        "tabs": 1,
        "spam": 1,
        "rescued": 1,
        "unknown": 0,
        "archived": 0,
        "custom": 0,
        "rescue_confirmed": 1,
        "rescue_missing": 0,
        "rescue_failed": 0,
    }
    route = respx.get(f"{BASE_URL}/analytics/warmup/placement").mock(
        return_value=httpx.Response(
            200,
            json={
                "email_account_id": "em_1",
                "date_range": {
                    "from": "2026-10-01T00:00:00Z",
                    "to": "2026-10-07T00:00:00Z",
                },
                "summary": COUNTS,
                "rate": RATE,
                "daily": [
                    {
                        **COUNTS,
                        "date": "2026-10-01",
                        "rolling_inbox_rate": 88.5,
                        "groups": [group],
                    }
                ],
                "providers": [
                    {
                        **COUNTS,
                        "group": "google",
                        "hosts": [{**COUNTS, "host": "gmail"}],
                    }
                ],
                "mailboxes": [
                    {
                        **COUNTS,
                        "email_account_id": "em_1",
                        "email": "ann@example.com",
                        "rate": RATE,
                        "daily_inbox_rate": [90.0, None],
                    }
                ],
            },
        )
    )
    got = await v(
        dual.analytics.warmup_placement(
            from_="2026-10-01", to="2026-10-07", email_id="em_1"
        )
    )
    params = last(route).url.params
    assert (params["from"], params["to"], params["email_id"]) == (
        "2026-10-01",
        "2026-10-07",
        "em_1",
    )
    assert got.email_account_id == "em_1"
    assert got.date_range["from"] == "2026-10-01T00:00:00Z"
    _check_counts(got.summary)
    _check_rate(got.rate)
    day = got.daily[0]
    _check_counts(day)
    assert (day.date, day.rolling_inbox_rate) == ("2026-10-01", 88.5)
    g = day.groups[0]
    assert (g.group, g.inbox, g.tabs, g.spam, g.rescued) == ("google", 9, 1, 1, 1)
    assert (g.unknown, g.archived, g.custom) == (0, 0, 0)
    assert (g.rescue_confirmed, g.rescue_missing, g.rescue_failed) == (1, 0, 0)
    prov = got.providers[0]
    _check_counts(prov)
    assert (prov.group, prov.hosts[0].host) == ("google", "gmail")
    _check_counts(prov.hosts[0])
    box = got.mailboxes[0]
    _check_counts(box)
    _check_rate(box.rate)
    assert (box.email_account_id, box.email) == ("em_1", "ann@example.com")
    assert list(box.daily_inbox_rate) == [90.0, None]


# -- placement --------------------------------------------------------------

PLACEMENT_COUNTS = {
    "total": 10,
    "pending": 1,
    "inbox": 5,
    "promotions": 1,
    "other": 1,
    "spam": 1,
    "missing": 1,
    "failed": 0,
    "cancelled": 0,
    "unknown": 0,
    "archive": 0,
    "custom": 0,
    "observed_receipts": 8,
    "classified_receipts": 8,
    "unresolved": 2,
    "primary_metric": METRIC,
    "non_spam_metric": METRIC,
    "delivered": 9,
    "inbox_rate": 0.55,
    "tabs_rate": 0.22,
    "spam_rate": 0.11,
    "missing_rate": 0.11,
}


def _check_pcounts(c: Any) -> None:
    assert (c.total, c.pending, c.inbox, c.promotions, c.other) == (10, 1, 5, 1, 1)
    assert (c.spam, c.missing, c.failed, c.cancelled) == (1, 1, 0, 0)
    assert (c.unknown, c.archive, c.custom) == (0, 0, 0)
    assert (c.observed_receipts, c.classified_receipts, c.unresolved) == (8, 8, 2)
    assert (c.primary_metric.numerator, c.non_spam_metric.denominator) == (18, 20)
    assert c.delivered == 9
    assert (c.inbox_rate, c.tabs_rate, c.spam_rate, c.missing_rate) == (
        0.55,
        0.22,
        0.11,
        0.11,
    )


FAMILIES = [
    {"family": "gmail", "label": "Gmail", "counts": PLACEMENT_COUNTS},
]

TEST = {
    "id": "pt_1",
    "sender_account_id": "em_1",
    "sender_email": "ann@example.com",
    "created_by": "usr_1",
    "campaign_id": "cmp_1",
    "sequence_id": "seq_1",
    "contact_id": "ct_1",
    "monitor_id": "mon_1",
    "batch_id": "pb_1",
    "subject": "Hello",
    "body_html": "<p>x</p>",
    "body_plain": "x",
    "open_tracking": True,
    "link_tracking": False,
    "compare_group_id": "cg_1",
    "origin": "manual",
    "panel": "instance",
    "status": "running",
    "error": "none",
    "pace": "spaced",
    "credits_charged": 3,
    "credits_refunded": 1,
    "credits_settled_at": "2026-10-02T00:00:00Z",
    "created_at": "2026-10-01T00:00:00Z",
    "finished_at": "2026-10-01T01:00:00Z",
    "summary": PLACEMENT_COUNTS,
    "families": FAMILIES,
}


def _check_test(t: Any) -> None:
    assert (t.id, t.sender_account_id, t.sender_email, t.created_by) == (
        "pt_1",
        "em_1",
        "ann@example.com",
        "usr_1",
    )
    assert (t.campaign_id, t.sequence_id, t.contact_id) == ("cmp_1", "seq_1", "ct_1")
    assert (t.monitor_id, t.batch_id, t.subject) == ("mon_1", "pb_1", "Hello")
    assert (t.body_html, t.body_plain) == ("<p>x</p>", "x")
    assert (t.open_tracking, t.link_tracking, t.compare_group_id) == (
        True,
        False,
        "cg_1",
    )
    assert (t.origin, t.panel, t.status, t.error, t.pace) == (
        "manual",
        "instance",
        "running",
        "none",
        "spaced",
    )
    assert (t.credits_charged, t.credits_refunded) == (3, 1)
    assert t.credits_settled_at == "2026-10-02T00:00:00Z"
    assert (t.created_at, t.finished_at) == (
        "2026-10-01T00:00:00Z",
        "2026-10-01T01:00:00Z",
    )
    _check_pcounts(t.summary)
    assert (t.families[0].family, t.families[0].label) == ("gmail", "Gmail")
    _check_pcounts(t.families[0].counts)


USAGE = {
    "used": 2,
    "limit": 10,
    "credits_per_test": 5,
    "credit_balance": 100,
    "period_start": "2026-10-01T00:00:00Z",
    "period_end": "2026-11-01T00:00:00Z",
}


def _check_usage(u: Any) -> None:
    assert (u.used, u.limit, u.credits_per_test, u.credit_balance) == (2, 10, 5, 100)
    assert (u.period_start, u.period_end) == (
        "2026-10-01T00:00:00Z",
        "2026-11-01T00:00:00Z",
    )


@pytest.mark.anyio
@respx.mock
async def test_placement_overview_coverage_seeds(dual: Any) -> None:
    p = dual.placement
    ov = respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "panels": [
                        {
                            "panel": "workspace",
                            "available": False,
                            "reason": "Mark a seed",
                            "seeds": 0,
                            "families": [
                                {"family": "gmail", "label": "Gmail", "seeds": 3}
                            ],
                            "metered": True,
                        }
                    ],
                    "usage": USAGE,
                    "workspace_seeds": 4,
                    "seeds_per_test": 12,
                    "spacing_seconds": 60,
                }
            },
        )
    )
    got = await v(p.overview())
    assert last(ov).method == "GET"
    panel = got.panels[0]
    assert (panel.panel, panel.available, panel.reason, panel.seeds, panel.metered) == (
        "workspace",
        False,
        "Mark a seed",
        0,
        True,
    )
    assert (
        panel.families[0].family,
        panel.families[0].label,
        panel.families[0].seeds,
    ) == (
        "gmail",
        "Gmail",
        3,
    )
    _check_usage(got.usage)
    assert (got.workspace_seeds, got.seeds_per_test, got.spacing_seconds) == (4, 12, 60)

    cov = respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "mailboxes": 20,
                    "tested_7d": 5,
                    "tested_30d": 12,
                    "never_tested": 8,
                }
            },
        )
    )
    c = await v(p.coverage())
    assert last(cov).method == "GET"
    assert (c.mailboxes, c.tested_7d, c.tested_30d, c.never_tested) == (20, 5, 12, 8)

    seeds = respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "email_account_id": "em_1",
                        "email": "ann@example.com",
                        "family": "gmail",
                        "label": "Gmail",
                        "status": "active",
                        "seed": False,
                        "blocker": "warming up",
                    }
                ]
            },
        )
    )
    rows = await items(p.seeds())
    assert last(seeds).method == "GET"
    s = rows[0]
    assert (s.email_account_id, s.email, s.family, s.label) == (
        "em_1",
        "ann@example.com",
        "gmail",
        "Gmail",
    )
    assert (s.status, s.seed, s.blocker) == ("active", False, "warming up")

    put = respx.put(f"{BASE_URL}/placement/seeds/em_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"email_account_id": "em_1", "email": "a@x.com", "seed": True}
            },
        )
    )
    seeded = await v(p.set_seed("em_1", seed=True))
    assert last(put).method == "PUT"
    assert json.loads(last(put).content) == {"seed": True}
    assert (seeded.email_account_id, seeded.seed) == ("em_1", True)


@pytest.mark.anyio
@respx.mock
async def test_placement_tests(dual: Any) -> None:
    p = dual.placement
    listing = respx.get(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(200, json=page([TEST]))
    )
    rows = await items(p.list_tests(campaign_id="cmp_1", limit=5))
    params = last(listing).url.params
    assert (params["campaign_id"], params["limit"]) == ("cmp_1", "5")
    _check_test(rows[0])

    evidence = {
        "version": "received-v1",
        "source": "headers",
        "trust": "unverified_headers",
        "observed_at": "2026-10-01T00:05:00Z",
        "spf": "unknown",
        "dkim": "unknown",
        "dmarc": "unknown",
        "alignment": "unknown",
        "tls": "unknown",
        "from_domain": "example.com",
        "envelope_domain_claim": "bounce.example.com",
        "signing_domain_claim": "example.com",
        "selector_claim": "s1",
        "authentication_results_present": True,
        "one_click_headers_present": True,
        "one_click_signing_claim": False,
        "one_click_compliance": "unknown",
        "dkim_verification": {
            "dkim": "pass",
            "alignment": "pass",
            "signing_domain": "example.com",
            "verifier": "warmbly",
            "observed_at": "2026-10-01T00:05:00Z",
        },
    }
    detail = respx.get(f"{BASE_URL}/placement/tests/pt_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    **TEST,
                    "results": [
                        {
                            "seed": "s***@gmail.com",
                            "family": "gmail",
                            "family_label": "Gmail",
                            "folder": "spam",
                            "scheduled_at": "2026-10-01T00:00:00Z",
                            "sent_at": "2026-10-01T00:01:00Z",
                            "detected_at": "2026-10-01T00:05:00Z",
                            "error": "boom",
                            "first_folder": "inbox",
                            "observed_at": "2026-10-01T00:06:00Z",
                            "late_observation": True,
                            "evidence": evidence,
                        }
                    ],
                    "content": {
                        "score": 80,
                        "issues": [
                            {
                                "severity": "warn",
                                "code": "spammy",
                                "message": "Spam words",
                                "field": "subject",
                                "spans": [
                                    {
                                        "field": "subject",
                                        "text": "FREE",
                                        "line": 1,
                                        "excerpt": "FREE money",
                                    }
                                ],
                                "suggestion": "Drop it",
                            }
                        ],
                    },
                    "compare": {**TEST, "id": "pt_2"},
                }
            },
        )
    )
    d = await v(p.retrieve_test("pt_1"))
    assert last(detail).method == "GET"
    _check_test(d)
    r = d.results[0]
    assert (r.seed, r.family, r.family_label, r.folder) == (
        "s***@gmail.com",
        "gmail",
        "Gmail",
        "spam",
    )
    assert (r.scheduled_at, r.sent_at, r.detected_at) == (
        "2026-10-01T00:00:00Z",
        "2026-10-01T00:01:00Z",
        "2026-10-01T00:05:00Z",
    )
    assert (r.error, r.first_folder, r.observed_at, r.late_observation) == (
        "boom",
        "inbox",
        "2026-10-01T00:06:00Z",
        True,
    )
    e = r.evidence
    assert (e.version, e.source, e.trust, e.observed_at) == (
        "received-v1",
        "headers",
        "unverified_headers",
        "2026-10-01T00:05:00Z",
    )
    assert (e.spf, e.dkim, e.dmarc, e.alignment, e.tls) == ("unknown",) * 5
    assert (e.from_domain, e.envelope_domain_claim) == (
        "example.com",
        "bounce.example.com",
    )
    assert (e.signing_domain_claim, e.selector_claim) == ("example.com", "s1")
    assert (
        e.authentication_results_present,
        e.one_click_headers_present,
        e.one_click_signing_claim,
        e.one_click_compliance,
    ) == (True, True, False, "unknown")
    dk = e.dkim_verification
    assert (dk.dkim, dk.alignment, dk.signing_domain, dk.verifier, dk.observed_at) == (
        "pass",
        "pass",
        "example.com",
        "warmbly",
        "2026-10-01T00:05:00Z",
    )
    assert d.content.score == 80
    issue = d.content.issues[0]
    assert (issue.severity, issue.code, issue.message, issue.field) == (
        "warn",
        "spammy",
        "Spam words",
        "subject",
    )
    assert issue.suggestion == "Drop it"
    span = issue.spans[0]
    assert (span.field, span.text, span.line, span.excerpt) == (
        "subject",
        "FREE",
        1,
        "FREE money",
    )
    assert d.compare.id == "pt_2"

    create = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [TEST, {**TEST, "id": "pt_2"}]})
    )
    made = await v(
        p.create_test(
            sender_account_id="em_1",
            campaign_id="cmp_1",
            sequence_id="seq_1",
            contact_id="ct_1",
            subject="Hello",
            body_html="<p>x</p>",
            body_plain="x",
            tracking="compare",
            panel="workspace",
            seed_ids=["s1"],
            families=["gmail"],
            pace="quick",
            max_credits=6,
        )
    )
    assert [t.id for t in made] == ["pt_1", "pt_2"]
    _check_test(made[0])
    assert last(create).method == "POST"
    assert last(create).headers["idempotency-key"]
    assert json.loads(last(create).content) == {
        "sender_account_id": "em_1",
        "campaign_id": "cmp_1",
        "sequence_id": "seq_1",
        "contact_id": "ct_1",
        "subject": "Hello",
        "body_html": "<p>x</p>",
        "body_plain": "x",
        "tracking": "compare",
        "panel": "workspace",
        "seed_ids": ["s1"],
        "families": ["gmail"],
        "pace": "quick",
        "max_credits": 6,
    }
    await v(p.create_test(sender_account_id="em_1"))
    assert json.loads(last(create).content) == {"sender_account_id": "em_1"}

    cancel = respx.post(f"{BASE_URL}/placement/tests/pt_1/cancel").mock(
        return_value=httpx.Response(200, json={"data": {**TEST, "status": "cancelled"}})
    )
    cancelled = await v(p.cancel_test("pt_1"))
    assert last(cancel).method == "POST"
    assert last(cancel).headers["idempotency-key"]
    assert cancelled.status == "cancelled"


BATCH = {
    "id": "pb_1",
    "created_by": "usr_1",
    "campaign_id": "cmp_1",
    "sequence_id": "seq_1",
    "contact_id": "ct_1",
    "subject": "Hello",
    "body_html": "<p>x</p>",
    "body_plain": "x",
    "tracking": "compare",
    "panel": "instance",
    "pace": "spaced",
    "families": ["gmail"],
    "seed_ids": ["s1"],
    "on_unavailable": "defer",
    "selection": {
        "sender_account_ids": 2,
        "sender_scope": {
            "type": "campaign",
            "campaign_id": "cmp_1",
            "providers": ["gmail"],
            "domains": ["example.com"],
            "tag_ids": ["tag_1"],
            "include_inactive": True,
            "untested_days": 7,
        },
        "sample": {"mode": "percent", "count": 3, "percent": 25, "stratify": "domain"},
        "matched": 40,
    },
    "sender_count": 10,
    "max_credits": 50,
    "credits_spent": 20,
    "status": "completed_with_warnings",
    "error": "some skipped",
    "retry_until": "2026-10-03T00:00:00Z",
    "created_at": "2026-10-01T00:00:00Z",
    "started_at": "2026-10-01T00:01:00Z",
    "finished_at": "2026-10-01T02:00:00Z",
    "progress": {
        "total": 10,
        "queued": 1,
        "deferred": 2,
        "running": 3,
        "completed": 4,
        "skipped": 5,
        "failed": 6,
        "cancelled": 7,
    },
    "summary": PLACEMENT_COUNTS,
}


def _check_batch(b: Any) -> None:
    assert (b.id, b.created_by, b.campaign_id, b.sequence_id, b.contact_id) == (
        "pb_1",
        "usr_1",
        "cmp_1",
        "seq_1",
        "ct_1",
    )
    assert (b.subject, b.body_html, b.body_plain) == ("Hello", "<p>x</p>", "x")
    assert (b.tracking, b.panel, b.pace, b.on_unavailable) == (
        "compare",
        "instance",
        "spaced",
        "defer",
    )
    assert (list(b.families), list(b.seed_ids)) == (["gmail"], ["s1"])
    sel = b.selection
    assert (sel.sender_account_ids, sel.matched) == (2, 40)
    sc = sel.sender_scope
    assert (sc.type, sc.campaign_id, list(sc.providers), list(sc.domains)) == (
        "campaign",
        "cmp_1",
        ["gmail"],
        ["example.com"],
    )
    assert (list(sc.tag_ids), sc.include_inactive, sc.untested_days) == (
        ["tag_1"],
        True,
        7,
    )
    sm = sel.sample
    assert (sm.mode, sm.count, sm.percent, sm.stratify) == ("percent", 3, 25, "domain")
    assert (b.sender_count, b.max_credits, b.credits_spent) == (10, 50, 20)
    assert (b.status, b.error, b.retry_until) == (
        "completed_with_warnings",
        "some skipped",
        "2026-10-03T00:00:00Z",
    )
    assert (b.created_at, b.started_at, b.finished_at) == (
        "2026-10-01T00:00:00Z",
        "2026-10-01T00:01:00Z",
        "2026-10-01T02:00:00Z",
    )
    pr = b.progress
    assert (pr.total, pr.queued, pr.deferred, pr.running) == (10, 1, 2, 3)
    assert (pr.completed, pr.skipped, pr.failed, pr.cancelled) == (4, 5, 6, 7)
    _check_pcounts(b.summary)


@pytest.mark.anyio
@respx.mock
async def test_placement_batches(dual: Any) -> None:
    p = dual.placement
    listing = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=page([BATCH]))
    )
    rows = await items(p.list_batches(limit=10))
    assert last(listing).url.params["limit"] == "10"
    _check_batch(rows[0])

    detail = respx.get(f"{BASE_URL}/placement/batches/pb_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    **BATCH,
                    "untracked": PLACEMENT_COUNTS,
                    "domains": [
                        {
                            "key": "example.com",
                            "label": "example.com",
                            "senders": 4,
                            "tested": 3,
                            "counts": PLACEMENT_COUNTS,
                        }
                    ],
                    "providers": [
                        {
                            "key": "gmail",
                            "label": "Gmail",
                            "senders": 2,
                            "tested": 2,
                            "counts": PLACEMENT_COUNTS,
                        }
                    ],
                    "recipients": FAMILIES,
                    "matrix": [{"domain": "example.com", "recipients": FAMILIES}],
                    "content": {"score": 90, "issues": []},
                }
            },
        )
    )
    d = await v(p.retrieve_batch("pb_1"))
    assert last(detail).method == "GET"
    _check_batch(d)
    _check_pcounts(d.untracked)
    dom = d.domains[0]
    assert (dom.key, dom.label, dom.senders, dom.tested) == (
        "example.com",
        "example.com",
        4,
        3,
    )
    _check_pcounts(dom.counts)
    assert (d.providers[0].key, d.providers[0].label) == ("gmail", "Gmail")
    assert d.recipients[0].family == "gmail"
    assert (d.matrix[0].domain, d.matrix[0].recipients[0].label) == (
        "example.com",
        "Gmail",
    )
    assert d.content.score == 90

    senders = respx.get(f"{BASE_URL}/placement/batches/pb_1/senders").mock(
        return_value=httpx.Response(
            200,
            json=page(
                [
                    {
                        "id": "ps_1",
                        "batch_id": "pb_1",
                        "email_account_id": "em_1",
                        "sender_email": "ann@example.com",
                        "sender_domain": "example.com",
                        "sender_family": "gmail",
                        "sender_family_label": "Gmail",
                        "status": "deferred",
                        "reason": "no_headroom",
                        "detail": "daily limit",
                        "attempts": 2,
                        "next_attempt_at": "2026-10-02T00:00:00Z",
                        "started_at": "2026-10-01T00:00:00Z",
                        "finished_at": "2026-10-01T00:30:00Z",
                        "summary": PLACEMENT_COUNTS,
                        "test_ids": ["pt_1"],
                    }
                ]
            ),
        )
    )
    rows = await items(
        p.list_batch_senders("pb_1", status="deferred", q="ann", sort="best", limit=20)
    )
    params = last(senders).url.params
    assert (params["status"], params["q"], params["sort"], params["limit"]) == (
        "deferred",
        "ann",
        "best",
        "20",
    )
    s = rows[0]
    assert (s.id, s.batch_id, s.email_account_id, s.sender_email) == (
        "ps_1",
        "pb_1",
        "em_1",
        "ann@example.com",
    )
    assert (s.sender_domain, s.sender_family, s.sender_family_label) == (
        "example.com",
        "gmail",
        "Gmail",
    )
    assert (s.status, s.reason, s.detail, s.attempts) == (
        "deferred",
        "no_headroom",
        "daily limit",
        2,
    )
    assert (s.next_attempt_at, s.started_at, s.finished_at) == (
        "2026-10-02T00:00:00Z",
        "2026-10-01T00:00:00Z",
        "2026-10-01T00:30:00Z",
    )
    _check_pcounts(s.summary)
    assert list(s.test_ids) == ["pt_1"]

    body = {
        "sender_account_ids": ["em_1"],
        "sender_scope": {"type": "workspace", "untested_days": 7},
        "sample": {"mode": "random", "count": 5},
        "campaign_id": "cmp_1",
        "sequence_id": "seq_1",
        "contact_id": "ct_1",
        "subject": "Hello",
        "body_html": "<p>x</p>",
        "body_plain": "x",
        "tracking": "compare",
        "panel": "workspace",
        "pace": "spaced",
        "families": ["gmail"],
        "seed_ids": ["s1"],
        "on_unavailable": "defer",
        "max_credits": 50,
    }
    preview = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "matched": 40,
                    "selected": 10,
                    "inactive": 3,
                    "domains": 4,
                    "providers": [{"key": "gmail", "label": "Gmail", "senders": 6}],
                    "variants": 2,
                    "tests": 20,
                    "seeds_per_test": 12,
                    "max_sends": 240,
                    "metered": True,
                    "free_tests": 5,
                    "paid_tests": 15,
                    "credits": 75,
                    "usage": USAGE,
                    "senders_max": 500,
                    "concurrency": 3,
                }
            },
        )
    )
    pv = await v(p.preview_batch(**body))
    assert last(preview).method == "POST"
    assert json.loads(last(preview).content) == body
    assert last(preview).headers["idempotency-key"]
    assert (pv.matched, pv.selected, pv.inactive, pv.domains) == (40, 10, 3, 4)
    assert (pv.providers[0].key, pv.providers[0].label, pv.providers[0].senders) == (
        "gmail",
        "Gmail",
        6,
    )
    assert (pv.variants, pv.tests, pv.seeds_per_test, pv.max_sends) == (2, 20, 12, 240)
    assert (pv.metered, pv.free_tests, pv.paid_tests, pv.credits) == (True, 5, 15, 75)
    _check_usage(pv.usage)
    assert (pv.senders_max, pv.concurrency) == (500, 3)

    create = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": BATCH})
    )
    made = await v(p.create_batch(**body))
    assert json.loads(last(create).content) == body
    assert last(create).headers["idempotency-key"]
    _check_batch(made)
    await v(p.create_batch(sender_account_ids=["em_1"]))
    assert json.loads(last(create).content) == {"sender_account_ids": ["em_1"]}

    cancel = respx.post(f"{BASE_URL}/placement/batches/pb_1/cancel").mock(
        return_value=httpx.Response(
            200, json={"data": {**BATCH, "status": "cancelled"}}
        )
    )
    cancelled = await v(p.cancel_batch("pb_1"))
    assert last(cancel).method == "POST"
    assert last(cancel).headers["idempotency-key"]
    assert cancelled.status == "cancelled"
