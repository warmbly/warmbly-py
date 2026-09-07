"""The ``lead_sync`` resource: on-demand Google Sheets to contacts sync.

Maps to the ``/v1/lead-sync`` route group. A *source* is a saved binding of a
spreadsheet tab to a column mapping; re-running it upserts contacts by email,
so a sync converges rather than duplicating.

The Google account itself is connected through the integrations OAuth flow with
provider ``google_sheets``, which is browser-only; this resource assumes the
connection already exists and surfaces it via :meth:`LeadSync.connection`.
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
    "AsyncLeadSync",
    "LeadSync",
    "LeadSyncConnection",
    "LeadSyncPreview",
    "LeadSyncResult",
    "LeadSyncSource",
    "LeadSyncSourceDeleted",
    "LeadSyncSpreadsheet",
]


class LeadSyncConnection(BaseModel):
    """Whether a Google Sheets account is connected, and which one."""

    connected: bool | None = None
    connection: dict[str, Any] | None = None


class LeadSyncSpreadsheet(BaseModel):
    """A spreadsheet's metadata, including its tabs (permissive)."""

    spreadsheet_id: str | None = None
    title: str | None = None
    tabs: Sequence[dict[str, Any]] = []


class LeadSyncPreview(BaseModel):
    """A parsed preview of a sheet tab, before any contacts are written."""

    headers: Sequence[str] = []
    rows: Sequence[dict[str, Any]] = []
    total_rows: int | None = None
    suggested_mapping: Sequence[dict[str, Any]] = []


