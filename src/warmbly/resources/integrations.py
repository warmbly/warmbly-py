"""The ``integrations`` resource: third-party connections.

Maps to the ``/v1/integrations`` route group. Covers the catalog of available
providers, the connections an organization has configured, their event
subscriptions, field mappings, sync runs, webhook signing secrets, connection
testing, contact pushes, and recently booked meetings.

Provider-specific pages live here too, prefixed by provider: ``apollo_*``
(list imports and contact enrichment), ``clay_*`` (inbound defaults and the
outbound table) and ``salesforce_*`` (sync settings, imports and the activity
log). ``community_apps`` browses the community app directory.

Connecting an OAuth provider is a session-only browser flow
(``/v1/integrations/oauth/*``), so it is not reachable with an API key or OAuth
token; :meth:`Integrations.create_connection` covers the API-key- and
webhook-style providers.

Sub-objects (``config``, ``display_fields``, mapping entries) are modeled
permissively because provider shapes vary and the catalog grows.
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
    "ApolloEnrichmentRun",
    "ApolloImportSource",
    "ApolloImportSourceDeleted",
    "ApolloList",
    "ApolloOverview",
    "ApolloPreview",
    "ApolloPreviewRow",
    "ApolloRunResult",
    "AppPermission",
    "AsyncIntegrations",
    "ClayInboundDefaults",
    "ClayOutbound",
    "ClaySettings",
    "ClayStats",
    "CommunityApp",
    "IntegrationBooking",
    "IntegrationCatalogEntry",
    "IntegrationConnection",
    "IntegrationConnectionDeleted",
    "IntegrationConnectionDetail",
    "IntegrationEvent",
    "IntegrationEventDeleted",
    "IntegrationFieldMapping",
    "IntegrationFieldMappings",
    "IntegrationInboundUrl",
    "IntegrationRun",
    "IntegrationTestResult",
    "IntegrationWebhookSecret",
    "Integrations",
    "PushResult",
    "SalesforceActivity",
    "SalesforceActivityCounts",
    "SalesforceActivityRules",
    "SalesforceApiUsage",
    "SalesforceCampaign",
    "SalesforceCheck",
    "SalesforceFieldDef",
    "SalesforceFieldInfo",
    "SalesforceFieldRule",
    "SalesforceImportSource",
    "SalesforceImportSourceDeleted",
    "SalesforceInbound",
    "SalesforceListView",
    "SalesforceMatching",
    "SalesforceMetadata",
    "SalesforceOrg",
    "SalesforceOverview",
    "SalesforcePickOption",
    "SalesforcePreview",
    "SalesforcePreviewRow",
    "SalesforceRequeued",
    "SalesforceRunResult",
    "SalesforceSettings",
    "SalesforceSettingsResult",
    "SalesforceSyncStarted",
    "SalesforceUser",
    "SalesforceWriteback",
]


class IntegrationCatalogEntry(BaseModel):
    """A provider available to connect from the integrations catalog.

    ``configured`` reports whether this deployment has the credentials needed
    to offer the provider at all. ``rank`` is the provider's popularity on this
    instance, 1 being the most used.
    """

    provider: str
    name: str | None = None
    tagline: str | None = None
    category: str | None = None
    docs_url: str | None = None
    auth_method: str | None = None
    badge_color: str | None = None
    beta: bool | None = None
    webhook_hint: str | None = None
    highlights: Sequence[str] = []
    scopes: Sequence[str] = []
    events: Sequence[str] = []
    action_types: Sequence[str] = []
    supports_push: bool | None = None
    capability: dict[str, Any] | None = None
    configured: bool | None = None
    rank: int | None = None


class IntegrationConnection(BaseModel):
    """A configured connection to a third-party provider."""

    id: str
    organization_id: str | None = None
    provider: str | None = None
    label: str | None = None
    status: str | None = None
    auth_method: str | None = None
    display_fields: dict[str, Any] | None = None
    config_capabilities: dict[str, Any] | None = None
    sync_direction: str | None = None
    connected_by_user_id: str | None = None
    external_account_id: str | None = None
    external_account_name: str | None = None
    granted_scopes: Sequence[str] = []
    token_expires_at: str | None = None
    health: str | None = None
    health_detail: str | None = None
    health_checked_at: str | None = None
    inbound_webhook_url: str | None = None
    last_synced_at: str | None = None
    last_error: str | None = None
    last_error_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class IntegrationEvent(BaseModel):
    """An event subscription on a connection."""

    id: str
    connection_id: str | None = None
    organization_id: str | None = None
    event_type: str | None = None
    action: str | None = None
    config: dict[str, Any] | None = None
    enabled: bool | None = None
    use_case: str | None = None
    automation_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class IntegrationRun(BaseModel):
    """A single sync run for a connection."""

    id: str
    connection_id: str | None = None
    organization_id: str | None = None
    kind: str | None = None
    status: str | None = None
    detail: str | None = None
    records_processed: int | None = None
    started_at: str | None = None
    finished_at: str | None = None


class IntegrationConnectionDetail(BaseModel):
    """A connection together with its subscriptions and recent runs.

    This is the shape both :meth:`Integrations.get_connection` and
    :meth:`Integrations.update_connection_config` return; the latter populates
    only ``connection``.
    """

    connection: IntegrationConnection | None = None
    events: Sequence[IntegrationEvent] = []
    runs: Sequence[IntegrationRun] = []


class IntegrationConnectionDeleted(BaseModel):
    """The result of removing a connection (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class IntegrationEventDeleted(BaseModel):
    """The result of removing an event subscription (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class IntegrationFieldMapping(BaseModel):
    """One field map between a Warmbly field and a provider field."""

    id: str | None = None
    connection_id: str | None = None
    organization_id: str | None = None
    subscription_id: str | None = None
    direction: str | None = None
    object_name: str | None = None
    warmbly_field: str | None = None
    external_field: str | None = None
    transform: str | None = None
    static_value: str | None = None
    is_default: bool | None = None
    created_at: str | None = None


class IntegrationFieldMappings(BaseModel):
    """The full set of field mappings configured for a connection."""

    mappings: Sequence[IntegrationFieldMapping] = []


class IntegrationWebhookSecret(BaseModel):
    """A connection's inbound webhook signing secret and its scheme.

    ``scheme`` documents exactly what is signed so you can verify the
    ``signature_header`` on inbound provider webhooks.
    """

    signing_secret: str | None = None
    signature_header: str | None = None
    scheme: str | None = None


class IntegrationTestResult(BaseModel):
    """The result of firing a synthetic event through a connection.

    ``sent`` counts the automations the test event actually reached, so ``0``
    means the connection is live but nothing is wired to it.
    """

    sent: int | None = None


class PushResult(BaseModel):
    """The result of pushing contacts into a connected CRM.

    ``results`` carries one entry per contact, so a partial failure is legible
    rather than an opaque count.
    """

    provider: str | None = None
    pushed: int | None = None
    failed: int | None = None
    results: Sequence[dict[str, Any]] = []


class IntegrationBooking(BaseModel):
    """A booked meeting ingested from a scheduling provider."""

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


class IntegrationInboundUrl(BaseModel):
    """A freshly minted inbound webhook URL for a Calendly or Cal.com
    connection. The previous URL stops working at once."""

    inbound_webhook_url: str | None = None


class AppPermission(BaseModel):
    """One API permission a community app is granted."""

    name: str | None = None
    value: int | None = None
    description: str | None = None
    category: str | None = None


class CommunityApp(BaseModel):
    """A published community app as a workspace browsing the directory sees it.

    ``scopes`` is the permission bitmask and ``permissions`` spells it out.
    ``status`` is ``"published"`` or ``"featured"``; ``listed`` is ``True`` when
    the app shows in discovery; ``installed`` is ``True`` when this workspace
    already uses it. No credential, redirect or webhook field is ever included.
    """

    application_id: str | None = None
    slug: str | None = None
    name: str | None = None
    tagline: str | None = None
    description: str | None = None
    category: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    install_url: str | None = None
    support_url: str | None = None
    privacy_url: str | None = None
    developer: str | None = None
    scopes: int | None = None
    permissions: Sequence[AppPermission] = []
    status: str | None = None
    listed: bool | None = None
    installs: int | None = None
    installed: bool | None = None
    published_at: str | None = None


class ApolloOverview(BaseModel):
    """The Apollo page header: the account a key acts as and what the
    connection has done."""

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


class ApolloList(BaseModel):
    """A saved Apollo list of contacts."""

    id: str
    name: str | None = None
    count: int | None = None


class ApolloPreviewRow(BaseModel):
    """One sample person of an Apollo list preview."""

    apollo_id: str | None = None
    name: str | None = None
    email: str | None = None
    email_status: str | None = None
    title: str | None = None
    company: str | None = None
    already_in_warmbly: bool | None = None
    will_import: bool | None = None


class ApolloPreview(BaseModel):
    """The first people of an Apollo list and how many it holds."""

    total: int | None = None
    sample: Sequence[ApolloPreviewRow] = []


class ApolloRunResult(BaseModel):
    """What one Apollo list import run did.

    ``next_page`` is where the next run resumes a list too long for one run.
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


class ApolloImportSource(BaseModel):
    """A saved Apollo list that feeds contacts into Warmbly.

    ``status`` is ``"running"`` while a run is in flight.
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


class ApolloImportSourceDeleted(BaseModel):
    """The result of removing an Apollo import source (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class ApolloEnrichmentRun(BaseModel):
    """One background request to enrich Warmbly contacts through Apollo.

    ``status`` is ``queued``, ``running``, ``done`` or ``error``.
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


class ClayInboundDefaults(BaseModel):
    """Where rows a Clay table sends land by default."""

    campaign_id: str | None = None
    category_ids: Sequence[str] = []
    segment_ids: Sequence[str] = []
    dedup: str | None = None
    subscribed: bool | None = None


class ClayOutbound(BaseModel):
    """The default Clay table Warmbly sends events to.

    The URL and token are sealed on the connection; only their presence is
    reported.
    """

    webhook_url_set: bool | None = None
    webhook_host: str | None = None
    auth_token_set: bool | None = None
    events: Sequence[str] = []


class ClayStats(BaseModel):
    """What the inbound URL has received."""

    received: int | None = None
    created: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    last_received_at: str | None = None
    last_error: str | None = None


class ClaySettings(BaseModel):
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


class SalesforceMatching(BaseModel):
    """Which record an email is, and what happens when it is none.

    ``prefer`` is ``contact`` or ``lead``; ``create_when`` is ``never``,
    ``reply`` or ``send``; ``create_as`` is ``lead`` or ``contact``; ``owner``
    is ``connected_user``, ``sender`` or ``fixed`` (with ``owner_id``).
    """

    prefer: str | None = None
    create_when: str | None = None
    create_as: str | None = None
    lead_source: str | None = None
    lead_status: str | None = None
    owner: str | None = None
    owner_id: str | None = None
    run_assignment_rules: bool | None = None


class SalesforceActivityRules(BaseModel):
    """Which campaign events become Salesforce Tasks.

    ``assign_to`` is ``record_owner``, ``sender`` or ``connected_user``.
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


class SalesforceWriteback(BaseModel):
    """Which Lead and Contact fields Warmbly changes.

    ``lead_status_on_reply`` maps a reply intent (``positive``, ``negative``,
    ``neutral``, ``question``, ``out_of_office`` or ``any``) to a Lead status.
    """

    lead_status_on_sent: str | None = None
    lead_status_on_reply: dict[str, str] = {}
    lead_status_on_meeting: str | None = None
    never_move_backwards: bool | None = None


class SalesforceInbound(BaseModel):
    """What a change in Salesforce does in Warmbly.

    ``opt_out`` is ``both``, ``to_salesforce``, ``from_salesforce`` or ``off``.
    """

    opt_out: str | None = None
    pause_on_converted: bool | None = None
    pause_on_statuses: Sequence[str] = []
    pause_on_open_opportunity: bool | None = None


class SalesforceFieldRule(BaseModel):
    """Syncs one Warmbly field with one Salesforce field.

    ``object`` is ``Lead`` or ``Contact``; ``direction`` is ``push``, ``pull``
    or ``both``; ``policy`` is ``overwrite`` or ``if_empty``.
    """

    object: str | None = None
    warmbly: str | None = None
    salesforce: str | None = None
    direction: str | None = None
    policy: str | None = None


class SalesforceSettings(BaseModel):
    """One connection's Salesforce sync configuration.

    ``daily_api_budget`` of ``0`` means a fifth of the org's daily allocation.
    """

    enabled: bool | None = None
    matching: SalesforceMatching | None = None
    activity: SalesforceActivityRules | None = None
    writeback: SalesforceWriteback | None = None
    inbound: SalesforceInbound | None = None
    field_map: Sequence[SalesforceFieldRule] = []
    daily_api_budget: int | None = None


class SalesforceFieldDef(BaseModel):
    """A Warmbly field a Salesforce field rule may name."""

    key: str | None = None
    label: str | None = None


class SalesforceSettingsResult(BaseModel):
    """The sync settings with the Warmbly field vocabulary and the defaults.

    Only :meth:`Integrations.get_salesforce_settings` fills ``warmbly_fields``
    and ``defaults``.
    """

    settings: SalesforceSettings | None = None
    warmbly_fields: Sequence[SalesforceFieldDef] = []
    defaults: SalesforceSettings | None = None


class SalesforceCheck(BaseModel):
    """One permission or setup probe."""

    key: str | None = None
    label: str | None = None
    ok: bool | None = None
    detail: str | None = None


class SalesforceOrg(BaseModel):
    """The connected Salesforce org."""

    id: str | None = None
    instance_url: str | None = None
    environment: str | None = None
    login_host: str | None = None
    user_id: str | None = None
    account: str | None = None


class SalesforceApiUsage(BaseModel):
    """The API budget picture."""

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
    """A Salesforce connection's health page."""

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    health_detail: str | None = None
    org: SalesforceOrg | None = None
    api: SalesforceApiUsage | None = None
    counts: SalesforceActivityCounts | None = None
    last_pull_at: str | None = None
    last_pull_error: str | None = None
    settings_enabled: bool | None = None
    checks: Sequence[SalesforceCheck] = []


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
    """What the Salesforce settings screens pick from."""

    lead_fields: Sequence[SalesforceFieldInfo] = []
    contact_fields: Sequence[SalesforceFieldInfo] = []
    lead_statuses: Sequence[SalesforcePickOption] = []
    lead_sources: Sequence[SalesforcePickOption] = []


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


class SalesforcePreviewRow(BaseModel):
    """One sample row of a Salesforce import preview."""

    record_id: str | None = None
    object: str | None = None
    name: str | None = None
    email: str | None = None
    company: str | None = None
    title: str | None = None
    owner_name: str | None = None
    status: str | None = None
    already_linked: bool | None = None


class SalesforcePreview(BaseModel):
    """The first rows of a Salesforce source and how many it holds."""

    total: int | None = None
    sample: Sequence[SalesforcePreviewRow] = []


class SalesforceRunResult(BaseModel):
    """What one Salesforce import run did.

    ``opted_out`` counts people with Email Opt Out set, who are suppressed
    rather than imported.
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
    """A saved list view or Salesforce Campaign that feeds contacts into
    Warmbly.

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
    """The result of removing a Salesforce import source (``204 No Content``)."""

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


class SalesforceRequeued(BaseModel):
    """How many activity rows a retry put back in the queue."""

    requeued: int | None = None


class SalesforceSyncStarted(BaseModel):
    """The acknowledgement of a Salesforce sync-now pass."""

    ok: bool | None = None


class Integrations(SyncAPIResource):
    """Synchronous ``integrations`` resource."""

    def catalog(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[IntegrationCatalogEntry]:
        """List every provider in the catalog. Returned in full, unpaginated."""
        return self._get_api_list(
            "/integrations/catalog",
            model=IntegrationCatalogEntry,
            data_key="catalog",
            options=options,
        )

    def list_connections(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[IntegrationConnection]:
        """List the organization's connections. Returned in full, unpaginated."""
        return self._get_api_list(
            "/integrations/connections",
            model=IntegrationConnection,
            data_key="connections",
            options=options,
        )

    def create_connection(
        self,
        *,
        provider: str,
        label: NotGivenOr[str] = NOT_GIVEN,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationConnection:
        """Connect an API-key or webhook provider.

        OAuth providers go through the browser flow instead.

        Args:
            provider: The catalog provider key to connect.
            label: A human-readable name for the connection.
            config: Provider-specific configuration (credentials, options).
        """
        body = drop_not_given({"provider": provider, "label": label, "config": config})
        return self._post(
            "/integrations/connections",
            cast_to=IntegrationConnection,
            body=body,
            options=options,
        )

    def get_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnectionDetail:
        """Retrieve a connection with its subscriptions and recent runs."""
        return self._get(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnectionDetail,
            options=options,
        )

    def update_connection_config(
        self,
        connection_id: str,
        *,
        config_capabilities: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        sync_direction: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationConnectionDetail:
        """Update a connection's capability snapshot and sync direction.

        Args:
            connection_id: The connection to update.
            config_capabilities: What the integration is configured to do.
            sync_direction: The direction records flow in.
        """
        body = drop_not_given(
            {
                "config_capabilities": config_capabilities,
                "sync_direction": sync_direction,
            }
        )
        return self._patch(
            f"/integrations/connections/{connection_id}/config",
            cast_to=IntegrationConnectionDetail,
            body=body,
            options=options,
        )

    def delete_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnectionDeleted:
        """Disconnect a provider."""
        return self._delete(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnectionDeleted,
            options=options,
        )

    def list_events(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[IntegrationEvent]:
        """List a connection's event subscriptions. Returned in full."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/events",
            model=IntegrationEvent,
            data_key="events",
            options=options,
        )

    def add_event(
        self,
        connection_id: str,
        *,
        event_type: str,
        action: NotGivenOr[str] = NOT_GIVEN,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationEvent:
        """Subscribe a connection to a Warmbly event.

        Args:
            connection_id: The connection to attach the subscription to.
            event_type: The Warmbly event to react to.
            action: What the provider should do when it fires.
            config: Action-specific configuration (channel, board, ...).
            enabled: Whether the subscription is active.
        """
        body = drop_not_given(
            {
                "event_type": event_type,
                "action": action,
                "config": config,
                "enabled": enabled,
            }
        )
        return self._post(
            f"/integrations/connections/{connection_id}/events",
            cast_to=IntegrationEvent,
            body=body,
            options=options,
        )

    def remove_event(
        self,
        connection_id: str,
        event_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> IntegrationEventDeleted:
        """Remove an event subscription from a connection."""
        return self._delete(
            f"/integrations/connections/{connection_id}/events/{event_id}",
            cast_to=IntegrationEventDeleted,
            options=options,
        )

    def get_field_mappings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationFieldMappings:
        """Retrieve a connection's field mappings."""
        return self._get(
            f"/integrations/connections/{connection_id}/field-mappings",
            cast_to=IntegrationFieldMappings,
            options=options,
        )

    def set_field_mappings(
        self,
        connection_id: str,
        *,
        object: str,
        mappings: Sequence[dict[str, Any]],
        options: RequestOptions | None = None,
    ) -> IntegrationFieldMappings:
        """Replace the field mappings for one object on a connection.

        Args:
            connection_id: The connection whose mappings to replace.
            object: The object the mappings apply to (e.g. ``"contact"``).
            mappings: The full set of maps, each
                ``{"warmbly_field", "external_field", "transform",
                "static_value"}``.
        """
        body = {"object": object, "mappings": [dict(m) for m in mappings]}
        return self._put(
            f"/integrations/connections/{connection_id}/field-mappings",
            cast_to=IntegrationFieldMappings,
            body=body,
            options=options,
        )

    def runs(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[IntegrationRun]:
        """List a connection's recent sync runs."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/runs",
            model=IntegrationRun,
            data_key="runs",
            options=options,
        )

    def connection_webhook_secret(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationWebhookSecret:
        """Retrieve (generating on first call) a connection's signing secret."""
        return self._get(
            f"/integrations/connections/{connection_id}/webhook-secret",
            cast_to=IntegrationWebhookSecret,
            options=options,
        )

    def test_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationTestResult:
        """Fire a synthetic event through the connection's automations."""
        return self._post(
            f"/integrations/connections/{connection_id}/test",
            cast_to=IntegrationTestResult,
            options=options,
        )

    def push(
        self,
        connection_id: str,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PushResult:
        """Upsert contacts into a connected CRM, synchronously.

        Every upsert is keyed by email, so repeating a push converges rather
        than duplicating records. A push covers at most 500 contacts, even
        when the selection came from a filter. Needs the ``INTEGRATIONS``
        permission.

        Args:
            connection_id: The connection to push to.
            contact_ids: The contacts to upsert.
            select_all: Select by *filters* instead of *contact_ids*.
            filters: The contact search filter body (the one
                ``contacts.search`` takes).
            exclude: Contact ids to drop from a ``select_all`` selection.
        """
        return self._post(
            f"/integrations/connections/{connection_id}/push",
            cast_to=PushResult,
            body=drop_not_given(
                {
                    "contact_ids": contact_ids,
                    "all": select_all,
                    "filters": filters,
                    "exclude": exclude,
                }
            ),
            options=options,
        )

    def bookings(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[IntegrationBooking]:
        """List recently booked meetings from scheduling integrations.

        Capped at the 50 most recent. Use ``client.meetings.list()`` for the
        full, filterable meetings list. Needs the ``READ_CONTACTS``
        permission.
        """
        return self._get_api_list(
            "/integrations/bookings",
            model=IntegrationBooking,
            data_key="bookings",
            options=options,
        )

    # -- inbound scheduling connections (Calendly, Cal.com) ------------------
    def set_connection_signing_key(
        self,
        connection_id: str,
        *,
        signing_key: str,
        options: RequestOptions | None = None,
    ) -> IntegrationConnectionDetail:
        """Set the key a Calendly or Cal.com connection's deliveries must be
        signed with.

        With a key set, the inbound URL secret alone is no longer enough. An
        empty key goes back to the URL secret alone. Needs the ``INTEGRATIONS``
        permission.

        Args:
            connection_id: The Calendly or Cal.com connection.
            signing_key: The provider's webhook signing key.
        """
        return self._put(
            f"/integrations/connections/{connection_id}/signing-key",
            cast_to=IntegrationConnectionDetail,
            body={"signing_key": signing_key},
            options=options,
        )

    def rotate_inbound_url(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationInboundUrl:
        """Mint a new inbound webhook URL for a Calendly or Cal.com connection.

        The previous URL stops working immediately, so update the provider's
        webhook first or right after. Needs the ``INTEGRATIONS`` permission.
        """
        return self._post(
            f"/integrations/connections/{connection_id}/rotate-inbound-url",
            cast_to=IntegrationInboundUrl,
            options=options,
        )

    # -- community directory -------------------------------------------------
    def community_apps(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CommunityApp]:
        """Browse community apps shown in discovery, featured first and then
        most installed.

        Args:
            limit: Page size, 1 to 200 (default 100).
        """
        return self._get_api_list(
            "/integrations/community",
            model=CommunityApp,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def community_app(
        self, slug: str, *, options: RequestOptions | None = None
    ) -> CommunityApp:
        """Open a published community app by its link, listed or not."""
        return self._get(
            f"/integrations/community/{slug}", cast_to=CommunityApp, options=options
        )

    # -- Apollo --------------------------------------------------------------
    def apollo_overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Retrieve an Apollo connection's account and import totals."""
        return self._get(
            f"/integrations/apollo/{connection_id}",
            cast_to=ApolloOverview,
            options=options,
        )

    def apollo_replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        Repeating the call converges on the same key. Needs the
        ``INTEGRATIONS`` permission.
        """
        return self._put(
            f"/integrations/apollo/{connection_id}/key",
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def apollo_lists(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ApolloList]:
        """List the account's saved Apollo contact lists."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/lists",
            model=ApolloList,
            options=options,
        )

    def apollo_preview_import(
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
            list_id: The Apollo list id.
            verified_only: Only count people with a verified address (the
                server default is ``True``).
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import/preview",
            cast_to=ApolloPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def apollo_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ApolloImportSource]:
        """List a connection's saved Apollo list imports."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/import-sources",
            model=ApolloImportSource,
            options=options,
        )

    def apollo_create_import_source(
        self,
        connection_id: str,
        *,
        list_id: str,
        list_name: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Save an Apollo list import and start its first run.

        People are deduplicated by address, so a retried create is harmless.
        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list id (at most 64 characters).
            list_name: The list's display name.
            name: A name for the import; defaults to the list name.
            campaign_id: A campaign to enrol imported people into.
            category_ids: Categories to apply (at most 50).
            verified_only: Import only verified addresses (default ``True``).
            recurring: Keep the import in sync on a schedule.
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import-sources",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "list_id": list_id,
                    "list_name": list_name,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "verified_only": verified_only,
                    "recurring": recurring,
                }
            ),
            options=options,
        )

    def apollo_update_import_source(
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
        """Edit an Apollo import's targets, filter and schedule.

        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Apollo connection.
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A campaign to enrol into, or ``None`` to detach the
                current one.
            category_ids: Replace the categories to apply (at most 50).
            verified_only: Import only verified addresses.
            recurring: Keep the import in sync on a schedule.
            enabled: Switch the import on or off.
        """
        return self._patch(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "verified_only": verified_only,
                    "recurring": recurring,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    def apollo_run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Run an Apollo import now.

        The run continues in the background and the returned source has
        ``status`` of ``"running"``. A second request while one runs is
        refused with a conflict. Needs the ``INTEGRATIONS`` permission.
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}/run",
            cast_to=ApolloImportSource,
            options=options,
        )

    def apollo_delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSourceDeleted:
        """Remove an Apollo import. Contacts it brought in stay.

        Needs the ``INTEGRATIONS`` permission.
        """
        return self._delete(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSourceDeleted,
            options=options,
        )

    def apollo_enrichments(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApolloEnrichmentRun]:
        """List a connection's recent Apollo enrichment runs.

        Args:
            connection_id: The Apollo connection.
            limit: How many runs to return, 1 to 100 (default 20).
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/enrichments",
            model=ApolloEnrichmentRun,
            query={"limit": limit},
            options=options,
        )

    def apollo_start_enrichment(
        self,
        connection_id: str,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        overwrite: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Queue an Apollo enrichment run over a contact selection.

        Enrichment writes contacts and spends the customer's Apollo credits,
        so it needs both the ``INTEGRATIONS`` and ``BULK_CONTACTS``
        permissions. Answers ``202 Accepted``; poll
        :meth:`apollo_enrichment` for progress. At most 5,000 contacts per
        run.

        Args:
            connection_id: The Apollo connection.
            contact_ids: Explicit contact ids.
            select_all: Select by *filters* instead of *contact_ids*.
            filters: The contact search filter body.
            exclude: Contact ids to drop from a ``select_all`` selection.
            overwrite: Replace values contacts already have.
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/enrichments",
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contact_ids": contact_ids,
                    "all": select_all,
                    "filters": filters,
                    "exclude": exclude,
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )

    def apollo_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Retrieve one Apollo enrichment run's progress."""
        return self._get(
            f"/integrations/apollo/{connection_id}/enrichments/{run_id}",
            cast_to=ApolloEnrichmentRun,
            options=options,
        )

    # -- Clay ----------------------------------------------------------------
    def clay_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ClaySettings:
        """Retrieve everything the Clay page shows for a connection."""
        return self._get(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            options=options,
        )

    def clay_update_settings(
        self,
        connection_id: str,
        *,
        defaults: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        auth_token: NotGivenOr[str] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ClaySettings:
        """Save a Clay connection's inbound defaults, outbound table and events.

        Every given field replaces its value, so a retry converges; an omitted
        field is left alone. Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Clay connection.
            defaults: Where inbound rows land (``campaign_id``,
                ``category_ids``, ``segment_ids``, ``dedup``, ``subscribed``).
            webhook_url: The Clay table's webhook URL; an empty string clears
                it.
            auth_token: The table's auth token; an empty string clears it.
            events: The Warmbly events to send to the table (see
                ``available_events``).
        """
        return self._patch(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            body=drop_not_given(
                {
                    "defaults": defaults,
                    "webhook_url": webhook_url,
                    "auth_token": auth_token,
                    "events": events,
                }
            ),
            options=options,
        )

    # -- Salesforce ----------------------------------------------------------
    def salesforce_overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve a Salesforce connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe permissions and setup (slower).
        """
        return self._get(
            f"/integrations/salesforce/{connection_id}/overview",
            cast_to=SalesforceOverview,
            query={"checks": "1"} if checks else None,
            options=options,
        )

    def get_salesforce_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettingsResult:
        """Retrieve the sync settings, the Warmbly field vocabulary and the
        defaults."""
        return self._get(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsResult,
            options=options,
        )

    def set_salesforce_settings(
        self,
        connection_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsResult:
        """Validate and save the whole sync settings document.

        The document replaces the stored one, so repeating the call converges.
        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings (see :class:`SalesforceSettings`).
        """
        return self._put(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsResult,
            body=dict(settings),
            options=options,
        )

    def salesforce_metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Retrieve the Lead and Contact fields and picklists."""
        return self._get(
            f"/integrations/salesforce/{connection_id}/metadata",
            cast_to=SalesforceMetadata,
            options=options,
        )

    def salesforce_users(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceUser]:
        """Search active Salesforce users.

        Args:
            connection_id: The Salesforce connection.
            q: Match against name or email.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/users",
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def salesforce_list_views(
        self,
        connection_id: str,
        *,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceListView]:
        """List Lead or Contact list views.

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

    def salesforce_campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceCampaign]:
        """Search Salesforce Campaigns.

        Args:
            connection_id: The Salesforce connection.
            q: Match against the campaign name.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/campaigns",
            model=SalesforceCampaign,
            query={"q": q},
            options=options,
        )

    def salesforce_preview_import(
        self,
        connection_id: str,
        *,
        source_kind: str,
        source_id: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforcePreview:
        """Read the first rows of a list view or Campaign without importing.

        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The Salesforce id of the list view or Campaign.
            object: ``"Lead"`` or ``"Contact"`` for a list view; ignored for a
                Campaign.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import/preview",
            cast_to=SalesforcePreview,
            body=drop_not_given(
                {"source_kind": source_kind, "object": object, "source_id": source_id}
            ),
            options=options,
        )

    def salesforce_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[SalesforceImportSource]:
        """List a connection's saved Salesforce imports."""
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/import-sources",
            model=SalesforceImportSource,
            options=options,
        )

    def salesforce_create_import_source(
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
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save a Salesforce import and start its first run.

        People are deduplicated by address, so a retried create is harmless.
        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The Salesforce id of the list view or Campaign.
            object: ``"Lead"`` or ``"Contact"`` for a list view.
            source_label: The source's display name.
            name: A name for the import; defaults to the label.
            campaign_id: A Warmbly campaign to enrol imported people into.
            category_ids: Categories to apply (at most 50).
            recurring: Keep the import in sync on a schedule.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import-sources",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "source_kind": source_kind,
                    "object": object,
                    "source_id": source_id,
                    "source_label": source_label,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "recurring": recurring,
                }
            ),
            options=options,
        )

    def salesforce_update_import_source(
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
        """Edit a Salesforce import's targets and schedule.

        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A Warmbly campaign to enrol into, or ``None`` to
                detach the current one.
            category_ids: Replace the categories to apply (at most 50).
            recurring: Keep the import in sync on a schedule.
            enabled: Switch the import on or off.
        """
        return self._patch(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "recurring": recurring,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    def salesforce_run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Run a Salesforce import now.

        The run continues in the background and the returned source has
        ``status`` of ``"running"``. A second request while one runs is
        refused with a conflict. Needs the ``INTEGRATIONS`` permission.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}/run",
            cast_to=SalesforceImportSource,
            options=options,
        )

    def salesforce_delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSourceDeleted:
        """Remove a Salesforce import. Contacts it brought in stay.

        Needs the ``INTEGRATIONS`` permission.
        """
        return self._delete(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSourceDeleted,
            options=options,
        )

    def salesforce_activity(
        self,
        connection_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[SalesforceActivity]:
        """List the Salesforce activity log, newest first (auto-paginating).

        Args:
            connection_id: The Salesforce connection.
            status: ``"pending"``, ``"synced"``, ``"skipped"`` or
                ``"failed"``.
            contact_id: Restrict to one contact.
            limit: Page size, 1 to 200 (default 50).
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

    def salesforce_retry_activity(
        self,
        connection_id: str,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SalesforceRequeued:
        """Requeue failed or skipped activity rows.

        Requeueing a row that is already pending changes nothing. Needs the
        ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            ids: The activity ids to requeue (at most 500).
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/activity/retry",
            cast_to=SalesforceRequeued,
            body={"ids": list(ids)},
            options=options,
        )

    def salesforce_sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending Salesforce activity and pull changes at once.

        Both passes are idempotent. Needs the ``INTEGRATIONS`` permission.
        """
        return self._post(
            f"/integrations/salesforce/{connection_id}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )


class AsyncIntegrations(AsyncAPIResource):
    """Asynchronous ``integrations`` resource."""

    def catalog(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[IntegrationCatalogEntry]:
        """List every provider in the catalog. Returned in full, unpaginated."""
        return self._get_api_list(
            "/integrations/catalog",
            model=IntegrationCatalogEntry,
            data_key="catalog",
            options=options,
        )

    def list_connections(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[IntegrationConnection]:
        """List the organization's connections. Returned in full, unpaginated."""
        return self._get_api_list(
            "/integrations/connections",
            model=IntegrationConnection,
            data_key="connections",
            options=options,
        )

    async def create_connection(
        self,
        *,
        provider: str,
        label: NotGivenOr[str] = NOT_GIVEN,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationConnection:
        """Connect an API-key or webhook provider.

        OAuth providers go through the browser flow instead.

        Args:
            provider: The catalog provider key to connect.
            label: A human-readable name for the connection.
            config: Provider-specific configuration (credentials, options).
        """
        body = drop_not_given({"provider": provider, "label": label, "config": config})
        return await self._post(
            "/integrations/connections",
            cast_to=IntegrationConnection,
            body=body,
            options=options,
        )

    async def get_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnectionDetail:
        """Retrieve a connection with its subscriptions and recent runs."""
        return await self._get(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnectionDetail,
            options=options,
        )

    async def update_connection_config(
        self,
        connection_id: str,
        *,
        config_capabilities: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        sync_direction: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationConnectionDetail:
        """Update a connection's capability snapshot and sync direction.

        Args:
            connection_id: The connection to update.
            config_capabilities: What the integration is configured to do.
            sync_direction: The direction records flow in.
        """
        body = drop_not_given(
            {
                "config_capabilities": config_capabilities,
                "sync_direction": sync_direction,
            }
        )
        return await self._patch(
            f"/integrations/connections/{connection_id}/config",
            cast_to=IntegrationConnectionDetail,
            body=body,
            options=options,
        )

    async def delete_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnectionDeleted:
        """Disconnect a provider."""
        return await self._delete(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnectionDeleted,
            options=options,
        )

    def list_events(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[IntegrationEvent]:
        """List a connection's event subscriptions. Returned in full."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/events",
            model=IntegrationEvent,
            data_key="events",
            options=options,
        )

    async def add_event(
        self,
        connection_id: str,
        *,
        event_type: str,
        action: NotGivenOr[str] = NOT_GIVEN,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationEvent:
        """Subscribe a connection to a Warmbly event.

        Args:
            connection_id: The connection to attach the subscription to.
            event_type: The Warmbly event to react to.
            action: What the provider should do when it fires.
            config: Action-specific configuration (channel, board, ...).
            enabled: Whether the subscription is active.
        """
        body = drop_not_given(
            {
                "event_type": event_type,
                "action": action,
                "config": config,
                "enabled": enabled,
            }
        )
        return await self._post(
            f"/integrations/connections/{connection_id}/events",
            cast_to=IntegrationEvent,
            body=body,
            options=options,
        )

    async def remove_event(
        self,
        connection_id: str,
        event_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> IntegrationEventDeleted:
        """Remove an event subscription from a connection."""
        return await self._delete(
            f"/integrations/connections/{connection_id}/events/{event_id}",
            cast_to=IntegrationEventDeleted,
            options=options,
        )

    async def get_field_mappings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationFieldMappings:
        """Retrieve a connection's field mappings."""
        return await self._get(
            f"/integrations/connections/{connection_id}/field-mappings",
            cast_to=IntegrationFieldMappings,
            options=options,
        )

    async def set_field_mappings(
        self,
        connection_id: str,
        *,
        object: str,
        mappings: Sequence[dict[str, Any]],
        options: RequestOptions | None = None,
    ) -> IntegrationFieldMappings:
        """Replace the field mappings for one object on a connection.

        Args:
            connection_id: The connection whose mappings to replace.
            object: The object the mappings apply to (e.g. ``"contact"``).
            mappings: The full set of maps, each
                ``{"warmbly_field", "external_field", "transform",
                "static_value"}``.
        """
        body = {"object": object, "mappings": [dict(m) for m in mappings]}
        return await self._put(
            f"/integrations/connections/{connection_id}/field-mappings",
            cast_to=IntegrationFieldMappings,
            body=body,
            options=options,
        )

    def runs(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[IntegrationRun]:
        """List a connection's recent sync runs."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/runs",
            model=IntegrationRun,
            data_key="runs",
            options=options,
        )

    async def connection_webhook_secret(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationWebhookSecret:
        """Retrieve (generating on first call) a connection's signing secret."""
        return await self._get(
            f"/integrations/connections/{connection_id}/webhook-secret",
            cast_to=IntegrationWebhookSecret,
            options=options,
        )

    async def test_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationTestResult:
        """Fire a synthetic event through the connection's automations."""
        return await self._post(
            f"/integrations/connections/{connection_id}/test",
            cast_to=IntegrationTestResult,
            options=options,
        )

    async def push(
        self,
        connection_id: str,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PushResult:
        """Upsert contacts into a connected CRM, synchronously.

        Every upsert is keyed by email, so repeating a push converges rather
        than duplicating records. A push covers at most 500 contacts, even
        when the selection came from a filter. Needs the ``INTEGRATIONS``
        permission.

        Args:
            connection_id: The connection to push to.
            contact_ids: The contacts to upsert.
            select_all: Select by *filters* instead of *contact_ids*.
            filters: The contact search filter body (the one
                ``contacts.search`` takes).
            exclude: Contact ids to drop from a ``select_all`` selection.
        """
        return await self._post(
            f"/integrations/connections/{connection_id}/push",
            cast_to=PushResult,
            body=drop_not_given(
                {
                    "contact_ids": contact_ids,
                    "all": select_all,
                    "filters": filters,
                    "exclude": exclude,
                }
            ),
            options=options,
        )

    def bookings(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[IntegrationBooking]:
        """List recently booked meetings from scheduling integrations.

        Capped at the 50 most recent. Use ``client.meetings.list()`` for the
        full, filterable meetings list. Needs the ``READ_CONTACTS``
        permission.
        """
        return self._get_api_list(
            "/integrations/bookings",
            model=IntegrationBooking,
            data_key="bookings",
            options=options,
        )

    # -- inbound scheduling connections (Calendly, Cal.com) ------------------
    async def set_connection_signing_key(
        self,
        connection_id: str,
        *,
        signing_key: str,
        options: RequestOptions | None = None,
    ) -> IntegrationConnectionDetail:
        """Set the key a Calendly or Cal.com connection's deliveries must be
        signed with.

        With a key set, the inbound URL secret alone is no longer enough. An
        empty key goes back to the URL secret alone. Needs the ``INTEGRATIONS``
        permission.

        Args:
            connection_id: The Calendly or Cal.com connection.
            signing_key: The provider's webhook signing key.
        """
        return await self._put(
            f"/integrations/connections/{connection_id}/signing-key",
            cast_to=IntegrationConnectionDetail,
            body={"signing_key": signing_key},
            options=options,
        )

    async def rotate_inbound_url(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationInboundUrl:
        """Mint a new inbound webhook URL for a Calendly or Cal.com connection.

        The previous URL stops working immediately, so update the provider's
        webhook first or right after. Needs the ``INTEGRATIONS`` permission.
        """
        return await self._post(
            f"/integrations/connections/{connection_id}/rotate-inbound-url",
            cast_to=IntegrationInboundUrl,
            options=options,
        )

    # -- community directory -------------------------------------------------
    def community_apps(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[CommunityApp]:
        """Browse community apps shown in discovery, featured first and then
        most installed.

        Args:
            limit: Page size, 1 to 200 (default 100).
        """
        return self._get_api_list(
            "/integrations/community",
            model=CommunityApp,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def community_app(
        self, slug: str, *, options: RequestOptions | None = None
    ) -> CommunityApp:
        """Open a published community app by its link, listed or not."""
        return await self._get(
            f"/integrations/community/{slug}", cast_to=CommunityApp, options=options
        )

    # -- Apollo --------------------------------------------------------------
    async def apollo_overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Retrieve an Apollo connection's account and import totals."""
        return await self._get(
            f"/integrations/apollo/{connection_id}",
            cast_to=ApolloOverview,
            options=options,
        )

    async def apollo_replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        Repeating the call converges on the same key. Needs the
        ``INTEGRATIONS`` permission.
        """
        return await self._put(
            f"/integrations/apollo/{connection_id}/key",
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def apollo_lists(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ApolloList]:
        """List the account's saved Apollo contact lists."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/lists",
            model=ApolloList,
            options=options,
        )

    async def apollo_preview_import(
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
            list_id: The Apollo list id.
            verified_only: Only count people with a verified address (the
                server default is ``True``).
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import/preview",
            cast_to=ApolloPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def apollo_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ApolloImportSource]:
        """List a connection's saved Apollo list imports."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/import-sources",
            model=ApolloImportSource,
            options=options,
        )

    async def apollo_create_import_source(
        self,
        connection_id: str,
        *,
        list_id: str,
        list_name: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Save an Apollo list import and start its first run.

        People are deduplicated by address, so a retried create is harmless.
        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list id (at most 64 characters).
            list_name: The list's display name.
            name: A name for the import; defaults to the list name.
            campaign_id: A campaign to enrol imported people into.
            category_ids: Categories to apply (at most 50).
            verified_only: Import only verified addresses (default ``True``).
            recurring: Keep the import in sync on a schedule.
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import-sources",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "list_id": list_id,
                    "list_name": list_name,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "verified_only": verified_only,
                    "recurring": recurring,
                }
            ),
            options=options,
        )

    async def apollo_update_import_source(
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
        """Edit an Apollo import's targets, filter and schedule.

        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Apollo connection.
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A campaign to enrol into, or ``None`` to detach the
                current one.
            category_ids: Replace the categories to apply (at most 50).
            verified_only: Import only verified addresses.
            recurring: Keep the import in sync on a schedule.
            enabled: Switch the import on or off.
        """
        return await self._patch(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "verified_only": verified_only,
                    "recurring": recurring,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    async def apollo_run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Run an Apollo import now.

        The run continues in the background and the returned source has
        ``status`` of ``"running"``. A second request while one runs is
        refused with a conflict. Needs the ``INTEGRATIONS`` permission.
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}/run",
            cast_to=ApolloImportSource,
            options=options,
        )

    async def apollo_delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSourceDeleted:
        """Remove an Apollo import. Contacts it brought in stay.

        Needs the ``INTEGRATIONS`` permission.
        """
        return await self._delete(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSourceDeleted,
            options=options,
        )

    def apollo_enrichments(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApolloEnrichmentRun]:
        """List a connection's recent Apollo enrichment runs.

        Args:
            connection_id: The Apollo connection.
            limit: How many runs to return, 1 to 100 (default 20).
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/enrichments",
            model=ApolloEnrichmentRun,
            query={"limit": limit},
            options=options,
        )

    async def apollo_start_enrichment(
        self,
        connection_id: str,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        overwrite: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Queue an Apollo enrichment run over a contact selection.

        Enrichment writes contacts and spends the customer's Apollo credits,
        so it needs both the ``INTEGRATIONS`` and ``BULK_CONTACTS``
        permissions. Answers ``202 Accepted``; poll
        :meth:`apollo_enrichment` for progress. At most 5,000 contacts per
        run.

        Args:
            connection_id: The Apollo connection.
            contact_ids: Explicit contact ids.
            select_all: Select by *filters* instead of *contact_ids*.
            filters: The contact search filter body.
            exclude: Contact ids to drop from a ``select_all`` selection.
            overwrite: Replace values contacts already have.
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/enrichments",
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contact_ids": contact_ids,
                    "all": select_all,
                    "filters": filters,
                    "exclude": exclude,
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )

    async def apollo_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Retrieve one Apollo enrichment run's progress."""
        return await self._get(
            f"/integrations/apollo/{connection_id}/enrichments/{run_id}",
            cast_to=ApolloEnrichmentRun,
            options=options,
        )

    # -- Clay ----------------------------------------------------------------
    async def clay_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ClaySettings:
        """Retrieve everything the Clay page shows for a connection."""
        return await self._get(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            options=options,
        )

    async def clay_update_settings(
        self,
        connection_id: str,
        *,
        defaults: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        auth_token: NotGivenOr[str] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ClaySettings:
        """Save a Clay connection's inbound defaults, outbound table and events.

        Every given field replaces its value, so a retry converges; an omitted
        field is left alone. Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Clay connection.
            defaults: Where inbound rows land (``campaign_id``,
                ``category_ids``, ``segment_ids``, ``dedup``, ``subscribed``).
            webhook_url: The Clay table's webhook URL; an empty string clears
                it.
            auth_token: The table's auth token; an empty string clears it.
            events: The Warmbly events to send to the table (see
                ``available_events``).
        """
        return await self._patch(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            body=drop_not_given(
                {
                    "defaults": defaults,
                    "webhook_url": webhook_url,
                    "auth_token": auth_token,
                    "events": events,
                }
            ),
            options=options,
        )

    # -- Salesforce ----------------------------------------------------------
    async def salesforce_overview(
        self,
        connection_id: str,
        *,
        checks: bool = False,
        options: RequestOptions | None = None,
    ) -> SalesforceOverview:
        """Retrieve a Salesforce connection's health page.

        Args:
            connection_id: The Salesforce connection.
            checks: Also probe permissions and setup (slower).
        """
        return await self._get(
            f"/integrations/salesforce/{connection_id}/overview",
            cast_to=SalesforceOverview,
            query={"checks": "1"} if checks else None,
            options=options,
        )

    async def get_salesforce_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSettingsResult:
        """Retrieve the sync settings, the Warmbly field vocabulary and the
        defaults."""
        return await self._get(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsResult,
            options=options,
        )

    async def set_salesforce_settings(
        self,
        connection_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> SalesforceSettingsResult:
        """Validate and save the whole sync settings document.

        The document replaces the stored one, so repeating the call converges.
        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            settings: The full settings (see :class:`SalesforceSettings`).
        """
        return await self._put(
            f"/integrations/salesforce/{connection_id}/settings",
            cast_to=SalesforceSettingsResult,
            body=dict(settings),
            options=options,
        )

    async def salesforce_metadata(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceMetadata:
        """Retrieve the Lead and Contact fields and picklists."""
        return await self._get(
            f"/integrations/salesforce/{connection_id}/metadata",
            cast_to=SalesforceMetadata,
            options=options,
        )

    def salesforce_users(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceUser]:
        """Search active Salesforce users.

        Args:
            connection_id: The Salesforce connection.
            q: Match against name or email.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/users",
            model=SalesforceUser,
            query={"q": q},
            options=options,
        )

    def salesforce_list_views(
        self,
        connection_id: str,
        *,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceListView]:
        """List Lead or Contact list views.

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

    def salesforce_campaigns(
        self,
        connection_id: str,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceCampaign]:
        """Search Salesforce Campaigns.

        Args:
            connection_id: The Salesforce connection.
            q: Match against the campaign name.
        """
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/campaigns",
            model=SalesforceCampaign,
            query={"q": q},
            options=options,
        )

    async def salesforce_preview_import(
        self,
        connection_id: str,
        *,
        source_kind: str,
        source_id: str,
        object: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SalesforcePreview:
        """Read the first rows of a list view or Campaign without importing.

        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The Salesforce id of the list view or Campaign.
            object: ``"Lead"`` or ``"Contact"`` for a list view; ignored for a
                Campaign.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import/preview",
            cast_to=SalesforcePreview,
            body=drop_not_given(
                {"source_kind": source_kind, "object": object, "source_id": source_id}
            ),
            options=options,
        )

    def salesforce_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[SalesforceImportSource]:
        """List a connection's saved Salesforce imports."""
        return self._get_api_list(
            f"/integrations/salesforce/{connection_id}/import-sources",
            model=SalesforceImportSource,
            options=options,
        )

    async def salesforce_create_import_source(
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
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Save a Salesforce import and start its first run.

        People are deduplicated by address, so a retried create is harmless.
        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            source_kind: ``"list_view"`` or ``"campaign"``.
            source_id: The Salesforce id of the list view or Campaign.
            object: ``"Lead"`` or ``"Contact"`` for a list view.
            source_label: The source's display name.
            name: A name for the import; defaults to the label.
            campaign_id: A Warmbly campaign to enrol imported people into.
            category_ids: Categories to apply (at most 50).
            recurring: Keep the import in sync on a schedule.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import-sources",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "source_kind": source_kind,
                    "object": object,
                    "source_id": source_id,
                    "source_label": source_label,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "recurring": recurring,
                }
            ),
            options=options,
        )

    async def salesforce_update_import_source(
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
        """Edit a Salesforce import's targets and schedule.

        Needs the ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            source_id: The import source to edit.
            name: A new name.
            campaign_id: A Warmbly campaign to enrol into, or ``None`` to
                detach the current one.
            category_ids: Replace the categories to apply (at most 50).
            recurring: Keep the import in sync on a schedule.
            enabled: Switch the import on or off.
        """
        return await self._patch(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSource,
            body=drop_not_given(
                {
                    "name": name,
                    "campaign_id": campaign_id,
                    "category_ids": category_ids,
                    "recurring": recurring,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    async def salesforce_run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSource:
        """Run a Salesforce import now.

        The run continues in the background and the returned source has
        ``status`` of ``"running"``. A second request while one runs is
        refused with a conflict. Needs the ``INTEGRATIONS`` permission.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}/run",
            cast_to=SalesforceImportSource,
            options=options,
        )

    async def salesforce_delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceImportSourceDeleted:
        """Remove a Salesforce import. Contacts it brought in stay.

        Needs the ``INTEGRATIONS`` permission.
        """
        return await self._delete(
            f"/integrations/salesforce/{connection_id}/import-sources/{source_id}",
            cast_to=SalesforceImportSourceDeleted,
            options=options,
        )

    def salesforce_activity(
        self,
        connection_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[SalesforceActivity]:
        """List the Salesforce activity log, newest first (auto-paginating).

        Args:
            connection_id: The Salesforce connection.
            status: ``"pending"``, ``"synced"``, ``"skipped"`` or
                ``"failed"``.
            contact_id: Restrict to one contact.
            limit: Page size, 1 to 200 (default 50).
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

    async def salesforce_retry_activity(
        self,
        connection_id: str,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> SalesforceRequeued:
        """Requeue failed or skipped activity rows.

        Requeueing a row that is already pending changes nothing. Needs the
        ``INTEGRATIONS`` permission.

        Args:
            connection_id: The Salesforce connection.
            ids: The activity ids to requeue (at most 500).
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/activity/retry",
            cast_to=SalesforceRequeued,
            body={"ids": list(ids)},
            options=options,
        )

    async def salesforce_sync_now(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SalesforceSyncStarted:
        """Drain pending Salesforce activity and pull changes at once.

        Both passes are idempotent. Needs the ``INTEGRATIONS`` permission.
        """
        return await self._post(
            f"/integrations/salesforce/{connection_id}/sync-now",
            cast_to=SalesforceSyncStarted,
            options=options,
        )
