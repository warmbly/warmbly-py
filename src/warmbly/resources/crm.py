"""The ``crm`` resource: pipelines, deals, tasks, task types, and CRM mode.

Maps to the ``/v1/crm`` route group. A pipeline owns ordered stages; a deal
sits in exactly one stage; tasks hang off contacts and deals and carry a
user-managed *type* (Call, Email, Meeting, ...).

Deals and tasks each expose three read paths: a cheap cursor ``list`` with a
couple of filters, a faceted ``search`` that filters server-side across the
whole organization, and a ``summary`` that aggregates over the *same* filter
body so header totals are true sums rather than a reduce over one page.

A workspace runs its CRM on Warmbly's own, or on a connected HubSpot or
Pipedrive. The settings, owners, sync, backfill, contact-record and list-import
methods (``get_settings`` and the rest of that section) manage the connected
case; they need a CRM provider configured on the instance.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import Field

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given

__all__ = [
    "AsyncCrm",
    "BulkTasksAffected",
    "Crm",
    "CrmAccount",
    "CrmAck",
    "CrmActivityLog",
    "CrmBackfillPreview",
    "CrmCompanyRef",
    "CrmContactView",
    "CrmEnrollmentGuards",
    "CrmExitRules",
    "CrmImportPerson",
    "CrmImportPreview",
    "CrmImportResult",
    "CrmImportSkip",
    "CrmList",
    "CrmMetadata",
    "CrmMirrorCounts",
    "CrmOption",
    "CrmOwner",
    "CrmProperty",
    "CrmPropertyView",
    "CrmProviderConfig",
    "CrmReplyOutcome",
    "CrmSettings",
    "CrmSyncAffected",
    "CrmSyncCursor",
    "CrmSyncHealth",
    "CrmSyncJob",
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


class BulkTasksAffected(BaseModel):
    """How many tasks a bulk update or delete touched."""

    affected: int | None = None


class CrmActivityLog(BaseModel):
    """Which Warmbly activity is written to the provider's timeline.

    Opens and clicks default off on the server: machine opens make them noise.
    """

    sent: bool | None = None
    replies: bool | None = None
    bounces: bool | None = None
    unsubscribes: bool | None = None
    opens: bool | None = None
    clicks: bool | None = None
    meetings: bool | None = None


class CrmReplyOutcome(BaseModel):
    """What a positive ("interested") reply does in the connected CRM.

    An empty ``lead_status`` or ``lifecycle_stage`` leaves that property alone.
    ``create_lead`` is Pipedrive only. ``deal_pipeline_id`` and
    ``deal_stage_id`` are local (mirrored) ids.
    """

    lead_status: str | None = None
    lifecycle_stage: str | None = None
    create_deal: bool | None = None
    create_lead: bool | None = None
    deal_pipeline_id: str | None = None
    deal_stage_id: str | None = None


class CrmExitRules(BaseModel):
    """Stop a contact's campaigns when the CRM says they have moved on."""

    deal_created: bool | None = None
    lifecycle_stages: Sequence[str] = []
    opted_out: bool | None = None


class CrmEnrollmentGuards(BaseModel):
    """Contacts to skip at import and enrolment time."""

    skip_lifecycle_stages: Sequence[str] = []
    skip_open_deals: bool | None = None
    skip_other_owners: bool | None = None
    skip_opted_out: bool | None = None


class CrmProviderConfig(BaseModel):
    """Every choice the CRM setup wizard asks, as stored on the server.

    ``field_map`` maps a Warmbly contact field (``first_name``, ``last_name``,
    ``email``, ``company``, ``phone`` or ``custom:<name>``) to a provider
    property; ``field_direction`` says which side wins per field (``push``,
    ``pull`` or ``both``). ``for_`` (the wire key is ``for``) names the
    provider the choices were made for; an empty value means HubSpot.
    """

    activity: CrmActivityLog | None = None
    create_contacts: bool | None = None
    create_companies: bool | None = None
    write_properties: bool | None = None
    positive_reply: CrmReplyOutcome | None = None
    exit_rules: CrmExitRules | None = None
    guards: CrmEnrollmentGuards | None = None
    deal_pipelines: Sequence[str] = []
    display_properties: Sequence[str] = []
    field_map: dict[str, str] = {}
    field_direction: dict[str, str] = {}
    for_: str | None = Field(default=None, alias="for")


