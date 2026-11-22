"""Fields and small routes that came with the store and segment pinning.

Segment pinning on Apollo and Salesforce import sources and forms, purchased
mailboxes, the full-check interval, the partner mailbox enablement list, the
agency card fee and the agency store overview.
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
CONN = "c0c0c0c0-1111-4222-8333-444455556666"
SRC = "5a5a5a5a-1111-4222-8333-444455556666"
SEG = "e1e1e1e1-1111-4222-8333-444455556666"
FORM = "f0f0f0f0-1111-4222-8333-444455556666"
MAILBOX = "a1a1a1a1-1111-4222-8333-444455556666"
AGENCY = "aaaaaaaa-1111-4222-8333-444455556666"
ORG = "bbbbbbbb-1111-4222-8333-444455556666"
DOMAIN = "dddddddd-1111-4222-8333-444455556666"

APOLLO_SOURCE: dict[str, Any] = {
    "id": SRC,
    "connection_id": CONN,
    "list_id": "L1",
    "list_name": "Founders",
    "category_ids": [],
    "segment_ids": [SEG],
    "verified_only": True,
    "recurring": False,
    "enabled": True,
}

SF_SOURCE: dict[str, Any] = {
    "id": SRC,
    "connection_id": CONN,
    "object": "Lead",
    "source_label": "Open leads",
    "category_ids": [],
    "segment_ids": [SEG],
    "recurring": True,
    "enabled": True,
}

FORM_BODY: dict[str, Any] = {
    "id": FORM,
    "name": "Demo request",
    "category_ids": [],
    "segment_ids": [SEG],
}

MAILBOX_BODY: dict[str, Any] = {
    "id": MAILBOX,
    "email": "sam@bought.example.com",
    "purchased": True,
    "purchase_cancelled_at": "2026-12-01T00:00:00Z",
}

SYNC_BODY: dict[str, Any] = {
    "state": None,
    "policy": {
        "backfill_days": 30,
        "skip_folders": [],
        "full_check_seconds": 900,
    },
    "skip_folders": [],
    "folders": [],
}

AGENCY_STORE: dict[str, Any] = {
    "enabled": True,
    "clients": [
        {
            "organization_id": ORG,
            "name": "Acme",
            "avatar_url": None,
            "domains": 3,
            "mailboxes_live": 9,
            "mailboxes_connected": 8,
            "monthly_spend_micros": 45_000_000,
            "renewals_30d": 1,
            "next_renewal": {
                "domain_id": DOMAIN,
                "domain": "acme-mail.com",
                "expires_at": "2026-12-10T00:00:00Z",
                "auto_renew": True,
            },
            "orders_open": 0,
            "attention": [{"kind": "connect_failed", "count": 1}],
        }
    ],
    "renewals": [
        {
            "organization_id": ORG,
            "organization_name": "Acme",
            "domain_id": DOMAIN,
            "domain": "acme-mail.com",
            "expires_at": "2026-12-10T00:00:00Z",
            "auto_renew": True,
            "renew_micros": 14_000_000,
        }
    ],
    "totals": {
        "domains": 3,
        "mailboxes_live": 9,
        "monthly_spend_micros": 45_000_000,
        "renewals_30d": 1,
        "attention": 1,
    },
}

TOPUP: dict[str, Any] = {
    "min_usd": 10,
    "max_usd": 5000,
    "presets_usd": [25, 50],
    "default_usd": 50,
    "fee_bps": 300,
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


def _mock() -> dict[str, respx.Route]:
    apollo = f"{BASE_URL}/integrations/apollo/{CONN}/import-sources"
    sf = f"{BASE_URL}/integrations/salesforce/{CONN}/import-sources"
    return {
        "apollo_create": respx.post(apollo).mock(
            return_value=httpx.Response(201, json=APOLLO_SOURCE)
        ),
        "apollo_update": respx.patch(f"{apollo}/{SRC}").mock(
            return_value=httpx.Response(200, json={**APOLLO_SOURCE, "segment_ids": []})
        ),
        "sf_create": respx.post(sf).mock(
            return_value=httpx.Response(201, json=SF_SOURCE)
        ),
        "sf_update": respx.patch(f"{sf}/{SRC}").mock(
            return_value=httpx.Response(200, json=SF_SOURCE)
        ),
        "form": respx.patch(f"{BASE_URL}/forms/{FORM}").mock(
            return_value=httpx.Response(200, json=FORM_BODY)
        ),
        "mailbox": respx.get(f"{BASE_URL}/emails/{MAILBOX}").mock(
            return_value=httpx.Response(200, json=MAILBOX_BODY)
        ),
        "sync": respx.get(f"{BASE_URL}/emails/{MAILBOX}/sync").mock(
            return_value=httpx.Response(200, json=SYNC_BODY)
        ),
        "partner": respx.get(f"{BASE_URL}/emails/partner").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "email_account_id": MAILBOX,
                            "enablement": "warmup_only",
                            "managed": True,
                        }
                    ]
                },
            )
        ),
        "agency_store": respx.get(f"{BASE_URL}/agency/{AGENCY}/store").mock(
            return_value=httpx.Response(200, json=AGENCY_STORE)
        ),
        "topup": respx.get(f"{BASE_URL}/agency/{AGENCY}/ai-balance").mock(
            return_value=httpx.Response(
                200, json={"balance_usd": 12.5, "top_up": TOPUP}
            )
        ),
    }


def _check_requests(routes: dict[str, respx.Route]) -> None:
    assert _body(routes["apollo_create"])["segment_ids"] == [SEG]
    assert _body(routes["apollo_update"]) == {"segment_ids": []}
    assert _body(routes["sf_create"])["segment_ids"] == [SEG]
    assert _body(routes["sf_update"]) == {"segment_ids": [SEG]}
    assert _body(routes["form"]) == {"segment_ids": [SEG]}


def _check_agency_store(overview: Any) -> None:
    assert overview.enabled is True
    client = overview.clients[0]
    assert client.organization_id == ORG
    assert client.mailboxes_connected == 8
    assert client.monthly_spend_micros == 45_000_000
    assert client.next_renewal.domain == "acme-mail.com"
    assert client.attention[0].kind == "connect_failed"
    assert not client.model_extra
    renewal = overview.renewals[0]
    assert renewal.organization_name == "Acme"
    assert renewal.renew_micros == 14_000_000
    assert overview.totals.attention == 1


@respx.mock
def test_store_fields_sync(client: Warmbly) -> None:
    routes = _mock()
    source = client.apollo.create_import_source(CONN, list_id="L1", segment_ids=[SEG])
    assert source.segment_ids == [SEG]
    updated = client.apollo.update_import_source(CONN, SRC, segment_ids=[])
    assert updated.segment_ids == []
    sf = client.salesforce.create_import_source(
        CONN,
        source_kind="list_view",
        source_id="00B1",
        object="Lead",
        source_label="Open leads",
        segment_ids=[SEG],
    )
    assert sf.segment_ids == [SEG]
    client.salesforce.update_import_source(CONN, SRC, segment_ids=[SEG])
    form = client.forms.update(FORM, segment_ids=[SEG])
    assert form.segment_ids == [SEG]

    mailbox = client.emails.retrieve(MAILBOX)
    assert mailbox.purchased is True
    assert mailbox.purchase_cancelled_at == "2026-12-01T00:00:00Z"
    sync = client.emails.sync(MAILBOX)
    assert sync.policy is not None
    assert sync.policy.full_check_seconds == 900

    enablement = list(client.emails.list_partner_mailboxes())
    assert enablement[0].email_account_id == MAILBOX
    assert enablement[0].enablement == "warmup_only"
    assert enablement[0].managed is True

    _check_agency_store(client.agency.store_overview(AGENCY))
    balance = client.agency.ai_balance(AGENCY)
    assert balance.top_up is not None
    assert balance.top_up.fee_bps == 300
    _check_requests(routes)


@pytest.mark.anyio
@respx.mock
async def test_store_fields_async(aclient: AsyncWarmbly) -> None:
    routes = _mock()
    source = await aclient.apollo.create_import_source(
        CONN, list_id="L1", segment_ids=[SEG]
    )
    assert source.segment_ids == [SEG]
    updated = await aclient.apollo.update_import_source(CONN, SRC, segment_ids=[])
    assert updated.segment_ids == []
    sf = await aclient.salesforce.create_import_source(
        CONN,
        source_kind="list_view",
        source_id="00B1",
        object="Lead",
        source_label="Open leads",
        segment_ids=[SEG],
    )
    assert sf.segment_ids == [SEG]
    await aclient.salesforce.update_import_source(CONN, SRC, segment_ids=[SEG])
    form = await aclient.forms.update(FORM, segment_ids=[SEG])
    assert form.segment_ids == [SEG]

    mailbox = await aclient.emails.retrieve(MAILBOX)
    assert mailbox.purchased is True
    sync = await aclient.emails.sync(MAILBOX)
    assert sync.policy is not None
    assert sync.policy.full_check_seconds == 900

    enablement = [m async for m in aclient.emails.list_partner_mailboxes()]
    assert enablement[0].managed is True

    _check_agency_store(await aclient.agency.store_overview(AGENCY))
    balance = await aclient.agency.ai_balance(AGENCY)
    assert balance.top_up is not None
    assert balance.top_up.fee_bps == 300
    _check_requests(routes)
