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
TEST_ID = "11111111-1111-1111-1111-111111111111"
BATCH_ID = "22222222-2222-2222-2222-222222222222"
SENDER_ID = "33333333-3333-3333-3333-333333333333"


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


def _page(data: list[dict[str, Any]], next_cursor: str | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
            "total": len(data),
        },
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


COUNTS = {
    "total": 10,
    "pending": 0,
    "inbox": 6,
    "promotions": 2,
    "other": 0,
    "spam": 1,
    "missing": 1,
    "failed": 0,
    "cancelled": 0,
    "delivered": 10,
    "inbox_rate": 0.6,
    "tabs_rate": 0.2,
    "spam_rate": 0.1,
    "missing_rate": 0.1,
}

TEST = {
    "id": TEST_ID,
    "sender_account_id": SENDER_ID,
    "sender_email": "alex@example.com",
    "created_by": None,
    "campaign_id": None,
    "sequence_id": None,
    "contact_id": None,
    "monitor_id": None,
    "batch_id": BATCH_ID,
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
    "created_at": "2026-10-01T10:00:00Z",
    "finished_at": None,
    "summary": COUNTS,
    "families": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
}

DETAIL = {
    **TEST,
    "body_plain": "Hi there",
    "results": [
        {
            "seed": "a***@gmail.com",
            "family": "gmail",
            "family_label": "Gmail",
            "folder": "promotions",
            "scheduled_at": "2026-10-01T10:00:00Z",
            "sent_at": "2026-10-01T10:01:00Z",
            "detected_at": "2026-10-01T10:03:00Z",
        }
    ],
    "content": {
        "score": 82,
        "issues": [{"severity": "warn", "code": "links", "message": "Many links"}],
    },
    "compare": {**TEST, "id": "44444444-4444-4444-4444-444444444444"},
}

BATCH = {
    "id": BATCH_ID,
    "created_by": None,
    "campaign_id": None,
    "subject": "Quick question",
    "tracking": "compare",
    "panel": "instance",
    "pace": "quick",
    "families": ["gmail"],
    "seed_ids": [],
    "on_unavailable": "defer",
    "selection": {
        "sender_scope": {"type": "workspace", "providers": ["gmail"]},
        "sample": {"mode": "percent", "percent": 20},
        "matched": 40,
    },
    "sender_count": 8,
    "max_credits": 5,
    "credits_spent": 2,
    "status": "running",
    "retry_until": "2026-10-02T10:00:00Z",
    "created_at": "2026-10-01T10:00:00Z",
    "started_at": "2026-10-01T10:00:05Z",
    "finished_at": None,
    "progress": {"total": 8, "queued": 2, "running": 1, "completed": 5},
    "summary": COUNTS,
}

BATCH_DETAIL = {
    **BATCH,
    "untracked": COUNTS,
    "domains": [
        {
            "key": "example.com",
            "label": "example.com",
            "senders": 4,
            "tested": 3,
            "counts": COUNTS,
        }
    ],
    "providers": [],
    "recipients": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
    "matrix": [
        {
            "domain": "example.com",
            "recipients": [{"family": "gmail", "label": "Gmail", "counts": COUNTS}],
        }
    ],
    "content": {"score": 90, "issues": []},
}

SENDER = {
    "id": "55555555-5555-5555-5555-555555555555",
    "batch_id": BATCH_ID,
    "email_account_id": SENDER_ID,
    "sender_email": "alex@example.com",
    "sender_domain": "example.com",
    "sender_family": "google_workspace",
    "status": "completed",
    "attempts": 1,
    "next_attempt_at": "2026-10-01T10:00:00Z",
    "started_at": "2026-10-01T10:00:00Z",
    "finished_at": "2026-10-01T10:05:00Z",
    "sender_family_label": "Google Workspace",
    "summary": COUNTS,
    "test_ids": [TEST_ID],
}

