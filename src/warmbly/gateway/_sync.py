"""A blocking facade over :class:`AsyncGatewayClient`.

:class:`GatewayClient` runs a dedicated asyncio event loop on a background
thread and proxies the async client's methods onto it, so callers in ordinary
synchronous code can use the realtime gateway without writing any ``async``
code. Handlers registered through the sync client may themselves be plain
(synchronous) functions; they are adapted to coroutines transparently and run
on the background loop.

The wrapper is intentionally thin: all protocol logic lives in the async client;
this module only marshals calls and results across the thread boundary.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

from .._utils import logger
from ._connection import DEFAULT_BASE_URL, AsyncGatewayClient

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from concurrent.futures import Future as ConcurrentFuture

    from ._events import Handler
    from ._resume import ResumeFailedCallback

__all__ = ["GatewayClient"]

_T = TypeVar("_T")

#: A user handler for the sync client: either a coroutine function or a plain
#: function. Both receive the topic and the event payload.
SyncHandler = Callable[[str, dict[str, Any]], Any]


class GatewayClient:
    """Synchronous, blocking client for the Warmbly realtime gateway.

    Wraps :class:`AsyncGatewayClient`, running it on a private event loop in a
    background thread. Method calls block until the underlying coroutine
    completes. Event handlers may be ordinary functions or coroutine functions.

    Example:
        >>> gw = GatewayClient(token="wmbly_...")
        >>> @gw.on_event(GatewayEvent.CAMPAIGN_STARTED)
        ... def _(topic, payload):
        ...     print("started", payload)
        >>> gw.connect()
        >>> gw.subscribe("org:org_123")
        >>> gw.run_forever()  # blocks until close() is called from another thread
    """

    def __init__(
        self,
        *,
        token: str,
        base_url: str = DEFAULT_BASE_URL,
        on_resume_failed: ResumeFailedCallback | None = None,
    ) -> None:
        """Initialize the client and start its background event loop.

        Args:
            token: A bearer credential carrying the ``realtime_subscribe`` scope.
                Never logged.
            base_url: The gateway base URL.
            on_resume_failed: Optional coroutine callback for ``resume_failed``.
        """
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, name="warmbly-gateway", daemon=True
        )
        self._thread.start()
        self._async = AsyncGatewayClient(
            token=token, base_url=base_url, on_resume_failed=on_resume_failed
        )

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()

    def _submit(self, coro: Awaitable[_T]) -> ConcurrentFuture[_T]:
        return asyncio.run_coroutine_threadsafe(coro, self._loop)  # type: ignore[arg-type]

    def _call(self, coro: Awaitable[_T]) -> _T:
        return self._submit(coro).result()

    # -- registration ------------------------------------------------------

    @staticmethod
    def _adapt(handler: SyncHandler) -> Handler:
        if asyncio.iscoroutinefunction(handler):
            return cast("Handler", handler)

        async def _wrapper(topic: str, payload: dict[str, Any]) -> None:
            handler(topic, payload)

        return _wrapper

    def on(self, key: tuple[str, str]) -> Callable[[SyncHandler], SyncHandler]:
        """Decorator: register a handler for an exact ``(topic, event)`` pair.

        Args:
            key: A ``(topic, event)`` tuple.

        Returns:
            A decorator that registers and returns the handler unchanged.
        """

        def decorator(handler: SyncHandler) -> SyncHandler:
            self._async.on(key)(self._adapt(handler))
            return handler

        return decorator

    def on_event(self, event: str) -> Callable[[SyncHandler], SyncHandler]:
        """Decorator: register a handler for *event* on any topic.

        Args:
            event: The event name to match regardless of topic.

        Returns:
            A decorator that registers and returns the handler unchanged.
        """

        def decorator(handler: SyncHandler) -> SyncHandler:
            self._async.on_event(event)(self._adapt(handler))
            return handler

        return decorator

    def wait_for(
        self,
        event: str | None,
        *,
        check: Callable[[str, dict[str, Any]], bool] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Block until the next matching event arrives and return its payload.

        Args:
            event: The event name to wait for, or ``None`` for any event.
            check: Optional predicate ``(topic, payload) -> bool``.
            timeout: Optional timeout in seconds.

        Returns:
            The matching event's payload.
        """
        return self._call(self._async.wait_for(event, check=check, timeout=timeout))

    def presence(self, topic: str) -> dict[str, dict[str, Any]]:
        """Return the current presence map for *topic*."""
        return self._async.presence(topic)

    # -- lifecycle ---------------------------------------------------------

    def connect(self) -> None:
        """Open the connection (blocks until the socket is established)."""
        self._call(self._async.connect())

    def subscribe(
        self,
        topic: str,
        *,
        intents: list[str] | None = None,
        resume: bool = True,
    ) -> dict[str, Any]:
        """Join *topic* and return the server's join reply (blocking)."""
        return self._call(self._async.subscribe(topic, intents=intents, resume=resume))

    def unsubscribe(self, topic: str) -> None:
        """Leave *topic* (blocking)."""
        self._call(self._async.unsubscribe(topic))

    def push(self, topic: str, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send *event* on *topic* and return the reply (blocking)."""
        return self._call(self._async.push(topic, event, payload))

    def run_forever(self) -> None:
        """Run the supervised connection, blocking until :meth:`close`.

        Raises:
            FatalDisconnect: On an unrecoverable rejection.
        """
        future = self._submit(self._async.run_forever())
        future.result()

    def close(self) -> None:
        """Close the connection and stop the background loop.

        Idempotent. Safe to call from any thread, including from inside a
        synchronous handler.
        """
        try:
            self._call(self._async.close())
        except Exception:
            logger.debug("error during gateway close", exc_info=True)
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=5.0)
