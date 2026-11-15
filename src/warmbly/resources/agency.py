"""The ``agency`` resource: the ``/v1/agency`` route group.

An agency is a company that runs many client workspaces from one account: its
staff, its client list, a shared monthly send pool and AI balance, a
cross-client inbox and overview, migrations in from other outreach tools, and
the white-label brand every client inherits.

Agency API keys
---------------
These routes take an **agency API key** (prefix ``wmagency_``), created by an
agency owner or admin from a signed-in session. On ``/agency`` routes the key
acts on its own agency only: pass that agency's id as ``agency_id`` (a
different id answers ``404 agency_not_found``). Each method names the agency
permission bit the key needs (``AGENCY_READ``, ``AGENCY_MANAGE_CLIENTS``,
``AGENCY_READ_USAGE``, ``AGENCY_TRANSFER_AI`` or ``AGENCY_MIGRATE``); a key
without it gets ``403``. A workspace API key (``wmbly_``) or an OAuth app token
is refused on every ``/agency`` route with ``403 agency_credential_required``.

Some routes (attaching and detaching clients, moving AI balance) demand a
recently re-authenticated session from a browser user. API keys are exempt
from that check, so the methods here work with an agency key as-is.

Acting inside a client workspace
--------------------------------
Every other resource (``client.campaigns``, ``client.unibox``, ...) is
workspace-scoped. An agency key reaches one of its clients' workspaces by
naming it in the ``Warmbly-Organization`` header, either for the whole
client::

    agency = Warmbly(api_key="wmagency_...")
    acme = Warmbly(api_key="wmagency_...", organization="<client org id>")
    acme.campaigns.list()

or for a single call::

    agency.campaigns.list(
        options={"headers": {"Warmbly-Organization": "<client org id>"}}
    )

Without the header a workspace route answers ``400`` asking for it. The key's
creator must still be an accepted member of that client workspace, and only
the key's workspace permission bits apply there.

Agency migrations return the same
:class:`~warmbly.resources.migrations.Migration` objects as
``client.migrations``, but each ``target`` maps a source workspace onto a
client workspace (an existing one, or a new one created on start). Mailbox
passwords the source tool returns are only used for a migration created from
a signed-in session, so through an agency key such mailboxes land in
``followup.reconnect``.

Agency administration that changes billing, staff, vendor accounts, brand
settings or the agency's own API keys is session-only and not exposed here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given
from .migrations import Migration, MigrationProvider
from .plans import Plan
from .unibox import Message, MessagePreview

__all__ = [
    "Agency",
    "AgencyAIBalance",
    "AgencyAIClient",
    "AgencyAITopUpInfo",
    "AgencyAITransfer",
    "AgencyAttention",
    "AgencyBrand",
    "AgencyBrandSettings",
    "AgencyClient",
    "AgencyClientAdvisor",
    "AgencyClientCampaigns",
    "AgencyClientInbox",
    "AgencyClientMailboxes",
    "AgencyClientUsage",
    "AgencyDNSRecord",
    "AgencyDetail",
    "AgencyGrant",
    "AgencyInboxMessage",
    "AgencyInboxThread",
    "AgencyInvitation",
    "AgencyList",
    "AgencyMailbox",
    "AgencyMember",
    "AgencyOverview",
    "AgencyOverviewClient",
    "AgencyOverviewTotals",
    "AgencyPlan",
    "AgencyPlanList",
    "AgencyPortalDomain",
    "AgencyPortalTheme",
    "AgencyPoweredBy",
    "AgencyRecord",
    "AgencyStaff",
    "AgencyUsage",
    "AsyncAgency",
]


# -- agency, plans, staff ---------------------------------------------------


class AgencyPlan(Plan):
    """A plan sold to agencies.

    ``monthly_send_pool`` is the sends shared by all clients each period
    (``0`` is an agency plan with no pool cap) and ``agency_ai_allowance_usd``
    what the shared AI balance refills to each period. Both fields live on
    :class:`~warmbly.resources.plans.Plan`.
    """


class AgencyGrant(BaseModel):
    """A plan an operator gave the agency; ``until`` is ``None`` for no end."""

    plan_id: str | None = None
    until: str | None = None


class AgencyRecord(BaseModel):
    """One agency.

    ``status`` is the subscription status: ``trialing``, ``active``,
    ``past_due``, ``canceled``, ``unpaid``, ``incomplete``,
    ``incomplete_expired`` or ``paused``. ``role`` is the caller's role
    (``owner``, ``admin`` or ``member``) when listed for a user, and
    ``billing_interval`` is ``month`` or ``year`` while a subscription is in
    force.
    """

    id: str
    name: str | None = None
    owner_user_id: str | None = None
    plan_id: str | None = None
    status: str | None = None
    current_period_start: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    plan: AgencyPlan | None = None
    role: str | None = None
    client_count: int | None = None
    has_billing: bool | None = None
    granted: AgencyGrant | None = None
    billing_interval: str | None = None


class AgencyList(BaseModel):
    """The agencies the caller can see.

    An agency API key sees exactly one: its own. ``billing_enabled`` is
    ``False`` on a self-hosted install without billing.
    """

    data: Sequence[AgencyRecord] = []
    billing_enabled: bool | None = None


class AgencyPlanList(BaseModel):
    """The agency plan catalog."""

    data: Sequence[AgencyPlan] = []
    billing_enabled: bool | None = None


class AgencyDetail(BaseModel):
    """One agency and whether billing is enabled on this install."""

    agency: AgencyRecord | None = None
    billing_enabled: bool | None = None


class AgencyMember(BaseModel):
    """One staff member; ``role`` is ``owner``, ``admin`` or ``member``."""

    agency_id: str | None = None
    user_id: str
    role: str | None = None
    created_at: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class AgencyInvitation(BaseModel):
    """Staff invited by an address no account uses yet."""

    id: str
    agency_id: str | None = None
    email: str | None = None
    role: str | None = None
    invited_by: str | None = None
    expires_at: str | None = None
    created_at: str | None = None


class AgencyStaff(BaseModel):
    """The agency's staff and its pending staff invitations."""

    data: Sequence[AgencyMember] = []
    invitations: Sequence[AgencyInvitation] = []