PREVIEW = {
    "matched": 40,
    "selected": 8,
    "inactive": 1,
    "domains": 3,
    "providers": [{"key": "gmail", "label": "Gmail", "senders": 8}],
    "variants": 2,
    "tests": 16,
    "seeds_per_test": 12,
    "max_sends": 192,
    "metered": True,
    "free_tests": 10,
    "paid_tests": 6,
    "credits": 12,
    "usage": {
        "used": 4,
        "limit": 10,
        "credits_per_test": 2,
        "credit_balance": 100,
        "period_start": "2026-10-01T00:00:00Z",
        "period_end": "2026-11-01T00:00:00Z",
    },
    "senders_max": 500,
    "concurrency": 3,
}

OVERVIEW = {
    "data": {
        "panels": [
            {
                "panel": "workspace",
                "available": False,
                "reason": "Mark one mailbox as a seed.",
                "seeds": 0,
                "families": [],
                "metered": False,
            },
            {
                "panel": "instance",
                "available": True,
                "seeds": 12,
                "families": [{"family": "gmail", "label": "Gmail", "seeds": 6}],
                "metered": True,
            },
        ],
        "usage": PREVIEW["usage"],
        "workspace_seeds": 0,
        "seeds_per_test": 12,
        "spacing_seconds": 60,
    }
}

SEED = {
    "email_account_id": SENDER_ID,
    "email": "seed@example.com",
    "family": "gmail",
    "label": "Gmail",
    "status": "active",
    "seed": True,
}


def _check_test(test: Any) -> None:
    assert test.id == TEST_ID
    assert test.sender_email == "alex@example.com"
    assert test.open_tracking is True
    assert test.status == "running"
    assert test.summary.inbox_rate == 0.6
    assert test.families[0].counts.promotions == 2


def _check_overview(overview: Any) -> None:
    assert overview.panels[1].available is True
    assert overview.panels[1].families[0].seeds == 6
    assert overview.usage.limit == 10
    assert overview.usage.credit_balance == 100
    assert overview.seeds_per_test == 12


def _check_detail(detail: Any) -> None:
    _check_test(detail)
    assert detail.results[0].folder == "promotions"
    assert detail.content.score == 82
    assert detail.content.issues[0]["code"] == "links"
    assert detail.compare.id == "44444444-4444-4444-4444-444444444444"


def _check_batch(batch: Any) -> None:
    assert batch.id == BATCH_ID
    assert batch.selection.sample.percent == 20
    assert batch.selection.sender_scope.providers == ["gmail"]
    assert batch.selection.matched == 40
    assert batch.progress.completed == 5
    assert batch.summary.spam == 1


def _check_batch_detail(detail: Any) -> None:
    _check_batch(detail)
    assert detail.untracked.total == 10
    assert detail.domains[0].tested == 3
    assert detail.matrix[0].recipients[0].family == "gmail"
    assert detail.content.score == 90


def _check_sender(sender: Any) -> None:
    assert sender.sender_domain == "example.com"
    assert sender.sender_family_label == "Google Workspace"
    assert sender.summary.delivered == 10
    assert sender.test_ids == [TEST_ID]


def _check_preview(preview: Any) -> None:
    assert preview.selected == 8
    assert preview.providers[0].key == "gmail"
    assert preview.credits == 12
    assert preview.usage.used == 4


TEST_BODY = {
    "sender_account_id": SENDER_ID,
    "campaign_id": "c1",
    "sequence_id": "s1",
    "contact_id": "k1",
    "subject": "Hi",
    "body_html": "<p>Hi</p>",
    "body_plain": "Hi",
    "tracking": "compare",
    "panel": "workspace",
    "seed_ids": ["seed1"],
    "families": ["gmail"],
    "pace": "quick",
    "max_credits": 4,
}

BATCH_BODY = {
    "sender_account_ids": [SENDER_ID],
    "sender_scope": {"type": "campaign", "campaign_id": "c1"},
    "sample": {"mode": "random", "count": 5},
    "campaign_id": "c1",
    "sequence_id": "s1",
    "contact_id": "k1",
    "subject": "Hi",
    "body_html": "<p>Hi</p>",
    "body_plain": "Hi",
    "tracking": "on",
    "panel": "instance",
    "pace": "spaced",
    "families": ["gmail"],
    "seed_ids": ["seed1"],
    "on_unavailable": "skip",
    "max_credits": 6,
}


@respx.mock
def test_placement_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    _check_overview(client.placement.overview())
    assert _last(route).method == "GET"

    route = respx.get(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(200, json=_page([TEST]))
    )
    tests = list(client.placement.list_tests(campaign_id="c1", limit=5, cursor="x"))
    _check_test(tests[0])
    params = _last(route).url.params
    assert params["campaign_id"] == "c1"
    assert params["limit"] == "5"
    assert params["cursor"] == "x"

    route = respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(200, json={"data": DETAIL})
    )
    _check_detail(client.placement.get_test(TEST_ID))
    assert _last(route).url.path == f"/v1/placement/tests/{TEST_ID}"

    route = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [TEST, TEST]})
    )
    created = client.placement.create_test(
        **TEST_BODY  # type: ignore[arg-type]
    )
    assert len(created) == 2
    _check_test(created[0])
    request = _last(route)
    assert request.method == "POST"
    assert json.loads(request.content) == TEST_BODY
    assert request.headers.get("idempotency-key")

    route = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [TEST]})
    )
    client.placement.create_test(sender_account_id=SENDER_ID)
    assert json.loads(_last(route).content) == {"sender_account_id": SENDER_ID}

    route = respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": TEST})
    )
    _check_test(client.placement.cancel_test(TEST_ID))
    assert _last(route).method == "POST"

    route = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_page([BATCH]))
    )
    batches = list(client.placement.list_batches(limit=10, cursor="y"))
    _check_batch(batches[0])
    assert _last(route).url.params["limit"] == "10"
    assert _last(route).url.params["cursor"] == "y"

    route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(200, json={"data": BATCH_DETAIL})
    )
    _check_batch_detail(client.placement.get_batch(BATCH_ID))

    route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_page([SENDER]))
    )
    senders = list(
        client.placement.list_batch_senders(
            BATCH_ID, status="completed", q="alex", sort="inbox_rate", limit=20
        )
    )
    _check_sender(senders[0])
    params = _last(route).url.params
    assert params["status"] == "completed"
    assert params["q"] == "alex"
    assert params["sort"] == "inbox_rate"
    assert params["limit"] == "20"

    route = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(200, json={"data": PREVIEW})
    )
    _check_preview(client.placement.preview_batch(**BATCH_BODY))  # type: ignore[arg-type]
    assert json.loads(_last(route).content) == BATCH_BODY

    route = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": BATCH})
    )
    _check_batch(client.placement.create_batch(**BATCH_BODY))  # type: ignore[arg-type]
    request = _last(route)
    assert json.loads(request.content) == BATCH_BODY
    assert request.headers.get("idempotency-key")

    route = respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": BATCH})
    )
    _check_batch(client.placement.cancel_batch(BATCH_ID))
    assert _last(route).method == "POST"

    respx.get(f"{BASE_URL}/placement/coverage").mock(
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
    coverage = client.placement.coverage()
    assert (coverage.mailboxes, coverage.tested_7d) == (20, 5)
    assert (coverage.tested_30d, coverage.never_tested) == (12, 8)

    respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(200, json={"data": [SEED]})
    )
    seeds = client.placement.list_seeds()
    assert seeds[0].email_account_id == SENDER_ID
    assert seeds[0].seed is True

    route = respx.put(f"{BASE_URL}/placement/seeds/{SENDER_ID}").mock(
        return_value=httpx.Response(
            200, json={"data": {**SEED, "seed": False, "blocker": "x"}}
        )
    )
    seed = client.placement.set_seed(SENDER_ID, seed=False)
    assert seed.seed is False
    assert seed.blocker == "x"
    assert _last(route).method == "PUT"
    assert json.loads(_last(route).content) == {"seed": False}


