"""The ``analytics`` resource: read-only reporting endpoints.

Maps to the ``/v1/analytics`` route group. Every method is a ``GET`` and needs
the ``read_analytics`` permission. The date and window parameters differ per
report: most take whole days (``YYYY-MM-DD``), the deliverability dashboard
takes RFC3339 timestamps, and the dashboard and usage reports take a named
``period``; each docstring says which. Most reports are permissive
:class:`~warmbly._models.BaseModel` subclasses (``extra="allow"``), so
additional or future fields the backend returns are preserved without a client
upgrade. The direct-mail, inbox-tagging and warmup-placement reports are typed.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import Field

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given
from .placement import ObservationMetric

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
    "InboxTagVerdict",
    "InboxTaggingOverview",
    "InboxTaggingSummary",
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
    """

    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    interval: str | None = None
    totals: dict[str, Any] | None = None
    series: Sequence[dict[str, Any]] | None = None
    data: Sequence[dict[str, Any]] | None = None


class DirectMailVolume(BaseModel):
    """How much hand-written mail was sent and answered, from the synced mailbox.

    ``median_reply_minutes`` is ``0`` when no thread has been answered.
    """

    sent: int | None = None
    received: int | None = None
    threads_started: int | None = None
    replied: int | None = None
    reply_rate: float | None = None
    bounced: int | None = None
    median_reply_minutes: int | None = None


class DirectMailTracking(BaseModel):
    """Opens and clicks for mailboxes that opted into tracking hand-written mail.

    ``tracked_sent`` is the denominator of both rates: untracked sends were
    never asked to be tracked.
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
    """The hand-written mail overview.

    Volume and replies cover everything the mailbox sent, including mail written
    in a mail client; opens and clicks cover only mail sent through Warmbly by a
    mailbox with tracking on. They are reported apart because they cover
    different messages.
    """

    period: str | None = None
    volume: DirectMailVolume | None = None
    tracking: DirectMailTracking | None = None
    daily_trend: Sequence[DirectMailDailyStats] = []
    mailboxes: Sequence[DirectMailMailboxStats] = []
    top_contacts: Sequence[DirectMailContact] = []


class InboxTagVerdict(BaseModel):
    """How a reply was classified, and how sure the classifier was.

    ``kind``/``intent``/``priority`` are the classifier's labels, ``actions`` is
    what the workspace's switches let this verdict do, and ``return_date`` is the
    out-of-office return date (``YYYY-MM-DD``) when one was read.
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


class InboxTaggingSummary(BaseModel):
    """Counts across every classified reply, whatever page was read."""

    total: int | None = None
    needs_review: int | None = None
    from_offline: int | None = None
    acted: int | None = None


class InboxTaggingOverview(BaseModel):
    """The inbox-tagging headline: whether the feature is on, and the counts."""

    enabled: bool | None = None
    total: int | None = None
    summary: InboxTaggingSummary | None = None


class WarmupPlacementCounts(BaseModel):
    """Where a set of verified warmup deliveries landed.

    ``delivered`` is what recipients verifiably received (inbox, tabs and spam);
    the inbox rate counts category tabs as inbox. Rates are percentages and
    ``None`` until something was delivered.
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
    non_spam_metric: ObservationMetric | None = None
    rescued: int | None = None
    rescue_confirmed: int | None = None
    rescue_missing: int | None = None
    rescue_failed: int | None = None
    rescue_unreported: int | None = None
    unconfirmed: int | None = None
    inbox_rate: float | None = None
    spam_rate: float | None = None


class WarmupPlacementRate(BaseModel):
    """A mailbox's headline deliverability over the trailing window.

    ``inbox_rate`` is withheld (``None``) below ``min_sample`` deliveries.
    ``band`` is ``good``, ``fair``, ``poor``, ``collecting`` or ``none``, and
    ``scope`` is ``major`` (Google, Microsoft and Yahoo recipients).
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
    metric: ObservationMetric | None = None
    other_delivered: int | None = None
    other_inbox_rate: float | None = None


class WarmupPlacementGroupCounts(BaseModel):
    """One recipient group's share of a day (``google``, ``microsoft``, ``yahoo``, ``other``)."""

    group: str | None = None
    inbox: int | None = None
    tabs: int | None = None
    spam: int | None = None
    rescued: int | None = None
    unknown: int | None = None
    archived: int | None = None
    custom: int | None = None
    rescue_confirmed: int | None = None
    rescue_missing: int | None = None
    rescue_failed: int | None = None


class WarmupPlacementDay(WarmupPlacementCounts):
    """One UTC day of placement.

    ``rolling_inbox_rate`` is the trailing-window rate ending on this day.
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

    ``daily_inbox_rate`` follows the report's days, ``None`` on a day without
    deliveries.
    """

    email_account_id: str | None = None
    email: str | None = None
    rate: WarmupPlacementRate | None = None
    daily_inbox_rate: Sequence[float | None] = []


