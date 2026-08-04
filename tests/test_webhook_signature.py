"""Tests for warmbly.verify_webhook_signature.

The gateway signs ``"{unix_timestamp}.{raw_body}"`` and ships the result as
``X-Warmbly-Signature: t=<unix>,v1=<hex>``. These tests recompute that with the
stdlib so a change to the verifier that stops matching the server is caught.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from warmbly import WarmblyError, verify_webhook_signature

SECRET = "whsec_test_secret_value"


def _digest(payload: bytes, timestamp: int, secret: str = SECRET) -> str:
    """Compute the ``v1`` digest the dispatcher would send."""
    signed = f"{timestamp}.".encode() + payload
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def _header(
    payload: bytes, *, timestamp: int | None = None, secret: str = SECRET
) -> str:
    """Build a full ``X-Warmbly-Signature`` header value."""
    ts = int(time.time()) if timestamp is None else timestamp
    return f"t={ts},v1={_digest(payload, ts, secret)}"


def _make_payload() -> bytes:
    return json.dumps(
        {"event": "email.delivered", "data": {"id": "evt_123", "n": 7}}
    ).encode()


def test_valid_signature_returns_parsed_body() -> None:
    payload = _make_payload()

    result = verify_webhook_signature(
        payload=payload, signature=_header(payload), secret=SECRET
    )

    assert result == json.loads(payload)


def test_bytes_payload() -> None:
    payload = _make_payload()
    assert isinstance(payload, bytes)

    result = verify_webhook_signature(
        payload=payload, signature=_header(payload), secret=SECRET
    )

    assert result == json.loads(payload)


def test_str_payload() -> None:
    payload_bytes = _make_payload()
    payload_str = payload_bytes.decode()
    assert isinstance(payload_str, str)

    result = verify_webhook_signature(
        payload=payload_str, signature=_header(payload_bytes), secret=SECRET
    )

    assert result == json.loads(payload_str)


def test_str_and_bytes_payload_produce_same_result() -> None:
    payload_bytes = _make_payload()
    sig = _header(payload_bytes)

    from_bytes = verify_webhook_signature(
        payload=payload_bytes, signature=sig, secret=SECRET
    )
    from_str = verify_webhook_signature(
        payload=payload_bytes.decode(), signature=sig, secret=SECRET
    )

    assert from_bytes == from_str


def test_returns_parsed_json_dict_on_success() -> None:
    expected = {"event": "contact.created", "data": {"id": "c_42", "tags": ["a", "b"]}}
    payload = json.dumps(expected).encode()

    result = verify_webhook_signature(
        payload=payload, signature=_header(payload), secret=SECRET
    )

    assert isinstance(result, dict)
    assert result == expected


def test_accepts_any_matching_v1_during_rotation() -> None:
    """A rotating endpoint may be sent more than one candidate digest."""
    payload = _make_payload()
    ts = int(time.time())
    header = f"t={ts},v1={_digest(payload, ts, 'whsec_old')},v1={_digest(payload, ts)}"

    assert verify_webhook_signature(
        payload=payload, signature=header, secret=SECRET
    ) == json.loads(payload)


def test_tampered_payload_raises_warmbly_error() -> None:
    payload = _make_payload()
    sig = _header(payload)
    tampered = payload.replace(b"evt_123", b"evt_999")
    assert tampered != payload

    with pytest.raises(WarmblyError):
        verify_webhook_signature(payload=tampered, signature=sig, secret=SECRET)


def test_wrong_secret_raises_warmbly_error() -> None:
    payload = _make_payload()

    with pytest.raises(WarmblyError):
        verify_webhook_signature(
            payload=payload, signature=_header(payload), secret="whsec_wrong_secret"
        )


def test_tampered_digest_raises() -> None:
    payload = _make_payload()
    ts = int(time.time())
    good = _digest(payload, ts)
    # Flip the last hex char to guarantee a mismatch.
    flipped = "0" if good[-1] != "0" else "1"

    with pytest.raises(WarmblyError):
        verify_webhook_signature(
            payload=payload, signature=f"t={ts},v1={good[:-1] + flipped}", secret=SECRET
        )


def test_swapped_timestamp_raises() -> None:
    """The timestamp is inside the digest, so it cannot be re-stamped."""
    payload = _make_payload()
    ts = int(time.time())

    with pytest.raises(WarmblyError):
        verify_webhook_signature(
            payload=payload,
            signature=f"t={ts - 1},v1={_digest(payload, ts)}",
            secret=SECRET,
        )


def test_stale_timestamp_is_rejected_as_replay() -> None:
    payload = _make_payload()
    old = int(time.time()) - 3600

    with pytest.raises(WarmblyError, match="tolerance"):
        verify_webhook_signature(
            payload=payload,
            signature=_header(payload, timestamp=old),
            secret=SECRET,
        )


def test_tolerance_none_accepts_an_old_signature() -> None:
    payload = _make_payload()
    old = int(time.time()) - 86_400

    result = verify_webhook_signature(
        payload=payload,
        signature=_header(payload, timestamp=old),
        secret=SECRET,
        tolerance=None,
    )

    assert result == json.loads(payload)


@pytest.mark.parametrize(
    "header",
    [
        "",
        "v1=abc",
        "t=1700000000",
        "t=not-a-number,v1=abc",
        "sha256=deadbeef",
    ],
)
def test_malformed_header_raises(header: str) -> None:
    with pytest.raises(WarmblyError):
        verify_webhook_signature(
            payload=_make_payload(), signature=header, secret=SECRET
        )
