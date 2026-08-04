"""The ``audit_logs`` resource: the organization's audit trail.

Maps to ``GET /v1/audit-logs``. Every state-changing action taken through the
dashboard, the API, or the AI assistant writes one row here, with the actor,
the entity touched, the originating IP, and the field-level ``changes``.

Reading the trail needs the ``read_audit_logs`` scope.
"""

from __future__ import annotations

from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions

__all__ = [
    "AsyncAuditLogs",
    "AuditLog",
    "AuditLogs",
]


class AuditLog(BaseModel):
    """One entry in the audit trail.

    ``user_id`` is the actor's id; ``actor`` carries their display details when
    the server could resolve them.
    """

    id: str
    org_id: str | None = None
    user_id: str | None = None
    actor: dict[str, Any] | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    changes: dict[str, str] = {}
    metadata: dict[str, str] = {}
    action_date: str | None = None
    timestamp: str | None = None


class AuditLogs(SyncAPIResource):
    """Synchronous ``audit_logs`` resource (read-only)."""

    def list(
        self,
        *,
        actor_id: NotGivenOr[str] = NOT_GIVEN,
        entity_type: NotGivenOr[str] = NOT_GIVEN,
        entity_id: NotGivenOr[str] = NOT_GIVEN,
        action: NotGivenOr[str] = NOT_GIVEN,
        date: NotGivenOr[str] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        end_date: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AuditLog]:
        """List audit-log entries, newest first (auto-paginating).

        Args:
            actor_id: Restrict to actions by one user.
            entity_type: Restrict to one kind of entity.
            entity_id: Restrict to one specific entity.
            action: Restrict to one action verb.
            date: A single day to scope to.
            start_date: Lower bound on the action date.
            end_date: Upper bound on the action date.
            limit: Page size.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/audit-logs",
            model=AuditLog,
            query={
                "actor_id": actor_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "date": date,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )


class AsyncAuditLogs(AsyncAPIResource):
    """Asynchronous ``audit_logs`` resource (read-only)."""

    def list(
        self,
        *,
        actor_id: NotGivenOr[str] = NOT_GIVEN,
        entity_type: NotGivenOr[str] = NOT_GIVEN,
        entity_id: NotGivenOr[str] = NOT_GIVEN,
        action: NotGivenOr[str] = NOT_GIVEN,
        date: NotGivenOr[str] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        end_date: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AuditLog]:
        """List audit-log entries, newest first (auto-paginating).

        Args:
            actor_id: Restrict to actions by one user.
            entity_type: Restrict to one kind of entity.
            entity_id: Restrict to one specific entity.
            action: Restrict to one action verb.
            date: A single day to scope to.
            start_date: Lower bound on the action date.
            end_date: Upper bound on the action date.
            limit: Page size.
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/audit-logs",
            model=AuditLog,
            query={
                "actor_id": actor_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "date": date,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )
