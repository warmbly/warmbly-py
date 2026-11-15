"""The ``reports`` resource: the ``/v1/reports`` route group.

Client reports are analytics shared outside the workspace. A report is a
saved, scoped view of campaign, reply and mailbox numbers that the workspace
shares with its client by public link (rendered at ``/r/<token>``) and can
email on a weekly or monthly schedule.

Reading reports needs the ``READ_ANALYTICS`` API permission. Creating,
changing or deleting a report, its share link or its schedule needs
``MANAGE_REPORTS``, because a link shows the numbers to anyone who has it.
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
    "AsyncReports",
    "Report",
    "ReportAccess",
    "ReportCampaign",
    "ReportDay",
    "ReportDeleted",
    "ReportLink",
    "ReportLinkCreated",
    "ReportMailboxes",
    "ReportOverview",
    "ReportPreview",
    "ReportReply",
    "ReportSchedule",
    "ReportSections",
    "Reports",
]


class ReportAccess(BaseModel):
    """Which campaigns, folders and mailboxes a report covers.

    ``scope`` is ``workspace`` (everything; the id lists are empty) or
    ``restricted`` (only the listed folders, campaigns and mailboxes).
    """

    scope: str | None = None
    campaign_folder_ids: Sequence[str] | None = None
    campaign_ids: Sequence[str] | None = None
    email_account_ids: Sequence[str] | None = None


class ReportSections(BaseModel):
    """The parts of a report that are shown."""

    overview: bool | None = None
    campaigns: bool | None = None
    replies: bool | None = None
    positive_replies: bool | None = None
    mailboxes: bool | None = None
    daily_chart: bool | None = None


class ReportLink(BaseModel):
    """The state of a report's share link.

    The link URL itself is only returned once, by
    :meth:`Reports.create_link`. ``hint`` is the token's first characters, so
    a person can tell links apart.
    """

    hint: str | None = None
    created_at: str | None = None
    expires_at: str | None = None
    expired: bool | None = None


class ReportSchedule(BaseModel):
    """When a report is emailed and to whom.

    ``cadence`` is ``weekly`` or ``monthly``. ``weekday`` is 0 (Sunday) to 6
    and is used by weekly schedules; ``month_day`` is 1 to 28 and is used by
    monthly schedules. ``hour`` is 0 to 23 in ``timezone`` (an IANA zone).
    """

    recipients: Sequence[str] | None = None
    cadence: str | None = None
    weekday: int | None = None
    month_day: int | None = None
    hour: int | None = None
    timezone: str | None = None
    paused: bool | None = None
    last_sent_at: str | None = None
    next_run_at: str | None = None


class Report(BaseModel):
    """A saved, scoped report a workspace shares with its client.

    ``date_range`` is the default period: ``last_7_days``, ``last_30_days``,
    ``this_month`` or ``last_month``. ``link`` and ``schedule`` are ``None``
    when the report has no share link or no email schedule.
    """

    id: str
    created_by: str | None = None
    name: str | None = None
    access: ReportAccess | None = None
    sections: ReportSections | None = None
    show_reply_snippets: bool | None = None
    date_range: str | None = None
    link: ReportLink | None = None
    schedule: ReportSchedule | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ReportLinkCreated(BaseModel):
    """A freshly minted share link.

    ``url`` and ``token`` are bearer secrets: anyone holding them can read the
    report, and this response is the only time they are shown. Both are kept
    out of ``repr``.
    """

    url: str | None = Field(default=None, repr=False)
    token: str | None = Field(default=None, repr=False)
    link: ReportLink | None = None
    report: Report | None = None


class ReportOverview(BaseModel):
    """The KPI row of a rendered report.

    ``open_rate`` is of ``open_tracked_sent`` (the sends that carried an open
    pixel). ``positive`` and ``positive_rate`` are ``None`` when the positive
    replies section is off.
    """

    sent: int | None = None
    opened: int | None = None
    open_tracked_sent: int | None = None
    open_rate: float | None = None
    clicked: int | None = None
    replied: int | None = None
    reply_rate: float | None = None
    positive: int | None = None
    positive_rate: float | None = None
    bounced: int | None = None
    bounce_rate: float | None = None


class ReportDay(BaseModel):
    """One day of the daily chart (``date`` is ``YYYY-MM-DD``)."""

    date: str | None = None
    sent: int | None = None
    opens: int | None = None
    replies: int | None = None


class ReportCampaign(BaseModel):
    """One row of the campaign table.

    ``positive`` is ``None`` when the positive replies section is off.
    """

    name: str | None = None
    status: str | None = None
    sent: int | None = None
    opens: int | None = None
    open_tracked_sent: int | None = None
    open_rate: float | None = None
    clicks: int | None = None
    replies: int | None = None
    reply_rate: float | None = None
    positive: int | None = None
    bounces: int | None = None
    bounce_rate: float | None = None


class ReportReply(BaseModel):
    """One reply in the replies list.

    ``snippet`` is set only when the report shows reply snippets.
    """

    name: str | None = None
    email: str | None = None
    campaign: str | None = None
    subject: str | None = None
    replied_at: str | None = None
    classification: str | None = None
    snippet: str | None = None


class ReportMailboxes(BaseModel):
    """The mailbox health and warmup summary."""

    total: int | None = None
    healthy: int | None = None
    warning: int | None = None
    error: int | None = None
    warmup_sent: int | None = None
    warmup_received: int | None = None
    warmup_replied: int | None = None


class ReportPreview(BaseModel):
    """A rendered report, as the public page shows it.

    ``from_`` (JSON ``from``) and ``to`` are the covered UTC days. Sections
    that are switched off are ``None`` (or empty).
    """

    name: str | None = None
    date_range: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    generated_at: str | None = None
    sections: ReportSections | None = None
    show_reply_snippets: bool | None = None
    overview: ReportOverview | None = None
    daily: Sequence[ReportDay] | None = None
    campaigns: Sequence[ReportCampaign] | None = None
    replies: Sequence[ReportReply] | None = None
    mailboxes: ReportMailboxes | None = None


class ReportDeleted(BaseModel):
    """The result of deleting a report.

    ``DELETE /reports/{id}`` answers ``204 No Content``, so every field is
    ``None`` on a successful delete; the object exists so the call has a
    uniform return type.
    """

    id: str | None = None
    deleted: bool | None = None


def _report_body(
    *,
    name: NotGivenOr[str],
    access: NotGivenOr[Mapping[str, Any]],
    sections: NotGivenOr[Mapping[str, bool]],
    show_reply_snippets: NotGivenOr[bool],
    date_range: NotGivenOr[str],
) -> dict[str, object]:
    return drop_not_given(
        {
            "name": name,
            "access": dict(access) if isinstance(access, Mapping) else access,
            "sections": dict(sections) if isinstance(sections, Mapping) else sections,
            "show_reply_snippets": show_reply_snippets,
            "date_range": date_range,
        }
    )


def _schedule_body(
    *,
    recipients: Sequence[str],
    cadence: str,
    weekday: NotGivenOr[int],
    month_day: NotGivenOr[int],
    hour: NotGivenOr[int],
    timezone: NotGivenOr[str],
    paused: NotGivenOr[bool],
) -> dict[str, object]:
    return drop_not_given(
        {
            "recipients": list(recipients),
            "cadence": cadence,
            "weekday": weekday,
            "month_day": month_day,
            "hour": hour,
            "timezone": timezone,
            "paused": paused,
        }
    )


class Reports(SyncAPIResource):
    """Synchronous ``reports`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Report]:
        """List the workspace's client reports, auto-paging.

        Requires the ``READ_ANALYTICS`` API permission.

        Args:
            limit: Page size, 1 to 100 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/reports",
            model=Report,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    def create(
        self,
        *,
        name: str,
        access: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sections: NotGivenOr[Mapping[str, bool]] = NOT_GIVEN,
        show_reply_snippets: NotGivenOr[bool] = NOT_GIVEN,
        date_range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Report:
        """Create a client report. A workspace keeps at most 200.

        Requires the ``MANAGE_REPORTS`` API permission.

        Args:
            name: The report's name.
            access: What it covers, ``{"scope": "workspace"}`` (the default)
                or ``{"scope": "restricted", "campaign_ids": [...],
                "campaign_folder_ids": [...], "email_account_ids": [...]}``.
            sections: Which sections show, keyed ``overview``, ``campaigns``,
                ``replies``, ``positive_replies``, ``mailboxes`` and
                ``daily_chart``. Defaults to all on; a key left out of the
                mapping is off, and at least one must be on.
            show_reply_snippets: Whether replies show a body snippet
                (default off).
            date_range: The default period, one of ``last_7_days``,
                ``last_30_days`` (the default), ``this_month`` or
                ``last_month``.
        """
        return self._post(
            "/reports",
            cast_to=Report,
            body=_report_body(
                name=name,
                access=access,
                sections=sections,
                show_reply_snippets=show_reply_snippets,
                date_range=date_range,
            ),
            options=options,
        )

    def retrieve(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> Report:
        """Fetch one client report.

        Requires the ``READ_ANALYTICS`` API permission.
        """
        return self._get(f"/reports/{report_id}", cast_to=Report, options=options)

    def preview(
        self,
        report_id: str,
        *,
        range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ReportPreview:
        """Render a report with live numbers, as its public page would.

        Requires the ``READ_ANALYTICS`` API permission.

        Args:
            report_id: The report to render.
            range: The period to cover, one of ``last_7_days``,
                ``last_30_days``, ``this_month`` or ``last_month``. Defaults
                to the report's own ``date_range``.
        """
        return self._get(
            f"/reports/{report_id}/preview",
            cast_to=ReportPreview,
            query=drop_not_given({"range": range}),
            options=options,
        )

    def update(
        self,
        report_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        access: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sections: NotGivenOr[Mapping[str, bool]] = NOT_GIVEN,
        show_reply_snippets: NotGivenOr[bool] = NOT_GIVEN,
        date_range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Report:
        """Change a client report. Omitted arguments keep their value.

        Requires the ``MANAGE_REPORTS`` API permission.

        Args:
            report_id: The report to change.
            name: A new name.
            access: A new scope, replacing the old one whole (see
                :meth:`create`).
            sections: A new section set, replacing the old one whole: a key
                left out of the mapping is turned off.
            show_reply_snippets: Whether replies show a body snippet.
            date_range: The default period, one of ``last_7_days``,
                ``last_30_days``, ``this_month`` or ``last_month``.
        """
        return self._patch(
            f"/reports/{report_id}",
            cast_to=Report,
            body=_report_body(
                name=name,
                access=access,
                sections=sections,
                show_reply_snippets=show_reply_snippets,
                date_range=date_range,
            ),
            options=options,
        )

    def delete(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> ReportDeleted:
        """Delete a client report, its share link and its schedule.

        Requires the ``MANAGE_REPORTS`` API permission.
        """
        return self._delete(
            f"/reports/{report_id}", cast_to=ReportDeleted, options=options
        )

    def create_link(
        self,
        report_id: str,
        *,
        expires_in_days: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ReportLinkCreated:
        """Mint a public share link, replacing any earlier one.

        The returned ``url`` and ``token`` are shown only this once. Requires
        the ``MANAGE_REPORTS`` API permission.

        Args:
            report_id: The report to share.
            expires_in_days: The link's lifetime, 1 to 365 days (default 90).
        """
        return self._post(
            f"/reports/{report_id}/link",
            cast_to=ReportLinkCreated,
            body=drop_not_given({"expires_in_days": expires_in_days}),
            options=options,
        )

    def revoke_link(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> Report:
        """Revoke a report's share link, returning the updated report.

        Requires the ``MANAGE_REPORTS`` API permission.
        """
        return self._delete(
            f"/reports/{report_id}/link", cast_to=Report, options=options
        )

    def set_schedule(
        self,
        report_id: str,
        *,
        recipients: Sequence[str],
        cadence: str,
        weekday: NotGivenOr[int] = NOT_GIVEN,
        month_day: NotGivenOr[int] = NOT_GIVEN,
        hour: NotGivenOr[int] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        paused: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Report:
        """Set (create or replace) a report's email schedule.

        The schedule is replaced whole: an omitted argument takes its default,
        not its previous value. Requires the ``MANAGE_REPORTS`` API
        permission.

        Args:
            report_id: The report to schedule.
            recipients: Up to 10 email addresses.
            cadence: ``weekly`` (emails cover the last 7 days) or ``monthly``
                (emails cover last month).
            weekday: For weekly schedules, 0 (Sunday) to 6 (default 0).
            month_day: For monthly schedules, 1 to 28 (default 1).
            hour: The hour to send, 0 to 23 (default 0).
            timezone: An IANA zone such as ``Europe/London`` (default UTC).
            paused: Keep the schedule but send nothing (default off).
        """
        return self._put(
            f"/reports/{report_id}/schedule",
            cast_to=Report,
            body=_schedule_body(
                recipients=recipients,
                cadence=cadence,
                weekday=weekday,
                month_day=month_day,
                hour=hour,
                timezone=timezone,
                paused=paused,
            ),
            options=options,
        )

    def delete_schedule(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> Report:
        """Remove a report's email schedule, returning the updated report.

        Requires the ``MANAGE_REPORTS`` API permission.
        """
        return self._delete(
            f"/reports/{report_id}/schedule", cast_to=Report, options=options
        )


class AsyncReports(AsyncAPIResource):
    """Asynchronous ``reports`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Report]:
        """List the workspace's client reports, auto-paging.

        Requires the ``READ_ANALYTICS`` API permission.

        Args:
            limit: Page size, 1 to 100 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/reports",
            model=Report,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    async def create(
        self,
        *,
        name: str,
        access: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sections: NotGivenOr[Mapping[str, bool]] = NOT_GIVEN,
        show_reply_snippets: NotGivenOr[bool] = NOT_GIVEN,
        date_range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Report:
        """Create a client report. A workspace keeps at most 200.

        Requires the ``MANAGE_REPORTS`` API permission.

        Args:
            name: The report's name.
            access: What it covers, ``{"scope": "workspace"}`` (the default)
                or ``{"scope": "restricted", "campaign_ids": [...],
                "campaign_folder_ids": [...], "email_account_ids": [...]}``.
            sections: Which sections show, keyed ``overview``, ``campaigns``,
                ``replies``, ``positive_replies``, ``mailboxes`` and
                ``daily_chart``. Defaults to all on; a key left out of the
                mapping is off, and at least one must be on.
            show_reply_snippets: Whether replies show a body snippet
                (default off).
            date_range: The default period, one of ``last_7_days``,
                ``last_30_days`` (the default), ``this_month`` or
                ``last_month``.
        """
        return await self._post(
            "/reports",
            cast_to=Report,
            body=_report_body(
                name=name,
                access=access,
                sections=sections,
                show_reply_snippets=show_reply_snippets,
                date_range=date_range,
            ),
            options=options,
        )

    async def retrieve(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> Report:
        """Fetch one client report.

        Requires the ``READ_ANALYTICS`` API permission.
        """
        return await self._get(f"/reports/{report_id}", cast_to=Report, options=options)

    async def preview(
        self,
        report_id: str,
        *,
        range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ReportPreview:
        """Render a report with live numbers, as its public page would.

        Requires the ``READ_ANALYTICS`` API permission.

        Args:
            report_id: The report to render.
            range: The period to cover, one of ``last_7_days``,
                ``last_30_days``, ``this_month`` or ``last_month``. Defaults
                to the report's own ``date_range``.
        """
        return await self._get(
            f"/reports/{report_id}/preview",
            cast_to=ReportPreview,
            query=drop_not_given({"range": range}),
            options=options,
        )

    async def update(
        self,
        report_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        access: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sections: NotGivenOr[Mapping[str, bool]] = NOT_GIVEN,
        show_reply_snippets: NotGivenOr[bool] = NOT_GIVEN,
        date_range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Report:
        """Change a client report. Omitted arguments keep their value.

        Requires the ``MANAGE_REPORTS`` API permission.

        Args:
            report_id: The report to change.
            name: A new name.
            access: A new scope, replacing the old one whole (see
                :meth:`create`).
            sections: A new section set, replacing the old one whole: a key
                left out of the mapping is turned off.
            show_reply_snippets: Whether replies show a body snippet.
            date_range: The default period, one of ``last_7_days``,
                ``last_30_days``, ``this_month`` or ``last_month``.
        """
        return await self._patch(
            f"/reports/{report_id}",
            cast_to=Report,
            body=_report_body(
                name=name,
                access=access,
                sections=sections,
                show_reply_snippets=show_reply_snippets,
                date_range=date_range,
            ),
            options=options,
        )

    async def delete(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> ReportDeleted:
        """Delete a client report, its share link and its schedule.

        Requires the ``MANAGE_REPORTS`` API permission.
        """
        return await self._delete(
            f"/reports/{report_id}", cast_to=ReportDeleted, options=options
        )

    async def create_link(
        self,
        report_id: str,
        *,
        expires_in_days: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ReportLinkCreated:
        """Mint a public share link, replacing any earlier one.

        The returned ``url`` and ``token`` are shown only this once. Requires
        the ``MANAGE_REPORTS`` API permission.

        Args:
            report_id: The report to share.
            expires_in_days: The link's lifetime, 1 to 365 days (default 90).
        """
        return await self._post(
            f"/reports/{report_id}/link",
            cast_to=ReportLinkCreated,
            body=drop_not_given({"expires_in_days": expires_in_days}),
            options=options,
        )

    async def revoke_link(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> Report:
        """Revoke a report's share link, returning the updated report.

        Requires the ``MANAGE_REPORTS`` API permission.
        """
        return await self._delete(
            f"/reports/{report_id}/link", cast_to=Report, options=options
        )

    async def set_schedule(
        self,
        report_id: str,
        *,
        recipients: Sequence[str],
        cadence: str,
        weekday: NotGivenOr[int] = NOT_GIVEN,
        month_day: NotGivenOr[int] = NOT_GIVEN,
        hour: NotGivenOr[int] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        paused: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Report:
        """Set (create or replace) a report's email schedule.

        The schedule is replaced whole: an omitted argument takes its default,
        not its previous value. Requires the ``MANAGE_REPORTS`` API
        permission.

        Args:
            report_id: The report to schedule.
            recipients: Up to 10 email addresses.
            cadence: ``weekly`` (emails cover the last 7 days) or ``monthly``
                (emails cover last month).
            weekday: For weekly schedules, 0 (Sunday) to 6 (default 0).
            month_day: For monthly schedules, 1 to 28 (default 1).
            hour: The hour to send, 0 to 23 (default 0).
            timezone: An IANA zone such as ``Europe/London`` (default UTC).
            paused: Keep the schedule but send nothing (default off).
        """
        return await self._put(
            f"/reports/{report_id}/schedule",
            cast_to=Report,
            body=_schedule_body(
                recipients=recipients,
                cadence=cadence,
                weekday=weekday,
                month_day=month_day,
                hour=hour,
                timezone=timezone,
                paused=paused,
            ),
            options=options,
        )

    async def delete_schedule(
        self, report_id: str, *, options: RequestOptions | None = None
    ) -> Report:
        """Remove a report's email schedule, returning the updated report.

        Requires the ``MANAGE_REPORTS`` API permission.
        """
        return await self._delete(
            f"/reports/{report_id}/schedule", cast_to=Report, options=options
        )
