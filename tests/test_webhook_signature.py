"""Tests for warmbly.verify_webhook_signature."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from warmbly import WarmblyError, verify_webhook_signature

SECRET = "whsec_test_secret_value"


def _sign(payload: bytes, secret: str = SECRET) -> str:
    """Compute the expected HMAC-SHA256 hexdigest using only the stdlib."""
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _make_payload() -> bytes:
    return json.dumps(
        {"event": "email.delivered", "data": {"id": "evt_123", "n": 7}}
    ).encode()


def test_valid_signature_with_sha256_prefix() -> None:
    payload = _make_payload()
    sig = "sha256=" + _sign(payload)

    result = verify_webhook_signature(payload=payload, signature=sig, secret=SECRET)

    assert result == json.loads(payload)


def test_valid_signature_without_prefix() -> None:
    payload = _make_payload()
    sig = _sign(payload)

    result = verify_webhook_signature(payload=payload, signature=sig, secret=SECRET)

    assert result == json.loads(payload)


def test_bytes_payload() -> None:
    payload = _make_payload()
    assert isinstance(payload, bytes)
    sig = _sign(payload)

    result = verify_webhook_signature(payload=payload, signature=sig, secret=SECRET)

    assert result == json.loads(payload)


def test_str_payload() -> None:
    payload_bytes = _make_payload()
    payload_str = payload_bytes.decode()
    assert isinstance(payload_str, str)
    # Signature is over the encoded bytes, which must equal payload_str.encode().
    sig = _sign(payload_str.encode())

    result = verify_webhook_signature(payload=payload_str, signature=sig, secret=SECRET)

    assert result == json.loads(payload_str)


def test_str_and_bytes_payload_produce_same_result() -> None:
    payload_bytes = _make_payload()
    sig = _sign(payload_bytes)

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
    sig = _sign(payload)

    result = verify_webhook_signature(payload=payload, signature=sig, secret=SECRET)

    assert isinstance(result, dict)
    assert result == expected


def test_tampered_payload_raises_warmbly_error() -> None:
    payload = _make_payload()
    sig = _sign(payload)
    tampered = payload.replace(b"evt_123", b"evt_999")
    assert tampered != payload

    with pytest.raises(WarmblyError):
        verify_webhook_signature(payload=tampered, signature=sig, secret=SECRET)


def test_wrong_secret_raises_warmbly_error() -> None:
    payload = _make_payload()
    # Signature was generated with SECRET, but verification uses a different secret.
    sig = _sign(payload, secret=SECRET)

    with pytest.raises(WarmblyError):
        verify_webhook_signature(
            payload=payload, signature=sig, secret="whsec_wrong_secret"
        )


def test_tampered_signature_with_prefix_raises() -> None:
    payload = _make_payload()
    good = _sign(payload)
    # Flip the last hex char to guarantee a mismatch.
    last = good[-1]
    flipped = "0" if last != "0" else "1"
    bad = "sha256=" + good[:-1] + flipped

    with pytest.raises(WarmblyError):
        verify_webhook_signature(payload=payload, signature=bad, secret=SECRET)
