"""The ``suppressions`` resource: the workspace suppression list.

Maps to the ``/v1/suppressions`` route group. An entry is an address, or a
whole domain, that campaign mail must never go to, whatever put it there: a
hard bounce, a spam complaint, a recipient's own opt-out, or a manual add.

Removing an entry is what re-enables sending to that recipient, so it is
audited: prefer it to deleting and re-creating the contact.
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
    "AsyncSuppressions",
    "SuppressedRecipient",
    "SuppressionRemoved",
    "Suppressions",
    "SuppressionsAdded",
]


class SuppressedRecipient(BaseModel):
    """One entry on the suppression list.

    A domain entry keeps the bare host in ``email`` (``kind`` is ``"domain"``)
    and matches every address at it. ``source`` is one of ``bounce``,
    ``complaint``, ``unsubscribe``, ``manual`` or ``import``.
    """

    id: str
    organization_id: str | None = None
    email: str | None = None
    kind: str | None = None
    reason: str | None = None
    source: str | None = None
    campaign_id: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SuppressionsAdded(BaseModel):
    """The result of adding entries.

    ``skipped`` lists the values that were neither a valid address nor a valid
    domain; everything else was added or already present.
    """

    added: int | None = None
    skipped: Sequence[str] = []


class SuppressionRemoved(BaseModel):
    """The result of lifting a suppression (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


def _entries(
    entries: Sequence[str | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize bare strings into ``{"value": ...}`` entry objects."""
    return [
        {"value": entry} if isinstance(entry, str) else dict(entry) for entry in entries
    ]


class Suppressions(SyncAPIResource):
    """Synchronous ``suppressions`` resource."""

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SuppressedRecipient]:
        """List the suppression list, newest first.

        Args:
            q: Filter to entries whose value contains this text.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/suppressions",
            model=SuppressedRecipient,
            query=drop_not_given({"q": q, "limit": limit, "cursor": cursor}),
            options=options,
        )

    def add(
        self,
        *,
        entries: Sequence[str | Mapping[str, Any]],
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SuppressionsAdded:
        """Add addresses or domains to the list.

        Args:
            entries: Up to 5000 entries. Each is either a bare string — an
                address, or a domain with or without a leading ``@`` — or a
                mapping of ``{"value": ..., "reason": ...}``.
            reason: Applied to every entry that carries no reason of its own.
        """
        return self._post(
            "/suppressions",
            cast_to=SuppressionsAdded,
            body=drop_not_given({"entries": _entries(entries), "reason": reason}),
            options=options,
        )

    def remove(
        self, suppression_id: str, *, options: RequestOptions | None = None
    ) -> SuppressionRemoved:
        """Lift a suppression, re-enabling campaign mail to that recipient."""
        return self._delete(
            f"/suppressions/{suppression_id}",
            cast_to=SuppressionRemoved,
            options=options,
        )


class AsyncSuppressions(AsyncAPIResource):
    """Asynchronous ``suppressions`` resource."""

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SuppressedRecipient]:
        """List the suppression list, newest first.

        Args:
            q: Filter to entries whose value contains this text.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/suppressions",
            model=SuppressedRecipient,
            query=drop_not_given({"q": q, "limit": limit, "cursor": cursor}),
            options=options,
        )

    async def add(
        self,
        *,
        entries: Sequence[str | Mapping[str, Any]],
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SuppressionsAdded:
        """Add addresses or domains to the list.

        Args:
            entries: Up to 5000 entries. Each is either a bare string — an
                address, or a domain with or without a leading ``@`` — or a
                mapping of ``{"value": ..., "reason": ...}``.
            reason: Applied to every entry that carries no reason of its own.
        """
        return await self._post(
            "/suppressions",
            cast_to=SuppressionsAdded,
            body=drop_not_given({"entries": _entries(entries), "reason": reason}),
            options=options,
        )

    async def remove(
        self, suppression_id: str, *, options: RequestOptions | None = None
    ) -> SuppressionRemoved:
        """Lift a suppression, re-enabling campaign mail to that recipient."""
        return await self._delete(
            f"/suppressions/{suppression_id}",
            cast_to=SuppressionRemoved,
            options=options,
        )
