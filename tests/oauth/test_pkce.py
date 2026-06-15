"""Tests for the PKCE (RFC 7636, S256) helpers."""

from __future__ import annotations

import base64
import hashlib

from hypothesis import given, settings
from hypothesis import strategies as st

from warmbly.oauth import (
    challenge_for_verifier,
    generate_pkce_pair,
    verify_pkce,
)


def _expected_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def test_generate_pair_verifier_is_43_chars_unpadded() -> None:
    verifier, _challenge = generate_pkce_pair()
    # 32 random bytes -> 43-character base64url string, the RFC 7636 minimum.
    assert len(verifier) == 43
    assert "=" not in verifier


def test_generate_pair_verifier_uses_base64url_alphabet() -> None:
    verifier, _challenge = generate_pkce_pair()
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    assert set(verifier) <= allowed


def test_challenge_is_b64url_sha256_unpadded() -> None:
    verifier, challenge = generate_pkce_pair()
    assert challenge == _expected_challenge(verifier)
    assert "=" not in challenge


def test_challenge_for_verifier_matches_manual_computation() -> None:
    verifier = "a-known-fixed-verifier-value-1234567890abcd"
    assert challenge_for_verifier(verifier) == _expected_challenge(verifier)


def test_verify_pkce_accepts_matching_pair() -> None:
    verifier, challenge = generate_pkce_pair()
    assert verify_pkce(verifier, challenge) is True


def test_verify_pkce_rejects_mismatched_pair() -> None:
    _verifier, challenge = generate_pkce_pair()
    other_verifier, _ = generate_pkce_pair()
    assert verify_pkce(other_verifier, challenge) is False


def test_generate_pair_uniqueness_loop() -> None:
    verifiers = set()
    challenges = set()
    for _ in range(200):
        verifier, challenge = generate_pkce_pair()
        verifiers.add(verifier)
        challenges.add(challenge)
    assert len(verifiers) == 200
    assert len(challenges) == 200


@settings(max_examples=50)
@given(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1))
def test_challenge_property_matches_sha256(verifier: str) -> None:
    assert challenge_for_verifier(verifier) == _expected_challenge(verifier)
    assert verify_pkce(verifier, challenge_for_verifier(verifier)) is True
