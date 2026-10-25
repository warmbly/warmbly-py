"""Tests for the template, form, segment and outreach changes of the server sync."""

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


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------
RULES: dict[str, Any] = {
    "score": 72,
    "issues": [
        {
            "severity": "high",
            "code": "trigger_word",
            "message": "Spammy phrase",
            "field": "subject",
            "spans": [
                {"field": "subject", "text": "FREE", "line": 1, "excerpt": "FREE offer"}
            ],
            "suggestion": "Drop it",
        }
    ],
}

ANALYSIS: dict[str, Any] = {
    "score": 64,
    "verdict": "Likely to be filtered",
    "findings": [
        {
            "severity": "warn",
            "field": "body",
            "text": "act now",
            "line": 3,
            "excerpt": "Please act now",
            "issue": "Urgency",
            "suggestion": "Say when it matters",
            "category": "tone",
        }
    ],
    "suggested_subject": "Quick question",
    "improvements": ["Shorten it"],
    "rules": RULES,
    "judgment": {
        "reads_as": 0.7,
        "personalization": 0.4,
        "ask": "one",
        "spam_claim": 0.1,
        "confidence": 0.8,
        "model": "judge-1",
        "input_tokens": 120,
    },
    "model": "gpt-x",
    "tokens_used": 900,
    "credits_remaining": 41,
    "credits_charged": 2,
}


def _check_rules(rules: Any) -> None:
    assert rules.score == 72
    issue = rules.issues[0]
    assert (issue.severity, issue.code, issue.field) == (
        "high",
        "trigger_word",
        "subject",
    )
    assert issue.suggestion == "Drop it"
    span = issue.spans[0]
    assert (span.field, span.text, span.line, span.excerpt) == (
        "subject",
        "FREE",
        1,
        "FREE offer",
    )


def _check_analysis(analysis: Any) -> None:
    assert analysis.score == 64
    assert analysis.verdict == "Likely to be filtered"
    finding = analysis.findings[0]
    assert (finding.severity, finding.field, finding.text) == (
        "warn",
        "body",
        "act now",
    )
    assert (finding.line, finding.issue, finding.category) == (3, "Urgency", "tone")
    assert finding.excerpt == "Please act now"
    assert finding.suggestion == "Say when it matters"
    assert analysis.suggested_subject == "Quick question"
    assert list(analysis.improvements) == ["Shorten it"]
    _check_rules(analysis.rules)
    assert analysis.judgment.reads_as == 0.7
    assert analysis.judgment.ask == "one"
    assert analysis.judgment.input_tokens == 120
    assert analysis.model == "gpt-x"
    assert analysis.tokens_used == 900
    assert analysis.credits_remaining == 41
    assert analysis.credits_charged == 2


@respx.mock
def test_template_score_and_analyze_sync(client: Warmbly) -> None:
    score = respx.post(f"{BASE_URL}/templates/score").mock(
        return_value=httpx.Response(200, json=RULES)
    )
    _check_rules(client.templates.score(subject="FREE offer"))
    assert _last(score).method == "POST"

    analyze = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    result = client.templates.analyze(
        subject="FREE offer", body_html="<p>x</p>", body_plain="x"
    )
    request = _last(analyze)
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "subject": "FREE offer",
        "body_html": "<p>x</p>",
        "body_plain": "x",
    }
    assert request.headers.get("idempotency-key")
    _check_analysis(result)


@pytest.mark.anyio
@respx.mock
async def test_template_score_and_analyze_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/templates/score").mock(
        return_value=httpx.Response(200, json=RULES)
    )
    _check_rules(await aclient.templates.score(subject="x"))
    analyze = respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(200, json=ANALYSIS)
    )
    _check_analysis(await aclient.templates.analyze(body_plain="x"))
    assert json.loads(_last(analyze).content) == {"body_plain": "x"}


@respx.mock
def test_template_analyze_without_a_language_model(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/templates/analyze").mock(
        return_value=httpx.Response(
            200,
            json={
                "score": 80,
                "verdict": "Reads as personal",
                "findings": [],
                "rules": RULES,
                "judgment": ANALYSIS["judgment"],
                "model": "judge-1",
                "tokens_used": 120,
                "credits_remaining": 0,
                "credits_charged": 0,
            },
        )
    )
    result = client.templates.analyze(subject="s")
    assert result.findings == []
    assert result.suggested_subject is None
    assert result.credits_charged == 0
    assert result.judgment.confidence == 0.8


