"""The ``agency`` resource: the ``/v1/agency`` route group."""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource

__all__ = ["Agency", "AsyncAgency"]


class Agency(SyncAPIResource):
    """Synchronous ``agency`` resource."""


class AsyncAgency(AsyncAPIResource):
    """Asynchronous ``agency`` resource."""
