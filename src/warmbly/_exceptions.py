"""Exception hierarchy for the Warmbly SDK.

The tree is single-rooted at :class:`WarmblyError` so callers can catch every
SDK-raised error with one ``except``. HTTP failures map the backend error
envelope ``{error, message, code, request_id}`` onto per-status subclasses.

No ``httpx`` type is ever stored on or raised from these exceptions: the
transport layer extracts plain values (status code, headers, parsed body)
before constructing them, which keeps the underlying HTTP client swappable.
"""

from __future__ import annotations

from collections.abc import Mapping

__all__ = [
    "APIConnectionError",
    "APIError",
    "APIResponseValidationError",
    "APIStatusError",
    "APITimeoutError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "ErrorCode",
    "GatewayError",
    "InternalServerError",
    "NotFoundError",
    "NotImplementedAPIError",
    "OAuthError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServiceUnavailableError",
    "UnprocessableEntityError",
    "WarmblyError",
    "make_status_error",
]


class WarmblyError(Exception):
    """Base class for every error raised by this SDK."""


class APIError(WarmblyError):
    """Base class for errors originating from an API interaction.

    Attributes:
        message: A human-readable description of the failure.
        body: The parsed response body, when one was returned.
        code: The machine-readable ``code`` from the error envelope, if present.
            See :class:`ErrorCode` for named constants.
        reason: The optional finer ``reason`` key some codes carry when one code
            has more than one next step. Treat an unknown or missing value as
            the plain code.
    """

    message: str
    body: object | None
    code: str | None
    reason: str | None

    def __init__(self, message: str, *, body: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.body = body
        self.code = body.get("code") if isinstance(body, dict) else None
        reason = body.get("reason") if isinstance(body, dict) else None
        self.reason = reason if isinstance(reason, str) else None


class APIConnectionError(APIError):
    """Raised when the request could not reach the server."""

    def __init__(
        self,
        *,
        message: str = "Connection error.",
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause


class APITimeoutError(APIConnectionError):
    """Raised when a request exceeds the configured timeout."""

    def __init__(self, *, cause: BaseException | None = None) -> None:
        super().__init__(message="Request timed out.", cause=cause)


class APIResponseValidationError(APIError):
    """Raised when a successful response could not be parsed into a model."""

    status_code: int | None

    def __init__(
        self,
        message: str = "Data returned by the API could not be validated.",
        *,
        status_code: int | None = None,
        body: object | None = None,
    ) -> None:
        super().__init__(message, body=body)
        self.status_code = status_code


class APIStatusError(APIError):
    """Raised when the API returns a non-success HTTP status code.

    Attributes:
        status_code: The HTTP status code of the response.
        request_id: The ``X-Request-Id`` header value, for support tickets.
        headers: The response headers as a plain mapping.
    """

    status_code: int
    request_id: str | None
    headers: Mapping[str, str]

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request_id: str | None = None,
        headers: Mapping[str, str] | None = None,
        body: object | None = None,
    ) -> None:
        super().__init__(message, body=body)
        self.status_code = status_code
        self.request_id = request_id
        self.headers = headers or {}

    def __str__(self) -> str:
        rid = f" (request_id: {self.request_id})" if self.request_id else ""
        return f"[{self.status_code}] {self.message}{rid}"


class BadRequestError(APIStatusError):
    """HTTP 400."""


class AuthenticationError(APIStatusError):
    """HTTP 401: missing or invalid credentials."""


class PaymentRequiredError(APIStatusError):
    """HTTP 402: the account is out of AI credits or needs a plan upgrade."""


class PermissionDeniedError(APIStatusError):
    """HTTP 403: authenticated but not allowed (named to avoid shadowing the builtin)."""


class NotFoundError(APIStatusError):
    """HTTP 404."""


class ConflictError(APIStatusError):
    """HTTP 409."""


class UnprocessableEntityError(APIStatusError):
    """HTTP 422: semantically invalid request."""


class RateLimitError(APIStatusError):
    """HTTP 429: too many requests.

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` header or the ``retry_after`` body field, if present.
    """

    retry_after: float | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        request_id: str | None = None,
        headers: Mapping[str, str] | None = None,
        body: object | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            request_id=request_id,
            headers=headers,
            body=body,
        )
        self.retry_after = retry_after


class InternalServerError(APIStatusError):
    """HTTP 5xx: server-side failure."""


class NotImplementedAPIError(InternalServerError):
    """HTTP 501: the endpoint is not enabled on this deployment."""


class ServiceUnavailableError(InternalServerError):
    """HTTP 503: a dependency (AI provider, mail server, ...) is temporarily down.

    The request changed nothing and is safe to try again. The client retries it
    automatically, honoring ``Retry-After``.

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` header or the ``retry_after`` body field, if present.
    """

    retry_after: float | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 503,
        request_id: str | None = None,
        headers: Mapping[str, str] | None = None,
        body: object | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            request_id=request_id,
            headers=headers,
            body=body,
        )
        self.retry_after = retry_after


class ErrorCode:
    """Named constants for the ``code`` an API error carries.

    ``code`` is the machine-readable field of the error envelope; branch on it
    (and the HTTP status) rather than on ``message``. Compare with
    ``exc.code == ErrorCode.REAUTH_REQUIRED``. The list names the codes a
    client is most likely to handle; the server may send others, which still
    arrive as plain strings.
    """

    # Request shape.
    BAD_REQUEST = "bad_request"
    DUPLICATE_QUERY_PARAMETER = "duplicate_query_parameter"
    DUPLICATE_HEADER = "duplicate_header"
    INVALID_CURSOR = "invalid_cursor"
    INVALID_RECIPIENT = "invalid_recipient"
    INVALID_MESSAGE_ID = "invalid_message_id"
    SELECTION_TOO_LARGE = "selection_too_large"
    TOO_MANY_CONTACTS = "too_many_contacts"
    TOO_MANY_TASKS = "too_many_tasks"
    EMPTY_STEP_BODY = "empty_step_body"

    # Authentication and access.
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    SESSION_ENDED = "session_ended"
    REAUTH_REQUIRED = "reauth_required"
    API_KEY_PERMISSIONS_EXCEED_CALLER = "api_key_permissions_exceed_caller"
    API_KEY_HOLDER_LEFT = "api_key_holder_left"
    API_KEY_MAILBOX_LIMITED = "api_key_mailbox_limited"
    OAUTH_TOKEN_NOT_ALLOWED = "oauth_token_not_allowed"
    MEMBER_ACCESS_RESTRICTED = "member_access_restricted"
    ACCOUNT_SUSPENDED = "account_suspended"
    ACCOUNT_SENDING_SUSPENDED = "account_sending_suspended"
    WORKSPACE_SENDING_SUSPENDED = "workspace_sending_suspended"

    # Lookup and conflicts.
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    CONTACT_EMAIL_TAKEN = "contact_email_taken"
    TRACKING_DOMAIN_TAKEN = "tracking_domain_taken"
    RECIPIENT_SUPPRESSED = "recipient_suppressed"

    # Limits and billing.
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    USAGE_CAP_EXCEEDED = "usage_cap_exceeded"
    INSUFFICIENT_CREDITS = "insufficient_credits"
    STORAGE_LIMIT_REACHED = "storage_limit_reached"
    MAILBOX_ALLOWANCE_REACHED = "mailbox_allowance_reached"
    PLACEMENT_QUOTA_EXCEEDED = "placement_quota_exceeded"
    PLACEMENT_NOT_ENTITLED = "placement_not_entitled"
    PLACEMENT_TOO_MANY_RUNNING = "placement_too_many_running"
    PLACEMENT_TOO_MANY_BATCHES = "placement_too_many_batches"

    # Server side. These answer 5xx and are safe to retry.
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    #: A 503 that is not transient: the deployment has no AI provider. The
    #: client does not retry it.
    AI_NOT_CONFIGURED = "ai_not_configured"
    ATTEMPT_CHECK_UNAVAILABLE = "attempt_check_unavailable"
    MAILBOX_WORKER_UNREACHABLE = "mailbox_worker_unreachable"
    MAILBOX_IDENTITY_UNAVAILABLE = "mailbox_identity_unavailable"


class OAuthError(WarmblyError):
    """An OAuth2 token-endpoint error (RFC 6749 ``{error, error_description}``).

    Attributes:
        error: The OAuth error code, e.g. ``invalid_grant``, ``invalid_client``.
        error_description: A human-readable explanation, when provided.
    """

    error: str
    error_description: str | None

    def __init__(self, error: str, error_description: str | None = None) -> None:
        super().__init__(error_description or error)
        self.error = error
        self.error_description = error_description


class GatewayError(WarmblyError):
    """Base class for realtime gateway errors (see :mod:`warmbly.gateway`)."""


_STATUS_MAP: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    501: NotImplementedAPIError,
    503: ServiceUnavailableError,
}


def make_status_error(
    *,
    status_code: int,
    request_id: str | None,
    headers: Mapping[str, str] | None,
    body: object | None,
    retry_after: float | None = None,
) -> APIStatusError:
    """Build the most specific :class:`APIStatusError` for *status_code*.

    Extracts ``message``/``code`` from the standard error envelope when *body*
    is a dict, falling back to a generic message otherwise.
    """
    message = _extract_message(body) or f"HTTP {status_code}"
    cls = _STATUS_MAP.get(status_code)
    if cls is None:
        cls = InternalServerError if status_code >= 500 else APIStatusError
    if cls is RateLimitError or cls is ServiceUnavailableError:
        return cls(
            message,
            status_code=status_code,
            request_id=request_id,
            headers=headers,
            body=body,
            retry_after=retry_after,
        )
    return cls(
        message,
        status_code=status_code,
        request_id=request_id,
        headers=headers,
        body=body,
    )


def _extract_message(body: object | None) -> str | None:
    if isinstance(body, dict):
        value = body.get("message") or body.get("error")
        if isinstance(value, str):
            return value
    return None
