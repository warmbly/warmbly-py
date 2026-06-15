"""Unit tests for the gateway's pure-logic pieces and the sync wrapper.

These exercise :class:`ResumeTracker`, :class:`EventDispatcher`,
:class:`PresenceTracker`, :class:`Channel`/:class:`PendingReplies`, the
close-code classifier, the ``resume_failed`` callback path, and the blocking
:class:`GatewayClient` facade.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from websockets.exceptions import ConnectionClosed
from websockets.frames import Close

from conftest import FakeGateway
from warmbly.gateway import (
    AsyncGatewayClient,
    FatalDisconnect,
    GatewayClient,
    GatewayEvent,
    GatewayPushError,
)
from warmbly.gateway._channel import Channel, ChannelState, PendingReplies
from warmbly.gateway._connection import TransientDisconnect
from warmbly.gateway._events import EventDispatcher
from warmbly.gateway._presence import PresenceTracker
from warmbly.gateway._resume import ResumeTracker

_TIMEOUT = 5.0


# ===========================================================================
# ResumeTracker
# ===========================================================================
def test_resume_supports_resume() -> None:
    assert ResumeTracker.supports_resume("org:org_1") is True
    assert ResumeTracker.supports_resume("campaign:c_1") is False


def test_resume_observe_tracks_highest_seq() -> None:
    tracker = ResumeTracker()
    assert tracker.last_seq("org:o") is None

    tracker.observe("org:o", {"seq": 3})
    tracker.observe("org:o", {"seq": 1})  # lower, ignored
    tracker.observe("org:o", {"seq": 5})
    assert tracker.last_seq("org:o") == 5

    # Non-int seq is ignored entirely.
    tracker.observe("org:o", {"seq": "nope"})
    tracker.observe("org:o", {})
    assert tracker.last_seq("org:o") == 5


def test_resume_join_params() -> None:
    tracker = ResumeTracker()
    base = {"intents": ["X"]}

    # resume disabled -> unchanged
    assert tracker.join_params("org:o", base, resume=False) == base
    # non-resumable topic -> unchanged
    assert tracker.join_params("campaign:c", base, resume=True) == base
    # resumable but no prior seq -> unchanged
    assert tracker.join_params("org:o", base, resume=True) == base

    tracker.observe("org:o", {"seq": 7})
    merged = tracker.join_params("org:o", base, resume=True)
    assert merged == {"intents": ["X"], "resume": {"last_seq": 7}}
    # The original params are not mutated.
    assert "resume" not in base


def test_resume_apply_resumed_and_reset() -> None:
    tracker = ResumeTracker()
    tracker.observe("org:o", {"seq": 2})

    tracker.apply_resumed("org:o", {"current_seq": 9})
    assert tracker.last_seq("org:o") == 9
    # Lower current_seq does not regress.
    tracker.apply_resumed("org:o", {"current_seq": 4})
    assert tracker.last_seq("org:o") == 9
    # Missing/non-int current_seq is a no-op.
    tracker.apply_resumed("org:o", {})
    assert tracker.last_seq("org:o") == 9

    tracker.reset("org:o")
    assert tracker.last_seq("org:o") is None
    # Resetting an unknown topic is harmless.
    tracker.reset("org:unknown")


# ===========================================================================
# EventDispatcher
# ===========================================================================
async def _noop(_topic: str, _payload: dict[str, Any]) -> None:
    return None


def test_dispatcher_register_exact_and_any() -> None:
    d = EventDispatcher()
    d.register(("org:o", "EMAIL_SENT"), _noop)
    d.register("EMAIL_SENT", _noop)

    handlers = d.handlers_for("org:o", "EMAIL_SENT")
    assert len(handlers) == 2
    # An unrelated topic gets only the any-topic handler.
    assert d.handlers_for("org:other", "EMAIL_SENT") == [_noop]
    # An unrelated event gets nothing.
    assert d.handlers_for("org:o", "OTHER") == []


def test_dispatcher_register_returns_handler() -> None:
    d = EventDispatcher()
    assert d.register("X", _noop) is _noop


def test_dispatcher_unregister() -> None:
    d = EventDispatcher()
    d.register(("org:o", "E"), _noop)
    d.register("E", _noop)

    d.unregister(("org:o", "E"), _noop)
    assert d.handlers_for("org:o", "E") == [_noop]
    d.unregister("E", _noop)
    assert d.handlers_for("org:o", "E") == []
    # Unregistering something absent is a no-op (no error).
    d.unregister("MISSING", _noop)
    d.unregister(("a", "b"), _noop)


@pytest.mark.anyio
async def test_dispatcher_wait_for_and_resolve() -> None:
    d = EventDispatcher()
    fut = d.wait_for("EMAIL_SENT")
    # A non-matching event leaves the waiter pending.
    d.resolve_waiters("org:o", "OTHER", {"x": 1})
    assert not fut.done()
    # A matching event resolves it.
    d.resolve_waiters("org:o", "EMAIL_SENT", {"id": "e1"})
    assert await fut == {"id": "e1"}


@pytest.mark.anyio
async def test_dispatcher_wait_for_check_predicate() -> None:
    d = EventDispatcher()
    fut = d.wait_for(None, check=lambda _t, p: p.get("pct") == 100)
    d.resolve_waiters("org:o", "P", {"pct": 50})
    assert not fut.done()
    d.resolve_waiters("org:o", "P", {"pct": 100})
    assert await fut == {"pct": 100}


@pytest.mark.anyio
async def test_dispatcher_resolve_with_no_waiters_is_noop() -> None:
    d = EventDispatcher()
    # Should not raise with an empty waiter list.
    d.resolve_waiters("org:o", "E", {})


@pytest.mark.anyio
async def test_dispatcher_fail_waiters() -> None:
    d = EventDispatcher()
    fut = d.wait_for("E")
    err = RuntimeError("dead")
    d.fail_waiters(err)
    with pytest.raises(RuntimeError, match="dead"):
        await fut
    # Already-resolved/failed waiters are dropped; failing again is a no-op.
    d.fail_waiters(err)


@pytest.mark.anyio
async def test_dispatcher_skips_already_done_waiter() -> None:
    d = EventDispatcher()
    fut = d.wait_for("E")
    fut.cancel()
    # resolve_waiters must skip the cancelled (done) future cleanly.
    d.resolve_waiters("org:o", "E", {"x": 1})


# ===========================================================================
# PresenceTracker
# ===========================================================================
def test_presence_state_then_diff() -> None:
    p = PresenceTracker()
    assert p.presence("org:o") == {}

    p.apply(
        "org:o",
        "presence_state",
        {
            "u1": {"metas": [{"name": "Ada"}]},
            "u2": {"metas": [{"name": "Bob"}]},
            "bad": "not-a-dict",
        },
    )
    snap = p.presence("org:o")
    assert set(snap) == {"u1", "u2"}

    p.apply(
        "org:o",
        "presence_diff",
        {
            "joins": {"u3": {"metas": [{"name": "Cy"}]}, "skip": 1},
            "leaves": {"u1": {"metas": []}},
        },
    )
    snap = p.presence("org:o")
    assert set(snap) == {"u2", "u3"}

    # Unknown event types are ignored.
    p.apply("org:o", "something_else", {})
    assert set(p.presence("org:o")) == {"u2", "u3"}


def test_presence_diff_without_prior_state() -> None:
    p = PresenceTracker()
    p.apply("org:o", "presence_diff", {"joins": {"u1": {"metas": []}}})
    assert set(p.presence("org:o")) == {"u1"}
    # leaves/joins that are not dicts are skipped.
    p.apply("org:o", "presence_diff", {"joins": "x", "leaves": "y"})
    assert set(p.presence("org:o")) == {"u1"}


def test_presence_clear() -> None:
    p = PresenceTracker()
    p.apply("org:o", "presence_state", {"u1": {"metas": []}})
    p.clear("org:o")
    assert p.presence("org:o") == {}
    # Clearing an unknown topic is harmless.
    p.clear("org:unknown")


def test_presence_returns_copy() -> None:
    p = PresenceTracker()
    p.apply("org:o", "presence_state", {"u1": {"metas": []}})
    snap = p.presence("org:o")
    snap["u1"]["mutated"] = True
    # The internal state is unaffected by mutating the returned copy.
    assert "mutated" not in p.presence("org:o")["u1"]


# ===========================================================================
# Channel
# ===========================================================================
def test_channel_lifecycle() -> None:
    ch = Channel("org:o", {"intents": []}, resume=True)
    assert ch.state == ChannelState.CLOSED
    assert ch.is_joined is False

    ch.mark_joining("ref-1")
    assert ch.state == ChannelState.JOINING
    assert ch.join_ref == "ref-1"

    ch.mark_joined()
    assert ch.is_joined is True

    ch.mark_errored()
    assert ch.state == ChannelState.ERRORED

    ch.mark_closed()
    assert ch.state == ChannelState.CLOSED
    assert ch.join_ref is None


# ===========================================================================
# PendingReplies
# ===========================================================================
@pytest.mark.anyio
async def test_pending_resolve_ok() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    assert pending.resolve(
        "r1", "org:o", "ping", {"status": "ok", "response": {"x": 1}}
    )
    assert await fut == {"x": 1}


@pytest.mark.anyio
async def test_pending_resolve_error_raises_push_error() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    ok = pending.resolve(
        "r1", "org:o", "ping", {"status": "error", "response": {"reason": "nope"}}
    )
    assert ok
    with pytest.raises(GatewayPushError) as excinfo:
        await fut
    assert excinfo.value.topic == "org:o"
    assert excinfo.value.event == "ping"
    assert excinfo.value.response == {"reason": "nope"}


@pytest.mark.anyio
async def test_pending_resolve_unknown_ref() -> None:
    pending = PendingReplies()
    # No future registered for this ref.
    assert pending.resolve("nope", "org:o", "e", {"status": "ok"}) is False


@pytest.mark.anyio
async def test_pending_resolve_non_dict_response() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    pending.resolve("r1", "org:o", "e", {"status": "ok", "response": "scalar"})
    assert await fut == {}


@pytest.mark.anyio
async def test_pending_fail_all() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    pending.fail_all(TransientDisconnect("lost"))
    with pytest.raises(TransientDisconnect):
        await fut


def test_push_error_default_reason() -> None:
    err = GatewayPushError("org:o", "e", {})
    assert "error" in str(err)
    err2 = GatewayPushError("org:o", "e", {"error": "boom"})
    assert "boom" in str(err2)


# ===========================================================================
# close-code classification (_handle_close)
# ===========================================================================
def _closed(code: int, reason: str = "") -> ConnectionClosed:
    close = Close(code, reason)
    return ConnectionClosed(close, None)


# The SDK reads the (lib-)deprecated ``ConnectionClosed.code`` / ``.reason``
# properties, which emit DeprecationWarnings from ``websockets`` we cannot fix
# in ``src/``.
_WS_CODE_DEPRECATION = pytest.mark.filterwarnings(
    "ignore:ConnectionClosed.code is deprecated:DeprecationWarning",
    "ignore:ConnectionClosed.reason is deprecated:DeprecationWarning",
)


@_WS_CODE_DEPRECATION
def test_handle_close_fatal_code() -> None:
    client = AsyncGatewayClient(token="t", base_url="ws://x")
    with pytest.raises(FatalDisconnect) as excinfo:
        client._handle_close(_closed(4004))
    assert excinfo.value.code == 4004


@_WS_CODE_DEPRECATION
def test_handle_close_transient_code() -> None:
    client = AsyncGatewayClient(token="t", base_url="ws://x")
    with pytest.raises(TransientDisconnect):
        client._handle_close(_closed(1006))


@_WS_CODE_DEPRECATION
def test_handle_close_backpressure_sets_retry_after() -> None:
    client = AsyncGatewayClient(token="t", base_url="ws://x")
    with pytest.raises(TransientDisconnect):
        client._handle_close(_closed(4007, '{"retry_after_ms": 2500}'))
    assert client._retry_after == 2.5


@_WS_CODE_DEPRECATION
def test_extract_retry_after_variants() -> None:
    client = AsyncGatewayClient(token="t", base_url="ws://x")
    assert client._extract_retry_after(_closed(4007, "")) is None
    assert client._extract_retry_after(_closed(4007, "not-json")) is None
    assert client._extract_retry_after(_closed(4007, "[1,2,3]")) is None
    assert client._extract_retry_after(_closed(4007, '{"x": 1}')) is None
    assert client._extract_retry_after(_closed(4007, '{"retry_after_ms": 1000}')) == 1.0


# ===========================================================================
# resume_failed callback wiring
# ===========================================================================
@pytest.mark.anyio
async def test_resume_failed_callback_invoked(fake_gateway: FakeGateway) -> None:
    seen: asyncio.Future[tuple[str, dict[str, Any]]] = (
        asyncio.get_running_loop().create_future()
    )

    async def _cb(topic: str, payload: dict[str, Any]) -> None:
        if not seen.done():
            seen.set_result((topic, payload))

    client = AsyncGatewayClient(
        token="t", base_url=fake_gateway.base_url, on_resume_failed=_cb
    )
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
    try:
        await asyncio.wait_for(client.subscribe("org:org_1"), timeout=_TIMEOUT)
        client._resume.observe("org:org_1", {"seq": 5})
        await fake_gateway.broadcast(
            "org:org_1", "resume_failed", {"reason": "too_old"}
        )
        topic, payload = await asyncio.wait_for(seen, timeout=_TIMEOUT)
        assert topic == "org:org_1"
        assert payload == {"reason": "too_old"}
        # The tracked seq was reset by the resume_failed handler.
        assert client._resume.last_seq("org:org_1") is None
    finally:
        await client.close()


@pytest.mark.anyio
async def test_resume_failed_callback_exception_isolated(
    fake_gateway: FakeGateway,
) -> None:
    started: asyncio.Event = asyncio.Event()

    async def _cb(_topic: str, _payload: dict[str, Any]) -> None:
        started.set()
        raise RuntimeError("handler boom")

    client = AsyncGatewayClient(
        token="t", base_url=fake_gateway.base_url, on_resume_failed=_cb
    )
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
    try:
        await asyncio.wait_for(client.subscribe("org:org_1"), timeout=_TIMEOUT)
        await fake_gateway.broadcast("org:org_1", "resume_failed", {})
        await asyncio.wait_for(started.wait(), timeout=_TIMEOUT)
        # The client survives a raising callback: it stays usable.
        reply = await asyncio.wait_for(
            client.push("org:org_1", "ping", {}), timeout=_TIMEOUT
        )
        assert reply == {}
    finally:
        await client.close()


# ===========================================================================
# sync GatewayClient facade
# ===========================================================================
@pytest.mark.filterwarnings(
    "ignore:'asyncio.iscoroutinefunction' is deprecated:DeprecationWarning"
)
@pytest.mark.anyio
async def test_sync_gateway_client(fake_gateway: FakeGateway) -> None:
    # Run the blocking client off the event loop thread so it does not deadlock.
    base_url = fake_gateway.base_url

    def _drive() -> dict[str, Any]:
        gw = GatewayClient(token="t", base_url=base_url)

        @gw.on_event(GatewayEvent.EMAIL_SENT)
        def _handler(_topic: str, _payload: dict[str, Any]) -> None:
            return None

        @gw.on(("org:org_1", GatewayEvent.CONTACT_CREATED))
        async def _async_handler(_topic: str, _payload: dict[str, Any]) -> None:
            return None

        gw.connect()
        reply = gw.subscribe("org:org_1", intents=["EMAIL"])
        push_reply = gw.push("org:org_1", "ping", {"n": 1})
        assert push_reply == {}
        assert gw.presence("org:org_1") == {}
        gw.unsubscribe("org:org_1")
        gw.close()
        return reply

    reply = await asyncio.to_thread(_drive)
    assert reply == {"seq": 0, "resume_supported": True}
    assert fake_gateway.join_params["org:org_1"] == {"intents": ["EMAIL"]}


@pytest.mark.anyio
async def test_sync_gateway_close_is_idempotent(fake_gateway: FakeGateway) -> None:
    base_url = fake_gateway.base_url

    def _drive() -> None:
        gw = GatewayClient(token="t", base_url=base_url)
        gw.connect()
        gw.close()

    # A single connect/close cycle on the background loop must complete cleanly.
    await asyncio.to_thread(_drive)


@pytest.mark.anyio
async def test_sync_gateway_wait_for(fake_gateway: FakeGateway) -> None:
    base_url = fake_gateway.base_url
    gw = GatewayClient(token="t", base_url=base_url)
    try:
        await asyncio.to_thread(gw.connect)
        await asyncio.to_thread(gw.subscribe, "org:org_1")

        # Block the sync wait_for in a worker thread, then broadcast from this
        # (the server's) loop so the receive loop dispatches it.
        waiter = asyncio.ensure_future(
            asyncio.to_thread(gw.wait_for, GatewayEvent.EMAIL_SENT, timeout=_TIMEOUT)
        )
        await asyncio.sleep(0.05)
        await fake_gateway.broadcast(
            "org:org_1", GatewayEvent.EMAIL_SENT, {"email_id": "e1"}
        )
        payload = await asyncio.wait_for(waiter, timeout=_TIMEOUT)
        assert payload == {"email_id": "e1"}
    finally:
        await asyncio.to_thread(gw.close)
