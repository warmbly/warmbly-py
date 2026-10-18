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
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "Analytics",
    "AnalyticsObservationMetric",
    "AnalyticsResult",
    "AsyncAnalytics",
    "DirectMailAnalytics",
    "DirectMailContact",
    "DirectMailDailyStats",
    "DirectMailMailboxStats",
    "DirectMailTracking",
    "DirectMailVolume",
    "InboxTaggingReview",
    "InboxTaggingReviewSummary",
    "InboxTaggingRow",
    "WarmupPlacementCounts",
    "WarmupPlacementDay",
    "WarmupPlacementGroupCounts",
    "WarmupPlacementHost",
    "WarmupPlacementMailbox",
    "WarmupPlacementProvider",
    "WarmupPlacementRate",
    "WarmupPlacementReport",
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
        date: The day an hourly report covers, if echoed back.
        pagination: The cursor block of a paged report (``next_cursor``,
            ``has_more``), if any.
    """

    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    interval: str | None = None
    totals: dict[str, Any] | None = None
    series: Sequence[dict[str, Any]] | None = None
    data: Sequence[dict[str, Any]] | None = None
    date: str | None = None
    pagination: dict[str, Any] | None = None


class DirectMailVolume(BaseModel):
    """Hand-written mail volume, measured from the synced mailbox.

    ``replied`` counts threads that got an inbound message back and excludes
    ``bounced``. ``median_reply_minutes`` is ``0`` when nothing was answered.
    """

    sent: int | None = None
    received: int | None = None
    threads_started: int | None = None
    replied: int | None = None
    reply_rate: float | None = None
    bounced: int | None = None
    median_reply_minutes: int | None = None


class DirectMailTracking(BaseModel):
    """The opt-in half: opens and clicks for mailboxes that track direct mail.

    ``tracked_sent`` is the denominator of both rates; untracked sends are not
    failures to open.
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
    """Mail written by hand rather than sent by a campaign.

    ``volume`` and replies cover everything the mailbox sent, including mail
    written outside Warmbly. ``tracking`` covers only mail sent through
    Warmbly by mailboxes with tracking switched on, so the two are reported
    apart and never blended into one rate.
    """

    period: str | None = None
    volume: DirectMailVolume | None = None
    tracking: DirectMailTracking | None = None
    daily_trend: Sequence[DirectMailDailyStats] = []
    mailboxes: Sequence[DirectMailMailboxStats] = []
    top_contacts: Sequence[DirectMailContact] = []


class InboxTaggingRow(BaseModel):
    """One message automatic inbox tagging classified.

    ``actions`` is what the workspace's switches let the verdict do and
    ``return_date`` (``YYYY-MM-DD``) the out-of-office return date the model
    was asked to confirm, ``None`` when it was not asked.
    """

    id: str | None = None
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


class InboxTaggingReviewSummary(BaseModel):
    """Counts across every tagged message of the workspace."""

    total: int | None = None
    needs_review: int | None = None
    from_offline: int | None = None
    acted: int | None = None


class InboxTaggingReview(BaseModel):
    """One page of the inbox-tagging review list.

    ``enabled`` says whether the feature is switched on for the instance, so
    an empty ``data`` can be explained. ``total`` counts every row matching the
    filter; ``pagination`` carries ``next_cursor`` and ``has_more``.
    """

    enabled: bool | None = None
    data: Sequence[InboxTaggingRow] = []
    total: int | None = None
    summary: InboxTaggingReviewSummary | None = None
    pagination: dict[str, Any] | None = None


class AnalyticsObservationMetric(BaseModel):
    """A rate with its numerator, denominator and confidence interval.

    ``value`` is ``None`` when the denominator is empty. The interval arrives
    under the ``wilson_95_independence_interval`` key as ``{"lower", "upper"}``.
    """

    version: str | None = None
    population: str | None = None
    denominator_kind: str | None = None
    unit: str | None = None
    source: str | None = None
    classification_policy: str | None = None
    numerator: int | None = None
    denominator: int | None = None
    unresolved: int | None = None
    window_days: int | None = None
    window_basis: str | None = None
    missingness_basis: str | None = None
    value: float | None = None
    wilson_95_independence_interval: dict[str, float] | None = None


