"""The Warmbly realtime gateway.

A WebSocket client for Warmbly's realtime gateway, which streams campaign,
email, contact, account, and bulk-operation events; supports topic presence; and
recovers missed events via sequence-based resume across reconnects. The gateway
speaks a compact JSON frame protocol (a Phoenix Channels v2 transport,
version ``2.0.0``).

Two clients are provided with identical surfaces:

* :class:`AsyncGatewayClient` — the native ``asyncio`` client.
* :class:`GatewayClient` — a blocking facade that runs the async client on a
  background event loop, for use from ordinary synchronous code.

Register handlers with the ``on``/``on_event`` decorators, wait for a single
event with ``wait_for``, then ``connect``, ``subscribe`` to topics, and
``run_forever`` to stream events while reconnects are supervised automatically.

Event names are available as constants on :class:`GatewayEvent`.

Example:
    >>> from warmbly.gateway import AsyncGatewayClient, GatewayEvent
    >>> gw = AsyncGatewayClient(token="wmbly_...")
    >>> @gw.on_event(GatewayEvent.CAMPAIGN_STARTED)
    ... async def _(topic, payload):
    ...     print(payload["campaign_id"])
    >>> await gw.connect()
    >>> await gw.subscribe("org:org_123", intents=["CAMPAIGN"])
    >>> await gw.run_forever()
"""

from __future__ import annotations

from .._exceptions import GatewayError
from ._channel import GatewayPushError
from ._connection import (
    DEFAULT_BASE_URL,
    AsyncGatewayClient,
    FatalDisconnect,
    TransientDisconnect,
)
from ._events import GatewayEvent
from ._phoenix import Frame, PhoenixCodec
from ._sync import GatewayClient

__all__ = [
    "DEFAULT_BASE_URL",
    "AsyncGatewayClient",
    "FatalDisconnect",
    "Frame",
    "GatewayClient",
    "GatewayError",
    "GatewayEvent",
    "GatewayPushError",
    "PhoenixCodec",
    "TransientDisconnect",
]
