"""Tests for the ``agency`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.agency import (
    AgencyAIBalance,
    AgencyAITransfer,
    AgencyBrand,
    AgencyClient,
    AgencyDetail,
    AgencyInboxMessage,
    AgencyList,
    AgencyOverview,
    AgencyPlanList,
    AgencyStaff,
    AgencyUsage,
)
from warmbly.resources.migrations import Migration

BASE_URL = "https://api.warmbly.com/v1"
AGENCY = "7d0c2b8e-1f4a-4c55-9d1e-3a2b6f8c9e01"
ORG = "1b2c3d4e-5f60-4718-8a9b-0c1d2e3f4a5b"
MIG = "9e8d7c6b-5a49-4382-9170-6f5e4d3c2b1a"
MSG = "44444444-5555-4666-8777-888899990000"


@pytest.fixture
def client() -> Iterator[Warmbly]:
    c = Warmbly(api_key="wmagency_test", base_url=BASE_URL, max_retries=0)
    yield c
    c.close()


@pytest.fixture
async def aclient() -> AsyncIterator[AsyncWarmbly]:
    async with AsyncWarmbly(
        api_key="wmagency_test", base_url=BASE_URL, max_retries=0
    ) as c:
        yield c


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


def _params(route: respx.Route) -> dict[str, str]:
    return dict(_last(route).url.params)


def _cpage(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {"data": data, "pagination": {"next_cursor": None, "has_more": False}}


# -- realistic payloads, built from the Go structs ---------------------------

PLAN = {
    "id": "00000000-0000-0000-0000-0000000000a1",
    "name": "Agency",
    "max_contacts": 0,
    "daily_emails": 0,
    "ai_generation": True,
    "account_limit": 0,
    "price": 499.0,
    "price_yearly": 4990.0,
    "discounted_price": 0,
    "duration": "monthly",
    "savings": 0,
    "public": True,
    "dedicated_workers": 0,
    "monthly_allowance_usd": 0,
    "monthly_credits": 0,
    "referral_reward_percent": 100,
    "monthly_send_pool": 250000,
    "agency_ai_allowance_usd": 50.0,
    "updated_at": "2026-10-01T00:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
}

AGENCY_JSON = {
    "id": AGENCY,
    "name": "Northwind Growth",
    "owner_user_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    "plan_id": PLAN["id"],
    "status": "active",
    "current_period_start": "2026-11-01T00:00:00Z",
    "current_period_end": "2026-12-01T00:00:00Z",
    "cancel_at_period_end": False,
    "created_at": "2026-01-10T09:00:00Z",
    "updated_at": "2026-11-01T00:00:00Z",
    "plan": PLAN,
    "role": "owner",
    "client_count": 12,
    "has_billing": True,
    "granted": {"plan_id": PLAN["id"], "until": "2027-01-01T00:00:00Z"},
    "billing_interval": "month",
}

STAFF = {
    "data": [
        {
            "agency_id": AGENCY,
            "user_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "role": "owner",
            "created_at": "2026-01-10T09:00:00Z",
            "email": "owner@northwind.example",
            "first_name": "Ada",
            "last_name": "Lane",
        }
    ],
    "invitations": [
        {
            "id": "cccccccc-dddd-4eee-8fff-000000000000",
            "agency_id": AGENCY,
            "email": "new@northwind.example",
            "role": "member",
            "invited_by": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "expires_at": "2026-11-29T00:00:00Z",
            "created_at": "2026-11-15T00:00:00Z",
        }
    ],
}

CLIENT_JSON = {
    "organization_id": ORG,
    "agency_id": AGENCY,
    "monthly_send_limit": 20000,
    "monthly_ai_limit_usd": 15.5,
    "added_at": "2026-02-01T00:00:00Z",
    "added_by": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    "name": "Acme Co",
    "slug": "acme-co",
    "avatar_url": "https://cdn.example/acme.png",
    "owner_user_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
}

USAGE = {
    "unlimited": False,
    "period_start": "2026-11-01T00:00:00Z",
    "period_end": "2026-12-01T00:00:00Z",
    "days_left": 16,
    "pool_size": 250000,
    "topups": 50000,
    "total": 300000,
    "used": 120000,
    "remaining": 180000,
    "projected": 240000,
    "clients": [
        {
            "organization_id": ORG,
            "name": "Acme Co",
            "used": 9000,
            "monthly_send_limit": 20000,
        }
    ],
    "topup_sends": 50000,
    "topup_price_cents": 8500,
}

AI_BALANCE = {
    "unmetered": False,
    "period_start": "2026-11-01T00:00:00Z",
    "period_end": "2026-12-01T00:00:00Z",
    "allowance_usd": 50.0,
    "allowance_left_usd": 20.0,
    "purchased_usd": 100.0,
    "bought_this_period_usd": 25.0,
    "spent_usd": 30.0,
    "moved_usd": 10.0,
    "balance_usd": 120.0,
    "clients": [
        {
            "organization_id": ORG,
            "name": "Acme Co",
            "spent_usd": 4.25,
            "moved_usd": 10.0,
            "monthly_ai_limit_usd": 15.5,
        }
    ],
    "top_up": {
        "min_usd": 10,
        "max_usd": 5000,
        "presets_usd": [25, 50, 100],
        "default_usd": 50,
    },
}

OVERVIEW = {
    "generated_at": "2026-11-15T12:00:00Z",
    "usage": USAGE,
    "totals": {
        "clients": 12,
        "sent_today": 3400,
        "replies_waiting": 7,
        "positive_replies_7d": 22,
        "active_campaigns": 31,
        "mailboxes": 140,
        "mailbox_problems": 3,
    },
    "attention": [
        {
            "kind": "bounce_spike",
            "severity": "high",
            "organization_id": ORG,
            "client_name": "Acme Co",
            "count": 140,
            "rate": 0.071,
        }
    ],
    "clients": [
        {
            "organization_id": ORG,
            "name": "Acme Co",
            "avatar_url": "https://cdn.example/acme.png",
            "access": "full",
            "manage_mailboxes": True,
            "pool_used": 9000,
            "monthly_send_limit": 20000,
            "campaigns": {
                "active": 3,
                "paused_by_limits": 1,
                "paused_by_billing": 0,
                "sent_today": 400,
                "sent_7d": 2800,
                "bounced_7d": 140,
                "bounce_rate_7d": 0.05,
                "positive_replies_7d": 4,
            },
            "inbox": {"replies_waiting": 2},
            "mailboxes": {
                "total": 12,
                "disconnected": 1,
                "erroring": 0,
                "watch": 1,
                "throttled": 0,
                "quarantined": 0,
                "blocked": 0,
            },
            "advisor": {"critical": 0, "high": 1, "medium": 2, "low": 5},
        }
    ],
}

MAILBOX = {
    "id": "55555555-6666-4777-8888-999900001111",
    "organization_id": ORG,
    "client": "Acme Co",
    "email": "sam@acme.example",
    "name": "Sam",
    "provider": "google",
    "status": "connected",
    "erroring": False,
    "warmup": True,
    "warmup_state": "watch",
    "vendor": "zapmail",
    "campaign_limit": 40,
    "created_at": "2026-03-01T00:00:00Z",
}

INBOX_THREAD = {
    "organization_id": ORG,
    "id": MSG,
    "email_id": MAILBOX["id"],
    "thread_id": "thread-abc",
    "from_addr": ["lead@prospect.example"],
    "to_addr": ["sam@acme.example"],
    "subject": "Re: quick question",
    "snippet": "Sounds good, let's talk Tuesday",
    "internal_date": "2026-11-15T10:00:00Z",
    "seen": False,
    "message_count": 3,
    "has_unread": True,
}

THREAD_MESSAGE = {
    "id": MSG,
    "email_id": MAILBOX["id"],
    "thread_id": "thread-abc",
    "from_addr": ["lead@prospect.example"],
    "to_addr": ["sam@acme.example"],
    "subject": "Re: quick question",
    "snippet": "Sounds good",
    "internal_date": "2026-11-15T10:00:00Z",
    "seen": True,
    "message_count": 0,
    "has_unread": False,
    "labels": [],
}

MESSAGE = {
    "id": MSG,
    "gmail_id": "18c2",
    "uid": 0,
    "email_id": MAILBOX["id"],
    "folder": "inbox",
    "parent_id": "",
    "thread_id": "thread-abc",
    "flags": ["\\Seen"],
    "bcc": [],
    "cc": [],
    "date": "2026-11-15T10:00:00Z",
    "from": ["lead@prospect.example"],
    "in_reply_to": ["<orig@acme.example>"],
    "message_id": "<reply@prospect.example>",
    "ReplyTo": [],
    "to": ["sam@acme.example"],
    "subject": "Re: quick question",
    "size": 2048,
    "internal_date": "2026-11-15T10:00:00Z",
    "mod_seq": 0,
    "body_plain": "Sounds good, let's talk Tuesday.",
    "body_html": "<p>Sounds good, let's talk Tuesday.</p>",
    "body_truncated": False,
}

BRAND = {
    "brand": {
        "display_name": "Northwind",
        "logo_url": "https://cdn.example/nw.png",
        "accent_color": "#0055ff",
        "website_url": "https://northwind.example",
        "hide_powered_by": True,
        "updated_at": "2026-10-01T00:00:00Z",
        "updated_by": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    },
    "full_white_label": True,
    "can_manage": False,
    "portal_domain": {
        "forms_domain": "app.northwind.example",
        "forms_domain_verified": True,
        "forms_domain_verified_at": "2026-10-02T00:00:00Z",
        "cname_target": "portal.warmbly.com",
        "txt_name": "_warmbly.app.northwind.example",
        "txt_value": "warmbly-verify=abc",
        "status": "verified",
        "message": "Verified.",
        "forms_host_unresolvable": False,
        "edge_records": [
            {
                "purpose": "certificate",
                "type": "TXT",
                "name": "_acme-challenge.app.northwind.example",
                "value": "xyz",
                "ok": True,
            }
        ],
    },
    "portal_base_url": "https://app.northwind.example",
    "powered_by": {"name": "Warmbly", "url": "https://warmbly.com"},
    "portal_sign_in": "portal",
    "icon_url": "https://cdn.example/icon.png",
    "sign_in_image_url": "",
    "theme": {"font": "serif", "corners": "round", "appearance": "dark"},
}

PROVIDER = {
    "id": "smartlead",
    "label": "Smartlead",
    "fields": [
        {"key": "api_key", "label": "API key", "secret": True},
    ],
    "key_help": "Settings > API",
    "key_url": "https://app.smartlead.ai/settings",
    "kinds": ["mailboxes", "campaigns", "leads", "blocklist"],
    "workspaces": True,
    "multi_key": False,
    "mailbox_secrets": True,
    "notes": ["LinkedIn steps do not carry over."],
}

MIGRATION = {
    "id": MIG,
    "agency_id": AGENCY,
    "created_by_user_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    "provider": "smartlead",
    "label": "Smartlead import",
    "status": "running",
    "accounts": [{"name": "Ada", "email": "ada@northwind.example", "plan": "Pro"}],
    "inventory": [
        {
            "workspace": {"id": "ws-1", "name": "Acme", "key": 0},
            "inventory": {
                "mailboxes": 4,
                "campaigns": 2,
                "leads": 900,
                "blocklist": 12,
                "campaign_summaries": [
                    {
                        "id": "c-1",
                        "name": "Q4 push",
                        "status": "active",
                        "steps": 3,
                        "leads": 450,
                    }
                ],
            },
        }
    ],
    "options": {
        "kinds": ["blocklist", "campaigns", "leads"],
        "campaign_ids": ["c-1"],
        "in_flight": "restart",
        "skip_finished": True,
        "warmup": False,
    },
    "targets": [
        {
            "id": "66666666-7777-4888-9999-000011112222",
            "migration_id": MIG,
            "workspace": {"id": "ws-1", "name": "Acme"},
            "organization_id": ORG,
            "organization_name": "Acme Co",
            "status": "running",
            "phase": "leads",
            "counts": {"campaigns_created": 2, "leads_enrolled": 300},
            "followup": {
                "reconnect": [{"email": "sam@acme.example", "kind": "google"}],
                "notes": ["LinkedIn steps skipped"],
                "campaigns": [
                    {
                        "source_id": "c-1",
                        "campaign_id": "77777777-8888-4999-8000-111122223333",
                        "name": "Q4 push",
                        "missing_senders": ["sam@acme.example"],
                    }
                ],
            },
            "updated_at": "2026-11-15T11:00:00Z",
        }
    ],
    "credentials_held": True,
    "started_at": "2026-11-15T10:30:00Z",
    "created_at": "2026-11-15T10:00:00Z",
    "updated_at": "2026-11-15T11:00:00Z",
}


def _check_agency_list(result: AgencyList) -> None:
    assert result.billing_enabled is True
    agency = result.data[0]
    assert agency.id == AGENCY
    assert agency.role == "owner"
    assert agency.client_count == 12
    assert agency.plan is not None
    assert agency.plan.monthly_send_pool == 250000
    assert agency.granted is not None
    assert agency.granted.until == "2027-01-01T00:00:00Z"


def _check_plans(result: AgencyPlanList) -> None:
    assert result.billing_enabled is True
    assert result.data[0].agency_ai_allowance_usd == 50.0
    assert result.data[0].price_yearly == 4990.0


def _check_detail(result: AgencyDetail) -> None:
    assert result.agency is not None
    assert result.agency.billing_interval == "month"
    assert result.billing_enabled is False


def _check_staff(result: AgencyStaff) -> None:
    assert result.data[0].email == "owner@northwind.example"
    assert result.invitations[0].role == "member"


def _check_client(result: AgencyClient) -> None:
    assert result.organization_id == ORG
    assert result.monthly_send_limit == 20000
    assert result.monthly_ai_limit_usd == 15.5
    assert result.slug == "acme-co"


def _check_usage(result: AgencyUsage) -> None:
    assert result.topup_price_cents == 8500
    assert result.clients[0].used == 9000
    assert result.remaining == 180000


def _check_ai_balance(result: AgencyAIBalance) -> None:
    assert result.bought_this_period_usd == 25.0
    assert result.clients[0].monthly_ai_limit_usd == 15.5
    assert result.top_up is not None
    assert result.top_up.presets_usd == [25, 50, 100]


def _check_transfer(result: AgencyAITransfer) -> None:
    assert result.amount_usd == 12.5
    assert result.agency_balance_usd == 107.5
    assert result.workspace_balance_usd == 20.0


def _check_overview(result: AgencyOverview) -> None:
    assert result.usage is not None and result.usage.total == 300000
    assert result.totals is not None and result.totals.mailbox_problems == 3
    assert result.attention[0].kind == "bounce_spike"
    row = result.clients[0]
    assert row.access == "full"
    assert row.campaigns is not None and row.campaigns.sent_7d == 2800
    assert row.inbox is not None and row.inbox.replies_waiting == 2
    assert row.mailboxes is not None and row.mailboxes.disconnected == 1
    assert row.advisor is not None and row.advisor.high == 1


def _check_message(result: AgencyInboxMessage) -> None:
    assert result.folder == "inbox"
    assert result.email_id == MAILBOX["id"]
    assert result.from_ == ["lead@prospect.example"]
    assert result.body_plain == "Sounds good, let's talk Tuesday."


def _check_brand(result: AgencyBrand) -> None:
    assert result.brand is not None and result.brand.display_name == "Northwind"
    assert result.portal_domain is not None
    assert result.portal_domain.status == "verified"
    assert result.portal_domain.edge_records[0].type == "TXT"
    assert result.powered_by is not None and result.powered_by.name == "Warmbly"
    assert result.theme is not None and result.theme.font == "serif"
    assert result.portal_sign_in == "portal"


def _check_migration(result: Migration) -> None:
    assert result.id == MIG
    assert result.agency_id == AGENCY
    assert result.accounts[0].email == "ada@northwind.example"
    ws = result.inventory[0]
    assert ws.workspace is not None and ws.workspace.id == "ws-1"
    assert ws.inventory is not None
    assert ws.inventory.campaign_summaries[0].name == "Q4 push"
    assert result.options is not None and result.options.in_flight == "restart"
    target = result.targets[0]
    assert target.organization_name == "Acme Co"
    assert target.counts is not None and target.counts.leads_enrolled == 300
    assert target.followup is not None
    assert target.followup.reconnect[0].kind == "google"
    assert target.followup.campaigns[0].missing_senders == ["sam@acme.example"]
    assert result.credentials_held is True


START_TARGETS = [
    {"workspace_id": "ws-1", "key": 0, "organization_id": ORG},
    {"workspace_id": "ws-2", "key": 0, "create_name": "Beta LLC"},
]
START_BODY = {
    "options": {
        "kinds": ["campaigns", "leads"],
        "in_flight": "restart",
        "campaign_ids": ["c-1"],
        "skip_finished": True,
        "warmup": False,
    },
    "targets": START_TARGETS,
}


# -- agency, plans, staff ----------------------------------------------------


@respx.mock
def test_list_and_plans_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/agency").mock(
        return_value=httpx.Response(
            200, json={"data": [AGENCY_JSON], "billing_enabled": True}
        )
    )
    _check_agency_list(client.agency.list())
    assert _last(route).method == "GET"
    assert _last(route).headers["authorization"] == "Bearer wmagency_test"

    plans = respx.get(f"{BASE_URL}/agency/plans").mock(
        return_value=httpx.Response(200, json={"data": [PLAN], "billing_enabled": True})
    )
    _check_plans(client.agency.list_plans())
    assert _last(plans).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_list_and_plans_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/agency").mock(
        return_value=httpx.Response(
            200, json={"data": [AGENCY_JSON], "billing_enabled": True}
        )
    )
    _check_agency_list(await aclient.agency.list())
    assert _last(route).method == "GET"

    plans = respx.get(f"{BASE_URL}/agency/plans").mock(
        return_value=httpx.Response(200, json={"data": [PLAN], "billing_enabled": True})
    )
    _check_plans(await aclient.agency.list_plans())
    assert _last(plans).method == "GET"


@respx.mock
def test_retrieve_and_members_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/agency/{AGENCY}").mock(
        return_value=httpx.Response(
            200, json={"agency": AGENCY_JSON, "billing_enabled": False}
        )
    )
    _check_detail(client.agency.retrieve(AGENCY))
    assert _last(route).method == "GET"

    members = respx.get(f"{BASE_URL}/agency/{AGENCY}/members").mock(
        return_value=httpx.Response(200, json=STAFF)
    )
    _check_staff(client.agency.list_members(AGENCY))
    assert _last(members).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_retrieve_and_members_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/agency/{AGENCY}").mock(
        return_value=httpx.Response(
            200, json={"agency": AGENCY_JSON, "billing_enabled": False}
        )
    )
    _check_detail(await aclient.agency.retrieve(AGENCY))
    assert _last(route).method == "GET"

    members = respx.get(f"{BASE_URL}/agency/{AGENCY}/members").mock(
        return_value=httpx.Response(200, json=STAFF)
    )
    _check_staff(await aclient.agency.list_members(AGENCY))
    assert _last(members).method == "GET"


# -- clients -----------------------------------------------------------------


@respx.mock
def test_clients_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/agency/{AGENCY}/clients").mock(
        return_value=httpx.Response(200, json={"data": [CLIENT_JSON]})
    )
    page = client.agency.list_clients(AGENCY)
    assert not page.has_next_page()
    _check_client(page.data[0])
    assert _last(listing).method == "GET"

    create = respx.post(f"{BASE_URL}/agency/{AGENCY}/clients").mock(
        return_value=httpx.Response(201, json=CLIENT_JSON)
    )
    _check_client(client.agency.create_client(AGENCY, name="Acme Co"))
    assert _body(create) == {"name": "Acme Co"}
    assert "idempotency-key" in _last(create).headers
    client.agency.create_client(AGENCY, name="Acme Co", timezone="Europe/Paris")
    assert _body(create) == {"name": "Acme Co", "timezone": "Europe/Paris"}

    attach = respx.post(f"{BASE_URL}/agency/{AGENCY}/clients/attach").mock(
        return_value=httpx.Response(201, json=CLIENT_JSON)
    )
    _check_client(client.agency.attach_client(AGENCY, organization_id=ORG))
    assert _last(attach).method == "POST"
    assert _body(attach) == {"organization_id": ORG}

    update = respx.patch(f"{BASE_URL}/agency/{AGENCY}/clients/{ORG}").mock(
        return_value=httpx.Response(200, json=CLIENT_JSON)
    )
    _check_client(
        client.agency.update_client(
            AGENCY, ORG, monthly_send_limit=20000, monthly_ai_limit_usd=15.5
        )
    )
    assert _body(update) == {"monthly_send_limit": 20000, "monthly_ai_limit_usd": 15.5}
    client.agency.update_client(AGENCY, ORG, monthly_send_limit=None)
    assert _body(update) == {"monthly_send_limit": None}

    detach = respx.delete(f"{BASE_URL}/agency/{AGENCY}/clients/{ORG}").mock(
        return_value=httpx.Response(204)
    )
    client.agency.detach_client(AGENCY, ORG)
    assert _last(detach).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_clients_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/agency/{AGENCY}/clients").mock(
        return_value=httpx.Response(200, json={"data": [CLIENT_JSON]})
    )
    items = [c async for c in aclient.agency.list_clients(AGENCY)]
    _check_client(items[0])
    assert _last(listing).method == "GET"

    create = respx.post(f"{BASE_URL}/agency/{AGENCY}/clients").mock(
        return_value=httpx.Response(201, json=CLIENT_JSON)
    )
    _check_client(
        await aclient.agency.create_client(
            AGENCY, name="Acme Co", timezone="Europe/Paris"
        )
    )
    assert _body(create) == {"name": "Acme Co", "timezone": "Europe/Paris"}
    assert "idempotency-key" in _last(create).headers

    attach = respx.post(f"{BASE_URL}/agency/{AGENCY}/clients/attach").mock(
        return_value=httpx.Response(201, json=CLIENT_JSON)
    )
    _check_client(await aclient.agency.attach_client(AGENCY, organization_id=ORG))
    assert _body(attach) == {"organization_id": ORG}

    update = respx.patch(f"{BASE_URL}/agency/{AGENCY}/clients/{ORG}").mock(
        return_value=httpx.Response(200, json=CLIENT_JSON)
    )
    _check_client(
        await aclient.agency.update_client(AGENCY, ORG, monthly_ai_limit_usd=None)
    )
    assert _last(update).method == "PATCH"
    assert _body(update) == {"monthly_ai_limit_usd": None}

    detach = respx.delete(f"{BASE_URL}/agency/{AGENCY}/clients/{ORG}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.agency.detach_client(AGENCY, ORG)
    assert _last(detach).method == "DELETE"


# -- usage and AI balance ----------------------------------------------------

TRANSFER = {
    "amount_usd": 12.5,
    "agency_balance_usd": 107.5,
    "workspace_balance_usd": 20.0,
}


@respx.mock
def test_usage_and_ai_sync(client: Warmbly) -> None:
    usage = respx.get(f"{BASE_URL}/agency/{AGENCY}/usage").mock(
        return_value=httpx.Response(200, json=USAGE)
    )
    _check_usage(client.agency.usage(AGENCY))
    assert _last(usage).method == "GET"

    balance = respx.get(f"{BASE_URL}/agency/{AGENCY}/ai-balance").mock(
        return_value=httpx.Response(200, json=AI_BALANCE)
    )
    _check_ai_balance(client.agency.ai_balance(AGENCY))
    assert _last(balance).method == "GET"

    transfer = respx.post(f"{BASE_URL}/agency/{AGENCY}/clients/{ORG}/ai-balance").mock(
        return_value=httpx.Response(200, json=TRANSFER)
    )
    _check_transfer(
        client.agency.transfer_ai_balance(
            AGENCY, ORG, amount_usd=12.5, options={"idempotency_key": "move-1"}
        )
    )
    assert _body(transfer) == {"amount_usd": 12.5}
    assert _last(transfer).headers["idempotency-key"] == "move-1"


@pytest.mark.anyio
@respx.mock
async def test_usage_and_ai_async(aclient: AsyncWarmbly) -> None:
    usage = respx.get(f"{BASE_URL}/agency/{AGENCY}/usage").mock(
        return_value=httpx.Response(200, json=USAGE)
    )
    _check_usage(await aclient.agency.usage(AGENCY))
    assert _last(usage).method == "GET"

    balance = respx.get(f"{BASE_URL}/agency/{AGENCY}/ai-balance").mock(
        return_value=httpx.Response(200, json=AI_BALANCE)
    )
    _check_ai_balance(await aclient.agency.ai_balance(AGENCY))
    assert _last(balance).method == "GET"

    transfer = respx.post(f"{BASE_URL}/agency/{AGENCY}/clients/{ORG}/ai-balance").mock(
        return_value=httpx.Response(200, json=TRANSFER)
    )
    _check_transfer(
        await aclient.agency.transfer_ai_balance(AGENCY, ORG, amount_usd=12.5)
    )
    assert _body(transfer) == {"amount_usd": 12.5}
    assert "idempotency-key" in _last(transfer).headers


# -- overview, mailboxes, inbox, brand --------------------------------------


@respx.mock
def test_overview_mailboxes_brand_sync(client: Warmbly) -> None:
    overview = respx.get(f"{BASE_URL}/agency/{AGENCY}/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    _check_overview(client.agency.overview(AGENCY))
    assert _last(overview).method == "GET"

    mailboxes = respx.get(f"{BASE_URL}/agency/{AGENCY}/mailboxes").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [MAILBOX],
                    "pagination": {"next_cursor": "cur-2", "has_more": True},
                },
            ),
            httpx.Response(200, json=_cpage([{**MAILBOX, "id": "mb-2"}])),
        ]
    )
    items = list(
        client.agency.list_mailboxes(
            AGENCY, client=[ORG, "org-2"], q="acme", attention=True, limit=50
        )
    )
    assert [m.id for m in items] == [MAILBOX["id"], "mb-2"]
    assert items[0].warmup_state == "watch"
    assert items[0].client == "Acme Co"
    first = mailboxes.calls[0].request
    assert dict(first.url.params) == {
        "client": f"{ORG},org-2",
        "q": "acme",
        "attention": "true",
        "limit": "50",
    }
    assert _params(mailboxes)["cursor"] == "cur-2"
    assert mailboxes.call_count == 2

    brand = respx.get(f"{BASE_URL}/agency/{AGENCY}/brand").mock(
        return_value=httpx.Response(200, json=BRAND)
    )
    _check_brand(client.agency.brand(AGENCY))
    assert _last(brand).method == "GET"


@pytest.mark.anyio
@respx.mock
async def test_overview_mailboxes_brand_async(aclient: AsyncWarmbly) -> None:
    overview = respx.get(f"{BASE_URL}/agency/{AGENCY}/overview").mock(
        return_value=httpx.Response(200, json=OVERVIEW)
    )
    _check_overview(await aclient.agency.overview(AGENCY))
    assert _last(overview).method == "GET"

    mailboxes = respx.get(f"{BASE_URL}/agency/{AGENCY}/mailboxes").mock(
        return_value=httpx.Response(200, json=_cpage([MAILBOX]))
    )
    page = await aclient.agency.list_mailboxes(
        AGENCY, client=[ORG], attention=False, cursor="cur-1"
    )
    assert page.data[0].vendor == "zapmail"
    assert _params(mailboxes) == {"client": ORG, "cursor": "cur-1"}

    brand = respx.get(f"{BASE_URL}/agency/{AGENCY}/brand").mock(
        return_value=httpx.Response(200, json=BRAND)
    )
    _check_brand(await aclient.agency.brand(AGENCY))
    assert _last(brand).method == "GET"


@respx.mock
def test_inbox_sync(client: Warmbly) -> None:
    inbox = respx.get(f"{BASE_URL}/agency/{AGENCY}/inbox").mock(
        return_value=httpx.Response(200, json=_cpage([INBOX_THREAD]))
    )
    threads = list(
        client.agency.list_inbox(
            AGENCY,
            client=[ORG],
            unread=True,
            needs_reply=True,
            positive=True,
            q="tuesday",
            limit=25,
            cursor="c0",
        )
    )
    assert threads[0].organization_id == ORG
    assert threads[0].has_unread is True
    assert threads[0].from_addr == ["lead@prospect.example"]
    assert _params(inbox) == {
        "client": ORG,
        "unread": "true",
        "needs_reply": "true",
        "positive": "true",
        "q": "tuesday",
        "limit": "25",
        "cursor": "c0",
    }

    thread = respx.get(f"{BASE_URL}/agency/{AGENCY}/inbox/thread").mock(
        return_value=httpx.Response(200, json=_cpage([THREAD_MESSAGE]))
    )
    messages = list(
        client.agency.retrieve_inbox_thread(
            AGENCY, organization_id=ORG, thread_id="thread-abc"
        )
    )
    assert messages[0].email_id == MAILBOX["id"]
    assert messages[0].thread_id == "thread-abc"
    assert _params(thread) == {"organization_id": ORG, "thread_id": "thread-abc"}

    message = respx.get(f"{BASE_URL}/agency/{AGENCY}/inbox/messages/{MSG}").mock(
        return_value=httpx.Response(200, json=MESSAGE)
    )
    _check_message(
        client.agency.retrieve_inbox_message(AGENCY, MSG, organization_id=ORG)
    )
    assert _params(message) == {"organization_id": ORG}


@pytest.mark.anyio
@respx.mock
async def test_inbox_async(aclient: AsyncWarmbly) -> None:
    inbox = respx.get(f"{BASE_URL}/agency/{AGENCY}/inbox").mock(
        return_value=httpx.Response(200, json=_cpage([INBOX_THREAD]))
    )
    threads = [t async for t in aclient.agency.list_inbox(AGENCY, unread=True)]
    assert threads[0].subject == "Re: quick question"
    assert _params(inbox) == {"unread": "true"}

    thread = respx.get(f"{BASE_URL}/agency/{AGENCY}/inbox/thread").mock(
        return_value=httpx.Response(200, json=_cpage([THREAD_MESSAGE]))
    )
    page = await aclient.agency.retrieve_inbox_thread(
        AGENCY, organization_id=ORG, thread_id="thread-abc", cursor="c1"
    )
    assert page.data[0].id == MSG
    assert _params(thread) == {
        "organization_id": ORG,
        "thread_id": "thread-abc",
        "cursor": "c1",
    }

    message = respx.get(f"{BASE_URL}/agency/{AGENCY}/inbox/messages/{MSG}").mock(
        return_value=httpx.Response(200, json=MESSAGE)
    )
    _check_message(
        await aclient.agency.retrieve_inbox_message(AGENCY, MSG, organization_id=ORG)
    )
    assert _params(message) == {"organization_id": ORG}


# -- migrations --------------------------------------------------------------


@respx.mock
def test_migrations_sync(client: Warmbly) -> None:
    base = f"{BASE_URL}/agency/{AGENCY}/migrations"
    providers = respx.get(f"{base}/providers").mock(
        return_value=httpx.Response(200, json={"data": [PROVIDER]})
    )
    provider = client.agency.list_migration_providers(AGENCY).data[0]
    assert provider.id == "smartlead"
    assert provider.fields[0].secret is True
    assert provider.kinds == ["mailboxes", "campaigns", "leads", "blocklist"]
    assert _last(providers).method == "GET"

    listing = respx.get(base).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [MIGRATION],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    page = client.agency.list_migrations(AGENCY, limit=10, cursor="m0")
    assert page.total == 1
    _check_migration(page.data[0])
    assert _params(listing) == {"limit": "10", "cursor": "m0"}

    create = respx.post(base).mock(
        return_value=httpx.Response(201, json={**MIGRATION, "status": "scanning"})
    )
    created = client.agency.create_migration(
        AGENCY,
        provider="smartlead",
        credentials=[{"api_key": "sl_secret"}],
        label="Smartlead import",
    )
    assert created.status == "scanning"
    assert _body(create) == {
        "provider": "smartlead",
        "label": "Smartlead import",
        "credentials": [{"api_key": "sl_secret"}],
    }
    assert "idempotency-key" in _last(create).headers

    retrieve = respx.get(f"{base}/{MIG}").mock(
        return_value=httpx.Response(200, json=MIGRATION)
    )
    _check_migration(client.agency.retrieve_migration(AGENCY, MIG))
    assert _last(retrieve).method == "GET"

    start = respx.post(f"{base}/{MIG}/start").mock(
        return_value=httpx.Response(200, json=MIGRATION)
    )
    _check_migration(
        client.agency.start_migration(
            AGENCY,
            MIG,
            kinds=["campaigns", "leads"],
            targets=START_TARGETS,
            in_flight="restart",
            campaign_ids=["c-1"],
            skip_finished=True,
            warmup=False,
        )
    )
    assert _body(start) == START_BODY
    client.agency.start_migration(AGENCY, MIG, kinds=["blocklist"])
    assert _body(start) == {"options": {"kinds": ["blocklist"]}}

    cancel = respx.post(f"{base}/{MIG}/cancel").mock(
        return_value=httpx.Response(200, json={**MIGRATION, "status": "canceled"})
    )
    assert client.agency.cancel_migration(AGENCY, MIG).status == "canceled"
    assert _last(cancel).method == "POST"

    link = respx.post(f"{base}/{MIG}/link-senders").mock(
        return_value=httpx.Response(200, json=MIGRATION)
    )
    _check_migration(client.agency.link_migration_senders(AGENCY, MIG))
    assert _last(link).method == "POST"

    dismiss = respx.delete(f"{base}/{MIG}").mock(return_value=httpx.Response(204))
    client.agency.dismiss_migration(AGENCY, MIG)
    assert _last(dismiss).method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_migrations_async(aclient: AsyncWarmbly) -> None:
    base = f"{BASE_URL}/agency/{AGENCY}/migrations"
    respx.get(f"{base}/providers").mock(
        return_value=httpx.Response(200, json={"data": [PROVIDER]})
    )
    providers = [p async for p in aclient.agency.list_migration_providers(AGENCY)]
    assert providers[0].mailbox_secrets is True

    listing = respx.get(base).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [MIGRATION],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    items = [m async for m in aclient.agency.list_migrations(AGENCY)]
    _check_migration(items[0])
    assert _params(listing) == {}

    create = respx.post(base).mock(return_value=httpx.Response(201, json=MIGRATION))
    _check_migration(
        await aclient.agency.create_migration(
            AGENCY, provider="smartlead", credentials=[{"api_key": "sl_secret"}]
        )
    )
    assert _body(create) == {
        "provider": "smartlead",
        "credentials": [{"api_key": "sl_secret"}],
    }

    respx.get(f"{base}/{MIG}").mock(return_value=httpx.Response(200, json=MIGRATION))
    _check_migration(await aclient.agency.retrieve_migration(AGENCY, MIG))

    start = respx.post(f"{base}/{MIG}/start").mock(
        return_value=httpx.Response(200, json=MIGRATION)
    )
    _check_migration(
        await aclient.agency.start_migration(
            AGENCY,
            MIG,
            kinds=["campaigns", "leads"],
            targets=START_TARGETS,
            in_flight="restart",
            campaign_ids=["c-1"],
            skip_finished=True,
            warmup=False,
        )
    )
    assert _body(start) == START_BODY
    assert "idempotency-key" in _last(start).headers

    cancel = respx.post(f"{base}/{MIG}/cancel").mock(
        return_value=httpx.Response(200, json={**MIGRATION, "status": "canceled"})
    )
    assert (await aclient.agency.cancel_migration(AGENCY, MIG)).status == "canceled"
    assert _last(cancel).method == "POST"

    link = respx.post(f"{base}/{MIG}/link-senders").mock(
        return_value=httpx.Response(200, json=MIGRATION)
    )
    _check_migration(await aclient.agency.link_migration_senders(AGENCY, MIG))
    assert _last(link).method == "POST"

    dismiss = respx.delete(f"{base}/{MIG}").mock(return_value=httpx.Response(204))
    await aclient.agency.dismiss_migration(AGENCY, MIG)
    assert _last(dismiss).method == "DELETE"
