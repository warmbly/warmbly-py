"""Provider-specific integration calls: Apollo, Salesforce and Clay.

These are the sub-namespaces of the ``integrations`` resource,
``client.integrations.apollo``, ``client.integrations.salesforce`` and
``client.integrations.clay``. Every call takes the id of an existing
connection (create it with ``client.integrations.create_connection`` or the
OAuth browser flow first) and maps to
``/v1/integrations/{apollo,salesforce,clay}/{connection_id}``.

Reads need the ``integrations`` API scope (or the use-integrations member
permission); changing what a connection syncs needs the manage-settings
permission with the same scope; running an import or a sync needs the
use-integrations permission with the same scope. Each method names its own bar.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given
from ._nullsafe import NullSafeModel

__all__ = [
    "ApolloEnrichmentRun",
    "ApolloImportSource",
    "ApolloList",
    "ApolloOverview",
    "ApolloPreview",
    "ApolloPreviewRow",
    "ApolloRunResult",
    "AsyncIntegrationApollo",
    "AsyncIntegrationClay",
    "AsyncIntegrationSalesforce",
    "ClayInboundDefaults",
    "ClayOutbound",
    "ClaySettings",
    "ClayStats",
    "IntegrationApollo",
    "IntegrationClay",
    "IntegrationSalesforce",
    "SalesforceActivity",
    "SalesforceActivityCounts",
    "SalesforceCampaign",
    "SalesforceCheck",
    "SalesforceField",
    "SalesforceImportSource",
    "SalesforceListView",
    "SalesforceMetadata",
    "SalesforceOverview",
    "SalesforcePicklistOption",
    "SalesforcePreview",
    "SalesforcePreviewRow",
    "SalesforceRequeued",
    "SalesforceRunResult",
    "SalesforceSettingsDocument",
    "SalesforceSettingsResult",
    "SalesforceSettingsSaved",
    "SalesforceSyncStarted",
    "SalesforceUser",
]


def _as_list(value: NotGivenOr[Sequence[str]]) -> NotGivenOr[list[str]]:
    return value if isinstance(value, NotGiven) else list(value)


def _as_dict(value: NotGivenOr[Mapping[str, Any]]) -> NotGivenOr[dict[str, Any]]:
    return value if isinstance(value, NotGiven) else dict(value)


# ---------------------------------------------------------------------------
# Apollo
# ---------------------------------------------------------------------------
class ApolloOverview(NullSafeModel):
    """The Apollo page header: the account a key acts as and what it has done."""

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    health_detail: str | None = None
    account_name: str | None = None
    account_email: str | None = None
    sources: int | None = None
    total_imported: int | None = None
    last_run_at: str | None = None


class ApolloList(NullSafeModel):
    """A saved Apollo contact list, as the import picker shows it."""

    id: str | None = None
    name: str | None = None
    count: int | None = None


class ApolloRunResult(NullSafeModel):
    """What one Apollo list import run did.

    ``next_page`` is where the next run resumes reading a list too long for
    one run.
    """

    read: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    no_email: int | None = None
    unverified: int | None = None
    suppressed: int | None = None
    truncated: bool | None = None
    already_seen: int | None = None
    next_page: int | None = None


class ApolloImportSource(NullSafeModel):
    """A saved Apollo list that feeds contacts into Warmbly.

    ``status`` is the run state (for example ``"running"``); unknown values
    are passed through.
    """

    id: str
    organization_id: str | None = None
    connection_id: str | None = None
    created_by_user_id: str | None = None
    name: str | None = None
    list_id: str | None = None
    list_name: str | None = None
    campaign_id: str | None = None
    category_ids: Sequence[str] = []
    verified_only: bool | None = None
    recurring: bool | None = None
    enabled: bool | None = None
    status: str | None = None
    last_run_at: str | None = None
    last_result: ApolloRunResult | None = None
    last_error: str | None = None
    total_imported: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ApolloPreviewRow(NullSafeModel):
    """One sample person of a list preview."""

    apollo_id: str | None = None
    name: str | None = None
    email: str | None = None
    email_status: str | None = None
    title: str | None = None
    company: str | None = None
    already_in_warmbly: bool | None = None
    will_import: bool | None = None


class ApolloPreview(NullSafeModel):
    """The first people of a list and how many it holds."""

    total: int | None = None
    sample: Sequence[ApolloPreviewRow] = []


class ApolloEnrichmentRun(NullSafeModel):
    """One background request to enrich Warmbly contacts through Apollo.

    ``status`` is ``"queued"``, ``"running"``, ``"done"`` or ``"error"``.
    """

    id: str
    organization_id: str | None = None
    connection_id: str | None = None
    requested_by_user_id: str | None = None
    overwrite: bool | None = None
    status: str | None = None
    total: int | None = None
    processed: int | None = None
    enriched: int | None = None
    not_found: int | None = None
    failed: int | None = None
    credits_consumed: int | None = None
    last_error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# ---------------------------------------------------------------------------
# Salesforce
# ---------------------------------------------------------------------------
class SalesforceCheck(NullSafeModel):
    """One permission or setup probe of the overview."""

    key: str | None = None
    label: str | None = None
    ok: bool | None = None
    detail: str | None = None


class SalesforceActivityCounts(NullSafeModel):
    """A summary of the activity outbox."""

    pending: int | None = None
    synced_24h: int | None = None
    failed: int | None = None
    skipped_24h: int | None = None
    linked_records: int | None = None


class SalesforceOverview(NullSafeModel):
    """The connection's health page.

    ``org``, ``api`` and ``counts`` are nested objects: ``org`` carries
    ``instance_url``, ``environment``, ``login_host`` and friends; ``api``
    carries ``used``, ``max``, ``calls_today`` and ``budget``. ``checks`` is
    populated only when requested.
    """

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    health_detail: str | None = None
    org: dict[str, Any] | None = None
    api: dict[str, Any] | None = None
    counts: SalesforceActivityCounts | None = None
    last_pull_at: str | None = None
    last_pull_error: str | None = None
    settings_enabled: bool | None = None
    checks: Sequence[SalesforceCheck] = []


class SalesforceSettingsDocument(NullSafeModel):
    """One connection's sync configuration.

    ``matching``, ``activity``, ``writeback`` and ``inbound`` are nested
    objects; ``field_map`` is a list of rules, each
    ``{"object", "warmbly", "salesforce", "direction", "policy"}``.
    """

    enabled: bool | None = None
    matching: dict[str, Any] | None = None
    activity: dict[str, Any] | None = None
    writeback: dict[str, Any] | None = None
    inbound: dict[str, Any] | None = None
    field_map: Sequence[dict[str, Any]] = []
    daily_api_budget: int | None = None


class SalesforceSettingsResult(NullSafeModel):
    """The sync settings with the Warmbly field vocabulary and the defaults.

    ``warmbly_fields`` is a list of ``{"key", "label"}``.
    """

    settings: SalesforceSettingsDocument | None = None
    warmbly_fields: Sequence[dict[str, Any]] = []
    defaults: SalesforceSettingsDocument | None = None


class SalesforceSettingsSaved(NullSafeModel):
    """The settings as stored after a save."""

    settings: SalesforceSettingsDocument | None = None


class SalesforcePicklistOption(NullSafeModel):
    """A picklist value."""

    value: str | None = None
    label: str | None = None


class SalesforceField(NullSafeModel):
    """One Lead or Contact field as the mapping editor shows it."""

    name: str | None = None
    label: str | None = None
    type: str | None = None
    createable: bool | None = None
    updateable: bool | None = None
    calculated: bool | None = None
    custom: bool | None = None
    picklist: Sequence[SalesforcePicklistOption] = []


class SalesforceMetadata(NullSafeModel):
    """The fields and picklists the settings screens pick from."""

    lead_fields: Sequence[SalesforceField] = []
    contact_fields: Sequence[SalesforceField] = []
    lead_statuses: Sequence[SalesforcePicklistOption] = []
    lead_sources: Sequence[SalesforcePicklistOption] = []


class SalesforceUser(NullSafeModel):
    """An active Salesforce user, for owner pickers."""

    id: str | None = None
    name: str | None = None
    email: str | None = None


class SalesforceListView(NullSafeModel):
    """A list view for the import picker."""

    id: str | None = None
    label: str | None = None
    object: str | None = None


class SalesforceCampaign(NullSafeModel):
    """A Salesforce Campaign for the import picker."""

    id: str | None = None
    name: str | None = None
    status: str | None = None
    type: str | None = None
    member_count: int | None = None


class SalesforceRunResult(NullSafeModel):
    """What one Salesforce import run did."""

    read: int | None = None
    imported: int | None = None
    updated: int | None = None
    linked: int | None = None
    skipped: int | None = None
    failed: int | None = None
    no_email: int | None = None
    opted_out: int | None = None
    truncated: bool | None = None


class SalesforceImportSource(NullSafeModel):
    """A saved list view or Salesforce Campaign that feeds contacts in.

    ``source_kind`` is ``"list_view"`` or ``"campaign"``; ``object`` is
    ``"Lead"``, ``"Contact"`` or ``"CampaignMember"``.
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


class SalesforcePreviewRow(NullSafeModel):
    """One sample row of an import preview."""

    record_id: str | None = None
    object: str | None = None
    name: str | None = None
    email: str | None = None
    company: str | None = None
    title: str | None = None
    owner_name: str | None = None
    status: str | None = None
    already_linked: bool | None = None


class SalesforcePreview(NullSafeModel):
    """The first rows of an import source and how many it holds."""

    total: int | None = None
    sample: Sequence[SalesforcePreviewRow] = []


class SalesforceActivity(NullSafeModel):
    """One queued or processed activity: a campaign event logged as a Task.

    ``status`` is ``"pending"``, ``"synced"``, ``"skipped"`` or ``"failed"``;
    ``kind`` is the event (``sent``, ``replied``, ``bounced``, ...).
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


class SalesforceRequeued(NullSafeModel):
    """How many activity rows a retry put back in the queue."""

    requeued: int | None = None


class SalesforceSyncStarted(NullSafeModel):
    """The acknowledgement of a sync-now call."""

    ok: bool | None = None


# ---------------------------------------------------------------------------
# Clay
# ---------------------------------------------------------------------------
class ClayInboundDefaults(NullSafeModel):
    """Where rows a Clay table sends land.

    ``dedup`` is ``"skip"``, ``"update"`` or ``"create_duplicate"``.
    """

    campaign_id: str | None = None
    category_ids: Sequence[str] = []
    segment_ids: Sequence[str] = []
    dedup: str | None = None
    subscribed: bool | None = None


class ClayOutbound(NullSafeModel):
    """The default Clay table Warmbly sends events to.

    The URL and token are never returned; only whether they are set.
    """

    webhook_url_set: bool | None = None
    webhook_host: str | None = None
    auth_token_set: bool | None = None
    events: Sequence[str] = []


class ClayStats(NullSafeModel):
    """What the Clay inbound URL has received."""

    received: int | None = None
    created: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    last_received_at: str | None = None
    last_error: str | None = None


class ClaySettings(NullSafeModel):
    """Everything the Clay page edits and shows."""

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    inbound_url_minted: bool | None = None
    defaults: ClayInboundDefaults | None = None
    outbound: ClayOutbound | None = None
    stats: ClayStats | None = None
    available_events: Sequence[str] = []


class IntegrationApollo(SyncAPIResource):
    """Synchronous Apollo calls, ``client.integrations.apollo``."""

    def overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Retrieve the Apollo page header for a connection.

        Requires the ``integrations`` API scope.
        """
        return self._get(
            f"/integrations/apollo/{connection_id}",
            cast_to=ApolloOverview,
            options=options,
        )

    def replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        Repeating the call with the same key converges on the same state.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._put(
            f"/integrations/apollo/{connection_id}/key",
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def list_lists(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ApolloList]:
        """List the account's saved Apollo contact lists. Returned in full.

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/lists",
            model=ApolloList,
            options=options,
        )

    def preview_import(
        self,
        connection_id: str,
        *,
        list_id: str,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloPreview:
        """Read the first people of an Apollo list without importing.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list to read.
            verified_only: Only count people with a verified address. The
                server defaults to ``True``.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import/preview",
            cast_to=ApolloPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ApolloImportSource]:
        """List a connection's saved list imports. Returned in full.

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/import-sources",
            model=ApolloImportSource,
            options=options,
        )

    def create_import_source(
        self,
        connection_id: str,
        *,
        list_id: str,
        list_name: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Save a list import and start its first run.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list to import (max 64 characters).
            list_name: The list's display name.
            name: A name for the import; defaults to the list name.
            campaign_id: A campaign to enroll new contacts into.
            category_ids: Categories to file new contacts under (max 50).
            verified_only: Skip unverified addresses. Defaults to ``True``.
            recurring: Re-read the list every hour.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import-sources",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "list_id": list_id,
                    "list_name": list_name,
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
                    "verified_only": verified_only,
                    "recurring": recurring,
                }
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
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Edit a list import's targets, filter and schedule.

        Args:
            connection_id: The Apollo connection.
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A campaign to enroll into; pass ``None`` to clear it.
            category_ids: Categories to file new contacts under (max 50).
            verified_only: Skip unverified addresses.
            recurring: Re-read the list every hour.
            enabled: Whether scheduled runs happen.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._patch(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
                    "verified_only": verified_only,
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
    ) -> ApolloImportSource:
        """Run a list import now.

        A run already in progress is refused with a conflict, so a retry
        cannot double-run it.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}/run",
            cast_to=ApolloImportSource,
            options=options,
        )

    def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Remove a list import. Contacts it already brought in stay.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._delete(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=type(None),
            options=options,
        )

    def list_enrichments(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApolloEnrichmentRun]:
        """List a connection's recent enrichment runs.

        Args:
            connection_id: The Apollo connection.
            limit: How many runs, 1 to 100 (default 20). Not paginated.

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/enrichments",
            model=ApolloEnrichmentRun,
            query={"limit": limit},
            options=options,
        )

    def get_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Retrieve one enrichment run's progress.

        Requires the ``integrations`` API scope.
        """
        return self._get(
            f"/integrations/apollo/{connection_id}/enrichments/{run_id}",
            cast_to=ApolloEnrichmentRun,
            options=options,
        )

    def start_enrichment(
        self,
        connection_id: str,
        *,
        contacts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        overwrite: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Queue an enrichment run over a contact selection (``202 Accepted``).

        Enrichment writes contacts and spends the customer's Apollo credits,
        and needs a paid plan. Name the contacts with *contacts* (or the older
        *contact_ids*), or with *select_all* plus the search *filters*.

        Args:
            connection_id: The Apollo connection.
            contacts: Contact ids to enrich (at most 5,000 in total).
            select_all: Act on every contact matching *filters* instead.
            filters: The body ``client.contacts.search`` takes, as a mapping.
            exclude: Ids to drop from a select-all.
            contact_ids: Alias of *contacts* kept for older callers.
            overwrite: Replace values contacts already have.

        Requires the use-integrations permission and the manage-contacts
        permission (API scopes ``integrations`` and ``bulk_contacts``).
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/enrichments",
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contacts": _as_list(contacts),
                    "all": select_all,
                    "filters": _as_dict(filters),
                    "exclude": _as_list(exclude),
                    "contact_ids": _as_list(contact_ids),
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )


class IntegrationSalesforce(SyncAPIResource):
    """Synchronous Salesforce calls, ``client.integrations.salesforce``."""

    def overview(
        self,
        connection_id: str,
        *,
        checks: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve the connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe permissions and setup (slower; calls Salesforce).

        Requires the ``integrations`` API scope.
        """
        return self._get(
            f"/integrations/salesforce/{connection_id}/overview",
            cast_to=SalesforceOverview,
            query={"checks": "1" if checks is True else NOT_GIVEN},
            options=options,
        )

    def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettingsResult:
        """Retrieve the sync settings, the Warmbly field list and the defaults.

        Requires the ``integrations`` API scope.
        """
        return self._get(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsResult,
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

        This is a whole-document write, so read :meth:`get_settings` first,
        change what you need and send the full document back. Repeating the
        call converges on the same state.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document: ``enabled``, ``matching``,
                ``activity``, ``writeback``, ``inbound``, ``field_map`` and
                ``daily_api_budget``.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._put(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    def get_metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Retrieve Lead and Contact fields and picklists.

        Requires the ``integrations`` API scope.
        """
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
        """Search active Salesforce users (at most 50, not paginated).

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/users",
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def list_list_views(
        self,
        connection_id: str,
        *,
        object: str,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceListView]:
        """List an object's list views.

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``.

        Requires the ``integrations`` API scope.
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
        """Search Salesforce Campaigns (at most 50, not paginated).

        Requires the ``integrations`` API scope.
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
    ) -> SalesforcePreview:
        """Read the first rows of a list view or Campaign without importing.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import/preview",
            cast_to=SalesforcePreview,
            body=drop_not_given(
                {"source_kind": source_kind, "source_id": source_id, "object": object}
            ),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[SalesforceImportSource]:
        """List a connection's saved imports. Returned in full.

        Requires the ``integrations`` API scope.
        """
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
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save an import and start its first run.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
            source_label: The source's display name.
            name: A name for the import; defaults to the label.
            campaign_id: A Warmbly campaign to enroll new contacts into.
            category_ids: Categories to file new contacts under (max 50).
            recurring: Re-read the source on a schedule.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import-sources",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "source_kind": source_kind,
                    "source_id": source_id,
                    "object": object,
                    "source_label": source_label,
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
                    "recurring": recurring,
                }
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
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A campaign to enroll into; pass ``None`` to clear it.
            category_ids: Categories to file new contacts under (max 50).
            recurring: Re-read the source on a schedule.
            enabled: Whether scheduled runs happen.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._patch(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
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
        """Run an import now.

        A run already in progress is refused with a conflict, so a retry
        cannot double-run it.

        Requires the use-integrations permission (API scope ``integrations``).
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
    ) -> None:
        """Remove an import. Contacts it already brought in stay.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._delete(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=type(None),
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
            status: ``pending``, ``synced``, ``skipped`` or ``failed``.
            contact_id: Only this contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: Resume from a previous page.

        Requires the ``integrations`` API scope.
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
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceRequeued:
        """Re-queue failed or skipped activity rows.

        Re-queuing a row that is already pending changes nothing, so a retry
        is safe.

        Args:
            connection_id: The Salesforce connection.
            ids: Activity ids to re-queue (at most 500). Omit to re-queue
                every failed row.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/activity/retry",
            cast_to=SalesforceRequeued,
            body=drop_not_given({"ids": _as_list(ids)}),
            options=options,
        )

    def sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull changes at once.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )


class IntegrationClay(SyncAPIResource):
    """Synchronous Clay calls, ``client.integrations.clay``."""

    def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ClaySettings:
        """Retrieve everything the Clay page shows.

        Requires the ``integrations`` API scope.
        """
        return self._get(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            options=options,
        )

    def update_settings(
        self,
        connection_id: str,
        *,
        defaults: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str | None] = NOT_GIVEN,
        auth_token: NotGivenOr[str | None] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ClaySettings:
        """Save the inbound defaults, the outbound table and its events.

        Every field that is passed replaces its stored value, so a retry
        converges; omitted fields are left alone.

        Args:
            connection_id: The Clay connection.
            defaults: Where inbound rows land: ``campaign_id``,
                ``category_ids``, ``segment_ids``, ``dedup`` (``skip``,
                ``update`` or ``create_duplicate``) and ``subscribed``.
            webhook_url: The Clay table's webhook URL; an empty string clears it.
            auth_token: The table's auth token; an empty string clears it.
            events: The Warmbly events sent to the table.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return self._patch(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            body=drop_not_given(
                {
                    "defaults": _as_dict(defaults),
                    "webhook_url": webhook_url,
                    "auth_token": auth_token,
                    "events": _as_list(events),
                }
            ),
            options=options,
        )


class AsyncIntegrationApollo(AsyncAPIResource):
    """Asynchronous Apollo calls, ``client.integrations.apollo``."""

    async def overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Retrieve the Apollo page header for a connection.

        Requires the ``integrations`` API scope.
        """
        return await self._get(
            f"/integrations/apollo/{connection_id}",
            cast_to=ApolloOverview,
            options=options,
        )

    async def replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        Repeating the call with the same key converges on the same state.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._put(
            f"/integrations/apollo/{connection_id}/key",
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def list_lists(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ApolloList]:
        """List the account's saved Apollo contact lists. Returned in full.

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/lists",
            model=ApolloList,
            options=options,
        )

    async def preview_import(
        self,
        connection_id: str,
        *,
        list_id: str,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloPreview:
        """Read the first people of an Apollo list without importing.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list to read.
            verified_only: Only count people with a verified address. The
                server defaults to ``True``.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import/preview",
            cast_to=ApolloPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ApolloImportSource]:
        """List a connection's saved list imports. Returned in full.

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/import-sources",
            model=ApolloImportSource,
            options=options,
        )

    async def create_import_source(
        self,
        connection_id: str,
        *,
        list_id: str,
        list_name: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Save a list import and start its first run.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list to import (max 64 characters).
            list_name: The list's display name.
            name: A name for the import; defaults to the list name.
            campaign_id: A campaign to enroll new contacts into.
            category_ids: Categories to file new contacts under (max 50).
            verified_only: Skip unverified addresses. Defaults to ``True``.
            recurring: Re-read the list every hour.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import-sources",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "list_id": list_id,
                    "list_name": list_name,
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
                    "verified_only": verified_only,
                    "recurring": recurring,
                }
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
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Edit a list import's targets, filter and schedule.

        Args:
            connection_id: The Apollo connection.
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A campaign to enroll into; pass ``None`` to clear it.
            category_ids: Categories to file new contacts under (max 50).
            verified_only: Skip unverified addresses.
            recurring: Re-read the list every hour.
            enabled: Whether scheduled runs happen.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._patch(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
                    "verified_only": verified_only,
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
    ) -> ApolloImportSource:
        """Run a list import now.

        A run already in progress is refused with a conflict, so a retry
        cannot double-run it.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}/run",
            cast_to=ApolloImportSource,
            options=options,
        )

    async def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Remove a list import. Contacts it already brought in stay.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._delete(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=type(None),
            options=options,
        )

    def list_enrichments(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApolloEnrichmentRun]:
        """List a connection's recent enrichment runs.

        Args:
            connection_id: The Apollo connection.
            limit: How many runs, 1 to 100 (default 20). Not paginated.

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/enrichments",
            model=ApolloEnrichmentRun,
            query={"limit": limit},
            options=options,
        )

    async def get_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Retrieve one enrichment run's progress.

        Requires the ``integrations`` API scope.
        """
        return await self._get(
            f"/integrations/apollo/{connection_id}/enrichments/{run_id}",
            cast_to=ApolloEnrichmentRun,
            options=options,
        )

    async def start_enrichment(
        self,
        connection_id: str,
        *,
        contacts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        overwrite: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Queue an enrichment run over a contact selection (``202 Accepted``).

        Enrichment writes contacts and spends the customer's Apollo credits,
        and needs a paid plan. Name the contacts with *contacts* (or the older
        *contact_ids*), or with *select_all* plus the search *filters*.

        Args:
            connection_id: The Apollo connection.
            contacts: Contact ids to enrich (at most 5,000 in total).
            select_all: Act on every contact matching *filters* instead.
            filters: The body ``client.contacts.search`` takes, as a mapping.
            exclude: Ids to drop from a select-all.
            contact_ids: Alias of *contacts* kept for older callers.
            overwrite: Replace values contacts already have.

        Requires the use-integrations permission and the manage-contacts
        permission (API scopes ``integrations`` and ``bulk_contacts``).
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/enrichments",
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contacts": _as_list(contacts),
                    "all": select_all,
                    "filters": _as_dict(filters),
                    "exclude": _as_list(exclude),
                    "contact_ids": _as_list(contact_ids),
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )


class AsyncIntegrationSalesforce(AsyncAPIResource):
    """Asynchronous Salesforce calls, ``client.integrations.salesforce``."""

    async def overview(
        self,
        connection_id: str,
        *,
        checks: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve the connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe permissions and setup (slower; calls Salesforce).

        Requires the ``integrations`` API scope.
        """
        return await self._get(
            f"/integrations/salesforce/{connection_id}/overview",
            cast_to=SalesforceOverview,
            query={"checks": "1" if checks is True else NOT_GIVEN},
            options=options,
        )

    async def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettingsResult:
        """Retrieve the sync settings, the Warmbly field list and the defaults.

        Requires the ``integrations`` API scope.
        """
        return await self._get(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsResult,
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

        This is a whole-document write, so read :meth:`get_settings` first,
        change what you need and send the full document back. Repeating the
        call converges on the same state.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings document: ``enabled``, ``matching``,
                ``activity``, ``writeback``, ``inbound``, ``field_map`` and
                ``daily_api_budget``.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._put(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsSaved,
            body=dict(settings),
            options=options,
        )

    async def get_metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Retrieve Lead and Contact fields and picklists.

        Requires the ``integrations`` API scope.
        """
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
        """Search active Salesforce users (at most 50, not paginated).

        Requires the ``integrations`` API scope.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/users",
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def list_list_views(
        self,
        connection_id: str,
        *,
        object: str,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceListView]:
        """List an object's list views.

        Args:
            connection_id: The Salesforce connection.
            object: ``"Lead"`` or ``"Contact"``.

        Requires the ``integrations`` API scope.
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
        """Search Salesforce Campaigns (at most 50, not paginated).

        Requires the ``integrations`` API scope.
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
    ) -> SalesforcePreview:
        """Read the first rows of a list view or Campaign without importing.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import/preview",
            cast_to=SalesforcePreview,
            body=drop_not_given(
                {"source_kind": source_kind, "source_id": source_id, "object": object}
            ),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[SalesforceImportSource]:
        """List a connection's saved imports. Returned in full.

        Requires the ``integrations`` API scope.
        """
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
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save an import and start its first run.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The list view or Campaign id.
            object: ``"Lead"`` or ``"Contact"``; required for a list view.
            source_label: The source's display name.
            name: A name for the import; defaults to the label.
            campaign_id: A Warmbly campaign to enroll new contacts into.
            category_ids: Categories to file new contacts under (max 50).
            recurring: Re-read the source on a schedule.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import-sources",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "source_kind": source_kind,
                    "source_id": source_id,
                    "object": object,
                    "source_label": source_label,
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
                    "recurring": recurring,
                }
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
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A campaign to enroll into; pass ``None`` to clear it.
            category_ids: Categories to file new contacts under (max 50).
            recurring: Re-read the source on a schedule.
            enabled: Whether scheduled runs happen.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._patch(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": _as_list(category_ids),
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
        """Run an import now.

        A run already in progress is refused with a conflict, so a retry
        cannot double-run it.

        Requires the use-integrations permission (API scope ``integrations``).
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
    ) -> None:
        """Remove an import. Contacts it already brought in stay.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._delete(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=type(None),
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
            status: ``pending``, ``synced``, ``skipped`` or ``failed``.
            contact_id: Only this contact's activity.
            limit: Page size, 1 to 200 (default 50).
            cursor: Resume from a previous page.

        Requires the ``integrations`` API scope.
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
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforceRequeued:
        """Re-queue failed or skipped activity rows.

        Re-queuing a row that is already pending changes nothing, so a retry
        is safe.

        Args:
            connection_id: The Salesforce connection.
            ids: Activity ids to re-queue (at most 500). Omit to re-queue
                every failed row.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/activity/retry",
            cast_to=SalesforceRequeued,
            body=drop_not_given({"ids": _as_list(ids)}),
            options=options,
        )

    async def sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending activity and pull changes at once.

        Requires the use-integrations permission (API scope ``integrations``).
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )


class AsyncIntegrationClay(AsyncAPIResource):
    """Asynchronous Clay calls, ``client.integrations.clay``."""

    async def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ClaySettings:
        """Retrieve everything the Clay page shows.

        Requires the ``integrations`` API scope.
        """
        return await self._get(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            options=options,
        )

    async def update_settings(
        self,
        connection_id: str,
        *,
        defaults: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str | None] = NOT_GIVEN,
        auth_token: NotGivenOr[str | None] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ClaySettings:
        """Save the inbound defaults, the outbound table and its events.

        Every field that is passed replaces its stored value, so a retry
        converges; omitted fields are left alone.

        Args:
            connection_id: The Clay connection.
            defaults: Where inbound rows land: ``campaign_id``,
                ``category_ids``, ``segment_ids``, ``dedup`` (``skip``,
                ``update`` or ``create_duplicate``) and ``subscribed``.
            webhook_url: The Clay table's webhook URL; an empty string clears it.
            auth_token: The table's auth token; an empty string clears it.
            events: The Warmbly events sent to the table.

        Requires the manage-settings permission (API scope ``integrations``).
        """
        return await self._patch(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            body=drop_not_given(
                {
                    "defaults": _as_dict(defaults),
                    "webhook_url": webhook_url,
                    "auth_token": auth_token,
                    "events": _as_list(events),
                }
            ),
            options=options,
        )
