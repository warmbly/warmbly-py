"""Per-topic channel state and reply correlation.

A :class:`Channel` is the client-side handle for one subscribed topic. It holds
the desired join parameters (so the topic can be transparently re-joined after a
reconnect or a server-side ``phx_error``/``phx_close``), the current join
reference, and the join lifecycle state.

Reply correlation is handled by :class:`PendingReplies`: every push carries a
unique ``ref`` and the sender awaits a future that the receive loop resolves
when the matching ``phx_reply`` arrives. A reply with ``status == "ok"``
resolves the future with its ``response`` object; ``status == "error"`` fails it
with a :class:`~warmbly._exceptions.GatewayError` carrying the payload.

These objects are protocol state only. Sending and receiving happen in the
connection layer.
"""

from __future__ import annotations

import asyncio
from typing import Any

from .._exceptions import GatewayError

__all__ = ["Channel", "ChannelState", "GatewayPushError", "PendingReplies"]


class GatewayPushError(GatewayError):
    """Raised when a push or join is rejected with ``status == "error"``.

    Attributes:
        topic: The topic the rejected push targeted.
        event: The event that was rejected.
        response: The server's error ``response`` object, when provided.
    """

    topic: str
    event: str
    response: dict[str, Any]

    def __init__(self, topic: str, event: str, response: dict[str, Any]) -> None:
        reason = response.get("reason") or response.get("error") or "error"
        super().__init__(f"gateway rejected {event!r} on {topic!r}: {reason}")
        self.topic = topic
        self.event = event
        self.response = response


class ChannelState:
    """The join lifecycle states a :class:`Channel` moves through."""

    CLOSED = "closed"
    JOINING = "joining"
    JOINED = "joined"
    ERRORED = "errored"


class Channel:
    """Client-side state for a single subscribed topic."""

    def __init__(
        self,
        topic: str,
        params: dict[str, Any],
        *,
        resume: bool = True,
    ) -> None:
        self.topic = topic
        self.params = params
        self.resume = resume
        self.join_ref: str | None = None
        self.state: str = ChannelState.CLOSED

    def mark_joining(self, join_ref: str) -> None:
        """Record that a join with *join_ref* is in flight."""
        self.join_ref = join_ref
        self.state = ChannelState.JOINING

    def mark_joined(self) -> None:
        """Record a successful join."""
        self.state = ChannelState.JOINED

    def mark_errored(self) -> None:
        """Record that the channel has errored and needs rejoining."""
        self.state = ChannelState.ERRORED

    def mark_closed(self) -> None:
        """Record that the channel is closed."""
        self.state = ChannelState.CLOSED
        self.join_ref = None

    @property
    def is_joined(self) -> bool:
        """Whether the channel is currently joined."""
        return self.state == ChannelState.JOINED


class PendingReplies:
    """Tracks in-flight pushes awaiting their ``phx_reply`` keyed by ``ref``."""

    def __init__(self) -> None:
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}

    def create(self, ref: str) -> asyncio.Future[dict[str, Any]]:
        """Create and register a future for the reply to *ref*."""
        future: asyncio.Future[dict[str, Any]] = (
            asyncio.get_running_loop().create_future()
        )
        self._pending[ref] = future
        return future

    def resolve(
        self, ref: str, topic: str, event: str, payload: dict[str, Any]
    ) -> bool:
        """Resolve the pending future for *ref* from a ``phx_reply`` payload.

        Args:
            ref: The reply reference.
            topic: The topic the reply arrived on (for error context).
            event: The originating event name (for error context).
            payload: The ``phx_reply`` payload (``{status, response}``).

        Returns:
            ``True`` if a pending future was found and resolved.
        """
        future = self._pending.pop(ref, None)
        if future is None or future.done():
            return future is not None
        status = payload.get("status")
        response = payload.get("response")
        response_dict: dict[str, Any] = response if isinstance(response, dict) else {}
        if status == "ok":
            future.set_result(response_dict)
        else:
            future.set_exception(GatewayPushError(topic, event, response_dict))
        return True

    def fail_all(self, exc: BaseException) -> None:
        """Fail every pending future with *exc* (used on disconnect)."""
        for future in self._pending.values():
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()
