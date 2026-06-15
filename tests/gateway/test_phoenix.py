"""Unit tests for the pure wire codec in :mod:`warmbly.gateway._phoenix`.

These exercise the 5-element frame serializer in isolation: round-tripping,
the shapes of the convenience builders (heartbeat/join/push/leave), and the
monotonic ``ref``/``join_ref`` counters. No network or async code is involved.
"""

from __future__ import annotations

import json

from hypothesis import given
from hypothesis import strategies as st

from warmbly.gateway._phoenix import (
    EVENT_HEARTBEAT,
    EVENT_JOIN,
    EVENT_LEAVE,
    PHOENIX_TOPIC,
    VSN,
    Frame,
    PhoenixCodec,
    decode,
    encode,
)

# JSON-serializable payload values (kept to dict payloads, as the protocol uses).
_json_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**53), max_value=2**53),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
)
_json_values = st.recursive(
    _json_scalars,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(st.text(), children, max_size=4),
    ),
    max_leaves=8,
)
_payloads = st.dictionaries(st.text(), _json_values, max_size=5)


class TestConstants:
    def test_version_string(self) -> None:
        assert VSN == "2.0.0"

    def test_reserved_phoenix_topic(self) -> None:
        assert PHOENIX_TOPIC == "phoenix"


class TestRoundTrip:
    @given(
        join_ref=st.one_of(st.none(), st.text(min_size=1)),
        ref=st.one_of(st.none(), st.text(min_size=1)),
        topic=st.text(),
        event=st.text(),
        payload=_payloads,
    )
    def test_decode_encode_round_trips(
        self,
        join_ref: str | None,
        ref: str | None,
        topic: str,
        event: str,
        payload: dict[str, object],
    ) -> None:
        frame = Frame(join_ref, ref, topic, event, payload)
        decoded = decode(encode(frame))
        assert decoded == frame

    def test_encode_emits_compact_five_element_array(self) -> None:
        frame = Frame("1", "2", "org:o1", "phx_join", {"a": 1})
        raw = encode(frame)
        # No spaces between elements (compact separators).
        assert raw == '["1","2","org:o1","phx_join",{"a":1}]'
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 5

    def test_decode_broadcast_with_null_refs(self) -> None:
        raw = json.dumps([None, None, "org:o1", "CAMPAIGN_STARTED", {"id": 7}])
        frame = decode(raw)
        assert frame.join_ref is None
        assert frame.ref is None
        assert frame.topic == "org:o1"
        assert frame.event == "CAMPAIGN_STARTED"
        assert frame.payload == {"id": 7}

    def test_decode_accepts_bytes(self) -> None:
        raw = json.dumps([None, "5", "phoenix", "phx_reply", {"status": "ok"}])
        frame = decode(raw.encode("utf-8"))
        assert frame.topic == "phoenix"
        assert frame.payload == {"status": "ok"}

    def test_decode_coerces_non_dict_payload_to_dict(self) -> None:
        # A null payload becomes an empty dict; a scalar is wrapped.
        assert decode(json.dumps([None, None, "t", "e", None])).payload == {}
        assert decode(json.dumps([None, None, "t", "e", 5])).payload == {"_": 5}

    def test_decode_rejects_non_five_element_array(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="5-element"):
            decode(json.dumps([1, 2, 3]))
        with pytest.raises(ValueError, match="5-element"):
            decode(json.dumps({"not": "a list"}))


class TestBuilders:
    def test_heartbeat_shape(self) -> None:
        codec = PhoenixCodec()
        ref, raw = codec.heartbeat()
        join_ref, frame_ref, topic, event, payload = json.loads(raw)
        assert join_ref is None
        assert frame_ref == ref
        assert topic == PHOENIX_TOPIC
        assert event == EVENT_HEARTBEAT
        assert payload == {}

    def test_join_shape(self) -> None:
        codec = PhoenixCodec()
        join_ref, ref, raw = codec.join("org:o1", {"intents": ["CAMPAIGN"]})
        decoded = decode(raw)
        assert decoded.join_ref == join_ref
        assert decoded.ref == ref
        assert decoded.topic == "org:o1"
        assert decoded.event == EVENT_JOIN
        assert decoded.payload == {"intents": ["CAMPAIGN"]}

    def test_join_defaults_params_to_empty_dict(self) -> None:
        codec = PhoenixCodec()
        _join_ref, _ref, raw = codec.join("org:o1")
        assert decode(raw).payload == {}

    def test_push_shape_carries_join_ref(self) -> None:
        codec = PhoenixCodec()
        ref, raw = codec.push("org:o1", "ping", {"n": 1}, join_ref="7")
        decoded = decode(raw)
        assert decoded.join_ref == "7"
        assert decoded.ref == ref
        assert decoded.topic == "org:o1"
        assert decoded.event == "ping"
        assert decoded.payload == {"n": 1}

    def test_leave_shape(self) -> None:
        codec = PhoenixCodec()
        ref, raw = codec.leave("org:o1", join_ref="3")
        decoded = decode(raw)
        assert decoded.join_ref == "3"
        assert decoded.ref == ref
        assert decoded.event == EVENT_LEAVE
        assert decoded.payload == {}


class TestCounters:
    def test_ref_increments_monotonically(self) -> None:
        codec = PhoenixCodec()
        refs = [codec.next_ref() for _ in range(5)]
        assert refs == ["1", "2", "3", "4", "5"]

    def test_join_ref_increments_independently(self) -> None:
        codec = PhoenixCodec()
        assert codec.next_join_ref() == "1"
        assert codec.next_join_ref() == "2"

    def test_join_advances_both_counters(self) -> None:
        codec = PhoenixCodec()
        join_ref1, ref1, _ = codec.join("org:o1")
        join_ref2, ref2, _ = codec.join("org:o2")
        assert join_ref1 == "1"
        assert join_ref2 == "2"
        # Each join also mints a fresh message ref.
        assert ref1 == "1"
        assert ref2 == "2"

    def test_refs_are_unique_across_builders(self) -> None:
        codec = PhoenixCodec()
        hb_ref, _ = codec.heartbeat()
        _, push_ref, _ = codec.join("org:o1")
        leave_ref, _ = codec.leave("org:o1")
        assert len({hb_ref, push_ref, leave_ref}) == 3
