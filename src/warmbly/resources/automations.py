"""The ``automations`` resource: the visual flow builder.

Maps to the ``/v1/automations`` route group. An automation is a trigger event
plus a directed graph of condition and action nodes that fan out across
connected integrations. The graph is the source of truth; node coordinates are
cosmetic and are saved separately by :meth:`Automations.set_layout` so a drag
never rewrites the flow.

:meth:`Automations.test` dry-runs the graph and returns a per-node trace of
what *would* happen, without performing any action.
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
    "AsyncAutomations",
    "Automation",
    "AutomationDeleted",
    "AutomationDryRun",
    "AutomationLayoutSaved",
    "AutomationRun",
    "Automations",
]


class Automation(BaseModel):
    """An automation: a trigger plus its node graph.

    ``inbound_url`` is present for automations triggered by an inbound webhook;
    the token in it is the capability, so treat it as a secret.
    """

    id: str
    organization_id: str | None = None
    name: str | None = None
    enabled: bool | None = None
    trigger_event: str | None = None
    filter: dict[str, Any] | None = None
    graph: dict[str, Any] | None = None
    inbound_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AutomationDeleted(BaseModel):
    """The result of deleting an automation."""

    deleted: bool | None = None


class AutomationLayoutSaved(BaseModel):
    """The acknowledgement of a cosmetic node-position save."""

    ok: bool | None = None


class AutomationRun(BaseModel):
    """One execution of an automation.

    ``node_results`` traces each node in order, so a failed run shows exactly
    where it stopped.
    """

    id: str
    automation_id: str | None = None
    organization_id: str | None = None
    trigger_event: str | None = None
    status: str | None = None
    node_results: Sequence[dict[str, Any]] = []
    error_detail: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


class AutomationDryRun(BaseModel):
    """The result of a dry run: what each node would have done."""

    trace: Sequence[dict[str, Any]] = []
    data: dict[str, Any] | None = None


class Automations(SyncAPIResource):
    """Synchronous ``automations`` resource."""

    def list(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[Automation]:
        """List the organization's automations. Returned in full."""
        return self._get_api_list(
            "/automations",
            model=Automation,
            data_key="automations",
            options=options,
        )

    def create(
        self,
        *,
        name: str,
        trigger_event: str,
        graph: Mapping[str, Any],
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Automation:
        """Create an automation.

        Args:
            name: A human-readable name.
            trigger_event: The event that starts a run.
            graph: ``{"nodes": [...], "edges": [...]}``.
            enabled: Whether it runs immediately.
            filter: A predicate that gates the trigger.
        """
        return self._post(
            "/automations",
            cast_to=Automation,
            body=drop_not_given(
                {
                    "name": name,
                    "trigger_event": trigger_event,
                    "graph": graph,
                    "enabled": enabled,
                    "filter": filter,
                }
            ),
            options=options,
        )

    def retrieve(
        self, automation_id: str, *, options: RequestOptions | None = None
    ) -> Automation:
        """Retrieve a single automation by id."""
        return self._get(
            f"/automations/{automation_id}", cast_to=Automation, options=options
        )

    def update(
        self,
        automation_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        trigger_event: NotGivenOr[str] = NOT_GIVEN,
        graph: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Automation:
        """Update an automation, or toggle it with *enabled*."""
        return self._patch(
            f"/automations/{automation_id}",
            cast_to=Automation,
            body=drop_not_given(
                {
                    "name": name,
                    "trigger_event": trigger_event,
                    "graph": graph,
                    "enabled": enabled,
                    "filter": filter,
                }
            ),
            options=options,
        )

    def delete(
        self, automation_id: str, *, options: RequestOptions | None = None
    ) -> AutomationDeleted:
        """Delete an automation."""
        return self._delete(
            f"/automations/{automation_id}",
            cast_to=AutomationDeleted,
            options=options,
        )

    def set_layout(
        self,
        automation_id: str,
        *,
        positions: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> AutomationLayoutSaved:
        """Persist node coordinates without touching the graph.

        Args:
            positions: One ``{"id", "x", "y"}`` entry per node, max 1000.
        """
        return self._patch(
            f"/automations/{automation_id}/layout",
            cast_to=AutomationLayoutSaved,
            body={"positions": [dict(p) for p in positions]},
            options=options,
        )

    def test(
        self,
        automation_id: str,
        *,
        data: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        skip_node_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AutomationDryRun:
        """Dry-run an automation. Performs no actions.

        Args:
            data: A sample trigger payload. Omit to let the server build one.
            skip_node_ids: Nodes to skip during the trace.
        """
        return self._post(
            f"/automations/{automation_id}/test",
            cast_to=AutomationDryRun,
            body=drop_not_given({"data": data, "skip_node_ids": skip_node_ids}),
            options=options,
        )

    def runs(
        self,
        automation_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AutomationRun]:
        """List an automation's recent runs."""
        return self._get_api_list(
            f"/automations/{automation_id}/runs",
            model=AutomationRun,
            data_key="runs",
            query={"limit": limit},
            options=options,
        )


class AsyncAutomations(AsyncAPIResource):
    """Asynchronous ``automations`` resource."""

    def list(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[Automation]:
        """List the organization's automations. Returned in full."""
        return self._get_api_list(
            "/automations",
            model=Automation,
            data_key="automations",
            options=options,
        )

    async def create(
        self,
        *,
        name: str,
        trigger_event: str,
        graph: Mapping[str, Any],
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Automation:
        """Create an automation.

        Args:
            name: A human-readable name.
            trigger_event: The event that starts a run.
            graph: ``{"nodes": [...], "edges": [...]}``.
            enabled: Whether it runs immediately.
            filter: A predicate that gates the trigger.
        """
        return await self._post(
            "/automations",
            cast_to=Automation,
            body=drop_not_given(
                {
                    "name": name,
                    "trigger_event": trigger_event,
                    "graph": graph,
                    "enabled": enabled,
                    "filter": filter,
                }
            ),
            options=options,
        )

    async def retrieve(
        self, automation_id: str, *, options: RequestOptions | None = None
    ) -> Automation:
        """Retrieve a single automation by id."""
        return await self._get(
            f"/automations/{automation_id}", cast_to=Automation, options=options
        )

    async def update(
        self,
        automation_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        trigger_event: NotGivenOr[str] = NOT_GIVEN,
        graph: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Automation:
        """Update an automation, or toggle it with *enabled*."""
        return await self._patch(
            f"/automations/{automation_id}",
            cast_to=Automation,
            body=drop_not_given(
                {
                    "name": name,
                    "trigger_event": trigger_event,
                    "graph": graph,
                    "enabled": enabled,
                    "filter": filter,
                }
            ),
            options=options,
        )

    async def delete(
        self, automation_id: str, *, options: RequestOptions | None = None
    ) -> AutomationDeleted:
        """Delete an automation."""
        return await self._delete(
            f"/automations/{automation_id}",
            cast_to=AutomationDeleted,
            options=options,
        )

    async def set_layout(
        self,
        automation_id: str,
        *,
        positions: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> AutomationLayoutSaved:
        """Persist node coordinates without touching the graph.

        Args:
            positions: One ``{"id", "x", "y"}`` entry per node, max 1000.
        """
        return await self._patch(
            f"/automations/{automation_id}/layout",
            cast_to=AutomationLayoutSaved,
            body={"positions": [dict(p) for p in positions]},
            options=options,
        )

    async def test(
        self,
        automation_id: str,
        *,
        data: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        skip_node_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AutomationDryRun:
        """Dry-run an automation. Performs no actions.

        Args:
            data: A sample trigger payload. Omit to let the server build one.
            skip_node_ids: Nodes to skip during the trace.
        """
        return await self._post(
            f"/automations/{automation_id}/test",
            cast_to=AutomationDryRun,
            body=drop_not_given({"data": data, "skip_node_ids": skip_node_ids}),
            options=options,
        )

    def runs(
        self,
        automation_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AutomationRun]:
        """List an automation's recent runs."""
        return self._get_api_list(
            f"/automations/{automation_id}/runs",
            model=AutomationRun,
            data_key="runs",
            query={"limit": limit},
            options=options,
        )