# -- clients, usage, AI balance --------------------------------------------


class AgencyClient(BaseModel):
    """One client workspace of the agency.

    ``monthly_send_limit`` caps the client's share of the send pool per period
    and ``monthly_ai_limit_usd`` its spend from the agency's AI balance; both
    are ``None`` when uncapped.
    """

    organization_id: str
    agency_id: str | None = None
    monthly_send_limit: int | None = None
    monthly_ai_limit_usd: float | None = None
    added_at: str | None = None
    added_by: str | None = None
    name: str | None = None
    slug: str | None = None
    avatar_url: str | None = None
    owner_user_id: str | None = None


class AgencyClientUsage(BaseModel):
    """One client's sends from the pool this period."""

    organization_id: str
    name: str | None = None
    used: int | None = None
    monthly_send_limit: int | None = None


class AgencyUsage(BaseModel):
    """The shared monthly send pool.

    ``total`` is ``pool_size`` plus ``topups``; ``projected`` extrapolates
    this period's use to its end. ``topup_sends`` and ``topup_price_cents``
    describe one top-up pack.
    """

    unlimited: bool | None = None
    period_start: str | None = None
    period_end: str | None = None
    days_left: int | None = None
    pool_size: int | None = None
    topups: int | None = None
    total: int | None = None
    used: int | None = None
    remaining: int | None = None
    projected: int | None = None
    clients: Sequence[AgencyClientUsage] = []
    topup_sends: int | None = None
    topup_price_cents: int | None = None


class AgencyAIClient(BaseModel):
    """One client's share of the agency AI balance this period."""

    organization_id: str
    name: str | None = None
    spent_usd: float | None = None
    moved_usd: float | None = None
    monthly_ai_limit_usd: float | None = None


class AgencyAITopUpInfo(BaseModel):
    """The range a purchase of agency AI balance may take."""

    min_usd: float | None = None
    max_usd: float | None = None
    presets_usd: Sequence[int] = []
    default_usd: int | None = None


class AgencyAIBalance(BaseModel):
    """The agency's shared AI balance.

    The period allowance refills each period; purchased money never expires.
    ``bought_this_period_usd`` is what was bought this period, ``moved_usd``
    what was moved into client workspaces. ``unmetered`` is ``True`` on a
    self-hosted install where AI is not charged.
    """

    unmetered: bool | None = None
    period_start: str | None = None
    period_end: str | None = None
    allowance_usd: float | None = None
    allowance_left_usd: float | None = None
    purchased_usd: float | None = None
    bought_this_period_usd: float | None = None
    spent_usd: float | None = None
    moved_usd: float | None = None
    balance_usd: float | None = None
    clients: Sequence[AgencyAIClient] = []
    top_up: AgencyAITopUpInfo | None = None


class AgencyAITransfer(BaseModel):
    """The result of moving agency AI balance into a client's own balance."""

    amount_usd: float | None = None
    agency_balance_usd: float | None = None
    workspace_balance_usd: float | None = None


# -- overview, mailboxes, inbox ---------------------------------------------


class AgencyClientCampaigns(BaseModel):
    """A client's campaign activity (needs ``view_campaigns`` there)."""

    active: int | None = None
    paused_by_limits: int | None = None
    paused_by_billing: int | None = None
    sent_today: int | None = None
    sent_7d: int | None = None
    bounced_7d: int | None = None
    bounce_rate_7d: float | None = None
    positive_replies_7d: int | None = None


class AgencyClientInbox(BaseModel):
    """A client's unanswered human mail (needs ``access_unibox`` there)."""

    replies_waiting: int | None = None


class AgencyClientMailboxes(BaseModel):
    """A client's mailbox health (needs ``view_campaigns`` there)."""

    total: int | None = None
    disconnected: int | None = None
    erroring: int | None = None
    watch: int | None = None
    throttled: int | None = None
    quarantined: int | None = None
    blocked: int | None = None


class AgencyClientAdvisor(BaseModel):
    """A client's open Advisor findings (needs ``view_analytics`` there)."""

    critical: int | None = None
    high: int | None = None
    medium: int | None = None
    low: int | None = None


class AgencyOverviewClient(BaseModel):
    """One client row on the agency overview.

    ``access`` is ``full``, ``restricted`` or ``none`` (the caller is not a
    member). A section is ``None`` when the caller lacks the permission it
    needs in that workspace.
    """

    organization_id: str
    name: str | None = None
    avatar_url: str | None = None
    access: str | None = None
    manage_mailboxes: bool | None = None
    pool_used: int | None = None
    monthly_send_limit: int | None = None
    campaigns: AgencyClientCampaigns | None = None
    inbox: AgencyClientInbox | None = None
    mailboxes: AgencyClientMailboxes | None = None
    advisor: AgencyClientAdvisor | None = None


