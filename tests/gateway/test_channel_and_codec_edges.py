"""Edge-branch coverage for the gateway support modules.

These close the last uncovered branches in :mod:`warmbly.gateway._channel`
(``PendingReplies.fail_all`` skipping an already-done future) and
:mod:`warmbly.gateway._events` (``EventDispatcher.fail_waiters`` skipping an
already-done waiter), plus a couple of small codec/state edges. No network or
async I/O beyond bare ``asyncio`` futures is involved.
"""

from __future__ import annotations

import json

import pytest

from warmbly.gateway._channel import (
    Channel,
    ChannelState,
    GatewayPushError,
    PendingReplies,
)
from warmbly.gateway._events import EventDispatcher
from warmbly.gateway._phoenix import Frame, decode, encode
from warmbly.gateway._presence import PresenceTracker
from warmbly.gateway._resume import ResumeTracker


# ===========================================================================
# PendingReplies.fail_all — the 141->140 branch (already-done future skipped)
# ===========================================================================
@pytest.mark.anyio
async def test_fail_all_skips_already_done_future() -> None:
    pending = PendingReplies()
    done_fut = pending.create("done")
    live_fut = pending.create("live")

    # Complete one future directly so it remains registered in _pending
    # (resolve would pop it). fail_all must then skip it because it is already
    # done (hits the `if not future.done()` false branch, 141->140).
    done_fut.set_result({"x": 9})
    assert done_fut.done()

    pending.fail_all(RuntimeError("disconnected"))

    # The pre-completed future kept its original result, untouched by fail_all.
    assert await done_fut == {"x": 9}
    # The still-pending future was failed with the supplied exception.
    with pytest.raises(RuntimeError, match="disconnected"):
        await live_fut


@pytest.mark.anyio
async def test_fail_all_empty_is_noop() -> None:
    pending = PendingReplies()
    # No pending futures: must not raise.
    pending.fail_all(RuntimeError("nothing here"))


@pytest.mark.anyio
async def test_pending_create_and_resolve_unknown_ref() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    # Resolving an unknown ref is a no-op returning False; the live future
    # remains pending.
    assert pending.resolve("other", "org:o", "e", {"status": "ok"}) is False
    assert not fut.done()
    assert pending.resolve("r1", "org:o", "e", {"status": "ok", "response": {}})
    assert await fut == {}


@pytest.mark.anyio
async def test_pending_resolve_error_raises_push_error() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    assert pending.resolve(
        "r1", "org:o", "ping", {"status": "error", "response": {"reason": "bad"}}
    )
    with pytest.raises(GatewayPushError) as excinfo:
        await fut
    assert excinfo.value.topic == "org:o"
    assert excinfo.value.event == "ping"


@pytest.mark.anyio
async def test_pending_resolve_done_ref_returns_true_without_clobbering() -> None:
    pending = PendingReplies()
    fut = pending.create("r1")
    fut.set_result({"first": True})
    # The future is already done; resolve pops it and returns True without
    # raising InvalidStateError (covers the `future.done()` true branch).
    assert pending.resolve("r1", "org:o", "e", {"status": "ok"}) is True
    assert await fut == {"first": True}


# ===========================================================================
# EventDispatcher.fail_waiters — the 189->188 branch (done waiter skipped)
# ===========================================================================
@pytest.mark.anyio
async def test_fail_waiters_skips_already_done_waiter() -> None:
    d = EventDispatcher()
    done_waiter = d.wait_for("E")
    live_waiter = d.wait_for("E")

    # Complete one waiter's future directly so it stays in the internal list
    # (resolve_waiters would prune it). fail_waiters must then skip it because
    # it is already done (covers the `if not waiter.future.done()` false
    # branch, 189->188).
    done_waiter.set_result({"done": True})
    assert done_waiter.done()

    d.fail_waiters(RuntimeError("fatal"))

    assert await done_waiter == {"done": True}
    with pytest.raises(RuntimeError, match="fatal"):
        await live_waiter


# ===========================================================================
# Channel state machine — full transition sweep
# ===========================================================================
def test_channel_transitions_and_join_ref() -> None:
    ch = Channel("org:o", {"intents": []}, resume=False)
    assert ch.resume is False
    assert ch.state == ChannelState.CLOSED
    assert ch.join_ref is None
    assert ch.is_joined is False

    ch.mark_joining("jr-1")
    assert ch.state == ChannelState.JOINING
    assert ch.join_ref == "jr-1"
    assert ch.is_joined is False

    ch.mark_joined()
    assert ch.state == ChannelState.JOINED
    assert ch.is_joined is True
    # join_ref is retained through a successful join.
    assert ch.join_ref == "jr-1"

    ch.mark_errored()
    assert ch.state == ChannelState.ERRORED
    assert ch.is_joined is False
    # Errored keeps the join_ref so a rejoin can correlate.
    assert ch.join_ref == "jr-1"

    ch.mark_closed()
    assert ch.state == ChannelState.CLOSED
    assert ch.join_ref is None
    assert ch.is_joined is False


# ===========================================================================
# Codec edges
# ===========================================================================
def test_decode_null_ref_and_null_payload() -> None:
    raw = json.dumps([None, None, "org:o", "EVT", None])
    frame = decode(raw)
    assert frame.join_ref is None
    assert frame.ref is None
    assert frame.payload == {}


def test_decode_wraps_scalar_payload() -> None:
    assert decode(json.dumps([None, None, "t", "e", 5])).payload == {"_": 5}


def test_decode_coerces_numeric_refs_to_str() -> None:
    frame = decode(json.dumps([1, 2, "t", "e", {}]))
    assert frame.join_ref == "1"
    assert frame.ref == "2"


def test_decode_rejects_malformed_frames() -> None:
    with pytest.raises(ValueError, match="5-element"):
        decode(json.dumps([1, 2, 3]))
    with pytest.raises(ValueError, match="5-element"):
        decode(json.dumps({"not": "a list"}))


def test_encode_decode_round_trip() -> None:
    frame = Frame("1", "2", "org:o", "phx_join", {"a": [1, 2]})
    assert decode(encode(frame)) == frame


# ===========================================================================
# ResumeTracker / PresenceTracker small branches
# ===========================================================================
def test_resume_observe_ignores_missing_and_non_int_seq() -> None:
    tracker = ResumeTracker()
    tracker.observe("org:o", {})  # no seq
    tracker.observe("org:o", {"seq": "x"})  # non-int seq
    assert tracker.last_seq("org:o") is None


def test_resume_apply_resumed_advances_and_guards() -> None:
    tracker = ResumeTracker()
    # apply_resumed on a topic with no prior seq sets it.
    tracker.apply_resumed("org:o", {"current_seq": 4})
    assert tracker.last_seq("org:o") == 4
    # Lower / missing current_seq do not regress.
    tracker.apply_resumed("org:o", {"current_seq": 1})
    tracker.apply_resumed("org:o", {})
    assert tracker.last_seq("org:o") == 4


def test_presence_diff_with_empty_joins_and_leaves() -> None:
    p = PresenceTracker()
    p.apply("org:o", "presence_diff", {"joins": {}, "leaves": {}})
    assert p.presence("org:o") == {}
    # Unknown event type is ignored.
    p.apply("org:o", "unknown", {"joins": {"u1": {"metas": []}}})
    assert p.presence("org:o") == {}