class CrmAccount(BaseModel):
    """The connected provider account, read-only.

    ``missing_scopes`` lists permissions the connection lacks for full mode,
    which a reconnect would grant.
    """

    external_id: str | None = None
    name: str | None = None
    app_url: str | None = None
    status: str | None = None
    health: str | None = None
    missing_scopes: Sequence[str] = []


class CrmSettings(BaseModel):
    """The workspace's CRM mode.

    ``provider`` is ``"native"`` (Warmbly's own CRM), ``"hubspot"`` or
    ``"pipedrive"``.
    """

    organization_id: str | None = None
    provider: str | None = None
    connection_id: str | None = None
    config: CrmProviderConfig | None = None
    setup_completed_at: str | None = None
    updated_at: str | None = None
    account: CrmAccount | None = None


class CrmOption(BaseModel):
    """A provider enum value with its label."""

    value: str | None = None
    label: str | None = None


class CrmProperty(BaseModel):
    """A provider contact property a Warmbly field can map to."""

    name: str | None = None
    label: str | None = None
    type: str | None = None
    group_name: str | None = None
    read_only: bool | None = None


class CrmMetadata(BaseModel):
    """The provider vocabulary the pickers render."""

    lifecycle_stages: Sequence[CrmOption] = []
    lead_statuses: Sequence[CrmOption] = []
    task_types: Sequence[CrmOption] = []
    properties: Sequence[CrmProperty] = []
    pipelines: Sequence[CrmOption] = []


class CrmOwner(BaseModel):
    """A provider user who can own records, and the member they map to.

    ``user_pinned`` is ``True`` when the match was set by hand with
    :meth:`Crm.map_owner` rather than by email.
    """

    external_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    user_id: str | None = None
    user_pinned: bool | None = None
    archived: bool | None = None


class CrmCompanyRef(BaseModel):
    """A contact's primary company in the provider."""

    external_id: str | None = None
    name: str | None = None
    domain: str | None = None
    url: str | None = None


class CrmPropertyView(BaseModel):
    """One displayed provider property, labelled."""

    name: str | None = None
    label: str | None = None
    value: str | None = None


class CrmContactView(BaseModel):
    """The provider side of a Warmbly contact.

    ``linked`` is ``False`` when the contact has no record in the provider
    yet (see :meth:`Crm.link_contact`).
    """

    provider: str | None = None
    linked: bool | None = None
    external_id: str | None = None
    url: str | None = None
    owner: CrmOwner | None = None
    lifecycle_stage: CrmOption | None = None
    lead_status: CrmOption | None = None
    company: CrmCompanyRef | None = None
    opted_out: bool | None = None
    properties: Sequence[CrmPropertyView] = []
    synced_at: str | None = None


class CrmSyncJob(BaseModel):
    """One queued or failed sync job. ``status`` mirrors the outbox state."""

    id: str
    organization_id: str | None = None
    provider: str | None = None
    kind: str | None = None
    subject: str | None = None
    status: str | None = None
    attempts: int | None = None
    next_attempt_at: str | None = None
    last_error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    finished_at: str | None = None


class CrmSyncCursor(BaseModel):
    """One incremental pull from the provider."""

    object_type: str | None = None
    cursor_at: str | None = None
    last_run_at: str | None = None
    last_error: str | None = None


class CrmMirrorCounts(BaseModel):
    """How much provider data the workspace mirrors."""

    contacts: int | None = None
    deals: int | None = None
    tasks: int | None = None
    pipelines: int | None = None
    owners: int | None = None