class AgencyOverviewTotals(BaseModel):
    """What the caller can see, added up across clients."""

    clients: int | None = None
    sent_today: int | None = None
    replies_waiting: int | None = None
    positive_replies_7d: int | None = None
    active_campaigns: int | None = None
    mailboxes: int | None = None
    mailbox_problems: int | None = None


class AgencyAttention(BaseModel):
    """One item on the overview's attention list.

    ``kind`` is ``mailbox_disconnected``, ``mailbox_held``, ``bounce_spike``,
    ``campaigns_paused_limits``, ``campaigns_paused_billing``,
    ``client_cap_near`` or ``pool_low``. ``organization_id`` is ``None`` for
    the agency itself. ``rate`` is the bounce rate for ``bounce_spike`` and
    the share of the cap used for ``client_cap_near``.
    """

    kind: str | None = None
    severity: str | None = None
    organization_id: str | None = None
    client_name: str | None = None
    count: int | None = None
    rate: float | None = None


class AgencyOverview(BaseModel):
    """The agency home: the pool, totals, problems first, then every client."""

    generated_at: str | None = None
    usage: AgencyUsage | None = None
    totals: AgencyOverviewTotals | None = None
    attention: Sequence[AgencyAttention] = []
    clients: Sequence[AgencyOverviewClient] = []


class AgencyMailbox(BaseModel):
    """One client mailbox in the agency's mailbox list.

    ``client`` is the client workspace's name. ``warmup_state`` is ``watch``,
    ``throttled``, ``quarantined`` or ``blocked``, and ``None`` in good
    standing. ``vendor`` is the inbox vendor it was imported from, if any.
    """

    id: str
    organization_id: str | None = None
    client: str | None = None
    email: str | None = None
    name: str | None = None
    provider: str | None = None
    status: str | None = None
    erroring: bool | None = None
    warmup: bool | None = None
    warmup_state: str | None = None
    vendor: str | None = None
    campaign_limit: int | None = None
    created_at: str | None = None


class AgencyInboxThread(BaseModel):
    """One conversation in the cross-client inbox: its newest message."""

    organization_id: str
    id: str
    email_id: str | None = None
    thread_id: str | None = None
    from_addr: Sequence[str] = []
    to_addr: Sequence[str] = []
    subject: str | None = None
    snippet: str | None = None
    internal_date: str | None = None
    seen: bool | None = None
    message_count: int | None = None
    has_unread: bool | None = None


class AgencyInboxMessage(Message):
    """One client message with its body, read without marking it read.

    Adds the mailbox (``email_id``) and canonical ``folder`` to
    :class:`~warmbly.resources.unibox.Message`.
    """

    email_id: str | None = None
    folder: str | None = None


# -- brand ------------------------------------------------------------------


class AgencyBrandSettings(BaseModel):
    """The agency's stored brand."""

    display_name: str | None = None
    logo_url: str | None = None
    accent_color: str | None = None
    website_url: str | None = None
    hide_powered_by: bool | None = None
    updated_at: str | None = None
    updated_by: str | None = None


class AgencyDNSRecord(BaseModel):
    """A DNS record the portal domain still needs."""

    purpose: str | None = None
    type: str | None = None
    name: str | None = None
    value: str | None = None
    ok: bool | None = None
    optional: bool | None = None


class AgencyPortalDomain(BaseModel):
    """The agency's portal domain and its DNS verification state.

    The fields share their names with the forms-domain status. ``status`` is
    ``verified``, ``unset``, ``no_target``, ``pending``, ``not_found``,
    ``wrong_target``, ``proof_missing`` or ``lookup_error``.
    """

    forms_domain: str | None = None
    forms_domain_verified: bool | None = None
    forms_domain_verified_at: str | None = None
    cname_target: str | None = None
    txt_name: str | None = None
    txt_value: str | None = None
    status: str | None = None
    message: str | None = None
    observed: str | None = None
    forms_host_unresolvable: bool | None = None
    edge_records: Sequence[AgencyDNSRecord] = []


class AgencyPoweredBy(BaseModel):
    """The deployment's attribution."""

    name: str | None = None
    url: str | None = None


class AgencyPortalTheme(BaseModel):
    """The portal theme; an empty field means the default.

    ``font`` is ``system``, ``geometric`` or ``serif``; ``corners`` is
    ``sharp`` or ``round``; ``appearance`` is ``light`` or ``dark``;
    ``sign_in_layout`` is ``split`` or ``cover``; ``sign_in_background`` is
    ``accent``, ``dark`` or ``image``.
    """

    font: str | None = None
    corners: str | None = None
    appearance: str | None = None
    sign_in_layout: str | None = None
    sign_in_background: str | None = None
    sign_in_heading: str | None = None
    sign_in_message: str | None = None
    support_email: str | None = None
    support_url: str | None = None
    terms_url: str | None = None
    privacy_url: str | None = None


class AgencyBrand(BaseModel):
    """The agency's white-label brand, inherited by every client workspace.

    ``full_white_label`` reports a plan that allows it; ``can_manage`` whether
    the caller may change it (always from a session). ``portal_sign_in`` is
    ``portal`` (clients sign in on the agency's domain) or ``warmbly``.
    """

    brand: AgencyBrandSettings | None = None
    full_white_label: bool | None = None
    can_manage: bool | None = None
    portal_domain: AgencyPortalDomain | None = None
    portal_base_url: str | None = None
    powered_by: AgencyPoweredBy | None = None
    portal_sign_in: str | None = None
    icon_url: str | None = None
    sign_in_image_url: str | None = None
    theme: AgencyPortalTheme | None = None


