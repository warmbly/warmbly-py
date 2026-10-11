"""The ``salesforce`` resource: the native Salesforce sync.

Maps to ``/v1/integrations/salesforce/{connection_id}/*``, where the id is a
Salesforce connection from ``client.integrations``. Covers the connection's
health overview, its sync settings, the Salesforce-side lookups the settings
and imports are built from (metadata, users, list views, campaigns), saved
imports and their runs, and the activity log. The per-contact side of the sync
lives on ``client.contacts`` (``salesforce``, ``sync_salesforce`` and
``unlink_salesforce``).

Reading needs the ``integrations`` scope or the manage-settings or
use-integrations permission, changing settings, import definitions and the
activity queue needs ``integrations`` or manage-settings, and the actions that
run work (previews, import runs, sync now) need ``integrations`` or
use-integrations. An instance without the Salesforce sync answers ``503``.
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
    "AsyncSalesforce",
    "Salesforce",
    "SalesforceAccount",
    "SalesforceActivity",
    "SalesforceActivityCounts",
    "SalesforceActivitySettings",
    "SalesforceCampaign",
    "SalesforceCheck",
    "SalesforceContactPanel",
    "SalesforceFieldInfo",
    "SalesforceFieldRule",
    "SalesforceImportPreview",
    "SalesforceImportSource",
    "SalesforceImportSourceDeleted",
    "SalesforceInboundSettings",
    "SalesforceListView",
    "SalesforceMatchingSettings",
    "SalesforceMetadata",
    "SalesforceOpportunity",
    "SalesforceOverview",
    "SalesforceOverviewApi",
    "SalesforceOverviewOrg",
    "SalesforcePanelConnection",
    "SalesforcePanelRecord",
    "SalesforcePanelSync",
    "SalesforcePanelTask",
    "SalesforcePicklistOption",
    "SalesforcePreviewRow",
    "SalesforceRef",
    "SalesforceRequeued",
    "SalesforceRunResult",
    "SalesforceSettings",
    "SalesforceSettingsDocument",
    "SalesforceSettingsSaved",
    "SalesforceSyncStarted",
    "SalesforceUser",
    "SalesforceWarmblyField",
    "SalesforceWritebackSettings",
]


# -- overview ---------------------------------------------------------------
class SalesforceCheck(BaseModel):
    """One live health check run by ``overview(checks=True)``."""

    key: str | None = None
    label: str | None = None
    ok: bool | None = None
    detail: str | None = None


class SalesforceOverviewOrg(BaseModel):
    """The connected Salesforce org."""

    id: str | None = None
    instance_url: str | None = None
    environment: str | None = None
    login_host: str | None = None
    user_id: str | None = None
    account: str | None = None


class SalesforceOverviewApi(BaseModel):
    """Salesforce API usage against the daily budget."""

    used: int | None = None
    max: int | None = None
    calls_today: int | None = None
    budget: int | None = None


class SalesforceActivityCounts(BaseModel):
    """A summary of the activity outbox."""

    pending: int | None = None
    synced_24h: int | None = None
    failed: int | None = None
    skipped_24h: int | None = None
    linked_records: int | None = None


class SalesforceOverview(BaseModel):
    """A Salesforce connection's health page.

    ``checks`` is only present when the request asked for live checks.
    """

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    health_detail: str | None = None
    org: SalesforceOverviewOrg | None = None
    api: SalesforceOverviewApi | None = None
    counts: SalesforceActivityCounts | None = None
    last_pull_at: str | None = None
    last_pull_error: str | None = None
    settings_enabled: bool | None = None
    checks: Sequence[SalesforceCheck] = []


# -- settings ---------------------------------------------------------------
class SalesforceMatchingSettings(BaseModel):
    """Which record an email is, and what happens when it is none.

    ``prefer`` is ``"contact"`` or ``"lead"``; ``owner_id`` is only present
    when a fixed owner is configured.
    """

    prefer: str | None = None
    create_when: str | None = None
    create_as: str | None = None
    lead_source: str | None = None
    lead_status: str | None = None
    owner: str | None = None
    owner_id: str | None = None
    run_assignment_rules: bool | None = None


class SalesforceActivitySettings(BaseModel):
    """Which campaign events become Salesforce Tasks.

    ``assign_to`` is ``"record_owner"``, ``"sender"`` or ``"connected_user"``.
    """

    sent: bool | None = None
    replied: bool | None = None
    opened: bool | None = None
    clicked: bool | None = None
    bounced: bool | None = None
    unsubscribed: bool | None = None
    meeting_booked: bool | None = None
    include_body: bool | None = None
    assign_to: str | None = None
    relate_to_opportunity: bool | None = None


class SalesforceWritebackSettings(BaseModel):
    """Which Lead and Contact fields Warmbly changes.

    ``lead_status_on_reply`` maps a reply intent (``positive``, ``negative``,
    ``neutral``, ``question``, ``out_of_office`` or ``any``) to a Lead status.
    """

    lead_status_on_sent: str | None = None
    lead_status_on_reply: dict[str, str] | None = None
    lead_status_on_meeting: str | None = None
    never_move_backwards: bool | None = None


class SalesforceInboundSettings(BaseModel):
    """What a change in Salesforce does in Warmbly.

    ``opt_out`` is ``"both"``, ``"to_salesforce"``, ``"from_salesforce"`` or
    ``"off"``.
    """

    opt_out: str | None = None
    pause_on_converted: bool | None = None
    pause_on_statuses: Sequence[str] = []
    pause_on_open_opportunity: bool | None = None


class SalesforceFieldRule(BaseModel):
    """One per-object field sync rule.

    ``direction`` is ``push``, ``pull`` or ``both``.
    """

    object: str | None = None
    warmbly: str | None = None
    salesforce: str | None = None
    direction: str | None = None
    policy: str | None = None


class SalesforceSettings(BaseModel):
    """One connection's sync configuration.

    ``enabled`` is the master switch for activity logging, writeback and the
    pull loop; imports and the contact panel work regardless. A
    ``daily_api_budget`` of ``0`` means a fifth of the org's daily allocation.
    """

    enabled: bool | None = None
    matching: SalesforceMatchingSettings | None = None
    activity: SalesforceActivitySettings | None = None
    writeback: SalesforceWritebackSettings | None = None
    inbound: SalesforceInboundSettings | None = None
    field_map: Sequence[SalesforceFieldRule] = []
    daily_api_budget: int | None = None


class SalesforceWarmblyField(BaseModel):
    """A Warmbly-side field a field rule may name.

    ``custom:<key>`` reads and writes a contact custom field; ``engagement.*``
    fields are push-only.
    """

    key: str | None = None
    label: str | None = None


class SalesforceSettingsDocument(BaseModel):
    """The settings together with the field vocabulary and the defaults."""

    settings: SalesforceSettings | None = None
    warmbly_fields: Sequence[SalesforceWarmblyField] = []
    defaults: SalesforceSettings | None = None


class SalesforceSettingsSaved(BaseModel):
    """The settings as saved, after validation."""

    settings: SalesforceSettings | None = None


# -- Salesforce-side lookups ------------------------------------------------
class SalesforcePicklistOption(BaseModel):
    """One value of a Salesforce picklist."""

    value: str | None = None
    label: str | None = None


class SalesforceFieldInfo(BaseModel):
    """A Lead or Contact field and, for a picklist, its values."""

    name: str | None = None
    label: str | None = None
    type: str | None = None
    createable: bool | None = None
    updateable: bool | None = None
    calculated: bool | None = None
    custom: bool | None = None
    picklist: Sequence[SalesforcePicklistOption] = []


class SalesforceMetadata(BaseModel):
    """Lead and Contact fields and the picklists the settings choose from."""

    lead_fields: Sequence[SalesforceFieldInfo] = []
    contact_fields: Sequence[SalesforceFieldInfo] = []
    lead_statuses: Sequence[SalesforcePicklistOption] = []
    lead_sources: Sequence[SalesforcePicklistOption] = []


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


# -- imports ----------------------------------------------------------------
class SalesforcePreviewRow(BaseModel):
    """One record in an import preview."""

    record_id: str
    object: str | None = None
    name: str | None = None
    email: str | None = None
    company: str | None = None
    title: str | None = None
    owner_name: str | None = None
    status: str | None = None
    already_linked: bool | None = None


class SalesforceImportPreview(BaseModel):
    """The first rows of an import source and how many it holds."""

    total: int | None = None
    sample: Sequence[SalesforcePreviewRow] = []


class SalesforceRunResult(BaseModel):
    """What one import run did.

    ``truncated`` is only present when the source held more than one run reads.
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

    ``source_kind`` is ``"list_view"`` or ``"campaign"``.
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
    """The result of removing an import (``204 No Content``).

    The contacts it brought in stay.
    """

    id: str | None = None
    deleted: bool | None = None