class CrmSyncHealth(BaseModel):
    """The sync health panel: counts, failures and freshness."""

    pending: int | None = None
    failed: int | None = None
    done_24h: int | None = None
    last_synced_at: str | None = None
    cursors: Sequence[CrmSyncCursor] = []
    failures: Sequence[CrmSyncJob] = []
    counts: CrmMirrorCounts | None = None


class CrmSyncAffected(BaseModel):
    """How many failed sync jobs a retry or discard touched."""

    affected: int | None = None


class CrmAck(BaseModel):
    """The acknowledgement of a call that answers without a body.

    The server answers ``204 No Content`` (owner mapping) or ``202 Accepted``
    (sync and backfill start), so no field is ever populated.
    """


class CrmList(BaseModel):
    """A provider contact list Warmbly can import from."""

    external_id: str | None = None
    name: str | None = None
    size: int | None = None
    dynamic: bool | None = None
    updated_at: str | None = None


class CrmImportSkip(BaseModel):
    """One skip reason and how many contacts it removed."""

    reason: str | None = None
    label: str | None = None
    count: int | None = None


class CrmImportPerson(BaseModel):
    """A sample row of an import preview."""

    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None


class CrmImportPreview(BaseModel):
    """Who a list import would bring in and who it would skip.

    ``truncated`` is ``True`` when the list is larger than one import takes.
    """

    list_name: str | None = None
    total: int | None = None
    included: int | None = None
    skipped: Sequence[CrmImportSkip] = []
    sample: Sequence[CrmImportPerson] = []
    truncated: bool | None = None


class CrmImportResult(BaseModel):
    """The contact import draft a list import produced.

    It is finished in the regular import review, like any other import.
    """

    import_id: str | None = None
    preview: CrmImportPreview | None = None


class CrmBackfillPreview(BaseModel):
    """How many Warmbly-only records a backfill would copy to the provider."""

    deals: int | None = None
    tasks: int | None = None
    notes: int | None = None


