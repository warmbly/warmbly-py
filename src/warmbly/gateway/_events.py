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

    These mirror the server's event names verbatim. The set is intentionally
    not exhaustive of every possible event (unknown events are still
    delivered to ``on_event`` handlers and ``wait_for``) but it covers the
    common campaign, email, contact, account/warmup, bulk, presence, and
    membership events.
    """

    # Campaign lifecycle.
    CAMPAIGN_STARTED = "CAMPAIGN_STARTED"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"
    CAMPAIGN_COMPLETED = "CAMPAIGN_COMPLETED"
    CAMPAIGN_PROGRESS = "CAMPAIGN_PROGRESS"
    CAMPAIGN_STATUS_CHANGED = "CAMPAIGN_STATUS_CHANGED"
    TASK_PROGRESS = "TASK_PROGRESS"

    # Email / sending events.
    EMAIL_SENT = "EMAIL_SENT"
    EMAIL_OPENED = "EMAIL_OPENED"
    EMAIL_CLICKED = "EMAIL_CLICKED"
    EMAIL_REPLIED = "EMAIL_REPLIED"
    EMAIL_BOUNCED = "EMAIL_BOUNCED"
    EMAIL_RECEIVED = "EMAIL_RECEIVED"
    EMAIL_UPDATED = "EMAIL_UPDATED"
    EMAIL_DELETED = "EMAIL_DELETED"
    INBOX = "INBOX"

    # Contact events.
    CONTACT_CREATED = "CONTACT_CREATED"
    CONTACT_UPDATED = "CONTACT_UPDATED"
    CONTACT_DELETED = "CONTACT_DELETED"

    # Account / warmup events.
    ACCOUNT_CONNECTED = "ACCOUNT_CONNECTED"
    ACCOUNT_DISCONNECTED = "ACCOUNT_DISCONNECTED"
    ACCOUNT_ERROR = "ACCOUNT_ERROR"
    WARMUP_PROGRESS = "WARMUP_PROGRESS"

    # Bulk-operation events.
    BULK_STARTED = "BULK_STARTED"
    BULK_PROGRESS = "BULK_PROGRESS"
    BULK_COMPLETED = "BULK_COMPLETED"

    # Membership / billing / settings.
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_REMOVED = "MEMBER_REMOVED"
    INVITATION_SENT = "INVITATION_SENT"
    SUBSCRIPTION_UPDATED = "SUBSCRIPTION_UPDATED"
    BILLING_UPDATED = "BILLING_UPDATED"
    SETTINGS_UPDATED = "SETTINGS_UPDATED"
    CUSTOM_EVENT = "CUSTOM_EVENT"
    PRESENCE_POLICY_UPDATED = "PRESENCE_POLICY_UPDATED"

    # Presence / lifecycle / control frames surfaced to handlers.
    PRESENCE_STATE = "presence_state"
    PRESENCE_DIFF = "presence_diff"
    RATE_LIMITED = "rate_limited"


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
