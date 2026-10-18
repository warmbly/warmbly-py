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

SENDER = "11111111-1111-1111-1111-111111111111"
TEST_ID = "22222222-2222-2222-2222-222222222222"
BATCH_ID = "33333333-3333-3333-3333-333333333333"

COUNTS: dict[str, Any] = {
    "total": 10,
    "pending": 0,
    "inbox": 6,
    "promotions": 1,
    "other": 0,
    "spam": 2,
    "missing": 1,
    "failed": 0,
    "cancelled": 0,
    "unknown": 0,
    "archive": 0,
    "custom": 0,
    "observed_receipts": 9,
    "classified_receipts": 9,
    "unresolved": 1,
    "primary_metric": {
        "version": "observed-v2",
        "population": "seed_panel",
        "denominator_kind": "classified_observed_receipts",
        "unit": "fraction",
        "numerator": 6,
        "denominator": 9,
        "unresolved": 1,
        "window_basis": "report_date_range_utc",
        "value": 0.667,
        "wilson_95_independence_interval": {"lower": 0.35, "upper": 0.88},
    },
    "non_spam_metric": None,
    "delivered": 10,
    "inbox_rate": 0.6,
    "tabs_rate": 0.1,
    "spam_rate": 0.2,
    "missing_rate": 0.1,
}

TEST_VIEW: dict[str, Any] = {
    "id": TEST_ID,
    "sender_account_id": SENDER,
    "sender_email": "me@acme.com",
    "created_by": None,
    "campaign_id": "c1",
    "sequence_id": None,
    "contact_id": None,
    "monitor_id": None,
    "batch_id": None,
    "subject": "Hello",
    "open_tracking": True,
    "link_tracking": False,
    "compare_group_id": "g1",
    "origin": "manual",
    "panel": "instance",
    "status": "running",
    "pace": "spaced",
    "credits_charged": 2,
    "credits_refunded": 0,
    "credits_settled_at": None,
    "created_at": "2026-10-01T10:00:00Z",
    "finished_at": None,
    "summary": COUNTS,
    "families": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
}

RESULT: dict[str, Any] = {
    "seed": "s***@gmail.com",
    "family": "gmail",
    "family_label": "Gmail",
    "folder": "promotions",
    "scheduled_at": "2026-10-01T10:00:00Z",
    "sent_at": "2026-10-01T10:01:00Z",
    "detected_at": "2026-10-01T10:02:00Z",
    "first_folder": "inbox",
    "observed_at": "2026-10-01T10:03:00Z",
    "late_observation": True,
    "evidence": {
        "dkim_verification": {
            "dkim": "pass",
            "alignment": "pass",
            "signing_domain": "acme.com",
            "verifier": "warmbly",
            "observed_at": "2026-10-01T10:02:00Z",
        },
        "version": "received-v1",
        "source": "headers",
        "trust": "high",
        "observed_at": "2026-10-01T10:02:00Z",
        "spf": "pass",
        "dkim": "pass",
        "dmarc": "pass",
        "alignment": "pass",
        "tls": "pass",
        "from_domain": "acme.com",
        "authentication_results_present": True,
        "one_click_headers_present": True,
        "one_click_signing_claim": False,
        "one_click_compliance": "unknown",
    },
}

CONTENT: dict[str, Any] = {
    "score": 82,
    "issues": [
        {
            "severity": "warn",
            "code": "spammy_word",
            "message": "Avoid this word",
            "field": "subject",
            "spans": [
                {"field": "subject", "text": "free", "line": 1, "excerpt": "free!"}
            ],
            "suggestion": "Rephrase it",
        }
    ],
}

BATCH: dict[str, Any] = {
    "id": BATCH_ID,
    "created_by": None,
    "campaign_id": None,
    "subject": "Hello",
    "tracking": "compare",
    "panel": "workspace",
    "pace": "quick",
    "families": ["gmail"],
    "seed_ids": [],
    "on_unavailable": "defer",
    "selection": {
        "sender_scope": {
            "type": "workspace",
            "providers": ["gmail"],
            "include_inactive": True,
            "untested_days": 7,
        },
        "sample": {"mode": "random", "count": 5, "stratify": "domain"},
        "matched": 40,
    },
    "sender_count": 5,
    "max_credits": 10,
    "credits_spent": 2,
    "status": "completed_with_warnings",
    "retry_until": "2026-10-02T10:00:00Z",
    "created_at": "2026-10-01T10:00:00Z",
    "started_at": "2026-10-01T10:01:00Z",
    "finished_at": None,
    "progress": {"total": 5, "completed": 3, "failed": 1, "skipped": 1},
    "summary": COUNTS,
}

