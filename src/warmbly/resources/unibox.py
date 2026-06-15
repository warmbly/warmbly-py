"""The ``unibox`` resource — unified inbox threads and replies.

Maps to the ``/v1/unibox`` route group. A thread groups related messages; you
can list threads, fetch a single thread, reply to a thread, and mark a thread
as read. The exact thread/message payloads are not fully enumerated in the
contract, so the models below are permissive (``extra="allow"`` via
:class:`~warmbly._models.BaseModel`).
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
    "AsyncUnibox",
    "Message",
    "Thread",
    "Unibox",
]


class Message(BaseModel):
    """A single message within a unibox thread (permissive)."""

    id: str
    thread_id: str | None = None
    organization_id: str | None = None
    email_account_id: str | None = None
    from_: str | None = None
    to: Sequence[str] = []
    subject: str | None = None
    body: str | None = None
    direction: str | None = None
    is_read: bool | None = None
    sent_at: str | None = None
    received_at: str | None = None
    created_at: str | None = None


class Thread(BaseModel):
    """A unibox conversation thread (permissive)."""

    id: str
    organization_id: str | None = None
    email_account_id: str | None = None
    contact_id: str | None = None
    subject: str | None = None
    snippet: str | None = None
    status: str | None = None
    is_read: bool | None = None
    message_count: int | None = None
    messages: Sequence[Message] = []
    last_message_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Unibox(SyncAPIResource):
    """Synchronous ``unibox`` resource (threads, replies)."""

    def list_threads(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Thread]:
        """List unibox threads (auto-paginating)."""
        return self._get_api_list(
            "/unibox/threads",
            model=Thread,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_thread(
        self, thread_id: str, *, options: RequestOptions | None = None
    ) -> Thread:
        """Retrieve a single thread (with its messages) by id."""
        return self._get(
            f"/unibox/threads/{thread_id}", cast_to=Thread, options=options
        )

    def reply(
        self,
        thread_id: str,
        *,
        body: str,
        options: RequestOptions | None = None,
    ) -> Message:
        """Reply to a thread.

        Args:
            thread_id: The thread to reply to.
            body: The reply body (HTML or text).
        """
        request_body: dict[str, Any] = drop_not_given({"body": body})
        return self._post(
            f"/unibox/threads/{thread_id}/reply",
            cast_to=Message,
            body=request_body,
            options=options,
        )

    def mark_read(
        self, thread_id: str, *, options: RequestOptions | None = None
    ) -> Thread:
        """Mark a thread as read."""
        return self._post(
            f"/unibox/threads/{thread_id}/read", cast_to=Thread, options=options
        )


class AsyncUnibox(AsyncAPIResource):
    """Asynchronous ``unibox`` resource (threads, replies)."""

    def list_threads(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[Thread]:
        """List unibox threads (auto-paginating)."""
        return self._get_api_list(
            "/unibox/threads",
            model=Thread,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_thread(
        self, thread_id: str, *, options: RequestOptions | None = None
    ) -> Thread:
        """Retrieve a single thread (with its messages) by id."""
        return await self._get(
            f"/unibox/threads/{thread_id}", cast_to=Thread, options=options
        )

    async def reply(
        self,
        thread_id: str,
        *,
        body: str,
        options: RequestOptions | None = None,
    ) -> Message:
        """Reply to a thread.

        Args:
            thread_id: The thread to reply to.
            body: The reply body (HTML or text).
        """
        request_body: dict[str, Any] = drop_not_given({"body": body})
        return await self._post(
            f"/unibox/threads/{thread_id}/reply",
            cast_to=Message,
            body=request_body,
            options=options,
        )

    async def mark_read(
        self, thread_id: str, *, options: RequestOptions | None = None
    ) -> Thread:
        """Mark a thread as read."""
        return await self._post(
            f"/unibox/threads/{thread_id}/read", cast_to=Thread, options=options
        )