# -- request builders -------------------------------------------------------


def _ids(values: NotGivenOr[Sequence[str]]) -> NotGivenOr[str]:
    """Comma-join an id list for a query parameter."""
    return ",".join(values) if is_given(values) else NOT_GIVEN


def _flag(value: NotGivenOr[bool]) -> NotGivenOr[str]:
    """The server reads a filter as on only when it is the string ``true``."""
    return "true" if value is True else NOT_GIVEN


def _mailbox_query(
    client: NotGivenOr[Sequence[str]],
    q: NotGivenOr[str],
    attention: NotGivenOr[bool],
    limit: NotGivenOr[int],
    cursor: NotGivenOr[str],
) -> dict[str, object]:
    return drop_not_given(
        {
            "client": _ids(client),
            "q": q,
            "attention": _flag(attention),
            "limit": limit,
            "cursor": cursor,
        }
    )


def _inbox_query(
    client: NotGivenOr[Sequence[str]],
    unread: NotGivenOr[bool],
    needs_reply: NotGivenOr[bool],
    positive: NotGivenOr[bool],
    q: NotGivenOr[str],
    limit: NotGivenOr[int],
    cursor: NotGivenOr[str],
) -> dict[str, object]:
    return drop_not_given(
        {
            "client": _ids(client),
            "unread": _flag(unread),
            "needs_reply": _flag(needs_reply),
            "positive": _flag(positive),
            "q": q,
            "limit": limit,
            "cursor": cursor,
        }
    )


def _start_body(
    kinds: Sequence[str],
    in_flight: NotGivenOr[str],
    campaign_ids: NotGivenOr[Sequence[str]],
    skip_finished: NotGivenOr[bool],
    warmup: NotGivenOr[bool],
    targets: NotGivenOr[Sequence[Mapping[str, Any]]],
) -> dict[str, object]:
    migration_options = drop_not_given(
        {
            "kinds": [str(kind) for kind in kinds],
            "in_flight": in_flight,
            "campaign_ids": (
                [str(c) for c in campaign_ids] if is_given(campaign_ids) else NOT_GIVEN
            ),
            "skip_finished": skip_finished,
            "warmup": warmup,
        }
    )
    return drop_not_given(
        {
            "options": migration_options,
            "targets": ([dict(t) for t in targets] if is_given(targets) else NOT_GIVEN),
        }
    )


# -- resources --------------------------------------------------------------


