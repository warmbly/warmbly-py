"""The ``salesforce`` resource: the native Salesforce sync.

Maps to ``/v1/integrations/salesforce/{connection_id}/...``. ``connection_id``
is the id of a Salesforce connection (see
:meth:`warmbly.resources.integrations.Integrations.list_connections`); the
OAuth connect flow itself is browser-only. Reads and the activity log are
operational; changing what syncs is a settings change.

Every call needs an API key with the ``INTEGRATIONS`` permission. A deployment
without the Salesforce sync answers ``503``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncSalesforce",
    "ContactSalesforcePanel",
    "Salesforce",
    "SalesforceActivity",
    "SalesforceCampaign",
    "SalesforceCheck",
    "SalesforceFieldInfo",
    "SalesforceImportPreview",
    "SalesforceImportSource",
    "SalesforceImportSourceDeleted",
    "SalesforceListView",
    "SalesforceMetadata",
    "SalesforceOverview",
    "SalesforcePanelConnection",
    "SalesforcePanelRecord",
    "SalesforcePickOption",
    "SalesforceRetried",
    "SalesforceRunResult",
    "SalesforceSettings",
    "SalesforceSettingsDocument",
    "SalesforceSettingsSaved",
    "SalesforceSyncStarted",
    "SalesforceUser",
]


class SalesforcePanelConnection(BaseModel):
    """One connected Salesforce org, as the contact panel lists it."""

    id: str
    label: str | None = None
    environment: str | None = None
    instance_url: str | None = None


class SalesforcePanelRecord(BaseModel):
    """The Lead or Contact a Warmbly contact is linked to in one org.

    ``object`` is ``"Lead"`` or ``"Contact"``; ``id`` is the Salesforce record
    id and ``link_id`` the Warmbly link (what
    :meth:`warmbly.resources.contacts.Contacts.unlink_salesforce` takes).
    ``opportunities`` and ``tasks`` are live reads and may be stale when
    ``stale`` is set; ``error`` says why a live read failed.
    """

    link_id: str | None = None
    connection_id: str | None = None
    connection_label: str | None = None
    object: str | None = None
    id: str | None = None
    url: str | None = None
    name: str | None = None
    title: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    owner: dict[str, Any] | None = None
    account: dict[str, Any] | None = None
    is_converted: bool | None = None
    opted_out: bool | None = None
    lead_source: str | None = None
    opportunities: Sequence[dict[str, Any]] = []
    tasks: Sequence[dict[str, Any]] = []
    linked_by: str | None = None
    last_synced_at: str | None = None
    last_pushed_at: str | None = None
    sync: dict[str, Any] | None = None
    stale: bool | None = None
    error: str | None = None


class ContactSalesforcePanel(BaseModel):
    """A contact's Salesforce panel: the connected orgs and the linked records.

    ``can_sync`` is whether a push is possible right now.
    """

    connections: Sequence[SalesforcePanelConnection] = []
    records: Sequence[SalesforcePanelRecord] = []
    can_sync: bool | None = None


class SalesforceCheck(BaseModel):
    """One permission or setup probe on the overview."""

    key: str | None = None
    label: str | None = None
    ok: bool | None = None
    detail: str | None = None


class SalesforceOverview(BaseModel):
    """A Salesforce connection's health page.

    ``org`` names the connected org (``id``, ``instance_url``, ``environment``,
    ``login_host``, ``user_id``, ``account``), ``api`` is the call budget
    (``used``, ``max``, ``calls_today``, ``budget``) and ``counts`` summarises
    the activity outbox (``pending``, ``synced_24h``, ``failed``,
    ``skipped_24h``, ``linked_records``). ``checks`` is present only when
    requested.
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
    checks: Sequence[SalesforceCheck] = []


class SalesforceSettings(BaseModel):
    """A connection's sync configuration.

    ``matching`` decides which record an email is and what happens when it is
    none; ``activity`` picks which events are logged as Tasks; ``writeback``
    sets lead-status changes; ``inbound`` decides how Salesforce changes pause
    Warmbly campaigns; ``field_map`` is the per-object field rules, each
    ``{object, warmbly, salesforce, direction, policy}``. ``daily_api_budget``
    of ``0`` means a fifth of the org's daily allocation.
    """

    enabled: bool | None = None
    matching: dict[str, Any] | None = None
    activity: dict[str, Any] | None = None
    writeback: dict[str, Any] | None = None
    inbound: dict[str, Any] | None = None
    field_map: Sequence[dict[str, Any]] = []
    daily_api_budget: int | None = None


