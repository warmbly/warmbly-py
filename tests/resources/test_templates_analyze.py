"""Tests for ``templates.analyze``, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

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


ANALYSIS: dict[str, Any] = {
    "score": 62,
    "verdict": "Likely to land in the inbox, with two risky phrases.",
    "findings": [
        {
            "severity": "high",
            "field": "subject",
            "text": "FREE MONEY",
            "line": 1,
            "excerpt": "FREE MONEY inside",
            "issue": "All-caps trigger words.",
            "suggestion": "Say what you offer in plain words.",
            "category": "trigger_word",
        }
    ],
    "suggested_subject": "A quick question about your bakery",
    "improvements": ["Add one clear ask."],
    "rules": {
        "score": 80,
        "issues": [
            {
                "severity": "warn",
                "code": "all_caps",
                "message": "Shouting in the subject.",
                "field": "subject",
                "spans": [
                    {
                        "field": "subject",
                        "text": "FREE MONEY",
                        "line": 1,
                        "excerpt": "FREE MONEY inside",
                    }
                ],
                "suggestion": "Use sentence case.",
            }
        ],
    },
    "judgment": {
        "reads_as": 0.7,
        "personalization": 0.2,
        "ask": "single",
        "spam_claim": 0.1,
        "confidence": 0.8,
        "model": "copy-judge-1",
        "input_tokens": 210,
    },
    "model": "claude-x",
    "tokens_used": 900,
    "credits_charged": 1.5,
    "credits_remaining": 98.5,
    "charged_usd": 0.015,
    "balance_usd": 0.985,
}


def _check(out: Any) -> None:
    assert out.score == 62
    assert out.verdict.startswith("Likely")
    assert out.findings[0].severity == "high"
    assert out.findings[0].field == "subject"
    assert out.findings[0].line == 1
    assert out.findings[0].category == "trigger_word"
    assert out.suggested_subject == "A quick question about your bakery"
    assert out.improvements == ["Add one clear ask."]
    assert out.rules.score == 80
    assert out.rules.issues[0].code == "all_caps"
    assert out.rules.issues[0].spans[0].excerpt == "FREE MONEY inside"
    assert out.judgment.reads_as == 0.7
    assert out.judgment.ask == "single"
    assert out.judgment.input_tokens == 210
    assert out.tokens_used == 900
    assert out.credits_charged == 1.5
    assert out.credits_remaining == 98.5
    assert out.charged_usd == 0.015
    assert out.balance_usd == 0.985


@respx.mock
def test_analyze_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    out = client.templates.analyze(
        subject="FREE MONEY inside",
        body_html="<p>Hi</p>",
        body_plain="Hi",
        options={"idempotency_key": "analyze-1"},
    )
    request = route.calls.last.request
    assert request.headers["Idempotency-Key"] == "analyze-1"
    assert json.loads(request.content) == {
        "subject": "FREE MONEY inside",
        "body_html": "<p>Hi</p>",
        "body_plain": "Hi",
    }
    _check(out)

    # Without an LLM the findings are empty and no judgment may be present.
    respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(
            200, json={"score": 90, "verdict": "Reads fine.", "findings": []}
        )
    )
    bare = client.templates.analyze(body_plain="Hi")
    assert bare.findings == []
    assert bare.judgment is None
    assert json.loads(route.calls.last.request.content) == {"body_plain": "Hi"}


@respx.mock
@pytest.mark.anyio
async def test_analyze_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    out = await aclient.templates.analyze(subject="FREE MONEY inside")
    assert json.loads(route.calls.last.request.content) == {
        "subject": "FREE MONEY inside"
    }
    assert route.calls.last.request.headers["Idempotency-Key"]
    _check(out)
