"""The asynchronous realtime gateway client.

:class:`AsyncGatewayClient` owns a single WebSocket connection to the Warmbly
realtime gateway and the machinery around it: an application-level heartbeat
loop with zombie detection, a receive loop that decodes frames and routes them,
reply correlation, per-topic (re)join, sequence-based resume, presence tracking,
and a reconnect supervisor with exponential backoff and jitter.

The networking uses the ``websockets`` library's modern asyncio client; the
on-the-wire framing is the realtime protocol implemented in :mod:`._phoenix`
(a Phoenix Channels v2 transport, version ``2.0.0``). No ``websockets`` or
``httpx`` type appears in any public signature.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import random
import sys
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidStatus, WebSocketException

from .._exceptions import GatewayError
from .._utils import logger
from ._channel import Channel, PendingReplies
from ._events import EventDispatcher, Handler
from ._phoenix import (
    EVENT_CLOSE,
    EVENT_ERROR,
    EVENT_REPLY,
    PhoenixCodec,
    decode,
)
from ._presence import PresenceTracker
from ._resume import ResumeFailedCallback, ResumeTracker

# ``TaskGroup`` is stdlib from 3.11; on 3.10 the 'taskgroup' backport provides
# an API-compatible class. The ``sys.version_info`` guard is understood
# statically by the type checker, so '--strict' resolves the right symbol on
# every supported Python. ``BaseExceptionGroup`` is a builtin from 3.11 (and
# known to the type checker on all versions); the 'exceptiongroup' backport is
# imported only at runtime on 3.10, never for type-checking.
if sys.version_info >= (3, 11):  # pragma: no cover - version-dependent import
    from asyncio import TaskGroup
else:  # pragma: no cover - version-dependent import
    from exceptiongroup import (  # type: ignore[import-not-found]
        BaseExceptionGroup,
    )
    from taskgroup import TaskGroup

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterator

__all__ = [
    "DEFAULT_BASE_URL",
    "AsyncGatewayClient",
    "FatalDisconnect",
    "TransientDisconnect",
]

#: Default realtime gateway base URL (the ``/socket/websocket`` suffix is added).
DEFAULT_BASE_URL = "wss://realtime.warmbly.com"

# Heartbeat / timing constants (from the gateway contract).
_HEARTBEAT_INTERVAL = 25.0
_SERVER_TIMEOUT = 60.0
_OPEN_TIMEOUT = 60.0
_MAX_FRAME_SIZE = 2**20

# Reconnect backoff.
_BACKOFF_INITIAL = 0.5
_BACKOFF_MAX = 30.0

# Close codes (from the gateway contract).
_CLOSE_ZOMBIE = 4000  # client-initiated; keeps the server session for resume
_CLOSE_MISSING_TOKEN = 4003
_CLOSE_INVALID_TOKEN = 4004
_CLOSE_RATE_LIMITED = 4007
_CLOSE_CONN_LIMIT = 4009
_CLOSE_PERMISSION = 4010

# Codes that must NOT be retried.
_FATAL_CODES = frozenset(
    {_CLOSE_MISSING_TOKEN, _CLOSE_INVALID_TOKEN, _CLOSE_PERMISSION}
)
# Codes that mean "back off, honoring retry_after_ms".
_BACKPRESSURE_CODES = frozenset({_CLOSE_RATE_LIMITED, _CLOSE_CONN_LIMIT})


def _flatten_group(
    group: BaseExceptionGroup[BaseException],
) -> Iterator[BaseException]:
    """Yield every leaf exception from a (possibly nested) exception group."""
    for exc in group.exceptions:
        if isinstance(exc, BaseExceptionGroup):
            yield from _flatten_group(exc)
        else:
            yield exc


class TransientDisconnect(GatewayError):
    """Internal signal that the connection dropped but should be retried."""

    def __init__(self, message: str = "Gateway connection lost.") -> None:
        super().__init__(message)


class FatalDisconnect(GatewayError):
    """Raised when the gateway rejects the connection unrecoverably.

    Fatal rejections (missing/invalid token, permission/IP denial) require the
    caller to fix credentials and reconnect deliberately; the supervisor will
    not loop on them.

    Attributes:
        code: The WebSocket close code that caused the failure, if known.
    """

    code: int | None

    def __init__(self, message: str, *, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class AsyncGatewayClient:
    """Asynchronous client for the Warmbly realtime gateway.

    Connects over a single WebSocket, keeps subscriptions alive across
    reconnects, and dispatches broadcast events to registered handlers. Typical
    use is to register handlers, :meth:`connect`, :meth:`subscribe` to topics,
    and then :meth:`run_forever` (which supervises reconnects) until
    :meth:`close`.

    Example:
        >>> gw = AsyncGatewayClient(token="wmbly_...")
        >>> @gw.on_event(GatewayEvent.CAMPAIGN_STARTED)
        ... async def _(topic, payload):
        ...     print("started", payload)
        >>> await gw.connect()
        >>> await gw.subscribe("org:org_123")
        >>> await gw.run_forever()
    """

    def __init__(
        self,
        *,
        token: str,
        base_url: str = DEFAULT_BASE_URL,
        on_resume_failed: ResumeFailedCallback | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            token: A bearer credential carrying the ``realtime_subscribe`` scope
                (an API key, OAuth access token, or session JWT). It is sent in
                the connect query string and is never logged.
            base_url: The gateway base URL. The ``/socket/websocket`` path and
                version query are appended automatically.
            on_resume_failed: Optional callback invoked when the server reports a
                ``resume_failed`` for a topic, so the application can do a REST
                re-sync. May be a coroutine function.
        """
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._on_resume_failed = on_resume_failed

        self._codec = PhoenixCodec()
        self._dispatcher = EventDispatcher()
        self._presence = PresenceTracker()
        self._resume = ResumeTracker()
        self._pending = PendingReplies()
        self._channels: dict[str, Channel] = {}

        self._ws: ClientConnection | None = None
        self._ready = asyncio.Event()
        self._closing = False

        # The supervisor task created by connect()/run_forever(); it owns the
        # heartbeat and receive loops and the reconnect lifecycle.
        self._supervisor: asyncio.Task[None] | None = None
        self._fatal: BaseException | None = None

        # Strong references to fire-and-forget tasks (handlers, rejoins) so the
        # event loop does not garbage-collect them mid-flight.
        self._background: set[asyncio.Task[None]] = set()

        # Heartbeat liveness tracking (monotonic timestamps).
        self._last_heartbeat_sent = 0.0
        self._last_heartbeat_ack = 0.0

        # Reconnect backoff, honored retry hint from the server (seconds).
        self._backoff = _BACKOFF_INITIAL
        self._retry_after: float | None = None

    # -- public registration API ------------------------------------------

    def on(self, key: tuple[str, str]) -> Callable[[Handler], Handler]:
        """Decorator: register a handler for an exact ``(topic, event)`` pair.

        Args:
            key: A ``(topic, event)`` tuple.

        Returns:
            A decorator that registers and returns the handler unchanged.
        """

        def decorator(handler: Handler) -> Handler:
            return self._dispatcher.register(key, handler)

        return decorator

    def on_event(self, event: str) -> Callable[[Handler], Handler]:
        """Decorator: register a handler for *event* on any topic.

        Args:
            event: The event name to match regardless of topic.

        Returns:
            A decorator that registers and returns the handler unchanged.
        """

        def decorator(handler: Handler) -> Handler:
            return self._dispatcher.register(event, handler)

        return decorator

    async def wait_for(
        self,
        event: str | None,
        *,
        check: Callable[[str, dict[str, Any]], bool] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Wait for the next event matching *event* (and optional *check*).

        Args:
            event: The event name to wait for, or ``None`` to match any event.
            check: Optional predicate ``(topic, payload) -> bool``.
            timeout: Optional timeout in seconds.

        Returns:
            The matching event's payload.

        Raises:
            asyncio.TimeoutError: If *timeout* elapses first.
        """
        future = self._dispatcher.wait_for(event, check=check)
        return await asyncio.wait_for(future, timeout=timeout)

    def presence(self, topic: str) -> dict[str, dict[str, Any]]:
        """Return the current presence map for *topic* (see :class:`PresenceTracker`)."""
        return self._presence.presence(topic)

    # -- connection lifecycle ---------------------------------------------

    async def connect(self) -> None:
        """Open the connection and start streaming.

        Starts the background supervisor (heartbeat loop, receive loop, and
        reconnect lifecycle) and returns once the socket is open and ready, so
        subsequent :meth:`subscribe`/:meth:`push`/:meth:`wait_for` calls work
        immediately. To block on the supervisor for the lifetime of the client,
        call :meth:`run_forever` afterwards.

        Raises:
            FatalDisconnect: If the gateway rejects the connection with a fatal
                close code (missing/invalid token, permission/IP denial).
            GatewayError: For other connection failures.
        """
        self._closing = False
        self._fatal = None
        if self._supervisor is None or self._supervisor.done():
            self._ready.clear()
            self._supervisor = asyncio.ensure_future(self._supervise())
        await self._wait_ready()

    async def _wait_ready(self) -> None:
        if self._ready.is_set():
            return
        supervisor = self._supervisor
        if supervisor is None:
            raise GatewayError("not connected; call connect() first")
        ready_task: asyncio.Task[bool] = asyncio.ensure_future(self._ready.wait())
        waitset: set[asyncio.Future[Any]] = {ready_task, supervisor}
        done, _pending = await asyncio.wait(
            waitset,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if ready_task in done:
            return
        # Supervisor finished before becoming ready: surface its failure.
        ready_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ready_task
        if self._fatal is not None:
            raise self._fatal
        exc = supervisor.exception() if not supervisor.cancelled() else None
        if exc is not None:
            raise exc
        raise GatewayError("gateway connection ended before becoming ready")

    async def _open_socket(self) -> None:
        url = self._build_url()
        try:
            ws = await connect(
                url,
                additional_headers={},
                user_agent_header="warmbly-py",
                open_timeout=_OPEN_TIMEOUT,
                max_size=_MAX_FRAME_SIZE,
                logger=logger,
            )
        except InvalidStatus as exc:
            code = exc.response.status_code
            raise FatalDisconnect(
                f"gateway refused the connection (HTTP {code})"
            ) from exc
        except (OSError, WebSocketException) as exc:
            raise GatewayError("could not connect to the gateway") from exc
        self._ws = ws
        now = time.monotonic()
        self._last_heartbeat_sent = now
        self._last_heartbeat_ack = now
        logger.debug("gateway connection opened")

    def _build_url(self) -> str:
        token = quote(self._token, safe="")
        return f"{self._base_url}/socket/websocket?token={token}&vsn=2.0.0"

    async def close(self) -> None:
        """Close the connection and stop reconnecting.

        Idempotent. Cancels the background supervisor, fails any pending reply
        futures, and cancels one-shot waiters.
        """
        self._closing = True
        self._ready.clear()
        ws = self._ws
        self._ws = None
        if ws is not None:
            with contextlib.suppress(Exception):
                await ws.close(code=1000)
        supervisor = self._supervisor
        self._supervisor = None
        if supervisor is not None and not supervisor.done():
            supervisor.cancel()
            with contextlib.suppress(asyncio.CancelledError, GatewayError):
                await supervisor
        self._pending.fail_all(GatewayError("gateway connection closed"))
        self._dispatcher.fail_waiters(GatewayError("gateway connection closed"))
        logger.debug("gateway connection closed by client")

    # -- subscriptions -----------------------------------------------------

    async def subscribe(
        self,
        topic: str,
        *,
        intents: list[str] | None = None,
        resume: bool = True,
    ) -> dict[str, Any]:
        """Join a topic and return the server's join reply.

        Args:
            topic: The topic to subscribe to, e.g. ``"org:org_123"``,
                ``"campaign:cmp_1"``, ``"user:usr_1"``, ``"account:acc_1"``, or
                ``"bulk:op_1"``.
            intents: Optional event-type substring filters (``org:*`` topics).
            resume: Whether to request sequence-based replay on rejoin
                (``org:*`` topics).

        Returns:
            The join reply ``response`` object.

        Raises:
            GatewayError: If not connected or the join is rejected.
        """
        await self._wait_ready()
        params: dict[str, Any] = {}
        if intents is not None:
            params["intents"] = intents
        channel = Channel(topic, params, resume=resume)
        self._channels[topic] = channel
        return await self._join(channel)

    async def unsubscribe(self, topic: str) -> None:
        """Leave a topic and stop tracking it.

        Args:
            topic: The topic to leave.
        """
        channel = self._channels.pop(topic, None)
        self._presence.clear(topic)
        self._resume.reset(topic)
        if channel is None:
            return
        ws = self._ws
        if ws is not None and channel.is_joined:
            _ref, frame = self._codec.leave(topic, channel.join_ref)
            with contextlib.suppress(ConnectionClosed):
                await ws.send(frame)
        channel.mark_closed()

    async def _send(self, ws: ClientConnection, frame: str) -> None:
        try:
            await ws.send(frame)
        except ConnectionClosed as exc:
            raise GatewayError("gateway connection lost while sending") from exc

    async def _join(self, channel: Channel) -> dict[str, Any]:
        ws = self._require_ws()
        params = self._resume.join_params(
            channel.topic, channel.params, resume=channel.resume
        )
        join_ref, ref, frame = self._codec.join(channel.topic, params)
        channel.mark_joining(join_ref)
        future = self._pending.create(ref)
        await self._send(ws, frame)
        try:
            response = await future
        except GatewayError:
            channel.mark_errored()
            raise
        channel.mark_joined()
        logger.debug("joined topic %s", channel.topic)
        return response

    async def push(
        self, topic: str, event: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Send *event* with *payload* on *topic* and await the reply.

        Args:
            topic: The target topic (must be subscribed).
            event: The event name, e.g. ``"ping"`` or ``"presence:update"``.
            payload: The payload object.

        Returns:
            The reply ``response`` object.

        Raises:
            GatewayError: If not connected, the topic is unknown, or the push is
                rejected.
        """
        await self._wait_ready()
        ws = self._require_ws()
        channel = self._channels.get(topic)
        join_ref = channel.join_ref if channel is not None else None
        ref, frame = self._codec.push(topic, event, payload, join_ref)
        future = self._pending.create(ref)
        await self._send(ws, frame)
        return await future

    # -- supervisor --------------------------------------------------------

    async def run_forever(self) -> None:
        """Run until :meth:`close`, supervising reconnects.

        If the supervisor is not already running (it is started by
        :meth:`connect`), this starts it. It opens the socket, runs the
        heartbeat and receive loops under a single task group, and on a
        transient disconnect reconnects with exponential backoff and jitter
        (honoring any server-supplied ``retry_after_ms``), re-joins every
        subscribed topic, and replays missed events via resume. Returns
        normally only after :meth:`close`.

        Raises:
            FatalDisconnect: On an unrecoverable rejection (not retried).
        """
        self._closing = False
        if self._supervisor is None or self._supervisor.done():
            self._ready.clear()
            self._supervisor = asyncio.ensure_future(self._supervise())
        await self._supervisor

    async def _supervise(self) -> None:
        try:
            while True:
                if self._closing:
                    break
                try:
                    if self._ws is None:
                        await self._open_socket()
                    await self._run_loops()
                except FatalDisconnect as exc:
                    logger.debug("gateway fatal disconnect; not retrying")
                    self._fatal = exc
                    raise
                except TransientDisconnect as exc:
                    await self._sleep_backoff(exc)
                except GatewayError as exc:
                    # e.g. the socket could not be (re)opened; retry with backoff.
                    await self._sleep_backoff(TransientDisconnect(str(exc)))
                else:
                    break
        finally:
            self._ready.clear()

    async def _run_loops(self) -> None:
        ws = self._require_ws()
        try:
            async with TaskGroup() as tg:
                tg.create_task(self._heartbeat_loop(ws))
                tg.create_task(self._receive_loop(ws))
                tg.create_task(self._after_connect())
        except BaseExceptionGroup as group:
            self._teardown_socket()
            self._raise_from_group(group)

    @staticmethod
    def _raise_from_group(group: BaseExceptionGroup[BaseException]) -> None:
        # A fatal rejection wins over any transient errors in the same group.
        leaves = list(_flatten_group(group))
        for leaf in leaves:
            if isinstance(leaf, FatalDisconnect):
                raise leaf
        for leaf in leaves:
            if isinstance(leaf, (TransientDisconnect, ConnectionClosed, OSError)):
                raise TransientDisconnect(str(leaf)) from leaf
        # Anything else is unexpected: surface the first leaf as-is.
        if leaves:
            raise leaves[0]
        raise TransientDisconnect()

    async def _after_connect(self) -> None:
        # Runs alongside the loops once the socket is open: (re)join every
        # subscribed topic, then mark the client ready for callers.
        await self._rejoin_all()
        self._ready.set()

    def _teardown_socket(self) -> None:
        self._ready.clear()
        self._ws = None
        self._pending.fail_all(TransientDisconnect())
        for channel in self._channels.values():
            channel.mark_closed()

    async def _sleep_backoff(self, exc: TransientDisconnect) -> None:
        if self._retry_after is not None:
            delay = self._retry_after
            self._retry_after = None
        else:
            delay = min(self._backoff, _BACKOFF_MAX)
            self._backoff = min(self._backoff * 2.0, _BACKOFF_MAX)
        jittered = delay * (0.75 + 0.5 * random.random())
        logger.debug("gateway reconnecting in %.2fs after %s", jittered, exc)
        await asyncio.sleep(jittered)

    def _reset_backoff(self) -> None:
        self._backoff = _BACKOFF_INITIAL

    async def _rejoin_all(self) -> None:
        if not self._channels:
            return
        joined_any = False
        for channel in list(self._channels.values()):
            try:
                await self._join(channel)
                joined_any = True
            except GatewayError:
                logger.debug("failed to rejoin topic %s", channel.topic)
        if joined_any:
            # Only reset backoff after a stable rejoin, to avoid storms.
            self._reset_backoff()

    # -- loops -------------------------------------------------------------

    async def _heartbeat_loop(self, ws: ClientConnection) -> None:
        # Initial jitter so reconnect storms don't synchronize heartbeats.
        await asyncio.sleep(_HEARTBEAT_INTERVAL * random.random())
        while not self._closing:
            now = time.monotonic()
            if (
                self._last_heartbeat_ack < self._last_heartbeat_sent
                and now - self._last_heartbeat_sent > _SERVER_TIMEOUT
            ):
                logger.debug("gateway heartbeat timed out; treating as zombie")
                with contextlib.suppress(Exception):
                    await ws.close(code=_CLOSE_ZOMBIE)
                raise TransientDisconnect("heartbeat timeout")
            self._last_heartbeat_sent = time.monotonic()
            _ref, frame = self._codec.heartbeat()
            try:
                await ws.send(frame)
            except ConnectionClosed as exc:
                raise TransientDisconnect("connection closed during heartbeat") from exc
            await asyncio.sleep(_HEARTBEAT_INTERVAL)

    async def _receive_loop(self, ws: ClientConnection) -> None:
        try:
            async for raw in ws:
                self._handle_raw(raw)
        except ConnectionClosed as exc:
            self._handle_close(exc)

    def _handle_close(self, exc: ConnectionClosed) -> None:
        code = self._close_code(exc)
        if code in _FATAL_CODES:
            raise FatalDisconnect(
                f"gateway closed the connection (code {code})", code=code
            ) from exc
        if code in _BACKPRESSURE_CODES:
            self._retry_after = self._extract_retry_after(exc)
        raise TransientDisconnect(f"gateway closed (code {code})") from exc

    @staticmethod
    def _close_code(exc: ConnectionClosed) -> int:
        """The close code from the received (or sent) Close frame.

        Uses the modern ``rcvd``/``sent`` frame attributes rather than the
        deprecated ``ConnectionClosed.code`` shortcut. Falls back to 1006
        (abnormal closure) when no frame is available.
        """
        if exc.rcvd is not None:
            return exc.rcvd.code
        if exc.sent is not None:
            return exc.sent.code
        return 1006

    @staticmethod
    def _extract_retry_after(exc: ConnectionClosed) -> float | None:
        # The reject body's reason field may be JSON carrying retry_after_ms.
        reason = exc.rcvd.reason if exc.rcvd is not None else ""
        if not reason:
            return None
        try:
            data = json.loads(reason)
        except (ValueError, TypeError):
            return None
        if isinstance(data, dict):
            ms = data.get("retry_after_ms")
            if isinstance(ms, (int, float)):
                return float(ms) / 1000.0
        return None

    # -- frame routing -----------------------------------------------------

    def _handle_raw(self, raw: str | bytes) -> None:
        try:
            frame = decode(raw)
        except ValueError:
            logger.debug("dropping malformed gateway frame")
            return
        topic, event, payload = frame.topic, frame.event, frame.payload

        if event == EVENT_REPLY:
            self._handle_reply(frame.ref, topic, payload)
            return
        if event in (EVENT_ERROR, EVENT_CLOSE):
            self._on_channel_dead(topic)
            return
        if event == "resumed":
            self._resume.apply_resumed(topic, payload)
            return
        if event == "resume_failed":
            self._handle_resume_failed(topic, payload)
            return

        # Presence and seq tracking on broadcasts.
        if event in ("presence_state", "presence_diff"):
            self._presence.apply(topic, event, payload)
        self._resume.observe(topic, payload)

        # Fan out to handlers (each as its own task) and resolve waiters.
        self._dispatch(topic, event, payload)

    def _handle_reply(
        self, ref: str | None, topic: str, payload: dict[str, Any]
    ) -> None:
        # The reserved "phoenix" topic reply is the heartbeat ack.
        if topic == "phoenix":
            self._last_heartbeat_ack = time.monotonic()
            return
        if ref is not None:
            self._pending.resolve(ref, topic, "push", payload)

    def _spawn(self, coro: Coroutine[Any, Any, None]) -> None:
        task = asyncio.ensure_future(coro)
        self._background.add(task)
        task.add_done_callback(self._background.discard)

    def _on_channel_dead(self, topic: str) -> None:
        channel = self._channels.get(topic)
        if channel is None:
            return
        channel.mark_errored()
        logger.debug("topic %s errored/closed; scheduling rejoin", topic)
        if self._ws is not None and not self._closing:
            self._spawn(self._safe_rejoin(channel))

    async def _safe_rejoin(self, channel: Channel) -> None:
        with contextlib.suppress(GatewayError):
            await self._join(channel)

    def _handle_resume_failed(self, topic: str, payload: dict[str, Any]) -> None:
        logger.debug("resume failed for %s: %s", topic, payload.get("reason"))
        self._resume.reset(topic)
        if self._on_resume_failed is not None:
            self._spawn(self._invoke_resume_failed(topic, payload))

    async def _invoke_resume_failed(self, topic: str, payload: dict[str, Any]) -> None:
        callback = self._on_resume_failed
        if callback is None:
            return
        try:
            await callback(topic, payload)
        except Exception:
            logger.exception("on_resume_failed callback raised for %s", topic)

    def _dispatch(self, topic: str, event: str, payload: dict[str, Any]) -> None:
        self._dispatcher.resolve_waiters(topic, event, payload)
        for handler in self._dispatcher.handlers_for(topic, event):
            self._spawn(self._run_handler(handler, topic, payload))

    @staticmethod
    async def _run_handler(
        handler: Handler, topic: str, payload: dict[str, Any]
    ) -> None:
        try:
            await handler(topic, payload)
        except Exception:
            logger.exception("gateway handler raised for topic %s", topic)

    # -- helpers -----------------------------------------------------------

    def _require_ws(self) -> ClientConnection:
        ws = self._ws
        if ws is None:
            raise GatewayError("not connected; call connect() first")
        return ws
