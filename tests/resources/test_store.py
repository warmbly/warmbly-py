"""Tests for the ``store`` resource (domains and mailboxes), sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly._exceptions import ConflictError
from warmbly.resources.store import (
    StoreConsentLink,
    StoreDNSCheck,
    StoreDNSRecord,
    StoreDomain,
    StoreDomainSearch,
    StoreMailbox,
    StoreOrder,
    StorePhoto,
    StoreQuote,
    StoreRegistrant,
    StoreSignIn,
    StoreStatus,
    StoreTransferOut,
)

BASE_URL = "https://api.warmbly.com/v1"
DID = "5b0e1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d"
MID = "6c1f2d3e-4f5a-4b6c-9d7e-8f9a0b1c2d3e"
OID = "7d2a3e4f-5a6b-4c7d-8e8f-9a0b1c2d3e4f"
QID = "8e3b4f5a-6b7c-4d8e-9f9a-0b1c2d3e4f5a"
RECID = "9f4c5a6b-7c8d-4e9f-8a0b-1c2d3e4f5a6b"
PID = "0a5d6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c"


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


# -- payloads, shaped like internal/app/store/types.go ------------------------


def _registrant() -> dict[str, Any]:
    return {
        "first_name": "Ana",
        "last_name": "Diaz",
        "organization": "Acme",
        "email": "ana@acme.test",
        "phone": "+1.4155550100",
        "address1": "1 Main St",
        "address2": "",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "country": "US",
    }


def _status() -> dict[str, Any]:
    return {
        "enabled": True,
        "configured": True,
        "locked": False,
        "can_configure": False,
        "disconnected": {"mailboxes": 0, "domains": 0},
        "metered": True,
        "currency": "usd",
        "mailbox_monthly_micros": 3_500_000,
        "domain_markup": "0.15",
        "limits": {
            "mailboxes_per_domain_max": 5,
            "mailboxes_per_domain_recommended": 3,
        },
        "providers": ["google", "microsoft"],
        "balance": {
            "balance_micros": 12_000_000,
            "card": {"brand": "visa", "last4": "4242"},
        },
        "plan_active": True,
        "registrant": _registrant(),
        "registrant_prefill": None,
        "stripe_publishable_key": "pk_test_x",
        "min_card_charge_micros": 10_000_000,
        "billing_day": 7,
        "next_bundle": {
            "charge_on": "2026-12-07T00:00:00Z",
            "mailboxes": 3,
            "amount_micros": 10_500_000,
        },
        "default_forwarding_url": "https://acme.test",
        "photos": True,
    }


def _record(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": RECID,
        "type": "MX",
        "name": "@",
        "content": "smtp.google.com",
        "ttl": 3600,
        "priority": 1,
        "managed": True,
        "purpose": "mail",
    }
    data.update(overrides)
    return data


def _domain(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": DID,
        "name": "acme-mail.com",
        "status": "active",
        "source": "purchased",
        "provider": "google",
        "renewable": True,
        "expires_at": "2027-11-20T00:00:00Z",
        "auto_renew": True,
        "renew_micros": 14_000_000,
        "forwarding_url": "https://acme.test",
        "forwarding_status": "active",
        "mail_auth": {"mx": "ok", "spf": "ok", "dkim": "ok", "dmarc": "ok"},
        "mailbox_count": 3,
        "nameservers": ["ns1.example.net", "ns2.example.net"],
        "connection": {
            "method": "nameservers",
            "status": "active",
            "expires_at": None,
            "checked_at": "2026-11-20T10:00:00Z",
            "current_nameservers": ["ns1.example.net"],
        },
        "dns_conflicts": [
            {"record_id": RECID, "type": "MX", "name": "@", "content": "mx.old.test"}
        ],
        "owner_verification": {
            "status": "pending",
            "email": "ana@acme.test",
            "deadline": "2026-12-05T00:00:00Z",
        },
        "transfer": {
            "status": "pending",
            "requested_at": "2026-11-21T00:00:00Z",
            "auto_approve_at": "2026-11-26T00:00:00Z",
        },
        "tracking_host": "go.acme-mail.com",
        "created_at": "2026-11-20T09:00:00Z",
    }
    data.update(overrides)
    return data


def _mailbox(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": MID,
        "email": "ana@acme-mail.com",
        "domain_id": DID,
        "provider": "google",
        "status": "active",
        "first_name": "Ana",
        "last_name": "Diaz",
        "is_admin": True,
        "paused": False,
        "monthly_micros": 3_500_000,
        "paid_through": "2026-12-20T00:00:00Z",
        "cancels_at": None,
        "cancelled_at": None,
        "email_account_id": "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e",
        "connect_state": "connected",
        "action_required": "microsoft_consent",
        "action_reason": "not_admin",
        "photo": "set",
        "created_at": "2026-11-20T09:00:00Z",
    }
    data.update(overrides)
    return data


def _quote() -> dict[str, Any]:
    return {
        "id": QID,
        "expires_at": "2026-11-22T10:15:00Z",
        "lines": [
            {
                "type": "domain",
                "domain": "acme-mail.com",
                "years": 1,
                "amount_micros": 14_000_000,
                "renew_micros": 14_000_000,
            },
            {
                "type": "mailboxes",
                "domain": "acme-mail.com",
                "provider": "google",
                "count": 1,
                "amount_micros": 3_500_000,
                "monthly_micros": 3_500_000,
                "admin_email": "ana@acme-mail.com",
                "nameservers_change": False,
            },
        ],
        "due_now_micros": 17_500_000,
        "recurring_monthly_micros": 3_500_000,
        "yearly_domain_renewal_micros": 14_000_000,
        "payment": {
            "balance_micros": 12_000_000,
            "from_balance_micros": 12_000_000,
            "card_charge_micros": 10_000_000,
            "balance_after_micros": 4_500_000,
            "card": {"brand": "visa", "last4": "4242"},
            "needs_payment_method": False,
            "auto_reload": {
                "enabled": True,
                "threshold_micros": 5_000_000,
                "amount_micros": 20_000_000,
                "store_managed": True,
            },
        },
    }


def _order(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": OID,
        "status": "processing",
        "created_at": "2026-11-22T10:00:00Z",
        "completed_at": None,
        "due_now_micros": 17_500_000,
        "charged_micros": 17_500_000,
        "refunded_micros": 0,
        "steps": [
            {"key": "register", "status": "done", "at": "2026-11-22T10:01:00Z"},
            {"key": "dns", "status": "running", "at": None},
        ],
        "domains": [_domain()],
        "mailboxes": [_mailbox()],
    }
    data.update(overrides)
    return data


def _page(items: list[dict[str, Any]], nxt: str | None = None) -> dict[str, Any]:
    return {"data": items, "pagination": {"next_cursor": nxt, "has_more": bool(nxt)}}


def _body(route: respx.Route) -> Any:
    return json.loads(route.calls.last.request.content)


def _assert_domain(d: StoreDomain) -> None:
    assert isinstance(d, StoreDomain)
    assert d.id == DID and d.name == "acme-mail.com"
    assert d.renewable is True and d.renew_micros == 14_000_000
    assert d.mail_auth is not None and d.mail_auth.dkim == "ok"
    assert d.connection is not None and d.connection.method == "nameservers"
    assert d.connection.current_nameservers == ["ns1.example.net"]
    assert d.dns_conflicts[0].record_id == RECID
    assert d.owner_verification is not None
    assert d.owner_verification.deadline == "2026-12-05T00:00:00Z"
    assert d.transfer is not None and d.transfer.auto_approve_at is not None
    assert d.tracking_host == "go.acme-mail.com"
    assert d.forwarding_status == "active" and d.mailbox_count == 3


def _assert_mailbox(m: StoreMailbox) -> None:
    assert isinstance(m, StoreMailbox)
    assert m.id == MID and m.domain_id == DID
    assert m.is_admin is True and m.paused is False
    assert m.monthly_micros == 3_500_000
    assert m.email_account_id is not None
    assert m.connect_state == "connected"
    assert m.action_required == "microsoft_consent"
    assert m.action_reason == "not_admin"
    assert m.photo == "set"


def _assert_order(o: StoreOrder) -> None:
    assert isinstance(o, StoreOrder)
    assert o.id == OID and o.status == "processing"
    assert o.charged_micros == 17_500_000 and o.refunded_micros == 0
    assert o.steps[0].key == "register" and o.steps[0].at is not None
    _assert_domain(o.domains[0])
    _assert_mailbox(o.mailboxes[0])


# -- status, search, registrant -------------------------------------------------


def _assert_status(s: StoreStatus) -> None:
    assert isinstance(s, StoreStatus)
    assert s.enabled is True and s.plan_active is True
    assert s.providers == ["google", "microsoft"]
    assert s.limits is not None and s.limits.mailboxes_per_domain_max == 5
    assert s.balance is not None and s.balance.card is not None
    assert s.balance.card.last4 == "4242"
    assert s.registrant is not None and s.registrant.country == "US"
    assert s.next_bundle is not None and s.next_bundle.mailboxes == 3
    assert s.disconnected is not None and s.disconnected.domains == 0
    assert s.billing_day == 7 and s.min_card_charge_micros == 10_000_000
    assert s.mailbox_monthly_micros == 3_500_000 and s.photos is True


@respx.mock
def test_status(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/store/status").mock(
        return_value=httpx.Response(200, json=_status())
    )
    _assert_status(client.store.status())
    assert route.called


@pytest.mark.anyio
@respx.mock
async def test_status_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/store/status").mock(
        return_value=httpx.Response(200, json=_status())
    )
    _assert_status(await aclient.store.status())


def _search() -> dict[str, Any]:
    return {
        "query": "acme",
        "data": [
            {
                "domain": "acme-mail.com",
                "display_name": "acme-mail.com",
                "tld": "com",
                "available": True,
                "exact": True,
                "years": 1,
                "price_micros": 14_000_000,
                "renew_micros": 14_000_000,
                "reason": None,
            }
        ],
    }


def _assert_search(r: StoreDomainSearch) -> None:
    assert isinstance(r, StoreDomainSearch)
    assert r.query == "acme"
    offer = r.data[0]
    assert offer.available is True and offer.exact is True
    assert offer.tld == "com" and offer.years == 1
    assert offer.price_micros == 14_000_000


@respx.mock
def test_search_domains(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/store/domains/search").mock(
        return_value=httpx.Response(200, json=_search())
    )
    _assert_search(
        client.store.search_domains(q="acme", tlds=["com", "io"], suggestions=False)
    )
    params = route.calls.last.request.url.params
    assert params["q"] == "acme"
    assert params.get_list("tlds") == ["com", "io"]
    assert params["suggestions"] == "false"


@pytest.mark.anyio
@respx.mock
async def test_search_domains_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/store/domains/search").mock(
        return_value=httpx.Response(200, json=_search())
    )
    _assert_search(await aclient.store.search_domains(q="acme"))
    params = route.calls.last.request.url.params
    assert params["q"] == "acme"
    assert "tlds" not in params and "suggestions" not in params


_REG_ARGS: dict[str, Any] = {
    "first_name": "Ana",
    "last_name": "Diaz",
    "email": "ana@acme.test",
    "phone": "+1.4155550100",
    "address1": "1 Main St",
    "city": "San Francisco",
    "postal_code": "94105",
    "country": "US",
}


def _assert_registrant(r: StoreRegistrant) -> None:
    assert isinstance(r, StoreRegistrant)
    assert r.phone == "+1.4155550100" and r.postal_code == "94105"
    assert r.organization == "Acme" and r.address1 == "1 Main St"


@respx.mock
def test_set_registrant(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/store/registrant").mock(
        return_value=httpx.Response(200, json=_registrant())
    )
    _assert_registrant(
        client.store.set_registrant(**_REG_ARGS, organization="Acme", state="CA")
    )
    assert _body(route) == {**_REG_ARGS, "organization": "Acme", "state": "CA"}


@pytest.mark.anyio
@respx.mock
async def test_set_registrant_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/store/registrant").mock(
        return_value=httpx.Response(200, json=_registrant())
    )
    _assert_registrant(await aclient.store.set_registrant(**_REG_ARGS, address2="#2"))
    assert _body(route) == {**_REG_ARGS, "address2": "#2"}


# -- quotes and orders -------------------------------------------------------------

_ITEMS: list[dict[str, Any]] = [
    {"type": "domain", "domain": "acme-mail.com", "years": 1},
    {
        "type": "mailboxes",
        "domain": "acme-mail.com",
        "provider": "google",
        "photo_id": PID,
        "mailboxes": [
            {
                "local_part": "ana",
                "first_name": "Ana",
                "last_name": "Diaz",
                "admin": True,
                "signature": {"html": "<p>Ana</p>", "plain": "Ana"},
            }
        ],
    },
]


def _assert_quote(q: StoreQuote) -> None:
    assert isinstance(q, StoreQuote)
    assert q.id == QID and q.due_now_micros == 17_500_000
    assert q.lines[1].admin_email == "ana@acme-mail.com"
    assert q.lines[1].monthly_micros == 3_500_000
    assert q.payment is not None and q.payment.card_charge_micros == 10_000_000
    assert q.payment.auto_reload is not None
    assert q.payment.auto_reload.store_managed is True
    assert q.yearly_domain_renewal_micros == 14_000_000


@respx.mock
def test_create_quote(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/quotes").mock(
        return_value=httpx.Response(201, json=_quote())
    )
    _assert_quote(client.store.create_quote(items=_ITEMS))
    assert _body(route) == {"items": _ITEMS}
    assert route.calls.last.request.headers.get("Idempotency-Key")


@pytest.mark.anyio
@respx.mock
async def test_create_quote_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/quotes").mock(
        return_value=httpx.Response(201, json=_quote())
    )
    _assert_quote(await aclient.store.create_quote(items=_ITEMS))
    assert _body(route) == {"items": _ITEMS}


@respx.mock
def test_create_order(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/orders").mock(
        return_value=httpx.Response(201, json=_order())
    )
    _assert_order(
        client.store.create_order(
            quote_id=QID,
            expected_due_now_micros=17_500_000,
            forwarding_url="https://acme.test",
            enable_auto_reload=False,
            options={"idempotency_key": "order-1"},
        )
    )
    assert _body(route) == {
        "quote_id": QID,
        "expected_due_now_micros": 17_500_000,
        "forwarding_url": "https://acme.test",
        "enable_auto_reload": False,
    }
    assert route.calls.last.request.headers["Idempotency-Key"] == "order-1"


@pytest.mark.anyio
@respx.mock
async def test_create_order_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/orders").mock(
        return_value=httpx.Response(201, json=_order())
    )
    _assert_order(await aclient.store.create_order(quote_id=QID))
    assert _body(route) == {"quote_id": QID}


@respx.mock
def test_create_order_price_changed(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/store/orders").mock(
        return_value=httpx.Response(
            409,
            json={
                "error": "Conflict",
                "code": "price_changed",
                "request_id": "req_1",
                "message": "The price changed since you looked.",
                "details": {"quote": _quote()},
            },
        )
    )
    with pytest.raises(ConflictError) as info:
        client.store.create_order(quote_id=QID, expected_due_now_micros=1)
    err = info.value
    assert err.code == "price_changed"
    assert isinstance(err.body, dict)
    fresh = StoreQuote.model_validate(err.body["details"]["quote"])
    assert fresh.due_now_micros == 17_500_000


def _mock_list(path: str, first: dict[str, Any], second: dict[str, Any]) -> respx.Route:
    return respx.get(f"{BASE_URL}{path}").mock(
        side_effect=[
            httpx.Response(200, json=_page([first], "c2")),
            httpx.Response(200, json=_page([second])),
        ]
    )


@respx.mock
def test_list_orders_paginates(client: Warmbly) -> None:
    route = _mock_list("/store/orders", _order(), _order(id="other"))
    orders = list(client.store.list_orders(limit=1))
    assert [o.id for o in orders] == [OID, "other"]
    _assert_order(orders[0])
    assert route.calls[0].request.url.params["limit"] == "1"
    assert route.calls[1].request.url.params["cursor"] == "c2"


@pytest.mark.anyio
@respx.mock
async def test_list_orders_async(aclient: AsyncWarmbly) -> None:
    route = _mock_list("/store/orders", _order(), _order(id="other"))
    orders = [o async for o in aclient.store.list_orders(limit=1)]
    assert [o.id for o in orders] == [OID, "other"]
    assert route.calls[1].request.url.params["cursor"] == "c2"


@respx.mock
def test_retrieve_order(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/store/orders/{OID}").mock(
        return_value=httpx.Response(200, json=_order())
    )
    _assert_order(client.store.retrieve_order(OID))


@pytest.mark.anyio
@respx.mock
async def test_retrieve_order_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/store/orders/{OID}").mock(
        return_value=httpx.Response(200, json=_order())
    )
    _assert_order(await aclient.store.retrieve_order(OID))


# -- domains -------------------------------------------------------------------------


@respx.mock
def test_list_domains(client: Warmbly) -> None:
    route = _mock_list("/store/domains", _domain(), _domain(id="d2"))
    domains = list(client.store.list_domains(limit=1))
    assert [d.id for d in domains] == [DID, "d2"]
    _assert_domain(domains[0])
    assert route.calls[1].request.url.params["cursor"] == "c2"


@pytest.mark.anyio
@respx.mock
async def test_list_domains_async(aclient: AsyncWarmbly) -> None:
    _mock_list("/store/domains", _domain(), _domain(id="d2"))
    domains = [d async for d in aclient.store.list_domains()]
    assert [d.id for d in domains] == [DID, "d2"]


def _assert_domain_with_dns(d: StoreDomain) -> None:
    _assert_domain(d)
    assert d.dns[0].id == RECID and d.dns[0].managed is True
    assert d.dns[0].priority == 1 and d.dns[0].purpose == "mail"


@respx.mock
def test_retrieve_domain(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/store/domains/{DID}").mock(
        return_value=httpx.Response(200, json=_domain(dns=[_record()]))
    )
    _assert_domain_with_dns(client.store.retrieve_domain(DID))


@pytest.mark.anyio
@respx.mock
async def test_retrieve_domain_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/store/domains/{DID}").mock(
        return_value=httpx.Response(200, json=_domain(dns=[_record()]))
    )
    _assert_domain_with_dns(await aclient.store.retrieve_domain(DID))


@respx.mock
def test_update_domain(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/store/domains/{DID}").mock(
        return_value=httpx.Response(200, json=_domain(auto_renew=False))
    )
    d = client.store.update_domain(DID, auto_renew=False, forwarding_url="")
    assert d.auto_renew is False
    assert _body(route) == {"auto_renew": False, "forwarding_url": ""}


@pytest.mark.anyio
@respx.mock
async def test_update_domain_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/store/domains/{DID}").mock(
        return_value=httpx.Response(200, json=_domain())
    )
    _assert_domain(
        await aclient.store.update_domain(DID, forwarding_url="https://acme.test")
    )
    assert _body(route) == {"forwarding_url": "https://acme.test"}


# POST routes that take no body and answer a domain.
_DOMAIN_POSTS: list[tuple[str, str]] = [
    ("renew_domain", f"/store/domains/{DID}/renew"),
    ("check_domain_connection", f"/store/domains/{DID}/connection/check"),
    ("regenerate_domain_connection", f"/store/domains/{DID}/connection/regenerate"),
]


@pytest.mark.parametrize(("method", "path"), _DOMAIN_POSTS)
@respx.mock
def test_domain_posts(client: Warmbly, method: str, path: str) -> None:
    route = respx.post(f"{BASE_URL}{path}").mock(
        return_value=httpx.Response(200, json=_domain())
    )
    fn: Callable[..., StoreDomain] = getattr(client.store, method)
    _assert_domain(fn(DID))
    assert route.calls.last.request.content == b""


@pytest.mark.anyio
@pytest.mark.parametrize(("method", "path"), _DOMAIN_POSTS)
@respx.mock
async def test_domain_posts_async(
    aclient: AsyncWarmbly, method: str, path: str
) -> None:
    route = respx.post(f"{BASE_URL}{path}").mock(
        return_value=httpx.Response(200, json=_domain())
    )
    _assert_domain(await getattr(aclient.store, method)(DID))
    assert route.called


@respx.mock
def test_transfer_out_domain(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/store/domains/{DID}/transfer-out").mock(
        return_value=httpx.Response(200, json={"auth_code": "Xy7!secret"})
    )
    out = client.store.transfer_out_domain(DID)
    assert isinstance(out, StoreTransferOut)
    assert out.auth_code == "Xy7!secret"
    assert "Xy7!secret" not in repr(out)


@pytest.mark.anyio
@respx.mock
async def test_transfer_out_domain_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/store/domains/{DID}/transfer-out").mock(
        return_value=httpx.Response(200, json={"auth_code": "Xy7!secret"})
    )
    out = await aclient.store.transfer_out_domain(DID)
    assert out.auth_code == "Xy7!secret"


@respx.mock
def test_connect_domain(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/domains/connect").mock(
        return_value=httpx.Response(201, json=_domain(source="connected"))
    )
    d = client.store.connect_domain(domain="acme.test", method="manual")
    assert d.source == "connected"
    assert _body(route) == {"domain": "acme.test", "method": "manual"}


@pytest.mark.anyio
@respx.mock
async def test_connect_domain_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/domains/connect").mock(
        return_value=httpx.Response(201, json=_domain(source="connected"))
    )
    d = await aclient.store.connect_domain(domain="acme.test", method="nameservers")
    assert d.source == "connected"
    assert _body(route) == {"domain": "acme.test", "method": "nameservers"}


@respx.mock
def test_delete_domain(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/store/domains/{DID}").mock(
        return_value=httpx.Response(204)
    )
    assert client.store.delete_domain(DID) is None  # type: ignore[func-returns-value]
    assert route.called


@pytest.mark.anyio
@respx.mock
async def test_delete_domain_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/store/domains/{DID}").mock(
        return_value=httpx.Response(204)
    )
    assert await aclient.store.delete_domain(DID) is None  # type: ignore[func-returns-value]
    assert route.called


# -- DNS -------------------------------------------------------------------------------


def _assert_record(r: StoreDNSRecord, **expect: Any) -> None:
    assert isinstance(r, StoreDNSRecord)
    assert r.id == RECID and r.ttl is not None
    for key, value in expect.items():
        assert getattr(r, key) == value


@respx.mock
def test_create_dns_record(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/domains/{DID}/dns").mock(
        return_value=httpx.Response(
            201, json=_record(type="TXT", name="@", content="v=x", managed=False)
        )
    )
    r = client.store.create_dns_record(
        DID, type="TXT", name="@", content="v=x", ttl=300
    )
    _assert_record(r, type="TXT", managed=False)
    assert _body(route) == {"type": "TXT", "name": "@", "content": "v=x", "ttl": 300}


@pytest.mark.anyio
@respx.mock
async def test_create_dns_record_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/domains/{DID}/dns").mock(
        return_value=httpx.Response(201, json=_record(managed=False))
    )
    r = await aclient.store.create_dns_record(
        DID, type="MX", name="@", content="mx.test", priority=10
    )
    _assert_record(r, type="MX")
    assert _body(route) == {
        "type": "MX",
        "name": "@",
        "content": "mx.test",
        "priority": 10,
    }


@respx.mock
def test_update_dns_record(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/store/domains/{DID}/dns/{RECID}").mock(
        return_value=httpx.Response(200, json=_record(content="mx2.test"))
    )
    r = client.store.update_dns_record(DID, RECID, content="mx2.test", ttl=600)
    _assert_record(r, content="mx2.test")
    assert _body(route) == {"content": "mx2.test", "ttl": 600}


@pytest.mark.anyio
@respx.mock
async def test_update_dns_record_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/store/domains/{DID}/dns/{RECID}").mock(
        return_value=httpx.Response(200, json=_record(name="www"))
    )
    r = await aclient.store.update_dns_record(DID, RECID, name="www", priority=5)
    _assert_record(r, name="www")
    assert _body(route) == {"name": "www", "priority": 5}


@respx.mock
def test_delete_dns_record(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/store/domains/{DID}/dns/{RECID}").mock(
        return_value=httpx.Response(204)
    )
    assert client.store.delete_dns_record(DID, RECID) is None  # type: ignore[func-returns-value]
    assert route.called


@pytest.mark.anyio
@respx.mock
async def test_delete_dns_record_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/store/domains/{DID}/dns/{RECID}").mock(
        return_value=httpx.Response(204)
    )
    assert await aclient.store.delete_dns_record(DID, RECID) is None  # type: ignore[func-returns-value]
    assert route.called


def _dns_check() -> dict[str, Any]:
    return {
        "nameservers": ["ns1.example.net"],
        "records": [_record(status="ok"), _record(status="missing")],
    }


def _assert_check(c: StoreDNSCheck) -> None:
    assert isinstance(c, StoreDNSCheck)
    assert c.nameservers == ["ns1.example.net"]
    assert [r.status for r in c.records] == ["ok", "missing"]


@respx.mock
def test_check_dns(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/store/domains/{DID}/dns/check").mock(
        return_value=httpx.Response(200, json=_dns_check())
    )
    _assert_check(client.store.check_dns(DID))


@pytest.mark.anyio
@respx.mock
async def test_check_dns_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/store/domains/{DID}/dns/check").mock(
        return_value=httpx.Response(200, json=_dns_check())
    )
    _assert_check(await aclient.store.check_dns(DID))


_CONSENT = {
    "url": "https://login.microsoftonline.com/x/adminconsent",
    "expires_at": "2026-11-22T11:00:00Z",
    "consented": False,
}


def _assert_consent(c: StoreConsentLink) -> None:
    assert isinstance(c, StoreConsentLink)
    assert c.url is not None and c.url.startswith("https://login")
    assert c.expires_at is not None and c.consented is False


@respx.mock
def test_microsoft_consent(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/domains/{DID}/microsoft-consent").mock(
        return_value=httpx.Response(200, json=_CONSENT)
    )
    _assert_consent(client.store.microsoft_consent(DID, order_id=OID))
    assert _body(route) == {"order_id": OID}


@pytest.mark.anyio
@respx.mock
async def test_microsoft_consent_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/domains/{DID}/microsoft-consent").mock(
        return_value=httpx.Response(200, json=_CONSENT)
    )
    _assert_consent(await aclient.store.microsoft_consent(DID))
    assert _body(route) == {}


# -- mailboxes -------------------------------------------------------------------------


@respx.mock
def test_list_mailboxes(client: Warmbly) -> None:
    route = _mock_list("/store/mailboxes", _mailbox(), _mailbox(id="m2"))
    boxes = list(client.store.list_mailboxes(limit=1, cursor="c1"))
    assert [m.id for m in boxes] == [MID, "m2"]
    _assert_mailbox(boxes[0])
    assert route.calls[0].request.url.params["cursor"] == "c1"
    assert route.calls[1].request.url.params["cursor"] == "c2"


@pytest.mark.anyio
@respx.mock
async def test_list_mailboxes_async(aclient: AsyncWarmbly) -> None:
    _mock_list("/store/mailboxes", _mailbox(), _mailbox(id="m2"))
    boxes = [m async for m in aclient.store.list_mailboxes()]
    assert [m.id for m in boxes] == [MID, "m2"]


@respx.mock
def test_update_mailbox(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/store/mailboxes/{MID}").mock(
        return_value=httpx.Response(200, json=_mailbox(first_name="Anna"))
    )
    m = client.store.update_mailbox(MID, first_name="Anna", last_name="Diaz")
    assert m.first_name == "Anna"
    assert _body(route) == {"first_name": "Anna", "last_name": "Diaz"}


@pytest.mark.anyio
@respx.mock
async def test_update_mailbox_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/store/mailboxes/{MID}").mock(
        return_value=httpx.Response(200, json=_mailbox(last_name="Ruiz"))
    )
    m = await aclient.store.update_mailbox(MID, last_name="Ruiz")
    assert m.last_name == "Ruiz"
    assert _body(route) == {"last_name": "Ruiz"}


@respx.mock
def test_set_mailbox_photo(client: Warmbly) -> None:
    route = respx.put(f"{BASE_URL}/store/mailboxes/{MID}/photo").mock(
        return_value=httpx.Response(200, json=_mailbox(photo="pending"))
    )
    m = client.store.set_mailbox_photo(MID, photo_id=PID)
    assert m.photo == "pending"
    assert _body(route) == {"photo_id": PID}


@pytest.mark.anyio
@respx.mock
async def test_set_mailbox_photo_async(aclient: AsyncWarmbly) -> None:
    route = respx.put(f"{BASE_URL}/store/mailboxes/{MID}/photo").mock(
        return_value=httpx.Response(200, json=_mailbox())
    )
    _assert_mailbox(await aclient.store.set_mailbox_photo(MID, photo_id=PID))
    assert _body(route) == {"photo_id": PID}


_CANCELLED = {"cancels_at": "2026-12-20T00:00:00Z"}


@respx.mock
def test_cancel_mailbox(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/store/mailboxes/{MID}").mock(
        return_value=httpx.Response(200, json=_mailbox(**_CANCELLED))
    )
    m = client.store.cancel_mailbox(MID)
    assert m.cancels_at == "2026-12-20T00:00:00Z"
    assert route.called


@pytest.mark.anyio
@respx.mock
async def test_cancel_mailbox_async(aclient: AsyncWarmbly) -> None:
    respx.delete(f"{BASE_URL}/store/mailboxes/{MID}").mock(
        return_value=httpx.Response(200, json=_mailbox(**_CANCELLED))
    )
    m = await aclient.store.cancel_mailbox(MID)
    assert m.cancels_at == "2026-12-20T00:00:00Z"


@respx.mock
def test_resume_mailbox(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/mailboxes/{MID}/resume").mock(
        return_value=httpx.Response(200, json=_mailbox())
    )
    _assert_mailbox(client.store.resume_mailbox(MID))
    assert route.calls.last.request.headers.get("Idempotency-Key")


@pytest.mark.anyio
@respx.mock
async def test_resume_mailbox_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/store/mailboxes/{MID}/resume").mock(
        return_value=httpx.Response(200, json=_mailbox())
    )
    _assert_mailbox(await aclient.store.resume_mailbox(MID))


_SIGN_IN = {
    "email": "ana@acme-mail.com",
    "username": "ana@acme-mail.com",
    "password": "S3cret-pass",
    "login_url": "https://accounts.google.com",
    "admin_console_url": "https://admin.google.com",
}


def _assert_sign_in(s: StoreSignIn) -> None:
    assert isinstance(s, StoreSignIn)
    assert s.password == "S3cret-pass" and s.username == "ana@acme-mail.com"
    assert s.login_url is not None and s.admin_console_url is not None
    assert "S3cret-pass" not in repr(s)


@respx.mock
def test_mailbox_sign_in(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/store/mailboxes/{MID}/sign-in").mock(
        return_value=httpx.Response(200, json=_SIGN_IN)
    )
    _assert_sign_in(client.store.mailbox_sign_in(MID))


@pytest.mark.anyio
@respx.mock
async def test_mailbox_sign_in_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/store/mailboxes/{MID}/sign-in").mock(
        return_value=httpx.Response(200, json=_SIGN_IN)
    )
    _assert_sign_in(await aclient.store.mailbox_sign_in(MID))


# -- photos ------------------------------------------------------------------------------

_PHOTO = {"id": PID, "created_at": "2026-11-22T10:00:00Z"}


def _assert_photo(p: StorePhoto) -> None:
    assert isinstance(p, StorePhoto)
    assert p.id == PID and p.created_at is not None


@respx.mock
def test_upload_photo(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/photos").mock(
        return_value=httpx.Response(201, json=_PHOTO)
    )
    _assert_photo(client.store.upload_photo(file=b"\xff\xd8jpeg"))
    req = route.calls.last.request
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="photo.jpg"' in req.content
    assert b"\xff\xd8jpeg" in req.content


@pytest.mark.anyio
@respx.mock
async def test_upload_photo_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/photos").mock(
        return_value=httpx.Response(201, json=_PHOTO)
    )
    _assert_photo(
        await aclient.store.upload_photo(
            file=b"png", filename="a.png", content_type="image/png"
        )
    )
    assert b'filename="a.png"' in route.calls.last.request.content


@respx.mock
def test_copy_profile_photo(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/photos").mock(
        return_value=httpx.Response(201, json=_PHOTO)
    )
    _assert_photo(client.store.copy_profile_photo())
    assert _body(route) == {"from": "profile"}


@pytest.mark.anyio
@respx.mock
async def test_copy_profile_photo_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/store/photos").mock(
        return_value=httpx.Response(201, json=_PHOTO)
    )
    _assert_photo(await aclient.store.copy_profile_photo())
    assert _body(route) == {"from": "profile"}


@respx.mock
def test_retrieve_photo(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/store/photos/{PID}").mock(
        return_value=httpx.Response(
            200, content=b"\xff\xd8\xff", headers={"content-type": "image/jpeg"}
        )
    )
    assert client.store.retrieve_photo(PID) == b"\xff\xd8\xff"


@pytest.mark.anyio
@respx.mock
async def test_retrieve_photo_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/store/photos/{PID}").mock(
        return_value=httpx.Response(
            200, content=b"\xff\xd8\xff", headers={"content-type": "image/jpeg"}
        )
    )
    assert await aclient.store.retrieve_photo(PID) == b"\xff\xd8\xff"


def test_unknown_fields_never_raise() -> None:
    m = StoreMailbox.model_validate({**_mailbox(), "future_field": 1})
    assert m.id == MID