USAGE: dict[str, Any] = {
    "used": 3,
    "limit": 10,
    "credits_per_test": 2,
    "credit_balance": None,
    "period_start": "2026-10-01T00:00:00Z",
    "period_end": "2026-11-01T00:00:00Z",
}


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


def _page(data: list[dict[str, Any]], *, has_more: bool = False) -> dict[str, Any]:
    return {
        "data": data,
        "pagination": {
            "next_cursor": "25" if has_more else None,
            "has_more": has_more,
            "total": len(data),
        },
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _ok(data: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json={"data": data})


def _check_test_detail(detail: Any) -> None:
    assert detail.id == TEST_ID
    assert detail.compare is not None
    assert detail.compare.id == "t2"
    assert detail.content.score == 82
    issue = detail.content.issues[0]
    assert issue.code == "spammy_word"
    assert issue.spans[0].excerpt == "free!"
    result = detail.results[0]
    assert result.folder == "promotions"
    assert result.first_folder == "inbox"
    assert result.late_observation is True
    assert result.evidence.dkim_verification.signing_domain == "acme.com"
    assert result.evidence.one_click_compliance == "unknown"
    assert detail.summary.primary_metric.wilson_95_independence_interval.upper == 0.88
    assert detail.families[0].counts.inbox == 6


def _check_overview(overview: Any) -> None:
    assert overview.panels[0].panel == "instance"
    assert overview.panels[0].families[0].seeds == 4
    assert overview.panels[1].reason == "No seed inboxes yet."
    assert overview.usage.limit == 10
    assert overview.usage.credit_balance is None
    assert overview.workspace_seeds == 2
    assert overview.seeds_per_test == 8
    assert overview.spacing_seconds == 60


OVERVIEW: dict[str, Any] = {
    "panels": [
        {
            "panel": "instance",
            "available": True,
            "seeds": 8,
            "families": [{"family": "gmail", "label": "Gmail", "seeds": 4}],
            "metered": True,
        },
        {
            "panel": "workspace",
            "available": False,
            "reason": "No seed inboxes yet.",
            "seeds": 0,
            "families": [],
            "metered": False,
        },
    ],
    "usage": USAGE,
    "workspace_seeds": 2,
    "seeds_per_test": 8,
    "spacing_seconds": 60,
}

TEST_DETAIL: dict[str, Any] = {
    **TEST_VIEW,
    "body_html": "<p>Hi</p>",
    "results": [RESULT],
    "content": CONTENT,
    "compare": {**TEST_VIEW, "id": "t2", "open_tracking": False},
}

BATCH_DETAIL: dict[str, Any] = {
    **BATCH,
    "untracked": COUNTS,
    "domains": [
        {
            "key": "acme.com",
            "label": "acme.com",
            "senders": 3,
            "tested": 2,
            "counts": COUNTS,
        }
    ],
    "providers": [
        {"key": "gmail", "label": "Gmail", "senders": 3, "tested": 3, "counts": COUNTS}
    ],
    "recipients": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
    "matrix": [
        {
            "domain": "acme.com",
            "recipients": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
        }
    ],
    "content": CONTENT,
}

BATCH_SENDER: dict[str, Any] = {
    "id": "s1",
    "batch_id": BATCH_ID,
    "email_account_id": SENDER,
    "sender_email": "me@acme.com",
    "sender_domain": "acme.com",
    "sender_family": "google_workspace",
    "status": "deferred",
    "reason": "no_headroom",
    "detail": "Daily limit reached",
    "attempts": 2,
    "next_attempt_at": "2026-10-01T12:00:00Z",
    "started_at": None,
    "finished_at": None,
    "sender_family_label": "Google Workspace",
    "summary": COUNTS,
    "test_ids": [TEST_ID],
}

PREVIEW: dict[str, Any] = {
    "matched": 40,
    "selected": 5,
    "inactive": 1,
    "domains": 2,
    "providers": [{"key": "gmail", "label": "Gmail", "senders": 5}],
    "variants": 2,
    "tests": 10,
    "seeds_per_test": 8,
    "max_sends": 80,
    "metered": True,
    "free_tests": 7,
    "paid_tests": 3,
    "credits": 6,
    "usage": USAGE,
    "senders_max": 500,
    "concurrency": 3,
}

SEED: dict[str, Any] = {
    "email_account_id": SENDER,
    "email": "me@acme.com",
    "family": "gmail",
    "label": "Gmail",
    "status": "connected",
    "seed": True,
}


def _check_batch(batch: Any) -> None:
    assert batch.id == BATCH_ID
    assert batch.status == "completed_with_warnings"
    assert batch.selection.matched == 40
    assert batch.selection.sender_scope.providers == ["gmail"]
    assert batch.selection.sender_scope.untested_days == 7
    assert batch.selection.sample.stratify == "domain"
    assert batch.progress.completed == 3
    assert batch.summary.spam == 2


def _check_batch_detail(detail: Any) -> None:
    _check_batch(detail)
    assert detail.untracked.inbox == 6
    assert detail.domains[0].tested == 2
    assert detail.providers[0].counts.promotions == 1
    assert detail.recipients[0].family == "gmail"
    assert detail.matrix[0].recipients[0].label == "Gmail"
    assert detail.content.score == 82


def _check_preview(preview: Any) -> None:
    assert preview.selected == 5
    assert preview.providers[0].senders == 5
    assert preview.max_sends == 80
    assert preview.paid_tests == 3
    assert preview.credits == 6
    assert preview.usage.used == 3
    assert preview.concurrency == 3


def _check_sender(sender: Any) -> None:
    assert sender.status == "deferred"
    assert sender.attempts == 2
    assert sender.sender_family_label == "Google Workspace"
    assert sender.summary.delivered == 10
    assert sender.test_ids == [TEST_ID]


BATCH_BODY_EXPECTED = {
    "sender_scope": {"type": "workspace", "providers": ["gmail"]},
    "sample": {"mode": "random", "count": 5},
    "on_unavailable": "skip",
    "campaign_id": "c1",
    "sequence_id": "q1",
    "contact_id": "k1",
    "subject": "Hi",
    "body_html": "<p>Hi</p>",
    "body_plain": "Hi",
    "tracking": "compare",
    "panel": "workspace",
    "pace": "quick",
    "families": ["gmail"],
    "seed_ids": ["a"],
    "max_credits": 4,
}


def _batch_kwargs() -> dict[str, Any]:
    return {
        "sender_scope": {"type": "workspace", "providers": ["gmail"]},
        "sample": {"mode": "random", "count": 5},
        "on_unavailable": "skip",
        "campaign_id": "c1",
        "sequence_id": "q1",
        "contact_id": "k1",
        "subject": "Hi",
        "body_html": "<p>Hi</p>",
        "body_plain": "Hi",
        "tracking": "compare",
        "panel": "workspace",
        "pace": "quick",
        "families": ["gmail"],
        "seed_ids": ["a"],
        "max_credits": 4,
    }


@respx.mock
def test_overview_and_coverage(client: Warmbly) -> None:
    overview = respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=_ok(OVERVIEW)
    )
    result = client.placement.overview()
    _check_overview(result)
    assert _last(overview).method == "GET"

    coverage = respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=_ok(
            {"mailboxes": 20, "tested_7d": 5, "tested_30d": 12, "never_tested": 8}
        )
    )
    cov = client.placement.coverage()
    assert (cov.mailboxes, cov.tested_7d, cov.tested_30d, cov.never_tested) == (
        20,
        5,
        12,
        8,
    )
    assert _last(coverage).url.path == "/v1/placement/coverage"