def _job_selection(ids: Sequence[str] | None) -> dict[str, Any]:
    """Build the body of a sync retry or discard.

    No body key means "every failed job" on the server, and so does an empty
    list, so an empty selection is refused instead of silently widening.
    """
    if ids is None:
        return {}
    if not ids:
        raise ValueError("ids is empty; omit it to act on every failed sync job")
    return {"ids": list(ids)}


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
    ) -> BulkTasksAffected:
        """Write one status and/or priority onto a whole selection of tasks.

        Name the tasks either by id (*tasks*) or as every task matching a search
        (*select_all* with *filters*, minus *exclude*). At least one of *status*
        and *priority* is required. A select-all is capped at 50000 tasks; past
        that the server refuses it and you narrow the filter. The response is the
        count, not the rows. Requires the ``write_crm`` scope.

        Args:
            tasks: The task ids to update.
            select_all: Update every task matching *filters* instead of the ids.
            filters: The same body :meth:`search_tasks` takes. Used with
                *select_all*.
            exclude: Task ids to drop from a *select_all* selection.
            status: ``pending``, ``in_progress``, ``completed`` or ``cancelled``.
            priority: ``low``, ``medium``, ``high`` or ``urgent``.
        """
        if select_all is True and not is_given(filters):
            raise ValueError("select_all=True requires filters")
        return self._patch(
            "/crm/tasks",
            cast_to=BulkTasksAffected,
            body=drop_not_given(
                {
                    "tasks": tasks,
                    "all": select_all,
                    "filters": filters,
                    "exclude": exclude,
                    "status": status,
                    "priority": priority,
                }
            ),
            options=options,
        )

    def bulk_delete_tasks(
        self,
        tasks: Sequence[str] = (),
        *,
        select_all: bool = False,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> BulkTasksAffected:
        """Delete a whole selection of tasks.

        The ids travel as a plain array; with *select_all* the request is a
        selection object instead. Requires the ``write_crm`` scope.

        Args:
            tasks: The task ids to delete.
            select_all: Delete every task matching *filters* instead of the ids.
            filters: The same body :meth:`search_tasks` takes. Used with
                *select_all*.
            exclude: Task ids to drop from a *select_all* selection.
        """
        body: Any = list(tasks)
        if select_all:
            if not is_given(filters):
                raise ValueError(
                    "bulk_delete_tasks(select_all=True) requires filters; "
                    "pass {} to delete every task"
                )
            body = drop_not_given({"all": True, "filters": filters, "exclude": exclude})
        return self._delete(
            "/crm/tasks",
            cast_to=BulkTasksAffected,
            body=body,
            options=options,
        )

    # -- CRM mode (native, HubSpot, Pipedrive) ------------------------------
    # These routes need a CRM provider configured on the instance; without one
    # the server answers 501. Those that read provider data answer 409 or 404
    # with the code ``crm_not_connected`` until the provider is connected and
    # chosen with :meth:`update_settings`.
    def get_settings(self, *, options: RequestOptions | None = None) -> CrmSettings:
        """Read the workspace's CRM mode and connected account.

        Requires the ``read_crm`` scope (API key) or the view-contacts
        permission (member).
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

        Requires the ``integrations`` scope (API key) or the manage-settings
        permission (member). It is a workspace-wide switch, so it is audited.

        Args:
            provider: ``"native"``, ``"hubspot"`` or ``"pipedrive"``.
            connection_id: The integration connection the provider runs on.
            config: The setup choices, in the shape of
                :class:`CrmProviderConfig`. The server validates and bounds it.
            complete_setup: Mark the setup wizard as finished.
        """
        return self._put(
            "/crm/settings",
            cast_to=CrmSettings,
            body=drop_not_given(
                {
                    "provider": provider,
                    "connection_id": connection_id,
                    "config": config,
                    "complete_setup": complete_setup,
                }
            ),
            options=options,
        )

    def get_metadata(self, *, options: RequestOptions | None = None) -> CrmMetadata:
        """Read the provider's lifecycle stages, lead statuses, task types,
        contact properties and pipelines, for pickers.

        Requires the ``read_crm`` scope or the view-contacts permission.
        """
        return self._get("/crm/metadata", cast_to=CrmMetadata, options=options)

    def list_owners(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[CrmOwner]:
        """List the provider's owners and the member each one maps to.

        Returned in full, unpaginated. Requires the ``read_crm`` scope or the
        view-contacts permission.
        """
        return self._get_api_list("/crm/owners", model=CrmOwner, options=options)

    def map_owner(
        self,
        external_id: str,
        *,
        user_id: str | None,
        options: RequestOptions | None = None,
    ) -> CrmAck:
        """Pin a provider owner to a workspace member, or clear the match.

        Answers ``204 No Content``. Requires the ``integrations`` scope or the
        manage-settings permission.

        Args:
            external_id: The provider's owner id (max 64 characters).
            user_id: The member's user id, or ``None`` to clear the pin.
        """
        return self._put(
            f"/crm/owners/{external_id}",
            cast_to=CrmAck,
            body={"user_id": user_id},
            options=options,
        )

    def get_sync_health(
        self, *, options: RequestOptions | None = None
    ) -> CrmSyncHealth:
        """Report what is waiting, what failed and when each pull last ran.

        Requires the ``read_crm`` scope or the view-contacts permission.
        """
        return self._get("/crm/sync", cast_to=CrmSyncHealth, options=options)

    def sync_now(self, *, options: RequestOptions | None = None) -> CrmAck:
        """Start a full pull from the provider in the background.

        Answers ``202 Accepted``; a second call within about 30 seconds is
        refused with ``429`` and the code ``crm_sync_running``. Requires the
        ``integrations`` scope or the manage-settings permission.
        """
        return self._post("/crm/sync", cast_to=CrmAck, options=options)

    def retry_sync_failures(
        self,
        ids: Sequence[str] | None = None,
        *,
        options: RequestOptions | None = None,
    ) -> CrmSyncAffected:
        """Requeue failed sync jobs. Requeueing a requeued job changes nothing.

        Requires the ``integrations`` scope or the manage-settings permission.

        Args:
            ids: Up to 500 job ids (see :meth:`get_sync_health`). Omit to
                requeue every failed job. An empty list is refused rather than
                sent, because the server reads it as "all".
        """
        return self._post(
            "/crm/sync/retry",
            cast_to=CrmSyncAffected,
            body=_job_selection(ids),
            options=options,
        )

    def discard_sync_failures(
        self,
        ids: Sequence[str] | None = None,
        *,
        options: RequestOptions | None = None,
    ) -> CrmSyncAffected:
        """Drop failed sync jobs for good.

        Requires the ``integrations`` scope or the manage-settings permission.

        Args:
            ids: Up to 500 job ids (see :meth:`get_sync_health`). Omit to
                discard every failed job. An empty list is refused rather than
                sent, because the server reads it as "all".
        """
        return self._post(
            "/crm/sync/discard",
            cast_to=CrmSyncAffected,
            body=_job_selection(ids),
            options=options,
        )

    def get_backfill_preview(
        self, *, options: RequestOptions | None = None
    ) -> CrmBackfillPreview:
        """Count the Warmbly-only records a switch would copy to the provider.

        Requires the ``integrations`` scope or the manage-settings permission.
        """
        return self._get("/crm/backfill", cast_to=CrmBackfillPreview, options=options)

    def start_backfill(
        self,
        *,
        deals: bool = False,
        tasks: bool = False,
        notes: bool = False,
        options: RequestOptions | None = None,
    ) -> CrmAck:
        """Copy Warmbly's own deals, tasks and notes into the provider once.

        Answers ``202 Accepted``. A second call while one runs is folded into
        it and copied records are never copied twice, so a retry is safe. At
        least one of *deals*, *tasks* and *notes* must be true. Requires the
        ``integrations`` scope or the manage-settings permission.
        """
        return self._post(
            "/crm/backfill",
            cast_to=CrmAck,
            body={"deals": deals, "tasks": tasks, "notes": notes},
            options=options,
        )

    # -- the provider side of a contact --------------------------------------
    def retrieve_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Read the provider side of a contact: owner, lifecycle stage, lead
        status, company and the chosen properties.

        Requires the ``read_crm`` scope or the view-contacts permission.
        """
        return self._get(
            f"/crm/contacts/{contact_id}", cast_to=CrmContactView, options=options
        )

    def refresh_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Pull a contact's provider record, deals, tasks and notes now.

        Debounced per contact on the server, so it is safe to call whenever a
        panel opens. It needs only read access: the ``read_crm`` scope or the
        view-contacts permission.
        """
        return self._post(
            f"/crm/contacts/{contact_id}/refresh",
            cast_to=CrmContactView,
            options=options,
        )

    def link_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Find the contact in the provider, or create it there.

        Audited. Requires the ``write_crm`` scope or the manage-contacts
        permission.
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

        Fields left out are not touched. Each value is at most 100 characters;
        valid values come from :meth:`get_metadata` and :meth:`list_owners`.
        Audited. Requires the ``write_crm`` scope or the manage-contacts
        permission.
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

    # -- importing a provider list -------------------------------------------
    def list_lists(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CrmList]:
        """List the provider's contact lists that can be imported (auto-paging).

        Requires the ``read_crm`` scope and the manage-contacts permission.

        Args:
            q: Filter by name (max 200 characters).
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/crm/lists",
            model=CrmList,
            query=drop_not_given({"q": q, "limit": limit, "cursor": cursor}),
            options=options,
        )

    def preview_list_import(
        self,
        *,
        list_id: str,
        apply_guards: bool = False,
        options: RequestOptions | None = None,
    ) -> CrmImportPreview:
        """Count who importing a list would bring in and who it would skip.

        Creates nothing. Requires the ``write_contacts`` scope and the
        manage-contacts permission.

        Args:
            list_id: A list's ``external_id`` (max 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return self._post(
            "/crm/lists/preview",
            cast_to=CrmImportPreview,
            body={"list_id": list_id, "apply_guards": apply_guards},
            options=options,
        )

    def import_list(
        self,
        *,
        list_id: str,
        apply_guards: bool = False,
        options: RequestOptions | None = None,
    ) -> CrmImportResult:
        """Turn a provider list into a contact import draft.

        Answers ``201 Created``. The draft is finished in the regular import
        review. The server answers ``401`` when it cannot tell which user starts
        the import. Audited.
        Requires the ``write_contacts`` scope and the manage-contacts
        permission.

        Args:
            list_id: A list's ``external_id`` (max 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return self._post(
            "/crm/lists/import",
            cast_to=CrmImportResult,
            body={"list_id": list_id, "apply_guards": apply_guards},
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
    ) -> BulkTasksAffected:
        """Write one status and/or priority onto a whole selection of tasks.

        Name the tasks either by id (*tasks*) or as every task matching a search
        (*select_all* with *filters*, minus *exclude*). At least one of *status*
        and *priority* is required. A select-all is capped at 50000 tasks; past
        that the server refuses it and you narrow the filter. The response is the
        count, not the rows. Requires the ``write_crm`` scope.

        Args:
            tasks: The task ids to update.
            select_all: Update every task matching *filters* instead of the ids.
            filters: The same body :meth:`search_tasks` takes. Used with
                *select_all*.
            exclude: Task ids to drop from a *select_all* selection.
            status: ``pending``, ``in_progress``, ``completed`` or ``cancelled``.
            priority: ``low``, ``medium``, ``high`` or ``urgent``.
        """
        if select_all is True and not is_given(filters):
            raise ValueError("select_all=True requires filters")
        return await self._patch(
            "/crm/tasks",
            cast_to=BulkTasksAffected,
            body=drop_not_given(
                {
                    "tasks": tasks,
                    "all": select_all,
                    "filters": filters,
                    "exclude": exclude,
                    "status": status,
                    "priority": priority,
                }
            ),
            options=options,
        )

    async def bulk_delete_tasks(
        self,
        tasks: Sequence[str] = (),
        *,
        select_all: bool = False,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> BulkTasksAffected:
        """Delete a whole selection of tasks.

        The ids travel as a plain array; with *select_all* the request is a
        selection object instead. Requires the ``write_crm`` scope.

        Args:
            tasks: The task ids to delete.
            select_all: Delete every task matching *filters* instead of the ids.
            filters: The same body :meth:`search_tasks` takes. Used with
                *select_all*.
            exclude: Task ids to drop from a *select_all* selection.
        """
        body: Any = list(tasks)
        if select_all:
            if not is_given(filters):
                raise ValueError(
                    "bulk_delete_tasks(select_all=True) requires filters; "
                    "pass {} to delete every task"
                )
            body = drop_not_given({"all": True, "filters": filters, "exclude": exclude})
        return await self._delete(
            "/crm/tasks",
            cast_to=BulkTasksAffected,
            body=body,
            options=options,
        )

    # -- CRM mode (native, HubSpot, Pipedrive) ------------------------------
    # These routes need a CRM provider configured on the instance; without one
    # the server answers 501. Those that read provider data answer 409 or 404
    # with the code ``crm_not_connected`` until the provider is connected and
    # chosen with :meth:`update_settings`.
    async def get_settings(
        self, *, options: RequestOptions | None = None
    ) -> CrmSettings:
        """Read the workspace's CRM mode and connected account.

        Requires the ``read_crm`` scope (API key) or the view-contacts
        permission (member).
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

        Requires the ``integrations`` scope (API key) or the manage-settings
        permission (member). It is a workspace-wide switch, so it is audited.

        Args:
            provider: ``"native"``, ``"hubspot"`` or ``"pipedrive"``.
            connection_id: The integration connection the provider runs on.
            config: The setup choices, in the shape of
                :class:`CrmProviderConfig`. The server validates and bounds it.
            complete_setup: Mark the setup wizard as finished.
        """
        return await self._put(
            "/crm/settings",
            cast_to=CrmSettings,
            body=drop_not_given(
                {
                    "provider": provider,
                    "connection_id": connection_id,
                    "config": config,
                    "complete_setup": complete_setup,
                }
            ),
            options=options,
        )

    async def get_metadata(
        self, *, options: RequestOptions | None = None
    ) -> CrmMetadata:
        """Read the provider's lifecycle stages, lead statuses, task types,
        contact properties and pipelines, for pickers.

        Requires the ``read_crm`` scope or the view-contacts permission.
        """
        return await self._get("/crm/metadata", cast_to=CrmMetadata, options=options)

    def list_owners(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[CrmOwner]:
        """List the provider's owners and the member each one maps to.

        Returned in full, unpaginated. Requires the ``read_crm`` scope or the
        view-contacts permission.
        """
        return self._get_api_list("/crm/owners", model=CrmOwner, options=options)

    async def map_owner(
        self,
        external_id: str,
        *,
        user_id: str | None,
        options: RequestOptions | None = None,
    ) -> CrmAck:
        """Pin a provider owner to a workspace member, or clear the match.

        Answers ``204 No Content``. Requires the ``integrations`` scope or the
        manage-settings permission.

        Args:
            external_id: The provider's owner id (max 64 characters).
            user_id: The member's user id, or ``None`` to clear the pin.
        """
        return await self._put(
            f"/crm/owners/{external_id}",
            cast_to=CrmAck,
            body={"user_id": user_id},
            options=options,
        )

    async def get_sync_health(
        self, *, options: RequestOptions | None = None
    ) -> CrmSyncHealth:
        """Report what is waiting, what failed and when each pull last ran.

        Requires the ``read_crm`` scope or the view-contacts permission.
        """
        return await self._get("/crm/sync", cast_to=CrmSyncHealth, options=options)

    async def sync_now(self, *, options: RequestOptions | None = None) -> CrmAck:
        """Start a full pull from the provider in the background.

        Answers ``202 Accepted``; a second call within about 30 seconds is
        refused with ``429`` and the code ``crm_sync_running``. Requires the
        ``integrations`` scope or the manage-settings permission.
        """
        return await self._post("/crm/sync", cast_to=CrmAck, options=options)

    async def retry_sync_failures(
        self,
        ids: Sequence[str] | None = None,
        *,
        options: RequestOptions | None = None,
    ) -> CrmSyncAffected:
        """Requeue failed sync jobs. Requeueing a requeued job changes nothing.

        Requires the ``integrations`` scope or the manage-settings permission.

        Args:
            ids: Up to 500 job ids (see :meth:`get_sync_health`). Omit to
                requeue every failed job. An empty list is refused rather than
                sent, because the server reads it as "all".
        """
        return await self._post(
            "/crm/sync/retry",
            cast_to=CrmSyncAffected,
            body=_job_selection(ids),
            options=options,
        )

    async def discard_sync_failures(
        self,
        ids: Sequence[str] | None = None,
        *,
        options: RequestOptions | None = None,
    ) -> CrmSyncAffected:
        """Drop failed sync jobs for good.

        Requires the ``integrations`` scope or the manage-settings permission.

        Args:
            ids: Up to 500 job ids (see :meth:`get_sync_health`). Omit to
                discard every failed job. An empty list is refused rather than
                sent, because the server reads it as "all".
        """
        return await self._post(
            "/crm/sync/discard",
            cast_to=CrmSyncAffected,
            body=_job_selection(ids),
            options=options,
        )

    async def get_backfill_preview(
        self, *, options: RequestOptions | None = None
    ) -> CrmBackfillPreview:
        """Count the Warmbly-only records a switch would copy to the provider.

        Requires the ``integrations`` scope or the manage-settings permission.
        """
        return await self._get(
            "/crm/backfill", cast_to=CrmBackfillPreview, options=options
        )

    async def start_backfill(
        self,
        *,
        deals: bool = False,
        tasks: bool = False,
        notes: bool = False,
        options: RequestOptions | None = None,
    ) -> CrmAck:
        """Copy Warmbly's own deals, tasks and notes into the provider once.

        Answers ``202 Accepted``. A second call while one runs is folded into
        it and copied records are never copied twice, so a retry is safe. At
        least one of *deals*, *tasks* and *notes* must be true. Requires the
        ``integrations`` scope or the manage-settings permission.
        """
        return await self._post(
            "/crm/backfill",
            cast_to=CrmAck,
            body={"deals": deals, "tasks": tasks, "notes": notes},
            options=options,
        )

    # -- the provider side of a contact --------------------------------------
    async def retrieve_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Read the provider side of a contact: owner, lifecycle stage, lead
        status, company and the chosen properties.

        Requires the ``read_crm`` scope or the view-contacts permission.
        """
        return await self._get(
            f"/crm/contacts/{contact_id}", cast_to=CrmContactView, options=options
        )

    async def refresh_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Pull a contact's provider record, deals, tasks and notes now.

        Debounced per contact on the server, so it is safe to call whenever a
        panel opens. It needs only read access: the ``read_crm`` scope or the
        view-contacts permission.
        """
        return await self._post(
            f"/crm/contacts/{contact_id}/refresh",
            cast_to=CrmContactView,
            options=options,
        )

    async def link_contact(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> CrmContactView:
        """Find the contact in the provider, or create it there.

        Audited. Requires the ``write_crm`` scope or the manage-contacts
        permission.
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

        Fields left out are not touched. Each value is at most 100 characters;
        valid values come from :meth:`get_metadata` and :meth:`list_owners`.
        Audited. Requires the ``write_crm`` scope or the manage-contacts
        permission.
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

    # -- importing a provider list -------------------------------------------
    def list_lists(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[CrmList]:
        """List the provider's contact lists that can be imported (auto-paging).

        Requires the ``read_crm`` scope and the manage-contacts permission.

        Args:
            q: Filter by name (max 200 characters).
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/crm/lists",
            model=CrmList,
            query=drop_not_given({"q": q, "limit": limit, "cursor": cursor}),
            options=options,
        )

    async def preview_list_import(
        self,
        *,
        list_id: str,
        apply_guards: bool = False,
        options: RequestOptions | None = None,
    ) -> CrmImportPreview:
        """Count who importing a list would bring in and who it would skip.

        Creates nothing. Requires the ``write_contacts`` scope and the
        manage-contacts permission.

        Args:
            list_id: A list's ``external_id`` (max 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return await self._post(
            "/crm/lists/preview",
            cast_to=CrmImportPreview,
            body={"list_id": list_id, "apply_guards": apply_guards},
            options=options,
        )

    async def import_list(
        self,
        *,
        list_id: str,
        apply_guards: bool = False,
        options: RequestOptions | None = None,
    ) -> CrmImportResult:
        """Turn a provider list into a contact import draft.

        Answers ``201 Created``. The draft is finished in the regular import
        review. The server answers ``401`` when it cannot tell which user starts
        the import. Audited.
        Requires the ``write_contacts`` scope and the manage-contacts
        permission.

        Args:
            list_id: A list's ``external_id`` (max 64 characters).
            apply_guards: Drop contacts the workspace's enrolment guards
                exclude.
        """
        return await self._post(
            "/crm/lists/import",
            cast_to=CrmImportResult,
            body={"list_id": list_id, "apply_guards": apply_guards},
            options=options,
        )
