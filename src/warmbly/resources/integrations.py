"""The ``integrations`` resource: third-party connections.

Maps to the ``/v1/integrations`` route group. Covers the catalog of available
providers, the connections an organization has configured, their event
subscriptions, field mappings, sync runs, webhook signing secrets, connection
testing, contact pushes, and recently booked meetings.

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
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given

__all__ = [
    "AsyncIntegrations",
    "CommunityApp",
    "CommunityAppPermission",
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
]


class CommunityAppPermission(BaseModel):
    """One API permission an app asks for, spelled out."""

    name: str | None = None
    value: int | None = None
    description: str | None = None
    category: str | None = None


class CommunityApp(BaseModel):
    """A community directory listing as this workspace sees it.

    ``status`` is ``published`` or ``featured``. ``listed`` means it shows in
    discovery; an unlisted published app is only reachable by its ``slug``.
    ``installed`` reports whether this workspace already uses it, and
    ``scopes`` is the bitmask that ``permissions`` spells out. No credential or
    redirect field is ever included.
    """

    application_id: str
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
    permissions: Sequence[CommunityAppPermission] = []
    status: str | None = None
    listed: bool | None = None
    installs: int | None = None
    installed: bool | None = None
    published_at: str | None = None


class IntegrationCatalogEntry(BaseModel):
    """A provider available to connect from the integrations catalog.

    ``configured`` reports whether this deployment has the credentials needed
    to offer the provider at all.
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


class IntegrationConnection(BaseModel):
    """A configured connection to a third-party provider.

    An automation connection's outbound HMAC signing secret is never part of
    ``config_capabilities`` here; read it with
    :meth:`Integrations.connection_webhook_secret`.
    """

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


class IntegrationInboundUrl(BaseModel):
    """The freshly minted inbound webhook URL of a Calendly or Cal.com connection.

    The previous URL stops working immediately.
    """

    inbound_webhook_url: str | None = None


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

    def community(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CommunityApp]:
        """List the community apps shown in discovery, featured first.

        Needs read access to integrations.

        Args:
            limit: Page size, 1 to 200 (default 100).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/integrations/community",
            model=CommunityApp,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    def get_community_app(
        self, slug: str, *, options: RequestOptions | None = None
    ) -> CommunityApp:
        """Open a published community app by its link slug, listed or not.

        Needs read access to integrations.
        """
        return self._get(
            f"/integrations/community/{slug}",
            cast_to=CommunityApp,
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

    def set_connection_signing_key(
        self,
        connection_id: str,
        *,
        signing_key: str,
        options: RequestOptions | None = None,
    ) -> IntegrationConnectionDetail:
        """Set the key a Calendly or Cal.com connection's deliveries are signed with.

        Once a key is set, an inbound delivery must carry a valid signature as
        well as the secret in the URL. Passing an empty string clears the key and
        goes back to the URL secret alone. Only Calendly and Cal.com connections
        take one (``400`` otherwise), and the key must be 8 to 512 characters.
        Only ``connection`` is populated in the result. Requires the
        ``integrations`` scope.

        Args:
            connection_id: The connection to configure.
            signing_key: The provider's webhook signing key.
        """
        return self._put(
            f"/integrations/connections/{connection_id}/signing-key",
            cast_to=IntegrationConnectionDetail,
            body={"signing_key": signing_key},
            options=options,
        )

    def rotate_connection_inbound_url(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationInboundUrl:
        """Mint a new inbound webhook URL for a Calendly or Cal.com connection.

        The previous URL stops working immediately, so update the provider's
        webhook settings right after. Only Calendly and Cal.com connections have
        one (``400`` otherwise). Requires the ``integrations`` scope.
        """
        return self._post(
            f"/integrations/connections/{connection_id}/rotate-inbound-url",
            cast_to=IntegrationInboundUrl,
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
        than duplicating records.

        Args:
            connection_id: The connection to push to.
            contact_ids: The contacts to upsert.
            select_all: Push every contact matching *filters* instead of the
                listed ids (the dashboard's "select all matching").
            filters: The same body ``client.contacts.search`` takes. Used with
                *select_all*.
            exclude: Contact ids to drop from a *select_all* selection.

        A push is synchronous against the provider's API, so one request is
        capped at 500 contacts even when the selection came from a filter.
        """
        if not is_given(contact_ids) and select_all is not True:
            raise ValueError("push() requires contact_ids or select_all=True")
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
        full, filterable meetings list. Requires ``read_contacts``.
        """
        return self._get_api_list(
            "/integrations/bookings",
            model=IntegrationBooking,
            data_key="bookings",
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

    def community(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[CommunityApp]:
        """List the community apps shown in discovery, featured first.

        Needs read access to integrations.

        Args:
            limit: Page size, 1 to 200 (default 100).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/integrations/community",
            model=CommunityApp,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    async def get_community_app(
        self, slug: str, *, options: RequestOptions | None = None
    ) -> CommunityApp:
        """Open a published community app by its link slug, listed or not.

        Needs read access to integrations.
        """
        return await self._get(
            f"/integrations/community/{slug}",
            cast_to=CommunityApp,
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

    async def set_connection_signing_key(
        self,
        connection_id: str,
        *,
        signing_key: str,
        options: RequestOptions | None = None,
    ) -> IntegrationConnectionDetail:
        """Set the key a Calendly or Cal.com connection's deliveries are signed with.

        Once a key is set, an inbound delivery must carry a valid signature as
        well as the secret in the URL. Passing an empty string clears the key and
        goes back to the URL secret alone. Only Calendly and Cal.com connections
        take one (``400`` otherwise), and the key must be 8 to 512 characters.
        Only ``connection`` is populated in the result. Requires the
        ``integrations`` scope.

        Args:
            connection_id: The connection to configure.
            signing_key: The provider's webhook signing key.
        """
        return await self._put(
            f"/integrations/connections/{connection_id}/signing-key",
            cast_to=IntegrationConnectionDetail,
            body={"signing_key": signing_key},
            options=options,
        )

    async def rotate_connection_inbound_url(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationInboundUrl:
        """Mint a new inbound webhook URL for a Calendly or Cal.com connection.

        The previous URL stops working immediately, so update the provider's
        webhook settings right after. Only Calendly and Cal.com connections have
        one (``400`` otherwise). Requires the ``integrations`` scope.
        """
        return await self._post(
            f"/integrations/connections/{connection_id}/rotate-inbound-url",
            cast_to=IntegrationInboundUrl,
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
        than duplicating records.

        Args:
            connection_id: The connection to push to.
            contact_ids: The contacts to upsert.
            select_all: Push every contact matching *filters* instead of the
                listed ids (the dashboard's "select all matching").
            filters: The same body ``client.contacts.search`` takes. Used with
                *select_all*.
            exclude: Contact ids to drop from a *select_all* selection.

        A push is synchronous against the provider's API, so one request is
        capped at 500 contacts even when the selection came from a filter.
        """
        if not is_given(contact_ids) and select_all is not True:
            raise ValueError("push() requires contact_ids or select_all=True")
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
        full, filterable meetings list. Requires ``read_contacts``.
        """
        return self._get_api_list(
            "/integrations/bookings",
            model=IntegrationBooking,
            data_key="bookings",
            options=options,
        )
