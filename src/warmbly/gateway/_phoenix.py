"""The Warmbly realtime wire codec.

This is the pure, I/O-free serializer for the realtime gateway's wire protocol.
The gateway speaks a compact 5-element JSON frame protocol (a Phoenix Channels
v2 transport, version string ``2.0.0``); this module encodes and decodes those
frames and hands out the monotonic reference counters the protocol requires.

A frame is a JSON array of exactly five elements::

    [join_ref, ref, topic, event, payload]

``join_ref`` ties a message to a particular channel-join lifetime (it is
``None`` for connection-level messages such as the heartbeat and for
server-originated broadcasts); ``ref`` is a per-message id used to correlate a
push with its reply; ``topic`` is the channel name; ``event`` is the event name;
and ``payload`` is an arbitrary JSON object.

The codec is deliberately free of any network or async code so it can be unit
tested in isolation: ``decode(encode(frame))`` round-trips exactly.
"""

from __future__ import annotations

import itertools
import json
from typing import Any, NamedTuple

__all__ = [
    "EVENT_CLOSE",
    "EVENT_ERROR",
    "EVENT_HEARTBEAT",
    "EVENT_JOIN",
    "EVENT_LEAVE",
    "EVENT_REPLY",
    "PHOENIX_TOPIC",
    "VSN",
    "Frame",
    "PhoenixCodec",
]

#: The protocol version advertised in the connect query string.
VSN = "2.0.0"

#: The reserved topic used for connection-level heartbeat messages.
PHOENIX_TOPIC = "phoenix"

# Reserved channel-lifecycle event names.
EVENT_HEARTBEAT = "heartbeat"
EVENT_JOIN = "phx_join"
EVENT_LEAVE = "phx_leave"
EVENT_REPLY = "phx_reply"
EVENT_ERROR = "phx_error"
EVENT_CLOSE = "phx_close"


class Frame(NamedTuple):
    """A decoded wire frame.

    Attributes:
        join_ref: The join reference, or ``None`` for connection-level and
            server-broadcast frames.
        ref: The message reference used to correlate replies, or ``None`` for
            unsolicited server broadcasts.
        topic: The channel topic the frame belongs to.
        event: The event name.
        payload: The frame payload (an arbitrary JSON object).
    """

    join_ref: str | None
    ref: str | None
    topic: str
    event: str
    payload: dict[str, Any]


def encode(frame: Frame) -> str:
    """Serialize a :class:`Frame` to its JSON wire string.

    Args:
        frame: The frame to encode.

    Returns:
        The compact JSON array string ``[join_ref, ref, topic, event, payload]``.
    """
    return json.dumps(
        [frame.join_ref, frame.ref, frame.topic, frame.event, frame.payload],
        separators=(",", ":"),
    )


def decode(raw: str | bytes) -> Frame:
    """Parse a JSON wire string into a :class:`Frame`.

    Args:
        raw: The raw text (or bytes) frame received from the gateway.

    Returns:
        The decoded :class:`Frame`.

    Raises:
        ValueError: If *raw* is not a 5-element JSON array.
    """
    data = json.loads(raw)
    if not isinstance(data, list) or len(data) != 5:
        raise ValueError("malformed gateway frame: expected a 5-element array")
    join_ref, ref, topic, event, payload = data
    if not isinstance(payload, dict):
        payload = {} if payload is None else {"_": payload}
    return Frame(
        join_ref=None if join_ref is None else str(join_ref),
        ref=None if ref is None else str(ref),
        topic=str(topic),
        event=str(event),
        payload=payload,
    )


class PhoenixCodec:
    """Stateful helper that mints references and builds outbound frames.

    Holds the two monotonic counters the protocol relies on — a per-message
    ``ref`` and a per-join ``join_ref`` — and offers convenience builders for
    the join, leave, push, and heartbeat frames. It is pure and side-effect
    free apart from advancing its internal counters.
    """

    def __init__(self) -> None:
        self._ref_counter = itertools.count(1)
        self._join_ref_counter = itertools.count(1)

    def next_ref(self) -> str:
        """Return the next monotonic message reference."""
        return str(next(self._ref_counter))

    def next_join_ref(self) -> str:
        """Return the next monotonic join reference."""
        return str(next(self._join_ref_counter))

    def join(
        self, topic: str, params: dict[str, Any] | None = None
    ) -> tuple[str, str, str]:
        """Build a channel-join frame.

        Args:
            topic: The topic to join.
            params: Optional join parameters.

        Returns:
            A tuple of ``(join_ref, ref, encoded_frame)``. Retain ``join_ref``
            and ``ref`` to correlate the resulting reply.
        """
        join_ref = self.next_join_ref()
        ref = self.next_ref()
        frame = Frame(join_ref, ref, topic, EVENT_JOIN, params or {})
        return join_ref, ref, encode(frame)

    def leave(self, topic: str, join_ref: str | None = None) -> tuple[str, str]:
        """Build a channel-leave frame.

        Args:
            topic: The topic to leave.
            join_ref: The join reference of the channel being left, if known.

        Returns:
            A tuple of ``(ref, encoded_frame)``.
        """
        ref = self.next_ref()
        frame = Frame(join_ref, ref, topic, EVENT_LEAVE, {})
        return ref, encode(frame)

    def push(
        self,
        topic: str,
        event: str,
        payload: dict[str, Any] | None = None,
        join_ref: str | None = None,
    ) -> tuple[str, str]:
        """Build an arbitrary push frame.

        Args:
            topic: The topic to push to.
            event: The event name.
            payload: The payload to send.
            join_ref: The join reference of the owning channel, if known.

        Returns:
            A tuple of ``(ref, encoded_frame)``.
        """
        ref = self.next_ref()
        frame = Frame(join_ref, ref, topic, event, payload or {})
        return ref, encode(frame)

    def heartbeat(self) -> tuple[str, str]:
        """Build a connection-level heartbeat frame.

        Returns:
            A tuple of ``(ref, encoded_frame)`` targeting the reserved
            ``phoenix`` topic with a ``None`` join reference.
        """
        ref = self.next_ref()
        frame = Frame(None, ref, PHOENIX_TOPIC, EVENT_HEARTBEAT, {})
        return ref, encode(frame)
