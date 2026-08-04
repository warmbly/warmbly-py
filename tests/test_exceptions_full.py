"""Exhaustive coverage for :mod:`warmbly._exceptions`.

Complements ``tests/test_exceptions.py`` by covering remaining branches:
the unmapped-4xx / >=500 fallbacks, ``_extract_message`` edge cases,
``APIError.code`` for non-dict bodies, the connection/timeout ``cause``
branches, ``APIResponseValidationError`` attributes, and ``GatewayError``.
"""

from __future__ import annotations

import pytest

from warmbly import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    GatewayError,
    InternalServerError,
    NotFoundError,
    OAuthError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
    WarmblyError,
)
from warmbly._exceptions import _extract_message, make_status_error

# ---------------------------------------------------------------------------
# make_status_error: full status-code mapping including fallbacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (409, ConflictError),
        (422, UnprocessableEntityError),
        (429, RateLimitError),
    ],
)
def test_make_status_error_maps_each_known_code(
    status_code: int, expected: type[APIStatusError]
) -> None:
    err = make_status_error(
        status_code=status_code,
        request_id="rid",
        headers={"X-Request-Id": "rid"},
        body={"message": "boom"},
    )
    assert type(err) is expected
    assert err.status_code == status_code
    assert err.message == "boom"
    assert err.request_id == "rid"


def test_make_status_error_unmapped_4xx_is_plain_status_error() -> None:
    err = make_status_error(
        status_code=418,
        request_id=None,
        headers=None,
        body=None,
    )
    assert type(err) is APIStatusError
    assert err.status_code == 418
    assert err.message == "HTTP 418"


def test_make_status_error_5xx_is_internal_server_error() -> None:
    err = make_status_error(
        status_code=500,
        request_id=None,
        headers=None,
        body={"message": "down"},
    )
    assert type(err) is InternalServerError
    assert err.status_code == 500
    assert err.message == "down"


def test_make_status_error_rate_limit_carries_retry_after() -> None:
    err = make_status_error(
        status_code=429,
        request_id="rid",
        headers={"Retry-After": "30"},
        body={"message": "slow down"},
        retry_after=30.0,
    )
    assert type(err) is RateLimitError
    assert err.retry_after == 30.0
    assert err.headers == {"Retry-After": "30"}
    assert err.request_id == "rid"


def test_make_status_error_rate_limit_retry_after_defaults_none() -> None:
    err = make_status_error(
        status_code=429,
        request_id=None,
        headers=None,
        body=None,
    )
    assert type(err) is RateLimitError
    assert err.retry_after is None
    assert err.message == "HTTP 429"


# ---------------------------------------------------------------------------
# _extract_message
# ---------------------------------------------------------------------------


def test_extract_message_prefers_message_over_error() -> None:
    assert _extract_message({"message": "m", "error": "e"}) == "m"


def test_extract_message_falls_back_to_error_field() -> None:
    assert _extract_message({"error": "e"}) == "e"


def test_extract_message_returns_none_when_empty_dict() -> None:
    assert _extract_message({}) is None


def test_extract_message_returns_none_for_non_str_message() -> None:
    # message is present but not a string -> fallback
    assert _extract_message({"message": 123}) is None
    assert _extract_message({"message": ["x"]}) is None


def test_extract_message_returns_none_for_non_dict_body() -> None:
    assert _extract_message(None) is None
    assert _extract_message("a plain string") is None
    assert _extract_message(42) is None
    assert _extract_message(["list"]) is None


def test_make_status_error_uses_fallback_when_value_not_str() -> None:
    err = make_status_error(
        status_code=400,
        request_id=None,
        headers=None,
        body={"message": 999},
    )
    assert err.message == "HTTP 400"


# ---------------------------------------------------------------------------
# APIError.code
# ---------------------------------------------------------------------------


def test_api_error_code_from_dict_body() -> None:
    err = APIError("oops", body={"code": "bad_param"})
    assert err.code == "bad_param"
    assert err.body == {"code": "bad_param"}
    assert err.message == "oops"


def test_api_error_code_none_when_missing_in_dict() -> None:
    err = APIError("oops", body={"message": "x"})
    assert err.code is None


