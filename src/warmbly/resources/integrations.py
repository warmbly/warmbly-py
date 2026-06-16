"""The ``integrations`` resource: third-party connections and lead sync.

Maps to the ``/v1/integrations`` route group. Covers the catalog of available
providers, the connections an organization has configured, their event
subscriptions, field mappings, sync runs, webhook signing secrets, connection
testing, ad-hoc pushes, and booked meetings.

A connection's ``webhook_secret`` is returned only by
:meth:`Integrations.connection_webhook_secret`; store it to verify inbound
provider webhooks. Sub-objects (``config``, mapping entries, run records) are
modeled permissively because provider shapes vary and the catalog grows.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncIntegrations",
    "IntegrationBooking",
    "IntegrationCatalogEntry",
    "IntegrationConnection",
    "IntegrationConnectionDeleted",
    "IntegrationEvent",
    "IntegrationEventDeleted",
    "IntegrationFieldMappings",
    "IntegrationRun",
    "IntegrationRunResult",
    "IntegrationTestResult",
    "IntegrationWebhookSecret",
    "Integrations",
]


class IntegrationCatalogEntry(BaseModel):
    """A provider available to connect from the integrations catalog."""

    provider: str
    name: str | None = None
    description: str | None = None
    category: str | None = None
    logo_url: str | None = None
    auth_type: str | None = None
    scopes: Sequence[str] = []
    capabilities: Sequence[str] = []
    config_schema: dict[str, Any] = {}
    docs_url: str | None = None
    status: str | None = None


class IntegrationConnection(BaseModel):
    """A configured connection to a third-party provider."""

    id: str
    organization_id: str | None = None
    provider: str | None = None
    status: str | None = None
    config: dict[str, Any] = {}
    name: str | None = None
    events: Sequence[str] = []
    webhook_url: str | None = None
    last_synced_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class IntegrationConnectionDeleted(BaseModel):
    """The result of removing a connection."""

    status: str | None = None


class IntegrationEvent(BaseModel):
    """An event subscription on a connection."""

    id: str
    connection_id: str | None = None
    event_type: str | None = None
    enabled: bool | None = None
    config: dict[str, Any] = {}
    created_at: str | None = None
    updated_at: str | None = None


class IntegrationEventDeleted(BaseModel):
    """The result of removing an event subscription."""

    status: str | None = None


class IntegrationFieldMappings(BaseModel):
    """The field mappings between Warmbly and a provider for a connection."""

    connection_id: str | None = None
    mappings: Sequence[dict[str, Any]] = []
    updated_at: str | None = None


class IntegrationRun(BaseModel):
    """A single sync run for a connection."""

    id: str
    connection_id: str | None = None
    status: str | None = None
    direction: str | None = None
    records_processed: int | None = None
    records_failed: int | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None


class IntegrationRunResult(BaseModel):
    """The result of triggering a push to a connection."""

    run_id: str | None = None
    status: str | None = None
    accepted: int | None = None


class IntegrationWebhookSecret(BaseModel):
    """A connection's inbound webhook signing secret."""

    webhook_secret: str | None = None


class IntegrationTestResult(BaseModel):
    """The result of testing a connection's credentials/connectivity."""

    ok: bool | None = None
    status: str | None = None
    message: str | None = None
    details: dict[str, Any] = {}