class SalesforceSettingsDocument(BaseModel):
    """The settings, the Warmbly field vocabulary and the defaults.

    ``warmbly_fields`` is the ``{key, label}`` list a field rule may name on
    the Warmbly side; ``defaults`` is what a new connection starts with.
    """

    settings: SalesforceSettings | None = None
    warmbly_fields: Sequence[dict[str, Any]] = []
    defaults: SalesforceSettings | None = None


class SalesforceSettingsSaved(BaseModel):
    """The settings as saved."""

    settings: SalesforceSettings | None = None


class SalesforcePickOption(BaseModel):
    """A picklist value."""

    value: str | None = None
    label: str | None = None


class SalesforceFieldInfo(BaseModel):
    """One Salesforce field as the mapping editor shows it."""

    name: str | None = None
    label: str | None = None
    type: str | None = None
    createable: bool | None = None
    updateable: bool | None = None
    calculated: bool | None = None
    custom: bool | None = None
    picklist: Sequence[SalesforcePickOption] = []


class SalesforceMetadata(BaseModel):
    """Lead and Contact fields and the picklists the settings screens use."""

    lead_fields: Sequence[SalesforceFieldInfo] = []
    contact_fields: Sequence[SalesforceFieldInfo] = []
    lead_statuses: Sequence[SalesforcePickOption] = []
    lead_sources: Sequence[SalesforcePickOption] = []


class SalesforceUser(BaseModel):
    """An active Salesforce user."""

    id: str | None = None
    name: str | None = None
    email: str | None = None


class SalesforceListView(BaseModel):
    """A Lead or Contact list view an import can read."""

    id: str | None = None
    label: str | None = None
    object: str | None = None


class SalesforceCampaign(BaseModel):
    """A Salesforce Campaign an import can read."""

    id: str | None = None
    name: str | None = None
    status: str | None = None
    type: str | None = None
    member_count: int | None = None


class SalesforceImportPreview(BaseModel):
    """The first rows of an import source and how many it holds.

    Each ``sample`` row has ``record_id``, ``object``, ``name``, ``email``,
    ``company``, ``title``, ``owner_name``, ``status`` and
    ``already_linked``.
    """

    total: int | None = None
    sample: Sequence[dict[str, Any]] = []


class SalesforceRunResult(BaseModel):
    """What one import run did.

    ``no_email`` counts records with no address; ``opted_out`` counts people
    with Email Opt Out set, who are suppressed rather than imported;
    ``truncated`` is set when the source held more than one run reads.
    """

    read: int | None = None
    imported: int | None = None
    updated: int | None = None
    linked: int | None = None
    skipped: int | None = None
    failed: int | None = None
    no_email: int | None = None
    opted_out: int | None = None
    truncated: bool | None = None


class SalesforceImportSource(BaseModel):
    """A saved list view or Salesforce Campaign that feeds contacts in.

    ``source_kind`` is ``list_view`` or ``campaign``; ``object`` is ``Lead``,
    ``Contact`` or ``CampaignMember``.
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
    last_result: SalesforceRunResult | None = None
    last_error: str | None = None
    total_imported: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SalesforceImportSourceDeleted(BaseModel):
    """The result of removing an import source (``204 No Content``).

    Contacts it brought in stay.
    """

    id: str | None = None
    deleted: bool | None = None


class SalesforceActivity(BaseModel):
    """One queued or processed activity: a campaign event to log as a Task.

    ``kind`` is ``sent``, ``opened``, ``clicked``, ``replied``, ``bounced``,
    ``unsubscribed`` or ``meeting_booked``; ``status`` is ``pending``,
    ``synced``, ``skipped`` or ``failed``.
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
    """How many activity rows were re-queued."""

    requeued: int | None = None


class SalesforceSyncStarted(BaseModel):
    """The acknowledgement of a sync-now pass."""

    ok: bool | None = None


