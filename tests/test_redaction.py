"""Tests for the secret-redaction logging helpers."""

from __future__ import annotations

import pytest

from warmbly._utils._logs import redact, redact_headers

_REDACTED = "[redacted]"


# ---------------------------------------------------------------------------
# Token-prefix scrubbing in strings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "token",
    [
        "wmbly_secretvalue123",
        "wmat_AccessToken-456",
        "wmrt_RefreshToken_789",
        "wmac_authcode0",
        "wmcid_ClientId1",
        "wmcs_ClientSecret2",
    ],
)
def test_redact_scrubs_each_token_prefix(token: str) -> None:
    assert redact(token) == _REDACTED


def test_redact_scrubs_token_embedded_in_text() -> None:
    out = redact("Authorization failed for wmat_abc123DEF in request")
    assert "wmat_abc123DEF" not in out
    assert _REDACTED in out
    # Surrounding non-secret text is preserved.
    assert out.startswith("Authorization failed for ")
    assert out.endswith(" in request")


def test_redact_scrubs_multiple_tokens_in_one_string() -> None:
    out = redact("first wmat_one second wmrt_two")
    assert "wmat_one" not in out
    assert "wmrt_two" not in out
    assert out.count(_REDACTED) == 2


def test_redact_leaves_non_token_strings_alone() -> None:
    assert redact("just a normal log line") == "just a normal log line"
    # A word that merely starts with 'wm' but lacks the prefix shape is kept.
    assert redact("wmx_notatoken") == "wmx_notatoken"
    assert redact("wm_nope") == "wm_nope"


# ---------------------------------------------------------------------------
# Sensitive field-name scrubbing in mappings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "client_secret",
        "code",
        "code_verifier",
        "refresh_token",
        "access_token",
        "secret",
        "password",
        "token",
    ],
)
def test_redact_scrubs_sensitive_field_names(field: str) -> None:
    out = redact({field: "super-sensitive"})
    assert out == {field: _REDACTED}


def test_redact_field_name_is_case_insensitive() -> None:
    out = redact({"Password": "x", "ACCESS_TOKEN": "y"})
    assert out == {"Password": _REDACTED, "ACCESS_TOKEN": _REDACTED}


def test_redact_nested_mapping() -> None:
    out = redact(
        {
            "ok": "visible",
            "creds": {"password": "hunter2", "username": "alice"},
        }
    )
    assert out == {
        "ok": "visible",
        "creds": {"password": _REDACTED, "username": "alice"},
    }


def test_redact_list_and_tuple_recursion() -> None:
    as_list = redact(["wmat_tok", {"secret": "s", "fine": "f"}, "plain"])
    assert as_list == [_REDACTED, {"secret": _REDACTED, "fine": "f"}, "plain"]

    as_tuple = redact(("wmrt_tok", "plain"))
    assert as_tuple == (_REDACTED, "plain")
    assert isinstance(as_tuple, tuple)


def test_redact_non_secret_field_values_pass_through() -> None:
    payload = {"name": "bob", "count": 5, "active": True, "ratio": 1.5}
    assert redact(payload) == payload


@pytest.mark.parametrize("value", [123, 3.14, True, None])
def test_redact_non_string_scalars_pass_through(value: object) -> None:
    assert redact(value) is value


# ---------------------------------------------------------------------------
# Header redaction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "header",
    [
        "Authorization",
        "Proxy-Authorization",
        "X-Api-Key",
        "Api-Key",
        "X-Warmbly-Signature",
        "Cookie",
        "Set-Cookie",
    ],
)
def test_redact_headers_masks_sensitive_headers(header: str) -> None:
    out = redact_headers({header: "Bearer secret-value"})
    assert out == {header: _REDACTED}


def test_redact_headers_is_case_insensitive() -> None:
    out = redact_headers({"authorization": "Bearer x", "X-WARMBLY-SIGNATURE": "sig"})
    assert out == {"authorization": _REDACTED, "X-WARMBLY-SIGNATURE": _REDACTED}


def test_redact_headers_passes_through_non_sensitive() -> None:
    out = redact_headers({"Content-Type": "application/json", "Accept": "*/*"})
    assert out == {"Content-Type": "application/json", "Accept": "*/*"}


def test_redact_headers_scrubs_tokens_in_non_sensitive_values() -> None:
    # A leaked token in an otherwise-innocent header is still scrubbed.
    out = redact_headers({"X-Custom": "value wmat_leaked tail"})
    assert "wmat_leaked" not in out["X-Custom"]
    assert _REDACTED in out["X-Custom"]
    assert out["X-Custom"].startswith("value ")


def test_redact_headers_masks_signature_and_passes_others() -> None:
    out = redact_headers(
        {
            "Authorization": "Bearer wmat_abc",
            "X-Warmbly-Signature": "t=1,v1=deadbeef",
            "Content-Type": "application/json",
        }
    )
    assert out["Authorization"] == _REDACTED
    assert out["X-Warmbly-Signature"] == _REDACTED
    assert out["Content-Type"] == "application/json"
