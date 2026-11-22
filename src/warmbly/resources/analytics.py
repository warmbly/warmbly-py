"""The ``analytics`` resource: read-only reporting endpoints.

Maps to the ``/v1/analytics`` route group. Every method is a ``GET`` and most
accept an optional date range (``from_`` / ``to``, RFC3339). Results are
permissive :class:`~warmbly._models.BaseModel` subclasses (``extra="allow"``),
so additional or future fields the backend returns are preserved without a
client upgrade.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import Field

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "Analytics",
    "AnalyticsResult",
    "AsyncAnalytics",
    "DirectMailAnalytics",
    "DirectMailContact",
    "DirectMailDailyStats",
    "DirectMailMailboxStats",
    "DirectMailTracking",
    "DirectMailVolume",
    "InboxTagRow",
    "InboxTaggingReview",
    "InboxTaggingSummary",
]


class AnalyticsResult(BaseModel):
    """A permissive analytics report.

    Analytics endpoints return widely varying shapes (dashboards, time-series,
    comparison tables, usage counters). Rather than model each one rigidly, this
    object exposes a few commonly present fields and relies on ``extra="allow"``
    to retain everything else; access the raw payload via :meth:`to_dict`.

    Attributes:
        from_: The start of the reporting window (RFC3339), if echoed back.
        to: The end of the reporting window (RFC3339), if echoed back.
        interval: The bucketing interval (e.g. ``"day"``, ``"hour"``), if any.
        totals: Aggregate metrics for the window, if provided.
        series: Time-bucketed data points, if provided.
        data: A generic data array some endpoints return.
    """

    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    interval: str | None = None
    totals: dict[str, Any] | None = None
    series: Sequence[dict[str, Any]] | None = None
    data: Sequence[dict[str, Any]] | None = None


class DirectMailVolume(BaseModel):
    """How much hand-written mail was sent and heard back, measured from the
    synced mailbox.

    ``replied`` counts the outbound threads that got an inbound message back;
    ``bounced`` is excluded from it. ``median_reply_minutes`` is ``0`` when
    nothing has been answered.
    """

    sent: int | None = None
    received: int | None = None
    threads_started: int | None = None
    replied: int | None = None
    reply_rate: float | None = None
    bounced: int | None = None
    median_reply_minutes: int | None = None


class DirectMailTracking(BaseModel):
    """The opt-in half: opens and clicks for the mailboxes that track them.

    ``tracked_sent`` is the denominator for both rates; ``mailboxes_opted_in``
    of ``mailboxes_total`` says how much of the picture this covers.
    """

    mailboxes_opted_in: int | None = None
    mailboxes_total: int | None = None
    tracked_sent: int | None = None
    opened: int | None = None
    machine_opened: int | None = None
    clicked: int | None = None
    open_rate: float | None = None
    click_rate: float | None = None


class DirectMailDailyStats(BaseModel):
    """One day of hand-written mail volume."""

    date: str | None = None
    sent: int | None = None
    received: int | None = None


class DirectMailMailboxStats(BaseModel):
    """One mailbox's hand-written mail volume."""

    email_account_id: str | None = None
    email: str | None = None
    track_direct_mail: bool | None = None
    sent: int | None = None
    received: int | None = None


class DirectMailContact(BaseModel):
    """One correspondent, ranked by how much was sent to them."""

    email: str | None = None
    sent: int | None = None
    received: int | None = None
    last_at: str | None = None


class DirectMailAnalytics(BaseModel):
    """The hand-written-mail overview.

    ``period`` is ``7d``, ``30d`` or ``90d``.
    """

    period: str | None = None
    volume: DirectMailVolume | None = None
    tracking: DirectMailTracking | None = None
    daily_trend: Sequence[DirectMailDailyStats] = []
    mailboxes: Sequence[DirectMailMailboxStats] = []
    top_contacts: Sequence[DirectMailContact] = []


