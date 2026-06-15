"""The ``plans`` resource — read-only billing plan catalog.

Maps to the ``/v1/plans`` route group. Both methods are ``GET``. Plan objects
are permissive :class:`~warmbly._models.BaseModel` subclasses so additional
pricing or feature fields are preserved without a client upgrade.
"""

from __future__ import annotations

from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions

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

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Plan]:
        """List the available billing plans (auto-paginating).

        Args:
            limit: Optional page size.
            cursor: Optional pagination cursor.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/plans",
            model=Plan,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve(self, plan_id: str, *, options: RequestOptions | None = None) -> Plan:
        """Retrieve a single billing plan by id.

        Args:
            plan_id: The plan id.
            options: Optional per-request overrides.
        """
        return self._get(f"/plans/{plan_id}", cast_to=Plan, options=options)


class AsyncPlans(AsyncAPIResource):
    """Asynchronous ``plans`` resource (read-only)."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Plan]:
        """List the available billing plans (auto-paginating).

        Args:
            limit: Optional page size.
            cursor: Optional pagination cursor.
            options: Optional per-request overrides.
        """
        return self._get_api_list(
            "/plans",
            model=Plan,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve(
        self, plan_id: str, *, options: RequestOptions | None = None
    ) -> Plan:
        """Retrieve a single billing plan by id.

        Args:
            plan_id: The plan id.
            options: Optional per-request overrides.
        """
        return await self._get(f"/plans/{plan_id}", cast_to=Plan, options=options)
