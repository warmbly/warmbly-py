"""The ``integrations.clay`` resource: the Clay inbound and outbound settings.

Maps to ``/v1/integrations/clay/:id``, where ``:id`` is the id of a Clay
*connection*. Reading needs the ``integrations`` API permission and changing
settings needs it as well (a settings action for people).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given

__all__ = ["AsyncClay", "Clay", "ClaySettings"]


class ClaySettings(BaseModel):
    """Everything the Clay page edits and shows.

    ``defaults`` decides where rows a Clay table sends land (``campaign_id``,
    ``category_ids``, ``segment_ids``, ``dedup``, ``subscribed``). ``outbound``
    is the default table Warmbly sends events to (``webhook_url_set``,
    ``webhook_host``, ``auth_token_set``, ``events``); the URL and token
    themselves are never returned. ``stats`` counts what the inbound URL has
    received (``received``, ``created``, ``updated``, ``skipped``, ``failed``,
    ``last_received_at``, ``last_error``).
    """

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    inbound_url_minted: bool | None = None
    defaults: dict[str, Any] | None = None
    outbound: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    available_events: Sequence[str] = []


class Clay(SyncAPIResource):
    """Synchronous ``integrations.clay`` resource."""

    def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ClaySettings:
        """Retrieve everything the Clay page shows."""
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
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        auth_token: NotGivenOr[str] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ClaySettings:
        """Save the inbound defaults, the outbound table and its events.

        Every field replaces its value, so a retry converges. Omitting a field
        leaves it alone.

        Args:
            connection_id: The Clay connection.
            defaults: Where inbound rows land (``campaign_id``,
                ``category_ids``, ``segment_ids``, ``dedup``, ``subscribed``).
            webhook_url: The Clay table's webhook URL; an empty string clears it.
            auth_token: The table's auth token; an empty string clears it.
            events: The Warmbly events sent to the table.
        """
        return self._patch(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            body=drop_not_given(
                {
                    "defaults": dict(defaults) if is_given(defaults) else defaults,
                    "webhook_url": webhook_url,
                    "auth_token": auth_token,
                    "events": list(events) if is_given(events) else events,
                }
            ),
            options=options,
        )


class AsyncClay(AsyncAPIResource):
    """Asynchronous ``integrations.clay`` resource."""

    async def get_settings(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ClaySettings:
        """Retrieve everything the Clay page shows."""
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
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        auth_token: NotGivenOr[str] = NOT_GIVEN,
        events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ClaySettings:
        """Save the inbound defaults, the outbound table and its events.

        Every field replaces its value, so a retry converges. Omitting a field
        leaves it alone.

        Args:
            connection_id: The Clay connection.
            defaults: Where inbound rows land (``campaign_id``,
                ``category_ids``, ``segment_ids``, ``dedup``, ``subscribed``).
            webhook_url: The Clay table's webhook URL; an empty string clears it.
            auth_token: The table's auth token; an empty string clears it.
            events: The Warmbly events sent to the table.
        """
        return await self._patch(
            f"/integrations/clay/{connection_id}",
            cast_to=ClaySettings,
            body=drop_not_given(
                {
                    "defaults": dict(defaults) if is_given(defaults) else defaults,
                    "webhook_url": webhook_url,
                    "auth_token": auth_token,
                    "events": list(events) if is_given(events) else events,
                }
            ),
            options=options,
        )
