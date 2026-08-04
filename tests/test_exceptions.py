"""Tests for the exception hierarchy and ``make_status_error``."""

from __future__ import annotations

import pytest

from warmbly import (
    APIError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    NotImplementedAPIError,
    OAuthError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    UnprocessableEntityError,
    WarmblyError,
)
from warmbly._exceptions import make_status_error

# ---------------------------------------------------------------------------
# make_status_error: class selection by status code
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
def test_make_status_error_known_codes(
    status_code: int, expected: type[APIStatusError]
) -> None:
    err = make_status_error(
        status_code=status_code,
        request_id="r",
        headers={},
        body={"message": "boom"},
    )
    assert type(err) is expected
    assert err.status_code == status_code
    assert err.message == "boom"


@pytest.mark.parametrize("status_code", [500, 502, 504, 599])
def test_make_status_error_5xx_is_internal_server_error(status_code: int) -> None:
    err = make_status_error(
        status_code=status_code,
        request_id=None,
        headers=None,
        body=None,
    )
    assert type(err) is InternalServerError
    assert err.status_code == status_code


@pytest.mark.parametrize("status_code", [405, 418, 451, 499])
def test_make_status_error_unknown_4xx_is_generic_status_error(
    status_code: int,
) -> None:
    err = make_status_error(
        status_code=status_code,
        request_id=None,
        headers=None,
        body=None,
    )
    # Unknown non-5xx codes fall back to the base APIStatusError exactly.
    assert type(err) is APIStatusError
    assert err.status_code == status_code


def test_make_status_error_402_is_payment_required() -> None:
    """The API answers 402 when an org runs out of AI credits."""
    err = make_status_error(
        status_code=402,
        request_id=None,
        headers=None,
        body={"message": "You're out of AI credits."},
    )
    assert type(err) is PaymentRequiredError
    assert err.status_code == 402


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(501, NotImplementedAPIError), (503, ServiceUnavailableError)],
)
def test_make_status_error_named_5xx_subclasses(
    status_code: int, expected: type
) -> None:
    err = make_status_error(
        status_code=status_code,
        request_id=None,
        headers=None,
        body=None,
    )
    assert type(err) is expected
    # Both stay catchable as InternalServerError.
    assert isinstance(err, InternalServerError)


# ---------------------------------------------------------------------------
# make_status_error: message/code/body extraction
# ---------------------------------------------------------------------------


def test_make_status_error_message_falls_back_to_error_field() -> None:
    err = make_status_error(
        status_code=400,
        request_id=None,
        headers=None,
        body={"error": "invalid_request"},
    )
    assert err.message == "invalid_request"


def test_make_status_error_generic_message_without_body() -> None:
    err = make_status_error(
        status_code=404,
        request_id=None,
        headers=None,
        body=None,
    )
    assert err.message == "HTTP 404"


def test_make_status_error_extracts_code_from_body() -> None:
    err = make_status_error(
        status_code=400,
        request_id="rq",
        headers={"X-Request-Id": "rq"},
        body={"message": "nope", "code": "bad_param"},
    )
    assert err.code == "bad_param"
    assert err.body == {"message": "nope", "code": "bad_param"}
    assert err.headers == {"X-Request-Id": "rq"}
    assert err.request_id == "rq"


def test_make_status_error_rate_limit_retry_after() -> None:
    err = make_status_error(
        status_code=429,
        request_id=None,
        headers=None,
        body={"message": "slow down"},
        retry_after=12.5,
    )
    assert isinstance(err, RateLimitError)
    assert err.retry_after == 12.5


# ---------------------------------------------------------------------------
# APIStatusError.__str__
# ---------------------------------------------------------------------------


def test_status_error_str_includes_request_id() -> None:
    err = APIStatusError("kaput", status_code=500, request_id="req_abc")
    text = str(err)
    assert "500" in text
    assert "kaput" in text
    assert "req_abc" in text
    assert "request_id" in text


def test_status_error_str_omits_request_id_when_absent() -> None:
    err = APIStatusError("kaput", status_code=503)
    text = str(err)
    assert text == "[503] kaput"
    assert "request_id" not in text


# ---------------------------------------------------------------------------
# Hierarchy / catchability
# ---------------------------------------------------------------------------


def test_hierarchy_roots_at_warmbly_error() -> None:
    assert issubclass(APIError, WarmblyError)
    assert issubclass(APIStatusError, APIError)
    assert issubclass(BadRequestError, APIStatusError)
    assert issubclass(InternalServerError, APIStatusError)
    assert issubclass(OAuthError, WarmblyError)


def test_status_error_is_catchable_as_base() -> None:
    err = make_status_error(status_code=401, request_id=None, headers=None, body=None)
    assert isinstance(err, AuthenticationError)
    assert isinstance(err, APIStatusError)
    assert isinstance(err, APIError)
    assert isinstance(err, WarmblyError)


# ---------------------------------------------------------------------------
# OAuthError
# ---------------------------------------------------------------------------


def test_oauth_error_attributes() -> None:
    err = OAuthError("invalid_grant", "The provided grant is invalid.")
    assert err.error == "invalid_grant"
    assert err.error_description == "The provided grant is invalid."
    # The human-readable description is used for the Exception message.
    assert str(err) == "The provided grant is invalid."


def test_oauth_error_description_optional() -> None:
    err = OAuthError("invalid_client")
    assert err.error == "invalid_client"
    assert err.error_description is None
    # Falls back to the error code when no description is supplied.
    assert str(err) == "invalid_client"


def test_oauth_error_is_warmbly_error_not_api_error() -> None:
    err = OAuthError("invalid_request")
    assert isinstance(err, WarmblyError)
    assert not isinstance(err, APIError)
