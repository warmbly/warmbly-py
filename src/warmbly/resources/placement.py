"""The ``placement`` resource: inbox placement tests and batches.

Maps to the ``/v1/placement`` route group.
"""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource

__all__ = ["AsyncPlacement", "Placement"]


class Placement(SyncAPIResource):
    """Synchronous ``placement`` resource."""


class AsyncPlacement(AsyncAPIResource):
    """Asynchronous ``placement`` resource."""
