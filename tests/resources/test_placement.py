"""Tests for the ``placement`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
TEST_ID = "d1e2f3a4-0000-0000-0000-000000000010"
BATCH_ID = "e1e2f3a4-0000-0000-0000-000000000011"
SENDER_ID = "a0a1a2a3-0000-0000-0000-000000000003"


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


def _paged(data: list[dict[str, Any]], *, next_cursor: str | None = None) -> dict:
    return {
        "data": data,
        "pagination": {
            "total": len(data),
            "has_more": next_cursor is not None,
            "next_cursor": next_cursor,
        },
    }


COUNTS = {
    "total": 38,
    "pending": 0,
    "inbox": 30,
    "promotions": 4,
    "other": 0,
    "spam": 2,
    "missing": 2,
    "failed": 0,
    "cancelled": 0,
    "unknown": 0,
    "archive": 0,
    "custom": 0,
    "observed_receipts": 36,
    "classified_receipts": 36,
    "unresolved": 2,
    "primary_metric": {
        "version": "observed-v2",
        "population": "seed_panel",
        "denominator_kind": "classified_observed_receipts",
        "unit": "fraction",
        "source": "mailbox_observation",
        "classification_policy": "first_folder_v2_with_legacy_classifications",
        "numerator": 30,
        "denominator": 36,
        "unresolved": 2,
        "window_basis": "report_date_range_utc",
        "missingness_basis": "unclassified_observed_receipts",
        "value": 0.8333,
        "wilson_95_independence_interval": {"lower": 0.69, "upper": 0.92},
    },
    "non_spam_metric": None,
    "delivered": 38,
    "inbox_rate": 0.79,
    "tabs_rate": 0.1,
    "spam_rate": 0.05,
    "missing_rate": 0.05,
}

TEST_VIEW = {
    "id": TEST_ID,
    "sender_account_id": SENDER_ID,
    "sender_email": "sales@yourdomain.com",
    "created_by": "9c2a0000-0000-0000-0000-000000000001",
    "campaign_id": "b1f2c3d4-0000-0000-0000-000000000001",
    "sequence_id": None,
    "contact_id": None,
    "monitor_id": None,
    "batch_id": BATCH_ID,
    "subject": "Quick question",
    "open_tracking": False,
    "link_tracking": False,
    "compare_group_id": None,
    "origin": "manual",
    "panel": "instance",
    "status": "running",
    "pace": "spaced",
    "credits_charged": 25,
    "credits_refunded": 0,
    "credits_settled_at": None,
    "charged_usd": 0.5,
    "refunded_usd": 0,
    "created_at": "2026-09-25T14:00:00Z",
    "finished_at": None,
    "summary": COUNTS,
    "families": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
}

RESULT = {
    "seed": "g***@gmail.com",
    "family": "gmail",
    "family_label": "Gmail",
    "folder": "promotions",
    "scheduled_at": "2026-09-25T14:00:00Z",
    "sent_at": "2026-09-25T14:00:05Z",
    "detected_at": "2026-09-25T14:01:00Z",
    "first_folder": "promotions",
    "observed_at": "2026-09-25T14:01:00Z",
    "late_observation": False,
    "evidence": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
}

CONTENT = {
    "score": 82,
    "issues": [
        {
            "severity": "warn",
            "code": "spammy_word",
            "message": "Avoid 'free'",
            "field": "subject",
            "spans": [{"start": 0, "end": 4}],
            "suggestion": "Reword it",
        }
    ],
}

BATCH_VIEW = {
    "id": BATCH_ID,
    "created_by": None,
    "campaign_id": None,
    "sequence_id": None,
    "contact_id": None,
    "subject": "Hello",
    "tracking": "campaign",
    "panel": "instance",
    "pace": "spaced",
    "families": ["gmail"],
    "seed_ids": [],
    "on_unavailable": "defer",
    "selection": {
        "sender_scope": {"type": "workspace"},
        "sample": {"mode": "random", "count": 5},
        "matched": 40,
    },
    "sender_count": 5,
    "max_credits": 125,
    "credits_spent": 0,
    "max_usd": 2.5,
    "spent_usd": 0.0,
    "status": "queued",
    "retry_until": "2026-09-26T14:00:00Z",
    "created_at": "2026-09-25T14:00:00Z",
    "started_at": None,
    "finished_at": None,
    "progress": {
        "total": 5,
        "queued": 5,
        "deferred": 0,
        "running": 0,
        "completed": 0,
        "skipped": 0,
        "failed": 0,
        "cancelled": 0,
    },
    "summary": COUNTS,
}

BATCH_DETAIL = {
    **BATCH_VIEW,
    "untracked": COUNTS,
    "domains": [
        {
            "key": "yourdomain.com",
            "label": "yourdomain.com",
            "senders": 3,
            "tested": 3,
            "counts": COUNTS,
        }
    ],
    "providers": [],
    "recipients": [{"family": "outlook", "label": "Outlook.com", "counts": COUNTS}],
    "matrix": [
        {
            "domain": "yourdomain.com",
            "recipients": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
        }
    ],
    "content": CONTENT,
}

USAGE = {
    "used": 4,
    "limit": 40,
    "price_per_test_usd": 0.5,
    "balance_usd": 36.8,
    "credits_per_test": 25,
    "credit_balance": 1840,
    "period_start": "2026-09-01T00:00:00Z",
    "period_end": "2026-10-01T00:00:00Z",
}


# -- overview / coverage -----------------------------------------------------


@respx.mock
def test_overview_and_coverage_sync(client: Warmbly) -> None:
    overview = respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "panels": [
                        {
                            "panel": "workspace",
                            "available": False,
                            "reason": "Mark a mailbox as a seed inbox.",
                            "seeds": 0,
                            "families": [
                                {"family": "gmail", "label": "Gmail", "seeds": 10}
                            ],
                            "metered": False,
                        }
                    ],
                    "usage": USAGE,
                    "workspace_seeds": 0,
                    "seeds_per_test": 20,
                    "spacing_seconds": 60,
                }
            },
        )
    )
    out = client.placement.overview()
    assert _last(overview).method == "GET"
    assert out.data is not None
    assert out.data.panels[0].reason == "Mark a mailbox as a seed inbox."
    assert out.data.panels[0].families[0].seeds == 10
    assert out.data.usage is not None
    assert out.data.usage.balance_usd == 36.8
    assert out.data.usage.limit == 40
    assert out.data.seeds_per_test == 20
    assert out.data.spacing_seconds == 60

    cov = respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "mailboxes": 50,
                    "tested_7d": 12,
                    "tested_30d": 31,
                    "never_tested": 9,
                }
            },
        )
    )
    coverage = client.placement.coverage()
    assert _last(cov).url.path == "/v1/placement/coverage"
    assert coverage.data is not None
    assert coverage.data.tested_30d == 31
    assert coverage.data.never_tested == 9


@respx.mock
@pytest.mark.anyio
async def test_overview_and_coverage_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(
            200, json={"data": {"panels": [], "usage": USAGE, "workspace_seeds": 3}}
        )
    )
    out = await aclient.placement.overview()
    assert out.data is not None
    assert out.data.workspace_seeds == 3
    assert out.data.usage is not None
    assert out.data.usage.credit_balance == 1840

    cov = respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "mailboxes": 5,
                    "tested_7d": 1,
                    "tested_30d": 2,
                    "never_tested": 3,
                }
            },
        )
    )
    coverage = await aclient.placement.coverage()
    assert _last(cov).method == "GET"
    assert coverage.data is not None
    assert coverage.data.mailboxes == 5


# -- tests -------------------------------------------------------------------


@respx.mock
def test_tests_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/tests").mock(
        side_effect=[
            httpx.Response(200, json=_paged([TEST_VIEW], next_cursor="c2")),
            httpx.Response(200, json=_paged([{"id": "t2"}])),
        ]
    )
    tests = list(
        client.placement.list_tests(
            campaign_id="b1f2c3d4-0000-0000-0000-000000000001", limit=1
        )
    )
    assert [t.id for t in tests] == [TEST_ID, "t2"]
    first = tests[0]
    assert first.sender_email == "sales@yourdomain.com"
    assert first.batch_id == BATCH_ID
    assert first.charged_usd == 0.5
    assert first.summary is not None
    assert first.summary.inbox_rate == 0.79
    assert first.summary.primary_metric is not None
    assert first.summary.primary_metric.numerator == 30
    assert first.summary.primary_metric.wilson_95_independence_interval == {
        "lower": 0.69,
        "upper": 0.92,
    }
    assert first.families[0].counts is not None
    assert first.families[0].counts.promotions == 4
    first_req = listing.calls[0].request
    assert first_req.url.params["campaign_id"] == "b1f2c3d4-0000-0000-0000-000000000001"
    assert first_req.url.params["limit"] == "1"
    assert listing.calls[1].request.url.params["cursor"] == "c2"

    create = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [TEST_VIEW, {"id": "t2"}]})
    )
    created = client.placement.create_test(
        sender_account_id=SENDER_ID,
        campaign_id="camp",
        sequence_id="seq",
        contact_id="con",
        subject="Hi",
        body_html="<p>x</p>",
        body_plain="x",
        tracking="compare",
        panel="workspace",
        seed_ids=["s1"],
        families=["gmail"],
        pace="quick",
        max_usd=1.5,
        max_credits=75,
    )
    assert [t.id for t in created.data] == [TEST_ID, "t2"]
    request = _last(create)
    assert request.method == "POST"
    assert request.headers["Idempotency-Key"]
    assert json.loads(request.content) == {
        "sender_account_id": SENDER_ID,
        "campaign_id": "camp",
        "sequence_id": "seq",
        "contact_id": "con",
        "subject": "Hi",
        "body_html": "<p>x</p>",
        "body_plain": "x",
        "tracking": "compare",
        "panel": "workspace",
        "seed_ids": ["s1"],
        "families": ["gmail"],
        "pace": "quick",
        "max_usd": 1.5,
        "max_credits": 75,
    }

    respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": []})
    )
    client.placement.create_test(sender_account_id=SENDER_ID, body_plain="x")

    detail = respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    **TEST_VIEW,
                    "body_html": "<p>x</p>",
                    "results": [RESULT],
                    "content": CONTENT,
                    "compare": {"id": "t2", "open_tracking": True},
                }
            },
        )
    )
    got = client.placement.retrieve_test(TEST_ID)
    assert _last(detail).url.path == f"/v1/placement/tests/{TEST_ID}"
    assert got.data is not None
    assert got.data.body_html == "<p>x</p>"
    assert got.data.results[0].folder == "promotions"
    assert got.data.results[0].late_observation is False
    assert got.data.results[0].evidence == {
        "spf": "pass",
        "dkim": "pass",
        "dmarc": "pass",
    }
    assert got.data.content is not None
    assert got.data.content.score == 82
    assert got.data.content.issues[0].suggestion == "Reword it"
    assert got.data.content.issues[0].spans[0]["end"] == 4
    assert got.data.compare is not None
    assert got.data.compare.open_tracking is True

    cancel = respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=httpx.Response(
            200, json={"data": {**TEST_VIEW, "status": "cancelled"}}
        )
    )
    cancelled = client.placement.cancel_test(TEST_ID)
    assert _last(cancel).method == "POST"
    assert cancelled.data is not None
    assert cancelled.data.status == "cancelled"


@respx.mock
@pytest.mark.anyio
async def test_tests_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(200, json=_paged([TEST_VIEW]))
    )
    assert [t.id async for t in aclient.placement.list_tests(limit=5)] == [TEST_ID]
    assert _last(listing).url.params["limit"] == "5"

    create = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [TEST_VIEW]})
    )
    created = await aclient.placement.create_test(
        sender_account_id=SENDER_ID,
        campaign_id="camp",
        sequence_id="seq",
        contact_id="con",
        subject="Hi",
        body_html="<p>x</p>",
        body_plain="x",
        tracking="on",
        panel="instance",
        seed_ids=["s1"],
        families=["gmail"],
        pace="spaced",
        max_usd=1.0,
        max_credits=50,
    )
    assert created.data[0].sender_email == "sales@yourdomain.com"
    body = json.loads(_last(create).content)
    assert body["sender_account_id"] == SENDER_ID
    assert body["max_usd"] == 1.0
    assert body["seed_ids"] == ["s1"]
    assert _last(create).headers["Idempotency-Key"]

    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(
            200, json={"data": {**TEST_VIEW, "results": [RESULT], "content": CONTENT}}
        )
    )
    got = await aclient.placement.retrieve_test(TEST_ID)
    assert got.data is not None
    assert got.data.results[0].seed == "g***@gmail.com"

    cancel = respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": TEST_VIEW})
    )
    cancelled = await aclient.placement.cancel_test(TEST_ID)
    assert _last(cancel).method == "POST"
    assert cancelled.data is not None
    assert cancelled.data.id == TEST_ID


# -- seeds -------------------------------------------------------------------

SEED = {
    "email_account_id": SENDER_ID,
    "email": "seed@yourdomain.com",
    "family": "google_workspace",
    "label": "Google Workspace",
    "status": "active",
    "seed": True,
}


@respx.mock
def test_seeds_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(
            200,
            json={"data": [SEED, {**SEED, "email_account_id": "x", "blocker": "No"}]},
        )
    )
    seeds = list(client.placement.list_seeds())
    assert _last(listing).url.path == "/v1/placement/seeds"
    assert seeds[0].family == "google_workspace"
    assert seeds[0].seed is True
    assert seeds[1].blocker == "No"

    put = respx.put(f"{BASE_URL}/placement/seeds/{SENDER_ID}").mock(
        return_value=httpx.Response(200, json={"data": {**SEED, "seed": False}})
    )
    out = client.placement.set_seed(SENDER_ID, seed=False)
    assert _last(put).method == "PUT"
    assert json.loads(_last(put).content) == {"seed": False}
    assert out.data is not None
    assert out.data.seed is False
    assert out.data.label == "Google Workspace"


@respx.mock
@pytest.mark.anyio
async def test_seeds_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(200, json={"data": [SEED]})
    )
    assert [s.email async for s in aclient.placement.list_seeds()] == [
        "seed@yourdomain.com"
    ]

    put = respx.put(f"{BASE_URL}/placement/seeds/{SENDER_ID}").mock(
        return_value=httpx.Response(200, json={"data": SEED})
    )
    out = await aclient.placement.set_seed(SENDER_ID, seed=True)
    assert json.loads(_last(put).content) == {"seed": True}
    assert out.data is not None
    assert out.data.status == "active"


# -- batches -----------------------------------------------------------------

PREVIEW = {
    "matched": 40,
    "selected": 5,
    "inactive": 2,
    "domains": 3,
    "providers": [
        {"key": "google_workspace", "label": "Google Workspace", "senders": 4}
    ],
    "variants": 2,
    "tests": 10,
    "seeds_per_test": 20,
    "max_sends": 200,
    "metered": True,
    "free_tests": 4,
    "paid_tests": 6,
    "cost_usd": 3.0,
    "credits": 150,
    "usage": USAGE,
    "senders_max": 500,
    "concurrency": 3,
}

BATCH_SENDER = {
    "id": "bs1",
    "batch_id": BATCH_ID,
    "email_account_id": SENDER_ID,
    "sender_email": "sales@yourdomain.com",
    "sender_domain": "yourdomain.com",
    "sender_family": "google_workspace",
    "status": "deferred",
    "reason": "daily_limit",
    "detail": "No headroom",
    "attempts": 2,
    "next_attempt_at": "2026-09-25T15:00:00Z",
    "started_at": None,
    "finished_at": None,
    "sender_family_label": "Google Workspace",
    "summary": COUNTS,
    "test_ids": [TEST_ID],
}

BATCH_ARGS: dict[str, Any] = {
    "sender_account_ids": [SENDER_ID],
    "sender_scope": {"type": "workspace", "providers": ["gmail"]},
    "sample": {"mode": "random", "count": 5, "stratify": "provider"},
    "campaign_id": "camp",
    "sequence_id": "seq",
    "contact_id": "con",
    "subject": "Hi",
    "body_html": "<p>x</p>",
    "body_plain": "x",
    "tracking": "compare",
    "panel": "instance",
    "pace": "quick",
    "families": ["gmail"],
    "seed_ids": ["s1"],
    "on_unavailable": "skip",
    "max_usd": 3.0,
    "max_credits": 150,
}


@respx.mock
def test_batches_sync(client: Warmbly) -> None:
    preview = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(200, json={"data": PREVIEW})
    )
    out = client.placement.preview_batch(**BATCH_ARGS)
    assert json.loads(_last(preview).content) == BATCH_ARGS
    assert out.data is not None
    assert out.data.providers[0].senders == 4
    assert out.data.cost_usd == 3.0
    assert out.data.paid_tests == 6
    assert out.data.usage is not None
    assert out.data.usage.used == 4
    assert out.data.concurrency == 3

    create = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": BATCH_VIEW})
    )
    created = client.placement.create_batch(**BATCH_ARGS)
    request = _last(create)
    assert request.method == "POST"
    assert request.headers["Idempotency-Key"]
    assert json.loads(request.content) == BATCH_ARGS
    assert created.data is not None
    assert created.data.status == "queued"
    assert created.data.progress is not None
    assert created.data.progress.queued == 5
    assert created.data.selection == BATCH_VIEW["selection"]
    assert created.data.max_usd == 2.5
    assert created.data.families == ["gmail"]

    respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": BATCH_VIEW})
    )
    client.placement.create_batch(sender_scope={"type": "campaign"})

    listing = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_paged([BATCH_VIEW]))
    )
    batches = list(client.placement.list_batches(limit=10, cursor="c1"))
    assert batches[0].id == BATCH_ID
    assert _last(listing).url.params["limit"] == "10"
    assert _last(listing).url.params["cursor"] == "c1"

    detail = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(200, json={"data": BATCH_DETAIL})
    )
    got = client.placement.retrieve_batch(BATCH_ID)
    assert _last(detail).method == "GET"
    assert got.data is not None
    assert got.data.untracked is not None
    assert got.data.untracked.inbox == 30
    assert got.data.domains[0].tested == 3
    assert got.data.domains[0].counts is not None
    assert got.data.domains[0].counts.spam == 2
    assert got.data.recipients[0].family == "outlook"
    assert got.data.matrix[0].recipients[0].label == "Gmail"
    assert got.data.content is not None
    assert got.data.content.issues[0].code == "spammy_word"

    cancel = respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=httpx.Response(
            200, json={"data": {**BATCH_VIEW, "status": "cancelled"}}
        )
    )
    cancelled = client.placement.cancel_batch(BATCH_ID)
    assert _last(cancel).method == "POST"
    assert cancelled.data is not None
    assert cancelled.data.status == "cancelled"

    senders_route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_paged([BATCH_SENDER]))
    )
    senders = list(
        client.placement.list_batch_senders(
            BATCH_ID, status="deferred", q="sales", sort="best", limit=20
        )
    )
    params = _last(senders_route).url.params
    assert params["status"] == "deferred"
    assert params["q"] == "sales"
    assert params["sort"] == "best"
    assert params["limit"] == "20"
    assert senders[0].reason == "daily_limit"
    assert senders[0].attempts == 2
    assert senders[0].sender_family_label == "Google Workspace"
    assert senders[0].test_ids == [TEST_ID]
    assert senders[0].summary is not None
    assert senders[0].summary.delivered == 38


@respx.mock
@pytest.mark.anyio
async def test_batches_async(aclient: AsyncWarmbly) -> None:
    preview = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(200, json={"data": PREVIEW})
    )
    out = await aclient.placement.preview_batch(**BATCH_ARGS)
    assert json.loads(_last(preview).content) == BATCH_ARGS
    assert out.data is not None
    assert out.data.selected == 5

    create = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": BATCH_VIEW})
    )
    created = await aclient.placement.create_batch(**BATCH_ARGS)
    assert json.loads(_last(create).content) == BATCH_ARGS
    assert _last(create).headers["Idempotency-Key"]
    assert created.data is not None
    assert created.data.sender_count == 5

    listing = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_paged([BATCH_VIEW]))
    )
    assert [b.id async for b in aclient.placement.list_batches(limit=2)] == [BATCH_ID]
    assert _last(listing).url.params["limit"] == "2"

    respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(200, json={"data": BATCH_DETAIL})
    )
    got = await aclient.placement.retrieve_batch(BATCH_ID)
    assert got.data is not None
    assert got.data.providers == []
    assert got.data.matrix[0].domain == "yourdomain.com"

    cancel = respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": BATCH_VIEW})
    )
    cancelled = await aclient.placement.cancel_batch(BATCH_ID)
    assert _last(cancel).method == "POST"
    assert cancelled.data is not None
    assert cancelled.data.id == BATCH_ID

    senders_route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_paged([BATCH_SENDER]))
    )
    senders = [
        s
        async for s in aclient.placement.list_batch_senders(
            BATCH_ID, status="deferred", q="s", sort="worst", limit=3, cursor="c"
        )
    ]
    params = _last(senders_route).url.params
    assert (params["status"], params["q"], params["sort"]) == ("deferred", "s", "worst")
    assert (params["limit"], params["cursor"]) == ("3", "c")
    assert senders[0].sender_domain == "yourdomain.com"