class Agency(SyncAPIResource):
    """Synchronous ``agency`` resource."""

    # -- agency, plans, staff

    def list(self, *, options: RequestOptions | None = None) -> AgencyList:
        """List the caller's agencies; an agency key sees only its own.

        Needs ``AGENCY_READ``.
        """
        return self._get("/agency", cast_to=AgencyList, options=options)

    def list_plans(self, *, options: RequestOptions | None = None) -> AgencyPlanList:
        """List the plans sold to agencies. Needs ``AGENCY_READ``."""
        return self._get("/agency/plans", cast_to=AgencyPlanList, options=options)

    def retrieve(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyDetail:
        """Retrieve one agency (under ``agency``). Needs ``AGENCY_READ``."""
        return self._get(f"/agency/{agency_id}", cast_to=AgencyDetail, options=options)

    def list_members(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyStaff:
        """List the agency's staff and pending invitations. Needs ``AGENCY_READ``."""
        return self._get(
            f"/agency/{agency_id}/members", cast_to=AgencyStaff, options=options
        )

    # -- clients

    def list_clients(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[AgencyClient]:
        """List the agency's client workspaces.

        The list is returned in full, so the page never has a next page.
        Needs ``AGENCY_READ``.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/clients", model=AgencyClient, options=options
        )

    def create_client(
        self,
        agency_id: str,
        *,
        name: str,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AgencyClient:
        """Create a new client workspace under the agency.

        The workspace is owned by the agency's owner. Needs
        ``AGENCY_MANAGE_CLIENTS``.

        Args:
            agency_id: The agency.
            name: The new workspace's name.
            timezone: An IANA timezone for the workspace.
        """
        return self._post(
            f"/agency/{agency_id}/clients",
            cast_to=AgencyClient,
            body=drop_not_given({"name": name, "timezone": timezone}),
            options=options,
        )

    def attach_client(
        self,
        agency_id: str,
        *,
        organization_id: str,
        options: RequestOptions | None = None,
    ) -> AgencyClient:
        """Bring an existing workspace under the agency.

        The caller (for a key, the staff member who created it) must own the
        workspace. Needs ``AGENCY_MANAGE_CLIENTS``.

        Args:
            agency_id: The agency.
            organization_id: The workspace to attach.
        """
        return self._post(
            f"/agency/{agency_id}/clients/attach",
            cast_to=AgencyClient,
            body={"organization_id": organization_id},
            options=options,
        )

    def update_client(
        self,
        agency_id: str,
        organization_id: str,
        *,
        monthly_send_limit: NotGivenOr[int | None] = NOT_GIVEN,
        monthly_ai_limit_usd: NotGivenOr[float | None] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AgencyClient:
        """Set a client's monthly send cap, AI spend cap, or both.

        Pass at least one; ``None`` clears that cap. Needs
        ``AGENCY_MANAGE_CLIENTS``.

        Args:
            agency_id: The agency.
            organization_id: The client workspace.
            monthly_send_limit: Sends per period from the shared pool.
            monthly_ai_limit_usd: Dollars per period from the agency AI
                balance, rounded to cents.
        """
        return self._patch(
            f"/agency/{agency_id}/clients/{organization_id}",
            cast_to=AgencyClient,
            body=drop_not_given(
                {
                    "monthly_send_limit": monthly_send_limit,
                    "monthly_ai_limit_usd": monthly_ai_limit_usd,
                }
            ),
            options=options,
        )

    def detach_client(
        self,
        agency_id: str,
        organization_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Take a client workspace out of the agency (``204 No Content``).

        Needs ``AGENCY_MANAGE_CLIENTS``.
        """
        return self._delete(
            f"/agency/{agency_id}/clients/{organization_id}",
            cast_to=type(None),
            options=options,
        )

    # -- usage and AI balance

    def usage(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyUsage:
        """The shared send pool this period. Needs ``AGENCY_READ_USAGE``."""
        return self._get(
            f"/agency/{agency_id}/usage", cast_to=AgencyUsage, options=options
        )

    def ai_balance(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyAIBalance:
        """The shared AI balance this period. Needs ``AGENCY_READ_USAGE``."""
        return self._get(
            f"/agency/{agency_id}/ai-balance", cast_to=AgencyAIBalance, options=options
        )

    def transfer_ai_balance(
        self,
        agency_id: str,
        organization_id: str,
        *,
        amount_usd: float,
        options: RequestOptions | None = None,
    ) -> AgencyAITransfer:
        """Move agency AI balance into a client workspace's own balance.

        The ``Idempotency-Key`` sent with the request makes a retry return the
        first transfer instead of moving the money twice. Needs
        ``AGENCY_TRANSFER_AI``.

        Args:
            agency_id: The agency.
            organization_id: The client workspace.
            amount_usd: Dollars to move, rounded to cents.
        """
        return self._post(
            f"/agency/{agency_id}/clients/{organization_id}/ai-balance",
            cast_to=AgencyAITransfer,
            body={"amount_usd": amount_usd},
            options=options,
        )

    # -- overview, mailboxes, inbox

    def overview(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyOverview:
        """The agency home: pool, totals, attention list and every client.

        Briefly cached per caller. Needs ``AGENCY_READ``.
        """
        return self._get(
            f"/agency/{agency_id}/overview", cast_to=AgencyOverview, options=options
        )

    def list_mailboxes(
        self,
        agency_id: str,
        *,
        client: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        attention: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AgencyMailbox]:
        """List mailboxes across clients, newest first (auto-paginating).

        Clients where the caller is restricted to selected mailboxes are left
        out. Needs ``AGENCY_READ``.

        Args:
            agency_id: The agency.
            client: Keep only these client workspace ids.
            q: Search text.
            attention: Keep only disconnected, erroring, quarantined or
                blocked mailboxes.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/mailboxes",
            model=AgencyMailbox,
            query=_mailbox_query(client, q, attention, limit, cursor),
            options=options,
        )

    def list_inbox(
        self,
        agency_id: str,
        *,
        client: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        unread: NotGivenOr[bool] = NOT_GIVEN,
        needs_reply: NotGivenOr[bool] = NOT_GIVEN,
        positive: NotGivenOr[bool] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AgencyInboxThread]:
        """List conversations across clients, newest first (auto-paginating).

        Needs ``AGENCY_READ`` and ``READ_UNIBOX``.

        Args:
            agency_id: The agency.
            client: Keep only these client workspace ids.
            unread: Only conversations with unread mail.
            needs_reply: Only conversations awaiting a reply.
            positive: Only conversations with a positive reply.
            q: Search text.
            limit: Page size.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/inbox",
            model=AgencyInboxThread,
            query=_inbox_query(client, unread, needs_reply, positive, q, limit, cursor),
            options=options,
        )

    def retrieve_inbox_thread(
        self,
        agency_id: str,
        *,
        organization_id: str,
        thread_id: str,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[MessagePreview]:
        """List one client conversation's messages, read-only (auto-paginating).

        Needs ``AGENCY_READ`` and ``READ_UNIBOX``.

        Args:
            agency_id: The agency.
            organization_id: The client workspace the thread belongs to.
            thread_id: The thread to expand.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/inbox/thread",
            model=MessagePreview,
            query=drop_not_given(
                {
                    "organization_id": organization_id,
                    "thread_id": thread_id,
                    "cursor": cursor,
                }
            ),
            options=options,
        )

    def retrieve_inbox_message(
        self,
        agency_id: str,
        message_id: str,
        *,
        organization_id: str,
        options: RequestOptions | None = None,
    ) -> AgencyInboxMessage:
        """Read one client message's body without marking it read.

        Needs ``AGENCY_READ`` and ``READ_UNIBOX``.

        Args:
            agency_id: The agency.
            message_id: The message.
            organization_id: The client workspace it belongs to.
        """
        return self._get(
            f"/agency/{agency_id}/inbox/messages/{message_id}",
            cast_to=AgencyInboxMessage,
            query={"organization_id": organization_id},
            options=options,
        )

    # -- brand

    def brand(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyBrand:
        """The agency's white-label brand and portal domain. Needs ``AGENCY_READ``."""
        return self._get(
            f"/agency/{agency_id}/brand", cast_to=AgencyBrand, options=options
        )

    # -- migrations

    def list_migration_providers(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[MigrationProvider]:
        """List the tools a migration can read from (single page).

        Needs ``AGENCY_MIGRATE``.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/migrations/providers",
            model=MigrationProvider,
            options=options,
        )

    def list_migrations(
        self,
        agency_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Migration]:
        """List the agency's migrations, newest first (auto-paginating).

        Needs ``AGENCY_MIGRATE``.

        Args:
            agency_id: The agency.
            limit: Page size, 1 to 100 (default 20).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/migrations",
            model=Migration,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    def create_migration(
        self,
        agency_id: str,
        *,
        provider: str,
        credentials: Sequence[Mapping[str, str]],
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Check the keys for another tool and start scanning it.

        The result starts in ``scanning``; poll :meth:`retrieve_migration`
        until it is ``ready``, then :meth:`start_migration`. Needs
        ``AGENCY_MIGRATE``.

        Args:
            agency_id: The agency.
            provider: The provider id from :meth:`list_migration_providers`.
            credentials: One mapping per key, keyed by the provider's field
                ``key`` names. A tool with a key per workspace takes several.
            label: A name for the migration.
        """
        return self._post(
            f"/agency/{agency_id}/migrations",
            cast_to=Migration,
            body=drop_not_given(
                {
                    "provider": provider,
                    "label": label,
                    "credentials": [dict(c) for c in credentials],
                }
            ),
            options=options,
        )

    def retrieve_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Retrieve one migration. Needs ``AGENCY_MIGRATE``."""
        return self._get(
            f"/agency/{agency_id}/migrations/{migration_id}",
            cast_to=Migration,
            options=options,
        )

    def start_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        kinds: Sequence[str],
        targets: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        in_flight: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        skip_finished: NotGivenOr[bool] = NOT_GIVEN,
        warmup: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Choose what to bring over, and into which clients, and start.

        Needs ``AGENCY_MIGRATE``. The key's own bits are also checked: a
        target that creates a client needs ``AGENCY_MANAGE_CLIENTS``, the
        ``campaigns`` kind ``WRITE_CAMPAIGNS`` and ``mailboxes``
        ``WRITE_EMAILS``.

        Args:
            agency_id: The agency.
            migration_id: The migration, in ``ready``.
            kinds: Any of ``mailboxes``, ``campaigns``, ``leads`` and
                ``blocklist``.
            targets: Where each source workspace goes: mappings of
                ``workspace_id`` and ``key``, plus ``organization_id`` (an
                existing client), ``create_name`` (a new client) or
                ``skip: True``.
            in_flight: ``restart`` or ``skip`` (default) for leads the old
                tool was part way through a sequence with.
            campaign_ids: Only these source campaigns; omit for all.
            skip_finished: Leave out completed or archived campaigns.
            warmup: Start warmup on mailboxes that connect.
        """
        return self._post(
            f"/agency/{agency_id}/migrations/{migration_id}/start",
            cast_to=Migration,
            body=_start_body(
                kinds, in_flight, campaign_ids, skip_finished, warmup, targets
            ),
            options=options,
        )

    def cancel_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Cancel a migration and wipe its keys. Needs ``AGENCY_MIGRATE``."""
        return self._post(
            f"/agency/{agency_id}/migrations/{migration_id}/cancel",
            cast_to=Migration,
            options=options,
        )

    def link_migration_senders(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Attach mailboxes connected since the run to the draft campaigns.

        Needs ``AGENCY_MIGRATE``, and the key's ``WRITE_CAMPAIGNS`` bit.
        """
        return self._post(
            f"/agency/{agency_id}/migrations/{migration_id}/link-senders",
            cast_to=Migration,
            options=options,
        )

    def dismiss_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Dismiss a migration that is not running (``204 No Content``).

        Needs ``AGENCY_MIGRATE``.
        """
        return self._delete(
            f"/agency/{agency_id}/migrations/{migration_id}",
            cast_to=type(None),
            options=options,
        )


class AsyncAgency(AsyncAPIResource):
    """Asynchronous ``agency`` resource."""

    # -- agency, plans, staff

    async def list(self, *, options: RequestOptions | None = None) -> AgencyList:
        """List the caller's agencies; an agency key sees only its own.

        Needs ``AGENCY_READ``.
        """
        return await self._get("/agency", cast_to=AgencyList, options=options)

    async def list_plans(
        self, *, options: RequestOptions | None = None
    ) -> AgencyPlanList:
        """List the plans sold to agencies. Needs ``AGENCY_READ``."""
        return await self._get("/agency/plans", cast_to=AgencyPlanList, options=options)

    async def retrieve(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyDetail:
        """Retrieve one agency (under ``agency``). Needs ``AGENCY_READ``."""
        return await self._get(
            f"/agency/{agency_id}", cast_to=AgencyDetail, options=options
        )

    async def list_members(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyStaff:
        """List the agency's staff and pending invitations. Needs ``AGENCY_READ``."""
        return await self._get(
            f"/agency/{agency_id}/members", cast_to=AgencyStaff, options=options
        )

    # -- clients

    def list_clients(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[AgencyClient]:
        """List the agency's client workspaces.

        The list is returned in full, so the page never has a next page.
        Needs ``AGENCY_READ``.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/clients", model=AgencyClient, options=options
        )

    async def create_client(
        self,
        agency_id: str,
        *,
        name: str,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AgencyClient:
        """Create a new client workspace under the agency.

        The workspace is owned by the agency's owner. Needs
        ``AGENCY_MANAGE_CLIENTS``.

        Args:
            agency_id: The agency.
            name: The new workspace's name.
            timezone: An IANA timezone for the workspace.
        """
        return await self._post(
            f"/agency/{agency_id}/clients",
            cast_to=AgencyClient,
            body=drop_not_given({"name": name, "timezone": timezone}),
            options=options,
        )

    async def attach_client(
        self,
        agency_id: str,
        *,
        organization_id: str,
        options: RequestOptions | None = None,
    ) -> AgencyClient:
        """Bring an existing workspace under the agency.

        The caller (for a key, the staff member who created it) must own the
        workspace. Needs ``AGENCY_MANAGE_CLIENTS``.

        Args:
            agency_id: The agency.
            organization_id: The workspace to attach.
        """
        return await self._post(
            f"/agency/{agency_id}/clients/attach",
            cast_to=AgencyClient,
            body={"organization_id": organization_id},
            options=options,
        )

    async def update_client(
        self,
        agency_id: str,
        organization_id: str,
        *,
        monthly_send_limit: NotGivenOr[int | None] = NOT_GIVEN,
        monthly_ai_limit_usd: NotGivenOr[float | None] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AgencyClient:
        """Set a client's monthly send cap, AI spend cap, or both.

        Pass at least one; ``None`` clears that cap. Needs
        ``AGENCY_MANAGE_CLIENTS``.

        Args:
            agency_id: The agency.
            organization_id: The client workspace.
            monthly_send_limit: Sends per period from the shared pool.
            monthly_ai_limit_usd: Dollars per period from the agency AI
                balance, rounded to cents.
        """
        return await self._patch(
            f"/agency/{agency_id}/clients/{organization_id}",
            cast_to=AgencyClient,
            body=drop_not_given(
                {
                    "monthly_send_limit": monthly_send_limit,
                    "monthly_ai_limit_usd": monthly_ai_limit_usd,
                }
            ),
            options=options,
        )

    async def detach_client(
        self,
        agency_id: str,
        organization_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Take a client workspace out of the agency (``204 No Content``).

        Needs ``AGENCY_MANAGE_CLIENTS``.
        """
        return await self._delete(
            f"/agency/{agency_id}/clients/{organization_id}",
            cast_to=type(None),
            options=options,
        )

    # -- usage and AI balance

    async def usage(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyUsage:
        """The shared send pool this period. Needs ``AGENCY_READ_USAGE``."""
        return await self._get(
            f"/agency/{agency_id}/usage", cast_to=AgencyUsage, options=options
        )

    async def ai_balance(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyAIBalance:
        """The shared AI balance this period. Needs ``AGENCY_READ_USAGE``."""
        return await self._get(
            f"/agency/{agency_id}/ai-balance", cast_to=AgencyAIBalance, options=options
        )

    async def transfer_ai_balance(
        self,
        agency_id: str,
        organization_id: str,
        *,
        amount_usd: float,
        options: RequestOptions | None = None,
    ) -> AgencyAITransfer:
        """Move agency AI balance into a client workspace's own balance.

        The ``Idempotency-Key`` sent with the request makes a retry return the
        first transfer instead of moving the money twice. Needs
        ``AGENCY_TRANSFER_AI``.

        Args:
            agency_id: The agency.
            organization_id: The client workspace.
            amount_usd: Dollars to move, rounded to cents.
        """
        return await self._post(
            f"/agency/{agency_id}/clients/{organization_id}/ai-balance",
            cast_to=AgencyAITransfer,
            body={"amount_usd": amount_usd},
            options=options,
        )

    # -- overview, mailboxes, inbox

    async def overview(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyOverview:
        """The agency home: pool, totals, attention list and every client.

        Briefly cached per caller. Needs ``AGENCY_READ``.
        """
        return await self._get(
            f"/agency/{agency_id}/overview", cast_to=AgencyOverview, options=options
        )

    def list_mailboxes(
        self,
        agency_id: str,
        *,
        client: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        attention: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AgencyMailbox]:
        """List mailboxes across clients, newest first (auto-paginating).

        Clients where the caller is restricted to selected mailboxes are left
        out. Needs ``AGENCY_READ``.

        Args:
            agency_id: The agency.
            client: Keep only these client workspace ids.
            q: Search text.
            attention: Keep only disconnected, erroring, quarantined or
                blocked mailboxes.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/mailboxes",
            model=AgencyMailbox,
            query=_mailbox_query(client, q, attention, limit, cursor),
            options=options,
        )

    def list_inbox(
        self,
        agency_id: str,
        *,
        client: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        unread: NotGivenOr[bool] = NOT_GIVEN,
        needs_reply: NotGivenOr[bool] = NOT_GIVEN,
        positive: NotGivenOr[bool] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AgencyInboxThread]:
        """List conversations across clients, newest first (auto-paginating).

        Needs ``AGENCY_READ`` and ``READ_UNIBOX``.

        Args:
            agency_id: The agency.
            client: Keep only these client workspace ids.
            unread: Only conversations with unread mail.
            needs_reply: Only conversations awaiting a reply.
            positive: Only conversations with a positive reply.
            q: Search text.
            limit: Page size.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/inbox",
            model=AgencyInboxThread,
            query=_inbox_query(client, unread, needs_reply, positive, q, limit, cursor),
            options=options,
        )

    def retrieve_inbox_thread(
        self,
        agency_id: str,
        *,
        organization_id: str,
        thread_id: str,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[MessagePreview]:
        """List one client conversation's messages, read-only (auto-paginating).

        Needs ``AGENCY_READ`` and ``READ_UNIBOX``.

        Args:
            agency_id: The agency.
            organization_id: The client workspace the thread belongs to.
            thread_id: The thread to expand.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/inbox/thread",
            model=MessagePreview,
            query=drop_not_given(
                {
                    "organization_id": organization_id,
                    "thread_id": thread_id,
                    "cursor": cursor,
                }
            ),
            options=options,
        )

    async def retrieve_inbox_message(
        self,
        agency_id: str,
        message_id: str,
        *,
        organization_id: str,
        options: RequestOptions | None = None,
    ) -> AgencyInboxMessage:
        """Read one client message's body without marking it read.

        Needs ``AGENCY_READ`` and ``READ_UNIBOX``.

        Args:
            agency_id: The agency.
            message_id: The message.
            organization_id: The client workspace it belongs to.
        """
        return await self._get(
            f"/agency/{agency_id}/inbox/messages/{message_id}",
            cast_to=AgencyInboxMessage,
            query={"organization_id": organization_id},
            options=options,
        )

    # -- brand

    async def brand(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AgencyBrand:
        """The agency's white-label brand and portal domain. Needs ``AGENCY_READ``."""
        return await self._get(
            f"/agency/{agency_id}/brand", cast_to=AgencyBrand, options=options
        )

    # -- migrations

    def list_migration_providers(
        self, agency_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[MigrationProvider]:
        """List the tools a migration can read from (single page).

        Needs ``AGENCY_MIGRATE``.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/migrations/providers",
            model=MigrationProvider,
            options=options,
        )

    def list_migrations(
        self,
        agency_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Migration]:
        """List the agency's migrations, newest first (auto-paginating).

        Needs ``AGENCY_MIGRATE``.

        Args:
            agency_id: The agency.
            limit: Page size, 1 to 100 (default 20).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/agency/{agency_id}/migrations",
            model=Migration,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    async def create_migration(
        self,
        agency_id: str,
        *,
        provider: str,
        credentials: Sequence[Mapping[str, str]],
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Check the keys for another tool and start scanning it.

        The result starts in ``scanning``; poll :meth:`retrieve_migration`
        until it is ``ready``, then :meth:`start_migration`. Needs
        ``AGENCY_MIGRATE``.

        Args:
            agency_id: The agency.
            provider: The provider id from :meth:`list_migration_providers`.
            credentials: One mapping per key, keyed by the provider's field
                ``key`` names. A tool with a key per workspace takes several.
            label: A name for the migration.
        """
        return await self._post(
            f"/agency/{agency_id}/migrations",
            cast_to=Migration,
            body=drop_not_given(
                {
                    "provider": provider,
                    "label": label,
                    "credentials": [dict(c) for c in credentials],
                }
            ),
            options=options,
        )

    async def retrieve_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Retrieve one migration. Needs ``AGENCY_MIGRATE``."""
        return await self._get(
            f"/agency/{agency_id}/migrations/{migration_id}",
            cast_to=Migration,
            options=options,
        )

    async def start_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        kinds: Sequence[str],
        targets: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        in_flight: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        skip_finished: NotGivenOr[bool] = NOT_GIVEN,
        warmup: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Choose what to bring over, and into which clients, and start.

        Needs ``AGENCY_MIGRATE``. The key's own bits are also checked: a
        target that creates a client needs ``AGENCY_MANAGE_CLIENTS``, the
        ``campaigns`` kind ``WRITE_CAMPAIGNS`` and ``mailboxes``
        ``WRITE_EMAILS``.

        Args:
            agency_id: The agency.
            migration_id: The migration, in ``ready``.
            kinds: Any of ``mailboxes``, ``campaigns``, ``leads`` and
                ``blocklist``.
            targets: Where each source workspace goes: mappings of
                ``workspace_id`` and ``key``, plus ``organization_id`` (an
                existing client), ``create_name`` (a new client) or
                ``skip: True``.
            in_flight: ``restart`` or ``skip`` (default) for leads the old
                tool was part way through a sequence with.
            campaign_ids: Only these source campaigns; omit for all.
            skip_finished: Leave out completed or archived campaigns.
            warmup: Start warmup on mailboxes that connect.
        """
        return await self._post(
            f"/agency/{agency_id}/migrations/{migration_id}/start",
            cast_to=Migration,
            body=_start_body(
                kinds, in_flight, campaign_ids, skip_finished, warmup, targets
            ),
            options=options,
        )

    async def cancel_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Cancel a migration and wipe its keys. Needs ``AGENCY_MIGRATE``."""
        return await self._post(
            f"/agency/{agency_id}/migrations/{migration_id}/cancel",
            cast_to=Migration,
            options=options,
        )

    async def link_migration_senders(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Attach mailboxes connected since the run to the draft campaigns.

        Needs ``AGENCY_MIGRATE``, and the key's ``WRITE_CAMPAIGNS`` bit.
        """
        return await self._post(
            f"/agency/{agency_id}/migrations/{migration_id}/link-senders",
            cast_to=Migration,
            options=options,
        )

    async def dismiss_migration(
        self,
        agency_id: str,
        migration_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Dismiss a migration that is not running (``204 No Content``).

        Needs ``AGENCY_MIGRATE``.
        """
        return await self._delete(
            f"/agency/{agency_id}/migrations/{migration_id}",
            cast_to=type(None),
            options=options,
        )