class InboxTagRow(BaseModel):
    """What automatic inbox tagging decided about one message, and how sure.

    ``kind``/``intent`` carry a confidence each; ``relevance`` is a score and
    ``priority`` a band. ``actions`` is what the workspace's switches let the
    verdict do. ``return_date`` (``YYYY-MM-DD``) is the out-of-office return
    date the model was asked to confirm, ``None`` when it was not asked.
    ``answers`` is the model's structured answers.
    """

    id: str
    message_id: str | None = None
    thread_id: str | None = None
    kind: str | None = None
    kind_confidence: float | None = None
    kind_source: str | None = None
    intent: str | None = None
    intent_confidence: float | None = None
    relevance: int | None = None
    priority: str | None = None
    needs_review: bool | None = None
    review_reason: str | None = None
    labels: Sequence[str] = []
    answers: dict[str, Any] | None = None
    model: str | None = None
    input_tokens: int | None = None
    actions: Sequence[str] = []
    return_date: str | None = None
    created_at: str | None = None


class InboxTaggingSummary(BaseModel):
    """Counts across every tagging result in the workspace."""

    total: int | None = None
    needs_review: int | None = None
    from_offline: int | None = None
    acted: int | None = None


class InboxTaggingReview(BaseModel):
    """One page of the review feed with its summary.

    ``enabled`` says whether automatic tagging is switched on for the
    instance, so an empty list can be explained.
    """

    enabled: bool | None = None
    data: Sequence[InboxTagRow] = []
    total: int | None = None
    summary: InboxTaggingSummary | None = None
    pagination: dict[str, Any] | None = None