class WarmupPlacementReport(BaseModel):
    """Where warmup mail landed over a date range.

    For one mailbox when ``email_id`` was given, otherwise for the whole
    workspace, in which case ``mailboxes`` lists each sender, worst rate first.
    ``date_range`` carries ``from`` and ``to`` as RFC3339 timestamps.
    """

    email_account_id: str | None = None
    date_range: dict[str, str] | None = None
    summary: WarmupPlacementCounts | None = None
    rate: WarmupPlacementRate | None = None
    daily: Sequence[WarmupPlacementDay] = []
    providers: Sequence[WarmupPlacementProvider] = []
    mailboxes: Sequence[WarmupPlacementMailbox] = []


def _csv(values: NotGivenOr[Sequence[str]]) -> NotGivenOr[str]:
    """Join an id list into the comma-separated form the reports read."""
    return ",".join(values) if is_given(values) else NOT_GIVEN


class Analytics(SyncAPIResource):
    """Synchronous ``analytics`` resource (read-only)."""

    def dashboard(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        The campaign filters narrow the campaign-derived sections only; mailbox
        counts stay workspace-wide.

        Args:
            period: ``"7d"`` (the default), ``"30d"`` or ``"90d"``; anything else reads as ``"7d"``.
            campaign_ids: Narrow the campaign figures to these campaigns (at most 100).
            folder_ids: Narrow the campaign figures to every campaign in these folders (at most 100).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
                "campaign_ids": _csv(campaign_ids),
                "folder_ids": _csv(folder_ids),
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

        Volume and replies from the synced mailbox, plus opens and clicks for the
        mailboxes that opted into tracking them (see
        :meth:`~warmbly.resources.emails.Emails.direct_tracking`).

        Args:
            period: ``"7d"`` (the default), ``"30d"`` or ``"90d"``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period})
        return self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
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
            from_: Optional start of the reporting window (RFC3339); defaults to seven days ago.
            to: Optional end of the reporting window (RFC3339); defaults to now.
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
        from_: str,
        to: str,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics across mailboxes.

        Args:
            from_: Start of the reporting window, a whole day (``YYYY-MM-DD``).
            to: End of the reporting window, a whole day (``YYYY-MM-DD``); not before *from_*.
            email_id: Report on one mailbox instead of the workspace.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to, "email_id": email_id})
        return self._get(
            "/analytics/warmup",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def warmup_placement(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupPlacementReport:
        """Report where warmup mail landed (inbox, category tabs, spam).

        Broken down per day and per recipient provider, for one mailbox or the whole
        workspace.

        Args:
            from_: Start of the window, a whole day (``YYYY-MM-DD``); defaults to 30 days ending on *to*.
            to: End of the window, a whole day (``YYYY-MM-DD``); defaults to today (UTC).
            email_id: Report on one mailbox instead of the workspace.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to, "email_id": email_id})
        return self._get(
            "/analytics/warmup/placement",
            cast_to=WarmupPlacementReport,
            query=query,
            options=options,
        )

    def inbox_tagging_overview(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> InboxTaggingOverview:
        """Read the inbox-tagging headline: whether it is on and the counts.

        The per-reply rows come from :meth:`inbox_tagging`; this reads only the
        summary, which that iterator does not expose.

        Args:
            needs_review: Count only replies flagged for review in ``total``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"needs_review": needs_review, "limit": 1})
        return self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingOverview,
            query=query,
            options=options,
        )

    def compare_campaigns(
        self,
        *,
        ids: Sequence[str],
        from_: str,
        to: str,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            ids: The campaigns to compare (at most 10; extra ids are ignored).
            from_: Start of the window, a whole day (``YYYY-MM-DD``).
            to: End of the window, a whole day (``YYYY-MM-DD``).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"ids": _csv(ids), "from": from_, "to": to})
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
            from_: Start of the window, a whole day (``YYYY-MM-DD``). Send with *to*; omit both for all time.
            to: End of the window, a whole day (``YYYY-MM-DD``).
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
        from_: str,
        to: str,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's daily time-series analytics.

        Args:
            campaign_id: The campaign id.
            from_: Start of the window, a whole day (``YYYY-MM-DD``).
            to: End of the window, a whole day (``YYYY-MM-DD``).
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's hourly time-series analytics for one day.

        Args:
            campaign_id: The campaign id.
            date: The day to break down, ``YYYY-MM-DD``; defaults to today.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"date": date})
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics across all email accounts, one page at a time.

        Read ``pagination.next_cursor`` from the result and pass it as *cursor* for
        the next page.

        Args:
            email_ids: Restrict the page to these mailboxes (at most the server's page cap).
            limit: Mailboxes per page.
            cursor: The ``pagination.next_cursor`` of a previous page.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {"email_ids": _csv(email_ids), "limit": limit, "cursor": cursor}
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the status and analytics of a single email account.

        Args:
            account_id: The email account id.
            options: Optional per-request overrides.
        """
        return self._get(
            f"/analytics/accounts/{account_id}",
            cast_to=AnalyticsResult,
            options=options,
        )

    def usage(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve account usage analytics (quota and consumption).

        Args:
            period: ``"day"`` (the default), ``"week"`` or ``"month"``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period})
        return self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[InboxTagVerdict]:
        """List how replies were classified (auto-paginating).

        Each row says what the classifier decided and how sure it was, so a
        person can review it before the workspace lets it act.

        Args:
            needs_review: Only replies flagged for review.
            limit: Rows per page (1 to 200).
            cursor: Opaque pagination cursor from a previous page.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/inbox-tagging",
            model=InboxTagVerdict,
            query={"needs_review": needs_review, "limit": limit, "cursor": cursor},
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        The campaign filters narrow the campaign-derived sections only; mailbox
        counts stay workspace-wide.

        Args:
            period: ``"7d"`` (the default), ``"30d"`` or ``"90d"``; anything else reads as ``"7d"``.
            campaign_ids: Narrow the campaign figures to these campaigns (at most 100).
            folder_ids: Narrow the campaign figures to every campaign in these folders (at most 100).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
                "campaign_ids": _csv(campaign_ids),
                "folder_ids": _csv(folder_ids),
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

        Volume and replies from the synced mailbox, plus opens and clicks for the
        mailboxes that opted into tracking them (see
        :meth:`~warmbly.resources.emails.Emails.direct_tracking`).

        Args:
            period: ``"7d"`` (the default), ``"30d"`` or ``"90d"``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period})
        return await self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
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
            from_: Optional start of the reporting window (RFC3339); defaults to seven days ago.
            to: Optional end of the reporting window (RFC3339); defaults to now.
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
        from_: str,
        to: str,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics across mailboxes.

        Args:
            from_: Start of the reporting window, a whole day (``YYYY-MM-DD``).
            to: End of the reporting window, a whole day (``YYYY-MM-DD``); not before *from_*.
            email_id: Report on one mailbox instead of the workspace.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to, "email_id": email_id})
        return await self._get(
            "/analytics/warmup",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def warmup_placement(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupPlacementReport:
        """Report where warmup mail landed (inbox, category tabs, spam).

        Broken down per day and per recipient provider, for one mailbox or the whole
        workspace.

        Args:
            from_: Start of the window, a whole day (``YYYY-MM-DD``); defaults to 30 days ending on *to*.
            to: End of the window, a whole day (``YYYY-MM-DD``); defaults to today (UTC).
            email_id: Report on one mailbox instead of the workspace.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"from": from_, "to": to, "email_id": email_id})
        return await self._get(
            "/analytics/warmup/placement",
            cast_to=WarmupPlacementReport,
            query=query,
            options=options,
        )

    async def inbox_tagging_overview(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> InboxTaggingOverview:
        """Read the inbox-tagging headline: whether it is on and the counts.

        The per-reply rows come from :meth:`inbox_tagging`; this reads only the
        summary, which that iterator does not expose.

        Args:
            needs_review: Count only replies flagged for review in ``total``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"needs_review": needs_review, "limit": 1})
        return await self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingOverview,
            query=query,
            options=options,
        )

    async def compare_campaigns(
        self,
        *,
        ids: Sequence[str],
        from_: str,
        to: str,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            ids: The campaigns to compare (at most 10; extra ids are ignored).
            from_: Start of the window, a whole day (``YYYY-MM-DD``).
            to: End of the window, a whole day (``YYYY-MM-DD``).
            options: Optional per-request overrides.
        """
        query = drop_not_given({"ids": _csv(ids), "from": from_, "to": to})
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
            from_: Start of the window, a whole day (``YYYY-MM-DD``). Send with *to*; omit both for all time.
            to: End of the window, a whole day (``YYYY-MM-DD``).
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
        from_: str,
        to: str,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's daily time-series analytics.

        Args:
            campaign_id: The campaign id.
            from_: Start of the window, a whole day (``YYYY-MM-DD``).
            to: End of the window, a whole day (``YYYY-MM-DD``).
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve a campaign's hourly time-series analytics for one day.

        Args:
            campaign_id: The campaign id.
            date: The day to break down, ``YYYY-MM-DD``; defaults to today.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"date": date})
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve analytics across all email accounts, one page at a time.

        Read ``pagination.next_cursor`` from the result and pass it as *cursor* for
        the next page.

        Args:
            email_ids: Restrict the page to these mailboxes (at most the server's page cap).
            limit: Mailboxes per page.
            cursor: The ``pagination.next_cursor`` of a previous page.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {"email_ids": _csv(email_ids), "limit": limit, "cursor": cursor}
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
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the status and analytics of a single email account.

        Args:
            account_id: The email account id.
            options: Optional per-request overrides.
        """
        return await self._get(
            f"/analytics/accounts/{account_id}",
            cast_to=AnalyticsResult,
            options=options,
        )

    async def usage(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve account usage analytics (quota and consumption).

        Args:
            period: ``"day"`` (the default), ``"week"`` or ``"month"``.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period})
        return await self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    def inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[InboxTagVerdict]:
        """List how replies were classified (auto-paginating).

        Each row says what the classifier decided and how sure it was, so a
        person can review it before the workspace lets it act.

        Args:
            needs_review: Only replies flagged for review.
            limit: Rows per page (1 to 200).
            cursor: Opaque pagination cursor from a previous page.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/inbox-tagging",
            model=InboxTagVerdict,
            query={"needs_review": needs_review, "limit": limit, "cursor": cursor},
            options=options,
        )
