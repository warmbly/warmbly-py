"""Placement observation metrics and received-header evidence, sync and async."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.placement import PlacementTestDetail

BASE_URL = "https://api.warmbly.com/v1"
TEST_ID = "11111111-1111-1111-1111-111111111111"

METRIC = {
    "version": "observed-v2",
    "population": "seed_panel",
    "denominator_kind": "classified_observed_receipts",
    "unit": "fraction",
    "source": "mailbox_observation",
    "classification_policy": "first_folder_v2_with_legacy_classifications",
    "numerator": 6,
    "denominator": 8,
    "unresolved": 2,
    "window_basis": "placement_test_classification_window",
    "missingness_basis": "pending_missing_and_unclassified_copies",
    "value": 0.75,
    "wilson_95_independence_interval": {"lower": 0.4, "upper": 0.9},
}

DETAIL: dict[str, Any] = {
    "id": TEST_ID,
    "status": "completed",
    "summary": {
        "total": 10,
        "inbox": 6,
        "promotions": 1,
        "spam": 1,
        "missing": 1,
        "unknown": 1,
        "archive": 2,
        "custom": 3,
        "observed_receipts": 14,
        "classified_receipts": 8,
        "unresolved": 2,
        "primary_metric": METRIC,
        "non_spam_metric": {**METRIC, "numerator": 7, "value": 0.875},
    },
    "results": [
        {
            "seed": "a***@gmail.com",
            "folder": "missing",
            "first_folder": "spam",
            "observed_at": "2026-10-01T10:00:00Z",
            "late_observation": True,
            "evidence": {
                "version": "received-v1",
                "source": "mailbox",
                "trust": "unverified_headers",
                "observed_at": "2026-10-01T10:00:00Z",
                "spf": "unknown",
                "dkim": "pass",
                "dmarc": "unknown",
                "alignment": "pass",
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
                    "verifier": "go-msgauth/dkim-v0.7.0",
                    "observed_at": "2026-10-01T10:00:00Z",
                },
            },
        },
        {"seed": "b***@outlook.com", "folder": "archive", "evidence": None},
    ],
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


def _check(detail: PlacementTestDetail) -> None:
    summary = detail.summary
    assert summary is not None
    assert (summary.unknown, summary.archive, summary.custom) == (1, 2, 3)
    assert summary.observed_receipts == 14
    assert summary.classified_receipts == 8
    assert summary.unresolved == 2
    assert summary.primary_metric is not None
    assert summary.primary_metric.value == 0.75
    assert summary.primary_metric.numerator == 6
    assert summary.primary_metric.denominator_kind == "classified_observed_receipts"
    assert summary.primary_metric.classification_policy.startswith("first_folder")
    interval = summary.primary_metric.wilson_95_independence_interval
    assert interval is not None
    assert (interval.lower, interval.upper) == (0.4, 0.9)
    assert summary.non_spam_metric is not None
    assert summary.non_spam_metric.numerator == 7

    late, archived = detail.results
    assert late.first_folder == "spam"
    assert late.late_observation is True
    assert late.observed_at == "2026-10-01T10:00:00Z"
    assert late.evidence is not None
    assert late.evidence.trust == "unverified_headers"
    assert late.evidence.envelope_domain_claim == "bounce.example.com"
    assert late.evidence.signing_domain_claim == "example.com"
    assert late.evidence.selector_claim == "s1"
    assert late.evidence.authentication_results_present is True
    assert late.evidence.one_click_headers_present is True
    assert late.evidence.one_click_signing_claim is False
    assert late.evidence.dkim_verification is not None
    assert late.evidence.dkim_verification.signing_domain == "example.com"
    assert late.evidence.dkim_verification.verifier == "go-msgauth/dkim-v0.7.0"
    assert archived.folder == "archive"
    assert archived.evidence is None
    assert archived.first_folder is None


@respx.mock
def test_placement_evidence_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(200, json={"data": DETAIL})
    )
    _check(client.placement.get_test(TEST_ID))


@respx.mock
@pytest.mark.anyio
async def test_placement_evidence_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/placement/tests/{TEST_ID}").mock(
        return_value=httpx.Response(200, json={"data": DETAIL})
    )
    _check(await aclient.placement.get_test(TEST_ID))