def _source_body(
    *,
    name: NotGivenOr[str],
    source_kind: NotGivenOr[str],
    object: NotGivenOr[str],
    source_id: NotGivenOr[str],
    source_label: NotGivenOr[str],
    campaign_id: NotGivenOr[str | None],
    category_ids: NotGivenOr[Sequence[str]],
    recurring: NotGivenOr[bool],
    enabled: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the body shared by creating and editing an import source."""
    return drop_not_given(
        {
            "name": name,
            "source_kind": source_kind,
            "object": object,
            "source_id": source_id,
            "source_label": source_label,
            "campaign_id": campaign_id,
            "category_ids": (
                NOT_GIVEN if isinstance(category_ids, NotGiven) else list(category_ids)
            ),
            "recurring": recurring,
            "enabled": enabled,
        }
    )


class Salesforce(SyncAPIResource):
    """Synchronous ``salesforce`` resource."""

    def _path(self, connection_id: str, tail: str = "") -> str:
        return f"/integrations/salesforce/{connection_id}{tail}"

    def overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Read the connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe permissions and setup, which makes live
                Salesforce calls.
        """
        return self._get(
            self._path(connection_id, "/overview"),
            cast_to=SalesforceOverview,
            query={"checks": "1" if checks else None},
            options=options,
        )

    def settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettingsDocument:
        """Read the sync settings, the Warmbly field list and the defaults."""
        return self._get(
            self._path(connection_id, "/settings"),
            cast_to=SalesforceSettingsDocument,
            options=options,
        )

    def update_settings(
        self,
        connection_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsSaved:
        """Replace the sync settings.

        A whole-document write, not a merge: read :meth:`settings`, change
        what you need and send the result back. A retry converges. An invalid
        document is refused with ``invalid_salesforce_settings``.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document (``enabled``, ``matching``,
                ``activity``, ``writeback``, ``inbound``, ``field_map``,
                ``daily_api_budget``).
        """
        return self._put(
            self._path(connection_id, "/settings"),
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    def metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Read the Lead and Contact fields and picklists."""
        return self._get(
            self._path(connection_id, "/metadata"),
            cast_to=SalesforceMetadata,
            options=options,
        )

    def users(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceUser]:
        """Search active Salesforce users (returned in full, unpaginated)."""
        return self._get_api_list(
            self._path(connection_id, "/users"),
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def list_views(
        self,
        connection_id: str,
        *,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceListView]:
        """List list views (returned in full, unpaginated).

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``.
        """
        return self._get_api_list(
            self._path(connection_id, "/list-views"),
            model=SalesforceListView,
            query={"object": object},
            options=options,
        )

    def campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceCampaign]:
        """Search Salesforce Campaigns (returned in full, unpaginated)."""
        return self._get_api_list(
            self._path(connection_id, "/campaigns"),
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
        """Read the first rows of a list view or Campaign. Writes nothing.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
        """
        return self._post(
            self._path(connection_id, "/import/preview"),
            cast_to=SalesforceImportPreview,
            body=drop_not_given(
                {"source_kind": source_kind, "source_id": source_id, "object": object}
            ),
            options=options,
        )

    def list_import_sources(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceImportSource]:
        """List a connection's saved imports (returned in full)."""
        return self._get_api_list(
            self._path(connection_id, "/import-sources"),
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
        name: NotGivenOr[str] = NOT_GIVEN,
        source_label: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
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
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``, for a list view.
            name: A display name.
            source_label: The list view or Campaign's label.
            campaign_id: A Warmbly campaign the imported contacts join.
            category_ids: Categories to assign.
            recurring: Re-read the source every 30 minutes.
            enabled: Whether a recurring source runs.
        """
        return self._post(
            self._path(connection_id, "/import-sources"),
            cast_to=SalesforceImportSource,
            body=_source_body(
                name=name,
                source_kind=source_kind,
                object=object,
                source_id=source_id,
                source_label=source_label,
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
        source_label: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Edit an import's targets and schedule.

        Args:
            connection_id: The Salesforce connection.
            source_id: The import source.
            campaign_id: A Warmbly campaign id; ``None`` clears the target and
                leaving it out keeps it.
        """
        return self._patch(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=SalesforceImportSource,
            body=_source_body(
                name=name,
                source_kind=NOT_GIVEN,
                object=NOT_GIVEN,
                source_id=NOT_GIVEN,
                source_label=source_label,
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
        """Run an import now. A run already in progress answers ``409``."""
        return self._post(
            self._path(connection_id, f"/import-sources/{source_id}/run"),
            cast_to=SalesforceImportSource,
            options=options,
        )

    def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSourceDeleted:
        """Remove an import. The contacts it brought in stay."""
        return self._delete(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=SalesforceImportSourceDeleted,
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
        """List the activity log, newest first (auto-paginating).

        Args:
            connection_id: The Salesforce connection.
            status: ``pending``, ``synced``, ``skipped`` or ``failed``.
            contact_id: Only this contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            self._path(connection_id, "/activity"),
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
        """Re-queue failed or skipped activity rows (at most 500 ids).

        Re-queuing a row that is already pending changes nothing.
        """
        return self._post(
            self._path(connection_id, "/activity/retry"),
            cast_to=SalesforceRetried,
            body={"ids": list(ids)},
            options=options,
        )

    def sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull Salesforce changes at once."""
        return self._post(
            self._path(connection_id, "/sync-now"),
            cast_to=SalesforceSyncStarted,
            options=options,
        )


class AsyncSalesforce(AsyncAPIResource):
    """Asynchronous ``salesforce`` resource."""

    def _path(self, connection_id: str, tail: str = "") -> str:
        return f"/integrations/salesforce/{connection_id}{tail}"

    async def overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Read the connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe permissions and setup, which makes live
                Salesforce calls.
        """
        return await self._get(
            self._path(connection_id, "/overview"),
            cast_to=SalesforceOverview,
            query={"checks": "1" if checks else None},
            options=options,
        )

    async def settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettingsDocument:
        """Read the sync settings, the Warmbly field list and the defaults."""
        return await self._get(
            self._path(connection_id, "/settings"),
            cast_to=SalesforceSettingsDocument,
            options=options,
        )

    async def update_settings(
        self,
        connection_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsSaved:
        """Replace the sync settings.

        A whole-document write, not a merge: read :meth:`settings`, change
        what you need and send the result back. A retry converges. An invalid
        document is refused with ``invalid_salesforce_settings``.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document (``enabled``, ``matching``,
                ``activity``, ``writeback``, ``inbound``, ``field_map``,
                ``daily_api_budget``).
        """
        return await self._put(
            self._path(connection_id, "/settings"),
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    async def metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Read the Lead and Contact fields and picklists."""
        return await self._get(
            self._path(connection_id, "/metadata"),
            cast_to=SalesforceMetadata,
            options=options,
        )

    def users(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceUser]:
        """Search active Salesforce users (returned in full, unpaginated)."""
        return self._get_api_list(
            self._path(connection_id, "/users"),
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def list_views(
        self,
        connection_id: str,
        *,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceListView]:
        """List list views (returned in full, unpaginated).

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``.
        """
        return self._get_api_list(
            self._path(connection_id, "/list-views"),
            model=SalesforceListView,
            query={"object": object},
            options=options,
        )

    def campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceCampaign]:
        """Search Salesforce Campaigns (returned in full, unpaginated)."""
        return self._get_api_list(
            self._path(connection_id, "/campaigns"),
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
        """Read the first rows of a list view or Campaign. Writes nothing.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
        """
        return await self._post(
            self._path(connection_id, "/import/preview"),
            cast_to=SalesforceImportPreview,
            body=drop_not_given(
                {"source_kind": source_kind, "source_id": source_id, "object": object}
            ),
            options=options,
        )

    def list_import_sources(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceImportSource]:
        """List a connection's saved imports (returned in full)."""
        return self._get_api_list(
            self._path(connection_id, "/import-sources"),
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
        name: NotGivenOr[str] = NOT_GIVEN,
        source_label: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
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
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``, for a list view.
            name: A display name.
            source_label: The list view or Campaign's label.
            campaign_id: A Warmbly campaign the imported contacts join.
            category_ids: Categories to assign.
            recurring: Re-read the source every 30 minutes.
            enabled: Whether a recurring source runs.
        """
        return await self._post(
            self._path(connection_id, "/import-sources"),
            cast_to=SalesforceImportSource,
            body=_source_body(
                name=name,
                source_kind=source_kind,
                object=object,
                source_id=source_id,
                source_label=source_label,
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
        source_label: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Edit an import's targets and schedule.

        Args:
            connection_id: The Salesforce connection.
            source_id: The import source.
            campaign_id: A Warmbly campaign id; ``None`` clears the target and
                leaving it out keeps it.
        """
        return await self._patch(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=SalesforceImportSource,
            body=_source_body(
                name=name,
                source_kind=NOT_GIVEN,
                object=NOT_GIVEN,
                source_id=NOT_GIVEN,
                source_label=source_label,
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
        """Run an import now. A run already in progress answers ``409``."""
        return await self._post(
            self._path(connection_id, f"/import-sources/{source_id}/run"),
            cast_to=SalesforceImportSource,
            options=options,
        )

    async def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSourceDeleted:
        """Remove an import. The contacts it brought in stay."""
        return await self._delete(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=SalesforceImportSourceDeleted,
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
        """List the activity log, newest first (auto-paginating).

        Args:
            connection_id: The Salesforce connection.
            status: ``pending``, ``synced``, ``skipped`` or ``failed``.
            contact_id: Only this contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            self._path(connection_id, "/activity"),
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
        """Re-queue failed or skipped activity rows (at most 500 ids).

        Re-queuing a row that is already pending changes nothing.
        """
        return await self._post(
            self._path(connection_id, "/activity/retry"),
            cast_to=SalesforceRetried,
            body={"ids": list(ids)},
            options=options,
        )

    async def sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull Salesforce changes at once."""
        return await self._post(
            self._path(connection_id, "/sync-now"),
            cast_to=SalesforceSyncStarted,
            options=options,
        )
