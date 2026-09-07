"""The ``plans`` resource: the read-only billing plan catalog.

Maps to ``GET /v1/plans``, which returns the whole catalog in one response
under a ``plans`` key. Plan objects are permissive
:class:`~warmbly._models.BaseModel` subclasses so additional pricing or feature
fields are preserved without a client upgrade.

Subscribing to a plan is a session-only flow (``/v1/subscription/*``) that an
API key or OAuth token cannot reach, so this resource is read-only by design.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions

__all__ = [
    "AsyncPlans",
    "Plan",
    "Plans",
]


class Plan(BaseModel):
    """A billing plan and the limits it carries.

    ``duration`` is the billing period the ``price`` covers and ``savings`` the
    percentage a yearly term saves against it. The ``max_*`` caps are ``None``
    where the plan sets none.

    Attributes:
        id: The plan identifier.
        name: The human-readable plan name.
        price: The list price for one ``duration``.
        discounted_price: The price actually charged, where a discount applies.
        duration: The billing period (e.g. ``"monthly"``, ``"yearly"``).
        savings: Percentage saved against paying per period.
        public: Whether the plan is offered on the pricing page.
        max_contacts: Contact-list ceiling.
        daily_emails: Campaign sends allowed per day.
        account_limit: Mailboxes the plan includes outright.
        ai_generation: Whether AI writing is included.
        monthly_credits: AI credits granted each month.
        dedicated_workers: Dedicated sending workers, if any.
        daily_campaign_limit: Per-campaign daily send ceiling.
        max_campaigns: Total campaigns allowed.
        max_active_campaigns: Campaigns that may run at once.
        max_team_members: Seats included.
        max_email_accounts: Mailboxes allowed.
        stripe_price_id: The Stripe price for the monthly term.
        stripe_price_id_yearly: The Stripe price for the yearly term.
        stripe_product_id: The Stripe product behind both.
        referral_reward_percent: Percentage of this plan's first-month-equivalent
            price a referrer earns when an invitee converts to it.
    """

    id: str
    name: str | None = None
    price: float | None = None
    discounted_price: float | None = None
    duration: str | None = None
    savings: int | None = None
    public: bool | None = None
    max_contacts: int | None = None
    daily_emails: int | None = None
    account_limit: int | None = None
    ai_generation: bool | None = None
    monthly_credits: int | None = None
    dedicated_workers: int | None = None
    daily_campaign_limit: int | None = None
    max_campaigns: int | None = None
    max_active_campaigns: int | None = None
    max_team_members: int | None = None
    max_email_accounts: int | None = None
    stripe_price_id: str | None = None
    stripe_price_id_yearly: str | None = None
    stripe_product_id: str | None = None
    referral_reward_percent: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Plans(SyncAPIResource):
    """Synchronous ``plans`` resource (read-only)."""

    def list(self, *, options: RequestOptions | None = None) -> SyncCursorPage[Plan]:
        """List the available billing plans.

        The catalog is returned in full, so the page never has a next page.

        Args:
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/plans", model=Plan, data_key="plans", options=options
        )


class AsyncPlans(AsyncAPIResource):
    """Asynchronous ``plans`` resource (read-only)."""

    def list(self, *, options: RequestOptions | None = None) -> AsyncPaginator[Plan]:
        """List the available billing plans.

        The catalog is returned in full, so the page never has a next page.

        Args:
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/plans", model=Plan, data_key="plans", options=options
        )
