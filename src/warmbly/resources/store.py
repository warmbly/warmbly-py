"""The ``store`` resource: the ``/v1/store`` route group.

The store buys domains and Google Workspace or Microsoft 365 mailboxes for the
workspace, sets up their DNS, mail authentication and tracking, and connects
the mailboxes to Warmbly once they are live. Purchases are paid from the
workspace balance, and a saved card covers any shortfall.

A purchase is two steps: :meth:`Store.create_quote` prices a cart and freezes
the prices for a short while, then :meth:`Store.create_order` charges and
orders it. Pass the total the person confirmed as ``expected_due_now_micros``:
if the quote expired and the price moved, the order is refused with ``409``
``price_changed`` (nothing is charged) and ``details.quote`` carries a fresh
quote to show instead. The order then progresses on its own; poll
:meth:`Store.retrieve_order` or listen for the ``STORE_ORDER_UPDATED``
gateway event.

Reading needs the ``READ_STORE`` API permission and changing anything needs
``MANAGE_STORE``. The routes that charge or change what is charged (saving the
registrant, ordering, renewing, transferring out, cancelling or resuming a
mailbox, and turning a domain's ``auto_renew`` on or off) also need the member
behind the key to hold ``manage_billing``; without it they answer ``403``
``forbidden``.

Every amount is in micros of the store's ``currency`` (1 USD is 1,000,000).
On an instance without a store connection every route answers ``404``
``store_disabled``, and a workspace a partner manages answers writes with
``403`` ``store_managed_by_partner``; :meth:`Store.status` reports both in
advance through ``enabled`` and ``reason``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import Field

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncStore",
    "Store",
    "StoreAutoReload",
    "StoreBalance",
    "StoreCard",
    "StoreConsentLink",
    "StoreDNSCheck",
    "StoreDNSConflict",
    "StoreDNSRecord",
    "StoreDisconnected",
    "StoreDomain",
    "StoreDomainConnection",
    "StoreDomainOffer",
    "StoreDomainSearch",
    "StoreLimits",
    "StoreMailAuth",
    "StoreMailbox",
    "StoreNextBundle",
    "StoreOrder",
    "StoreOrderStep",
    "StoreOwnerVerification",
    "StorePayment",
    "StorePhoto",
    "StoreQuote",
    "StoreQuoteLine",
    "StoreRegistrant",
    "StoreSignIn",
    "StoreStatus",
    "StoreTransferOut",
    "StoreTransferRequest",
]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class StoreCard(BaseModel):
    """The saved card a checkout covers a shortfall from."""

    brand: str | None = None
    last4: str | None = None


class StoreBalance(BaseModel):
    """The workspace balance as the checkout sees it."""

    balance_micros: int | None = None
    card: StoreCard | None = None


class StoreLimits(BaseModel):
    """How many mailboxes one domain may hold, and how many are advised."""

    mailboxes_per_domain_max: int | None = None
    mailboxes_per_domain_recommended: int | None = None


class StoreNextBundle(BaseModel):
    """The next monthly mailbox charge: ``amount_micros`` for ``mailboxes`` on ``charge_on``."""

    charge_on: str | None = None
    mailboxes: int | None = None
    amount_micros: int | None = None


class StoreDisconnected(BaseModel):
    """Live purchases the instance can no longer reach while the store is off."""

    mailboxes: int | None = None
    domains: int | None = None


class StoreRegistrant(BaseModel):
    """The ICANN registrant the workspace's domains are registered under.

    ``phone`` is ``+CC.NUMBER`` (for example ``+1.4155550100``) and
    ``country`` an ISO 3166-1 alpha-2 code.
    """

    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class StoreStatus(BaseModel):
    """Whether the workspace can buy, at what prices, and how it would pay.

    ``enabled`` is ``False`` with ``reason`` ``not_configured`` (the instance
    has no store connection) or ``partner_managed`` (a partner buys for the
    workspace). ``plan_active`` is ``False`` when the workspace has no paid
    plan, which buying needs. ``providers`` lists the mailbox providers that
    can be ordered now. ``registrant`` is ``None`` until one is saved, and
    ``registrant_prefill`` is a draft from the billing details meanwhile.
    """

    enabled: bool | None = None
    configured: bool | None = None
    reason: str | None = None
    locked: bool | None = None
    can_configure: bool | None = None
    configure_url: str | None = None
    disconnected: StoreDisconnected | None = None
    metered: bool | None = None
    currency: str | None = None
    mailbox_monthly_micros: int | None = None
    domain_markup: str | None = None
    limits: StoreLimits | None = None
    providers: Sequence[str] = []
    balance: StoreBalance | None = None
    plan_active: bool | None = None
    registrant: StoreRegistrant | None = None
    registrant_prefill: StoreRegistrant | None = None
    stripe_publishable_key: str | None = None
    min_card_charge_micros: int | None = None
    billing_day: int | None = None
    next_bundle: StoreNextBundle | None = None
    default_forwarding_url: str | None = None
    photos: bool | None = None


class StoreDomainOffer(BaseModel):
    """One domain search result at retail.

    ``price_micros`` covers ``years``, the extension's minimum term;
    ``renew_micros`` is per year. ``reason`` says why an unavailable name
    cannot be bought.
    """

    domain: str | None = None
    display_name: str | None = None
    tld: str | None = None
    available: bool | None = None
    exact: bool | None = None
    years: int | None = None
    price_micros: int | None = None
    renew_micros: int | None = None
    reason: str | None = None


class StoreDomainSearch(BaseModel):
    """The answer to a domain search: exact matches first, then suggestions."""

    query: str | None = None
    data: Sequence[StoreDomainOffer] = []


class StoreQuoteLine(BaseModel):
    """One priced line of a quote.

    ``type`` is ``domain`` or ``mailboxes``. ``admin_email`` names the mailbox
    that becomes the domain's Workspace or tenant admin. ``nameservers_change``
    means a connected domain needs new nameservers set after the order.
    """

    type: str | None = None
    domain: str | None = None
    years: int | None = None
    provider: str | None = None
    count: int | None = None
    amount_micros: int | None = None
    renew_micros: int | None = None
    monthly_micros: int | None = None
    admin_email: str | None = None
    nameservers_change: bool | None = None


class StoreAutoReload(BaseModel):
    """The balance's automatic reload as it will be after the order."""

    enabled: bool | None = None
    threshold_micros: int | None = None
    amount_micros: int | None = None
    store_managed: bool | None = None


