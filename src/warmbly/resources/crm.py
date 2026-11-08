"""The ``crm`` resource: pipelines, deals, tasks, task types, and CRM mode.

Maps to the ``/v1/crm`` route group. A pipeline owns ordered stages; a deal
sits in exactly one stage; tasks hang off contacts and deals and carry a
user-managed *type* (Call, Email, Meeting, ...).

Deals and tasks each expose three read paths: a cheap cursor ``list`` with a
couple of filters, a faceted ``search`` that filters server-side across the
whole organization, and a ``summary`` that aggregates over the *same* filter
body so header totals are true sums rather than a reduce over one page.

A workspace runs its CRM either on Warmbly's own or on a connected one
(HubSpot, Pipedrive). The *CRM mode* methods (``settings``, ``metadata``,
``owners``, ``sync``, ``backfill``, the provider-side contact record and the
provider list import) only work once a provider is connected and chosen; in
Warmbly's own CRM they answer ``409`` with the identifier ``crm_not_connected``.
In provider mode, records read through the pipeline, deal, task and note
methods carry an ``external`` reference to where they live.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncCrm",
    "Crm",
    "CrmAccount",
    "CrmAffected",
    "CrmBackfillPreview",
    "CrmBulkTasksResult",
    "CrmContactView",
    "CrmExternalRef",
    "CrmImportPreview",
    "CrmImportResult",
    "CrmList",
    "CrmMetadata",
    "CrmOwner",
    "CrmSettings",
    "CrmSyncHealth",
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


class CrmExternalRef(BaseModel):
    """Where a CRM record lives outside Warmbly.

    Attached to deals, tasks, notes and pipelines read in provider mode.
    ``provider`` is ``hubspot`` or ``pipedrive``; ``owner_name`` is the
    provider-side owner when that owner is not a workspace member.
    """

    provider: str | None = None
    external_id: str | None = None
    url: str | None = None
    synced_at: str | None = None
    owner_name: str | None = None


class PipelineStage(BaseModel):
    """A stage within a pipeline.

    ``closed``, ``won`` and ``probability`` come from a connected CRM's stage
    metadata and are absent for Warmbly's own stages.
    """

    id: str
    pipeline_id: str | None = None
    name: str | None = None
    color: str | None = None
    position: int | None = None
    deal_count: int | None = None
    closed: bool | None = None
    won: bool | None = None
    probability: float | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Pipeline(BaseModel):
    """A CRM pipeline and its ordered stages."""

    id: str
    organization_id: str | None = None
    name: str | None = None
    position: int | None = None
    stages: Sequence[PipelineStage] = []
    external: CrmExternalRef | None = None
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
    external: CrmExternalRef | None = None
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
    external: CrmExternalRef | None = None
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


class CrmAccount(BaseModel):
    """The connected provider account.

    ``app_url`` is the provider's web app root for "Open in" links.
    ``missing_scopes`` lists permissions the connection lacks for full mode,
    in which case a reconnect is needed.
    """

    external_id: str | None = None
    name: str | None = None
    app_url: str | None = None
    status: str | None = None
    health: str | None = None
    missing_scopes: Sequence[str] = []


class CrmSettings(BaseModel):
    """The workspace's CRM mode.

    ``provider`` is ``native``, ``hubspot`` or ``pipedrive``. ``config`` holds
    the setup choices: ``activity`` (which events are written to the
    provider's timeline), ``create_contacts``, ``create_companies``,
    ``write_properties``, ``positive_reply``, ``exit_rules``, ``guards``,
    ``deal_pipelines``, ``display_properties``, ``field_map``,
    ``field_direction`` and ``for``.
    """

    organization_id: str | None = None
    provider: str | None = None
    connection_id: str | None = None
    config: dict[str, Any] | None = None
    setup_completed_at: str | None = None
    updated_at: str | None = None
    account: CrmAccount | None = None


class CrmMetadata(BaseModel):
    """The provider vocabulary the pickers render.

    ``lifecycle_stages``, ``lead_statuses``, ``task_types`` and ``pipelines``
    are ``{value, label}`` options; ``properties`` are ``{name, label, type,
    group_name, read_only}`` entries.
    """

    lifecycle_stages: Sequence[dict[str, Any]] = []
    lead_statuses: Sequence[dict[str, Any]] = []
    task_types: Sequence[dict[str, Any]] = []
    properties: Sequence[dict[str, Any]] = []
    pipelines: Sequence[dict[str, Any]] = []


class CrmOwner(BaseModel):
    """A provider user who can own records, and the member they map to.

    ``user_pinned`` is ``True`` when a member chose the match by hand rather
    than the server matching on address.
    """

    external_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    user_id: str | None = None
    user_pinned: bool | None = None
    archived: bool | None = None


class CrmSyncHealth(BaseModel):
    """The sync health panel: counts, failures and freshness.

    ``cursors`` reports each incremental pull (``object_type``,
    ``cursor_at``, ``last_run_at``, ``last_error``), ``failures`` the failed
    sync jobs, and ``counts`` how much provider data is mirrored
    (``contacts``, ``deals``, ``tasks``, ``pipelines``, ``owners``).
    """

    pending: int | None = None
    failed: int | None = None
    done_24h: int | None = None
    last_synced_at: str | None = None
    cursors: Sequence[dict[str, Any]] = []
    failures: Sequence[dict[str, Any]] = []
    counts: dict[str, Any] | None = None


class CrmAffected(BaseModel):
    """How many sync jobs a retry or discard touched."""

    affected: int | None = None


class CrmContactView(BaseModel):
    """The provider side of a contact.

    ``linked`` is whether the contact exists in the provider yet. ``owner`` is
    a :class:`CrmOwner`-shaped dict; ``lifecycle_stage`` and ``lead_status``
    are ``{value, label}``; ``company`` is ``{external_id, name, domain,
    url}``; ``properties`` are the displayed ``{name, label, value}`` entries.
    """

    provider: str | None = None
    linked: bool | None = None
    external_id: str | None = None
    url: str | None = None
    owner: dict[str, Any] | None = None
    lifecycle_stage: dict[str, Any] | None = None
    lead_status: dict[str, Any] | None = None
    company: dict[str, Any] | None = None
    opted_out: bool | None = None
    properties: Sequence[dict[str, Any]] = []
    synced_at: str | None = None


class CrmList(BaseModel):
    """A provider contact list Warmbly can import from."""

    external_id: str
    name: str | None = None
    size: int | None = None
    dynamic: bool | None = None
    updated_at: str | None = None


class CrmImportPreview(BaseModel):
    """Who a list import would bring in and who it skips.

    ``skipped`` is ``{reason, label, count}`` entries, ``sample`` is
    ``{email, first_name, last_name, company}`` rows, and ``truncated`` is set
    when the list is larger than one import takes.
    """

    list_name: str | None = None
    total: int | None = None
    included: int | None = None
    skipped: Sequence[dict[str, Any]] = []
    sample: Sequence[dict[str, Any]] = []
    truncated: bool | None = None


class CrmImportResult(BaseModel):
    """The contact import draft a list import produced.

    Finish it with the background-import methods on
    :class:`~warmbly.resources.contacts.Contacts` (``retrieve_import``,
    ``analyze_import``, ``start_import``).
    """

    import_id: str | None = None
    preview: CrmImportPreview | None = None


class CrmBackfillPreview(BaseModel):
    """What a backfill would copy into the provider."""

    deals: int | None = None
    tasks: int | None = None
    notes: int | None = None


class CrmBulkTasksResult(BaseModel):
    """How many tasks a bulk action touched."""

    affected: int | None = None


def _task_selection(
    *,
    tasks: NotGivenOr[Sequence[str]],
    select_all: NotGivenOr[bool],
    filters: NotGivenOr[Mapping[str, Any]],
    exclude: NotGivenOr[Sequence[str]],
) -> dict[str, Any]:
    """Build the selection fields shared by the bulk task actions."""
    return drop_not_given(
        {
            "tasks": NOT_GIVEN if isinstance(tasks, NotGiven) else list(tasks),
            "all": select_all,
            "filters": filters,
            "exclude": NOT_GIVEN if isinstance(exclude, NotGiven) else list(exclude),
        }
    )


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

    # -- CRM mode (HubSpot, Pipedrive) ---------------------------------------
    def settings(self, *, options: RequestOptions | None = None) -> CrmSettings:
        """Read the workspace's CRM mode and the connected account.

        Permissions: ``READ_CRM``.
        """
        return self._get("/crm/settings", cast_to=CrmSettings, options=options)

    def update_settings(
        self,
        *,
        provider: NotGivenOr[str] = NOT_GIVEN,
        connection_id: NotGivenOr[str] = NOT_GIVEN,
        config: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        complete_setup: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmSettings:
        """Switch the CRM and store the setup choices.

        Permissions: ``INTEGRATIONS``.

        Args:
            provider: ``"native"``, ``"hubspot"`` or ``"pipedrive"``.
            connection_id: The integration connection the provider runs on.
            config: The setup choices (see :class:`CrmSettings`).
            complete_setup: Stamp the setup wizard as finished.
        """
        return self._put(
            "/crm/settings",
            cast_to=CrmSettings,
            body=drop_not_given(
                {
                    "provider": provider,
                    "connection_id": connection_id,
                    "config": NOT_GIVEN
                    if isinstance(config, NotGiven)
                    else dict(config),
                    "complete_setup": complete_setup,
                }
            ),
            options=options,
        )

    def metadata(self, *, options: RequestOptions | None = None) -> CrmMetadata:
        """Read the provider's lifecycle stages, lead statuses, task types,
        contact properties and pipelines.

        Permissions: ``READ_CRM``.
        """
        return self._get("/crm/metadata", cast_to=CrmMetadata, options=options)

    def list_owners(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[CrmOwner]:
        """List the provider's owners and the member each maps to.

        Returned in full, unpaginated. Permissions: ``READ_CRM``.
        """
        return self._get_api_list("/crm/owners", model=CrmOwner, options=options)

    def map_owner(
        self,
        external_id: str,
        *,
        user_id: str | None,
        options: RequestOptions | None = None,
    ) -> None:
        """Pin a provider owner to a workspace member (``204``).

        Permissions: ``INTEGRATIONS``.

        Args:
            external_id: The provider's owner id.
            user_id: The member to pin, or ``None`` to clear the match.
        """
        return self._put(
            f"/crm/owners/{external_id}",
            cast_to=type(None),
            body={"user_id": user_id},
            options=options,
        )

    def sync_health(self, *, options: RequestOptions | None = None) -> CrmSyncHealth:
        """Report what is waiting, what failed and when each pull ran.

        Permissions: ``READ_CRM``.
        """
        return self._get("/crm/sync", cast_to=CrmSyncHealth, options=options)

    def sync_now(self, *, options: RequestOptions | None = None) -> None:
        """Start a full pull from the provider (``202``, no body).

        Permissions: ``INTEGRATIONS``.
        """
        return self._post("/crm/sync", cast_to=type(None), options=options)

    def retry_sync_failures(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmAffected:
        """Requeue failed sync jobs: all of them, or the *ids* given (max 500).

        Requeueing a requeued job changes nothing. Permissions:
        ``INTEGRATIONS``.
        """
        return self._post(
            "/crm/sync/retry",
            cast_to=CrmAffected,
            body=drop_not_given(
                {"ids": NOT_GIVEN if isinstance(ids, NotGiven) else list(ids)}
            ),
            options=options,
        )

    def discard_sync_failures(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmAffected:
        """Drop failed sync jobs: all of them, or the *ids* given (max 500).

        Permissions: ``INTEGRATIONS``.
        """
        return self._post(
            "/crm/sync/discard",
            cast_to=CrmAffected,
            body=drop_not_given(
                {"ids": NOT_GIVEN if isinstance(ids, NotGiven) else list(ids)}
            ),
            options=options,
        )

    def backfill_preview(
        self, *, options: RequestOptions | None = None
    ) -> CrmBackfillPreview:
        """Count the Warmbly-only records a switch would copy.

        Permissions: ``INTEGRATIONS``.
        """
        return self._get("/crm/backfill", cast_to=CrmBackfillPreview, options=options)

    def start_backfill(
        self,
        *,
        deals: NotGivenOr[bool] = NOT_GIVEN,
        tasks: NotGivenOr[bool] = NOT_GIVEN,
        notes: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> None:
        """Copy Warmbly's own deals, tasks and notes into the provider once
        (``202``, no body).

        A second call while one runs is folded into it, and copied records are
        never copied twice. Permissions: ``INTEGRATIONS``.
        """
        return self._post(
            "/crm/backfill",
            cast_to=type(None),
            body=drop_not_given({"deals": deals, "tasks": tasks, "notes": notes}),
            options=options,
        )

    def retrieve_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Read the provider side of a contact: owner, lifecycle stage, lead
        status, company and the chosen properties.

        Permissions: ``READ_CRM``.
        """
        return self._get(
            f"/crm/contacts/{contact_id}", cast_to=CrmContactView, options=options
        )

    def refresh_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Pull a contact's provider record, deals, tasks and notes now.

        Debounced per contact, so it is safe to call whenever a panel opens.
        Permissions: ``READ_CRM``.
        """
        return self._post(
            f"/crm/contacts/{contact_id}/refresh",
            cast_to=CrmContactView,
            options=options,
        )

    def link_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Find or create the contact in the provider.

        Permissions: ``WRITE_CRM``.
        """
        return self._post(
            f"/crm/contacts/{contact_id}/link",
            cast_to=CrmContactView,
            options=options,
        )

    def update_contact(
        self,
        contact_id: str,
        *,
        owner_external_id: NotGivenOr[str] = NOT_GIVEN,
        lifecycle_stage: NotGivenOr[str] = NOT_GIVEN,
        lead_status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmContactView:
        """Edit a contact's owner, lifecycle stage or lead status in place.

        Each value is at most 100 characters. Permissions: ``WRITE_CRM``.
        """
        return self._patch(
            f"/crm/contacts/{contact_id}",
            cast_to=CrmContactView,
            body=drop_not_given(
                {
                    "owner_external_id": owner_external_id,
                    "lifecycle_stage": lifecycle_stage,
                    "lead_status": lead_status,
                }
            ),
            options=options,
        )

    def list_lists(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CrmList]:
        """List the provider's contact lists for import (auto-paginating).

        Permissions: ``READ_CRM``.

        Args:
            q: Filter by name (at most 200 characters).
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/crm/lists",
            model=CrmList,
            query={"q": q, "limit": limit, "cursor": cursor},
            options=options,
        )

    def preview_list_import(
        self,
        *,
        list_id: str,
        apply_guards: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmImportPreview:
        """Count who a list import brings in and who it skips. Writes nothing.

        Permissions: ``WRITE_CONTACTS``.

        Args:
            list_id: The provider list (at most 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return self._post(
            "/crm/lists/preview",
            cast_to=CrmImportPreview,
            body=drop_not_given({"list_id": list_id, "apply_guards": apply_guards}),
            options=options,
        )

    def import_list(
        self,
        *,
        list_id: str,
        apply_guards: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmImportResult:
        """Turn a provider list into a contact import draft (``201``).

        The draft is finished in the regular import flow, see
        :class:`CrmImportResult`. Permissions: ``WRITE_CONTACTS``.

        Args:
            list_id: The provider list (at most 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return self._post(
            "/crm/lists/import",
            cast_to=CrmImportResult,
            body=drop_not_given({"list_id": list_id, "apply_guards": apply_guards}),
            options=options,
        )

    # -- bulk task actions ---------------------------------------------------
    def bulk_update_tasks(
        self,
        *,
        tasks: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmBulkTasksResult:
        """Write one status or priority onto a whole selection of tasks.

        Name the tasks by id, or by a search with *select_all* (up to 50000).
        The response carries the count, not the rows. At least one of
        *status* and *priority* is required. Permissions: ``WRITE_CRM``.

        Args:
            tasks: The task ids.
            select_all: Switch the selection from *tasks* to *filters*.
            filters: The same body :meth:`search_tasks` takes.
            exclude: Task ids to drop from a select-all.
            status: ``pending``, ``in_progress``, ``completed`` or
                ``cancelled``.
            priority: ``low``, ``medium``, ``high`` or ``urgent``.
        """
        return self._patch(
            "/crm/tasks",
            cast_to=CrmBulkTasksResult,
            body={
                **_task_selection(
                    tasks=tasks, select_all=select_all, filters=filters, exclude=exclude
                ),
                **drop_not_given({"status": status, "priority": priority}),
            },
            options=options,
        )

    def bulk_delete_tasks(
        self,
        task_ids: Sequence[str] | None = None,
        *,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmBulkTasksResult:
        """Delete a whole selection of tasks.

        Name the tasks by id (sent as a plain array), or by a search with
        *select_all* (up to 50000). The response carries the count.
        Permissions: ``WRITE_CRM``.

        Args:
            task_ids: The task ids.
            select_all: Switch the selection from ids to *filters*.
            filters: The same body :meth:`search_tasks` takes.
            exclude: Task ids to drop from a select-all.
        """
        body: Any
        if isinstance(select_all, NotGiven) and isinstance(filters, NotGiven):
            body = list(task_ids or [])
        else:
            body = _task_selection(
                tasks=list(task_ids or []),
                select_all=select_all,
                filters=filters,
                exclude=exclude,
            )
        return self._delete(
            "/crm/tasks", cast_to=CrmBulkTasksResult, body=body, options=options
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

    # -- CRM mode (HubSpot, Pipedrive) ---------------------------------------
    async def settings(self, *, options: RequestOptions | None = None) -> CrmSettings:
        """Read the workspace's CRM mode and the connected account.

        Permissions: ``READ_CRM``.
        """
        return await self._get("/crm/settings", cast_to=CrmSettings, options=options)

    async def update_settings(
        self,
        *,
        provider: NotGivenOr[str] = NOT_GIVEN,
        connection_id: NotGivenOr[str] = NOT_GIVEN,
        config: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        complete_setup: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmSettings:
        """Switch the CRM and store the setup choices.

        Permissions: ``INTEGRATIONS``.

        Args:
            provider: ``"native"``, ``"hubspot"`` or ``"pipedrive"``.
            connection_id: The integration connection the provider runs on.
            config: The setup choices (see :class:`CrmSettings`).
            complete_setup: Stamp the setup wizard as finished.
        """
        return await self._put(
            "/crm/settings",
            cast_to=CrmSettings,
            body=drop_not_given(
                {
                    "provider": provider,
                    "connection_id": connection_id,
                    "config": NOT_GIVEN
                    if isinstance(config, NotGiven)
                    else dict(config),
                    "complete_setup": complete_setup,
                }
            ),
            options=options,
        )

    async def metadata(self, *, options: RequestOptions | None = None) -> CrmMetadata:
        """Read the provider's lifecycle stages, lead statuses, task types,
        contact properties and pipelines.

        Permissions: ``READ_CRM``.
        """
        return await self._get("/crm/metadata", cast_to=CrmMetadata, options=options)

    def list_owners(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[CrmOwner]:
        """List the provider's owners and the member each maps to.

        Returned in full, unpaginated. Permissions: ``READ_CRM``.
        """
        return self._get_api_list("/crm/owners", model=CrmOwner, options=options)

    async def map_owner(
        self,
        external_id: str,
        *,
        user_id: str | None,
        options: RequestOptions | None = None,
    ) -> None:
        """Pin a provider owner to a workspace member (``204``).

        Permissions: ``INTEGRATIONS``.

        Args:
            external_id: The provider's owner id.
            user_id: The member to pin, or ``None`` to clear the match.
        """
        return await self._put(
            f"/crm/owners/{external_id}",
            cast_to=type(None),
            body={"user_id": user_id},
            options=options,
        )

    async def sync_health(
        self, *, options: RequestOptions | None = None
    ) -> CrmSyncHealth:
        """Report what is waiting, what failed and when each pull ran.

        Permissions: ``READ_CRM``.
        """
        return await self._get("/crm/sync", cast_to=CrmSyncHealth, options=options)

    async def sync_now(self, *, options: RequestOptions | None = None) -> None:
        """Start a full pull from the provider (``202``, no body).

        Permissions: ``INTEGRATIONS``.
        """
        return await self._post("/crm/sync", cast_to=type(None), options=options)

    async def retry_sync_failures(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmAffected:
        """Requeue failed sync jobs: all of them, or the *ids* given (max 500).

        Requeueing a requeued job changes nothing. Permissions:
        ``INTEGRATIONS``.
        """
        return await self._post(
            "/crm/sync/retry",
            cast_to=CrmAffected,
            body=drop_not_given(
                {"ids": NOT_GIVEN if isinstance(ids, NotGiven) else list(ids)}
            ),
            options=options,
        )

    async def discard_sync_failures(
        self,
        *,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmAffected:
        """Drop failed sync jobs: all of them, or the *ids* given (max 500).

        Permissions: ``INTEGRATIONS``.
        """
        return await self._post(
            "/crm/sync/discard",
            cast_to=CrmAffected,
            body=drop_not_given(
                {"ids": NOT_GIVEN if isinstance(ids, NotGiven) else list(ids)}
            ),
            options=options,
        )

    async def backfill_preview(
        self, *, options: RequestOptions | None = None
    ) -> CrmBackfillPreview:
        """Count the Warmbly-only records a switch would copy.

        Permissions: ``INTEGRATIONS``.
        """
        return await self._get(
            "/crm/backfill", cast_to=CrmBackfillPreview, options=options
        )

    async def start_backfill(
        self,
        *,
        deals: NotGivenOr[bool] = NOT_GIVEN,
        tasks: NotGivenOr[bool] = NOT_GIVEN,
        notes: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> None:
        """Copy Warmbly's own deals, tasks and notes into the provider once
        (``202``, no body).

        A second call while one runs is folded into it, and copied records are
        never copied twice. Permissions: ``INTEGRATIONS``.
        """
        return await self._post(
            "/crm/backfill",
            cast_to=type(None),
            body=drop_not_given({"deals": deals, "tasks": tasks, "notes": notes}),
            options=options,
        )

    async def retrieve_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Read the provider side of a contact: owner, lifecycle stage, lead
        status, company and the chosen properties.

        Permissions: ``READ_CRM``.
        """
        return await self._get(
            f"/crm/contacts/{contact_id}", cast_to=CrmContactView, options=options
        )

    async def refresh_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Pull a contact's provider record, deals, tasks and notes now.

        Debounced per contact, so it is safe to call whenever a panel opens.
        Permissions: ``READ_CRM``.
        """
        return await self._post(
            f"/crm/contacts/{contact_id}/refresh",
            cast_to=CrmContactView,
            options=options,
        )

    async def link_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Find or create the contact in the provider.

        Permissions: ``WRITE_CRM``.
        """
        return await self._post(
            f"/crm/contacts/{contact_id}/link",
            cast_to=CrmContactView,
            options=options,
        )

    async def update_contact(
        self,
        contact_id: str,
        *,
        owner_external_id: NotGivenOr[str] = NOT_GIVEN,
        lifecycle_stage: NotGivenOr[str] = NOT_GIVEN,
        lead_status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmContactView:
        """Edit a contact's owner, lifecycle stage or lead status in place.

        Each value is at most 100 characters. Permissions: ``WRITE_CRM``.
        """
        return await self._patch(
            f"/crm/contacts/{contact_id}",
            cast_to=CrmContactView,
            body=drop_not_given(
                {
                    "owner_external_id": owner_external_id,
                    "lifecycle_stage": lifecycle_stage,
                    "lead_status": lead_status,
                }
            ),
            options=options,
        )

    def list_lists(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[CrmList]:
        """List the provider's contact lists for import (auto-paginating).

        Permissions: ``READ_CRM``.

        Args:
            q: Filter by name (at most 200 characters).
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/crm/lists",
            model=CrmList,
            query={"q": q, "limit": limit, "cursor": cursor},
            options=options,
        )

    async def preview_list_import(
        self,
        *,
        list_id: str,
        apply_guards: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmImportPreview:
        """Count who a list import brings in and who it skips. Writes nothing.

        Permissions: ``WRITE_CONTACTS``.

        Args:
            list_id: The provider list (at most 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return await self._post(
            "/crm/lists/preview",
            cast_to=CrmImportPreview,
            body=drop_not_given({"list_id": list_id, "apply_guards": apply_guards}),
            options=options,
        )

    async def import_list(
        self,
        *,
        list_id: str,
        apply_guards: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmImportResult:
        """Turn a provider list into a contact import draft (``201``).

        The draft is finished in the regular import flow, see
        :class:`CrmImportResult`. Permissions: ``WRITE_CONTACTS``.

        Args:
            list_id: The provider list (at most 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return await self._post(
            "/crm/lists/import",
            cast_to=CrmImportResult,
            body=drop_not_given({"list_id": list_id, "apply_guards": apply_guards}),
            options=options,
        )

    # -- bulk task actions ---------------------------------------------------
    async def bulk_update_tasks(
        self,
        *,
        tasks: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmBulkTasksResult:
        """Write one status or priority onto a whole selection of tasks.

        Name the tasks by id, or by a search with *select_all* (up to 50000).
        The response carries the count, not the rows. At least one of
        *status* and *priority* is required. Permissions: ``WRITE_CRM``.

        Args:
            tasks: The task ids.
            select_all: Switch the selection from *tasks* to *filters*.
            filters: The same body :meth:`search_tasks` takes.
            exclude: Task ids to drop from a select-all.
            status: ``pending``, ``in_progress``, ``completed`` or
                ``cancelled``.
            priority: ``low``, ``medium``, ``high`` or ``urgent``.
        """
        return await self._patch(
            "/crm/tasks",
            cast_to=CrmBulkTasksResult,
            body={
                **_task_selection(
                    tasks=tasks, select_all=select_all, filters=filters, exclude=exclude
                ),
                **drop_not_given({"status": status, "priority": priority}),
            },
            options=options,
        )

    async def bulk_delete_tasks(
        self,
        task_ids: Sequence[str] | None = None,
        *,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CrmBulkTasksResult:
        """Delete a whole selection of tasks.

        Name the tasks by id (sent as a plain array), or by a search with
        *select_all* (up to 50000). The response carries the count.
        Permissions: ``WRITE_CRM``.

        Args:
            task_ids: The task ids.
            select_all: Switch the selection from ids to *filters*.
            filters: The same body :meth:`search_tasks` takes.
            exclude: Task ids to drop from a select-all.
        """
        body: Any
        if isinstance(select_all, NotGiven) and isinstance(filters, NotGiven):
            body = list(task_ids or [])
        else:
            body = _task_selection(
                tasks=list(task_ids or []),
                select_all=select_all,
                filters=filters,
                exclude=exclude,
            )
        return await self._delete(
            "/crm/tasks", cast_to=CrmBulkTasksResult, body=body, options=options
        )
