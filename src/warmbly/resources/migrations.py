"""The ``migrations`` resource: the ``/v1/migrations`` route group."""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource

__all__ = ["AsyncMigrations", "Migrations"]


class Migrations(SyncAPIResource):
    """Synchronous ``migrations`` resource."""


class AsyncMigrations(AsyncAPIResource):
    """Asynchronous ``migrations`` resource."""