@respx.mock
@pytest.mark.anyio
async def test_placement_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/placement/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    _check_overview(await aclient.placement.overview())
    assert _last(route).method == "GET"

    route = respx.get(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(200, json=_page([TEST]))
    )
    tests = [t async for t in aclient.placement.list_tests(campaign_id="c1", limit=5)]
    _check_test(tests[0])
    assert _last(route).url.params["campaign_id"] == "c1"
    assert _last(route).url.params["limit"] == "5"

    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(200, json={"data": DETAIL})
    )
    _check_detail(await aclient.placement.get_test(TEST_ID))

    route = respx.post(f"{BASE_URL}/placement/tests").mock(
        return_value=httpx.Response(201, json={"data": [TEST, TEST]})
    )
    created = await aclient.placement.create_test(**TEST_BODY)  # type: ignore[arg-type]
    assert len(created) == 2
    _check_test(created[1])
    request = _last(route)
    assert json.loads(request.content) == TEST_BODY
    assert request.headers.get("idempotency-key")

    respx.post(f"{BASE_URL}/placement/tests/{TEST_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": TEST})
    )
    _check_test(await aclient.placement.cancel_test(TEST_ID))

    route = respx.get(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(200, json=_page([BATCH]))
    )
    batches = [b async for b in aclient.placement.list_batches(limit=10)]
    _check_batch(batches[0])
    assert _last(route).url.params["limit"] == "10"

    respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}").mock(
        return_value=httpx.Response(200, json={"data": BATCH_DETAIL})
    )
    _check_batch_detail(await aclient.placement.get_batch(BATCH_ID))

    route = respx.get(f"{BASE_URL}/placement/batches/{BATCH_ID}/senders").mock(
        return_value=httpx.Response(200, json=_page([SENDER]))
    )
    senders = [
        s
        async for s in aclient.placement.list_batch_senders(
            BATCH_ID, status="completed", q="alex", sort="inbox_rate", limit=20
        )
    ]
    _check_sender(senders[0])
    params = _last(route).url.params
    assert params["status"] == "completed"
    assert params["sort"] == "inbox_rate"

    route = respx.post(f"{BASE_URL}/placement/batches/preview").mock(
        return_value=httpx.Response(200, json={"data": PREVIEW})
    )
    _check_preview(await aclient.placement.preview_batch(**BATCH_BODY))  # type: ignore[arg-type]
    assert json.loads(_last(route).content) == BATCH_BODY

    route = respx.post(f"{BASE_URL}/placement/batches").mock(
        return_value=httpx.Response(201, json={"data": BATCH})
    )
    _check_batch(await aclient.placement.create_batch(**BATCH_BODY))  # type: ignore[arg-type]
    request = _last(route)
    assert json.loads(request.content) == BATCH_BODY
    assert request.headers.get("idempotency-key")

    respx.post(f"{BASE_URL}/placement/batches/{BATCH_ID}/cancel").mock(
        return_value=httpx.Response(200, json={"data": BATCH})
    )
    _check_batch(await aclient.placement.cancel_batch(BATCH_ID))

    respx.get(f"{BASE_URL}/placement/coverage").mock(
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
    assert (await aclient.placement.coverage()).never_tested == 8

    respx.get(f"{BASE_URL}/placement/seeds").mock(
        return_value=httpx.Response(200, json={"data": [SEED]})
    )
    seeds = await aclient.placement.list_seeds()
    assert seeds[0].email == "seed@example.com"

    route = respx.put(f"{BASE_URL}/placement/seeds/{SENDER_ID}").mock(
        return_value=httpx.Response(200, json={"data": {**SEED, "seed": False}})
    )
    seed = await aclient.placement.set_seed(SENDER_ID, seed=False)
    assert seed.seed is False
    assert json.loads(_last(route).content) == {"seed": False}
