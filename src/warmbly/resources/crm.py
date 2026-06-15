"""The ``crm`` resource — deals, pipelines, and tasks.

Maps to the ``/v1/crm`` route group. The contract documents the route groups
(``/crm/deals``, ``/crm/pipelines``, ``/crm/tasks``) but does not enumerate
their exact payload shapes, so the models below are intentionally permissive
(``extra="allow"`` via :class:`~warmbly._models.BaseModel`) and only the
fields needed for routing/identification are typed explicitly.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncCursorPage, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncCrm",
    "Crm",
    "CrmTask",
    "Deal",
    "DealDeleted",
    "Pipeline",
]


class Deal(BaseModel):
    """A CRM deal.

    Permissive: only ``id`` is typed; all other fields are tolerated and
    accessible as attributes (the backend deal shape is not fully enumerated
    in the contract).
    """

    id: str
    organization_id: str | None = None
    name: str | None = None
    pipeline_id: str | None = None
    stage: str | None = None
    amount: float | None = None
    currency: str | None = None
    contact_id: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DealDeleted(BaseModel):
    """The result of deleting a deal."""

    id: str | None = None
    deleted: bool | None = None
    status: str | None = None


class Pipeline(BaseModel):
    """A CRM pipeline (permissive)."""

    id: str
    organization_id: str | None = None
    name: str | None = None
    stages: Sequence[dict[str, Any]] = []
    created_at: str | None = None
    updated_at: str | None = None


class CrmTask(BaseModel):
    """A CRM task (permissive)."""

    id: str
    organization_id: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_at: str | None = None
    deal_id: str | None = None
    contact_id: str | None = None
    assignee_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Crm(SyncAPIResource):
    """Synchronous ``crm`` resource (deals, pipelines, tasks)."""

    def list_deals(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Deal]:
        """List deals (auto-paginating)."""
        return self._get_api_list(
            "/crm/deals",
            model=Deal,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_deal(
        self,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        pipeline_id: NotGivenOr[str] = NOT_GIVEN,
        stage: NotGivenOr[str] = NOT_GIVEN,
        amount: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Create a deal.

        The deal payload is not fully enumerated in the contract; the typed
        params cover the common fields. Pass additional fields via
        ``options["extra_body"]`` if the backend accepts them.
        """
        body = drop_not_given(
            {
                "name": name,
                "pipeline_id": pipeline_id,
                "stage": stage,
                "amount": amount,
                "currency": currency,
                "contact_id": contact_id,
            }
        )
        return self._post("/crm/deals", cast_to=Deal, body=body, options=options)

    def retrieve_deal(
        self, deal_id: str, *, options: RequestOptions | None = None
    ) -> Deal:
        """Retrieve a single deal by id."""
        return self._get(f"/crm/deals/{deal_id}", cast_to=Deal, options=options)

    def update_deal(
        self,
        deal_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        pipeline_id: NotGivenOr[str] = NOT_GIVEN,
        stage: NotGivenOr[str] = NOT_GIVEN,
        amount: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Update a deal."""
        body = drop_not_given(
            {
                "name": name,
                "pipeline_id": pipeline_id,
                "stage": stage,
                "amount": amount,
                "currency": currency,
                "contact_id": contact_id,
                "status": status,
            }
        )
        return self._patch(
            f"/crm/deals/{deal_id}", cast_to=Deal, body=body, options=options
        )

    def delete_deal(
        self, deal_id: str, *, options: RequestOptions | None = None
    ) -> DealDeleted:
        """Delete a deal."""
        return self._delete(
            f"/crm/deals/{deal_id}", cast_to=DealDeleted, options=options
        )

    def list_pipelines(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Pipeline]:
        """List pipelines (auto-paginating)."""
        return self._get_api_list(
            "/crm/pipelines",
            model=Pipeline,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def list_tasks(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CrmTask]:
        """List CRM tasks (auto-paginating)."""
        return self._get_api_list(
            "/crm/tasks",
            model=CrmTask,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_task(
        self,
        *,
        title: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        due_at: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        assignee_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTask:
        """Create a CRM task.

        The task payload is not fully enumerated in the contract; the typed
        params cover the common fields. Pass additional fields via
        ``options["extra_body"]`` if the backend accepts them.
        """
        body = drop_not_given(
            {
                "title": title,
                "description": description,
                "due_at": due_at,
                "deal_id": deal_id,
                "contact_id": contact_id,
                "assignee_id": assignee_id,
            }
        )
        return self._post("/crm/tasks", cast_to=CrmTask, body=body, options=options)


class AsyncCrm(AsyncAPIResource):
    """Asynchronous ``crm`` resource (deals, pipelines, tasks)."""

    def list_deals(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[Deal]:
        """List deals (auto-paginating)."""
        return self._get_api_list(
            "/crm/deals",
            model=Deal,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_deal(
        self,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        pipeline_id: NotGivenOr[str] = NOT_GIVEN,
        stage: NotGivenOr[str] = NOT_GIVEN,
        amount: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Create a deal.

        The deal payload is not fully enumerated in the contract; the typed
        params cover the common fields. Pass additional fields via
        ``options["extra_body"]`` if the backend accepts them.
        """
        body = drop_not_given(
            {
                "name": name,
                "pipeline_id": pipeline_id,
                "stage": stage,
                "amount": amount,
                "currency": currency,
                "contact_id": contact_id,
            }
        )
        return await self._post("/crm/deals", cast_to=Deal, body=body, options=options)

    async def retrieve_deal(
        self, deal_id: str, *, options: RequestOptions | None = None
    ) -> Deal:
        """Retrieve a single deal by id."""
        return await self._get(f"/crm/deals/{deal_id}", cast_to=Deal, options=options)

    async def update_deal(
        self,
        deal_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        pipeline_id: NotGivenOr[str] = NOT_GIVEN,
        stage: NotGivenOr[str] = NOT_GIVEN,
        amount: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Update a deal."""
        body = drop_not_given(
            {
                "name": name,
                "pipeline_id": pipeline_id,
                "stage": stage,
                "amount": amount,
                "currency": currency,
                "contact_id": contact_id,
                "status": status,
            }
        )
        return await self._patch(
            f"/crm/deals/{deal_id}", cast_to=Deal, body=body, options=options
        )

    async def delete_deal(
        self, deal_id: str, *, options: RequestOptions | None = None
    ) -> DealDeleted:
        """Delete a deal."""
        return await self._delete(
            f"/crm/deals/{deal_id}", cast_to=DealDeleted, options=options
        )

    def list_pipelines(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[Pipeline]:
        """List pipelines (auto-paginating)."""
        return self._get_api_list(
            "/crm/pipelines",
            model=Pipeline,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def list_tasks(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[CrmTask]:
        """List CRM tasks (auto-paginating)."""
        return self._get_api_list(
            "/crm/tasks",
            model=CrmTask,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_task(
        self,
        *,
        title: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        due_at: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        assignee_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTask:
        """Create a CRM task.

        The task payload is not fully enumerated in the contract; the typed
        params cover the common fields. Pass additional fields via
        ``options["extra_body"]`` if the backend accepts them.
        """
        body = drop_not_given(
            {
                "title": title,
                "description": description,
                "due_at": due_at,
                "deal_id": deal_id,
                "contact_id": contact_id,
                "assignee_id": assignee_id,
            }
        )
        return await self._post(
            "/crm/tasks", cast_to=CrmTask, body=body, options=options
        )
