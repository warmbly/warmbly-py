"""Campaign review: the readiness report, the approval hold and per-lead copy."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.campaigns import (
    CampaignReviewChange,
    CampaignReviewLead,
    CampaignReviewSummary,
    CampaignReviewWriteResult,
    LeadEmails,
    LeadStepOverride,
)

BASE_URL = "https://api.warmbly.com/v1"
CID = "6b1f7f0e-2a0c-4c8e-9a51-1d2b3c4d5e6f"
LEAD = "0f3c2d1e-4b5a-4c6d-8e7f-9a0b1c2d3e4f"
LEAD2 = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
STEP = "7c6b5a49-3827-4615-a0b9-c8d7e6f5a4b3"

SUMMARY: dict[str, Any] = {
    "campaign_id": CID,
    "review_leads": True,
    "counts": {
        "total": 120,
        "waiting": 80,
        "ready": 10,
        "held": 5,
        "started": 25,
        "personalized": 3,
    },
    "missing": [{"field": "Company", "leads": 12}],
    "undeliverable": 4,
    "unsubscribed": 2,
    "ai": {
        "step_id": STEP,
        "blocks": 2,
        "written": 60,
        "pending": 35,
        "estimated_cost_usd": 0.42,
        "auto": False,
    },
    "template_errors": [
        {"step_id": STEP, "position": 2, "message": "unknown merge tag {{title}}"}
    ],
}

REVIEW_LEAD: dict[str, Any] = {
    "contact_id": LEAD,
    "email": "ada@example.com",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "company": "",
    "status": "waiting",
    "hold": {"since": "2026-11-20T10:00:00Z", "source": "review"},
    "personalized": 1,
    "missing": ["Company"],
    "added_at": "2026-11-20T09:59:00Z",
}

CHANGE: dict[str, Any] = {
    "campaign_id": CID,
    "review_leads": True,
    "held": 0,
    "released": 2,
}

WRITE: dict[str, Any] = {
    "written": 20,
    "failed": 1,
    "remaining": 14,
    "stopped": "insufficient_credits",
    "next": "eyJlIjoiYUBiLmNvbSJ9",
}

LEAD_EMAILS: dict[str, Any] = {
    "campaign_id": CID,
    "lead": REVIEW_LEAD,
    "from": {"name": "Sam Sender", "email": "sam@outreach.example.com"},
    "steps": [
        {
            "step_id": STEP,
            "position": 1,
            "name": "Intro",
            "subject": "Hi Ada",
            "body_html": "<p>Hi Ada</p>",
            "body_plain": "Hi Ada",
            "source": {
                "subject": "Hi {{first_name}}",
                "body_html": "<p>Hi {{first_name}}</p>",
                "body_plain": "Hi {{first_name}}",
            },
            "threaded": False,
            "personalized": True,
            "edited_at": "2026-11-21T08:00:00Z",
            "step_changed": True,
            "variant_id": "9e8d7c6b-5a49-4382-a716-f5e4d3c2b1a0",
            "ai_blocks": [{"id": "opener", "name": "Opener", "written": True}],
            "missing": ["Company"],
            "errors": ["unknown merge tag {{title}}"],
            "sent": True,
            "sent_at": "2026-11-21T09:00:00Z",
        }
    ],
}

OVERRIDE: dict[str, Any] = {
    "campaign_id": CID,
    "contact_id": LEAD,
    "step_id": STEP,
    "subject": "Hi Ada, a note",
    "body_html": "<p>Custom</p>",
    "body_plain": "Custom",
    "edited_by": "5d4c3b2a-1908-4f7e-8d6c-5b4a39281706",
    "updated_at": "2026-11-21T08:00:00Z",
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


def _body(route: respx.Route) -> Any:
    return json.loads(route.calls.last.request.content)


def _mock_all() -> dict[str, respx.Route]:
    base = f"{BASE_URL}/campaigns/{CID}"
    lead = f"{base}/leads/{LEAD}/emails"
    return {
        "summary": respx.get(f"{base}/review").mock(
            return_value=httpx.Response(200, json=SUMMARY)
        ),
        "set": respx.put(f"{base}/review").mock(
            return_value=httpx.Response(200, json={**CHANGE, "review_leads": False})
        ),
        "list": respx.get(f"{base}/review/leads").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": [REVIEW_LEAD],
                        "pagination": {"next_cursor": "c2", "has_more": True},
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "data": [{**REVIEW_LEAD, "contact_id": LEAD2}],
                        "pagination": {"next_cursor": None, "has_more": False},
                    },
                ),
            ]
        ),
        "approve": respx.post(f"{base}/review/approve").mock(
            return_value=httpx.Response(200, json=CHANGE)
        ),
        "reopen": respx.post(f"{base}/review/reopen").mock(
            return_value=httpx.Response(200, json={**CHANGE, "held": 1, "released": 0})
        ),
        "write": respx.post(f"{base}/review/write").mock(
            return_value=httpx.Response(200, json=WRITE)
        ),
        "emails": respx.get(lead).mock(
            return_value=httpx.Response(200, json=LEAD_EMAILS)
        ),
        "put": respx.put(f"{lead}/{STEP}").mock(
            return_value=httpx.Response(200, json=OVERRIDE)
        ),
        "delete": respx.delete(f"{lead}/{STEP}").mock(return_value=httpx.Response(204)),
        "write_one": respx.post(f"{lead}/{STEP}/write").mock(
            return_value=httpx.Response(200, json=LEAD_EMAILS)
        ),
    }


def _check_summary(summary: CampaignReviewSummary) -> None:
    assert summary.campaign_id == CID
    assert summary.review_leads is True
    assert summary.counts is not None
    assert summary.counts.waiting == 80
    assert summary.counts.personalized == 3
    assert summary.missing[0].field == "Company"
    assert summary.missing[0].leads == 12
    assert summary.undeliverable == 4
    assert summary.unsubscribed == 2
    assert summary.ai is not None
    assert summary.ai.step_id == STEP
    assert summary.ai.pending == 35
    assert summary.ai.estimated_cost_usd == 0.42
    assert summary.ai.auto is False
    assert summary.template_errors[0].position == 2
    assert summary.template_errors[0].message.startswith("unknown")  # type: ignore[union-attr]
    assert not summary.model_extra


def _check_lead(lead: CampaignReviewLead, contact_id: str = LEAD) -> None:
    assert lead.contact_id == contact_id
    assert lead.email == "ada@example.com"
    assert lead.status == "waiting"
    assert lead.hold is not None
    assert lead.hold.source == "review"
    assert lead.personalized == 1
    assert lead.missing == ["Company"]
    assert lead.added_at == "2026-11-20T09:59:00Z"
    assert not lead.model_extra


def _check_change(change: CampaignReviewChange, released: int = 2) -> None:
    assert change.campaign_id == CID
    assert change.released == released
    assert change.held is not None


def _check_write(result: CampaignReviewWriteResult) -> None:
    assert result.written == 20
    assert result.failed == 1
    assert result.remaining == 14
    assert result.stopped == "insufficient_credits"
    assert result.next == "eyJlIjoiYUBiLmNvbSJ9"


def _check_emails(emails: LeadEmails) -> None:
    assert emails.campaign_id == CID
    assert emails.lead is not None
    assert emails.lead.contact_id == LEAD
    assert emails.from_ is not None
    assert emails.from_.email == "sam@outreach.example.com"
    step = emails.steps[0]
    assert step.step_id == STEP
    assert step.subject == "Hi Ada"
    assert step.source is not None
    assert step.source.subject == "Hi {{first_name}}"
    assert step.personalized is True
    assert step.step_changed is True
    assert step.variant_id is not None
    assert step.ai_blocks[0].id == "opener"
    assert step.ai_blocks[0].written is True
    assert step.errors == ["unknown merge tag {{title}}"]
    assert step.sent is True
    assert step.sent_at == "2026-11-21T09:00:00Z"
    assert not step.model_extra
    assert not emails.model_extra


def _check_override(override: LeadStepOverride) -> None:
    assert override.contact_id == LEAD
    assert override.step_id == STEP
    assert override.subject == "Hi Ada, a note"
    assert override.body_plain == "Custom"
    assert override.edited_by is not None
    assert override.updated_at is not None


def _check_requests(routes: dict[str, respx.Route]) -> None:
    assert _body(routes["set"]) == {"enabled": False}
    first, second = routes["list"].calls
    assert dict(first.request.url.params) == {
        "status": "waiting",
        "missing": "Company",
        "q": "ada",
        "limit": "1",
    }
    assert second.request.url.params["cursor"] == "c2"
    assert _body(routes["approve"]) == {"contact_ids": [LEAD, LEAD2]}
    assert _body(routes["reopen"]) == {"contact_ids": [LEAD]}
    assert _body(routes["write"]) == {
        "step_id": STEP,
        "contact_ids": [LEAD],
        "waiting_only": True,
        "after": "c1",
    }
    assert _body(routes["put"]) == {
        "subject": "Hi Ada, a note",
        "body_html": "<p>Custom</p>",
        "body_plain": "Custom",
    }
    assert routes["put"].calls.last.request.method == "PUT"
    assert routes["delete"].calls.last.request.method == "DELETE"
    assert _body(routes["write_one"]) == {"rewrite": True}
    for name in ("approve", "reopen", "write", "write_one"):
        assert "idempotency-key" in routes[name].calls.last.request.headers


@respx.mock
def test_campaign_review_sync(client: Warmbly) -> None:
    routes = _mock_all()
    c = client.campaigns

    _check_summary(c.review(CID))
    change = c.set_review(CID, enabled=False)
    assert change.review_leads is False
    leads = list(
        c.list_review_leads(CID, status="waiting", missing="Company", q="ada", limit=1)
    )
    assert [lead.contact_id for lead in leads] == [LEAD, LEAD2]
    _check_lead(leads[0])
    _check_change(c.approve_review_leads(CID, contact_ids=[LEAD, LEAD2]))
    _check_change(c.reopen_review_leads(CID, contact_ids=[LEAD]), released=0)
    _check_write(
        c.write_review_ai(
            CID, step_id=STEP, contact_ids=[LEAD], waiting_only=True, after="c1"
        )
    )
    _check_emails(c.lead_emails(CID, LEAD))
    _check_override(
        c.personalize_lead_email(
            CID,
            LEAD,
            STEP,
            subject="Hi Ada, a note",
            body_html="<p>Custom</p>",
            body_plain="Custom",
        )
    )
    assert c.reset_lead_email(CID, LEAD, STEP) is None
    _check_emails(c.write_lead_email_ai(CID, LEAD, STEP, rewrite=True))
    _check_requests(routes)


@pytest.mark.anyio
@respx.mock
async def test_campaign_review_async(aclient: AsyncWarmbly) -> None:
    routes = _mock_all()
    c = aclient.campaigns

    _check_summary(await c.review(CID))
    change = await c.set_review(CID, enabled=False)
    assert change.review_leads is False
    leads = [
        lead
        async for lead in c.list_review_leads(
            CID, status="waiting", missing="Company", q="ada", limit=1
        )
    ]
    assert [lead.contact_id for lead in leads] == [LEAD, LEAD2]
    _check_lead(leads[0])
    _check_change(await c.approve_review_leads(CID, contact_ids=[LEAD, LEAD2]))
    _check_change(await c.reopen_review_leads(CID, contact_ids=[LEAD]), released=0)
    _check_write(
        await c.write_review_ai(
            CID, step_id=STEP, contact_ids=[LEAD], waiting_only=True, after="c1"
        )
    )
    _check_emails(await c.lead_emails(CID, LEAD))
    _check_override(
        await c.personalize_lead_email(
            CID,
            LEAD,
            STEP,
            subject="Hi Ada, a note",
            body_html="<p>Custom</p>",
            body_plain="Custom",
        )
    )
    assert await c.reset_lead_email(CID, LEAD, STEP) is None
    _check_emails(await c.write_lead_email_ai(CID, LEAD, STEP, rewrite=True))
    _check_requests(routes)


@respx.mock
def test_review_defaults_send_minimal_bodies_sync(client: Warmbly) -> None:
    base = f"{BASE_URL}/campaigns/{CID}"
    approve = respx.post(f"{base}/review/approve").mock(
        return_value=httpx.Response(200, json=CHANGE)
    )
    write = respx.post(f"{base}/review/write").mock(
        return_value=httpx.Response(
            200, json={"written": 0, "failed": 0, "remaining": 0}
        )
    )
    one = respx.post(f"{base}/leads/{LEAD}/emails/{STEP}/write").mock(
        return_value=httpx.Response(200, json=LEAD_EMAILS)
    )
    put = respx.put(f"{base}/leads/{LEAD}/emails/{STEP}").mock(
        return_value=httpx.Response(200, json=OVERRIDE)
    )
    client.campaigns.approve_review_leads(CID, select_all=True)
    assert _body(approve) == {"all": True}
    result = client.campaigns.write_review_ai(CID)
    assert _body(write) == {}
    assert result.stopped is None
    client.campaigns.write_lead_email_ai(CID, LEAD, STEP)
    assert one.calls.last.request.content == b""
    client.campaigns.personalize_lead_email(
        CID, LEAD, STEP, subject="s", body_html="<p>b</p>"
    )
    assert _body(put) == {"subject": "s", "body_html": "<p>b</p>"}


@pytest.mark.anyio
@respx.mock
async def test_review_defaults_send_minimal_bodies_async(
    aclient: AsyncWarmbly,
) -> None:
    base = f"{BASE_URL}/campaigns/{CID}"
    approve = respx.post(f"{base}/review/approve").mock(
        return_value=httpx.Response(200, json=CHANGE)
    )
    one = respx.post(f"{base}/leads/{LEAD}/emails/{STEP}/write").mock(
        return_value=httpx.Response(200, json=LEAD_EMAILS)
    )
    await aclient.campaigns.approve_review_leads(CID, select_all=True)
    assert _body(approve) == {"all": True}
    await aclient.campaigns.write_lead_email_ai(CID, LEAD, STEP)
    assert one.calls.last.request.content == b""


@respx.mock
def test_campaign_reads_review_leads(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/campaigns/{CID}").mock(
        return_value=httpx.Response(
            200, json={"id": CID, "name": "Reviewed", "review_leads": True}
        )
    )
    campaign = client.campaigns.retrieve(CID)
    assert campaign.review_leads is True
    assert "review_leads" not in (campaign.model_extra or {})
