"""The ``tasks`` resource: the send-task dead-letter queue.

Maps to the ``/v1/tasks/dlq`` routes. A send task that exhausts its attempts
lands here with the error that killed it, rather than disappearing. Replaying
one re-dispatches real mail, which is why the endpoint requires the
``send_campaigns`` scope rather than a read scope.
"""

from __future__ import annotations

from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions

__all__ = [
    "AsyncTasks",
    "DeadLetter",
    "DeadLetterReplayed",
    "Tasks",
]


class DeadLetter(BaseModel):
    """A send task that exhausted its retries."""

    id: str
    task_id: str | None = None
    task_type: str | None = None
    payload: dict[str, Any] | None = None
    last_error: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None
    status: str | None = None
    next_retry_at: str | None = None
    replayed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DeadLetterReplayed(BaseModel):
    """The result of re-queueing a dead-lettered task."""

    status: str | None = None


class Tasks(SyncAPIResource):
    """Synchronous ``tasks`` resource (dead-letter queue)."""

    def list_dead_letters(
        self,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[DeadLetter]:
        """List dead-lettered send tasks.

        Args:
            status: Restrict to one status.
            limit: Page size (1-200; the server defaults to 100).
        """
        return self._get_api_list(
            "/tasks/dlq",
            model=DeadLetter,
            query={"status": status, "limit": limit},
            options=options,
        )

    def replay(
        self, dead_letter_id: str, *, options: RequestOptions | None = None
    ) -> DeadLetterReplayed:
        """Re-queue a dead-lettered task. This dispatches real mail."""
        return self._post(
            f"/tasks/dlq/{dead_letter_id}/replay",
            cast_to=DeadLetterReplayed,
            options=options,
        )


class AsyncTasks(AsyncAPIResource):
    """Asynchronous ``tasks`` resource (dead-letter queue)."""

    def list_dead_letters(
        self,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[DeadLetter]:
        """List dead-lettered send tasks.

        Args:
            status: Restrict to one status.
            limit: Page size (1-200; the server defaults to 100).
        """
        return self._get_api_list(
            "/tasks/dlq",
            model=DeadLetter,
            query={"status": status, "limit": limit},
            options=options,
        )

    async def replay(
        self, dead_letter_id: str, *, options: RequestOptions | None = None
    ) -> DeadLetterReplayed:
        """Re-queue a dead-lettered task. This dispatches real mail."""
        return await self._post(
            f"/tasks/dlq/{dead_letter_id}/replay",
            cast_to=DeadLetterReplayed,
            options=options,
        )
