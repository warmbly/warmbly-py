"""The ``meetings`` resource: booked calls as a first-class CRM list.

Maps to the ``/v1/meetings`` route group. Most rows arrive automatically from a
connected scheduling provider (Calendly, Cal.com); :meth:`Meetings.create`
exists for calls booked outside those, so the timeline stays complete.

A meeting is attributed to a contact by ``invitee_email``, or explicitly with
``contact_id``.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncMeetings",
    "Meeting",
    "MeetingCreated",
    "MeetingDeleted",
    "Meetings",
    "MeetingsSummary",
]


class Meeting(BaseModel):
    """A booked meeting."""

    id: str
    organization_id: str | None = None
    source: str | None = None
    external_event_id: str | None = None
    status: str | None = None
    invitee_email: str | None = None
    invitee_name: str | None = None
    event_name: str | None = None
    event_type: str | None = None
    scheduled_for: str | None = None
    end_time: str | None = None
    join_url: str | None = None
    location: str | None = None
    cancel_url: str | None = None
    reschedule_url: str | None = None
    canceled_reason: str | None = None
    contact_id: str | None = None
    contact_name: str | None = None
    campaign_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MeetingCreated(BaseModel):
    """The meeting a manual booking created."""

    meeting: Meeting | None = None


class MeetingDeleted(BaseModel):
    """The result of deleting a meeting."""

    deleted: bool | None = None


class MeetingsSummary(BaseModel):
    """Counts behind the meetings header and sidebar."""

    upcoming: int | None = None
    today: int | None = None
    total: int | None = None
    canceled: int | None = None


class Meetings(SyncAPIResource):
    """Synchronous ``meetings`` resource."""

    def list(
        self,
        *,
        timeframe: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Meeting]:
        """List meetings (auto-paginating).

        Args:
            timeframe: ``"upcoming"`` or ``"past"``; omit for all.
            status: Restrict to one booking status.
            q: Match the invitee name, invitee email, or event name.
            limit: Page size (1-200).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/meetings",
            model=Meeting,
            query={
                "timeframe": timeframe,
                "status": status,
                "q": q,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def summary(self, *, options: RequestOptions | None = None) -> MeetingsSummary:
        """Return the upcoming / today / total / canceled counts."""
        return self._get("/meetings/summary", cast_to=MeetingsSummary, options=options)

    def create(
        self,
        *,
        title: str,
        invitee_email: str,
        scheduled_for: str,
        invitee_name: NotGivenOr[str] = NOT_GIVEN,
        duration_minutes: NotGivenOr[int] = NOT_GIVEN,
        location: NotGivenOr[str] = NOT_GIVEN,
        join_url: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> MeetingCreated:
        """Log a meeting booked outside a connected provider.

        Args:
            title: What the meeting is called.
            invitee_email: The attendee's address; used to attribute the
                meeting to a contact when *contact_id* is omitted.
            scheduled_for: RFC 3339 start time.
            invitee_name: The attendee's name.
            duration_minutes: How long the meeting runs.
            location: Where it happens.
            join_url: A video-call link.
            contact_id: Attribute to this contact explicitly.
        """
        return self._post(
            "/meetings",
            cast_to=MeetingCreated,
            body=drop_not_given(
                {
                    "title": title,
                    "invitee_email": invitee_email,
                    "scheduled_for": scheduled_for,
                    "invitee_name": invitee_name,
                    "duration_minutes": duration_minutes,
                    "location": location,
                    "join_url": join_url,
                    "contact_id": contact_id,
                }
            ),
            options=options,
        )

    def delete(
        self, meeting_id: str, *, options: RequestOptions | None = None
    ) -> MeetingDeleted:
        """Delete a meeting from the list."""
        return self._delete(
            f"/meetings/{meeting_id}", cast_to=MeetingDeleted, options=options
        )


class AsyncMeetings(AsyncAPIResource):
    """Asynchronous ``meetings`` resource."""

    def list(
        self,
        *,
        timeframe: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Meeting]:
        """List meetings (auto-paginating).

        Args:
            timeframe: ``"upcoming"`` or ``"past"``; omit for all.
            status: Restrict to one booking status.
            q: Match the invitee name, invitee email, or event name.
            limit: Page size (1-200).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/meetings",
            model=Meeting,
            query={
                "timeframe": timeframe,
                "status": status,
                "q": q,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def summary(
        self, *, options: RequestOptions | None = None
    ) -> MeetingsSummary:
        """Return the upcoming / today / total / canceled counts."""
        return await self._get(
            "/meetings/summary", cast_to=MeetingsSummary, options=options
        )

    async def create(
        self,
        *,
        title: str,
        invitee_email: str,
        scheduled_for: str,
        invitee_name: NotGivenOr[str] = NOT_GIVEN,
        duration_minutes: NotGivenOr[int] = NOT_GIVEN,
        location: NotGivenOr[str] = NOT_GIVEN,
        join_url: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> MeetingCreated:
        """Log a meeting booked outside a connected provider.

        Args:
            title: What the meeting is called.
            invitee_email: The attendee's address; used to attribute the
                meeting to a contact when *contact_id* is omitted.
            scheduled_for: RFC 3339 start time.
            invitee_name: The attendee's name.
            duration_minutes: How long the meeting runs.
            location: Where it happens.
            join_url: A video-call link.
            contact_id: Attribute to this contact explicitly.
        """
        return await self._post(
            "/meetings",
            cast_to=MeetingCreated,
            body=drop_not_given(
                {
                    "title": title,
                    "invitee_email": invitee_email,
                    "scheduled_for": scheduled_for,
                    "invitee_name": invitee_name,
                    "duration_minutes": duration_minutes,
                    "location": location,
                    "join_url": join_url,
                    "contact_id": contact_id,
                }
            ),
            options=options,
        )

    async def delete(
        self, meeting_id: str, *, options: RequestOptions | None = None
    ) -> MeetingDeleted:
        """Delete a meeting from the list."""
        return await self._delete(
            f"/meetings/{meeting_id}", cast_to=MeetingDeleted, options=options
        )