class StorePayment(BaseModel):
    """How a checkout will be paid: from the balance first, then the card."""

    balance_micros: int | None = None
    from_balance_micros: int | None = None
    card_charge_micros: int | None = None
    balance_after_micros: int | None = None
    card: StoreCard | None = None
    needs_payment_method: bool | None = None
    auto_reload: StoreAutoReload | None = None


class StoreQuote(BaseModel):
    """A priced cart, frozen until ``expires_at``."""

    id: str
    expires_at: str | None = None
    lines: Sequence[StoreQuoteLine] = []
    due_now_micros: int | None = None
    recurring_monthly_micros: int | None = None
    yearly_domain_renewal_micros: int | None = None
    payment: StorePayment | None = None


class StoreMailAuth(BaseModel):
    """The state of a domain's MX, SPF, DKIM and DMARC records."""

    mx: str | None = None
    spf: str | None = None
    dkim: str | None = None
    dmarc: str | None = None


class StoreDNSRecord(BaseModel):
    """One record in a store domain's zone.

    ``managed`` records are kept for mail and forwarding and cannot be changed.
    ``status`` is set by :meth:`Store.check_dns`: ``ok`` or ``missing``.
    """

    id: str
    type: str | None = None
    name: str | None = None
    content: str | None = None
    ttl: int | None = None
    priority: int | None = None
    managed: bool | None = None
    purpose: str | None = None
    status: str | None = None


class StoreDNSCheck(BaseModel):
    """Every record of a domain looked up in public DNS."""

    nameservers: Sequence[str] = []
    records: Sequence[StoreDNSRecord] = []


class StoreDomainConnection(BaseModel):
    """How far a domain registered elsewhere is connected.

    ``method`` is ``nameservers`` or ``manual``.
    """

    method: str | None = None
    status: str | None = None
    expires_at: str | None = None
    checked_at: str | None = None
    current_nameservers: Sequence[str] = []


class StoreDNSConflict(BaseModel):
    """A record in the way of mail. ``record_id`` is set when it can be removed here."""

    record_id: str | None = None
    type: str | None = None
    name: str | None = None
    content: str | None = None


class StoreOwnerVerification(BaseModel):
    """The domain owner's email check, with its deadline while pending."""

    status: str | None = None
    email: str | None = None
    deadline: str | None = None


class StoreTransferRequest(BaseModel):
    """Another registrar asking for the domain."""

    status: str | None = None
    requested_at: str | None = None
    auto_approve_at: str | None = None


class StoreDomain(BaseModel):
    """A domain bought in the store, or one registered elsewhere and connected.

    ``source`` is ``purchased`` or ``connected``. ``renewable`` marks a
    purchased domain that renewal, ``auto_renew`` and transfer-out apply to.
    ``dns`` is filled by :meth:`Store.retrieve_domain` only.
    """

    id: str
    name: str | None = None
    status: str | None = None
    source: str | None = None
    provider: str | None = None
    renewable: bool | None = None
    expires_at: str | None = None
    auto_renew: bool | None = None
    renew_micros: int | None = None
    forwarding_url: str | None = None
    forwarding_status: str | None = None
    mail_auth: StoreMailAuth | None = None
    mailbox_count: int | None = None
    nameservers: Sequence[str] = []
    connection: StoreDomainConnection | None = None
    dns_conflicts: Sequence[StoreDNSConflict] = []
    owner_verification: StoreOwnerVerification | None = None
    transfer: StoreTransferRequest | None = None
    tracking_host: str | None = None
    created_at: str | None = None
    dns: Sequence[StoreDNSRecord] = []


class StoreMailbox(BaseModel):
    """A purchased mailbox.

    ``connect_state`` is ``waiting``, ``connecting``, ``connected`` or
    ``failed``; ``email_account_id`` is the Warmbly mailbox once connected.
    ``action_required`` is ``microsoft_consent`` while the domain's Microsoft
    365 administrator has not approved Warmbly (see
    :meth:`Store.microsoft_consent`), and ``action_reason`` says why the
    automatic approval left it to them. ``paused`` means sending and warmup
    stopped because the workspace has no plan; the mailbox still bills.
    ``photo`` is ``none``, ``pending`` or ``set``.
    """

    id: str
    email: str | None = None
    domain_id: str | None = None
    provider: str | None = None
    status: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool | None = None
    paused: bool | None = None
    monthly_micros: int | None = None
    paid_through: str | None = None
    cancels_at: str | None = None
    cancelled_at: str | None = None
    email_account_id: str | None = None
    connect_state: str | None = None
    action_required: str | None = None
    action_reason: str | None = None
    photo: str | None = None
    created_at: str | None = None


class StoreOrderStep(BaseModel):
    """One stage of an order's progress track.

    ``key`` is one of ``register``, ``dns``, ``mail_auth``, ``mailboxes``,
    ``delegation`` or ``ready``.
    """

    key: str | None = None
    status: str | None = None
    at: str | None = None


class StoreOrder(BaseModel):
    """One checkout and its live progress.

    ``status`` is ``charging``, ``processing``, ``completed``,
    ``partially_failed`` or ``failed``.
    """

    id: str
    status: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    due_now_micros: int | None = None
    charged_micros: int | None = None
    refunded_micros: int | None = None
    steps: Sequence[StoreOrderStep] = []
    domains: Sequence[StoreDomain] = []
    mailboxes: Sequence[StoreMailbox] = []


class StoreTransferOut(BaseModel):
    """A purchased domain's transfer authorization code.

    ``auth_code`` is a secret that moves the domain to another registrar, so
    it is kept out of ``repr``.
    """

    auth_code: str | None = Field(default=None, repr=False)


class StoreSignIn(BaseModel):
    """A purchased mailbox's sign-in.

    For the admin mailbox ``admin_console_url`` opens the Workspace or tenant
    admin console. ``password`` is kept out of ``repr``.
    """

    email: str | None = None
    username: str | None = None
    password: str | None = Field(default=None, repr=False)
    login_url: str | None = None
    admin_console_url: str | None = None


class StorePhoto(BaseModel):
    """An uploaded mailbox profile photo, named by ``id`` from a quote or a mailbox."""

    id: str
    created_at: str | None = None


class StoreConsentLink(BaseModel):
    """Where a domain's Microsoft 365 administrator approves Warmbly.

    ``url`` is ``None`` and ``consented`` ``True`` when nothing is left to
    approve.
    """

    url: str | None = None
    expires_at: str | None = None
    consented: bool | None = None


# ---------------------------------------------------------------------------
# Body helpers
# ---------------------------------------------------------------------------


def _registrant_body(
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    address1: str,
    city: str,
    postal_code: str,
    country: str,
    organization: NotGivenOr[str],
    address2: NotGivenOr[str],
    state: NotGivenOr[str],
) -> dict[str, object]:
    return drop_not_given(
        {
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization,
            "email": email,
            "phone": phone,
            "address1": address1,
            "address2": address2,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
        }
    )