class WarmupPlacementCounts(BaseModel):
    """Where a set of verified warmup deliveries landed.

    ``delivered`` is ``inbox + tabs + spam``; category tabs count as inbox in
    ``inbox_rate``. Both rates are ``None`` with nothing delivered.
    """

    sent: int | None = None
    delivered: int | None = None
    inbox: int | None = None
    tabs: int | None = None
    spam: int | None = None
    unknown: int | None = None
    archived: int | None = None
    custom: int | None = None
    instrumented_receipts: int | None = None
    observed_receipts: int | None = None
    legacy_uninstrumented_receipts: int | None = None
    rescue_requested: int | None = None
    rescue_confirmed: int | None = None
    non_spam_metric: AnalyticsObservationMetric | None = None
    rescued: int | None = None
    unconfirmed: int | None = None
    inbox_rate: float | None = None
    spam_rate: float | None = None


class WarmupPlacementRate(BaseModel):
    """A mailbox's headline deliverability over a trailing window.

    ``scope`` is the recipients the rate is taken over (``major``: Google,
    Microsoft and Yahoo). ``inbox_rate`` is ``None`` until ``delivered``
    reaches ``min_sample``. ``band`` is ``good``, ``fair``, ``poor``,
    ``collecting`` or ``none``. ``other_delivered`` and ``other_inbox_rate``
    describe the hosts left out of a major-scope rate.
    """

    window_days: int | None = None
    min_sample: int | None = None
    scope: str | None = None
    delivered: int | None = None
    inbox: int | None = None
    tabs: int | None = None
    spam: int | None = None
    inbox_rate: float | None = None
    band: str | None = None
    metric: AnalyticsObservationMetric | None = None
    other_delivered: int | None = None
    other_inbox_rate: float | None = None


class WarmupPlacementGroupCounts(BaseModel):
    """One recipient group's share of a day."""

    group: str | None = None
    inbox: int | None = None
    tabs: int | None = None
    spam: int | None = None
    rescued: int | None = None
    unknown: int | None = None
    archived: int | None = None
    custom: int | None = None


class WarmupPlacementDay(WarmupPlacementCounts):
    """One UTC day of placement.

    ``rolling_inbox_rate`` is the trailing-window rate ending on the day,
    ``None`` below the sample floor.
    """

    date: str | None = None
    rolling_inbox_rate: float | None = None
    groups: Sequence[WarmupPlacementGroupCounts] = []


class WarmupPlacementHost(WarmupPlacementCounts):
    """One mail host inside a recipient group."""

    host: str | None = None


class WarmupPlacementProvider(WarmupPlacementCounts):
    """The window's placement at one recipient group."""

    group: str | None = None
    hosts: Sequence[WarmupPlacementHost] = []


class WarmupPlacementMailbox(WarmupPlacementCounts):
    """One sender's row in the workspace report.

    ``daily_inbox_rate`` follows the report's days and holds ``None`` on a day
    with no deliveries.
    """

    email_account_id: str | None = None
    email: str | None = None
    rate: WarmupPlacementRate | None = None
    daily_inbox_rate: Sequence[float | None] = []


class WarmupPlacementReport(BaseModel):
    """Where warmup mail landed over a date range.

    Covers one mailbox when ``email_account_id`` is set, otherwise the whole
    workspace, in which case ``mailboxes`` is filled, worst rate first.
    """

    email_account_id: str | None = None
    date_range: dict[str, str] | None = None
    summary: WarmupPlacementCounts | None = None
    rate: WarmupPlacementRate | None = None
    daily: Sequence[WarmupPlacementDay] = []
    providers: Sequence[WarmupPlacementProvider] = []
    mailboxes: Sequence[WarmupPlacementMailbox] = []


def _csv(values: NotGivenOr[Sequence[str]]) -> NotGivenOr[str]:
    """Join an id list into the comma-separated form the server reads."""
    if isinstance(values, NotGiven):
        return values
    return ",".join(values)