# -- activity ---------------------------------------------------------------
class SalesforceActivity(BaseModel):
    """One queued or processed activity: a campaign event to log as a Task.

    ``status`` is ``pending``, ``synced``, ``skipped`` or ``failed``.
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


class SalesforceRequeued(BaseModel):
    """How many activity rows a retry put back on the queue."""

    requeued: int | None = None


class SalesforceSyncStarted(BaseModel):
    """The acknowledgement of a sync-now pass."""

    ok: bool | None = None


# -- contact panel ----------------------------------------------------------
class SalesforcePanelConnection(BaseModel):
    """A connected Salesforce org, as the contact panel lists it."""

    id: str
    label: str | None = None
    environment: str | None = None
    instance_url: str | None = None


class SalesforceRef(BaseModel):
    """A Salesforce user reference."""

    id: str | None = None
    name: str | None = None


class SalesforceAccount(BaseModel):
    """A Salesforce account reference."""

    id: str | None = None
    name: str | None = None
    url: str | None = None


class SalesforceOpportunity(BaseModel):
    """An opportunity on the linked record's account."""

    id: str | None = None
    name: str | None = None
    stage: str | None = None
    amount: float | None = None
    close_date: str | None = None
    is_closed: bool | None = None
    is_won: bool | None = None
    url: str | None = None