class IntegrationBooking(BaseModel):
    """A booked meeting surfaced through a calendar/scheduling integration."""

    id: str
    connection_id: str | None = None
    provider: str | None = None
    contact_id: str | None = None
    campaign_id: str | None = None
    status: str | None = None
    title: str | None = None
    attendee_email: str | None = None
    start_at: str | None = None
    end_at: str | None = None
    location: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Integrations(SyncAPIResource):
    """Synchronous ``integrations`` resource."""

    def catalog(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[IntegrationCatalogEntry]:
        """List providers available to connect (auto-paginating)."""
        return self._get_api_list(
            "/integrations/catalog",
            model=IntegrationCatalogEntry,
            options=options,
        )

    def list_connections(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        provider: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[IntegrationConnection]:
        """List configured connections (auto-paginating)."""
        return self._get_api_list(
            "/integrations/connections",
            model=IntegrationConnection,
            query={
                "limit": limit,
                "cursor": cursor,
                "provider": provider,
                "status": status,
            },
            options=options,
        )

    def create_connection(
        self,
        *,
        provider: str,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationConnection:
        """Create a connection to a provider.

        Args:
            provider: The catalog provider key to connect.
            config: Provider-specific configuration (credentials, options).
            name: An optional human-readable label for the connection.
            events: Optional list of provider event types to subscribe to.
        """
        body = drop_not_given(
            {
                "provider": provider,
                "config": config,
                "name": name,
                "events": events,
            }
        )
        return self._post(
            "/integrations/connections",
            cast_to=IntegrationConnection,
            body=body,
            options=options,
        )

    def get_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnection:
        """Retrieve a single connection by id."""
        return self._get(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnection,
            options=options,
        )

    def update_connection_config(
        self,
        connection_id: str,
        *,
        config: dict[str, Any],
        options: RequestOptions | None = None,
    ) -> IntegrationConnection:
        """Update a connection's provider-specific configuration.

        Args:
            connection_id: The connection to update.
            config: The new provider configuration to merge/apply.
        """
        body = drop_not_given({"config": config})
        return self._patch(
            f"/integrations/connections/{connection_id}/config",
            cast_to=IntegrationConnection,
            body=body,
            options=options,
        )

    def delete_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnectionDeleted:
        """Remove a connection."""
        return self._delete(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnectionDeleted,
            options=options,
        )

    def list_events(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[IntegrationEvent]:
        """List a connection's event subscriptions (auto-paginating)."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/events",
            model=IntegrationEvent,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def add_event(
        self,
        connection_id: str,
        *,
        event_type: str,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationEvent:
        """Subscribe a connection to a provider event type.

        Args:
            connection_id: The connection to attach the event to.
            event_type: The provider event type to subscribe to.
            enabled: Whether the subscription is active.
            config: Optional event-specific configuration.
        """
        body = drop_not_given(
            {
                "event_type": event_type,
                "enabled": enabled,
                "config": config,
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
        mappings: Sequence[dict[str, Any]],
        options: RequestOptions | None = None,
    ) -> IntegrationFieldMappings:
        """Replace a connection's field mappings.

        Args:
            connection_id: The connection whose mappings to replace.
            mappings: The full set of field mappings to store.
        """
        body = drop_not_given({"mappings": mappings})
        return self._put(
            f"/integrations/connections/{connection_id}/field-mappings",
            cast_to=IntegrationFieldMappings,
            body=body,
            options=options,
        )

    def runs(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[IntegrationRun]:
        """List a connection's sync runs (auto-paginating)."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/runs",
            model=IntegrationRun,
            query={"limit": limit, "cursor": cursor, "status": status},
            options=options,
        )

    def connection_webhook_secret(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationWebhookSecret:
        """Retrieve a connection's inbound webhook signing secret."""
        return self._get(
            f"/integrations/connections/{connection_id}/webhook-secret",
            cast_to=IntegrationWebhookSecret,
            options=options,
        )

    def test_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationTestResult:
        """Test a connection's credentials and connectivity."""
        return self._post(
            f"/integrations/connections/{connection_id}/test",
            cast_to=IntegrationTestResult,
            options=options,
        )

    def push(
        self,
        connection_id: str,
        *,
        records: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        payload: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationRunResult:
        """Push records or an event to a connection's provider.

        Args:
            connection_id: The connection to push to.
            records: Optional records to send to the provider.
            event_type: Optional event type describing the push.
            payload: Optional free-form payload for the push.
        """
        body = drop_not_given(
            {
                "records": records,
                "event_type": event_type,
                "payload": payload,
            }
        )
        return self._post(
            f"/integrations/connections/{connection_id}/push",
            cast_to=IntegrationRunResult,
            body=body,
            options=options,
        )

    def bookings(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        connection_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[IntegrationBooking]:
        """List booked meetings from calendar/scheduling integrations.

        Args:
            limit: Maximum number of bookings per page.
            cursor: Pagination cursor.
            connection_id: Filter by source connection.
            contact_id: Filter by contact.
            campaign_id: Filter by campaign.
            status: Filter by booking status.
            from_: Lower bound (RFC3339) on the booking start time.
            to: Upper bound (RFC3339) on the booking start time.
        """
        return self._get_api_list(
            "/integrations/bookings",
            model=IntegrationBooking,
            query={
                "limit": limit,
                "cursor": cursor,
                "connection_id": connection_id,
                "contact_id": contact_id,
                "campaign_id": campaign_id,
                "status": status,
                "from": from_,
                "to": to,
            },
            options=options,
        )


class AsyncIntegrations(AsyncAPIResource):
    """Asynchronous ``integrations`` resource."""

    def catalog(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[IntegrationCatalogEntry]:
        """List providers available to connect (auto-paginating)."""
        return self._get_api_list(
            "/integrations/catalog",
            model=IntegrationCatalogEntry,
            options=options,
        )

    def list_connections(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        provider: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[IntegrationConnection]:
        """List configured connections (auto-paginating)."""
        return self._get_api_list(
            "/integrations/connections",
            model=IntegrationConnection,
            query={
                "limit": limit,
                "cursor": cursor,
                "provider": provider,
                "status": status,
            },
            options=options,
        )

    async def create_connection(
        self,
        *,
        provider: str,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationConnection:
        """Create a connection to a provider.

        Args:
            provider: The catalog provider key to connect.
            config: Provider-specific configuration (credentials, options).
            name: An optional human-readable label for the connection.
            events: Optional list of provider event types to subscribe to.
        """
        body = drop_not_given(
            {
                "provider": provider,
                "config": config,
                "name": name,
                "events": events,
            }
        )
        return await self._post(
            "/integrations/connections",
            cast_to=IntegrationConnection,
            body=body,
            options=options,
        )

    async def get_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnection:
        """Retrieve a single connection by id."""
        return await self._get(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnection,
            options=options,
        )

    async def update_connection_config(
        self,
        connection_id: str,
        *,
        config: dict[str, Any],
        options: RequestOptions | None = None,
    ) -> IntegrationConnection:
        """Update a connection's provider-specific configuration.

        Args:
            connection_id: The connection to update.
            config: The new provider configuration to merge/apply.
        """
        body = drop_not_given({"config": config})
        return await self._patch(
            f"/integrations/connections/{connection_id}/config",
            cast_to=IntegrationConnection,
            body=body,
            options=options,
        )

    async def delete_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationConnectionDeleted:
        """Remove a connection."""
        return await self._delete(
            f"/integrations/connections/{connection_id}",
            cast_to=IntegrationConnectionDeleted,
            options=options,
        )

    def list_events(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[IntegrationEvent]:
        """List a connection's event subscriptions (auto-paginating)."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/events",
            model=IntegrationEvent,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def add_event(
        self,
        connection_id: str,
        *,
        event_type: str,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        config: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationEvent:
        """Subscribe a connection to a provider event type.

        Args:
            connection_id: The connection to attach the event to.
            event_type: The provider event type to subscribe to.
            enabled: Whether the subscription is active.
            config: Optional event-specific configuration.
        """
        body = drop_not_given(
            {
                "event_type": event_type,
                "enabled": enabled,
                "config": config,
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
        mappings: Sequence[dict[str, Any]],
        options: RequestOptions | None = None,
    ) -> IntegrationFieldMappings:
        """Replace a connection's field mappings.

        Args:
            connection_id: The connection whose mappings to replace.
            mappings: The full set of field mappings to store.
        """
        body = drop_not_given({"mappings": mappings})
        return await self._put(
            f"/integrations/connections/{connection_id}/field-mappings",
            cast_to=IntegrationFieldMappings,
            body=body,
            options=options,
        )

    def runs(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[IntegrationRun]:
        """List a connection's sync runs (auto-paginating)."""
        return self._get_api_list(
            f"/integrations/connections/{connection_id}/runs",
            model=IntegrationRun,
            query={"limit": limit, "cursor": cursor, "status": status},
            options=options,
        )

    async def connection_webhook_secret(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationWebhookSecret:
        """Retrieve a connection's inbound webhook signing secret."""
        return await self._get(
            f"/integrations/connections/{connection_id}/webhook-secret",
            cast_to=IntegrationWebhookSecret,
            options=options,
        )

    async def test_connection(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> IntegrationTestResult:
        """Test a connection's credentials and connectivity."""
        return await self._post(
            f"/integrations/connections/{connection_id}/test",
            cast_to=IntegrationTestResult,
            options=options,
        )

    async def push(
        self,
        connection_id: str,
        *,
        records: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        payload: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> IntegrationRunResult:
        """Push records or an event to a connection's provider.

        Args:
            connection_id: The connection to push to.
            records: Optional records to send to the provider.
            event_type: Optional event type describing the push.
            payload: Optional free-form payload for the push.
        """
        body = drop_not_given(
            {
                "records": records,
                "event_type": event_type,
                "payload": payload,
            }
        )
        return await self._post(
            f"/integrations/connections/{connection_id}/push",
            cast_to=IntegrationRunResult,
            body=body,
            options=options,
        )

    def bookings(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        connection_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[IntegrationBooking]:
        """List booked meetings from calendar/scheduling integrations.

        Args:
            limit: Maximum number of bookings per page.
            cursor: Pagination cursor.
            connection_id: Filter by source connection.
            contact_id: Filter by contact.
            campaign_id: Filter by campaign.
            status: Filter by booking status.
            from_: Lower bound (RFC3339) on the booking start time.
            to: Upper bound (RFC3339) on the booking start time.
        """
        return self._get_api_list(
            "/integrations/bookings",
            model=IntegrationBooking,
            query={
                "limit": limit,
                "cursor": cursor,
                "connection_id": connection_id,
                "contact_id": contact_id,
                "campaign_id": campaign_id,
                "status": status,
                "from": from_,
                "to": to,
            },
            options=options,
        )
