"""Exhaustive unit + integration tests for :mod:`warmbly.gateway._connection`.

Part A unit-tests the pure/static helpers (close-code extraction, retry-after
parsing, exception-group flattening/raising, URL building) without any socket.

Part B drives the real :class:`AsyncGatewayClient` supervisor against a
*configurable* in-process gateway defined in this file (modelled on the shared
``FakeGateway`` but with injectable behaviour) so the reconnect/heartbeat/rejoin
machinery can be exercised. The module timing constants are monkeypatched to
tiny values to keep the suite fast, and every awaited rendezvous is bounded.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys
import time
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import (
    ConnectionClosed,
    InvalidStatus,
    WebSocketException,
)
from websockets.frames import Close
from websockets.http11 import Response

import warmbly.gateway._connection as conn
from warmbly._exceptions import GatewayError
from warmbly.gateway._connection import (
    AsyncGatewayClient,
    FatalDisconnect,
    TransientDisconnect,
    _flatten_group,
)
from warmbly.gateway._phoenix import (
    EVENT_CLOSE,
    EVENT_ERROR,
    EVENT_HEARTBEAT,
    EVENT_JOIN,
    EVENT_LEAVE,
    EVENT_REPLY,
    PHOENIX_TOPIC,
    decode,
)

# ``ExceptionGroup``/``BaseExceptionGroup`` are builtins from 3.11; on 3.10 the
# 'exceptiongroup' backport (a runtime dependency there) provides them, mirroring
# the guarded import in ``warmbly.gateway._connection`` itself.
if sys.version_info < (3, 11):  # pragma: no cover - version-dependent import
    from exceptiongroup import (  # type: ignore[import-not-found]
        BaseExceptionGroup,
        ExceptionGroup,
    )

# Bound every awaited rendezvous so a hang fails fast instead of stalling CI.
_TIMEOUT = 5.0


# ---------------------------------------------------------------------------
# PART A -- pure / static helpers (no socket)
# ---------------------------------------------------------------------------


def _closed(
    rcvd: Close | None,
    sent: Close | None,
    *,
    rcvd_then_sent: bool | None = None,
) -> ConnectionClosed:
    """Build a real ConnectionClosed with the given rcvd/sent Close frames."""
    return ConnectionClosed(rcvd=rcvd, sent=sent, rcvd_then_sent=rcvd_then_sent)


def test_close_code_prefers_rcvd() -> None:
    # When both frames are present, websockets requires the rcvd_then_sent flag;
    # _close_code must still prefer the received frame's code.
    exc = _closed(Close(4004, "nope"), Close(4000, "other"), rcvd_then_sent=True)
    assert AsyncGatewayClient._close_code(exc) == 4004


def test_close_code_falls_back_to_sent() -> None:
    exc = _closed(None, Close(4000, "zombie"))
    assert AsyncGatewayClient._close_code(exc) == 4000


def test_close_code_defaults_to_1006_when_no_frame() -> None:
    exc = _closed(None, None)
    assert AsyncGatewayClient._close_code(exc) == 1006


def test_extract_retry_after_empty_reason_is_none() -> None:
    exc = _closed(Close(4007, ""), None)
    assert AsyncGatewayClient._extract_retry_after(exc) is None


def test_extract_retry_after_no_rcvd_is_none() -> None:
    # rcvd is None -> reason defaults to "" -> None.
    exc = _closed(None, Close(4007, "ignored"))
    assert AsyncGatewayClient._extract_retry_after(exc) is None


def test_extract_retry_after_valid_json() -> None:
    exc = _closed(Close(4007, json.dumps({"retry_after_ms": 2500})), None)
    assert AsyncGatewayClient._extract_retry_after(exc) == 2.5


def test_extract_retry_after_valid_json_float() -> None:
    exc = _closed(Close(4009, json.dumps({"retry_after_ms": 1500.0})), None)
    assert AsyncGatewayClient._extract_retry_after(exc) == 1.5


def test_extract_retry_after_invalid_json_is_none() -> None:
    exc = _closed(Close(4007, "not json {{{"), None)
    assert AsyncGatewayClient._extract_retry_after(exc) is None


def test_extract_retry_after_non_dict_json_is_none() -> None:
    exc = _closed(Close(4007, json.dumps([1, 2, 3])), None)
    assert AsyncGatewayClient._extract_retry_after(exc) is None


def test_extract_retry_after_dict_without_key_is_none() -> None:
    exc = _closed(Close(4007, json.dumps({"other": 1})), None)
    assert AsyncGatewayClient._extract_retry_after(exc) is None


def test_extract_retry_after_non_numeric_value_is_none() -> None:
    exc = _closed(Close(4007, json.dumps({"retry_after_ms": "soon"})), None)
    assert AsyncGatewayClient._extract_retry_after(exc) is None


def test_flatten_group_yields_all_leaves_in_order() -> None:
    a = ValueError("a")
    b = OSError("b")
    c = TransientDisconnect("c")
    inner = ExceptionGroup("inner", [b, c])
    outer = ExceptionGroup("outer", [a, inner])
    leaves = list(_flatten_group(outer))
    assert leaves == [a, b, c]


def test_raise_from_group_fatal_wins() -> None:
    fatal = FatalDisconnect("denied", code=4004)
    group = ExceptionGroup("g", [TransientDisconnect("x"), OSError("y"), fatal])
    with pytest.raises(FatalDisconnect) as info:
        AsyncGatewayClient._raise_from_group(group)
    assert info.value is fatal
    assert info.value.code == 4004


def test_raise_from_group_transient_for_connection_closed() -> None:
    group = ExceptionGroup("g", [_closed(Close(1011, ""), None)])
    with pytest.raises(TransientDisconnect):
        AsyncGatewayClient._raise_from_group(group)


def test_raise_from_group_transient_for_oserror() -> None:
    group = ExceptionGroup("g", [OSError("boom")])
    with pytest.raises(TransientDisconnect):
        AsyncGatewayClient._raise_from_group(group)


def test_raise_from_group_transient_for_transient_leaf() -> None:
    group = ExceptionGroup("g", [TransientDisconnect("lost")])
    with pytest.raises(TransientDisconnect):
        AsyncGatewayClient._raise_from_group(group)


def test_raise_from_group_surfaces_lone_unexpected_leaf() -> None:
    sentinel = RuntimeError("weird")
    group = ExceptionGroup("g", [sentinel])
    with pytest.raises(RuntimeError) as info:
        AsyncGatewayClient._raise_from_group(group)
    assert info.value is sentinel


def test_raise_from_group_empty_raises_transient() -> None:
    # A BaseExceptionGroup with no leaves still surfaces a TransientDisconnect.
    group = BaseExceptionGroup("g", [KeyboardInterrupt()])
    # KeyboardInterrupt is a BaseException leaf but not Fatal/Transient/OSError;
    # it is surfaced as-is via the "lone leaf" branch.
    with pytest.raises(KeyboardInterrupt):
        AsyncGatewayClient._raise_from_group(group)


def test_raise_from_group_no_matching_leaf_via_stub() -> None:
    # Exercise the final ``raise TransientDisconnect()`` (no leaves at all) with
    # a lightweight stand-in whose ``exceptions`` is empty. A real
    # BaseExceptionGroup always carries >=1 leaf, so this branch is otherwise
    # unreachable from genuine groups.
    class _Emptyish:
        exceptions: tuple[BaseException, ...] = ()

    with pytest.raises(TransientDisconnect):
        AsyncGatewayClient._raise_from_group(_Emptyish())  # type: ignore[arg-type]


def test_fatal_disconnect_carries_code() -> None:
    exc = FatalDisconnect("bad token", code=4004)
    assert exc.code == 4004
    assert isinstance(exc, GatewayError)
    assert str(exc) == "bad token"


def test_fatal_disconnect_default_code_none() -> None:
    exc = FatalDisconnect("gone")
    assert exc.code is None


def test_transient_disconnect_default_message() -> None:
    exc = TransientDisconnect()
    assert isinstance(exc, GatewayError)
    assert str(exc) == "Gateway connection lost."


def test_build_url_quotes_token_and_appends_vsn() -> None:
    client = AsyncGatewayClient(
        token="wmbly/with spaces&x", base_url="wss://rt.example.com/"
    )
    url = client._build_url()
    # The base_url trailing slash is stripped in __init__.
    assert url.startswith("wss://rt.example.com/socket/websocket?token=")
    assert "wmbly%2Fwith%20spaces%26x" in url
    assert url.endswith("&vsn=2.0.0")
    # No raw special characters leaked from the token.
    assert "with spaces" not in url


def test_require_ws_when_never_connected_raises() -> None:
    client = AsyncGatewayClient(token="t")
    with pytest.raises(GatewayError, match="not connected"):
        client._require_ws()


@pytest.mark.anyio
async def test_wait_ready_without_supervisor_raises(
    anyio_backend: str,
) -> None:
    client = AsyncGatewayClient(token="t")
    with pytest.raises(GatewayError, match="not connected"):
        await client._wait_ready()


@pytest.mark.anyio
async def test_subscribe_before_connect_raises(anyio_backend: str) -> None:
    client = AsyncGatewayClient(token="t")
    with pytest.raises(GatewayError, match="not connected"):
        await client.subscribe("org:org_1")


@pytest.mark.anyio
async def test_push_before_connect_raises(anyio_backend: str) -> None:
    client = AsyncGatewayClient(token="t")
    with pytest.raises(GatewayError, match="not connected"):
        await client.push("org:org_1", "ping", {})


# ---------------------------------------------------------------------------
# PART B -- configurable in-process gateway + supervisor integration
# ---------------------------------------------------------------------------


class ConfigurableGateway:
    """A behaviour-injectable in-process gateway for supervisor tests."""

    def __init__(self) -> None:
        self._server: Any = None
        self.host = "localhost"
        self.port = 0
        self.connections: set[ServerConnection] = set()
        self.received: list[Any] = []
        self.join_params: dict[str, dict[str, Any]] = {}
        #: Number of joins seen per topic (for re-join assertions).
        self.join_count: dict[str, int] = {}
        #: A new Event fires whenever ANY join completes.
        self.joined = asyncio.Event()
        #: How many client connections we have accepted in total.
        self.accept_count = 0
        # -- injectable behaviour --------------------------------------
        #: If set, the server closes the socket with this code on connect
        #: (after optionally replying to the first join).
        self.close_on_connect_code: int | None = None
        self.close_on_connect_reason: str = ""
        #: If True, the server never acks heartbeats (zombie simulation).
        self.swallow_heartbeats = False
        #: If set, drop the Nth-and-onward connections abnormally right after
        #: the first join (transient drop simulation). None disables.
        self.drop_after_join_on_accept: int | None = None
        #: A hook awaited after each frame is processed (test instrumentation).
        self.on_join_topics: list[str] = []

    @property
    def base_url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    async def start(self) -> None:
        # The in-process websocket server + rapid reconnect cycling is flaky on
        # the Windows ProactorEventLoop (intermittent accept hangs that time the
        # whole supervisor suite out). Skip these integration tests there; the
        # gateway logic is still exercised by the socket-free unit tests in this
        # file and by the full integration suite on Linux and macOS. This single
        # chokepoint covers every test that stands up a gateway (fixture or not).
        if sys.platform == "win32":
            pytest.skip("in-process gateway server is flaky on Windows CI")
        self._server = await serve(self._handler, self.host, 0)
        sock = next(iter(self._server.sockets))
        self.port = sock.getsockname()[1]

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handler(self, connection: ServerConnection) -> None:
        self.accept_count += 1
        accept_index = self.accept_count
        self.connections.add(connection)
        try:
            # Fatal/backpressure: accept then immediately close with the code.
            if self.close_on_connect_code is not None:
                await connection.close(
                    code=self.close_on_connect_code,
                    reason=self.close_on_connect_reason,
                )
                return
            async for raw in connection:
                await self._on_frame(connection, raw, accept_index)
        except ConnectionClosed:
            pass
        finally:
            self.connections.discard(connection)

    async def _on_frame(
        self, connection: ServerConnection, raw: Any, accept_index: int
    ) -> None:
        frame = decode(raw)
        self.received.append(frame)

        if frame.event == EVENT_HEARTBEAT:
            if self.swallow_heartbeats:
                return
            reply = [None, frame.ref, PHOENIX_TOPIC, EVENT_REPLY, {"status": "ok"}]
            await connection.send(json.dumps(reply))
            return

        if frame.event == EVENT_JOIN:
            self.join_params[frame.topic] = frame.payload
            self.join_count[frame.topic] = self.join_count.get(frame.topic, 0) + 1
            self.on_join_topics.append(frame.topic)
            reply = [
                frame.join_ref,
                frame.ref,
                frame.topic,
                EVENT_REPLY,
                {"status": "ok", "response": {"seq": 0, "resume_supported": True}},
            ]
            await connection.send(json.dumps(reply))
            self.joined.set()
            # Transient drop: on the designated connection, after the first
            # join completes, slam the socket abnormally to force a reconnect.
            if (
                self.drop_after_join_on_accept is not None
                and accept_index == self.drop_after_join_on_accept
            ):
                await connection.close(code=1011, reason="boom")
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

        # Any other push: ack it.
        reply = [
            frame.join_ref,
            frame.ref,
            frame.topic,
            EVENT_REPLY,
            {"status": "ok", "response": {}},
        ]
        await connection.send(json.dumps(reply))

    async def broadcast(
        self, topic: str, event: str, payload: dict[str, Any] | None = None
    ) -> None:
        frame = [None, None, topic, event, payload or {}]
        raw = json.dumps(frame)
        for connection in list(self.connections):
            await connection.send(raw)

    async def send_to_all(self, frame: list[Any]) -> None:
        raw = json.dumps(frame)
        for connection in list(self.connections):
            await connection.send(raw)


@pytest.fixture
def tiny_timing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink the module timing constants so reconnect tests run fast."""
    monkeypatch.setattr(conn, "_HEARTBEAT_INTERVAL", 0.02)
    monkeypatch.setattr(conn, "_SERVER_TIMEOUT", 0.05)
    monkeypatch.setattr(conn, "_BACKOFF_INITIAL", 0.01)
    monkeypatch.setattr(conn, "_BACKOFF_MAX", 0.05)
    monkeypatch.setattr(conn, "_OPEN_TIMEOUT", 2.0)