def _items_body(items: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    return {"items": [dict(item) for item in items]}


def _dns_patch_body(
    *,
    name: NotGivenOr[str],
    content: NotGivenOr[str],
    ttl: NotGivenOr[int],
    priority: NotGivenOr[int],
) -> dict[str, object]:
    return drop_not_given(
        {"name": name, "content": content, "ttl": ttl, "priority": priority}
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


class Store(SyncAPIResource):
    """Synchronous ``store`` resource."""

    def status(self, *, options: RequestOptions | None = None) -> StoreStatus:
        """Report whether the workspace can buy, the prices, and how it would pay.

        Requires the ``READ_STORE`` API permission.
        """
        return self._get("/store/status", cast_to=StoreStatus, options=options)

    def search_domains(
        self,
        *,
        q: str,
        tlds: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        suggestions: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDomainSearch:
        """Search domain names to buy, with retail prices.

        Requires the ``READ_STORE`` API permission. A ``q`` that is not a word
        or a domain name answers ``400`` ``invalid_query``.

        Args:
            q: A word or a domain name.
            tlds: Extensions to search (``["com", "io"]``); defaults to the
                store's own selection.
            suggestions: ``False`` answers with the exact matches only.
        """
        return self._get(
            "/store/domains/search",
            cast_to=StoreDomainSearch,
            query={
                "q": q,
                "tlds": list(tlds) if isinstance(tlds, Sequence) else tlds,
                "suggestions": suggestions,
            },
            options=options,
        )

    def set_registrant(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        address1: str,
        city: str,
        postal_code: str,
        country: str,
        organization: NotGivenOr[str] = NOT_GIVEN,
        address2: NotGivenOr[str] = NOT_GIVEN,
        state: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreRegistrant:
        """Save the registrant the workspace's domains are registered under.

        Needed before a quote that contains a domain (otherwise ``422``
        ``registrant_required``). An incomplete or malformed registrant is
        refused with ``400`` ``contact_invalid``, and ``details.fields`` names
        the refused fields.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``.

        Args:
            phone: ``+CC.NUMBER``, for example ``+1.4155550100``.
            country: An ISO 3166-1 alpha-2 code, for example ``US``.
        """
        return self._put(
            "/store/registrant",
            cast_to=StoreRegistrant,
            body=_registrant_body(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address1=address1,
                city=city,
                postal_code=postal_code,
                country=country,
                organization=organization,
                address2=address2,
                state=state,
            ),
            options=options,
        )

    def create_quote(
        self,
        *,
        items: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> StoreQuote:
        """Price a cart and freeze the prices until ``expires_at``.

        Nothing is charged. Requires the ``MANAGE_STORE`` API permission. A
        workspace without a paid plan gets ``402`` ``plan_required``; a
        domain before a registrant is saved gets ``422``
        ``registrant_required``; malformed items get ``400``
        ``store_items_invalid``.

        Args:
            items: The cart. A domain line is ``{"type": "domain", "domain":
                "acme.com", "years": 1}``. A mailbox line is ``{"type":
                "mailboxes", "domain": "acme.com", "provider": "google",
                "mailboxes": [{"local_part": "ana", "first_name": "Ana",
                "last_name": "Diaz", "admin": False}]}``; it may carry a
                ``photo_id`` for every mailbox on the domain, and each mailbox
                its own ``photo_id`` and ``signature`` (``{"html": ...,
                "plain": ...}``). ``provider`` is one of
                :attr:`StoreStatus.providers`.
        """
        return self._post(
            "/store/quotes",
            cast_to=StoreQuote,
            body=_items_body(items),
            options=options,
        )

    def create_order(
        self,
        *,
        quote_id: str,
        expected_due_now_micros: NotGivenOr[int] = NOT_GIVEN,
        forwarding_url: NotGivenOr[str] = NOT_GIVEN,
        enable_auto_reload: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreOrder:
        """Charge the workspace for a quote and place the order.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. The balance pays first and the saved card covers
        the rest. Refusals charge nothing: ``409`` ``price_changed`` when an
        expired quote was priced again at a different total
        (``details.quote`` is the fresh quote), ``402``
        ``payment_method_required`` when no card is saved (the body's
        ``setup_url`` opens a card-setup page), ``402`` ``card_declined``,
        ``404`` ``quote_not_found``. The idempotency key the SDK sends makes a
        retry return the same order rather than charge twice.

        Args:
            quote_id: The quote from :meth:`create_quote`.
            expected_due_now_micros: The total the person confirmed. A
                different total is refused, not charged.
            forwarding_url: An ``https://`` website new domains forward to.
            enable_auto_reload: Turn the balance's automatic reload on, sized
                to the mailboxes. Defaults to on unless the workspace set
                automatic reload up itself.
        """
        return self._post(
            "/store/orders",
            cast_to=StoreOrder,
            body=drop_not_given(
                {
                    "quote_id": quote_id,
                    "forwarding_url": forwarding_url,
                    "expected_due_now_micros": expected_due_now_micros,
                    "enable_auto_reload": enable_auto_reload,
                }
            ),
            options=options,
        )

    def list_orders(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[StoreOrder]:
        """List the workspace's orders, newest first (auto-paginating).

        Requires the ``READ_STORE`` API permission.

        Args:
            limit: Page size, 1 to 100.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/store/orders",
            model=StoreOrder,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_order(
        self, order_id: str, *, options: RequestOptions | None = None
    ) -> StoreOrder:
        """Fetch one order with its progress, domains and mailboxes.

        Requires the ``READ_STORE`` API permission.
        """
        return self._get(
            f"/store/orders/{order_id}", cast_to=StoreOrder, options=options
        )

    def list_domains(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[StoreDomain]:
        """List purchased and connected domains (auto-paginating).

        Requires the ``READ_STORE`` API permission.

        Args:
            limit: Page size, 1 to 100.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/store/domains",
            model=StoreDomain,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Fetch one domain with its DNS records (``dns``).

        Requires the ``READ_STORE`` API permission.
        """
        return self._get(
            f"/store/domains/{domain_id}", cast_to=StoreDomain, options=options
        )

    def update_domain(
        self,
        domain_id: str,
        *,
        auto_renew: NotGivenOr[bool] = NOT_GIVEN,
        forwarding_url: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDomain:
        """Change a domain's automatic renewal or forwarding website.

        Requires the ``MANAGE_STORE`` API permission. Changing ``auto_renew``
        changes what is charged, so it also needs the member's
        ``manage_billing``. A connected domain refuses ``auto_renew`` with
        ``409`` ``domain_registered_elsewhere``.

        Args:
            auto_renew: Renew the domain automatically before it expires.
            forwarding_url: An ``https://`` website the bare domain forwards
                to, or ``""`` for none.
        """
        return self._patch(
            f"/store/domains/{domain_id}",
            cast_to=StoreDomain,
            body=drop_not_given(
                {"auto_renew": auto_renew, "forwarding_url": forwarding_url}
            ),
            options=options,
        )

    def renew_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Renew a purchased domain for another year now, charging the workspace.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. Refused with ``422`` ``renewal_not_due`` before the
        renewal window opens and ``409`` ``renewal_in_progress`` while one is
        running.
        """
        return self._post(
            f"/store/domains/{domain_id}/renew", cast_to=StoreDomain, options=options
        )

    def transfer_out_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreTransferOut:
        """Get the authorization code that moves a purchased domain to another registrar.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. The server keeps no copy of the answer, and asking
        again returns the same code and charges nothing, so a retry is safe.
        Refused with ``409`` ``transfer_locked`` within 60 days of
        registration.
        """
        return self._post(
            f"/store/domains/{domain_id}/transfer-out",
            cast_to=StoreTransferOut,
            options=options,
        )

    def connect_domain(
        self,
        *,
        domain: str,
        method: str,
        options: RequestOptions | None = None,
    ) -> StoreDomain:
        """Add a domain registered elsewhere, so mailboxes can be bought on it.

        Nothing is charged. Requires the ``MANAGE_STORE`` API permission.
        Follow ``connection`` on the answer, and call
        :meth:`check_domain_connection` once the change is made.

        Args:
            domain: The domain name.
            method: ``nameservers`` (move the domain's DNS here) or ``manual``
                (add the records at its DNS provider).
        """
        return self._post(
            "/store/domains/connect",
            cast_to=StoreDomain,
            body={"domain": domain, "method": method},
            options=options,
        )

    def check_domain_connection(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Check a connected domain's nameservers or records again now.

        Requires the ``MANAGE_STORE`` API permission.
        """
        return self._post(
            f"/store/domains/{domain_id}/connection/check",
            cast_to=StoreDomain,
            options=options,
        )

    def regenerate_domain_connection(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Start a connected domain's connection over, for an expired one.

        Requires the ``MANAGE_STORE`` API permission.
        """
        return self._post(
            f"/store/domains/{domain_id}/connection/regenerate",
            cast_to=StoreDomain,
            options=options,
        )

    def delete_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Remove a connected domain that has no mailboxes (``204``).

        Requires the ``MANAGE_STORE`` API permission. A purchased domain is
        refused with ``409`` ``domain_registered_here`` (it leaves by
        :meth:`transfer_out_domain`), and one with mailboxes with ``409``
        ``domain_in_use``.
        """
        self._delete(f"/store/domains/{domain_id}", cast_to=type(None), options=options)

    def create_dns_record(
        self,
        domain_id: str,
        *,
        type: str,
        name: str,
        content: str,
        ttl: NotGivenOr[int] = NOT_GIVEN,
        priority: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDNSRecord:
        """Add a DNS record to a store domain.

        Requires the ``MANAGE_STORE`` API permission. A record that clashes
        with one kept for mail answers ``409`` ``dns_record_conflict``; a
        domain connected with ``manual`` answers ``409`` ``dns_not_hosted``.

        Args:
            type: The record type, such as ``A``, ``CNAME``, ``TXT`` or ``MX``.
            name: The host name, ``@`` for the domain itself.
            content: The record's value.
            ttl: Time to live in seconds.
            priority: For ``MX`` and ``SRV`` records.
        """
        return self._post(
            f"/store/domains/{domain_id}/dns",
            cast_to=StoreDNSRecord,
            body=drop_not_given(
                {
                    "type": type,
                    "name": name,
                    "content": content,
                    "ttl": ttl,
                    "priority": priority,
                }
            ),
            options=options,
        )

    def update_dns_record(
        self,
        domain_id: str,
        record_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        content: NotGivenOr[str] = NOT_GIVEN,
        ttl: NotGivenOr[int] = NOT_GIVEN,
        priority: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDNSRecord:
        """Change a DNS record. Omitted arguments keep their value.

        Requires the ``MANAGE_STORE`` API permission. A ``managed`` record
        answers ``409`` ``dns_record_managed``.
        """
        return self._patch(
            f"/store/domains/{domain_id}/dns/{record_id}",
            cast_to=StoreDNSRecord,
            body=_dns_patch_body(
                name=name, content=content, ttl=ttl, priority=priority
            ),
            options=options,
        )

    def delete_dns_record(
        self,
        domain_id: str,
        record_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Delete a DNS record (``204``).

        Requires the ``MANAGE_STORE`` API permission.
        """
        self._delete(
            f"/store/domains/{domain_id}/dns/{record_id}",
            cast_to=type(None),
            options=options,
        )

    def check_dns(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDNSCheck:
        """Look every record of a domain up in public DNS now.

        Changes nothing. Requires the ``READ_STORE`` API permission.
        """
        return self._post(
            f"/store/domains/{domain_id}/dns/check",
            cast_to=StoreDNSCheck,
            options=options,
        )

    def microsoft_consent(
        self,
        domain_id: str,
        *,
        order_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreConsentLink:
        """Get the link where a domain's Microsoft 365 administrator approves Warmbly.

        Needed while a mailbox reports ``action_required``
        ``microsoft_consent``. Nothing changes until the administrator
        approves. Requires the ``MANAGE_STORE`` API permission.

        Args:
            order_id: The order the approval is started from, which the
                administrator lands back on.
        """
        return self._post(
            f"/store/domains/{domain_id}/microsoft-consent",
            cast_to=StoreConsentLink,
            body=drop_not_given({"order_id": order_id}),
            options=options,
        )

    def list_mailboxes(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[StoreMailbox]:
        """List purchased mailboxes (auto-paginating).

        Requires the ``READ_STORE`` API permission.

        Args:
            limit: Page size, 1 to 100.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/store/mailboxes",
            model=StoreMailbox,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def update_mailbox(
        self,
        mailbox_id: str,
        *,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreMailbox:
        """Change a purchased mailbox's sender name.

        Requires the ``MANAGE_STORE`` API permission. A name that breaks the
        naming rules answers ``400`` ``invalid_name``.
        """
        return self._patch(
            f"/store/mailboxes/{mailbox_id}",
            cast_to=StoreMailbox,
            body=drop_not_given({"first_name": first_name, "last_name": last_name}),
            options=options,
        )

    def set_mailbox_photo(
        self,
        mailbox_id: str,
        *,
        photo_id: str,
        options: RequestOptions | None = None,
    ) -> StoreMailbox:
        """Set a purchased mailbox's profile photo at Google or Microsoft.

        Requires the ``MANAGE_STORE`` API permission.

        Args:
            photo_id: A photo from :meth:`upload_photo` or
                :meth:`copy_profile_photo`.
        """
        return self._put(
            f"/store/mailboxes/{mailbox_id}/photo",
            cast_to=StoreMailbox,
            body={"photo_id": photo_id},
            options=options,
        )

    def cancel_mailbox(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> StoreMailbox:
        """Cancel a purchased mailbox at the end of its paid month.

        The answer carries ``cancels_at``. Requires the ``MANAGE_STORE`` API
        permission, and the member's ``manage_billing``.
        """
        return self._delete(
            f"/store/mailboxes/{mailbox_id}", cast_to=StoreMailbox, options=options
        )

    def resume_mailbox(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> StoreMailbox:
        """Undo a pending cancellation, so the mailbox keeps billing monthly.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. A mailbox that is not set to cancel answers
        ``409`` ``mailbox_not_cancellable``.
        """
        return self._post(
            f"/store/mailboxes/{mailbox_id}/resume",
            cast_to=StoreMailbox,
            options=options,
        )

    def mailbox_sign_in(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> StoreSignIn:
        """Show a purchased mailbox's sign-in (the admin console's, for the admin mailbox).

        Requires the ``MANAGE_STORE`` API permission. The server keeps no copy
        of the answer, and asking again returns the same sign-in, so a retry
        is safe. A mailbox without one answers ``409``
        ``sign_in_unavailable``.
        """
        return self._post(
            f"/store/mailboxes/{mailbox_id}/sign-in",
            cast_to=StoreSignIn,
            options=options,
        )

    def upload_photo(
        self,
        *,
        file: bytes,
        filename: str = "photo.jpg",
        content_type: str = "image/jpeg",
        options: RequestOptions | None = None,
    ) -> StorePhoto:
        """Upload a mailbox profile photo, for a quote line or :meth:`set_mailbox_photo`.

        PNG or JPG, up to 2 MB and 2048 pixels on each side; anything else
        answers ``400`` ``photo_invalid``. A photo nothing uses is deleted
        after 24 hours. Requires the ``MANAGE_STORE`` API permission.

        Args:
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
            content_type: The image's MIME type.
        """
        return self._client.request(
            cast_to=StorePhoto,
            method="POST",
            path="/store/photos",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def copy_profile_photo(
        self, *, options: RequestOptions | None = None
    ) -> StorePhoto:
        """Copy the calling member's own profile photo for use on mailboxes.

        Answers ``404`` ``profile_photo_missing`` when the member has none.
        Requires the ``MANAGE_STORE`` API permission.
        """
        return self._post(
            "/store/photos",
            cast_to=StorePhoto,
            body={"from": "profile"},
            options=options,
        )

    def retrieve_photo(
        self, photo_id: str, *, options: RequestOptions | None = None
    ) -> bytes:
        """Download an uploaded photo as JPEG bytes.

        Requires the ``READ_STORE`` API permission.
        """
        return self._get(f"/store/photos/{photo_id}", cast_to=bytes, options=options)


class AsyncStore(AsyncAPIResource):
    """Asynchronous ``store`` resource."""

    async def status(self, *, options: RequestOptions | None = None) -> StoreStatus:
        """Report whether the workspace can buy, the prices, and how it would pay.

        Requires the ``READ_STORE`` API permission.
        """
        return await self._get("/store/status", cast_to=StoreStatus, options=options)

    async def search_domains(
        self,
        *,
        q: str,
        tlds: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        suggestions: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDomainSearch:
        """Search domain names to buy, with retail prices.

        Requires the ``READ_STORE`` API permission. A ``q`` that is not a word
        or a domain name answers ``400`` ``invalid_query``.

        Args:
            q: A word or a domain name.
            tlds: Extensions to search (``["com", "io"]``); defaults to the
                store's own selection.
            suggestions: ``False`` answers with the exact matches only.
        """
        return await self._get(
            "/store/domains/search",
            cast_to=StoreDomainSearch,
            query={
                "q": q,
                "tlds": list(tlds) if isinstance(tlds, Sequence) else tlds,
                "suggestions": suggestions,
            },
            options=options,
        )

    async def set_registrant(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        address1: str,
        city: str,
        postal_code: str,
        country: str,
        organization: NotGivenOr[str] = NOT_GIVEN,
        address2: NotGivenOr[str] = NOT_GIVEN,
        state: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreRegistrant:
        """Save the registrant the workspace's domains are registered under.

        Needed before a quote that contains a domain (otherwise ``422``
        ``registrant_required``). An incomplete or malformed registrant is
        refused with ``400`` ``contact_invalid``, and ``details.fields`` names
        the refused fields.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``.

        Args:
            phone: ``+CC.NUMBER``, for example ``+1.4155550100``.
            country: An ISO 3166-1 alpha-2 code, for example ``US``.
        """
        return await self._put(
            "/store/registrant",
            cast_to=StoreRegistrant,
            body=_registrant_body(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address1=address1,
                city=city,
                postal_code=postal_code,
                country=country,
                organization=organization,
                address2=address2,
                state=state,
            ),
            options=options,
        )

    async def create_quote(
        self,
        *,
        items: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> StoreQuote:
        """Price a cart and freeze the prices until ``expires_at``.

        Nothing is charged. Requires the ``MANAGE_STORE`` API permission. A
        workspace without a paid plan gets ``402`` ``plan_required``; a
        domain before a registrant is saved gets ``422``
        ``registrant_required``; malformed items get ``400``
        ``store_items_invalid``.

        Args:
            items: The cart. A domain line is ``{"type": "domain", "domain":
                "acme.com", "years": 1}``. A mailbox line is ``{"type":
                "mailboxes", "domain": "acme.com", "provider": "google",
                "mailboxes": [{"local_part": "ana", "first_name": "Ana",
                "last_name": "Diaz", "admin": False}]}``; it may carry a
                ``photo_id`` for every mailbox on the domain, and each mailbox
                its own ``photo_id`` and ``signature`` (``{"html": ...,
                "plain": ...}``). ``provider`` is one of
                :attr:`StoreStatus.providers`.
        """
        return await self._post(
            "/store/quotes",
            cast_to=StoreQuote,
            body=_items_body(items),
            options=options,
        )

    async def create_order(
        self,
        *,
        quote_id: str,
        expected_due_now_micros: NotGivenOr[int] = NOT_GIVEN,
        forwarding_url: NotGivenOr[str] = NOT_GIVEN,
        enable_auto_reload: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreOrder:
        """Charge the workspace for a quote and place the order.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. The balance pays first and the saved card covers
        the rest. Refusals charge nothing: ``409`` ``price_changed`` when an
        expired quote was priced again at a different total
        (``details.quote`` is the fresh quote), ``402``
        ``payment_method_required`` when no card is saved (the body's
        ``setup_url`` opens a card-setup page), ``402`` ``card_declined``,
        ``404`` ``quote_not_found``. The idempotency key the SDK sends makes a
        retry return the same order rather than charge twice.

        Args:
            quote_id: The quote from :meth:`create_quote`.
            expected_due_now_micros: The total the person confirmed. A
                different total is refused, not charged.
            forwarding_url: An ``https://`` website new domains forward to.
            enable_auto_reload: Turn the balance's automatic reload on, sized
                to the mailboxes. Defaults to on unless the workspace set
                automatic reload up itself.
        """
        return await self._post(
            "/store/orders",
            cast_to=StoreOrder,
            body=drop_not_given(
                {
                    "quote_id": quote_id,
                    "forwarding_url": forwarding_url,
                    "expected_due_now_micros": expected_due_now_micros,
                    "enable_auto_reload": enable_auto_reload,
                }
            ),
            options=options,
        )

    def list_orders(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[StoreOrder]:
        """List the workspace's orders, newest first (auto-paginating).

        Requires the ``READ_STORE`` API permission.

        Args:
            limit: Page size, 1 to 100.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/store/orders",
            model=StoreOrder,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_order(
        self, order_id: str, *, options: RequestOptions | None = None
    ) -> StoreOrder:
        """Fetch one order with its progress, domains and mailboxes.

        Requires the ``READ_STORE`` API permission.
        """
        return await self._get(
            f"/store/orders/{order_id}", cast_to=StoreOrder, options=options
        )

    def list_domains(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[StoreDomain]:
        """List purchased and connected domains (auto-paginating).

        Requires the ``READ_STORE`` API permission.

        Args:
            limit: Page size, 1 to 100.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/store/domains",
            model=StoreDomain,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Fetch one domain with its DNS records (``dns``).

        Requires the ``READ_STORE`` API permission.
        """
        return await self._get(
            f"/store/domains/{domain_id}", cast_to=StoreDomain, options=options
        )

    async def update_domain(
        self,
        domain_id: str,
        *,
        auto_renew: NotGivenOr[bool] = NOT_GIVEN,
        forwarding_url: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDomain:
        """Change a domain's automatic renewal or forwarding website.

        Requires the ``MANAGE_STORE`` API permission. Changing ``auto_renew``
        changes what is charged, so it also needs the member's
        ``manage_billing``. A connected domain refuses ``auto_renew`` with
        ``409`` ``domain_registered_elsewhere``.

        Args:
            auto_renew: Renew the domain automatically before it expires.
            forwarding_url: An ``https://`` website the bare domain forwards
                to, or ``""`` for none.
        """
        return await self._patch(
            f"/store/domains/{domain_id}",
            cast_to=StoreDomain,
            body=drop_not_given(
                {"auto_renew": auto_renew, "forwarding_url": forwarding_url}
            ),
            options=options,
        )

    async def renew_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Renew a purchased domain for another year now, charging the workspace.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. Refused with ``422`` ``renewal_not_due`` before the
        renewal window opens and ``409`` ``renewal_in_progress`` while one is
        running.
        """
        return await self._post(
            f"/store/domains/{domain_id}/renew", cast_to=StoreDomain, options=options
        )

    async def transfer_out_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreTransferOut:
        """Get the authorization code that moves a purchased domain to another registrar.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. The server keeps no copy of the answer, and asking
        again returns the same code and charges nothing, so a retry is safe.
        Refused with ``409`` ``transfer_locked`` within 60 days of
        registration.
        """
        return await self._post(
            f"/store/domains/{domain_id}/transfer-out",
            cast_to=StoreTransferOut,
            options=options,
        )

    async def connect_domain(
        self,
        *,
        domain: str,
        method: str,
        options: RequestOptions | None = None,
    ) -> StoreDomain:
        """Add a domain registered elsewhere, so mailboxes can be bought on it.

        Nothing is charged. Requires the ``MANAGE_STORE`` API permission.
        Follow ``connection`` on the answer, and call
        :meth:`check_domain_connection` once the change is made.

        Args:
            domain: The domain name.
            method: ``nameservers`` (move the domain's DNS here) or ``manual``
                (add the records at its DNS provider).
        """
        return await self._post(
            "/store/domains/connect",
            cast_to=StoreDomain,
            body={"domain": domain, "method": method},
            options=options,
        )

    async def check_domain_connection(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Check a connected domain's nameservers or records again now.

        Requires the ``MANAGE_STORE`` API permission.
        """
        return await self._post(
            f"/store/domains/{domain_id}/connection/check",
            cast_to=StoreDomain,
            options=options,
        )

    async def regenerate_domain_connection(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDomain:
        """Start a connected domain's connection over, for an expired one.

        Requires the ``MANAGE_STORE`` API permission.
        """
        return await self._post(
            f"/store/domains/{domain_id}/connection/regenerate",
            cast_to=StoreDomain,
            options=options,
        )

    async def delete_domain(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Remove a connected domain that has no mailboxes (``204``).

        Requires the ``MANAGE_STORE`` API permission. A purchased domain is
        refused with ``409`` ``domain_registered_here`` (it leaves by
        :meth:`transfer_out_domain`), and one with mailboxes with ``409``
        ``domain_in_use``.
        """
        await self._delete(
            f"/store/domains/{domain_id}", cast_to=type(None), options=options
        )

    async def create_dns_record(
        self,
        domain_id: str,
        *,
        type: str,
        name: str,
        content: str,
        ttl: NotGivenOr[int] = NOT_GIVEN,
        priority: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDNSRecord:
        """Add a DNS record to a store domain.

        Requires the ``MANAGE_STORE`` API permission. A record that clashes
        with one kept for mail answers ``409`` ``dns_record_conflict``; a
        domain connected with ``manual`` answers ``409`` ``dns_not_hosted``.

        Args:
            type: The record type, such as ``A``, ``CNAME``, ``TXT`` or ``MX``.
            name: The host name, ``@`` for the domain itself.
            content: The record's value.
            ttl: Time to live in seconds.
            priority: For ``MX`` and ``SRV`` records.
        """
        return await self._post(
            f"/store/domains/{domain_id}/dns",
            cast_to=StoreDNSRecord,
            body=drop_not_given(
                {
                    "type": type,
                    "name": name,
                    "content": content,
                    "ttl": ttl,
                    "priority": priority,
                }
            ),
            options=options,
        )

    async def update_dns_record(
        self,
        domain_id: str,
        record_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        content: NotGivenOr[str] = NOT_GIVEN,
        ttl: NotGivenOr[int] = NOT_GIVEN,
        priority: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreDNSRecord:
        """Change a DNS record. Omitted arguments keep their value.

        Requires the ``MANAGE_STORE`` API permission. A ``managed`` record
        answers ``409`` ``dns_record_managed``.
        """
        return await self._patch(
            f"/store/domains/{domain_id}/dns/{record_id}",
            cast_to=StoreDNSRecord,
            body=_dns_patch_body(
                name=name, content=content, ttl=ttl, priority=priority
            ),
            options=options,
        )

    async def delete_dns_record(
        self,
        domain_id: str,
        record_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Delete a DNS record (``204``).

        Requires the ``MANAGE_STORE`` API permission.
        """
        await self._delete(
            f"/store/domains/{domain_id}/dns/{record_id}",
            cast_to=type(None),
            options=options,
        )

    async def check_dns(
        self, domain_id: str, *, options: RequestOptions | None = None
    ) -> StoreDNSCheck:
        """Look every record of a domain up in public DNS now.

        Changes nothing. Requires the ``READ_STORE`` API permission.
        """
        return await self._post(
            f"/store/domains/{domain_id}/dns/check",
            cast_to=StoreDNSCheck,
            options=options,
        )

    async def microsoft_consent(
        self,
        domain_id: str,
        *,
        order_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreConsentLink:
        """Get the link where a domain's Microsoft 365 administrator approves Warmbly.

        Needed while a mailbox reports ``action_required``
        ``microsoft_consent``. Nothing changes until the administrator
        approves. Requires the ``MANAGE_STORE`` API permission.

        Args:
            order_id: The order the approval is started from, which the
                administrator lands back on.
        """
        return await self._post(
            f"/store/domains/{domain_id}/microsoft-consent",
            cast_to=StoreConsentLink,
            body=drop_not_given({"order_id": order_id}),
            options=options,
        )

    def list_mailboxes(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[StoreMailbox]:
        """List purchased mailboxes (auto-paginating).

        Requires the ``READ_STORE`` API permission.

        Args:
            limit: Page size, 1 to 100.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/store/mailboxes",
            model=StoreMailbox,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def update_mailbox(
        self,
        mailbox_id: str,
        *,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> StoreMailbox:
        """Change a purchased mailbox's sender name.

        Requires the ``MANAGE_STORE`` API permission. A name that breaks the
        naming rules answers ``400`` ``invalid_name``.
        """
        return await self._patch(
            f"/store/mailboxes/{mailbox_id}",
            cast_to=StoreMailbox,
            body=drop_not_given({"first_name": first_name, "last_name": last_name}),
            options=options,
        )

    async def set_mailbox_photo(
        self,
        mailbox_id: str,
        *,
        photo_id: str,
        options: RequestOptions | None = None,
    ) -> StoreMailbox:
        """Set a purchased mailbox's profile photo at Google or Microsoft.

        Requires the ``MANAGE_STORE`` API permission.

        Args:
            photo_id: A photo from :meth:`upload_photo` or
                :meth:`copy_profile_photo`.
        """
        return await self._put(
            f"/store/mailboxes/{mailbox_id}/photo",
            cast_to=StoreMailbox,
            body={"photo_id": photo_id},
            options=options,
        )

    async def cancel_mailbox(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> StoreMailbox:
        """Cancel a purchased mailbox at the end of its paid month.

        The answer carries ``cancels_at``. Requires the ``MANAGE_STORE`` API
        permission, and the member's ``manage_billing``.
        """
        return await self._delete(
            f"/store/mailboxes/{mailbox_id}", cast_to=StoreMailbox, options=options
        )

    async def resume_mailbox(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> StoreMailbox:
        """Undo a pending cancellation, so the mailbox keeps billing monthly.

        Requires the ``MANAGE_STORE`` API permission, and the member's
        ``manage_billing``. A mailbox that is not set to cancel answers
        ``409`` ``mailbox_not_cancellable``.
        """
        return await self._post(
            f"/store/mailboxes/{mailbox_id}/resume",
            cast_to=StoreMailbox,
            options=options,
        )

    async def mailbox_sign_in(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> StoreSignIn:
        """Show a purchased mailbox's sign-in (the admin console's, for the admin mailbox).

        Requires the ``MANAGE_STORE`` API permission. The server keeps no copy
        of the answer, and asking again returns the same sign-in, so a retry
        is safe. A mailbox without one answers ``409``
        ``sign_in_unavailable``.
        """
        return await self._post(
            f"/store/mailboxes/{mailbox_id}/sign-in",
            cast_to=StoreSignIn,
            options=options,
        )

    async def upload_photo(
        self,
        *,
        file: bytes,
        filename: str = "photo.jpg",
        content_type: str = "image/jpeg",
        options: RequestOptions | None = None,
    ) -> StorePhoto:
        """Upload a mailbox profile photo, for a quote line or :meth:`set_mailbox_photo`.

        PNG or JPG, up to 2 MB and 2048 pixels on each side; anything else
        answers ``400`` ``photo_invalid``. A photo nothing uses is deleted
        after 24 hours. Requires the ``MANAGE_STORE`` API permission.

        Args:
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
            content_type: The image's MIME type.
        """
        return await self._client.request(
            cast_to=StorePhoto,
            method="POST",
            path="/store/photos",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def copy_profile_photo(
        self, *, options: RequestOptions | None = None
    ) -> StorePhoto:
        """Copy the calling member's own profile photo for use on mailboxes.

        Answers ``404`` ``profile_photo_missing`` when the member has none.
        Requires the ``MANAGE_STORE`` API permission.
        """
        return await self._post(
            "/store/photos",
            cast_to=StorePhoto,
            body={"from": "profile"},
            options=options,
        )

    async def retrieve_photo(
        self, photo_id: str, *, options: RequestOptions | None = None
    ) -> bytes:
        """Download an uploaded photo as JPEG bytes.

        Requires the ``READ_STORE`` API permission.
        """
        return await self._get(
            f"/store/photos/{photo_id}", cast_to=bytes, options=options
        )
