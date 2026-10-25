"""The ``integrations.salesforce`` resource: the native Salesforce sync.

Maps to ``/v1/integrations/salesforce/:id``, where ``:id`` is the id of a
Salesforce *connection* (see :meth:`warmbly.resources.integrations.Integrations.list_connections`).
Connecting the Salesforce org itself is a browser-only OAuth flow, so these
methods assume the connection already exists.

Every route needs the ``integrations`` API permission. Reading health and the
activity log is operational; changing what syncs is a settings action.
A contact's own Salesforce panel lives on :class:`~warmbly.resources.contacts.Contacts`
(``get_salesforce``, ``sync_salesforce``, ``unlink_salesforce``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given
from .integrations import IntegrationAck

__all__ = [
    "AsyncSalesforce",
    "Salesforce",
    "SalesforceActivity",
    "SalesforceCampaign",
    "SalesforceImportPreview",
    "SalesforceImportSource",
    "SalesforceListView",
    "SalesforceMetadata",
    "SalesforceOverview",
    "SalesforceRetried",
    "SalesforceSettings",
    "SalesforceSettingsSaved",
    "SalesforceSyncStarted",
    "SalesforceUser",
]


class SalesforceOverview(BaseModel):
    """A Salesforce connection's health page.

    ``org`` names the connected org (``instance_url``, ``environment``,
    ``login_host``, ``user_id``, ``account``), ``api`` is the API budget
    picture (``used``, ``max``, ``calls_today``, ``budget``) and ``counts``
    summarises the activity outbox (``pending``, ``synced_24h``, ``failed``,
    ``skipped_24h``, ``linked_records``). ``checks`` is filled only when the
    overview was requested with ``checks=True``.
    """

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    health_detail: str | None = None
    org: dict[str, Any] | None = None
    api: dict[str, Any] | None = None
    counts: dict[str, Any] | None = None
    last_pull_at: str | None = None
    last_pull_error: str | None = None
    settings_enabled: bool | None = None
    checks: Sequence[dict[str, Any]] = []


class SalesforceSettings(BaseModel):
    """The sync settings, the Warmbly field vocabulary, and the defaults.

    ``settings`` has ``enabled``, ``matching``, ``activity``, ``writeback``,
    ``inbound``, ``field_map`` and ``daily_api_budget``. ``warmbly_fields``
    lists the ``{"key", "label"}`` fields a field rule may name on the Warmbly
    side, and ``defaults`` is the document a new connection starts with.
    """

    settings: dict[str, Any] | None = None
    warmbly_fields: Sequence[dict[str, Any]] = []
    defaults: dict[str, Any] | None = None


class SalesforceSettingsSaved(BaseModel):
    """The sync settings as stored after a save."""

    settings: dict[str, Any] | None = None


class SalesforceMetadata(BaseModel):
    """Lead and Contact fields and picklists the settings screens pick from.

    Fields are ``{"name", "label", "type", "createable", "updateable",
    "calculated", "custom", "picklist"}``; picklist options are
    ``{"value", "label"}``.
    """

    lead_fields: Sequence[dict[str, Any]] = []
    contact_fields: Sequence[dict[str, Any]] = []
    lead_statuses: Sequence[dict[str, Any]] = []
    lead_sources: Sequence[dict[str, Any]] = []


class SalesforceUser(BaseModel):
    """An active Salesforce user."""

    id: str
    name: str | None = None
    email: str | None = None


class SalesforceListView(BaseModel):
    """A Lead or Contact list view."""

    id: str
    label: str | None = None
    object: str | None = None


class SalesforceCampaign(BaseModel):
    """A Salesforce Campaign."""

    id: str
    name: str | None = None
    status: str | None = None
    type: str | None = None
    member_count: int | None = None


class SalesforceImportPreview(BaseModel):
    """The first rows of a list view or Campaign, and how many it holds.

    ``sample`` rows have ``record_id``, ``object``, ``name``, ``email``,
    ``company``, ``title``, ``owner_name``, ``status`` and ``already_linked``.
    """

    total: int | None = None
    sample: Sequence[dict[str, Any]] = []


class SalesforceImportSource(BaseModel):
    """A saved list view or Campaign that feeds contacts into Warmbly.

    ``source_kind`` is ``"list_view"`` or ``"campaign"``. ``last_result``
    reports one run (``read``, ``imported``, ``updated``, ``linked``,
    ``skipped``, ``failed``, ``no_email``, ``opted_out``, ``truncated``).
    """

    id: str
    organization_id: str | None = None
    connection_id: str | None = None
    created_by_user_id: str | None = None
    name: str | None = None
    source_kind: str | None = None
    object: str | None = None
    source_id: str | None = None
    source_label: str | None = None
    campaign_id: str | None = None
    category_ids: Sequence[str] = []
    recurring: bool | None = None
    enabled: bool | None = None
    status: str | None = None
    last_run_at: str | None = None
    last_result: dict[str, Any] | None = None
    last_error: str | None = None
    total_imported: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SalesforceActivity(BaseModel):
    """One queued or processed activity: a campaign event logged as a Task.

    ``status`` is ``pending``, ``synced``, ``skipped``, or ``failed``.
    """

    id: str
    organization_id: str | None = None
    connection_id: str | None = None
    contact_id: str | None = None
    contact_email: str | None = None
    kind: str | None = None
    payload: dict[str, Any] | None = None
    status: str | None = None
    attempts: int | None = None
    next_attempt_at: str | None = None
    record_id: str | None = None
    task_id: str | None = None
    detail: str | None = None
    occurred_at: str | None = None
    created_at: str | None = None
    processed_at: str | None = None


class SalesforceRetried(BaseModel):
    """How many activity rows a retry re-queued."""

    requeued: int | None = None


class SalesforceSyncStarted(BaseModel):
    """The acknowledgement of a sync-now request."""

    ok: bool | None = None


def _source_body(**fields: Any) -> dict[str, Any]:
    return drop_not_given(
        {k: (list(v) if isinstance(v, (list, tuple)) else v) for k, v in fields.items()}
    )


class Salesforce(SyncAPIResource):
    """Synchronous ``integrations.salesforce`` resource."""

    def overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve a connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe the connected user's permissions.
        """
        return self._get(
            f"/integrations/salesforce/{connection_id}/overview",
            cast_to=SalesforceOverview,
            query={"checks": "1" if checks else NOT_GIVEN},
            options=options,
        )

    def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettings:
        """Retrieve the sync settings, the Warmbly field list, and the defaults."""
        return self._get(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettings,
            options=options,
        )

    def update_settings(
        self,
        connection_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsSaved:
        """Validate and save the sync settings.

        This is a PUT of the whole document, so a retry converges.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document (see :meth:`get_settings`).
        """
        return self._put(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    def metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Retrieve Lead and Contact fields and picklists."""
        return self._get(
            f"/integrations/salesforce/{connection_id}/metadata",
            cast_to=SalesforceMetadata,
            options=options,
        )

    def list_users(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceUser]:
        """Search active Salesforce users.

        Args:
            connection_id: The Salesforce connection.
            q: Text to match against name or email.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/users",
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def list_views(
        self,
        connection_id: str,
        *,
        object: str,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceListView]:
        """List the list views of an object.

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/list-views",
            model=SalesforceListView,
            query={"object": object},
            options=options,
        )

    def list_campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceCampaign]:
        """Search Salesforce Campaigns.

        Args:
            connection_id: The Salesforce connection.
            q: Text to match against the campaign name.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/campaigns",
            model=SalesforceCampaign,
            query={"q": q},
            options=options,
        )

    def preview_import(
        self,
        connection_id: str,
        *,
        source_kind: str,
        source_id: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportPreview:
        """Read the first rows of a list view or Campaign without importing.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view's or Campaign's Salesforce id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import/preview",
            cast_to=SalesforceImportPreview,
            body=drop_not_given(
                {"source_kind": source_kind, "source_id": source_id, "object": object}
            ),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[SalesforceImportSource]:
        """List a connection's saved imports."""
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/import-sources",
            model=SalesforceImportSource,
            options=options,
        )

    def create_import_source(
        self,
        connection_id: str,
        *,
        source_kind: str,
        source_id: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        source_label: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save an import and start its first run.

        People are deduplicated by address, so a retried create makes a second
        source whose run imports nothing new.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view's or Campaign's Salesforce id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
            source_label: A display label for the source.
            name: A name for the saved import.
            campaign_id: A Warmbly campaign to enrol imported contacts into.
            category_ids: Categories to apply to imported contacts.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import-sources",
            cast_to=SalesforceImportSource,
            body=_source_body(
                source_kind=source_kind,
                source_id=source_id,
                object=object,
                source_label=source_label,
                name=name,
                campaign_id=campaign_id,
                category_ids=category_ids,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    def update_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Edit an import's targets and schedule.

        Args:
            connection_id: The Salesforce connection.
            source_id: The saved import's id.
            name: A new name.
            campaign_id: A Warmbly campaign to enrol into; pass ``None`` to
                clear the target, omit it to leave it.
            category_ids: Categories to apply to imported contacts.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return self._patch(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=_source_body(
                name=name,
                campaign_id=campaign_id,
                category_ids=category_ids,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    def run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Run a saved import now.

        A second request while one runs is refused with a conflict, so retries
        cannot double-run it.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}/run",
            cast_to=SalesforceImportSource,
            options=options,
        )

    def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> IntegrationAck:
        """Remove a saved import. Contacts it brought in stay."""
        return self._delete(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=IntegrationAck,
            options=options,
        )

    def list_activity(
        self,
        connection_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceActivity]:
        """Page the activity log, newest first (auto-paginating).

        Args:
            connection_id: The Salesforce connection.
            status: ``"pending"``, ``"synced"``, ``"skipped"``, or ``"failed"``.
            contact_id: Only one contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/activity",
            model=SalesforceActivity,
            query={
                "status": status,
                "contact_id": contact_id,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def retry_activity(
        self,
        connection_id: str,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SalesforceRetried:
        """Re-queue failed or skipped activity rows.

        Re-queuing a row that is already pending changes nothing, so retries
        are safe.

        Args:
            connection_id: The Salesforce connection.
            ids: The activity ids to re-queue, at most 500.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/activity/retry",
            cast_to=SalesforceRetried,
            body={"ids": list(ids)},
            options=options,
        )

    def sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull changes at once."""
        return self._post(
            f"/integrations/salesforce/{connection_id}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )


class AsyncSalesforce(AsyncAPIResource):
    """Asynchronous ``integrations.salesforce`` resource."""

    async def overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve a connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe the connected user's permissions.
        """
        return await self._get(
            f"/integrations/salesforce/{connection_id}/overview",
            cast_to=SalesforceOverview,
            query={"checks": "1" if checks else NOT_GIVEN},
            options=options,
        )

    async def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettings:
        """Retrieve the sync settings, the Warmbly field list, and the defaults."""
        return await self._get(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettings,
            options=options,
        )

    async def update_settings(
        self,
        connection_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsSaved:
        """Validate and save the sync settings.

        This is a PUT of the whole document, so a retry converges.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document (see :meth:`get_settings`).
        """
        return await self._put(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    async def metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Retrieve Lead and Contact fields and picklists."""
        return await self._get(
            f"/integrations/salesforce/{connection_id}/metadata",
            cast_to=SalesforceMetadata,
            options=options,
        )

    def list_users(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceUser]:
        """Search active Salesforce users.

        Args:
            connection_id: The Salesforce connection.
            q: Text to match against name or email.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/users",
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def list_views(
        self,
        connection_id: str,
        *,
        object: str,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceListView]:
        """List the list views of an object.

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/list-views",
            model=SalesforceListView,
            query={"object": object},
            options=options,
        )

    def list_campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceCampaign]:
        """Search Salesforce Campaigns.

        Args:
            connection_id: The Salesforce connection.
            q: Text to match against the campaign name.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/campaigns",
            model=SalesforceCampaign,
            query={"q": q},
            options=options,
        )

    async def preview_import(
        self,
        connection_id: str,
        *,
        source_kind: str,
        source_id: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportPreview:
        """Read the first rows of a list view or Campaign without importing.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view's or Campaign's Salesforce id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import/preview",
            cast_to=SalesforceImportPreview,
            body=drop_not_given(
                {"source_kind": source_kind, "source_id": source_id, "object": object}
            ),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[SalesforceImportSource]:
        """List a connection's saved imports."""
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/import-sources",
            model=SalesforceImportSource,
            options=options,
        )

    async def create_import_source(
        self,
        connection_id: str,
        *,
        source_kind: str,
        source_id: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        source_label: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save an import and start its first run.

        People are deduplicated by address, so a retried create makes a second
        source whose run imports nothing new.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view's or Campaign's Salesforce id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
            source_label: A display label for the source.
            name: A name for the saved import.
            campaign_id: A Warmbly campaign to enrol imported contacts into.
            category_ids: Categories to apply to imported contacts.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import-sources",
            cast_to=SalesforceImportSource,
            body=_source_body(
                source_kind=source_kind,
                source_id=source_id,
                object=object,
                source_label=source_label,
                name=name,
                campaign_id=campaign_id,
                category_ids=category_ids,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    async def update_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Edit an import's targets and schedule.

        Args:
            connection_id: The Salesforce connection.
            source_id: The saved import's id.
            name: A new name.
            campaign_id: A Warmbly campaign to enrol into; pass ``None`` to
                clear the target, omit it to leave it.
            category_ids: Categories to apply to imported contacts.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return await self._patch(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=_source_body(
                name=name,
                campaign_id=campaign_id,
                category_ids=category_ids,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    async def run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Run a saved import now.

        A second request while one runs is refused with a conflict, so retries
        cannot double-run it.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}/run",
            cast_to=SalesforceImportSource,
            options=options,
        )

    async def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> IntegrationAck:
        """Remove a saved import. Contacts it brought in stay."""
        return await self._delete(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=IntegrationAck,
            options=options,
        )

    def list_activity(
        self,
        connection_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceActivity]:
        """Page the activity log, newest first (auto-paginating).

        Args:
            connection_id: The Salesforce connection.
            status: ``"pending"``, ``"synced"``, ``"skipped"``, or ``"failed"``.
            contact_id: Only one contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/activity",
            model=SalesforceActivity,
            query={
                "status": status,
                "contact_id": contact_id,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def retry_activity(
        self,
        connection_id: str,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SalesforceRetried:
        """Re-queue failed or skipped activity rows.

        Re-queuing a row that is already pending changes nothing, so retries
        are safe.

        Args:
            connection_id: The Salesforce connection.
            ids: The activity ids to re-queue, at most 500.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/activity/retry",
            cast_to=SalesforceRetried,
            body={"ids": list(ids)},
            options=options,
        )

    async def sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull changes at once."""
        return await self._post(
            f"/integrations/salesforce/{connection_id}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )
