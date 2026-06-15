"""Fixtures for the gateway tests: an ephemeral in-process Phoenix-ish server.

The :class:`FakeGateway` fixture binds a real ``websockets`` server on
``localhost`` at an ephemeral port (port 0), speaks the 5-element frame wire
protocol the client expects, and lets a test inject broadcast frames.

The server handler:

* replies to a ``phx_join`` with a ``phx_reply`` carrying
  ``{status: "ok", response: {seq: 0, resume_supported: true}}``;
* replies to a connection-level ``heartbeat`` with a ``phx_reply`` ``{status:
  "ok"}`` on the reserved ``phoenix`` topic;
* replies to a ``phx_leave`` with an ``ok`` reply; and
* exposes :meth:`FakeGateway.broadcast` so a test can push an arbitrary frame
  (with a ``None`` ref, like a real server broadcast) to every connected client.

Everything is pure ``websockets`` + the wire codec under test; there is no
HTTP/httpx and no real network.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from warmbly.gateway._phoenix import (
    EVENT_HEARTBEAT,
    EVENT_JOIN,
    EVENT_LEAVE,
    EVENT_REPLY,
    PHOENIX_TOPIC,
    decode,
)


class FakeGateway:
    """A tiny in-process realtime gateway used by the integration tests."""

    def __init__(self) -> None:
        self._server: Any = None
        self.host: str = "localhost"
        self.port: int = 0
        #: Every live client connection, so the test can broadcast to all.
        self.connections: set[ServerConnection] = set()
        #: Decoded frames received from clients, for assertions.
        self.received: list[Any] = []
        #: Join params seen on the most recent join, keyed by topic.
        self.join_params: dict[str, dict[str, Any]] = {}
        #: Resolves once at least one client has completed a join.
        self.joined = asyncio.Event()

    @property
    def base_url(self) -> str:
        """The ``ws://`` base URL the client should connect to."""
        return f"ws://{self.host}:{self.port}"

    async def start(self) -> None:
        self._server = await serve(self._handler, self.host, 0)
        # Resolve the ephemeral port that was actually bound.
        sock = next(iter(self._server.sockets))
        self.port = sock.getsockname()[1]

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handler(self, connection: ServerConnection) -> None:
        self.connections.add(connection)
        try:
            async for raw in connection:
                await self._on_frame(connection, raw)
        finally:
            self.connections.discard(connection)

    async def _on_frame(self, connection: ServerConnection, raw: Any) -> None:
        frame = decode(raw)
        self.received.append(frame)

        if frame.event == EVENT_HEARTBEAT:
            reply = [None, frame.ref, PHOENIX_TOPIC, EVENT_REPLY, {"status": "ok"}]
            await connection.send(json.dumps(reply))
            return

        if frame.event == EVENT_JOIN:
            self.join_params[frame.topic] = frame.payload
            reply = [
                frame.join_ref,
                frame.ref,
                frame.topic,
                EVENT_REPLY,
                {
                    "status": "ok",
                    "response": {"seq": 0, "resume_supported": True},
                },
            ]
            await connection.send(json.dumps(reply))
            self.joined.set()
            return

        if frame.event == EVENT_LEAVE:
            reply = [
                frame.join_ref,
                frame.ref,
                frame.topic,
                EVENT_REPLY,
                {"status": "ok", "response": {}},
            ]
            await connection.send(json.dumps(reply))
            return

        # Any other client push: ack it so push() callers resolve.
        reply = [
            frame.join_ref,
            frame.ref,
            frame.topic,
            EVENT_REPLY,
            {"status": "ok", "response": {}},
        ]
        await connection.send(json.dumps(reply))

    async def broadcast(
        self,
        topic: str,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Send a server-originated broadcast (``None`` ref) to all clients."""
        frame = [None, None, topic, event, payload or {}]
        raw = json.dumps(frame)
        for connection in list(self.connections):
            await connection.send(raw)


@pytest.fixture
def anyio_backend() -> str:
    """Run AnyIO-marked async tests on asyncio (the client is asyncio-native)."""
    return "asyncio"


@pytest.fixture
async def fake_gateway() -> AsyncIterator[FakeGateway]:
    """Start an ephemeral in-process gateway and tear it down after the test."""
    gateway = FakeGateway()
    await gateway.start()
    try:
        yield gateway
    finally:
        await gateway.stop()
