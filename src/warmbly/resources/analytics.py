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
    "AnalyticsResult",
    "AsyncAnalytics",
    "DirectMailAnalytics",
    "InboxTaggingReview",
    "InboxTaggingRow",
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


class DirectMailAnalytics(BaseModel):
    """Hand-written mail: volume and replies from the synced mailbox, plus
    opens and clicks for the mailboxes that opted into tracking them.

    ``volume`` holds ``sent``, ``received``, ``threads_started``, ``replied``,
    ``reply_rate``, ``bounced`` and ``median_reply_minutes``; ``tracking``
    holds ``mailboxes_opted_in``, ``mailboxes_total``, ``tracked_sent``,
    ``opened``, ``machine_opened``, ``clicked``, ``open_rate`` and
    ``click_rate``. The two halves are kept apart on purpose: untracked sends
    are not failures to open.
    """

    period: str | None = None
    volume: dict[str, Any] | None = None
    tracking: dict[str, Any] | None = None
    daily_trend: Sequence[dict[str, Any]] = []
    mailboxes: Sequence[dict[str, Any]] = []
    top_contacts: Sequence[dict[str, Any]] = []


class WarmupPlacementReport(BaseModel):
    """Where warmup mail landed (inbox, category tabs, spam) over a date
    range, for one mailbox or the whole workspace.

    ``rate`` is the headline inbox rate over the trailing window (``band`` is
    ``good``, ``fair``, ``poor``, ``collecting`` or ``none``); ``inbox_rate``
    is ``None`` until enough mail is delivered. ``mailboxes`` is present on the
    workspace report only, worst rate first.
    """

    email_account_id: str | None = None
    date_range: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None
    rate: dict[str, Any] | None = None
    daily: Sequence[dict[str, Any]] = []
    providers: Sequence[dict[str, Any]] = []
    mailboxes: Sequence[dict[str, Any]] = []