class Analytics(SyncAPIResource):
    """Synchronous ``analytics`` resource (read-only)."""

    def dashboard(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            "/analytics/dashboard",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def deliverability(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve deliverability analytics (bounces, complaints, placement).

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            "/analytics/deliverability",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def warmup(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics across mailboxes.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            "/analytics/warmup",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def compare_campaigns(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            "/analytics/campaigns/compare",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def campaign(
        self,
        campaign_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics for a single campaign.

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            f"/analytics/campaigns/{campaign_id}",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def campaign_daily(
        self,
        campaign_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's daily time-series analytics.

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            f"/analytics/campaigns/{campaign_id}/daily",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def campaign_hourly(
        self,
        campaign_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's hourly time-series analytics.

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            f"/analytics/campaigns/{campaign_id}/hourly",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def accounts(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics across all email accounts.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            "/analytics/accounts",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def account(
        self,
        account_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics for a single email account.

        Args:
            account_id: The email account id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            f"/analytics/accounts/{account_id}",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def usage(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve account usage analytics (quota and consumption).

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def direct(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DirectMailAnalytics:
        """Retrieve the hand-written-mail overview.

        Volume and replies come from the synced mailbox; opens and clicks only
        from mailboxes that opted into tracking them. Requires the
        ``read_analytics`` scope.

        Args:
            period: ``7d`` (default), ``30d`` or ``90d``. Anything else is
                treated as ``7d``.
            options: Optional per-request overrides.
        """
        return self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
            query=drop_not_given({"period": period}),
            options=options,
        )

    def inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[InboxTagRow]:
        """List what automatic inbox tagging decided and how sure it was
        (auto-paginating).

        Requires the ``read_analytics`` scope. Use :meth:`inbox_tagging_summary`
        for the counts and the feature's on/off state.

        Args:
            needs_review: Only results a person should look at.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/inbox-tagging",
            model=InboxTagRow,
            query=drop_not_given(
                {"needs_review": needs_review, "limit": limit, "cursor": cursor}
            ),
            options=options,
        )

    def inbox_tagging_summary(
        self, *, options: RequestOptions | None = None
    ) -> InboxTaggingReview:
        """Retrieve the inbox-tagging counts and whether tagging is enabled.

        Fetches a one-row page, so ``data`` holds at most one result. Requires
        the ``read_analytics`` scope.
        """
        return self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
            query={"limit": 1},
            options=options,
        )

    def warmup_placement(
        self,
        *,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve where warmup mail landed (inbox, category tabs, spam) per
        day and per recipient provider.

        Requires the ``read_analytics`` scope and an organization.

        Args:
            email_id: Limit the report to one mailbox; omit for the workspace.
            from_: First day, ``YYYY-MM-DD`` (default: 29 days before *to*).
            to: Last day, ``YYYY-MM-DD`` (default: today, UTC).
            options: Optional per-request overrides.
        """
        return self._get(
            "/analytics/warmup/placement",
            cast_to=AnalyticsResult,
            query=drop_not_given({"email_id": email_id, "from": from_, "to": to}),
            options=options,
        )


class AsyncAnalytics(AsyncAPIResource):
    """Asynchronous ``analytics`` resource (read-only)."""

    async def dashboard(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            "/analytics/dashboard",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def deliverability(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve deliverability analytics (bounces, complaints, placement).

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            "/analytics/deliverability",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def warmup(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics across mailboxes.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            "/analytics/warmup",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def compare_campaigns(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            "/analytics/campaigns/compare",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def campaign(
        self,
        campaign_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics for a single campaign.

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            f"/analytics/campaigns/{campaign_id}",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def campaign_daily(
        self,
        campaign_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's daily time-series analytics.

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            f"/analytics/campaigns/{campaign_id}/daily",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def campaign_hourly(
        self,
        campaign_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's hourly time-series analytics.

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            f"/analytics/campaigns/{campaign_id}/hourly",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def accounts(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics across all email accounts.

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            "/analytics/accounts",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def account(
        self,
        account_id: str,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics for a single email account.

        Args:
            account_id: The email account id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            f"/analytics/accounts/{account_id}",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def usage(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve account usage analytics (quota and consumption).

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to})
        return await self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def direct(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DirectMailAnalytics:
        """Retrieve the hand-written-mail overview.

        Volume and replies come from the synced mailbox; opens and clicks only
        from mailboxes that opted into tracking them. Requires the
        ``read_analytics`` scope.

        Args:
            period: ``7d`` (default), ``30d`` or ``90d``. Anything else is
                treated as ``7d``.
            options: Optional per-request overrides.
        """
        return await self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
            query=drop_not_given({"period": period}),
            options=options,
        )

    def inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[InboxTagRow]:
        """List what automatic inbox tagging decided and how sure it was
        (auto-paginating).

        Requires the ``read_analytics`` scope. Use :meth:`inbox_tagging_summary`
        for the counts and the feature's on/off state.

        Args:
            needs_review: Only results a person should look at.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/inbox-tagging",
            model=InboxTagRow,
            query=drop_not_given(
                {"needs_review": needs_review, "limit": limit, "cursor": cursor}
            ),
            options=options,
        )

    async def inbox_tagging_summary(
        self, *, options: RequestOptions | None = None
    ) -> InboxTaggingReview:
        """Retrieve the inbox-tagging counts and whether tagging is enabled.

        Fetches a one-row page, so ``data`` holds at most one result. Requires
        the ``read_analytics`` scope.
        """
        return await self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
            query={"limit": 1},
            options=options,
        )

    async def warmup_placement(
        self,
        *,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve where warmup mail landed (inbox, category tabs, spam) per
        day and per recipient provider.

        Requires the ``read_analytics`` scope and an organization.

        Args:
            email_id: Limit the report to one mailbox; omit for the workspace.
            from_: First day, ``YYYY-MM-DD`` (default: 29 days before *to*).
            to: Last day, ``YYYY-MM-DD`` (default: today, UTC).
            options: Optional per-request overrides.
        """
        return await self._get(
            "/analytics/warmup/placement",
            cast_to=AnalyticsResult,
            query=drop_not_given({"email_id": email_id, "from": from_, "to": to}),
            options=options,
        )