class LeadSyncSource(BaseModel):
    """A saved spreadsheet-to-contacts binding."""

    id: str
    organization_id: str | None = None
    created_by_user_id: str | None = None
    provider: str | None = None
    connection_id: str | None = None
    sheet_id: str | None = None
    sheet_title: str | None = None
    tab_title: str | None = None
    a1_range: str | None = None
    has_header: bool | None = None
    column_mapping: Sequence[dict[str, Any]] = []
    dedup: str | None = None
    target_campaign_id: str | None = None
    category_ids: Sequence[str] = []
    subscribed_default: bool | None = None
    label: str | None = None
    status: str | None = None
    last_synced_at: str | None = None
    last_result: dict[str, Any] | None = None
    last_error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LeadSyncSourceDeleted(BaseModel):
    """The result of deleting a source (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class LeadSyncResult(BaseModel):
    """The per-row outcome of running a sync."""

    source_id: str | None = None
    result: dict[str, Any] | None = None


def _source_body(
    *,
    connection_id: NotGivenOr[str],
    sheet_id: NotGivenOr[str],
    sheet_title: NotGivenOr[str],
    tab_title: NotGivenOr[str],
    has_header: NotGivenOr[bool],
    column_mapping: NotGivenOr[Sequence[Mapping[str, Any]]],
    dedup: NotGivenOr[str],
    target_campaign_id: NotGivenOr[str],
    category_ids: NotGivenOr[Sequence[str]],
    subscribed_default: NotGivenOr[bool],
    label: NotGivenOr[str],
    clear_campaign: NotGivenOr[bool] = NOT_GIVEN,
) -> dict[str, Any]:
    return drop_not_given(
        {
            "connection_id": connection_id,
            "sheet_id": sheet_id,
            "sheet_title": sheet_title,
            "tab_title": tab_title,
            "has_header": has_header,
            "column_mapping": column_mapping,
            "dedup": dedup,
            "target_campaign_id": target_campaign_id,
            "category_ids": category_ids,
            "subscribed_default": subscribed_default,
            "label": label,
            "clear_campaign": clear_campaign,
        }
    )


class LeadSync(SyncAPIResource):
    """Synchronous ``lead_sync`` resource."""

    def connection(
        self, *, options: RequestOptions | None = None
    ) -> LeadSyncConnection:
        """Report whether a Google Sheets account is connected."""
        return self._get(
            "/lead-sync/google/connection",
            cast_to=LeadSyncConnection,
            options=options,
        )

    def spreadsheet(
        self,
        *,
        connection_id: str,
        sheet_id: str,
        options: RequestOptions | None = None,
    ) -> LeadSyncSpreadsheet:
        """Read a spreadsheet's title and tabs."""
        return self._post(
            "/lead-sync/google/spreadsheet",
            cast_to=LeadSyncSpreadsheet,
            body={"connection_id": connection_id, "sheet_id": sheet_id},
            options=options,
        )

    def preview(
        self,
        *,
        connection_id: str,
        sheet_id: str,
        tab_title: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSyncPreview:
        """Preview a sheet tab's headers, rows, and a suggested mapping.

        Writes nothing.
        """
        return self._post(
            "/lead-sync/google/preview",
            cast_to=LeadSyncPreview,
            body=drop_not_given(
                {
                    "connection_id": connection_id,
                    "sheet_id": sheet_id,
                    "tab_title": tab_title,
                }
            ),
            options=options,
        )

    def list_sources(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[LeadSyncSource]:
        """List saved sync sources.

        Args:
            campaign_id: Restrict to sources targeting one campaign.
        """
        return self._get_api_list(
            "/lead-sync/sources",
            model=LeadSyncSource,
            query={"campaign_id": campaign_id},
            options=options,
        )

    def create_source(
        self,
        *,
        connection_id: str,
        sheet_id: str,
        column_mapping: Sequence[Mapping[str, Any]],
        sheet_title: NotGivenOr[str] = NOT_GIVEN,
        tab_title: NotGivenOr[str] = NOT_GIVEN,
        has_header: NotGivenOr[bool] = NOT_GIVEN,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        target_campaign_id: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSyncSource:
        """Save a sync source.

        Args:
            connection_id: The Google Sheets connection to read through.
            sheet_id: The spreadsheet id.
            column_mapping: One entry per column, mapping it to a contact
                field.
            tab_title: The tab to read; defaults to the first.
            has_header: Whether row 1 is a header row.
            dedup: How to resolve an existing contact with the same email.
            target_campaign_id: A campaign to enrol synced contacts into.
            category_ids: Categories to apply to synced contacts.
            subscribed_default: The subscription state for new contacts.
            label: A human-readable name for the source.
        """
        return self._post(
            "/lead-sync/sources",
            cast_to=LeadSyncSource,
            body=_source_body(
                connection_id=connection_id,
                sheet_id=sheet_id,
                sheet_title=sheet_title,
                tab_title=tab_title,
                has_header=has_header,
                column_mapping=column_mapping,
                dedup=dedup,
                target_campaign_id=target_campaign_id,
                category_ids=category_ids,
                subscribed_default=subscribed_default,
                label=label,
            ),
            options=options,
        )

    def retrieve_source(
        self, source_id: str, *, options: RequestOptions | None = None
    ) -> LeadSyncSource:
        """Retrieve a single sync source by id."""
        return self._get(
            f"/lead-sync/sources/{source_id}",
            cast_to=LeadSyncSource,
            options=options,
        )

    def update_source(
        self,
        source_id: str,
        *,
        sheet_id: NotGivenOr[str] = NOT_GIVEN,
        sheet_title: NotGivenOr[str] = NOT_GIVEN,
        tab_title: NotGivenOr[str] = NOT_GIVEN,
        has_header: NotGivenOr[bool] = NOT_GIVEN,
        column_mapping: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        target_campaign_id: NotGivenOr[str] = NOT_GIVEN,
        clear_campaign: NotGivenOr[bool] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSyncSource:
        """Update a sync source.

        Args:
            clear_campaign: Detach the target campaign. Use this rather than
                passing a null ``target_campaign_id``.
        """
        return self._patch(
            f"/lead-sync/sources/{source_id}",
            cast_to=LeadSyncSource,
            body=_source_body(
                connection_id=NOT_GIVEN,
                sheet_id=sheet_id,
                sheet_title=sheet_title,
                tab_title=tab_title,
                has_header=has_header,
                column_mapping=column_mapping,
                dedup=dedup,
                target_campaign_id=target_campaign_id,
                category_ids=category_ids,
                subscribed_default=subscribed_default,
                label=label,
                clear_campaign=clear_campaign,
            ),
            options=options,
        )

    def delete_source(
        self, source_id: str, *, options: RequestOptions | None = None
    ) -> LeadSyncSourceDeleted:
        """Delete a sync source. Synced contacts are left alone."""
        return self._delete(
            f"/lead-sync/sources/{source_id}",
            cast_to=LeadSyncSourceDeleted,
            options=options,
        )

    def sync_now(
        self, source_id: str, *, options: RequestOptions | None = None
    ) -> LeadSyncResult:
        """Run a source now and return its per-row result.

        Upserts by email, so re-running converges rather than duplicating.
        """
        return self._post(
            f"/lead-sync/sources/{source_id}/sync",
            cast_to=LeadSyncResult,
            options=options,
        )


class AsyncLeadSync(AsyncAPIResource):
    """Asynchronous ``lead_sync`` resource."""

    async def connection(
        self, *, options: RequestOptions | None = None
    ) -> LeadSyncConnection:
        """Report whether a Google Sheets account is connected."""
        return await self._get(
            "/lead-sync/google/connection",
            cast_to=LeadSyncConnection,
            options=options,
        )

    async def spreadsheet(
        self,
        *,
        connection_id: str,
        sheet_id: str,
        options: RequestOptions | None = None,
    ) -> LeadSyncSpreadsheet:
        """Read a spreadsheet's title and tabs."""
        return await self._post(
            "/lead-sync/google/spreadsheet",
            cast_to=LeadSyncSpreadsheet,
            body={"connection_id": connection_id, "sheet_id": sheet_id},
            options=options,
        )

    async def preview(
        self,
        *,
        connection_id: str,
        sheet_id: str,
        tab_title: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSyncPreview:
        """Preview a sheet tab's headers, rows, and a suggested mapping.

        Writes nothing.
        """
        return await self._post(
            "/lead-sync/google/preview",
            cast_to=LeadSyncPreview,
            body=drop_not_given(
                {
                    "connection_id": connection_id,
                    "sheet_id": sheet_id,
                    "tab_title": tab_title,
                }
            ),
            options=options,
        )

    def list_sources(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[LeadSyncSource]:
        """List saved sync sources.

        Args:
            campaign_id: Restrict to sources targeting one campaign.
        """
        return self._get_api_list(
            "/lead-sync/sources",
            model=LeadSyncSource,
            query={"campaign_id": campaign_id},
            options=options,
        )

    async def create_source(
        self,
        *,
        connection_id: str,
        sheet_id: str,
        column_mapping: Sequence[Mapping[str, Any]],
        sheet_title: NotGivenOr[str] = NOT_GIVEN,
        tab_title: NotGivenOr[str] = NOT_GIVEN,
        has_header: NotGivenOr[bool] = NOT_GIVEN,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        target_campaign_id: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSyncSource:
        """Save a sync source.

        Args:
            connection_id: The Google Sheets connection to read through.
            sheet_id: The spreadsheet id.
            column_mapping: One entry per column, mapping it to a contact
                field.
            tab_title: The tab to read; defaults to the first.
            has_header: Whether row 1 is a header row.
            dedup: How to resolve an existing contact with the same email.
            target_campaign_id: A campaign to enrol synced contacts into.
            category_ids: Categories to apply to synced contacts.
            subscribed_default: The subscription state for new contacts.
            label: A human-readable name for the source.
        """
        return await self._post(
            "/lead-sync/sources",
            cast_to=LeadSyncSource,
            body=_source_body(
                connection_id=connection_id,
                sheet_id=sheet_id,
                sheet_title=sheet_title,
                tab_title=tab_title,
                has_header=has_header,
                column_mapping=column_mapping,
                dedup=dedup,
                target_campaign_id=target_campaign_id,
                category_ids=category_ids,
                subscribed_default=subscribed_default,
                label=label,
            ),
            options=options,
        )

    async def retrieve_source(
        self, source_id: str, *, options: RequestOptions | None = None
    ) -> LeadSyncSource:
        """Retrieve a single sync source by id."""
        return await self._get(
            f"/lead-sync/sources/{source_id}",
            cast_to=LeadSyncSource,
            options=options,
        )

    async def update_source(
        self,
        source_id: str,
        *,
        sheet_id: NotGivenOr[str] = NOT_GIVEN,
        sheet_title: NotGivenOr[str] = NOT_GIVEN,
        tab_title: NotGivenOr[str] = NOT_GIVEN,
        has_header: NotGivenOr[bool] = NOT_GIVEN,
        column_mapping: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        target_campaign_id: NotGivenOr[str] = NOT_GIVEN,
        clear_campaign: NotGivenOr[bool] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSyncSource:
        """Update a sync source.

        Args:
            clear_campaign: Detach the target campaign. Use this rather than
                passing a null ``target_campaign_id``.
        """
        return await self._patch(
            f"/lead-sync/sources/{source_id}",
            cast_to=LeadSyncSource,
            body=_source_body(
                connection_id=NOT_GIVEN,
                sheet_id=sheet_id,
                sheet_title=sheet_title,
                tab_title=tab_title,
                has_header=has_header,
                column_mapping=column_mapping,
                dedup=dedup,
                target_campaign_id=target_campaign_id,
                category_ids=category_ids,
                subscribed_default=subscribed_default,
                label=label,
                clear_campaign=clear_campaign,
            ),
            options=options,
        )

    async def delete_source(
        self, source_id: str, *, options: RequestOptions | None = None
    ) -> LeadSyncSourceDeleted:
        """Delete a sync source. Synced contacts are left alone."""
        return await self._delete(
            f"/lead-sync/sources/{source_id}",
            cast_to=LeadSyncSourceDeleted,
            options=options,
        )

    async def sync_now(
        self, source_id: str, *, options: RequestOptions | None = None
    ) -> LeadSyncResult:
        """Run a source now and return its per-row result.

        Upserts by email, so re-running converges rather than duplicating.
        """
        return await self._post(
            f"/lead-sync/sources/{source_id}/sync",
            cast_to=LeadSyncResult,
            options=options,
        )
