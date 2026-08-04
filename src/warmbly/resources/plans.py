"""The ``plans`` resource: the read-only billing plan catalog.

Maps to ``GET /v1/plans``, which returns the whole catalog in one response
under a ``plans`` key. Plan objects are permissive
:class:`~warmbly._models.BaseModel` subclasses so additional pricing or feature
fields are preserved without a client upgrade.

Subscribing to a plan is a session-only flow (``/v1/subscription/*``) that an
API key or OAuth token cannot reach, so this resource is read-only by design.
"""

from __future__ import annotations

from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions

__all__ = [
    "AsyncPlans",
    "Plan",
    "Plans",
]


class Plan(BaseModel):
    """A billing plan.

    Attributes:
        id: The plan identifier.
        name: The human-readable plan name.
        description: An optional longer description.
        price: The plan price, if exposed.
        currency: The ISO currency code for ``price``, if exposed.
        interval: The billing interval (e.g. ``"month"``, ``"year"``).
        features: Plan feature flags or limits, if exposed.
    """

    id: str
    name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    interval: str | None = None
    features: dict[str, Any] | None = None


class Plans(SyncAPIResource):
    """Synchronous ``plans`` resource (read-only)."""

    def list(self, *, options: RequestOptions | None = None) -> SyncCursorPage[Plan]:
        """List the available billing plans.

        The catalog is returned in full, so the page never has a next page.

        Args:
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/plans", model=Plan, data_key="plans", options=options
        )


class AsyncPlans(AsyncAPIResource):
    """Asynchronous ``plans`` resource (read-only)."""

    def list(self, *, options: RequestOptions | None = None) -> AsyncPaginator[Plan]:
        """List the available billing plans.

        The catalog is returned in full, so the page never has a next page.

        Args:
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/plans", model=Plan, data_key="plans", options=options
        )
