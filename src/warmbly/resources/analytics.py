"""The ``analytics`` resource: read-only reporting endpoints.

Maps to the ``/v1/analytics`` route group. Every method is a ``GET``. The
reports that take a date range read it as whole days (``YYYY-MM-DD``, UTC)
except ``deliverability`` and ``hourly`` which read RFC3339 timestamps, as noted
on each method. Most results are permissive
:class:`~warmbly._models.BaseModel` subclasses (``extra="allow"``), so
additional or future fields the backend returns are preserved without a client
upgrade; the direct-mail, inbox-tagging, warmup-placement and account-status
reports have typed models for their headline fields.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import Field

from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given
from ._nullsafe import NullSafeModel
from .placement import PlacementMetric

__all__ = [
    "AccountStatus",
    "Analytics",
    "AnalyticsResult",
    "AsyncAnalytics",
    "DirectMailAnalytics",
    "DirectMailContact",
    "DirectMailDay",
    "DirectMailMailbox",
    "DirectMailTracking",
    "DirectMailVolume",
    "InboxTagDecision",
    "InboxTaggingReview",
    "InboxTaggingSummary",
    "WarmupPlacementCounts",
    "WarmupPlacementDay",
    "WarmupPlacementMailbox",
    "WarmupPlacementProvider",
    "WarmupPlacementRate",
    "WarmupPlacementReport",
]


class AnalyticsResult(NullSafeModel):
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
        pagination: ``{"total", "next_cursor", "has_more"}`` on the paged
            reports (``accounts``).
    """

    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    interval: str | None = None
    totals: dict[str, Any] | None = None
    series: Sequence[dict[str, Any]] | None = None
    data: Sequence[dict[str, Any]] | None = None
    pagination: dict[str, Any] | None = None


class AccountStatus(NullSafeModel):
    """One email account's status in ``analytics.accounts``.

    ``health``, ``daily_usage``, ``warmup_status``, ``warmup_health``,
    ``warmup_placement``, ``send_lifecycle`` and ``cold_ramp`` are kept as
    plain dicts. ``cold_ramp`` is present only while the warmup graduation
    ceiling holds the cold cap below the mailbox's own, and
    ``send_recovery_reason`` only while a send safety hold is in place.
    """

    id: str
    email: str | None = None
    provider: str | None = None
    status: str | None = None
    last_synced_at: str | None = None
    health: dict[str, Any] | None = None
    errors: Sequence[dict[str, Any]] = []
    daily_usage: dict[str, Any] | None = None
    warmup_status: dict[str, Any] | None = None
    warmup_health: dict[str, Any] | None = None
    warmup_placement: dict[str, Any] | None = None
    in_campaign: bool | None = None
    send_lifecycle: dict[str, Any] | None = None
    cold_ramp: dict[str, Any] | None = None
    send_recovery_reason: str | None = None


class DirectMailVolume(NullSafeModel):
    """How much hand-written mail went out and came back.

    ``median_reply_minutes`` is ``0`` when no thread has been answered.
    ``bounced`` is excluded from ``replied``.
    """

    sent: int | None = None
    received: int | None = None
    threads_started: int | None = None
    replied: int | None = None
    reply_rate: float | None = None
    bounced: int | None = None
    median_reply_minutes: int | None = None


class DirectMailTracking(NullSafeModel):
    """The opt-in half: opens and clicks for mailboxes that track direct mail.

    ``tracked_sent`` is the denominator of both rates.
    """

    mailboxes_opted_in: int | None = None
    mailboxes_total: int | None = None
    tracked_sent: int | None = None
    opened: int | None = None
    machine_opened: int | None = None
    clicked: int | None = None
    open_rate: float | None = None
    click_rate: float | None = None


class DirectMailDay(NullSafeModel):
    """One day of direct-mail volume."""

    date: str | None = None
    sent: int | None = None
    received: int | None = None


class DirectMailMailbox(NullSafeModel):
    """One mailbox's direct-mail volume."""

    email_account_id: str | None = None
    email: str | None = None
    track_direct_mail: bool | None = None
    sent: int | None = None
    received: int | None = None


class DirectMailContact(NullSafeModel):
    """One correspondent, ranked by how much was sent to them."""

    email: str | None = None
    sent: int | None = None
    received: int | None = None
    last_at: str | None = None


class DirectMailAnalytics(NullSafeModel):
    """The hand-written-mail overview for a window (``period``: ``7d``, ``30d``
    or ``90d``)."""

    period: str | None = None
    volume: DirectMailVolume | None = None
    tracking: DirectMailTracking | None = None
    daily_trend: Sequence[DirectMailDay] = []
    mailboxes: Sequence[DirectMailMailbox] = []
    top_contacts: Sequence[DirectMailContact] = []


class InboxTagDecision(NullSafeModel):
    """One automatic inbox-tagging decision.

    ``kind_confidence`` and ``intent_confidence`` are model confidences.
    ``needs_review`` flags a decision a person should check, with
    ``review_reason``. ``actions`` is what the workspace's switches let the
    verdict do, and ``return_date`` the out-of-office return date (``YYYY-MM-DD``)
    when the model was asked to confirm one.
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


class InboxTaggingSummary(NullSafeModel):
    """Counts across every decision, not just the page."""

    total: int | None = None
    needs_review: int | None = None
    from_offline: int | None = None
    acted: int | None = None


class InboxTaggingReview(NullSafeModel):
    """One page of the inbox-tagging review.

    ``enabled`` says whether tagging is switched on for the instance, so an
    empty ``data`` can be explained. ``total`` is the number of decisions
    matching the filter and ``pagination`` is ``{"next_cursor", "has_more"}``.
    """

    enabled: bool | None = None
    data: Sequence[InboxTagDecision] = []
    total: int | None = None
    summary: InboxTaggingSummary | None = None
    pagination: dict[str, Any] | None = None


class WarmupPlacementCounts(NullSafeModel):
    """Where warmup mail landed.

    ``delivered`` is what recipients verifiably received (inbox, tabs and
    spam). ``inbox_rate`` and ``spam_rate`` are percentages of ``delivered``
    and ``None`` until something is delivered. The same counters appear on the
    report ``summary``, each daily row, each provider and each mailbox.
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
    non_spam_metric: PlacementMetric | None = None
    rescued: int | None = None
    rescue_confirmed: int | None = None
    rescue_missing: int | None = None
    rescue_failed: int | None = None
    rescue_unreported: int | None = None
    unconfirmed: int | None = None
    inbox_rate: float | None = None
    spam_rate: float | None = None


class WarmupPlacementRate(NullSafeModel):
    """A rolling inbox rate over the major providers.

    ``inbox_rate`` is ``None`` until ``delivered`` reaches ``min_sample``.
    ``band`` is ``good``, ``fair``, ``poor``, ``collecting`` or ``none``.
    ``other_delivered`` and ``other_inbox_rate`` cover the smaller hosts left
    out of the headline.
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
    metric: PlacementMetric | None = None
    other_delivered: int | None = None
    other_inbox_rate: float | None = None


class WarmupPlacementDay(WarmupPlacementCounts):
    """One UTC day of warmup placement. ``groups`` splits it per recipient
    group (``group`` plus the same counters)."""

    date: str | None = None
    rolling_inbox_rate: float | None = None
    groups: Sequence[dict[str, Any]] = []


class WarmupPlacementProvider(WarmupPlacementCounts):
    """The window's placement at one recipient group, with its ``hosts``."""

    group: str | None = None
    hosts: Sequence[dict[str, Any]] = []


class WarmupPlacementMailbox(WarmupPlacementCounts):
    """One sender's row in the workspace report. ``daily_inbox_rate`` follows
    the report's days, with ``None`` on a day with no deliveries."""

    email_account_id: str | None = None
    email: str | None = None
    rate: WarmupPlacementRate | None = None
    daily_inbox_rate: Sequence[float | None] = []


class WarmupPlacementReport(NullSafeModel):
    """Where warmup mail landed over a date range, for one mailbox or the
    whole workspace. ``email_account_id`` is set on a single-mailbox report and
    ``mailboxes`` on the workspace report only."""

    email_account_id: str | None = None
    date_range: dict[str, Any] | None = None
    summary: WarmupPlacementCounts | None = None
    rate: WarmupPlacementRate | None = None
    daily: Sequence[WarmupPlacementDay] = []
    providers: Sequence[WarmupPlacementProvider] = []
    mailboxes: Sequence[WarmupPlacementMailbox] = []


def _csv(values: NotGivenOr[Sequence[str]]) -> NotGivenOr[str]:
    """Join ids into the comma-separated form the server's list params take."""
    return values if isinstance(values, NotGiven) else ",".join(values)


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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            period: The window: ``"7d"`` (default), ``"30d"`` or ``"90d"``.
            campaign_ids: Narrow the campaign-derived sections to these campaigns (up to
                100). Account health stays workspace-wide.
            folder_ids: Narrow the campaign-derived sections to the campaigns in these
                folders (up to 100).
            from_: Ignored by the server, which reads *period*; kept for compatibility.
            to: Ignored by the server, which reads *period*; kept for compatibility.
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
        """Retrieve the direct-mail overview: hand-written mail sent from the mailboxes.

        Volume and replies come from the synced mailbox; opens and clicks cover only
        the mailboxes that opted into tracking them.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            period: The window: ``"7d"`` (default), ``"30d"`` or ``"90d"``. Anything
                else falls back to ``"7d"``.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
            }
        )
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve warmup analytics across mailboxes.

        The server requires both ``from_`` and ``to`` and rejects ``from_`` after ``to``.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_id: Restrict to one mailbox.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "email_id": email_id,
                "from": from_,
                "to": to,
            }
        )
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
        """Report where warmup mail landed (inbox, tabs, spam).

        The report breaks placement down per day and per recipient provider. The
        workspace report (no *email_id*) also lists each mailbox, worst rate first.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_id: Restrict to one mailbox; omit for the whole workspace.
            from_: Start day (``YYYY-MM-DD``). Defaults to 29 days before *to*.
            to: End day (``YYYY-MM-DD``). Defaults to today (UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "email_id": email_id,
                "from": from_,
                "to": to,
            }
        )
        return self._get(
            "/analytics/warmup/placement",
            cast_to=WarmupPlacementReport,
            query=query,
            options=options,
        )

    def compare_campaigns(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        The server requires both ``from_`` and ``to``.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            ids: The campaigns to compare (at most 10). The server requires at least
                one.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "ids": _csv(ids),
                "from": from_,
                "to": to,
            }
        )
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

        ``from_`` and ``to`` must be given together; without them the figures cover all time.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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

        The server requires both ``from_`` and ``to``.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve a campaign's hourly time-series analytics.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: The campaign id.
            date: The day to report (``YYYY-MM-DD``); defaults to today.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "date": date,
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve analytics across email accounts, one page at a time.

        The result carries ``pagination`` for the next page. To walk every page
        automatically, use :meth:`list_accounts`.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_ids: Restrict the page to these mailbox ids (a bounded set).
            limit: Page size.
            cursor: The ``pagination.next_cursor`` of the previous page.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
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

    def list_accounts(
        self,
        *,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AccountStatus]:
        """List the status of every email account (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_ids: Restrict to these mailbox ids (a bounded set).
            limit: Page size.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/accounts",
            model=AccountStatus,
            query=drop_not_given(
                {
                    "email_ids": _csv(email_ids),
                    "limit": limit,
                }
            ),
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            account_id: The email account id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            period: ``"day"`` (default), ``"week"`` or ``"month"``.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
                "from": from_,
                "to": to,
            }
        )
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
    ) -> InboxTaggingReview:
        """Retrieve one page of the automatic inbox-tagging review.

        The page also carries ``enabled`` (whether tagging is switched on for the
        instance) and a ``summary``. To walk every decision automatically, use
        :meth:`list_inbox_tagging`.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            needs_review: Only decisions flagged for review.
            limit: Page size (1-200; the server defaults to 50).
            cursor: The ``pagination.next_cursor`` of the previous page.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "needs_review": needs_review,
                "limit": limit,
                "cursor": cursor,
            }
        )
        return self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
            query=query,
            options=options,
        )

    def list_inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[InboxTagDecision]:
        """List the inbox-tagging decisions (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            needs_review: Only decisions flagged for review.
            limit: Page size (1-200; the server defaults to 50).
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/inbox-tagging",
            model=InboxTagDecision,
            query=drop_not_given(
                {
                    "needs_review": needs_review,
                    "limit": limit,
                }
            ),
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            period: The window: ``"7d"`` (default), ``"30d"`` or ``"90d"``.
            campaign_ids: Narrow the campaign-derived sections to these campaigns (up to
                100). Account health stays workspace-wide.
            folder_ids: Narrow the campaign-derived sections to the campaigns in these
                folders (up to 100).
            from_: Ignored by the server, which reads *period*; kept for compatibility.
            to: Ignored by the server, which reads *period*; kept for compatibility.
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
        """Retrieve the direct-mail overview: hand-written mail sent from the mailboxes.

        Volume and replies come from the synced mailbox; opens and clicks cover only
        the mailboxes that opted into tracking them.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            period: The window: ``"7d"`` (default), ``"30d"`` or ``"90d"``. Anything
                else falls back to ``"7d"``.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
            }
        )
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve warmup analytics across mailboxes.

        The server requires both ``from_`` and ``to`` and rejects ``from_`` after ``to``.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_id: Restrict to one mailbox.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "email_id": email_id,
                "from": from_,
                "to": to,
            }
        )
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
        """Report where warmup mail landed (inbox, tabs, spam).

        The report breaks placement down per day and per recipient provider. The
        workspace report (no *email_id*) also lists each mailbox, worst rate first.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_id: Restrict to one mailbox; omit for the whole workspace.
            from_: Start day (``YYYY-MM-DD``). Defaults to 29 days before *to*.
            to: End day (``YYYY-MM-DD``). Defaults to today (UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "email_id": email_id,
                "from": from_,
                "to": to,
            }
        )
        return await self._get(
            "/analytics/warmup/placement",
            cast_to=WarmupPlacementReport,
            query=query,
            options=options,
        )

    async def compare_campaigns(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        The server requires both ``from_`` and ``to``.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            ids: The campaigns to compare (at most 10). The server requires at least
                one.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "ids": _csv(ids),
                "from": from_,
                "to": to,
            }
        )
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

        ``from_`` and ``to`` must be given together; without them the figures cover all time.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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

        The server requires both ``from_`` and ``to``.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the reporting window (``YYYY-MM-DD``, UTC).
            to: Optional end of the reporting window (``YYYY-MM-DD``, UTC).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve a campaign's hourly time-series analytics.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: The campaign id.
            date: The day to report (``YYYY-MM-DD``); defaults to today.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "date": date,
                "from": from_,
                "to": to,
            }
        )
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
        """Retrieve analytics across email accounts, one page at a time.

        The result carries ``pagination`` for the next page. To walk every page
        automatically, use :meth:`list_accounts`.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_ids: Restrict the page to these mailbox ids (a bounded set).
            limit: Page size.
            cursor: The ``pagination.next_cursor`` of the previous page.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
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

    def list_accounts(
        self,
        *,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AccountStatus]:
        """List the status of every email account (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            email_ids: Restrict to these mailbox ids (a bounded set).
            limit: Page size.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/accounts",
            model=AccountStatus,
            query=drop_not_given(
                {
                    "email_ids": _csv(email_ids),
                    "limit": limit,
                }
            ),
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            account_id: The email account id.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "from": from_,
                "to": to,
            }
        )
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            period: ``"day"`` (default), ``"week"`` or ``"month"``.
            from_: Optional start of the reporting window (RFC3339).
            to: Optional end of the reporting window (RFC3339).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "period": period,
                "from": from_,
                "to": to,
            }
        )
        return await self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )

    async def inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> InboxTaggingReview:
        """Retrieve one page of the automatic inbox-tagging review.

        The page also carries ``enabled`` (whether tagging is switched on for the
        instance) and a ``summary``. To walk every decision automatically, use
        :meth:`list_inbox_tagging`.

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            needs_review: Only decisions flagged for review.
            limit: Page size (1-200; the server defaults to 50).
            cursor: The ``pagination.next_cursor`` of the previous page.
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {
                "needs_review": needs_review,
                "limit": limit,
                "cursor": cursor,
            }
        )
        return await self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
            query=query,
            options=options,
        )

    def list_inbox_tagging(
        self,
        *,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[InboxTagDecision]:
        """List the inbox-tagging decisions (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            needs_review: Only decisions flagged for review.
            limit: Page size (1-200; the server defaults to 50).
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/analytics/inbox-tagging",
            model=InboxTagDecision,
            query=drop_not_given(
                {
                    "needs_review": needs_review,
                    "limit": limit,
                }
            ),
            options=options,
        )