class InboxTaggingRow(BaseModel):
    """One automatic tagging verdict awaiting or past review.

    ``return_date`` (``YYYY-MM-DD``) is the out-of-office return date the
    model was asked to confirm, ``None`` when it was not asked. ``actions`` is
    what the workspace's switches let this verdict do.
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


class InboxTaggingReview(BaseModel):
    """One page of the inbox-tagging review list.

    ``enabled`` says whether tagging is switched on for the instance, so an
    empty list can be explained. ``summary`` has ``total``, ``needs_review``,
    ``from_offline`` and ``acted``. Pass ``pagination["next_cursor"]`` back as
    ``cursor`` for the next page.
    """

    enabled: bool | None = None
    data: Sequence[InboxTaggingRow] = []
    total: int | None = None
    summary: dict[str, Any] | None = None
    pagination: dict[str, Any] | None = None


def _csv(values: NotGivenOr[Sequence[str]]) -> NotGivenOr[str]:
    """Join a list into the comma-separated form the server expects."""
    if isinstance(values, NotGiven):
        return values
    if isinstance(values, str):
        return values
    return ",".join(values)


class Analytics(SyncAPIResource):
    """Synchronous ``analytics`` resource (read-only).

    Every method needs the ``read_analytics`` API-key permission. The server
    reads ``from`` / ``to`` as whole UTC days (``YYYY-MM-DD``).
    """

    def dashboard(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period, "from": from_, "to": to})
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
        """Retrieve analytics for hand-written mail (not campaign sends).

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
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
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        needs_review: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> InboxTaggingReview:
        """Retrieve one page of automatic inbox-tagging verdicts to review.

        Args:
            limit: Page size, 1 to 200 (default 50).
            cursor: ``pagination["next_cursor"]`` from a previous page.
            needs_review: Only verdicts flagged for review.
            options: Optional per-request overrides.
        """
        return self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
            query=drop_not_given(
                {"limit": limit, "cursor": cursor, "needs_review": needs_review}
            ),
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
            from_: Optional start of the reporting window.
            to: Optional end of the reporting window.
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
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics for the organization.

        Args:
            from_: Start of the reporting window (``YYYY-MM-DD``). The server
                requires both ``from_`` and ``to``.
            to: End of the reporting window (``YYYY-MM-DD``).
            email_id: Limit the report to one mailbox.
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
        """Report where warmup mail landed (inbox, tabs, spam) per day and per
        recipient provider.

        Args:
            from_: Start of the window (``YYYY-MM-DD``). Defaults to 29 days
                before ``to``.
            to: End of the window (``YYYY-MM-DD``). Defaults to today (UTC).
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

    def compare_campaigns(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            ids: The campaigns to compare (the server keeps the first 10 and
                requires at least one).
            from_: Start of the reporting window (``YYYY-MM-DD``, required by
                the server).
            to: End of the reporting window (``YYYY-MM-DD``, required by the
                server).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {"ids": _csv(ids), "from": from_, "to": to},
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

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the window (``YYYY-MM-DD``). Give it
                together with ``to``; with neither, the report covers all time.
            to: Optional end of the window (``YYYY-MM-DD``).
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
            from_: Start of the window (``YYYY-MM-DD``, required by the
                server).
            to: End of the window (``YYYY-MM-DD``, required by the server).
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
        """Retrieve a campaign's hourly analytics for one day.

        Args:
            campaign_id: The campaign id.
            date: The day (``YYYY-MM-DD``). Defaults to today.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
        """Retrieve the status of the organization's email accounts, one page.

        The result's ``data`` is the page and ``pagination`` carries
        ``next_cursor``; pass it back as ``cursor`` for the next page.

        Args:
            email_ids: Only these mailboxes (a bounded set; too many is a 400).
            limit: Page size.
            cursor: An opaque cursor from a previous page.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
        """Retrieve the status and detail of a single email account.

        Args:
            account_id: The email account id.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
            period: The window, ``day`` by default.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
    """Asynchronous ``analytics`` resource (read-only).

    Every method needs the ``read_analytics`` API-key permission. The server
    reads ``from`` / ``to`` as whole UTC days (``YYYY-MM-DD``).
    """

    async def dashboard(
        self,
        *,
        period: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve the top-level analytics dashboard summary.

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period, "from": from_, "to": to})
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
        """Retrieve analytics for hand-written mail (not campaign sends).

        Args:
            period: The window: ``7d`` (default), ``30d`` or ``90d``.
            options: Optional per-request overrides.
        """
        return await self._get(
            "/analytics/direct",
            cast_to=DirectMailAnalytics,
            query=drop_not_given({"period": period}),
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
        """Retrieve one page of automatic inbox-tagging verdicts to review.

        Args:
            limit: Page size, 1 to 200 (default 50).
            cursor: ``pagination["next_cursor"]`` from a previous page.
            needs_review: Only verdicts flagged for review.
            options: Optional per-request overrides.
        """
        return await self._get(
            "/analytics/inbox-tagging",
            cast_to=InboxTaggingReview,
            query=drop_not_given(
                {"limit": limit, "cursor": cursor, "needs_review": needs_review}
            ),
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
            from_: Optional start of the reporting window.
            to: Optional end of the reporting window.
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
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Retrieve warmup analytics for the organization.

        Args:
            from_: Start of the reporting window (``YYYY-MM-DD``). The server
                requires both ``from_`` and ``to``.
            to: End of the reporting window (``YYYY-MM-DD``).
            email_id: Limit the report to one mailbox.
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
        """Report where warmup mail landed (inbox, tabs, spam) per day and per
        recipient provider.

        Args:
            from_: Start of the window (``YYYY-MM-DD``). Defaults to 29 days
                before ``to``.
            to: End of the window (``YYYY-MM-DD``). Defaults to today (UTC).
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

    async def compare_campaigns(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AnalyticsResult:
        """Compare metrics across campaigns side by side.

        Args:
            ids: The campaigns to compare (the server keeps the first 10 and
                requires at least one).
            from_: Start of the reporting window (``YYYY-MM-DD``, required by
                the server).
            to: End of the reporting window (``YYYY-MM-DD``, required by the
                server).
            options: Optional per-request overrides.
        """
        query = drop_not_given(
            {"ids": _csv(ids), "from": from_, "to": to},
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

        Args:
            campaign_id: The campaign id.
            from_: Optional start of the window (``YYYY-MM-DD``). Give it
                together with ``to``; with neither, the report covers all time.
            to: Optional end of the window (``YYYY-MM-DD``).
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
            from_: Start of the window (``YYYY-MM-DD``, required by the
                server).
            to: End of the window (``YYYY-MM-DD``, required by the server).
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
        """Retrieve a campaign's hourly analytics for one day.

        Args:
            campaign_id: The campaign id.
            date: The day (``YYYY-MM-DD``). Defaults to today.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
        """Retrieve the status of the organization's email accounts, one page.

        The result's ``data`` is the page and ``pagination`` carries
        ``next_cursor``; pass it back as ``cursor`` for the next page.

        Args:
            email_ids: Only these mailboxes (a bounded set; too many is a 400).
            limit: Page size.
            cursor: An opaque cursor from a previous page.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
        """Retrieve the status and detail of a single email account.

        Args:
            account_id: The email account id.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
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
            period: The window, ``day`` by default.
            from_: Ignored by the server; kept for compatibility.
            to: Ignored by the server; kept for compatibility.
            options: Optional per-request overrides.
        """
        query = drop_not_given({"period": period, "from": from_, "to": to})
        return await self._get(
            "/analytics/usage",
            cast_to=AnalyticsResult,
            query=query,
            options=options,
        )