def test_api_error_code_none_for_non_dict_body() -> None:
    assert APIError("oops", body="string").code is None
    assert APIError("oops", body=None).code is None
    assert APIError("oops", body=["a"]).code is None


def test_api_error_default_body_is_none() -> None:
    err = APIError("oops")
    assert err.body is None
    assert err.code is None


# ---------------------------------------------------------------------------
# APIStatusError.__str__ both branches
# ---------------------------------------------------------------------------


def test_status_error_str_with_request_id() -> None:
    err = APIStatusError("boom", status_code=400, request_id="req_1")
    assert str(err) == "[400] boom (request_id: req_1)"


def test_status_error_str_without_request_id() -> None:
    err = APIStatusError("boom", status_code=400)
    assert str(err) == "[400] boom"
    assert err.request_id is None
    assert err.headers == {}


def test_status_error_str_empty_request_id_omits_suffix() -> None:
    # falsy request_id ("") takes the no-suffix branch
    err = APIStatusError("boom", status_code=400, request_id="")
    assert str(err) == "[400] boom"


# ---------------------------------------------------------------------------
# APIConnectionError / APITimeoutError cause handling
# ---------------------------------------------------------------------------


def test_connection_error_default_message_no_cause() -> None:
    err = APIConnectionError()
    assert err.message == "Connection error."
    assert err.__cause__ is None


def test_connection_error_custom_message_with_cause() -> None:
    cause = ValueError("socket dead")
    err = APIConnectionError(message="nope", cause=cause)
    assert err.message == "nope"
    assert err.__cause__ is cause


def test_timeout_error_message_and_no_cause() -> None:
    err = APITimeoutError()
    assert err.message == "Request timed out."
    assert err.__cause__ is None


def test_timeout_error_sets_cause_when_given() -> None:
    cause = TimeoutError("slow")
    err = APITimeoutError(cause=cause)
    assert err.message == "Request timed out."
    assert err.__cause__ is cause


def test_timeout_error_subclassing() -> None:
    err = APITimeoutError()
    assert isinstance(err, APIConnectionError)
    assert isinstance(err, APIError)
    assert isinstance(err, WarmblyError)


# ---------------------------------------------------------------------------
# APIResponseValidationError
# ---------------------------------------------------------------------------


def test_response_validation_error_defaults() -> None:
    err = APIResponseValidationError()
    assert err.message == "Data returned by the API could not be validated."
    assert err.status_code is None
    assert err.body is None
    assert isinstance(err, APIError)


def test_response_validation_error_carries_status_and_body() -> None:
    err = APIResponseValidationError(
        "bad shape",
        status_code=200,
        body={"unexpected": True, "code": "x"},
    )
    assert err.message == "bad shape"
    assert err.status_code == 200
    assert err.body == {"unexpected": True, "code": "x"}
    assert err.code == "x"


# ---------------------------------------------------------------------------
# OAuthError
# ---------------------------------------------------------------------------


def test_oauth_error_with_description() -> None:
    err = OAuthError("invalid_grant", "expired")
    assert err.error == "invalid_grant"
    assert err.error_description == "expired"
    assert str(err) == "expired"


def test_oauth_error_without_description() -> None:
    err = OAuthError("invalid_client")
    assert err.error == "invalid_client"
    assert err.error_description is None
    assert str(err) == "invalid_client"


# ---------------------------------------------------------------------------
# GatewayError + whole-tree catchability
# ---------------------------------------------------------------------------


def test_gateway_error_is_warmbly_error() -> None:
    err = GatewayError("gateway down")
    assert isinstance(err, WarmblyError)
    assert not isinstance(err, APIError)


@pytest.mark.parametrize(
    "exc",
    [
        APIError("x"),
        APIConnectionError(),
        APITimeoutError(),
        APIResponseValidationError(),
        APIStatusError("x", status_code=400),
        BadRequestError("x", status_code=400),
        InternalServerError("x", status_code=500),
        RateLimitError("x"),
        OAuthError("invalid_grant"),
        GatewayError("g"),
    ],
)
def test_entire_tree_catchable_as_warmbly_error(exc: Exception) -> None:
    try:
        raise exc
    except WarmblyError as caught:
        assert caught is exc
    else:  # pragma: no cover - defensive
        pytest.fail("not caught as WarmblyError")