class Analytics(SyncAPIResource):
    """Synchronous ``analytics`` resource (read-only)."""

    def dashboard(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            campaign_ids: Narrow the campaign-derived sections to these campaigns
                (at most 100).
            folder_ids: Narrow them to the campaigns in these folders (at most 100).
            from_: Not read by the server and ignored; use *period*. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
                "campaign_ids": _csv(campaign_ids),
                "folder_ids": _csv(folder_ids),
                "from": from_,
                "to": to,
            }
        )
        return self._get(
            "/analytics/dashboard",
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
        """Retrieve the hand-written mail overview.

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period})
        return self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
            query=query,
            options=options,
        )

    def inbox_tagging(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> InboxTaggingReview:
        """Review what automatic inbox tagging decided.

        Returns one page; pass the ``pagination.next_cursor`` of a page as
        *cursor* to fetch the next.

        Args:
            limit: Page size (1-200; the server defaults to 50).
            cursor: The opaque cursor from the previous page.
            needs_review: Only the messages flagged for review.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {"limit": limit, "cursor": cursor, "needs_review": needs_review}
        )
        return self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
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
            from_: Start of the reporting window (RFC3339).
            to: End of the reporting window (RFC3339).
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
        email_id: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics.

        Args:
            email_id: Restrict to one mailbox; omitted covers the workspace.
            from_: Start of the reporting window (``YYYY-MM-DD``).
            to: End of the reporting window (``YYYY-MM-DD``).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"email_id": email_id, "from": from_, "to": to})
        return self._get(
            "/analytics/warmup",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def warmup_placement(
        self,
        *,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupPlacementReport:
        """Report where warmup mail landed.

        Breaks inbox, category tabs and spam down per day and per recipient
        provider, for one mailbox or the workspace. A report covers a limited
        number of days.

        Args:
            email_id: Restrict to one mailbox; omitted covers the workspace.
            from_: First day (``YYYY-MM-DD``); defaults to 29 days before *to*.
            to: Last day (``YYYY-MM-DD``); defaults to today (UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"email_id": email_id, "from": from_, "to": to})
        return self._get(
            "/analytics/warmup/placement",
            cast_to=WarmupPlacementReport,
            query=query,
            options=options,
        )

    def compare_campaigns(
        self,
        *,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            campaign_ids: The campaigns to compare (up to 10). The server requires
                them.
            from_: Start of the reporting window (``YYYY-MM-DD``); the server requires it.
            to: End of the reporting window (``YYYY-MM-DD``); the server requires it.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"ids": _csv(campaign_ids), "from": from_, "to": to})
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
            from_: Start of the reporting window (``YYYY-MM-DD``; give both or neither, neither meaning all time).
            to: End of the reporting window (``YYYY-MM-DD``; give both or neither, neither meaning all time).
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
            from_: Start of the reporting window (``YYYY-MM-DD``); the server requires it.
            to: End of the reporting window (``YYYY-MM-DD``); the server requires it.
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
        date: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's hourly time-series analytics for one day.

        Args:
            campaign_id: The campaign id.
            date: The day (``YYYY-MM-DD``); defaults to today.
            from_: Not read by the server and ignored; use *date*. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"date": date, "from": from_, "to": to})
        return self._get(
            f"/analytics/campaigns/{campaign_id}/hourly",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def accounts(
        self,
        *,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the status of email accounts, one page at a time.

        The result carries a ``pagination`` block; pass its ``next_cursor`` as
        *cursor* to fetch the next page.

        Args:
            email_ids: Only these mailboxes (at most 200).
            limit: Page size (1-1000; the server defaults to 1000).
            cursor: The opaque cursor from the previous page.
            from_: Not read by the server and ignored. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "email_ids": _csv(email_ids),
                "limit": limit,
                "cursor": cursor,
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve the detailed status of a single email account.

        Args:
            account_id: The email account id.
            from_: Not read by the server and ignored. Deprecated.
            to: Not read by the server and ignored. Deprecated.
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
        period: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve account usage analytics (quota and consumption).

        Args:
            period: ``day`` (default), ``week`` or ``month``.
            from_: Not read by the server and ignored; use *period*. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period, "from": from_, "to": to})
        return self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )


class AsyncAnalytics(AsyncAPIResource):
    """Asynchronous ``analytics`` resource (read-only)."""

    async def dashboard(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            campaign_ids: Narrow the campaign-derived sections to these campaigns
                (at most 100).
            folder_ids: Narrow them to the campaigns in these folders (at most 100).
            from_: Not read by the server and ignored; use *period*. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
                "campaign_ids": _csv(campaign_ids),
                "folder_ids": _csv(folder_ids),
                "from": from_,
                "to": to,
            }
        )
        return await self._get(
            "/analytics/dashboard",
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
        """Retrieve the hand-written mail overview.

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period})
        return await self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
            query=query,
            options=options,
        )

    async def inbox_tagging(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> InboxTaggingReview:
        """Review what automatic inbox tagging decided.

        Returns one page; pass the ``pagination.next_cursor`` of a page as
        *cursor* to fetch the next.

        Args:
            limit: Page size (1-200; the server defaults to 50).
            cursor: The opaque cursor from the previous page.
            needs_review: Only the messages flagged for review.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {"limit": limit, "cursor": cursor, "needs_review": needs_review}
        )
        return await self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
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
            from_: Start of the reporting window (RFC3339).
            to: End of the reporting window (RFC3339).
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
        email_id: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics.

        Args:
            email_id: Restrict to one mailbox; omitted covers the workspace.
            from_: Start of the reporting window (``YYYY-MM-DD``).
            to: End of the reporting window (``YYYY-MM-DD``).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"email_id": email_id, "from": from_, "to": to})
        return await self._get(
            "/analytics/warmup",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def warmup_placement(
        self,
        *,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupPlacementReport:
        """Report where warmup mail landed.

        Breaks inbox, category tabs and spam down per day and per recipient
        provider, for one mailbox or the workspace. A report covers a limited
        number of days.

        Args:
            email_id: Restrict to one mailbox; omitted covers the workspace.
            from_: First day (``YYYY-MM-DD``); defaults to 29 days before *to*.
            to: Last day (``YYYY-MM-DD``); defaults to today (UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"email_id": email_id, "from": from_, "to": to})
        return await self._get(
            "/analytics/warmup/placement",
            cast_to=WarmupPlacementReport,
            query=query,
            options=options,
        )

    async def compare_campaigns(
        self,
        *,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            campaign_ids: The campaigns to compare (up to 10). The server requires
                them.
            from_: Start of the reporting window (``YYYY-MM-DD``); the server requires it.
            to: End of the reporting window (``YYYY-MM-DD``); the server requires it.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"ids": _csv(campaign_ids), "from": from_, "to": to})
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
            from_: Start of the reporting window (``YYYY-MM-DD``; give both or neither, neither meaning all time).
            to: End of the reporting window (``YYYY-MM-DD``; give both or neither, neither meaning all time).
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
            from_: Start of the reporting window (``YYYY-MM-DD``); the server requires it.
            to: End of the reporting window (``YYYY-MM-DD``); the server requires it.
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
        date: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's hourly time-series analytics for one day.

        Args:
            campaign_id: The campaign id.
            date: The day (``YYYY-MM-DD``); defaults to today.
            from_: Not read by the server and ignored; use *date*. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"date": date, "from": from_, "to": to})
        return await self._get(
            f"/analytics/campaigns/{campaign_id}/hourly",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def accounts(
        self,
        *,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the status of email accounts, one page at a time.

        The result carries a ``pagination`` block; pass its ``next_cursor`` as
        *cursor* to fetch the next page.

        Args:
            email_ids: Only these mailboxes (at most 200).
            limit: Page size (1-1000; the server defaults to 1000).
            cursor: The opaque cursor from the previous page.
            from_: Not read by the server and ignored. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "email_ids": _csv(email_ids),
                "limit": limit,
                "cursor": cursor,
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve the detailed status of a single email account.

        Args:
            account_id: The email account id.
            from_: Not read by the server and ignored. Deprecated.
            to: Not read by the server and ignored. Deprecated.
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
        period: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve account usage analytics (quota and consumption).

        Args:
            period: ``day`` (default), ``week`` or ``month``.
            from_: Not read by the server and ignored; use *period*. Deprecated.
            to: Not read by the server and ignored. Deprecated.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period, "from": from_, "to": to})
        return await self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )
