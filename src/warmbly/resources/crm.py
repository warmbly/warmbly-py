"""The ``crm`` resource: pipelines, deals, tasks, and task types.

Maps to the ``/v1/crm`` route group. A pipeline owns ordered stages; a deal
sits in exactly one stage; tasks hang off contacts and deals and carry a
user-managed *type* (Call, Email, Meeting, ...).

Deals and tasks each expose three read paths: a cheap cursor ``list`` with a
couple of filters, a faceted ``search`` that filters server-side across the
whole organization, and a ``summary`` that aggregates over the *same* filter
body so header totals are true sums rather than a reduce over one page.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncCrm",
    "Crm",
    "CrmTask",
    "CrmTaskDeleted",
    "CrmTaskType",
    "CrmTaskTypeDeleted",
    "Deal",
    "DealDeleted",
    "DealSearchPage",
    "DealsSummary",
    "Pipeline",
    "PipelineDeleted",
    "PipelineStage",
    "PipelineStageDeleted",
    "TaskSearchPage",
    "TasksSummary",
]


class PipelineStage(BaseModel):
    """A stage within a pipeline."""

    id: str
    pipeline_id: str | None = None
    name: str | None = None
    color: str | None = None
    position: int | None = None
    deal_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Pipeline(BaseModel):
    """A CRM pipeline and its ordered stages."""

    id: str
    organization_id: str | None = None
    name: str | None = None
    position: int | None = None
    stages: Sequence[PipelineStage] = []
    created_at: str | None = None
    updated_at: str | None = None


class PipelineDeleted(BaseModel):
    """The result of deleting a pipeline (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class PipelineStageDeleted(BaseModel):
    """The result of deleting a pipeline stage (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class Deal(BaseModel):
    """A CRM deal.

    ``status`` is one of ``"open"``, ``"won"``, or ``"lost"``. ``value`` is
    the monetary amount in ``currency``.
    """

    id: str
    organization_id: str | None = None
    pipeline_id: str | None = None
    stage_id: str | None = None
    contact_id: str | None = None
    name: str | None = None
    value: float | None = None
    currency: str | None = None
    status: str | None = None
    expected_close_date: str | None = None
    won_at: str | None = None
    lost_at: str | None = None
    lost_reason: str | None = None
    assigned_to: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    source_mailbox_id: str | None = None
    contact: dict[str, Any] | None = None
    stage: PipelineStage | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DealDeleted(BaseModel):
    """The result of deleting a deal (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class DealSearchPage(BaseModel):
    """One page of faceted deal-search results."""

    data: Sequence[Deal] = []
    pagination: dict[str, Any] = {}


class DealsSummary(BaseModel):
    """Server-side aggregates over a deal filter body.

    ``mixed_currency`` is ``True`` when the matching deals span more than one
    currency, in which case the money totals are not directly comparable.
    """

    total: int | None = None
    open_count: int | None = None
    open_value: float | None = None
    won_count: int | None = None
    won_value: float | None = None
    lost_count: int | None = None
    lost_value: float | None = None
    currency: str | None = None
    mixed_currency: bool | None = None
    stages: Sequence[dict[str, Any]] = []


class CrmTaskType(BaseModel):
    """A user-managed task type (Call, Email, Meeting, ...).

    Tasks reference their type by *name*, so deleting a type never orphans
    existing tasks.
    """

    id: str
    organization_id: str | None = None
    name: str | None = None
    color: str | None = None
    position: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CrmTaskTypeDeleted(BaseModel):
    """The result of deleting a task type (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class CrmTask(BaseModel):
    """A CRM task.

    ``priority`` is one of ``"low"``, ``"medium"``, ``"high"``, ``"urgent"``;
    ``status`` is one of ``"pending"``, ``"in_progress"``, ``"completed"``,
    ``"cancelled"``. ``type`` is a task-type *name*.
    """

    id: str
    organization_id: str | None = None
    contact_id: str | None = None
    deal_id: str | None = None
    assigned_to: str | None = None
    assigned_team_id: str | None = None
    created_by: str | None = None
    title: str | None = None
    description: str | None = None
    due_date: str | None = None
    priority: str | None = None
    type: str | None = None
    status: str | None = None
    completed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CrmTaskDeleted(BaseModel):
    """The result of deleting a CRM task (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class TaskSearchPage(BaseModel):
    """One page of faceted task-search results."""

    data: Sequence[CrmTask] = []
    pagination: dict[str, Any] = {}


class TasksSummary(BaseModel):
    """Server-side aggregates over a task filter body."""

    total: int | None = None
    pending_count: int | None = None
    in_progress_count: int | None = None
    completed_count: int | None = None
    cancelled_count: int | None = None
    overdue_count: int | None = None
    high_priority_count: int | None = None


def _deal_filter(
    *,
    query: NotGivenOr[str],
    statuses: NotGivenOr[Sequence[str]],
    pipeline_ids: NotGivenOr[Sequence[str]],
    stage_ids: NotGivenOr[Sequence[str]],
    assigned_to: NotGivenOr[Sequence[str]],
    campaign_ids: NotGivenOr[Sequence[str]],
    min_value: NotGivenOr[float],
    max_value: NotGivenOr[float],
    close_after: NotGivenOr[str],
    close_before: NotGivenOr[str],
    created_after: NotGivenOr[str],
    created_before: NotGivenOr[str],
    sort_by: NotGivenOr[str],
    reverse: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the shared filter body for deal search and summary."""
    return drop_not_given(
        {
            "query": query,
            "statuses": statuses,
            "pipeline_ids": pipeline_ids,
            "stage_ids": stage_ids,
            "assigned_to": assigned_to,
            "campaign_ids": campaign_ids,
            "min_value": min_value,
            "max_value": max_value,
            "close_after": close_after,
            "close_before": close_before,
            "created_after": created_after,
            "created_before": created_before,
            "sort_by": sort_by,
            "reverse": reverse,
        }
    )


def _task_filter(
    *,
    query: NotGivenOr[str],
    statuses: NotGivenOr[Sequence[str]],
    priorities: NotGivenOr[Sequence[str]],
    types: NotGivenOr[Sequence[str]],
    assigned_to: NotGivenOr[Sequence[str]],
    team_ids: NotGivenOr[Sequence[str]],
    contact_id: NotGivenOr[str],
    deal_id: NotGivenOr[str],
    due_after: NotGivenOr[str],
    due_before: NotGivenOr[str],
    overdue: NotGivenOr[bool],
    sort_by: NotGivenOr[str],
    reverse: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the shared filter body for task search and summary."""
    return drop_not_given(
        {
            "query": query,
            "statuses": statuses,
            "priorities": priorities,
            "types": types,
            "assigned_to": assigned_to,
            "team_ids": team_ids,
            "contact_id": contact_id,
            "deal_id": deal_id,
            "due_after": due_after,
            "due_before": due_before,
            "overdue": overdue,
            "sort_by": sort_by,
            "reverse": reverse,
        }
    )


def _deal_body(
    *,
    name: NotGivenOr[str],
    pipeline_id: NotGivenOr[str],
    stage_id: NotGivenOr[str],
    contact_id: NotGivenOr[str],
    value: NotGivenOr[float],
    currency: NotGivenOr[str],
    expected_close_date: NotGivenOr[str],
    assigned_to: NotGivenOr[str],
    campaign_id: NotGivenOr[str],
    source_mailbox_id: NotGivenOr[str],
    status: NotGivenOr[str] = NOT_GIVEN,
    lost_reason: NotGivenOr[str] = NOT_GIVEN,
) -> dict[str, Any]:
    return drop_not_given(
        {
            "name": name,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
            "contact_id": contact_id,
            "value": value,
            "currency": currency,
            "expected_close_date": expected_close_date,
            "assigned_to": assigned_to,
            "campaign_id": campaign_id,
            "source_mailbox_id": source_mailbox_id,
            "status": status,
            "lost_reason": lost_reason,
        }
    )


def _task_body(
    *,
    title: NotGivenOr[str],
    description: NotGivenOr[str],
    due_date: NotGivenOr[str],
    priority: NotGivenOr[str],
    type: NotGivenOr[str],
    contact_id: NotGivenOr[str],
    deal_id: NotGivenOr[str],
    assigned_to: NotGivenOr[str],
    assigned_team_id: NotGivenOr[str],
    status: NotGivenOr[str] = NOT_GIVEN,
) -> dict[str, Any]:
    return drop_not_given(
        {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "type": type,
            "contact_id": contact_id,
            "deal_id": deal_id,
            "assigned_to": assigned_to,
            "assigned_team_id": assigned_team_id,
            "status": status,
        }
    )


class Crm(SyncAPIResource):
    """Synchronous ``crm`` resource (pipelines, deals, tasks, task types)."""

    # -- pipelines -----------------------------------------------------------
    def list_pipelines(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[Pipeline]:
        """List pipelines with their stages. Returned in full, unpaginated."""
        return self._get_api_list("/crm/pipelines", model=Pipeline, options=options)

    def create_pipeline(
        self,
        *,
        name: str,
        stages: Sequence[Mapping[str, str]] | None = None,
        options: RequestOptions | None = None,
    ) -> Pipeline:
        """Create a pipeline.

        Args:
            name: The pipeline name.
            stages: Initial stages, each ``{"name": ..., "color": ...}``, in
                order.
        """
        body = drop_not_given(
            {"name": name, "stages": [dict(s) for s in stages] if stages else NOT_GIVEN}
        )
        return self._post(
            "/crm/pipelines", cast_to=Pipeline, body=body, options=options
        )

    def retrieve_pipeline(
        self, pipeline_id: str, *, options: RequestOptions | None = None
    ) -> Pipeline:
        """Retrieve a single pipeline by id."""
        return self._get(
            f"/crm/pipelines/{pipeline_id}", cast_to=Pipeline, options=options
        )

    def update_pipeline(
        self,
        pipeline_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Pipeline:
        """Rename a pipeline."""
        return self._patch(
            f"/crm/pipelines/{pipeline_id}",
            cast_to=Pipeline,
            body=drop_not_given({"name": name}),
            options=options,
        )

    def delete_pipeline(
        self, pipeline_id: str, *, options: RequestOptions | None = None
    ) -> PipelineDeleted:
        """Delete a pipeline."""
        return self._delete(
            f"/crm/pipelines/{pipeline_id}", cast_to=PipelineDeleted, options=options
        )

    def create_stage(
        self,
        pipeline_id: str,
        *,
        name: str,
        color: str,
        options: RequestOptions | None = None,
    ) -> PipelineStage:
        """Append a stage to a pipeline."""
        return self._post(
            f"/crm/pipelines/{pipeline_id}/stages",
            cast_to=PipelineStage,
            body={"name": name, "color": color},
            options=options,
        )

    def update_stage(
        self,
        pipeline_id: str,
        stage_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PipelineStage:
        """Rename or recolour a pipeline stage."""
        return self._patch(
            f"/crm/pipelines/{pipeline_id}/stages/{stage_id}",
            cast_to=PipelineStage,
            body=drop_not_given({"name": name, "color": color}),
            options=options,
        )

    def delete_stage(
        self,
        pipeline_id: str,
        stage_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> PipelineStageDeleted:
        """Delete a pipeline stage."""
        return self._delete(
            f"/crm/pipelines/{pipeline_id}/stages/{stage_id}",
            cast_to=PipelineStageDeleted,
            options=options,
        )

    # -- deals ---------------------------------------------------------------
    def list_deals(
        self,
        *,
        pipeline_id: NotGivenOr[str] = NOT_GIVEN,
        stage_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Deal]:
        """List deals (auto-paginating).

        Args:
            pipeline_id: Restrict to one pipeline.
            stage_id: Restrict to one stage.
            status: ``"open"``, ``"won"``, or ``"lost"``.
        """
        return self._get_api_list(
            "/crm/deals",
            model=Deal,
            query={
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
                "status": status,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def create_deal(
        self,
        *,
        name: str,
        pipeline_id: str,
        stage_id: str,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        value: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        expected_close_date: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        source_mailbox_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Create a deal.

        Args:
            name: The deal name.
            pipeline_id: The pipeline to create it in.
            stage_id: The stage to place it in.
            contact_id: The contact the deal is with.
            value: The monetary value.
            currency: The ISO currency code for *value*.
            expected_close_date: RFC 3339 timestamp.
            assigned_to: The owning user's id.
            campaign_id: The campaign to attribute the deal to.
            source_mailbox_id: The mailbox the deal originated from.
        """
        return self._post(
            "/crm/deals",
            cast_to=Deal,
            body=_deal_body(
                name=name,
                pipeline_id=pipeline_id,
                stage_id=stage_id,
                contact_id=contact_id,
                value=value,
                currency=currency,
                expected_close_date=expected_close_date,
                assigned_to=assigned_to,
                campaign_id=campaign_id,
                source_mailbox_id=source_mailbox_id,
            ),
            options=options,
        )

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
        stage_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        value: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        expected_close_date: NotGivenOr[str] = NOT_GIVEN,
        lost_reason: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Update a deal. Moving it between stages is a ``stage_id`` change."""
        return self._patch(
            f"/crm/deals/{deal_id}",
            cast_to=Deal,
            body=_deal_body(
                name=name,
                pipeline_id=NOT_GIVEN,
                stage_id=stage_id,
                contact_id=contact_id,
                value=value,
                currency=currency,
                expected_close_date=expected_close_date,
                assigned_to=assigned_to,
                campaign_id=NOT_GIVEN,
                source_mailbox_id=NOT_GIVEN,
                status=status,
                lost_reason=lost_reason,
            ),
            options=options,
        )

    def delete_deal(
        self, deal_id: str, *, options: RequestOptions | None = None
    ) -> DealDeleted:
        """Delete a deal."""
        return self._delete(
            f"/crm/deals/{deal_id}", cast_to=DealDeleted, options=options
        )

    def search_deals(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        pipeline_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        stage_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        min_value: NotGivenOr[float] = NOT_GIVEN,
        max_value: NotGivenOr[float] = NOT_GIVEN,
        close_after: NotGivenOr[str] = NOT_GIVEN,
        close_before: NotGivenOr[str] = NOT_GIVEN,
        created_after: NotGivenOr[str] = NOT_GIVEN,
        created_before: NotGivenOr[str] = NOT_GIVEN,
        sort_by: NotGivenOr[str] = NOT_GIVEN,
        reverse: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DealSearchPage:
        """Search deals across every pipeline.

        Every facet is optional; an empty filter matches every deal. Paging is
        explicit here (pass ``cursor`` from ``pagination.next_cursor``) because
        the filter travels in the request body.

        Args:
            query: Substring matched against the deal name.
            statuses: Any of ``"open"``, ``"won"``, ``"lost"``.
            sort_by: ``created_at``, ``updated_at``, ``value``,
                ``expected_close_date``, or ``name``.
            reverse: ``True`` for ascending; the default is descending.
            limit: Page size (max 200).
            cursor: An opaque cursor from a previous page.
        """
        return self._post(
            "/crm/deals/search",
            cast_to=DealSearchPage,
            body=_deal_filter(
                query=query,
                statuses=statuses,
                pipeline_ids=pipeline_ids,
                stage_ids=stage_ids,
                assigned_to=assigned_to,
                campaign_ids=campaign_ids,
                min_value=min_value,
                max_value=max_value,
                close_after=close_after,
                close_before=close_before,
                created_after=created_after,
                created_before=created_before,
                sort_by=sort_by,
                reverse=reverse,
            ),
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def deals_summary(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        pipeline_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        stage_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        min_value: NotGivenOr[float] = NOT_GIVEN,
        max_value: NotGivenOr[float] = NOT_GIVEN,
        close_after: NotGivenOr[str] = NOT_GIVEN,
        close_before: NotGivenOr[str] = NOT_GIVEN,
        created_after: NotGivenOr[str] = NOT_GIVEN,
        created_before: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DealsSummary:
        """Aggregate deals over the same filter body as :meth:`search_deals`."""
        return self._post(
            "/crm/deals/summary",
            cast_to=DealsSummary,
            body=_deal_filter(
                query=query,
                statuses=statuses,
                pipeline_ids=pipeline_ids,
                stage_ids=stage_ids,
                assigned_to=assigned_to,
                campaign_ids=campaign_ids,
                min_value=min_value,
                max_value=max_value,
                close_after=close_after,
                close_before=close_before,
                created_after=created_after,
                created_before=created_before,
                sort_by=NOT_GIVEN,
                reverse=NOT_GIVEN,
            ),
            options=options,
        )

    # -- task types ----------------------------------------------------------
    def list_task_types(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[CrmTaskType]:
        """List task types. The first call seeds Call / Email / Meeting."""
        return self._get_api_list("/crm/task-types", model=CrmTaskType, options=options)

    def create_task_type(
        self,
        *,
        name: str,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTaskType:
        """Create a task type."""
        return self._post(
            "/crm/task-types",
            cast_to=CrmTaskType,
            body=drop_not_given({"name": name, "color": color}),
            options=options,
        )

    def update_task_type(
        self,
        task_type_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        position: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTaskType:
        """Rename, recolour, or reposition a task type."""
        return self._patch(
            f"/crm/task-types/{task_type_id}",
            cast_to=CrmTaskType,
            body=drop_not_given({"name": name, "color": color, "position": position}),
            options=options,
        )

    def delete_task_type(
        self, task_type_id: str, *, options: RequestOptions | None = None
    ) -> CrmTaskTypeDeleted:
        """Delete a task type. Existing tasks keep the label."""
        return self._delete(
            f"/crm/task-types/{task_type_id}",
            cast_to=CrmTaskTypeDeleted,
            options=options,
        )

    # -- tasks ---------------------------------------------------------------
    def list_tasks(
        self,
        *,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CrmTask]:
        """List CRM tasks (auto-paginating)."""
        return self._get_api_list(
            "/crm/tasks",
            model=CrmTask,
            query={
                "contact_id": contact_id,
                "deal_id": deal_id,
                "assigned_to": assigned_to,
                "status": status,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def create_task(
        self,
        *,
        title: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        due_date: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[str] = NOT_GIVEN,
        type: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        assigned_team_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTask:
        """Create a CRM task.

        Args:
            title: The task title.
            description: A longer description.
            due_date: RFC 3339 due timestamp.
            priority: ``"low"``, ``"medium"``, ``"high"``, or ``"urgent"``.
            type: A task-type name (see :meth:`list_task_types`).
            contact_id: The contact the task relates to.
            deal_id: The deal the task relates to.
            assigned_to: The assignee's user id.
            assigned_team_id: The assignee team's id.
        """
        return self._post(
            "/crm/tasks",
            cast_to=CrmTask,
            body=_task_body(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                type=type,
                contact_id=contact_id,
                deal_id=deal_id,
                assigned_to=assigned_to,
                assigned_team_id=assigned_team_id,
            ),
            options=options,
        )

    def retrieve_task(
        self, task_id: str, *, options: RequestOptions | None = None
    ) -> CrmTask:
        """Retrieve a single CRM task by id."""
        return self._get(f"/crm/tasks/{task_id}", cast_to=CrmTask, options=options)

    def update_task(
        self,
        task_id: str,
        *,
        title: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        due_date: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[str] = NOT_GIVEN,
        type: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        assigned_team_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTask:
        """Update a CRM task. Completing one is a ``status`` change."""
        return self._patch(
            f"/crm/tasks/{task_id}",
            cast_to=CrmTask,
            body=_task_body(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                type=type,
                contact_id=NOT_GIVEN,
                deal_id=NOT_GIVEN,
                assigned_to=assigned_to,
                assigned_team_id=assigned_team_id,
                status=status,
            ),
            options=options,
        )

    def delete_task(
        self, task_id: str, *, options: RequestOptions | None = None
    ) -> CrmTaskDeleted:
        """Delete a CRM task."""
        return self._delete(
            f"/crm/tasks/{task_id}", cast_to=CrmTaskDeleted, options=options
        )

    def search_tasks(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        priorities: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        types: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        team_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        due_after: NotGivenOr[str] = NOT_GIVEN,
        due_before: NotGivenOr[str] = NOT_GIVEN,
        overdue: NotGivenOr[bool] = NOT_GIVEN,
        sort_by: NotGivenOr[str] = NOT_GIVEN,
        reverse: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TaskSearchPage:
        """Search CRM tasks.

        Every facet is optional; an empty filter matches every task. Paging is
        explicit (pass ``cursor`` from ``pagination.next_cursor``).

        Args:
            overdue: Only tasks past their due date and not finished.
            sort_by: ``created_at``, ``due_date``, ``priority``, ``title``, or
                ``updated_at``.
            reverse: ``True`` for ascending; the default is descending.
            limit: Page size (max 200).
        """
        return self._post(
            "/crm/tasks/search",
            cast_to=TaskSearchPage,
            body=_task_filter(
                query=query,
                statuses=statuses,
                priorities=priorities,
                types=types,
                assigned_to=assigned_to,
                team_ids=team_ids,
                contact_id=contact_id,
                deal_id=deal_id,
                due_after=due_after,
                due_before=due_before,
                overdue=overdue,
                sort_by=sort_by,
                reverse=reverse,
            ),
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def tasks_summary(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        priorities: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        types: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        team_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        due_after: NotGivenOr[str] = NOT_GIVEN,
        due_before: NotGivenOr[str] = NOT_GIVEN,
        overdue: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TasksSummary:
        """Aggregate tasks over the same filter body as :meth:`search_tasks`."""
        return self._post(
            "/crm/tasks/summary",
            cast_to=TasksSummary,
            body=_task_filter(
                query=query,
                statuses=statuses,
                priorities=priorities,
                types=types,
                assigned_to=assigned_to,
                team_ids=team_ids,
                contact_id=contact_id,
                deal_id=deal_id,
                due_after=due_after,
                due_before=due_before,
                overdue=overdue,
                sort_by=NOT_GIVEN,
                reverse=NOT_GIVEN,
            ),
            options=options,
        )


class AsyncCrm(AsyncAPIResource):
    """Asynchronous ``crm`` resource (pipelines, deals, tasks, task types)."""

    # -- pipelines -----------------------------------------------------------
    def list_pipelines(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[Pipeline]:
        """List pipelines with their stages. Returned in full, unpaginated."""
        return self._get_api_list("/crm/pipelines", model=Pipeline, options=options)

    async def create_pipeline(
        self,
        *,
        name: str,
        stages: Sequence[Mapping[str, str]] | None = None,
        options: RequestOptions | None = None,
    ) -> Pipeline:
        """Create a pipeline.

        Args:
            name: The pipeline name.
            stages: Initial stages, each ``{"name": ..., "color": ...}``, in
                order.
        """
        body = drop_not_given(
            {"name": name, "stages": [dict(s) for s in stages] if stages else NOT_GIVEN}
        )
        return await self._post(
            "/crm/pipelines", cast_to=Pipeline, body=body, options=options
        )

    async def retrieve_pipeline(
        self, pipeline_id: str, *, options: RequestOptions | None = None
    ) -> Pipeline:
        """Retrieve a single pipeline by id."""
        return await self._get(
            f"/crm/pipelines/{pipeline_id}", cast_to=Pipeline, options=options
        )

    async def update_pipeline(
        self,
        pipeline_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Pipeline:
        """Rename a pipeline."""
        return await self._patch(
            f"/crm/pipelines/{pipeline_id}",
            cast_to=Pipeline,
            body=drop_not_given({"name": name}),
            options=options,
        )

    async def delete_pipeline(
        self, pipeline_id: str, *, options: RequestOptions | None = None
    ) -> PipelineDeleted:
        """Delete a pipeline."""
        return await self._delete(
            f"/crm/pipelines/{pipeline_id}", cast_to=PipelineDeleted, options=options
        )

    async def create_stage(
        self,
        pipeline_id: str,
        *,
        name: str,
        color: str,
        options: RequestOptions | None = None,
    ) -> PipelineStage:
        """Append a stage to a pipeline."""
        return await self._post(
            f"/crm/pipelines/{pipeline_id}/stages",
            cast_to=PipelineStage,
            body={"name": name, "color": color},
            options=options,
        )

    async def update_stage(
        self,
        pipeline_id: str,
        stage_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PipelineStage:
        """Rename or recolour a pipeline stage."""
        return await self._patch(
            f"/crm/pipelines/{pipeline_id}/stages/{stage_id}",
            cast_to=PipelineStage,
            body=drop_not_given({"name": name, "color": color}),
            options=options,
        )

    async def delete_stage(
        self,
        pipeline_id: str,
        stage_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> PipelineStageDeleted:
        """Delete a pipeline stage."""
        return await self._delete(
            f"/crm/pipelines/{pipeline_id}/stages/{stage_id}",
            cast_to=PipelineStageDeleted,
            options=options,
        )

    # -- deals ---------------------------------------------------------------
    def list_deals(
        self,
        *,
        pipeline_id: NotGivenOr[str] = NOT_GIVEN,
        stage_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Deal]:
        """List deals (auto-paginating).

        Args:
            pipeline_id: Restrict to one pipeline.
            stage_id: Restrict to one stage.
            status: ``"open"``, ``"won"``, or ``"lost"``.
        """
        return self._get_api_list(
            "/crm/deals",
            model=Deal,
            query={
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
                "status": status,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def create_deal(
        self,
        *,
        name: str,
        pipeline_id: str,
        stage_id: str,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        value: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        expected_close_date: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        source_mailbox_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Create a deal.

        Args:
            name: The deal name.
            pipeline_id: The pipeline to create it in.
            stage_id: The stage to place it in.
            contact_id: The contact the deal is with.
            value: The monetary value.
            currency: The ISO currency code for *value*.
            expected_close_date: RFC 3339 timestamp.
            assigned_to: The owning user's id.
            campaign_id: The campaign to attribute the deal to.
            source_mailbox_id: The mailbox the deal originated from.
        """
        return await self._post(
            "/crm/deals",
            cast_to=Deal,
            body=_deal_body(
                name=name,
                pipeline_id=pipeline_id,
                stage_id=stage_id,
                contact_id=contact_id,
                value=value,
                currency=currency,
                expected_close_date=expected_close_date,
                assigned_to=assigned_to,
                campaign_id=campaign_id,
                source_mailbox_id=source_mailbox_id,
            ),
            options=options,
        )

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
        stage_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        value: NotGivenOr[float] = NOT_GIVEN,
        currency: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        expected_close_date: NotGivenOr[str] = NOT_GIVEN,
        lost_reason: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Deal:
        """Update a deal. Moving it between stages is a ``stage_id`` change."""
        return await self._patch(
            f"/crm/deals/{deal_id}",
            cast_to=Deal,
            body=_deal_body(
                name=name,
                pipeline_id=NOT_GIVEN,
                stage_id=stage_id,
                contact_id=contact_id,
                value=value,
                currency=currency,
                expected_close_date=expected_close_date,
                assigned_to=assigned_to,
                campaign_id=NOT_GIVEN,
                source_mailbox_id=NOT_GIVEN,
                status=status,
                lost_reason=lost_reason,
            ),
            options=options,
        )

    async def delete_deal(
        self, deal_id: str, *, options: RequestOptions | None = None
    ) -> DealDeleted:
        """Delete a deal."""
        return await self._delete(
            f"/crm/deals/{deal_id}", cast_to=DealDeleted, options=options
        )

    async def search_deals(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        pipeline_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        stage_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        min_value: NotGivenOr[float] = NOT_GIVEN,
        max_value: NotGivenOr[float] = NOT_GIVEN,
        close_after: NotGivenOr[str] = NOT_GIVEN,
        close_before: NotGivenOr[str] = NOT_GIVEN,
        created_after: NotGivenOr[str] = NOT_GIVEN,
        created_before: NotGivenOr[str] = NOT_GIVEN,
        sort_by: NotGivenOr[str] = NOT_GIVEN,
        reverse: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DealSearchPage:
        """Search deals across every pipeline.

        Every facet is optional; an empty filter matches every deal. Paging is
        explicit here (pass ``cursor`` from ``pagination.next_cursor``) because
        the filter travels in the request body.

        Args:
            query: Substring matched against the deal name.
            statuses: Any of ``"open"``, ``"won"``, ``"lost"``.
            sort_by: ``created_at``, ``updated_at``, ``value``,
                ``expected_close_date``, or ``name``.
            reverse: ``True`` for ascending; the default is descending.
            limit: Page size (max 200).
            cursor: An opaque cursor from a previous page.
        """
        return await self._post(
            "/crm/deals/search",
            cast_to=DealSearchPage,
            body=_deal_filter(
                query=query,
                statuses=statuses,
                pipeline_ids=pipeline_ids,
                stage_ids=stage_ids,
                assigned_to=assigned_to,
                campaign_ids=campaign_ids,
                min_value=min_value,
                max_value=max_value,
                close_after=close_after,
                close_before=close_before,
                created_after=created_after,
                created_before=created_before,
                sort_by=sort_by,
                reverse=reverse,
            ),
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def deals_summary(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        pipeline_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        stage_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        min_value: NotGivenOr[float] = NOT_GIVEN,
        max_value: NotGivenOr[float] = NOT_GIVEN,
        close_after: NotGivenOr[str] = NOT_GIVEN,
        close_before: NotGivenOr[str] = NOT_GIVEN,
        created_after: NotGivenOr[str] = NOT_GIVEN,
        created_before: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DealsSummary:
        """Aggregate deals over the same filter body as :meth:`search_deals`."""
        return await self._post(
            "/crm/deals/summary",
            cast_to=DealsSummary,
            body=_deal_filter(
                query=query,
                statuses=statuses,
                pipeline_ids=pipeline_ids,
                stage_ids=stage_ids,
                assigned_to=assigned_to,
                campaign_ids=campaign_ids,
                min_value=min_value,
                max_value=max_value,
                close_after=close_after,
                close_before=close_before,
                created_after=created_after,
                created_before=created_before,
                sort_by=NOT_GIVEN,
                reverse=NOT_GIVEN,
            ),
            options=options,
        )

    # -- task types ----------------------------------------------------------
    def list_task_types(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[CrmTaskType]:
        """List task types. The first call seeds Call / Email / Meeting."""
        return self._get_api_list("/crm/task-types", model=CrmTaskType, options=options)

    async def create_task_type(
        self,
        *,
        name: str,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTaskType:
        """Create a task type."""
        return await self._post(
            "/crm/task-types",
            cast_to=CrmTaskType,
            body=drop_not_given({"name": name, "color": color}),
            options=options,
        )

    async def update_task_type(
        self,
        task_type_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        position: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTaskType:
        """Rename, recolour, or reposition a task type."""
        return await self._patch(
            f"/crm/task-types/{task_type_id}",
            cast_to=CrmTaskType,
            body=drop_not_given({"name": name, "color": color, "position": position}),
            options=options,
        )

    async def delete_task_type(
        self, task_type_id: str, *, options: RequestOptions | None = None
    ) -> CrmTaskTypeDeleted:
        """Delete a task type. Existing tasks keep the label."""
        return await self._delete(
            f"/crm/task-types/{task_type_id}",
            cast_to=CrmTaskTypeDeleted,
            options=options,
        )

    # -- tasks ---------------------------------------------------------------
    def list_tasks(
        self,
        *,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[CrmTask]:
        """List CRM tasks (auto-paginating)."""
        return self._get_api_list(
            "/crm/tasks",
            model=CrmTask,
            query={
                "contact_id": contact_id,
                "deal_id": deal_id,
                "assigned_to": assigned_to,
                "status": status,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def create_task(
        self,
        *,
        title: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        due_date: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[str] = NOT_GIVEN,
        type: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        assigned_team_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTask:
        """Create a CRM task.

        Args:
            title: The task title.
            description: A longer description.
            due_date: RFC 3339 due timestamp.
            priority: ``"low"``, ``"medium"``, ``"high"``, or ``"urgent"``.
            type: A task-type name (see :meth:`list_task_types`).
            contact_id: The contact the task relates to.
            deal_id: The deal the task relates to.
            assigned_to: The assignee's user id.
            assigned_team_id: The assignee team's id.
        """
        return await self._post(
            "/crm/tasks",
            cast_to=CrmTask,
            body=_task_body(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                type=type,
                contact_id=contact_id,
                deal_id=deal_id,
                assigned_to=assigned_to,
                assigned_team_id=assigned_team_id,
            ),
            options=options,
        )

    async def retrieve_task(
        self, task_id: str, *, options: RequestOptions | None = None
    ) -> CrmTask:
        """Retrieve a single CRM task by id."""
        return await self._get(
            f"/crm/tasks/{task_id}", cast_to=CrmTask, options=options
        )

    async def update_task(
        self,
        task_id: str,
        *,
        title: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        due_date: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[str] = NOT_GIVEN,
        type: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        assigned_to: NotGivenOr[str] = NOT_GIVEN,
        assigned_team_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmTask:
        """Update a CRM task. Completing one is a ``status`` change."""
        return await self._patch(
            f"/crm/tasks/{task_id}",
            cast_to=CrmTask,
            body=_task_body(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                type=type,
                contact_id=NOT_GIVEN,
                deal_id=NOT_GIVEN,
                assigned_to=assigned_to,
                assigned_team_id=assigned_team_id,
                status=status,
            ),
            options=options,
        )

    async def delete_task(
        self, task_id: str, *, options: RequestOptions | None = None
    ) -> CrmTaskDeleted:
        """Delete a CRM task."""
        return await self._delete(
            f"/crm/tasks/{task_id}", cast_to=CrmTaskDeleted, options=options
        )

    async def search_tasks(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        priorities: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        types: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        team_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        due_after: NotGivenOr[str] = NOT_GIVEN,
        due_before: NotGivenOr[str] = NOT_GIVEN,
        overdue: NotGivenOr[bool] = NOT_GIVEN,
        sort_by: NotGivenOr[str] = NOT_GIVEN,
        reverse: NotGivenOr[bool] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TaskSearchPage:
        """Search CRM tasks.

        Every facet is optional; an empty filter matches every task. Paging is
        explicit (pass ``cursor`` from ``pagination.next_cursor``).

        Args:
            overdue: Only tasks past their due date and not finished.
            sort_by: ``created_at``, ``due_date``, ``priority``, ``title``, or
                ``updated_at``.
            reverse: ``True`` for ascending; the default is descending.
            limit: Page size (max 200).
        """
        return await self._post(
            "/crm/tasks/search",
            cast_to=TaskSearchPage,
            body=_task_filter(
                query=query,
                statuses=statuses,
                priorities=priorities,
                types=types,
                assigned_to=assigned_to,
                team_ids=team_ids,
                contact_id=contact_id,
                deal_id=deal_id,
                due_after=due_after,
                due_before=due_before,
                overdue=overdue,
                sort_by=sort_by,
                reverse=reverse,
            ),
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def tasks_summary(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        statuses: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        priorities: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        types: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        assigned_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        team_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        deal_id: NotGivenOr[str] = NOT_GIVEN,
        due_after: NotGivenOr[str] = NOT_GIVEN,
        due_before: NotGivenOr[str] = NOT_GIVEN,
        overdue: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TasksSummary:
        """Aggregate tasks over the same filter body as :meth:`search_tasks`."""
        return await self._post(
            "/crm/tasks/summary",
            cast_to=TasksSummary,
            body=_task_filter(
                query=query,
                statuses=statuses,
                priorities=priorities,
                types=types,
                assigned_to=assigned_to,
                team_ids=team_ids,
                contact_id=contact_id,
                deal_id=deal_id,
                due_after=due_after,
                due_before=due_before,
                overdue=overdue,
                sort_by=NOT_GIVEN,
                reverse=NOT_GIVEN,
            ),
            options=options,
        )
