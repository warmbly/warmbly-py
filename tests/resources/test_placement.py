"""Tests for the ``placement`` resource, sync and async.

Payloads are built from the server's Go structs: the ``data`` envelope, the
nullable pointers (``null``) and the ``omitempty`` fields (absent).
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

TEST_ID = "5b0b3c1e-1111-4a6e-9d11-000000000001"
BATCH_ID = "5b0b3c1e-2222-4a6e-9d11-000000000002"
SENDER_ID = "5b0b3c1e-3333-4a6e-9d11-000000000003"
CAMPAIGN_ID = "5b0b3c1e-4444-4a6e-9d11-000000000004"


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


def _paged(
    data: list[dict[str, Any]], *, next_cursor: str | None = None
) -> dict[str, Any]:
    return {
        "data": data,
        "pagination": {
            "total": len(data),
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        },
    }


def _counts(**over: Any) -> dict[str, Any]:
    """A models.PlacementCounts after Finish()."""
    base: dict[str, Any] = {
        "total": 10,
        "pending": 0,
        "inbox": 6,
        "promotions": 2,
        "other": 0,
        "spam": 1,
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
            "version": "observation-metric-v1",
            "population": "seed_panel",
            "denominator_kind": "classified_observed_receipts",
            "unit": "fraction",
            "source": "seed_panel",
            "classification_policy": "v1",
            "numerator": 6,
            "denominator": 9,
            "unresolved": 1,
            "window_basis": "test",
            "missingness_basis": "unresolved",
            "value": 0.6667,
            "wilson_95_independence_interval": {"lower": 0.35, "upper": 0.88},
        },
        "non_spam_metric": None,
        "delivered": 10,
        "inbox_rate": 0.6,
        "tabs_rate": 0.2,
        "spam_rate": 0.1,
        "missing_rate": 0.1,
    }
    base.update(over)
    return base


def _test(**over: Any) -> dict[str, Any]:
    """A placement.TestView (models.PlacementTest plus summary and families)."""
    base: dict[str, Any] = {
        "id": TEST_ID,
        "sender_account_id": SENDER_ID,
        "sender_email": "sam@acme.io",
        "created_by": None,
        "campaign_id": CAMPAIGN_ID,
        "sequence_id": None,
        "contact_id": None,
        "monitor_id": None,
        "batch_id": None,
        "subject": "Quick question",
        "open_tracking": True,
        "link_tracking": False,
        "compare_group_id": None,
        "origin": "manual",
        "panel": "instance",
        "status": "running",
        "pace": "spaced",
        "credits_charged": 0,
        "credits_refunded": 0,
        "credits_settled_at": None,
        "created_at": "2026-10-30T09:00:00Z",
        "finished_at": None,
        "summary": _counts(),
        "families": [
            {
                "family": "gmail",
                "label": "Gmail",
                "counts": _counts(total=4, inbox=3),
            }
        ],
    }
    base.update(over)
    return base


def _batch(**over: Any) -> dict[str, Any]:
    """A placement.BatchView."""
    base: dict[str, Any] = {
        "id": BATCH_ID,
        "created_by": None,
        "campaign_id": None,
        "sequence_id": None,
        "contact_id": None,
        "subject": "Hello",
        "tracking": "campaign",
        "panel": "instance",
        "pace": "spaced",
        "families": [],
        "seed_ids": [],
        "on_unavailable": "defer",
        "selection": {
            "sender_scope": {"type": "workspace", "providers": ["gmail"]},
            "sample": {"mode": "all"},
            "matched": 40,
        },
        "sender_count": 40,
        "max_credits": 0,
        "credits_spent": 0,
        "status": "running",
        "retry_until": "2026-11-02T09:00:00Z",
        "created_at": "2026-10-30T09:00:00Z",
        "started_at": "2026-10-30T09:01:00Z",
        "finished_at": None,
        "progress": {
            "total": 40,
            "queued": 30,
            "deferred": 0,
            "running": 5,
            "completed": 5,
            "skipped": 0,
            "failed": 0,
            "cancelled": 0,
        },
        "summary": _counts(),
    }
    base.update(over)
    return base


def _check_test(t: Any) -> None:
    assert t.id == TEST_ID
    assert t.sender_account_id == SENDER_ID
    assert t.sender_email == "sam@acme.io"
    assert t.campaign_id == CAMPAIGN_ID
    assert t.sequence_id is None
    assert t.open_tracking is True
    assert t.link_tracking is False
    assert t.origin == "manual"
    assert t.panel == "instance"
    assert t.status == "running"
    assert t.pace == "spaced"
    assert t.summary.inbox == 6
    assert t.summary.archive == 0
    assert t.summary.inbox_rate == 0.6
    assert t.summary.primary_metric.numerator == 6
    assert t.summary.primary_metric.wilson_95_independence_interval["upper"] == 0.88
    assert t.summary.non_spam_metric is None
    assert t.families[0].family == "gmail"
    assert t.families[0].counts.inbox == 3


# ---------------------------------------------------------------- workspace


@respx.mock
def test_overview_and_coverage(client: Warmbly) -> None:
    overview = respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "panels": [
                        {
                            "panel": "instance",
                            "available": True,
                            "seeds": 12,
                            "families": [
                                {"family": "gmail", "label": "Gmail", "seeds": 5}
                            ],
                            "metered": True,
                        },
                        {
                            "panel": "workspace",
                            "available": False,
                            "reason": "Mark at least one mailbox as a seed.",
                            "seeds": 0,
                            "families": [],
                            "metered": False,
                        },
                    ],
                    "usage": {
                        "used": 3,
                        "limit": 10,
                        "credits_per_test": 2,
                        "credit_balance": None,
                        "period_start": "2026-10-01T00:00:00Z",
                        "period_end": "2026-11-01T00:00:00Z",
                    },
                    "workspace_seeds": 0,
                    "seeds_per_test": 12,
                    "spacing_seconds": 60,
                }
            },
        )
    )
    out = client.placement.overview().data
    assert _last(overview).method == "GET"
    assert out.panels[0].panel == "instance"
    assert out.panels[0].metered is True
    assert out.panels[0].families[0].seeds == 5
    assert out.panels[1].available is False
    assert out.panels[1].reason == "Mark at least one mailbox as a seed."
    assert out.usage.used == 3
    assert out.usage.limit == 10
    assert out.usage.credits_per_test == 2
    assert out.usage.credit_balance is None
    assert out.usage.period_end == "2026-11-01T00:00:00Z"
    assert out.seeds_per_test == 12
    assert out.spacing_seconds == 60

    coverage = respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "mailboxes": 20,
                    "tested_7d": 8,
                    "tested_30d": 15,
                    "never_tested": 5,
                }
            },
        )
    )
    cov = client.placement.coverage().data
    assert _last(coverage).url.path == "/v1/placement/coverage"
    assert (cov.mailboxes, cov.tested_7d, cov.tested_30d, cov.never_tested) == (
        20,
        8,
        15,
        5,
    )


@pytest.mark.anyio
@respx.mock
async def test_overview_and_coverage_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"panels": [], "usage": {"used": 1, "limit": None}}},
        )
    )
    out = (await aclient.placement.overview()).data
    assert out.usage.used == 1
    assert out.usage.limit is None

    respx.get(f"{BASE_URL}/placement/coverage").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "mailboxes": 3,
                    "tested_7d": 1,
                    "tested_30d": 2,
                    "never_tested": 1,
                }
            },
        )
    )
    assert (await aclient.placement.coverage()).data.never_tested == 1


# -------------------------------------------------------------------- seeds


SEED = {
    "email_account_id": SENDER_ID,
    "email": "seed@acme.io",
    "family": "google_workspace",
    "label": "Google Workspace",
    "status": "active",
    "seed": True,
}


@respx.mock
def test_seeds(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    SEED,
                    {**SEED, "email": "b@acme.io", "seed": False, "blocker": "Busy"},
                ]
            },
        )
    )
    seeds = list(client.placement.list_seeds())
    assert _last(listing).method == "GET"
    assert [s.email for s in seeds] == ["seed@acme.io", "b@acme.io"]
    assert seeds[0].email_account_id == SENDER_ID
    assert seeds[0].family == "google_workspace"
    assert seeds[0].label == "Google Workspace"
    assert seeds[0].status == "active"
    assert seeds[0].seed is True
    assert seeds[0].blocker is None
    assert seeds[1].seed is False
    assert seeds[1].blocker == "Busy"

    put = respx.put(f"{BASE_URL}/placement/seeds/{SENDER_ID}").mock(
        return_value=httpx.Response(200, json={"data": SEED})
    )
    out = client.placement.set_seed(SENDER_ID, seed=True).data
    assert _last(put).method == "PUT"
    assert _body(put) == {"seed": True}
    assert out.email == "seed@acme.io"
    assert out.seed is True


@pytest.mark.anyio
@respx.mock
async def test_seeds_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(200, json={"data": [SEED]})
    )
    seeds = [s async for s in aclient.placement.list_seeds()]
    assert seeds[0].email == "seed@acme.io"
    assert seeds[0].seed is True

    put = respx.put(f"{BASE_URL}/placement/seeds/{SENDER_ID}").mock(
        return_value=httpx.Response(200, json={"data": {**SEED, "seed": False}})
    )
    out = (await aclient.placement.set_seed(SENDER_ID, seed=False)).data
    assert _body(put) == {"seed": False}
    assert out.seed is False


# -------------------------------------------------------------------- tests


@respx.mock
def test_list_tests_pages(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/tests").mock(
        side_effect=[
            httpx.Response(200, json=_paged([_test()], next_cursor="c2")),
            httpx.Response(200, json=_paged([_test(id="t2")])),
        ]
    )
    tests = list(client.placement.list_tests(campaign_id=CAMPAIGN_ID, limit=1))
    assert [t.id for t in tests] == [TEST_ID, "t2"]
    _check_test(tests[0])
    first, second = (c.request for c in route.calls)
    assert first.url.params["campaign_id"] == CAMPAIGN_ID
    assert first.url.params["limit"] == "1"
    assert "cursor" not in first.url.params
    assert second.url.params["cursor"] == "c2"
    assert second.url.params["campaign_id"] == CAMPAIGN_ID


@pytest.mark.anyio
@respx.mock
async def test_list_tests_pages_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/tests").mock(
        side_effect=[
            httpx.Response(200, json=_paged([_test()], next_cursor="c2")),
            httpx.Response(200, json=_paged([_test(id="t2")])),
        ]
    )
    tests = [t async for t in aclient.placement.list_tests()]
    assert [t.id for t in tests] == [TEST_ID, "t2"]
    _check_test(tests[0])
    assert route.calls[1].request.url.params["cursor"] == "c2"
    assert "campaign_id" not in route.calls[0].request.url.params


DETAIL = {
    **_test(body_html="<p>Hi</p>", body_plain="Hi"),
    "results": [
        {
            "seed": "g***@gmail.com",
            "family": "gmail",
            "family_label": "Gmail",
            "folder": "missing",
            "scheduled_at": "2026-10-30T09:00:00Z",
            "sent_at": "2026-10-30T09:01:00Z",
            "detected_at": None,
            "first_folder": "spam",
            "observed_at": "2026-10-30T09:20:00Z",
            "late_observation": True,
            "evidence": {
                "version": "received-v1",
                "source": "headers",
                "trust": "high",
                "observed_at": "2026-10-30T09:20:00Z",
                "spf": "pass",
                "dkim": "pass",
                "dmarc": "pass",
                "alignment": "aligned",
                "tls": "yes",
                "authentication_results_present": True,
                "one_click_headers_present": False,
                "one_click_signing_claim": False,
                "one_click_compliance": "unknown",
                "dkim_verification": None,
            },
        }
    ],
    "content": {
        "score": 82,
        "issues": [
            {
                "severity": "warn",
                "code": "spammy_word",
                "message": "Avoid 'free'.",
                "field": "subject",
                "suggestion": "Reword it.",
            }
        ],
    },
    "compare": _test(id="t-untracked", open_tracking=False),
}


def _check_detail(d: Any) -> None:
    _check_test(d)
    assert d.body_html == "<p>Hi</p>"
    assert d.body_plain == "Hi"
    r = d.results[0]
    assert r.seed == "g***@gmail.com"
    assert r.family_label == "Gmail"
    assert r.folder == "missing"
    assert r.sent_at == "2026-10-30T09:01:00Z"
    assert r.detected_at is None
    assert r.first_folder == "spam"
    assert r.late_observation is True
    assert r.evidence.spf == "pass"
    assert r.evidence.alignment == "aligned"
    assert r.evidence.authentication_results_present is True
    assert d.content.score == 82
    assert d.content.issues[0]["code"] == "spammy_word"
    assert d.compare.id == "t-untracked"
    assert d.compare.open_tracking is False


@respx.mock
def test_retrieve_test(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(200, json={"data": DETAIL})
    )
    _check_detail(client.placement.retrieve_test(TEST_ID).data)
    assert _last(route).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_retrieve_test_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(200, json={"data": DETAIL})
    )
    _check_detail((await aclient.placement.retrieve_test(TEST_ID)).data)


@respx.mock
def test_create_test(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(
            201, json={"data": [_test(), _test(id="t-untracked")]}
        )
    )
    out = client.placement.create_test(
        sender_account_id=SENDER_ID,
        campaign_id=CAMPAIGN_ID,
        sequence_id="seq_1",
        tracking="compare",
        panel="workspace",
        seed_ids=["s1", "s2"],
        families=("gmail",),
        pace="quick",
        max_credits=4,
        options={"idempotency_key": "idem-1"},
    )
    req = _last(route)
    assert req.method == "POST"
    assert req.headers["Idempotency-Key"] == "idem-1"
    assert _body(route) == {
        "sender_account_id": SENDER_ID,
        "campaign_id": CAMPAIGN_ID,
        "sequence_id": "seq_1",
        "tracking": "compare",
        "panel": "workspace",
        "seed_ids": ["s1", "s2"],
        "families": ["gmail"],
        "pace": "quick",
        "max_credits": 4,
    }
    assert [t.id for t in out.data] == [TEST_ID, "t-untracked"]
    _check_test(out.data[0])


@respx.mock
def test_create_test_minimal_body_and_auto_idempotency(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [_test()]})
    )
    client.placement.create_test(
        sender_account_id=SENDER_ID, subject="Hi", body_plain="Hello"
    )
    assert _body(route) == {
        "sender_account_id": SENDER_ID,
        "subject": "Hi",
        "body_plain": "Hello",
    }
    assert _last(route).headers["Idempotency-Key"]


@pytest.mark.anyio
@respx.mock
async def test_create_and_cancel_test_async(aclient: AsyncWarmbly) -> None:
    create = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [_test()]})
    )
    out = await aclient.placement.create_test(
        sender_account_id=SENDER_ID, campaign_id=CAMPAIGN_ID, max_credits=2
    )
    assert _body(create) == {
        "sender_account_id": SENDER_ID,
        "campaign_id": CAMPAIGN_ID,
        "max_credits": 2,
    }
    _check_test(out.data[0])

    cancel = respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": _test(status="cancelled", finished_at="2026-10-30T10:00:00Z")
            },
        )
    )
    done = (await aclient.placement.cancel_test(TEST_ID)).data
    assert _last(cancel).method == "POST"
    assert done.status == "cancelled"
    assert done.finished_at == "2026-10-30T10:00:00Z"


@respx.mock
def test_cancel_test(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": _test(status="cancelled")})
    )
    out = client.placement.cancel_test(TEST_ID).data
    assert _last(route).method == "POST"
    assert out.status == "cancelled"
    assert out.sender_email == "sam@acme.io"


# ------------------------------------------------------------------ batches


def _check_batch(b: Any) -> None:
    assert b.id == BATCH_ID
    assert b.subject == "Hello"
    assert b.tracking == "campaign"
    assert b.panel == "instance"
    assert b.on_unavailable == "defer"
    assert b.selection["matched"] == 40
    assert b.selection["sender_scope"]["providers"] == ["gmail"]
    assert b.sender_count == 40
    assert b.status == "running"
    assert b.retry_until == "2026-11-02T09:00:00Z"
    assert b.started_at == "2026-10-30T09:01:00Z"
    assert b.finished_at is None
    assert b.progress.total == 40
    assert b.progress.queued == 30
    assert b.progress.running == 5
    assert b.summary.inbox == 6
    assert b.summary.inbox_rate == 0.6


@respx.mock
def test_list_batches_pages(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/batches").mock(
        side_effect=[
            httpx.Response(200, json=_paged([_batch()], next_cursor="b2")),
            httpx.Response(200, json=_paged([_batch(id="b-2")])),
        ]
    )
    batches = list(client.placement.list_batches(limit=1))
    assert [b.id for b in batches] == [BATCH_ID, "b-2"]
    _check_batch(batches[0])
    assert route.calls[0].request.url.params["limit"] == "1"
    assert route.calls[1].request.url.params["cursor"] == "b2"


@pytest.mark.anyio
@respx.mock
async def test_list_batches_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_paged([_batch()]))
    )
    batches = [b async for b in aclient.placement.list_batches()]
    _check_batch(batches[0])


BATCH_DETAIL = {
    **_batch(),
    "untracked": _counts(inbox=5),
    "domains": [
        {
            "key": "acme.io",
            "label": "acme.io",
            "senders": 10,
            "tested": 8,
            "counts": _counts(),
        }
    ],
    "providers": [
        {
            "key": "google_workspace",
            "label": "Google Workspace",
            "senders": 30,
            "tested": 20,
            "counts": _counts(),
        }
    ],
    "recipients": [{"family": "gmail", "label": "Gmail", "counts": _counts()}],
    "matrix": [
        {
            "domain": "acme.io",
            "recipients": [
                {"family": "gmail", "label": "Gmail", "counts": _counts(inbox=4)}
            ],
        }
    ],
    "content": {"score": 90, "issues": []},
}


def _check_batch_detail(d: Any) -> None:
    _check_batch(d)
    assert d.untracked.inbox == 5
    assert d.domains[0].key == "acme.io"
    assert d.domains[0].senders == 10
    assert d.domains[0].tested == 8
    assert d.domains[0].counts.inbox == 6
    assert d.providers[0].label == "Google Workspace"
    assert d.recipients[0].family == "gmail"
    assert d.matrix[0].domain == "acme.io"
    assert d.matrix[0].recipients[0].counts.inbox == 4
    assert d.content.score == 90


@respx.mock
def test_retrieve_batch(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(200, json={"data": BATCH_DETAIL})
    )
    _check_batch_detail(client.placement.retrieve_batch(BATCH_ID).data)
    assert _last(route).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_retrieve_batch_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(200, json={"data": BATCH_DETAIL})
    )
    _check_batch_detail((await aclient.placement.retrieve_batch(BATCH_ID)).data)


BATCH_SENDER = {
    "id": "bs-1",
    "batch_id": BATCH_ID,
    "email_account_id": SENDER_ID,
    "sender_email": "sam@acme.io",
    "sender_domain": "acme.io",
    "sender_family": "google_workspace",
    "status": "deferred",
    "reason": "no_headroom",
    "detail": "Daily limit reached.",
    "attempts": 2,
    "next_attempt_at": "2026-10-31T09:00:00Z",
    "started_at": None,
    "finished_at": None,
    "sender_family_label": "Google Workspace",
    "summary": _counts(),
    "test_ids": [TEST_ID],
}


def _check_sender(s: Any) -> None:
    assert s.id == "bs-1"
    assert s.batch_id == BATCH_ID
    assert s.email_account_id == SENDER_ID
    assert s.sender_email == "sam@acme.io"
    assert s.sender_domain == "acme.io"
    assert s.sender_family == "google_workspace"
    assert s.sender_family_label == "Google Workspace"
    assert s.status == "deferred"
    assert s.reason == "no_headroom"
    assert s.detail == "Daily limit reached."
    assert s.attempts == 2
    assert s.next_attempt_at == "2026-10-31T09:00:00Z"
    assert s.started_at is None
    assert s.summary.inbox == 6
    assert s.test_ids == [TEST_ID]


@respx.mock
def test_list_batch_senders(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        side_effect=[
            httpx.Response(200, json=_paged([BATCH_SENDER], next_cursor="n2")),
            httpx.Response(200, json=_paged([{**BATCH_SENDER, "id": "bs-2"}])),
        ]
    )
    senders = list(
        client.placement.list_batch_senders(
            BATCH_ID, status="deferred", q="sam", sort="worst", limit=1
        )
    )
    assert [s.id for s in senders] == ["bs-1", "bs-2"]
    _check_sender(senders[0])
    params = route.calls[0].request.url.params
    assert params["status"] == "deferred"
    assert params["q"] == "sam"
    assert params["sort"] == "worst"
    assert params["limit"] == "1"
    assert route.calls[1].request.url.params["cursor"] == "n2"
    assert route.calls[1].request.url.params["q"] == "sam"


@pytest.mark.anyio
@respx.mock
async def test_list_batch_senders_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_paged([BATCH_SENDER]))
    )
    senders = [s async for s in aclient.placement.list_batch_senders(BATCH_ID)]
    _check_sender(senders[0])
    assert dict(route.calls[0].request.url.params) == {}


PREVIEW = {
    "matched": 40,
    "selected": 25,
    "inactive": 3,
    "domains": 4,
    "providers": [
        {"key": "google_workspace", "label": "Google Workspace", "senders": 25}
    ],
    "variants": 2,
    "tests": 50,
    "seeds_per_test": 12,
    "max_sends": 600,
    "metered": True,
    "free_tests": 20,
    "paid_tests": 30,
    "credits": 60,
    "usage": {
        "used": 0,
        "limit": 20,
        "credits_per_test": 2,
        "credit_balance": 100,
        "period_start": "2026-10-01T00:00:00Z",
        "period_end": "2026-11-01T00:00:00Z",
    },
    "senders_max": 500,
    "concurrency": 3,
}

BATCH_ARGS: dict[str, Any] = {
    "sender_scope": {"type": "campaign", "campaign_id": CAMPAIGN_ID},
    "sample": {"mode": "random", "count": 25, "stratify": "provider"},
    "campaign_id": CAMPAIGN_ID,
    "tracking": "compare",
    "panel": "instance",
    "families": ["gmail"],
    "on_unavailable": "skip",
    "max_credits": 60,
}


def _check_preview(p: Any) -> None:
    assert p.matched == 40
    assert p.selected == 25
    assert p.inactive == 3
    assert p.domains == 4
    assert p.providers[0].key == "google_workspace"
    assert p.providers[0].senders == 25
    assert p.variants == 2
    assert p.tests == 50
    assert p.seeds_per_test == 12
    assert p.max_sends == 600
    assert p.metered is True
    assert (p.free_tests, p.paid_tests, p.credits) == (20, 30, 60)
    assert p.usage.credit_balance == 100
    assert p.senders_max == 500
    assert p.concurrency == 3


@respx.mock
def test_preview_batch(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(200, json={"data": PREVIEW})
    )
    out = client.placement.preview_batch(**BATCH_ARGS)
    assert _last(route).method == "POST"
    assert _body(route) == BATCH_ARGS
    _check_preview(out.data)


@respx.mock
def test_create_batch(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": _batch()})
    )
    out = client.placement.create_batch(
        sender_account_ids=(SENDER_ID,),
        subject="Hello",
        body_plain="Hi",
        seed_ids=["s1"],
        panel="workspace",
        options={"idempotency_key": "idem-b"},
    )
    req = _last(route)
    assert req.method == "POST"
    assert req.headers["Idempotency-Key"] == "idem-b"
    assert _body(route) == {
        "sender_account_ids": [SENDER_ID],
        "subject": "Hello",
        "body_plain": "Hi",
        "seed_ids": ["s1"],
        "panel": "workspace",
    }
    _check_batch(out.data)


@respx.mock
def test_cancel_batch(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": _batch(status="cancelled")})
    )
    out = client.placement.cancel_batch(BATCH_ID).data
    assert _last(route).method == "POST"
    assert out.status == "cancelled"
    assert out.progress.total == 40


@pytest.mark.anyio
@respx.mock
async def test_batch_writes_async(aclient: AsyncWarmbly) -> None:
    preview = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(200, json={"data": PREVIEW})
    )
    _check_preview((await aclient.placement.preview_batch(**BATCH_ARGS)).data)
    assert _body(preview) == BATCH_ARGS

    create = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": _batch()})
    )
    out = await aclient.placement.create_batch(**BATCH_ARGS)
    assert _body(create) == BATCH_ARGS
    assert _last(create).headers["Idempotency-Key"]
    _check_batch(out.data)

    cancel = respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": _batch(status="cancelled")})
    )
    assert (await aclient.placement.cancel_batch(BATCH_ID)).data.status == "cancelled"
    assert _last(cancel).method == "POST"


# -------------------------------------------------------------- tolerance


@respx.mock
def test_unknown_values_and_fields_never_raise(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": TEST_ID,
                    "status": "a_future_status",
                    "panel": "a_future_panel",
                    "a_future_field": {"x": 1},
                    "summary": {"total": 1, "a_future_folder": 3},
                    "results": [{"folder": "a_future_folder", "extra": True}],
                }
            },
        )
    )
    d = client.placement.retrieve_test(TEST_ID).data
    assert d.status == "a_future_status"
    assert d.panel == "a_future_panel"
    assert d.summary.total == 1
    assert d.results[0].folder == "a_future_folder"
    assert d.a_future_field == {"x": 1}


@respx.mock
def test_go_nil_slices_read_as_empty(client: Warmbly) -> None:
    """Go marshals a nil slice as ``null``; the model must still validate."""
    respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": BATCH_ID,
                    "status": "queued",
                    "families": None,
                    "seed_ids": None,
                    "domains": None,
                    "matrix": None,
                    "progress": {"total": 2, "queued": 2},
                }
            },
        )
    )
    b = client.placement.retrieve_batch(BATCH_ID).data
    assert b.status == "queued"
    assert b.families == []
    assert b.seed_ids == []
    assert b.domains == []
    assert b.matrix == []
    assert b.progress.queued == 2
