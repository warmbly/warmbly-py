"""Event-name constants and the gateway dispatch registry.

:class:`GatewayEvent` collects the realtime event names from the gateway's
event catalog as constants so callers can avoid stringly-typed handler keys.

:class:`EventDispatcher` is the registry behind the ``on``/``on_event``
decorators and ``wait_for``. Handlers are stored in plain ``dict`` maps keyed
either by ``(topic, event)`` (exact) or by ``event`` alone (any topic). The
dispatcher itself performs no I/O and schedules nothing. The connection layer
calls :meth:`EventDispatcher.handlers_for` and runs each handler as its own
task so a single misbehaving handler cannot stall the receive loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

__all__ = ["EventDispatcher", "EventKey", "GatewayEvent", "Handler"]

#: A user event handler. Receives the topic and the event payload.
Handler = Callable[[str, dict[str, Any]], Awaitable[None]]

#: A registry key: either ``(topic, event)`` for an exact match or a bare
#: ``event`` string for an any-topic match.
EventKey = tuple[str, str] | str


class GatewayEvent:
    """Realtime event-name constants from the gateway event catalog.

    These mirror the server's event names verbatim. Unknown events are still
    delivered to ``on_event`` handlers and ``wait_for``, so a server that adds
    an event never needs an SDK upgrade to be observable.

    An ``org:*`` subscription can narrow delivery with ``intents``: the server
    upper-cases the event name, replaces separators with ``_``, and keeps the
    event if any intent token is a substring. ``intents=["CAMPAIGN"]`` therefore
    matches every ``CAMPAIGN_*`` event.
    """

    # Campaign lifecycle.
    CAMPAIGN_CREATED = "CAMPAIGN_CREATED"
    CAMPAIGN_UPDATED = "CAMPAIGN_UPDATED"
    CAMPAIGN_DELETED = "CAMPAIGN_DELETED"
    CAMPAIGN_STARTED = "CAMPAIGN_STARTED"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"
    CAMPAIGN_COMPLETED = "CAMPAIGN_COMPLETED"
    #: A continuous campaign ran out of leads and is waiting for more.
    CAMPAIGN_IDLE = "CAMPAIGN_IDLE"

    # Task lifecycle.
    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_PROGRESS = "TASK_PROGRESS"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"

    # Email / sending events.
    EMAIL_SENT = "EMAIL_SENT"
    EMAIL_FAILED = "EMAIL_FAILED"
    EMAIL_OPENED = "EMAIL_OPENED"
    EMAIL_CLICKED = "EMAIL_CLICKED"
    EMAIL_REPLIED = "EMAIL_REPLIED"
    EMAIL_RECEIVED = "EMAIL_RECEIVED"
    EMAIL_UPDATED = "EMAIL_UPDATED"
    EMAIL_DELETED = "EMAIL_DELETED"

    # Contact events.
    CONTACT_CREATED = "CONTACT_CREATED"
    CONTACT_UPDATED = "CONTACT_UPDATED"
    CONTACT_DELETED = "CONTACT_DELETED"
    CONTACTS_RELOAD = "CONTACTS_RELOAD"

    # Hosted forms and website tracking.
    FORM_SUBMISSION_CREATED = "FORM_SUBMISSION_CREATED"
    PAGE_HIT = "PAGE_HIT"

    # Mailbox events.
    ACCOUNT_CONNECTED = "ACCOUNT_CONNECTED"
    ACCOUNT_DISCONNECTED = "ACCOUNT_DISCONNECTED"
    ACCOUNT_ERROR = "ACCOUNT_ERROR"
    ACCOUNT_SYNCED = "ACCOUNT_SYNCED"
    ACCOUNT_HEALTH_CHANGED = "ACCOUNT_HEALTH_CHANGED"
    #: A mailbox's import progress or fair-use hold changed.
    ACCOUNT_SYNC_STATE = "ACCOUNT_SYNC_STATE"

    # Bulk-operation events.
    BULK_STARTED = "BULK_STARTED"
    BULK_PROGRESS = "BULK_PROGRESS"
    BULK_COMPLETED = "BULK_COMPLETED"
    BULK_FAILED = "BULK_FAILED"

    # Automation events.
    AUTOMATION_CREATED = "AUTOMATION_CREATED"
    AUTOMATION_UPDATED = "AUTOMATION_UPDATED"
    AUTOMATION_DELETED = "AUTOMATION_DELETED"
    AUTOMATION_RUN = "AUTOMATION_RUN"

    # Meetings.
    MEETING_BOOKED = "MEETING_BOOKED"
    MEETING_RESCHEDULED = "MEETING_RESCHEDULED"
    MEETING_CANCELED = "MEETING_CANCELED"

    # AI.
    AI_RESEARCH_PROGRESS = "AI_RESEARCH_PROGRESS"
    AI_DRAFT_READY = "AI_DRAFT_READY"

    # Billing / audit / notifications.
    BILLING_CREDITS_LOW = "BILLING_CREDITS_LOW"
    BILLING_CREDITS_CHANGED = "BILLING_CREDITS_CHANGED"
    AUDIT_CREATED = "AUDIT_CREATED"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"

    # Developer-fired custom events, plus generic severity signals.
    CUSTOM_EVENT = "CUSTOM_EVENT"
    ERROR = "ERROR"
    WARNING = "WARNING"

    PRESENCE_POLICY_UPDATED = "PRESENCE_POLICY_UPDATED"

    # Presence / lifecycle / control frames surfaced to handlers.
    PRESENCE_STATE = "presence_state"
    PRESENCE_DIFF = "presence_diff"
    RATE_LIMITED = "rate_limited"
    RESUMED = "resumed"
    RESUME_FAILED = "resume_failed"


class _Waiter:
    """An internal one-shot waiter created by :meth:`EventDispatcher.wait_for`."""

    __slots__ = ("check", "event", "future")

    def __init__(
        self,
        event: str | None,
        check: Callable[[str, dict[str, Any]], bool] | None,
        future: asyncio.Future[dict[str, Any]],
    ) -> None:
        self.event = event
        self.check = check
        self.future = future


class EventDispatcher:
    """In-memory registry of event handlers and one-shot waiters."""

    def __init__(self) -> None:
        self._exact: dict[tuple[str, str], list[Handler]] = {}
        self._any_topic: dict[str, list[Handler]] = {}
        self._waiters: list[_Waiter] = []

    def register(self, key: EventKey, handler: Handler) -> Handler:
        """Register *handler* under *key*.

        Args:
            key: Either a ``(topic, event)`` tuple for an exact match or a bare
                ``event`` string to match that event on any topic.
            handler: The coroutine function to invoke.

        Returns:
            The handler unchanged, so this can be used as a decorator.
        """
        if isinstance(key, tuple):
            self._exact.setdefault(key, []).append(handler)
        else:
            self._any_topic.setdefault(key, []).append(handler)
        return handler

    def unregister(self, key: EventKey, handler: Handler) -> None:
        """Remove a previously registered *handler* for *key* (no error if absent)."""
        bucket = (
            self._exact.get(key) if isinstance(key, tuple) else self._any_topic.get(key)
        )
        if bucket and handler in bucket:
            bucket.remove(handler)

    def handlers_for(self, topic: str, event: str) -> list[Handler]:
        """Return every handler that should run for ``(topic, event)``."""
        result: list[Handler] = []
        result.extend(self._exact.get((topic, event), ()))
        result.extend(self._any_topic.get(event, ()))
        return result

    def wait_for(
        self,
        event: str | None,
        *,
        check: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> asyncio.Future[dict[str, Any]]:
        """Create a one-shot future resolved by the next matching event.

        Args:
            event: The event name to wait for, or ``None`` to match any event
                (use *check* to narrow).
            check: An optional predicate ``(topic, payload) -> bool`` that must
                return ``True`` for the event to satisfy the wait.

        Returns:
            A future resolving to the matching event's payload.
        """
        future: asyncio.Future[dict[str, Any]] = (
            asyncio.get_running_loop().create_future()
        )
        self._waiters.append(_Waiter(event, check, future))
        return future

    def resolve_waiters(self, topic: str, event: str, payload: dict[str, Any]) -> None:
        """Resolve and drop any one-shot waiters matching ``(topic, event)``."""
        if not self._waiters:
            return
        survivors: list[_Waiter] = []
        for waiter in self._waiters:
            if waiter.future.done():
                continue
            matches_event = waiter.event is None or waiter.event == event
            passes_check = waiter.check is None or waiter.check(topic, payload)
            if matches_event and passes_check:
                waiter.future.set_result(payload)
            else:
                survivors.append(waiter)
        self._waiters = survivors

    def fail_waiters(self, exc: BaseException) -> None:
        """Fail every pending waiter with *exc* (used on fatal disconnect)."""
        for waiter in self._waiters:
            if not waiter.future.done():
                waiter.future.set_exception(exc)
        self._waiters = []