@respx.mock
def test_malformed_envelope_never_raises(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=_ok({"usage": "unexpected"})
    )
    assert client.placement.overview() is not None


@respx.mock
def test_tests(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(200, json=_page([TEST_VIEW]))
    )
    tests = list(client.placement.list_tests(campaign_id="c1", limit=10))
    assert tests[0].id == TEST_ID
    assert tests[0].sender_email == "me@acme.com"
    assert tests[0].open_tracking is True
    assert tests[0].summary.inbox_rate == 0.6
    assert dict(_last(listing).url.params) == {"campaign_id": "c1", "limit": "10"}

    detail = respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=_ok(TEST_DETAIL)
    )
    _check_test_detail(client.placement.retrieve_test(TEST_ID))
    assert _last(detail).method == "GET"

    create = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=_ok([TEST_VIEW, {**TEST_VIEW, "id": "t2"}], 201)
    )
    created = client.placement.create_tests(
        sender_account_id=SENDER,
        campaign_id="c1",
        sequence_id="q1",
        contact_id="k1",
        subject="Hi",
        body_html="<p>Hi</p>",
        body_plain="Hi",
        tracking="compare",
        panel="instance",
        pace="quick",
        families=["gmail"],
        seed_ids=["a"],
        max_credits=4,
    )
    assert [t.id for t in created] == [TEST_ID, "t2"]
    assert created[0].compare_group_id == "g1"
    assert json.loads(_last(create).content) == {
        "sender_account_id": SENDER,
        "campaign_id": "c1",
        "sequence_id": "q1",
        "contact_id": "k1",
        "subject": "Hi",
        "body_html": "<p>Hi</p>",
        "body_plain": "Hi",
        "tracking": "compare",
        "panel": "instance",
        "pace": "quick",
        "families": ["gmail"],
        "seed_ids": ["a"],
        "max_credits": 4,
    }
    assert _last(create).headers.get("idempotency-key")

    minimal = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=_ok([TEST_VIEW], 201)
    )
    client.placement.create_tests(sender_account_id=SENDER, campaign_id="c1")
    assert json.loads(_last(minimal).content) == {
        "sender_account_id": SENDER,
        "campaign_id": "c1",
    }

    cancel = respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=_ok({**TEST_VIEW, "status": "cancelled"})
    )
    assert client.placement.cancel_test(TEST_ID).status == "cancelled"
    assert _last(cancel).method == "POST"


@respx.mock
def test_seeds(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=_ok(
            [
                SEED,
                {
                    **SEED,
                    "email_account_id": "x",
                    "seed": False,
                    "blocker": "Not connected",
                },
            ]
        )
    )
    seeds = list(client.placement.list_seeds())
    assert seeds[0].email_account_id == SENDER
    assert seeds[0].seed is True
    assert seeds[1].blocker == "Not connected"
    assert _last(listing).method == "GET"

    put = respx.put(f"{BASE_URL}/placement/seeds/{SENDER}").mock(
        return_value=_ok({**SEED, "seed": False})
    )
    seed = client.placement.set_seed(SENDER, seed=False)
    assert seed.seed is False
    assert seed.family == "gmail"
    assert json.loads(_last(put).content) == {"seed": False}


@respx.mock
def test_batches(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_page([BATCH]))
    )
    batches = list(client.placement.list_batches(limit=5))
    _check_batch(batches[0])
    assert dict(_last(listing).url.params) == {"limit": "5"}

    detail = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=_ok(BATCH_DETAIL)
    )
    _check_batch_detail(client.placement.retrieve_batch(BATCH_ID))
    assert _last(detail).method == "GET"

    senders = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_page([BATCH_SENDER]))
    )
    rows = list(
        client.placement.list_batch_senders(
            BATCH_ID, status="deferred", q="acme", sort="best", limit=20
        )
    )
    _check_sender(rows[0])
    assert dict(_last(senders).url.params) == {
        "status": "deferred",
        "q": "acme",
        "sort": "best",
        "limit": "20",
    }

    preview = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=_ok(PREVIEW)
    )
    _check_preview(client.placement.preview_batch(**_batch_kwargs()))
    assert json.loads(_last(preview).content) == BATCH_BODY_EXPECTED

    create = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=_ok(BATCH, 201)
    )
    _check_batch(
        client.placement.create_batch(sender_account_ids=[SENDER], subject="Hi")
    )
    assert json.loads(_last(create).content) == {
        "sender_account_ids": [SENDER],
        "subject": "Hi",
    }
    assert _last(create).headers.get("idempotency-key")
    client.placement.create_batch(**_batch_kwargs())
    assert json.loads(_last(create).content) == BATCH_BODY_EXPECTED

    cancel = respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=_ok({**BATCH, "status": "cancelled"})
    )
    assert client.placement.cancel_batch(BATCH_ID).status == "cancelled"
    assert _last(cancel).method == "POST"