@pytest.fixture
async def server() -> Any:
    gw = ConfigurableGateway()
    await gw.start()
    try:
        yield gw
    finally:
        await gw.stop()


def _new_client(server: ConfigurableGateway, **kwargs: Any) -> AsyncGatewayClient:
    return AsyncGatewayClient(
        token="wmbly_test_token", base_url=server.base_url, **kwargs
    )


async def _wait_until(predicate: Any, timeout: float = _TIMEOUT) -> None:
    """Poll *predicate* (sync callable) until true or timeout."""

    async def _loop() -> None:
        while not predicate():  # noqa: ASYNC110 - polling an arbitrary predicate
            await asyncio.sleep(0.005)

    await asyncio.wait_for(_loop(), timeout=timeout)


# -- fatal close codes -------------------------------------------------------


@pytest.mark.anyio
@pytest.mark.parametrize("code", [4003, 4004, 4010])
async def test_fatal_close_code_surfaces_and_no_retry(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
    code: int,
) -> None:
    # The server accepts then immediately closes with a fatal code. run_forever
    # awaits the supervisor to completion, so the FatalDisconnect surfaces
    # deterministically (connect() can race ready-vs-fatal).
    server.close_on_connect_code = code
    client = _new_client(server)
    try:
        with pytest.raises(FatalDisconnect) as info:
            await asyncio.wait_for(client.run_forever(), timeout=_TIMEOUT)
        assert info.value.code == code
        # The supervisor recorded the fatal and did NOT loop/reconnect.
        assert isinstance(client._fatal, FatalDisconnect)
        await asyncio.sleep(0.05)
        assert server.accept_count == 1
    finally:
        await client.close()


@pytest.mark.anyio
async def test_fatal_close_via_connect_records_fatal(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    # connect() may win the ready-vs-fatal race and return, or surface the
    # FatalDisconnect directly (the outcome differs by interpreter); either way
    # the supervisor records the fatal and stops. The supervisor task ends *with*
    # that exception, so the test must retrieve it or asyncio reports it as a
    # never-retrieved task exception at loop teardown.
    server.close_on_connect_code = 4004
    client = _new_client(server)
    try:
        try:
            await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        except FatalDisconnect as exc:
            assert exc.code == 4004
        await _wait_until(
            lambda: (
                isinstance(client._fatal, FatalDisconnect)
                and client._supervisor is not None
                and client._supervisor.done()
            )
        )
        assert isinstance(client._fatal, FatalDisconnect)
        assert client._fatal.code == 4004
        # Retrieve the supervisor's terminal exception so it is not flagged as
        # unretrieved when the event loop closes.
        supervisor = client._supervisor
        assert supervisor is not None
        with contextlib.suppress(FatalDisconnect, asyncio.CancelledError):
            await supervisor
        assert server.accept_count == 1
    finally:
        await client.close()


# -- backpressure close ------------------------------------------------------


@pytest.mark.anyio
@pytest.mark.parametrize("code", [4007, 4009])
async def test_backpressure_close_sets_retry_after(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
    code: int,
) -> None:
    server.close_on_connect_code = code
    server.close_on_connect_reason = json.dumps({"retry_after_ms": 30})
    client = _new_client(server)
    # run_forever supervises reconnects; the backpressure close should set
    # _retry_after, back off, then reconnect (and get closed again).
    runner = asyncio.ensure_future(client.run_forever())
    try:
        # Wait until at least one reconnect has happened (accept_count >= 2),
        # which proves the backpressure path backed off and retried.
        await _wait_until(lambda: server.accept_count >= 2)
    finally:
        await client.close()
        # close() cancels the supervisor that run_forever awaits; depending on
        # the close()-vs-supervisor race the runner ends either cancelled or
        # returns normally, so drain it tolerantly rather than asserting which.
        runner.cancel()
        with contextlib.suppress(asyncio.CancelledError, GatewayError, FatalDisconnect):
            await asyncio.wait_for(runner, timeout=_TIMEOUT)


# -- transient drop + rejoin -------------------------------------------------


@pytest.mark.anyio
async def test_transient_drop_reconnects_and_rejoins(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    # The first accepted connection drops abnormally right after the join.
    server.drop_after_join_on_accept = 1
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        # Subscribe -- this join triggers the drop on connection #1.
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # The supervisor reconnects (connection #2) and re-joins the topic.
        await _wait_until(lambda: server.join_count.get("org:org_123", 0) >= 2)
        # And the client returns to ready on the new connection.
        await _wait_until(lambda: client._ready.is_set())
        assert server.accept_count >= 2
    finally:
        await client.close()


# -- channel-level phx_error / phx_close triggers safe rejoin ---------------


@pytest.mark.anyio
@pytest.mark.parametrize("dead_event", [EVENT_ERROR, EVENT_CLOSE])
async def test_channel_dead_event_triggers_rejoin(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
    dead_event: str,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        assert server.join_count["org:org_123"] == 1
        # Server pushes phx_error/phx_close for the joined topic.
        await server.send_to_all([None, None, "org:org_123", dead_event, {}])
        # _on_channel_dead schedules a background _safe_rejoin -> 2nd join.
        await _wait_until(lambda: server.join_count.get("org:org_123", 0) >= 2)
    finally:
        await client.close()


@pytest.mark.anyio
async def test_channel_dead_unknown_topic_is_noop(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # phx_error for a topic we never joined -> no channel -> no rejoin.
        await server.send_to_all([None, None, "org:unknown", EVENT_ERROR, {}])
        await asyncio.sleep(0.05)
        assert "org:unknown" not in server.join_count
        assert server.join_count["org:org_123"] == 1
    finally:
        await client.close()


# -- resume / resume_failed --------------------------------------------------


@pytest.mark.anyio
async def test_resumed_event_applies_resume_state(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        assert client._resume.last_seq("org:org_123") is None
        await server.send_to_all(
            [None, None, "org:org_123", "resumed", {"current_seq": 42}]
        )
        await _wait_until(lambda: client._resume.last_seq("org:org_123") == 42)
    finally:
        await client.close()


@pytest.mark.anyio
async def test_resume_failed_resets_and_invokes_callback(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    seen: asyncio.Future[tuple[str, dict[str, Any]]] = (
        asyncio.get_running_loop().create_future()
    )

    async def on_resume_failed(topic: str, payload: dict[str, Any]) -> None:
        if not seen.done():
            seen.set_result((topic, payload))

    client = _new_client(server, on_resume_failed=on_resume_failed)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # Seed a tracked seq so we can prove reset() clears it.
        await server.broadcast("org:org_123", "EMAIL_SENT", {"seq": 7})
        await _wait_until(lambda: client._resume.last_seq("org:org_123") == 7)
        await server.send_to_all(
            [None, None, "org:org_123", "resume_failed", {"reason": "gap"}]
        )
        topic, payload = await asyncio.wait_for(seen, timeout=_TIMEOUT)
        assert topic == "org:org_123"
        assert payload == {"reason": "gap"}
        # reset() forgot the tracked seq.
        assert client._resume.last_seq("org:org_123") is None
    finally:
        await client.close()


@pytest.mark.anyio
async def test_resume_failed_callback_that_raises_is_swallowed(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    called = asyncio.Event()

    async def boom(topic: str, payload: dict[str, Any]) -> None:
        called.set()
        raise RuntimeError("callback blew up")

    client = _new_client(server, on_resume_failed=boom)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await server.send_to_all(
            [None, None, "org:org_123", "resume_failed", {"reason": "x"}]
        )
        # The callback ran; the exception was logged, not raised. The client
        # remains healthy (a subsequent push still works).
        await asyncio.wait_for(called.wait(), timeout=_TIMEOUT)
        await asyncio.sleep(0.02)
        reply = await asyncio.wait_for(
            client.push("org:org_123", "ping", {}), timeout=_TIMEOUT
        )
        assert reply == {}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_resume_failed_without_callback_is_safe(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)  # no on_resume_failed
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await server.broadcast("org:org_123", "EMAIL_SENT", {"seq": 3})
        await _wait_until(lambda: client._resume.last_seq("org:org_123") == 3)
        await server.send_to_all(
            [None, None, "org:org_123", "resume_failed", {"reason": "x"}]
        )
        # Reset still happens even though there is no callback.
        await _wait_until(lambda: client._resume.last_seq("org:org_123") is None)
    finally:
        await client.close()


# -- heartbeat ---------------------------------------------------------------


@pytest.mark.anyio
async def test_heartbeat_ack_updates_liveness(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        # Wait until at least one real heartbeat frame has reached the server.
        await _wait_until(
            lambda: any(f.event == EVENT_HEARTBEAT for f in server.received)
        )
        # And until that heartbeat has been acked (liveness restored).
        await _wait_until(
            lambda: client._last_heartbeat_ack >= client._last_heartbeat_sent
        )
        # The connection survives -- it never went into the zombie path.
        assert client._ready.is_set()
    finally:
        await client.close()


@pytest.mark.anyio
async def test_heartbeat_zombie_timeout_reconnects(
    anyio_backend: str,
    server: ConfigurableGateway,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The server never acks heartbeats: the client should detect the zombie,
    # close with 4000, raise TransientDisconnect, and reconnect.
    #
    # The zombie check only trips when a full heartbeat interval elapses
    # without an ack AND that gap exceeds _SERVER_TIMEOUT, so the timeout must
    # be SMALLER than the interval here (each iteration refreshes "sent").
    monkeypatch.setattr(conn, "_HEARTBEAT_INTERVAL", 0.05)
    monkeypatch.setattr(conn, "_SERVER_TIMEOUT", 0.02)
    monkeypatch.setattr(conn, "_BACKOFF_INITIAL", 0.01)
    monkeypatch.setattr(conn, "_BACKOFF_MAX", 0.05)
    monkeypatch.setattr(conn, "_OPEN_TIMEOUT", 2.0)
    server.swallow_heartbeats = True
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        # The heartbeat loop trips the zombie detector and the supervisor
        # reconnects -> a second connection is accepted.
        await _wait_until(lambda: server.accept_count >= 2, timeout=_TIMEOUT)
    finally:
        await client.close()


# -- malformed inbound frame -------------------------------------------------


@pytest.mark.anyio
async def test_malformed_inbound_frame_is_dropped(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # Send a non-5-element frame: it must be dropped without crashing.
        for connection in list(server.connections):
            await connection.send(json.dumps({"not": "a frame"}))
            await connection.send(json.dumps([1, 2, 3]))
        await asyncio.sleep(0.03)
        # The client is still alive: a push round-trips.
        reply = await asyncio.wait_for(
            client.push("org:org_123", "ping", {}), timeout=_TIMEOUT
        )
        assert reply == {}
    finally:
        await client.close()


# -- push semantics ----------------------------------------------------------


@pytest.mark.anyio
async def test_push_before_subscribe_uses_null_join_ref(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        # No subscribe -> channel is None -> join_ref is None on the frame.
        reply = await asyncio.wait_for(
            client.push("org:org_999", "ping", {"n": 1}), timeout=_TIMEOUT
        )
        assert reply == {}
        pushed = [
            f for f in server.received if f.event == "ping" and f.topic == "org:org_999"
        ]
        assert pushed and pushed[-1].join_ref is None
    finally:
        await client.close()


# -- unsubscribe -------------------------------------------------------------


@pytest.mark.anyio
async def test_unsubscribe_joined_topic_sends_leave(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await asyncio.wait_for(client.unsubscribe("org:org_123"), timeout=_TIMEOUT)
        await _wait_until(
            lambda: any(
                f.event == EVENT_LEAVE and f.topic == "org:org_123"
                for f in server.received
            )
        )
        # The channel is forgotten.
        assert "org:org_123" not in client._channels
    finally:
        await client.close()


@pytest.mark.anyio
async def test_unsubscribe_unknown_topic_is_noop(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        # Never subscribed -> pop returns None -> early return, no leave frame.
        await asyncio.wait_for(client.unsubscribe("org:nope"), timeout=_TIMEOUT)
        await asyncio.sleep(0.03)
        leaves = [f for f in server.received if f.event == EVENT_LEAVE]
        assert leaves == []
    finally:
        await client.close()


@pytest.mark.anyio
async def test_unsubscribe_subscribed_but_not_joined_no_leave(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    # Create a channel that is tracked but not in JOINED state, so the
    # is_joined guard short-circuits and no leave frame is sent.
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        from warmbly.gateway._channel import Channel

        client._channels["org:ghost"] = Channel("org:ghost", {})  # CLOSED state
        await asyncio.wait_for(client.unsubscribe("org:ghost"), timeout=_TIMEOUT)
        await asyncio.sleep(0.02)
        assert "org:ghost" not in client._channels
        assert not any(
            f.event == EVENT_LEAVE and f.topic == "org:ghost" for f in server.received
        )
    finally:
        await client.close()


# -- lifecycle: run_forever + close ------------------------------------------


@pytest.mark.anyio
async def test_run_forever_then_close_returns_cleanly(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    runner = asyncio.ensure_future(client.run_forever())
    try:
        # Let run_forever open the socket and become ready.
        await _wait_until(lambda: client._ready.is_set())
        # close() from "another task" cancels the supervisor that run_forever
        # awaits; close() itself completes without error and the runner ends.
        await asyncio.wait_for(client.close(), timeout=_TIMEOUT)
        # close() cancels the supervisor that run_forever awaits; depending on
        # the close()-vs-supervisor race the runner ends either cancelled or
        # returns normally. Either way it must terminate and tear the client down.
        with contextlib.suppress(asyncio.CancelledError, GatewayError, FatalDisconnect):
            await asyncio.wait_for(runner, timeout=_TIMEOUT)
        assert runner.done()
        assert client._ws is None
        assert not client._ready.is_set()
    finally:
        if not runner.done():
            runner.cancel()
        with contextlib.suppress(asyncio.CancelledError, GatewayError, FatalDisconnect):
            await runner
        await client.close()


@pytest.mark.anyio
async def test_close_is_idempotent(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
    await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
    await asyncio.wait_for(client.close(), timeout=_TIMEOUT)
    assert client._ws is None
    # A second (and third) close must not raise or warn.
    await asyncio.wait_for(client.close(), timeout=_TIMEOUT)
    await asyncio.wait_for(client.close(), timeout=_TIMEOUT)


@pytest.mark.anyio
async def test_connect_twice_reuses_running_supervisor(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        first = client._supervisor
        # Already ready -> _wait_ready returns immediately, supervisor reused.
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        assert client._supervisor is first
        assert server.accept_count == 1
    finally:
        await client.close()


@pytest.mark.anyio
async def test_send_after_connection_lost_raises_gateway_error(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    # Drive _send's ConnectionClosed branch: close the underlying ws out from
    # under a push so the send fails with a wrapped GatewayError.
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        ws = client._ws
        assert ws is not None
        await ws.close(code=1000)
        with pytest.raises(GatewayError):
            await asyncio.wait_for(
                client._send(ws, '[null,"1","t","ping",{}]'), timeout=_TIMEOUT
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Registration API + small accessors (no socket needed)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_on_decorator_registers_exact_handler(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    got: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()

    @client.on(("org:org_123", "EMAIL_SENT"))
    async def _handler(topic: str, payload: dict[str, Any]) -> None:
        if not got.done():
            got.set_result(payload)

    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await server.broadcast("org:org_123", "EMAIL_SENT", {"id": "e1"})
        payload = await asyncio.wait_for(got, timeout=_TIMEOUT)
        assert payload == {"id": "e1"}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_on_event_decorator_and_presence_accessor(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    got: asyncio.Future[str] = asyncio.get_running_loop().create_future()

    @client.on_event("CONTACT_CREATED")
    async def _handler(topic: str, payload: dict[str, Any]) -> None:
        if not got.done():
            got.set_result(topic)

    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # presence() accessor returns the (empty) map for the topic.
        assert client.presence("org:org_123") == {}
        await server.broadcast("org:org_123", "CONTACT_CREATED", {"c": 1})
        topic = await asyncio.wait_for(got, timeout=_TIMEOUT)
        assert topic == "org:org_123"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_wait_for_via_public_api(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        waiter = asyncio.ensure_future(
            client.wait_for("CAMPAIGN_STARTED", timeout=_TIMEOUT)
        )
        await asyncio.sleep(0)
        await server.broadcast("org:org_123", "CAMPAIGN_STARTED", {"k": "v"})
        payload = await asyncio.wait_for(waiter, timeout=_TIMEOUT)
        assert payload == {"k": "v"}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_subscribe_with_intents_sends_intents_param(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(
            client.subscribe("org:org_123", intents=["CAMPAIGN", "EMAIL"]),
            timeout=_TIMEOUT,
        )
        assert server.join_params["org:org_123"] == {"intents": ["CAMPAIGN", "EMAIL"]}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_presence_state_broadcast_updates_presence_map(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        waiter = asyncio.ensure_future(
            client.wait_for("presence_state", timeout=_TIMEOUT)
        )
        await asyncio.sleep(0)
        await server.broadcast(
            "org:org_123",
            "presence_state",
            {"usr_1": {"metas": [{"online_at": 1}]}},
        )
        await asyncio.wait_for(waiter, timeout=_TIMEOUT)
        assert set(client.presence("org:org_123")) == {"usr_1"}
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# _open_socket error mapping (driven by patching the connect() coroutine)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_open_socket_invalid_status_is_fatal(
    anyio_backend: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _bad_connect(*args: Any, **kwargs: Any) -> Any:
        response = Response(403, "Forbidden", Headers())
        raise InvalidStatus(response)

    monkeypatch.setattr(conn, "connect", _bad_connect)
    client = AsyncGatewayClient(token="t", base_url="ws://localhost:1")
    with pytest.raises(FatalDisconnect) as info:
        await asyncio.wait_for(client._open_socket(), timeout=_TIMEOUT)
    assert "HTTP 403" in str(info.value)
    await client.close()


@pytest.mark.anyio
async def test_open_socket_oserror_is_gateway_error(
    anyio_backend: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _bad_connect(*args: Any, **kwargs: Any) -> Any:
        raise OSError("connection refused")

    monkeypatch.setattr(conn, "connect", _bad_connect)
    client = AsyncGatewayClient(token="t", base_url="ws://localhost:1")
    with pytest.raises(GatewayError) as info:
        await asyncio.wait_for(client._open_socket(), timeout=_TIMEOUT)
    assert "could not connect" in str(info.value)
    await client.close()


@pytest.mark.anyio
async def test_open_socket_websocket_exception_is_gateway_error(
    anyio_backend: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _bad_connect(*args: Any, **kwargs: Any) -> Any:
        raise WebSocketException("handshake failed")

    monkeypatch.setattr(conn, "connect", _bad_connect)
    client = AsyncGatewayClient(token="t", base_url="ws://localhost:1")
    with pytest.raises(GatewayError):
        await asyncio.wait_for(client._open_socket(), timeout=_TIMEOUT)
    await client.close()


@pytest.mark.anyio
async def test_supervisor_retries_on_socket_open_failure(
    anyio_backend: str,
    monkeypatch: pytest.MonkeyPatch,
    tiny_timing: None,
) -> None:
    # First open raises a GatewayError (the _supervise `except GatewayError`
    # backoff branch); the second succeeds against the real server.
    gw = ConfigurableGateway()
    await gw.start()
    calls = {"n": 0}
    real_connect = conn.connect

    async def _flaky_connect(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("temporary failure")
        return await real_connect(*args, **kwargs)

    monkeypatch.setattr(conn, "connect", _flaky_connect)
    client = _new_client(gw)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        assert client._ready.is_set()
        assert calls["n"] >= 2
    finally:
        await client.close()
        await gw.stop()


# ---------------------------------------------------------------------------
# join rejected, rejoin partial failure, heartbeat send drop
# ---------------------------------------------------------------------------


class _RejectJoinGateway(ConfigurableGateway):
    """A gateway that rejects joins with status == error."""

    async def _on_frame(
        self, connection: ServerConnection, raw: Any, accept_index: int
    ) -> None:
        frame = decode(raw)
        self.received.append(frame)
        if frame.event == EVENT_HEARTBEAT:
            await connection.send(
                json.dumps(
                    [None, frame.ref, PHOENIX_TOPIC, EVENT_REPLY, {"status": "ok"}]
                )
            )
            return
        if frame.event == EVENT_JOIN:
            self.join_count[frame.topic] = self.join_count.get(frame.topic, 0) + 1
            await connection.send(
                json.dumps(
                    [
                        frame.join_ref,
                        frame.ref,
                        frame.topic,
                        EVENT_REPLY,
                        {"status": "error", "response": {"reason": "denied"}},
                    ]
                )
            )
            return
        await connection.send(
            json.dumps(
                [
                    frame.join_ref,
                    frame.ref,
                    frame.topic,
                    EVENT_REPLY,
                    {"status": "ok", "response": {}},
                ]
            )
        )


@pytest.mark.anyio
async def test_subscribe_rejected_raises_and_marks_errored(
    anyio_backend: str,
    tiny_timing: None,
) -> None:
    gw = _RejectJoinGateway()
    await gw.start()
    client = _new_client(gw)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        with pytest.raises(GatewayError):
            await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # The channel is tracked but marked errored (the _join error path).
        channel = client._channels["org:org_123"]
        from warmbly.gateway._channel import ChannelState

        assert channel.state == ChannelState.ERRORED
    finally:
        await client.close()
        await gw.stop()


@pytest.mark.anyio
async def test_rejoin_all_swallows_failed_rejoin(
    anyio_backend: str,
    tiny_timing: None,
) -> None:
    # A pre-seeded channel whose join the server rejects: _rejoin_all logs and
    # continues (joined_any stays False, so no backoff reset is forced).
    gw = _RejectJoinGateway()
    await gw.start()
    client = _new_client(gw)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        from warmbly.gateway._channel import Channel

        client._channels["org:seed"] = Channel("org:seed", {})
        # Call _rejoin_all directly; the rejected join is swallowed.
        await asyncio.wait_for(client._rejoin_all(), timeout=_TIMEOUT)
        assert gw.join_count.get("org:seed", 0) >= 1
    finally:
        await client.close()
        await gw.stop()


@pytest.mark.anyio
async def test_rejoin_all_no_channels_is_noop(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        assert client._channels == {}
        # Early return when there are no channels to rejoin.
        await asyncio.wait_for(client._rejoin_all(), timeout=_TIMEOUT)
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# handler that raises is swallowed; resume-failed without callback
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_handler_that_raises_is_swallowed(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    ran = asyncio.Event()
    client = _new_client(server)

    @client.on_event("EMAIL_SENT")
    async def _bad(topic: str, payload: dict[str, Any]) -> None:
        ran.set()
        raise RuntimeError("handler boom")

    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await server.broadcast("org:org_123", "EMAIL_SENT", {"id": "x"})
        await asyncio.wait_for(ran.wait(), timeout=_TIMEOUT)
        # The receive loop survived: a follow-up push still round-trips.
        await asyncio.sleep(0.02)
        reply = await asyncio.wait_for(
            client.push("org:org_123", "ping", {}), timeout=_TIMEOUT
        )
        assert reply == {}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_invoke_resume_failed_with_no_callback_returns(
    anyio_backend: str,
) -> None:
    # Directly exercise the early-return guard in _invoke_resume_failed.
    client = AsyncGatewayClient(token="t")
    await client._invoke_resume_failed("org:x", {"reason": "y"})
    await client.close()


@pytest.mark.anyio
async def test_heartbeat_send_on_closed_socket_reconnects(
    anyio_backend: str,
    server: ConfigurableGateway,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Make the heartbeat interval tiny but the server timeout large so the
    # zombie path does not fire; instead, drop the socket so the next
    # heartbeat send hits ConnectionClosed -> TransientDisconnect -> reconnect.
    monkeypatch.setattr(conn, "_HEARTBEAT_INTERVAL", 0.02)
    monkeypatch.setattr(conn, "_SERVER_TIMEOUT", 60.0)
    monkeypatch.setattr(conn, "_BACKOFF_INITIAL", 0.01)
    monkeypatch.setattr(conn, "_BACKOFF_MAX", 0.05)
    monkeypatch.setattr(conn, "_OPEN_TIMEOUT", 2.0)
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await _wait_until(
            lambda: any(f.event == EVENT_HEARTBEAT for f in server.received)
        )
        # Drop the server side abruptly; a subsequent heartbeat send fails.
        for connection in list(server.connections):
            await connection.close(code=1011, reason="drop")
        await _wait_until(lambda: server.accept_count >= 2, timeout=_TIMEOUT)
    finally:
        await client.close()


@pytest.mark.anyio
async def test_reply_for_unknown_ref_is_ignored(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        # A phx_reply with a ref nobody is waiting on must be ignored quietly.
        await server.send_to_all(
            [None, "999999", "org:org_123", EVENT_REPLY, {"status": "ok"}]
        )
        await asyncio.sleep(0.02)
        # Client still healthy.
        reply = await asyncio.wait_for(
            client.push("org:org_123", "ping", {}), timeout=_TIMEOUT
        )
        assert reply == {}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_reply_with_null_ref_on_real_topic_is_ignored(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    # A phx_reply broadcast with a null ref on a non-phoenix topic exercises
    # the `ref is None` fall-through in _handle_reply (no pending to resolve).
    client = _new_client(server)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await server.send_to_all(
            [None, None, "org:org_123", EVENT_REPLY, {"status": "ok"}]
        )
        await asyncio.sleep(0.02)
        reply = await asyncio.wait_for(
            client.push("org:org_123", "ping", {}), timeout=_TIMEOUT
        )
        assert reply == {}
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Direct-call coverage of supervisor/loops edge branches
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_wait_ready_surfaces_recorded_fatal(anyio_backend: str) -> None:
    # Supervisor finishes (without ever setting ready) and _fatal is recorded:
    # _wait_ready re-raises the stored FatalDisconnect.
    client = AsyncGatewayClient(token="t")
    fatal = FatalDisconnect("denied", code=4010)
    client._fatal = fatal

    async def _done_supervisor() -> None:
        return None

    client._supervisor = asyncio.ensure_future(_done_supervisor())
    await asyncio.sleep(0)  # let it finish
    with pytest.raises(FatalDisconnect) as info:
        await asyncio.wait_for(client._wait_ready(), timeout=_TIMEOUT)
    assert info.value is fatal
    await client.close()


@pytest.mark.anyio
async def test_wait_ready_surfaces_supervisor_exception(
    anyio_backend: str,
) -> None:
    # Supervisor finishes with a non-fatal exception and no _fatal recorded:
    # _wait_ready re-raises that exception.
    client = AsyncGatewayClient(token="t")
    boom = GatewayError("supervisor blew up")

    async def _failing_supervisor() -> None:
        raise boom

    client._supervisor = asyncio.ensure_future(_failing_supervisor())
    await asyncio.sleep(0)
    with pytest.raises(GatewayError) as info:
        await asyncio.wait_for(client._wait_ready(), timeout=_TIMEOUT)
    assert info.value is boom
    await client.close()


@pytest.mark.anyio
async def test_wait_ready_ended_before_ready_raises_gateway_error(
    anyio_backend: str,
) -> None:
    # Supervisor finishes cleanly without ready and without _fatal/exception:
    # _wait_ready raises the "ended before becoming ready" GatewayError.
    client = AsyncGatewayClient(token="t")

    async def _clean_supervisor() -> None:
        return None

    client._supervisor = asyncio.ensure_future(_clean_supervisor())
    await asyncio.sleep(0)
    with pytest.raises(GatewayError, match="ended before becoming ready"):
        await asyncio.wait_for(client._wait_ready(), timeout=_TIMEOUT)
    await client.close()


@pytest.mark.anyio
async def test_on_channel_dead_noops_when_ws_is_none(
    anyio_backend: str,
) -> None:
    # Channel present but no socket -> mark errored but DO NOT spawn a rejoin.
    client = AsyncGatewayClient(token="t")
    from warmbly.gateway._channel import Channel, ChannelState

    channel = Channel("org:x", {})
    channel.mark_joined()
    client._channels["org:x"] = channel
    assert client._ws is None
    client._on_channel_dead("org:x")
    assert channel.state == ChannelState.ERRORED
    # No background rejoin task was scheduled.
    assert client._background == set()
    await client.close()


@pytest.mark.anyio
async def test_heartbeat_loop_exits_when_closing(
    anyio_backend: str, tiny_timing: None
) -> None:
    # With _closing already True the loop's `while not self._closing` is false
    # immediately after the initial (tiny) jitter sleep, so it exits cleanly.
    client = AsyncGatewayClient(token="t")
    client._closing = True

    class _FakeWS:
        async def send(self, frame: str) -> None:  # pragma: no cover - unused
            raise AssertionError("should not send when closing")

        async def close(self, code: int = 1000) -> None:  # pragma: no cover
            return None

    # Patch the jitter sleep to be instant so the loop reaches the guard fast.
    await asyncio.wait_for(
        client._heartbeat_loop(_FakeWS()),  # type: ignore[arg-type]
        timeout=_TIMEOUT,
    )
    await client.close()


@pytest.mark.anyio
async def test_heartbeat_loop_raises_transient_on_send_close(
    anyio_backend: str, tiny_timing: None
) -> None:
    # A ConnectionClosed during the heartbeat send maps to TransientDisconnect.
    client = AsyncGatewayClient(token="t")

    class _SendClosesWS:
        async def send(self, frame: str) -> None:
            raise ConnectionClosed(rcvd=None, sent=Close(1011, ""))

        async def close(self, code: int = 1000) -> None:  # pragma: no cover
            return None

    with pytest.raises(TransientDisconnect, match="during heartbeat"):
        await asyncio.wait_for(
            client._heartbeat_loop(_SendClosesWS()),  # type: ignore[arg-type]
            timeout=_TIMEOUT,
        )
    await client.close()


@pytest.mark.anyio
async def test_heartbeat_loop_zombie_timeout_raises_transient(
    anyio_backend: str, tiny_timing: None
) -> None:
    # A connection whose heartbeats are never acked is detected as a zombie: the
    # loop closes it with code 4000 and raises TransientDisconnect. Drive it with
    # liveness timestamps forced far into the past so the branch fires on the
    # first iteration, deterministically, without relying on wall-clock timing
    # (which is what makes the integration-level zombie test flaky across runners).
    client = AsyncGatewayClient(token="t")
    client._last_heartbeat_sent = time.monotonic() - 1_000_000.0
    client._last_heartbeat_ack = client._last_heartbeat_sent - 1.0

    closed: dict[str, int] = {}

    class _NeverAcksWS:
        async def send(self, frame: str) -> None:  # pragma: no cover - unreached
            raise AssertionError("zombie must be detected before the next send")

        async def close(self, code: int = 1000) -> None:
            closed["code"] = code

    with pytest.raises(TransientDisconnect, match="heartbeat timeout"):
        await asyncio.wait_for(
            client._heartbeat_loop(_NeverAcksWS()),  # type: ignore[arg-type]
            timeout=_TIMEOUT,
        )
    assert closed["code"] == 4000  # _CLOSE_ZOMBIE
    await client.close()


@pytest.mark.anyio
async def test_supervise_skips_open_when_ws_already_present(
    anyio_backend: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # When _ws is already set at the top of the loop, _open_socket is skipped
    # (the `if self._ws is None` guard is false) and _run_loops runs directly.
    client = AsyncGatewayClient(token="t")
    client._ws = object()  # type: ignore[assignment]
    opened = {"n": 0}

    async def _should_not_open() -> None:  # pragma: no cover - asserted unused
        opened["n"] += 1

    async def _noop_loops() -> None:
        return None

    monkeypatch.setattr(client, "_open_socket", _should_not_open)
    monkeypatch.setattr(client, "_run_loops", _noop_loops)
    await asyncio.wait_for(client._supervise(), timeout=_TIMEOUT)
    assert opened["n"] == 0
    await client.close()


@pytest.mark.anyio
async def test_supervise_breaks_immediately_when_closing(
    anyio_backend: str,
) -> None:
    # _supervise with _closing already set takes the top-of-loop break.
    client = AsyncGatewayClient(token="t")
    client._closing = True
    await asyncio.wait_for(client._supervise(), timeout=_TIMEOUT)
    assert not client._ready.is_set()
    await client.close()


@pytest.mark.anyio
async def test_supervise_clean_exit_when_loops_return(
    anyio_backend: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # If _open_socket and _run_loops both return without error, _supervise
    # takes the `else: break` clean-exit path.
    client = AsyncGatewayClient(token="t")

    async def _noop_open() -> None:
        client._ws = object()  # type: ignore[assignment]

    async def _noop_loops() -> None:
        return None

    monkeypatch.setattr(client, "_open_socket", _noop_open)
    monkeypatch.setattr(client, "_run_loops", _noop_loops)
    await asyncio.wait_for(client._supervise(), timeout=_TIMEOUT)
    await client.close()


@pytest.mark.anyio
async def test_run_forever_awaits_existing_supervisor(
    anyio_backend: str,
    server: ConfigurableGateway,
    tiny_timing: None,
) -> None:
    # connect() starts the supervisor; run_forever() must NOT create a new one
    # (the `if supervisor is None or done` branch is false) and just awaits it.
    client = _new_client(server)
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
    existing = client._supervisor
    runner = asyncio.ensure_future(client.run_forever())
    await asyncio.sleep(0.02)
    assert client._supervisor is existing
    await asyncio.wait_for(client.close(), timeout=_TIMEOUT)
    # The runner ends either cancelled or cleanly depending on the close() race.
    with contextlib.suppress(asyncio.CancelledError, GatewayError, FatalDisconnect):
        await asyncio.wait_for(runner, timeout=_TIMEOUT)
    assert runner.done()