# ---------------------------------------------------------------------------
# forms
# ---------------------------------------------------------------------------
FORM: dict[str, Any] = {
    "id": "f_1",
    "name": "Contact",
    "redirect_url": "https://other.test/thanks",
    "redirect_url_active": False,
    "captcha_enabled": True,
    "triage_enabled": True,
}


@respx.mock
def test_form_triage_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(
            200,
            json={
                "base_url": "https://forms.test",
                "captcha_available": True,
                "triage_available": False,
            },
        )
    )
    assert client.forms.config().triage_available is False

    update = respx.patch(f"{BASE_URL}/forms/f_1").mock(
        return_value=httpx.Response(200, json=FORM)
    )
    form = client.forms.update("f_1", triage_enabled=True)
    assert json.loads(_last(update).content) == {"triage_enabled": True}
    assert form.triage_enabled is True
    assert form.redirect_url_active is False

    respx.get(f"{BASE_URL}/forms/f_1/submissions").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "s_1",
                        "form_id": "f_1",
                        "triage": "junk",
                        "triage_confidence": 0.93,
                        "data": {"email": "a@b.test"},
                    }
                ],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    submission = next(iter(client.forms.list_submissions("f_1")))
    assert submission.triage == "junk"
    assert submission.triage_confidence == 0.93


@pytest.mark.anyio
@respx.mock
async def test_form_triage_async(aclient: AsyncWarmbly) -> None:
    update = respx.patch(f"{BASE_URL}/forms/f_1").mock(
        return_value=httpx.Response(200, json=FORM)
    )
    form = await aclient.forms.update("f_1", triage_enabled=False)
    assert json.loads(_last(update).content) == {"triage_enabled": False}
    assert form.redirect_url_active is False


# ---------------------------------------------------------------------------
# segments
# ---------------------------------------------------------------------------
@respx.mock
def test_segment_members_selection_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 40})
    )
    result = client.segments.set_members(
        "seg_1",
        mode="exclude",
        all=True,
        filters={"query": "acme"},
        exclude=["c_9"],
    )
    assert result.updated == 40
    assert json.loads(_last(route).content) == {
        "mode": "exclude",
        "all": True,
        "filters": {"query": "acme"},
        "exclude": ["c_9"],
    }
    client.segments.set_members("seg_1", mode="include", contacts=["c_1"])
    assert json.loads(_last(route).content) == {"mode": "include", "contacts": ["c_1"]}


@pytest.mark.anyio
@respx.mock
async def test_segment_members_selection_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 2})
    )
    await aclient.segments.set_members("seg_1", mode="auto", all=True, exclude=[])
    assert json.loads(_last(route).content) == {
        "mode": "auto",
        "all": True,
        "exclude": [],
    }
    await aclient.segments.set_members("seg_1", mode="include", contacts=["c"])
    assert json.loads(_last(route).content) == {"mode": "include", "contacts": ["c"]}


@respx.mock
def test_segment_field_option_labels(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "field": "esp_provider",
                        "label": "Email provider family",
                        "group": "Contact",
                        "kind": "enum",
                        "options": ["gmail", "outlook", "other"],
                        "option_labels": {"gmail": "Google", "outlook": "Microsoft"},
                    }
                ],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    field = next(iter(client.segments.fields()))
    assert field.option_labels == {"gmail": "Google", "outlook": "Microsoft"}
    assert list(field.options) == ["gmail", "outlook", "other"]


# ---------------------------------------------------------------------------
# outreach
# ---------------------------------------------------------------------------
@respx.mock
def test_outreach_inbox_tagging(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/outreach/settings").mock(
        return_value=httpx.Response(
            200,
            json={
                "reply_intent": {
                    "hold_on_out_of_office": True,
                    "out_of_office_hold_days": 7,
                    "crm_task_intents": ["positive", "question"],
                },
                "inbox_tagging": {
                    "hold_on_not_now": True,
                    "not_now_hold_days": 30,
                    "stop_on_declined": True,
                    "languages": ["de"],
                    "questions": [],
                },
            },
        )
    )
    settings = client.outreach.settings()
    assert settings.inbox_tagging["not_now_hold_days"] == 30
    assert settings.inbox_tagging["languages"] == ["de"]
    assert settings.reply_intent["out_of_office_hold_days"] == 7


@respx.mock
def test_plan_price_yearly(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/plans").mock(
        return_value=httpx.Response(
            200,
            json={
                "plans": [
                    {"id": "pro", "price": 49.0, "price_yearly": 490.0},
                    {"id": "starter", "price": 19.0},
                ]
            },
        )
    )
    plans = list(client.plans.list())
    assert plans[0].price_yearly == 490.0
    assert plans[1].price_yearly is None