@respx.mock
@pytest.mark.anyio
async def test_async_overview_and_coverage(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/overview").mock(return_value=_ok(OVERVIEW))
    _check_overview(await aclient.placement.overview())

    respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=_ok(
            {"mailboxes": 20, "tested_7d": 5, "tested_30d": 12, "never_tested": 8}
        )
    )
    cov = await aclient.placement.coverage()
    assert (cov.mailboxes, cov.never_tested) == (20, 8)


@respx.mock
@pytest.mark.anyio
async def test_async_tests(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(200, json=_page([TEST_VIEW]))
    )
    tests = [t async for t in aclient.placement.list_tests(campaign_id="c1")]
    assert tests[0].id == TEST_ID
    assert tests[0].summary.spam == 2
    assert dict(_last(listing).url.params) == {"campaign_id": "c1"}

    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=_ok(TEST_DETAIL)
    )
    _check_test_detail(await aclient.placement.retrieve_test(TEST_ID))

    create = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=_ok([TEST_VIEW], 201)
    )
    created = await aclient.placement.create_tests(
        sender_account_id=SENDER,
        subject="Hi",
        body_plain="Hi",
        tracking="off",
        families=["gmail"],
    )
    assert created[0].id == TEST_ID
    assert json.loads(_last(create).content) == {
        "sender_account_id": SENDER,
        "subject": "Hi",
        "body_plain": "Hi",
        "tracking": "off",
        "families": ["gmail"],
    }
    assert _last(create).headers.get("idempotency-key")

    respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=_ok({**TEST_VIEW, "status": "cancelled"})
    )
    assert (await aclient.placement.cancel_test(TEST_ID)).status == "cancelled"


@respx.mock
@pytest.mark.anyio
async def test_async_seeds(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/seeds").mock(return_value=_ok([SEED]))
    seeds = [s async for s in aclient.placement.list_seeds()]
    assert seeds[0].email == "me@acme.com"
    assert seeds[0].label == "Gmail"

    put = respx.put(f"{BASE_URL}/placement/seeds/{SENDER}").mock(return_value=_ok(SEED))
    seed = await aclient.placement.set_seed(SENDER, seed=True)
    assert seed.seed is True
    assert json.loads(_last(put).content) == {"seed": True}


@respx.mock
@pytest.mark.anyio
async def test_async_batches(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_page([BATCH]))
    )
    batches = [b async for b in aclient.placement.list_batches(limit=5)]
    _check_batch(batches[0])
    assert dict(_last(listing).url.params) == {"limit": "5"}

    respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=_ok(BATCH_DETAIL)
    )
    _check_batch_detail(await aclient.placement.retrieve_batch(BATCH_ID))

    senders = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_page([BATCH_SENDER]))
    )
    rows = [
        r
        async for r in aclient.placement.list_batch_senders(
            BATCH_ID, status="deferred", q="acme", sort="best", limit=20
        )
    ]
    _check_sender(rows[0])
    assert dict(_last(senders).url.params) == {
        "status": "deferred",
        "q": "acme",
        "sort": "best",
        "limit": "20",
    }

    preview = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=_ok(PREVIEW)
    )
    _check_preview(await aclient.placement.preview_batch(**_batch_kwargs()))
    assert json.loads(_last(preview).content) == BATCH_BODY_EXPECTED

    create = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=_ok(BATCH, 201)
    )
    _check_batch(await aclient.placement.create_batch(**_batch_kwargs()))
    assert json.loads(_last(create).content) == BATCH_BODY_EXPECTED
    assert _last(create).headers.get("idempotency-key")

    respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=_ok({**BATCH, "status": "cancelled"})
    )
    assert (await aclient.placement.cancel_batch(BATCH_ID)).status == "cancelled"
