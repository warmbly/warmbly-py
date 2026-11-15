"""The ``reports`` resource: the ``/v1/reports`` route group."""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource

__all__ = ["AsyncReports", "Reports"]


class Reports(SyncAPIResource):
    """Synchronous ``reports`` resource."""


class AsyncReports(AsyncAPIResource):
    """Asynchronous ``reports`` resource."""