class SalesforcePanelTask(BaseModel):
    """A Task on the linked record."""

    id: str | None = None
    subject: str | None = None
    date: str | None = None
    status: str | None = None
    owner_name: str | None = None
    url: str | None = None
    from_warmbly: bool | None = None


class SalesforcePanelSync(BaseModel):
    """Activity sync counters for one linked record."""

    pending: int | None = None
    failed: int | None = None
    synced: int | None = None
    last_error: str | None = None


class SalesforcePanelRecord(BaseModel):
    """The linked Lead or Contact in one Salesforce org.

    ``link_id`` is what ``client.contacts.unlink_salesforce`` takes. ``stale``
    means the live data could not be refreshed and ``error`` says why.
    """

    link_id: str
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
    owner: SalesforceRef | None = None
    account: SalesforceAccount | None = None
    is_converted: bool | None = None
    opted_out: bool | None = None
    lead_source: str | None = None
    opportunities: Sequence[SalesforceOpportunity] = []
    tasks: Sequence[SalesforcePanelTask] = []
    linked_by: str | None = None
    last_synced_at: str | None = None
    last_pushed_at: str | None = None
    sync: SalesforcePanelSync | None = None
    stale: bool | None = None
    error: str | None = None


class SalesforceContactPanel(BaseModel):
    """A contact's Salesforce panel: the orgs it can sync to and its records."""

    connections: Sequence[SalesforcePanelConnection] = []
    records: Sequence[SalesforcePanelRecord] = []
    can_sync: bool | None = None


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
) -> dict[str, object]:
    return drop_not_given(
        {
            "name": name,
            "source_kind": source_kind,
            "object": object,
            "source_id": source_id,
            "source_label": source_label,
            "campaign_id": campaign_id,
            "category_ids": category_ids,
            "recurring": recurring,
            "enabled": enabled,
        }
    )


def _base(connection_id: str) -> str:
    return f"/integrations/salesforce/{connection_id}"


class Salesforce(SyncAPIResource):
    """Synchronous ``salesforce`` resource."""

    def overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve the connection's health page.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            checks: Also run the live health checks (a few Salesforce calls),
                filling ``checks``."""
        return self._get(
            f"{_base(connection_id)}/overview",
            cast_to=SalesforceOverview,
            query=drop_not_given({"checks": "1" if checks else NOT_GIVEN}),
            options=options,
        )

    def get_settings(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsDocument:
        """Retrieve the sync settings, the Warmbly field vocabulary and the defaults.

        Needs read access to integrations."""
        return self._get(
            f"{_base(connection_id)}/settings",
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
        """Replace the sync settings. This is a PUT of the whole document.

        Needs the ``integrations`` scope or the manage-settings permission.
        Send the complete document (start from ``get_settings().settings``),
        because a key left out reverts to its zero value rather than keeping
        its saved value. The server validates it and answers ``400`` on a bad
        one.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document: ``enabled``, ``matching``,
                ``activity``, ``writeback``, ``inbound``, ``field_map`` and
                ``daily_api_budget``."""
        return self._put(
            f"{_base(connection_id)}/settings",
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    def metadata(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceMetadata:
        """Retrieve the Lead and Contact fields and the picklists in the org.

        Needs read access to integrations."""
        return self._get(
            f"{_base(connection_id)}/metadata",
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
        """Search active Salesforce users. Returned in full, unpaginated.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            q: Filter to users matching this text."""
        return self._get_api_list(
            f"{_base(connection_id)}/users",
            model=SalesforceUser,
            query=drop_not_given({"q": q}),
            options=options,
        )

    def list_views(
        self,
        connection_id: str,
        *,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceListView]:
        """List Lead or Contact list views. Returned in full, unpaginated.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``."""
        return self._get_api_list(
            f"{_base(connection_id)}/list-views",
            model=SalesforceListView,
            query=drop_not_given({"object": object}),
            options=options,
        )

    def campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceCampaign]:
        """Search Salesforce Campaigns. Returned in full, unpaginated.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            q: Filter to campaigns matching this text."""
        return self._get_api_list(
            f"{_base(connection_id)}/campaigns",
            model=SalesforceCampaign,
            query=drop_not_given({"q": q}),
            options=options,
        )

    def preview_import(
        self,
        connection_id: str,
        *,
        source_kind: str,
        object: str,
        source_id: str,
        options: RequestOptions | None = None,
    ) -> SalesforceImportPreview:
        """Read the first rows of a list view or Campaign without importing.

        Needs the ``integrations`` scope or the use-integrations permission.
        Read-only, so it is safe to repeat.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            object: ``"Lead"`` or ``"Contact"`` (for a list view).
            source_id: The Salesforce id of the list view or Campaign."""
        return self._post(
            f"{_base(connection_id)}/import/preview",
            cast_to=SalesforceImportPreview,
            body={"source_kind": source_kind, "object": object, "source_id": source_id},
            options=options,
        )

    def list_import_sources(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceImportSource]:
        """List the connection's saved imports. Returned in full, unpaginated.

        Needs read access to integrations."""
        return self._get_api_list(
            f"{_base(connection_id)}/import-sources",
            model=SalesforceImportSource,
            options=options,
        )

    def create_import_source(
        self,
        connection_id: str,
        *,
        source_kind: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        source_id: str,
        name: NotGivenOr[str] = NOT_GIVEN,
        source_label: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save an import and start its first run (``201``).

        Needs the ``integrations`` scope or the manage-settings permission.
        People are deduplicated by address, so repeating the call makes a
        second source whose run imports nothing new.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
            source_id: The Salesforce id of the list view or Campaign.
            name: A name for the import.
            source_label: The source's display label.
            campaign_id: A Warmbly campaign to add imported contacts to.
            category_ids: Categories to put imported contacts in.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active."""
        return self._post(
            f"{_base(connection_id)}/import-sources",
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

        Needs the ``integrations`` scope or the manage-settings permission.

        Args:
            connection_id: The Salesforce connection.
            source_id: The saved import (``SalesforceImportSource.id``), not
                the Salesforce id.
            name: A new name.
            source_label: A new display label.
            campaign_id: A Warmbly campaign to add imported contacts to, or
                ``None`` to clear the target. Left out, it is unchanged.
            category_ids: Categories to put imported contacts in.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return self._patch(
            f"{_base(connection_id)}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "source_label": source_label,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "recurring": recurring,
                    "enabled": enabled,
                }
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

        Needs the ``integrations`` scope or the use-integrations permission.
        A second call while a run is in progress is refused with ``409``, so
        retries cannot double-run it.

        Args:
            connection_id: The Salesforce connection.
            source_id: The saved import (``SalesforceImportSource.id``).
        """
        return self._post(
            f"{_base(connection_id)}/import-sources/{source_id}/run",
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
        """Remove a saved import (``204 No Content``). Its contacts stay.

        Needs the ``integrations`` scope or the manage-settings permission.
        """
        return self._delete(
            f"{_base(connection_id)}/import-sources/{source_id}",
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
        """Page the activity log, newest first.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            status: ``"pending"``, ``"synced"``, ``"skipped"`` or ``"failed"``.
            contact_id: Only this contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page."""
        return self._get_api_list(
            f"{_base(connection_id)}/activity",
            model=SalesforceActivity,
            query=drop_not_given(
                {
                    "status": status,
                    "contact_id": contact_id,
                    "limit": limit,
                    "cursor": cursor,
                }
            ),
            options=options,
        )

    def retry_activity(
        self,
        connection_id: str,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SalesforceRequeued:
        """Re-queue failed or skipped activity rows.

        Needs the ``integrations`` scope or the manage-settings permission.
        Re-queuing a row that is already pending changes nothing, so it is
        safe to repeat.

        Args:
            connection_id: The Salesforce connection.
            ids: Up to 500 activity ids."""
        return self._post(
            f"{_base(connection_id)}/activity/retry",
            cast_to=SalesforceRequeued,
            body={"ids": list(ids)},
            options=options,
        )

    def sync_now(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull Salesforce changes at once.

        Needs the ``integrations`` scope or the use-integrations permission.
        Both passes are idempotent, so repeating the call only repeats a no-op."""
        return self._post(
            f"{_base(connection_id)}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )


class AsyncSalesforce(AsyncAPIResource):
    """Asynchronous ``salesforce`` resource."""

    async def overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve the connection's health page.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            checks: Also run the live health checks (a few Salesforce calls),
                filling ``checks``."""
        return await self._get(
            f"{_base(connection_id)}/overview",
            cast_to=SalesforceOverview,
            query=drop_not_given({"checks": "1" if checks else NOT_GIVEN}),
            options=options,
        )

    async def get_settings(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsDocument:
        """Retrieve the sync settings, the Warmbly field vocabulary and the defaults.

        Needs read access to integrations."""
        return await self._get(
            f"{_base(connection_id)}/settings",
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
        """Replace the sync settings. This is a PUT of the whole document.

        Needs the ``integrations`` scope or the manage-settings permission.
        Send the complete document (start from ``get_settings().settings``),
        because a key left out reverts to its zero value rather than keeping
        its saved value. The server validates it and answers ``400`` on a bad
        one.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document: ``enabled``, ``matching``,
                ``activity``, ``writeback``, ``inbound``, ``field_map`` and
                ``daily_api_budget``."""
        return await self._put(
            f"{_base(connection_id)}/settings",
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    async def metadata(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceMetadata:
        """Retrieve the Lead and Contact fields and the picklists in the org.

        Needs read access to integrations."""
        return await self._get(
            f"{_base(connection_id)}/metadata",
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
        """Search active Salesforce users. Returned in full, unpaginated.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            q: Filter to users matching this text."""
        return self._get_api_list(
            f"{_base(connection_id)}/users",
            model=SalesforceUser,
            query=drop_not_given({"q": q}),
            options=options,
        )

    def list_views(
        self,
        connection_id: str,
        *,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceListView]:
        """List Lead or Contact list views. Returned in full, unpaginated.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``."""
        return self._get_api_list(
            f"{_base(connection_id)}/list-views",
            model=SalesforceListView,
            query=drop_not_given({"object": object}),
            options=options,
        )

    def campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceCampaign]:
        """Search Salesforce Campaigns. Returned in full, unpaginated.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            q: Filter to campaigns matching this text."""
        return self._get_api_list(
            f"{_base(connection_id)}/campaigns",
            model=SalesforceCampaign,
            query=drop_not_given({"q": q}),
            options=options,
        )

    async def preview_import(
        self,
        connection_id: str,
        *,
        source_kind: str,
        object: str,
        source_id: str,
        options: RequestOptions | None = None,
    ) -> SalesforceImportPreview:
        """Read the first rows of a list view or Campaign without importing.

        Needs the ``integrations`` scope or the use-integrations permission.
        Read-only, so it is safe to repeat.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            object: ``"Lead"`` or ``"Contact"`` (for a list view).
            source_id: The Salesforce id of the list view or Campaign."""
        return await self._post(
            f"{_base(connection_id)}/import/preview",
            cast_to=SalesforceImportPreview,
            body={"source_kind": source_kind, "object": object, "source_id": source_id},
            options=options,
        )

    def list_import_sources(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceImportSource]:
        """List the connection's saved imports. Returned in full, unpaginated.

        Needs read access to integrations."""
        return self._get_api_list(
            f"{_base(connection_id)}/import-sources",
            model=SalesforceImportSource,
            options=options,
        )

    async def create_import_source(
        self,
        connection_id: str,
        *,
        source_kind: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        source_id: str,
        name: NotGivenOr[str] = NOT_GIVEN,
        source_label: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save an import and start its first run (``201``).

        Needs the ``integrations`` scope or the manage-settings permission.
        People are deduplicated by address, so repeating the call makes a
        second source whose run imports nothing new.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
            source_id: The Salesforce id of the list view or Campaign.
            name: A name for the import.
            source_label: The source's display label.
            campaign_id: A Warmbly campaign to add imported contacts to.
            category_ids: Categories to put imported contacts in.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active."""
        return await self._post(
            f"{_base(connection_id)}/import-sources",
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

        Needs the ``integrations`` scope or the manage-settings permission.

        Args:
            connection_id: The Salesforce connection.
            source_id: The saved import (``SalesforceImportSource.id``), not
                the Salesforce id.
            name: A new name.
            source_label: A new display label.
            campaign_id: A Warmbly campaign to add imported contacts to, or
                ``None`` to clear the target. Left out, it is unchanged.
            category_ids: Categories to put imported contacts in.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return await self._patch(
            f"{_base(connection_id)}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "source_label": source_label,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "recurring": recurring,
                    "enabled": enabled,
                }
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

        Needs the ``integrations`` scope or the use-integrations permission.
        A second call while a run is in progress is refused with ``409``, so
        retries cannot double-run it.

        Args:
            connection_id: The Salesforce connection.
            source_id: The saved import (``SalesforceImportSource.id``).
        """
        return await self._post(
            f"{_base(connection_id)}/import-sources/{source_id}/run",
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
        """Remove a saved import (``204 No Content``). Its contacts stay.

        Needs the ``integrations`` scope or the manage-settings permission.
        """
        return await self._delete(
            f"{_base(connection_id)}/import-sources/{source_id}",
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
        """Page the activity log, newest first.

        Needs read access to integrations.

        Args:
            connection_id: The Salesforce connection.
            status: ``"pending"``, ``"synced"``, ``"skipped"`` or ``"failed"``.
            contact_id: Only this contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page."""
        return self._get_api_list(
            f"{_base(connection_id)}/activity",
            model=SalesforceActivity,
            query=drop_not_given(
                {
                    "status": status,
                    "contact_id": contact_id,
                    "limit": limit,
                    "cursor": cursor,
                }
            ),
            options=options,
        )

    async def retry_activity(
        self,
        connection_id: str,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SalesforceRequeued:
        """Re-queue failed or skipped activity rows.

        Needs the ``integrations`` scope or the manage-settings permission.
        Re-queuing a row that is already pending changes nothing, so it is
        safe to repeat.

        Args:
            connection_id: The Salesforce connection.
            ids: Up to 500 activity ids."""
        return await self._post(
            f"{_base(connection_id)}/activity/retry",
            cast_to=SalesforceRequeued,
            body={"ids": list(ids)},
            options=options,
        )

    async def sync_now(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull Salesforce changes at once.

        Needs the ``integrations`` scope or the use-integrations permission.
        Both passes are idempotent, so repeating the call only repeats a no-op."""
        return await self._post(
            f"{_base(connection_id)}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )
