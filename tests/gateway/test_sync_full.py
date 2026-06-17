"""Full-coverage tests for :class:`warmbly.gateway._sync.GatewayClient`.

The sync client runs the underlying :class:`AsyncGatewayClient` on a private
asyncio loop on a daemon thread. The :class:`~tests.gateway.conftest.FakeGateway`
fixture, however, runs on the test's own asyncio loop. To bridge the two without
deadlocking the event loop the fake server needs, every blocking sync-client call
is driven through :func:`asyncio.to_thread`, so the test loop stays free to serve
the WebSocket while the sync client's background loop does its work.
"""

from __future__ import annotations

import asyncio
import inspect
import threading
from typing import Any

import pytest

from conftest import FakeGateway
from warmbly.gateway._sync import GatewayClient

# Bound every cross-thread rendezvous so a hang fails fast instead of stalling CI.
_TIMEOUT = 5.0


async def _make_connected(gateway: FakeGateway) -> GatewayClient:
    gw = GatewayClient(token="wmbly_test_token", base_url=gateway.base_url)
    await asyncio.wait_for(asyncio.to_thread(gw.connect), timeout=_TIMEOUT)
    return gw


@pytest.mark.anyio
async def test_adapt_wraps_plain_handler(fake_gateway: FakeGateway) -> None:
    seen: dict[str, Any] = {}
    fired = threading.Event()

    gw = await _make_connected(fake_gateway)
    try:

        @gw.on_event("widget")
        def _plain(topic: str, payload: dict[str, Any]) -> None:
            seen["topic"] = topic
            seen["payload"] = payload
            fired.set()

        await asyncio.wait_for(asyncio.to_thread(gw.subscribe, "org:o_1"), _TIMEOUT)
        await fake_gateway.broadcast("org:o_1", "widget", {"value": 7})

        await asyncio.wait_for(asyncio.to_thread(fired.wait, _TIMEOUT), _TIMEOUT)
        assert fired.is_set()
        assert seen["topic"] == "org:o_1"
        assert seen["payload"] == {"value": 7}
    finally:
        await asyncio.to_thread(gw.close)
        assert not gw._thread.is_alive()


@pytest.mark.anyio
async def test_adapt_passes_coroutine_through(fake_gateway: FakeGateway) -> None:
    fired = threading.Event()
    captured: dict[str, Any] = {}

    gw = await _make_connected(fake_gateway)
    try:

        @gw.on(("org:o_1", "gadget"))
        async def _coro(topic: str, payload: dict[str, Any]) -> None:
            captured["payload"] = payload
            fired.set()

        # A coroutine function must be registered unchanged (not wrapped).
        assert inspect.iscoroutinefunction(_coro)

        await asyncio.wait_for(asyncio.to_thread(gw.subscribe, "org:o_1"), _TIMEOUT)
        await fake_gateway.broadcast("org:o_1", "gadget", {"ok": True})

        await asyncio.wait_for(asyncio.to_thread(fired.wait, _TIMEOUT), _TIMEOUT)
        assert captured["payload"] == {"ok": True}
    finally:
        await asyncio.to_thread(gw.close)
        assert not gw._thread.is_alive()


@pytest.mark.anyio
async def test_subscribe_push_and_unsubscribe(fake_gateway: FakeGateway) -> None:
    gw = await _make_connected(fake_gateway)
    try:
        reply = await asyncio.wait_for(
            asyncio.to_thread(gw.subscribe, "org:o_1"), _TIMEOUT
        )
        assert reply == {"seq": 0, "resume_supported": True}

        push_reply = await asyncio.wait_for(
            asyncio.to_thread(gw.push, "org:o_1", "ping", {}), _TIMEOUT
        )
        assert push_reply == {}

        await asyncio.wait_for(asyncio.to_thread(gw.unsubscribe, "org:o_1"), _TIMEOUT)
        assert "org:o_1" not in gw._async._channels
    finally:
        await asyncio.to_thread(gw.close)
        assert not gw._thread.is_alive()


@pytest.mark.anyio
async def test_wait_for_and_presence(fake_gateway: FakeGateway) -> None:
    gw = await _make_connected(fake_gateway)
    try:
        await asyncio.wait_for(asyncio.to_thread(gw.subscribe, "org:o_1"), _TIMEOUT)

        # presence map starts empty for a freshly-joined topic.
        assert gw.presence("org:o_1") == {}

        async def _broadcast_soon() -> None:
            await asyncio.sleep(0.05)
            await fake_gateway.broadcast("org:o_1", "thing", {"n": 1})

        broadcaster = asyncio.ensure_future(_broadcast_soon())
        try:
            payload = await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: gw.wait_for("thing", check=None, timeout=_TIMEOUT)
                ),
                _TIMEOUT,
            )
        finally:
            await broadcaster
        assert payload == {"n": 1}
    finally:
        await asyncio.to_thread(gw.close)
        assert not gw._thread.is_alive()


@pytest.mark.anyio
async def test_run_forever_unblocks_after_close(fake_gateway: FakeGateway) -> None:
    gw = await _make_connected(fake_gateway)
    outcome: dict[str, str] = {}

    def _run() -> None:
        # run_forever submits the supervisor coroutine (line 194) and blocks on
        # future.result() (line 195). close() cancels the supervisor, so result()
        # surfaces a cancellation; either way run_forever stops blocking.
        try:
            gw.run_forever()
            outcome["how"] = "returned"
        except BaseException as exc:
            outcome["how"] = type(exc).__name__

    try:
        run_task = asyncio.ensure_future(asyncio.to_thread(_run))
        # Give run_forever a moment to start blocking on the background loop.
        await asyncio.sleep(0.1)
        assert not run_task.done()

        # close() from the test thread must make run_forever stop blocking.
        await asyncio.to_thread(gw.close)
        await asyncio.wait_for(run_task, _TIMEOUT)
        assert run_task.done()
        assert "how" in outcome
        assert not gw._thread.is_alive()
    finally:
        await asyncio.to_thread(gw.close)


@pytest.mark.anyio
async def test_close_is_idempotent(fake_gateway: FakeGateway) -> None:
    gw = await _make_connected(fake_gateway)
    await asyncio.to_thread(gw.close)
    assert gw._closed is True
    assert not gw._thread.is_alive()

    # Second close returns immediately (the early-return branch).
    await asyncio.to_thread(gw.close)
    assert gw._closed is True


@pytest.mark.anyio
async def test_close_swallows_underlying_error(fake_gateway: FakeGateway) -> None:
    gw = await _make_connected(fake_gateway)
    try:
        # Cleanly tear down the real socket via the sync client first so no
        # transport leaks, while keeping the background loop alive.
        await asyncio.to_thread(gw._call, gw._async.close())

        # Now make the underlying async close raise. close() must swallow it
        # (lines 208-209) and still flip _closed and stop the loop/thread.
        async def _boom() -> None:
            raise RuntimeError("close failed")

        gw._async.close = lambda: _boom()  # type: ignore[method-assign]

        await asyncio.to_thread(gw.close)
        assert gw._closed is True
        assert not gw._thread.is_alive()
    finally:
        await asyncio.to_thread(gw.close)


@pytest.mark.anyio
async def test_close_skips_join_when_thread_already_dead(
    fake_gateway: FakeGateway,
) -> None:
    gw = await _make_connected(fake_gateway)
    try:
        # Cleanly close the real socket so nothing leaks, keeping the loop alive.
        await asyncio.to_thread(gw._call, gw._async.close())

        # Stop the loop and join its thread so the worker is already dead before
        # close() runs. The join branch (line 212 condition) is then False and
        # close() falls through to exit without re-joining.
        gw._loop.call_soon_threadsafe(gw._loop.stop)
        await asyncio.to_thread(gw._thread.join, _TIMEOUT)
        assert not gw._thread.is_alive()

        # Replace the underlying close with one that yields no coroutine, so
        # _call() fails immediately (no orphan coroutine to leak); close()
        # swallows the error (lines 208-209) and the dead-thread join branch is
        # skipped (line 212 condition False).
        gw._async.close = lambda: None  # type: ignore[method-assign,return-value]

        await asyncio.to_thread(gw.close)
        assert gw._closed is True
        assert not gw._thread.is_alive()
    finally:
        await asyncio.to_thread(gw.close)
