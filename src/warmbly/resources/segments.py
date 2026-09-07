"""The ``segments`` resource: saved, reusable contact audiences.

Maps to the ``/v1/segments`` route group. A segment is a list of conditions
over contacts plus per-contact manual overrides; membership is evaluated at
read time, so a segment always reflects the contacts as they are now.

Conditions name a *field* (``"email_domain"``, ``"last_replied_at"``, or a
custom field as ``"custom.industry"``), an *operator*, and either ``value``
(scalar operators) or ``values`` (list operators such as ``in``). Which
operators a field accepts depends on its kind; :meth:`Segments.fields` returns
the catalog the dashboard's condition builder is driven from.

Linking a segment to a campaign (``campaigns.set_segments``) makes it a live
audience source: members are enrolled as leads and kept current.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncSegments",
    "Segment",
    "SegmentAddedToCampaign",
    "SegmentDeleted",
    "SegmentField",
    "SegmentMemberModes",
    "SegmentMembersUpdated",
    "SegmentOverride",
    "SegmentPreview",
    "Segments",
]


class Segment(BaseModel):
    """A saved contact audience.

    ``match`` is ``"all"`` or ``"any"``: whether every condition or any one of
    them must hold. ``contact_count`` is the live membership size, while
    ``included_count`` and ``excluded_count`` are the manual overrides pinning
    contacts in or out regardless of the conditions.
    """

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    name: str | None = None
    description: str | None = None
    color: str | None = None
    match: str | None = None
    conditions: Sequence[dict[str, Any]] = []
    contact_count: int | None = None
    included_count: int | None = None
    excluded_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SegmentDeleted(BaseModel):
    """The result of deleting a segment (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class SegmentField(BaseModel):
    """One filterable field, with the operators its ``kind`` accepts.

    ``kind`` is one of ``text``, ``enum``, ``bool``, ``date``, ``number``,
    ``category``, ``campaign`` or ``segment``; ``options`` lists the accepted
    values of an enum field.
    """

    field: str | None = None
    label: str | None = None
    group: str | None = None
    kind: str | None = None
    options: Sequence[str] = []


class SegmentPreview(BaseModel):
    """How many contacts an unsaved definition would match."""

    contact_count: int | None = None


class SegmentMembersUpdated(BaseModel):
    """How many contacts a manual override actually changed."""

    updated: int | None = None


class SegmentMemberModes(BaseModel):
    """The manual override of each looked-up contact.

    ``data`` maps a contact id to ``"include"``, ``"exclude"``, or ``"auto"``
    when the conditions alone decide.
    """

    data: dict[str, str] = {}


class SegmentOverride(BaseModel):
    """One contact pinned into or out of a segment."""

    contact_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    company: str | None = None
    mode: str | None = None
    created_at: str | None = None


class SegmentAddedToCampaign(BaseModel):
    """The result of enrolling a segment's members as campaign leads.

    ``members`` is the segment's size at enrol time and ``added`` how many of
    those were not already leads of the campaign.
    """

    campaign_id: str | None = None
    added: int | None = None
    members: int | None = None


def _segment_body(
    *,
    name: NotGivenOr[str],
    description: NotGivenOr[str],
    color: NotGivenOr[str],
    match: NotGivenOr[str],
    conditions: NotGivenOr[Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Build the create/update body (they share one field set)."""
    return drop_not_given(
        {
            "name": name,
            "description": description,
            "color": color,
            "match": match,
            "conditions": conditions,
        }
    )


class Segments(SyncAPIResource):
    """Synchronous ``segments`` resource."""

    def list(self, *, options: RequestOptions | None = None) -> SyncCursorPage[Segment]:
        """List the organization's segments."""
        return self._get_api_list("/segments", model=Segment, options=options)

    def fields(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[SegmentField]:
        """List every field a condition may name, with its kind and options."""
        return self._get_api_list(
            "/segments/fields", model=SegmentField, options=options
        )

    def preview(
        self,
        *,
        match: str,
        conditions: Sequence[Mapping[str, Any]],
        segment_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SegmentPreview:
        """Count the contacts an unsaved definition would match.

        Args:
            match: ``"all"`` or ``"any"``.
            conditions: The conditions to evaluate.
            segment_id: An existing segment whose manual overrides should be
                kept in the count, for previewing an edit.
        """
        return self._post(
            "/segments/preview",
            cast_to=SegmentPreview,
            body=drop_not_given(
                {"id": segment_id, "match": match, "conditions": conditions}
            ),
            options=options,
        )

    def create(
        self,
        *,
        name: str,
        conditions: Sequence[Mapping[str, Any]],
        match: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Segment:
        """Create a segment.

        Args:
            name: A human-readable name.
            conditions: The membership conditions.
            match: ``"all"`` (default) or ``"any"``.
            description: An optional longer description.
            color: A ``#rrggbb`` swatch for the dashboard.
        """
        return self._post(
            "/segments",
            cast_to=Segment,
            body=_segment_body(
                name=name,
                description=description,
                color=color,
                match=match,
                conditions=conditions,
            ),
            options=options,
        )

    def retrieve(
        self, segment_id: str, *, options: RequestOptions | None = None
    ) -> Segment:
        """Retrieve a single segment by id."""
        return self._get(f"/segments/{segment_id}", cast_to=Segment, options=options)

    def update(
        self,
        segment_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        match: NotGivenOr[str] = NOT_GIVEN,
        conditions: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Segment:
        """Update a segment. Omitted fields keep their stored value."""
        return self._patch(
            f"/segments/{segment_id}",
            cast_to=Segment,
            body=_segment_body(
                name=name,
                description=description,
                color=color,
                match=match,
                conditions=conditions,
            ),
            options=options,
        )

    def delete(
        self, segment_id: str, *, options: RequestOptions | None = None
    ) -> SegmentDeleted:
        """Delete a segment. The contacts themselves are untouched."""
        return self._delete(
            f"/segments/{segment_id}", cast_to=SegmentDeleted, options=options
        )

    def set_members(
        self,
        segment_id: str,
        *,
        contacts: Sequence[str],
        mode: str,
        options: RequestOptions | None = None,
    ) -> SegmentMembersUpdated:
        """Pin contacts into or out of a segment.

        Args:
            segment_id: The segment id.
            contacts: The contact ids to override.
            mode: ``"include"``, ``"exclude"``, or ``"auto"`` to clear the
                override so the conditions decide again.
        """
        return self._post(
            f"/segments/{segment_id}/members",
            cast_to=SegmentMembersUpdated,
            body={"contacts": list(contacts), "mode": mode},
            options=options,
        )

    def member_modes(
        self,
        segment_id: str,
        *,
        contacts: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SegmentMemberModes:
        """Report the manual override carried by each of *contacts*."""
        return self._post(
            f"/segments/{segment_id}/members/lookup",
            cast_to=SegmentMemberModes,
            body={"contacts": list(contacts)},
            options=options,
        )

    def overrides(
        self, segment_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[SegmentOverride]:
        """List the contacts manually pinned into or out of a segment."""
        return self._get_api_list(
            f"/segments/{segment_id}/overrides",
            model=SegmentOverride,
            options=options,
        )

    def add_to_campaign(
        self,
        segment_id: str,
        *,
        campaign_id: str,
        options: RequestOptions | None = None,
    ) -> SegmentAddedToCampaign:
        """Enroll the segment's current members as leads of a campaign.

        This is a one-off copy. To keep the audience live, link the segment to
        the campaign with :meth:`Campaigns.set_segments` instead.
        """
        return self._post(
            f"/segments/{segment_id}/add-to-campaign",
            cast_to=SegmentAddedToCampaign,
            body={"campaign_id": campaign_id},
            options=options,
        )


class AsyncSegments(AsyncAPIResource):
    """Asynchronous ``segments`` resource."""

    def list(self, *, options: RequestOptions | None = None) -> AsyncPaginator[Segment]:
        """List the organization's segments."""
        return self._get_api_list("/segments", model=Segment, options=options)

    def fields(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[SegmentField]:
        """List every field a condition may name, with its kind and options."""
        return self._get_api_list(
            "/segments/fields", model=SegmentField, options=options
        )

    async def preview(
        self,
        *,
        match: str,
        conditions: Sequence[Mapping[str, Any]],
        segment_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SegmentPreview:
        """Count the contacts an unsaved definition would match.

        Args:
            match: ``"all"`` or ``"any"``.
            conditions: The conditions to evaluate.
            segment_id: An existing segment whose manual overrides should be
                kept in the count, for previewing an edit.
        """
        return await self._post(
            "/segments/preview",
            cast_to=SegmentPreview,
            body=drop_not_given(
                {"id": segment_id, "match": match, "conditions": conditions}
            ),
            options=options,
        )

    async def create(
        self,
        *,
        name: str,
        conditions: Sequence[Mapping[str, Any]],
        match: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Segment:
        """Create a segment.

        Args:
            name: A human-readable name.
            conditions: The membership conditions.
            match: ``"all"`` (default) or ``"any"``.
            description: An optional longer description.
            color: A ``#rrggbb`` swatch for the dashboard.
        """
        return await self._post(
            "/segments",
            cast_to=Segment,
            body=_segment_body(
                name=name,
                description=description,
                color=color,
                match=match,
                conditions=conditions,
            ),
            options=options,
        )

    async def retrieve(
        self, segment_id: str, *, options: RequestOptions | None = None
    ) -> Segment:
        """Retrieve a single segment by id."""
        return await self._get(
            f"/segments/{segment_id}", cast_to=Segment, options=options
        )

    async def update(
        self,
        segment_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        match: NotGivenOr[str] = NOT_GIVEN,
        conditions: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Segment:
        """Update a segment. Omitted fields keep their stored value."""
        return await self._patch(
            f"/segments/{segment_id}",
            cast_to=Segment,
            body=_segment_body(
                name=name,
                description=description,
                color=color,
                match=match,
                conditions=conditions,
            ),
            options=options,
        )

    async def delete(
        self, segment_id: str, *, options: RequestOptions | None = None
    ) -> SegmentDeleted:
        """Delete a segment. The contacts themselves are untouched."""
        return await self._delete(
            f"/segments/{segment_id}", cast_to=SegmentDeleted, options=options
        )

    async def set_members(
        self,
        segment_id: str,
        *,
        contacts: Sequence[str],
        mode: str,
        options: RequestOptions | None = None,
    ) -> SegmentMembersUpdated:
        """Pin contacts into or out of a segment.

        Args:
            segment_id: The segment id.
            contacts: The contact ids to override.
            mode: ``"include"``, ``"exclude"``, or ``"auto"`` to clear the
                override so the conditions decide again.
        """
        return await self._post(
            f"/segments/{segment_id}/members",
            cast_to=SegmentMembersUpdated,
            body={"contacts": list(contacts), "mode": mode},
            options=options,
        )

    async def member_modes(
        self,
        segment_id: str,
        *,
        contacts: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SegmentMemberModes:
        """Report the manual override carried by each of *contacts*."""
        return await self._post(
            f"/segments/{segment_id}/members/lookup",
            cast_to=SegmentMemberModes,
            body={"contacts": list(contacts)},
            options=options,
        )

    def overrides(
        self, segment_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[SegmentOverride]:
        """List the contacts manually pinned into or out of a segment."""
        return self._get_api_list(
            f"/segments/{segment_id}/overrides",
            model=SegmentOverride,
            options=options,
        )

    async def add_to_campaign(
        self,
        segment_id: str,
        *,
        campaign_id: str,
        options: RequestOptions | None = None,
    ) -> SegmentAddedToCampaign:
        """Enroll the segment's current members as leads of a campaign.

        This is a one-off copy. To keep the audience live, link the segment to
        the campaign with :meth:`AsyncCampaigns.set_segments` instead.
        """
        return await self._post(
            f"/segments/{segment_id}/add-to-campaign",
            cast_to=SegmentAddedToCampaign,
            body={"campaign_id": campaign_id},
            options=options,
        )
