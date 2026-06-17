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

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "Analytics",
    "AnalyticsResult",
    "AsyncAnalytics",
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

    from_: str | None = None
    to: str | None = None
    interval: str | None = None
    totals: dict[str, Any] | None = None
    series: Sequence[dict[str, Any]] | None = None
    data: Sequence[dict[str, Any]] | None = None


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
