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


class ErrorCode:
    """Machine-readable ``code`` values from the API error envelope.

    Compare against :attr:`APIError.code`, for example
    ``err.code == ErrorCode.REAUTH_REQUIRED``. The names are the server's
    codes upper-cased. The server may add codes at any time, so always handle
    an unrecognized ``code`` as a generic failure of its HTTP status.
    """

    ACTION_PROVIDER_MISMATCH = "action_provider_mismatch"
    ADMIN_DEVICE_EXPIRED = "admin_device_expired"
    ADMIN_DEVICE_RESOLVED = "admin_device_resolved"
    ADMIN_DEVICE_SLOW_DOWN = "admin_device_slow_down"
    ADMIN_MFA_REQUIRED = "admin_mfa_required"
    AI_NOT_CONFIGURED = "ai_not_configured"
    API_KEY_HOLDER_LEFT = "api_key_holder_left"
    API_KEY_MAILBOX_LIMITED = "api_key_mailbox_limited"
    API_KEY_PERMISSIONS_EXCEED_CALLER = "api_key_permissions_exceed_caller"
    APPROVAL_NOT_PENDING = "approval_not_pending"
    APP_NOT_LISTABLE = "app_not_listable"
    APP_PASSWORD_INVALID = "app_password_invalid"
    APP_SUSPENDED = "app_suspended"
    BAD_REQUEST = "bad_request"
    CLI_AUTH_SCOPES_ROLE = "cli_auth_scopes_role"
    CLOUD_LINK_MANAGED_PROTOCOL = "cloud_link_managed_protocol"
    CLOUD_LINK_UPGRADE_REQUIRED = "cloud_link_upgrade_required"
    CLOUD_LINK_WORKSPACE_REQUIRED = "cloud_link_workspace_required"
    CONFLICT = "conflict"
    CONTACT_EMAIL_TAKEN = "contact_email_taken"
    CRM_CONTACT_MISSING = "crm_contact_missing"
    CRM_MANAGED_EXTERNALLY = "crm_managed_externally"
    CRM_NOT_CONNECTED = "crm_not_connected"
    CRM_OPTED_OUT = "crm_opted_out"
    CRM_OWNER_UNMAPPED = "crm_owner_unmapped"
    CRM_PROVIDER_REJECTED = "crm_provider_rejected"
    CRM_REAUTH_REQUIRED = "crm_reauth_required"
    CRM_RECORD_MISSING = "crm_record_missing"
    CRM_STAGE_UNKNOWN = "crm_stage_unknown"
    CRM_SYNC_RUNNING = "crm_sync_running"
    CRM_UNAVAILABLE = "crm_unavailable"
    DEVELOPER_ACCESS_BLOCKED = "developer_access_blocked"
    DOMAIN_REDIRECT_CLOUD_UNAVAILABLE = "domain_redirect_cloud_unavailable"
    DOMAIN_REDIRECT_CLOUD_UNREACHABLE = "domain_redirect_cloud_unreachable"
    DOMAIN_REDIRECT_INVALID_TARGET = "domain_redirect_invalid_target"
    DOMAIN_REDIRECT_LIMIT = "domain_redirect_limit"
    DOMAIN_REDIRECT_LINKED = "domain_redirect_linked"
    DOMAIN_REDIRECT_TAKEN = "domain_redirect_taken"
    DUPLICATE_COLUMN = "duplicate_column"
    EMPTY_STEP_BODY = "empty_step_body"
    FORBIDDEN = "forbidden"
    GOOGLE_DELEGATION_UNAUTHORIZED = "google_delegation_unauthorized"
    IMPORT_RUNNING = "import_running"
    INSUFFICIENT_CREDITS = "insufficient_credits"
    INTERNAL_ERROR = "internal_error"
    INVALID_ACCESS_RESOURCE = "invalid_access_resource"
    INVALID_ACCESS_SCOPE = "invalid_access_scope"
    INVALID_ACTION = "invalid_action"
    INVALID_COLUMN = "invalid_column"
    INVALID_CURSOR = "invalid_cursor"
    INVALID_ENGAGEMENT = "invalid_engagement"
    INVALID_FILTER = "invalid_filter"
    INVALID_LAYOUT = "invalid_layout"
    INVALID_LEAD_STATUS = "invalid_lead_status"
    INVALID_LISTING = "invalid_listing"
    INVALID_LOGO = "invalid_logo"
    INVALID_MAIL_HOST = "invalid_mail_host"
    INVALID_MESSAGE_ID = "invalid_message_id"
    INVALID_NAME = "invalid_name"
    INVALID_RECIPIENT = "invalid_recipient"
    INVALID_SALESFORCE_DOMAIN = "invalid_salesforce_domain"
    INVALID_SALESFORCE_SETTINGS = "invalid_salesforce_settings"
    INVALID_SETTING = "invalid_setting"
    INVALID_SLUG = "invalid_slug"
    INVALID_SORT = "invalid_sort"
    INVALID_SORT_BY = "invalid_sort_by"
    INVALID_SYNC_FOLDER = "invalid_sync_folder"
    INVALID_WEBSITE = "invalid_website"
    INVITATION_INVALID = "invitation_invalid"
    LEADS_UNDELIVERABLE = "leads_undeliverable"
    LEAD_CC_CONTACT_NOT_FOUND = "lead_cc_contact_not_found"
    LEAD_CC_HAS_COPIES = "lead_cc_has_copies"
    LEAD_CC_LEAD_IS_COPIED = "lead_cc_lead_is_copied"
    LEAD_CC_LIMIT = "lead_cc_limit"
    LEAD_CC_SELF = "lead_cc_self"
    LEAD_FILTER_REQUIRES_CAMPAIGN = "lead_filter_requires_campaign"
    LISTING_HIDDEN = "listing_hidden"
    LISTING_SLUG_TAKEN = "listing_slug_taken"
    LIST_BOUNCE_RISK = "list_bounce_risk"
    MAILBOX_ALLOWANCE_REACHED = "mailbox_allowance_reached"
    MAILBOX_CLOUD_UNENROLL_FAILED = "mailbox_cloud_unenroll_failed"
    MAILBOX_GMAIL_OAUTH_DISABLED = "mailbox_gmail_oauth_disabled"
    MAILBOX_GRANT_DOMAIN_MISMATCH = "mailbox_grant_domain_mismatch"
    MAILBOX_GRANT_INACTIVE = "mailbox_grant_inactive"
    MAILBOX_GRANT_MAILBOX_UNREACHABLE = "mailbox_grant_mailbox_unreachable"
    MAILBOX_GRANT_NOT_CONFIGURED = "mailbox_grant_not_configured"
    MAILBOX_GRANT_PROOF_MISSING = "mailbox_grant_proof_missing"
    MAILBOX_GRANT_STATE_INVALID = "mailbox_grant_state_invalid"
    MAILBOX_GRANT_UNAVAILABLE = "mailbox_grant_unavailable"
    MAILBOX_IDENTITY_UNAVAILABLE = "mailbox_identity_unavailable"
    MAILBOX_IMPORT_CREDENTIALS_EXPIRED = "mailbox_import_credentials_expired"
    MAILBOX_IMPORT_EMPTY = "mailbox_import_empty"
    MAILBOX_IMPORT_NOTHING_TO_RETRY = "mailbox_import_nothing_to_retry"
    MAILBOX_IMPORT_NO_EMAIL_COLUMN = "mailbox_import_no_email_column"
    MAILBOX_IMPORT_ROW_INCOMPLETE = "mailbox_import_row_incomplete"
    MAILBOX_IMPORT_ROW_NOT_FAILED = "mailbox_import_row_not_failed"
    MAILBOX_IMPORT_TOO_LARGE = "mailbox_import_too_large"
    MAILBOX_IS_SEED = "mailbox_is_seed"
    MAILBOX_NOT_GOOGLE_SIGNIN = "mailbox_not_google_signin"
    MAILBOX_OAUTH_RETURN_ORIGIN = "mailbox_oauth_return_origin"
    MAILBOX_PROVIDER_NOT_CONFIGURED = "mailbox_provider_not_configured"
    MAILBOX_REAUTH_DELEGATED = "mailbox_reauth_delegated"
    MAILBOX_SEND_AS_UNKNOWN = "mailbox_send_as_unknown"
    MAILBOX_SEND_AS_UNSUPPORTED = "mailbox_send_as_unsupported"
    MAILBOX_SIGNATURE_TOO_LARGE = "mailbox_signature_too_large"
    MAILBOX_VALIDATION_TIMEOUT = "mailbox_validation_timeout"
    MAILBOX_VENDOR_DOMAIN_NOT_FOUND = "mailbox_vendor_domain_not_found"
    MAILBOX_VENDOR_DOMAIN_UNSUPPORTED = "mailbox_vendor_domain_unsupported"
    MAILBOX_VENDOR_INVALID_FIELDS = "mailbox_vendor_invalid_fields"
    MAILBOX_VENDOR_NO_WORKSPACE = "mailbox_vendor_no_workspace"
    MAILBOX_VENDOR_RATE_LIMITED = "mailbox_vendor_rate_limited"
    MAILBOX_VENDOR_UNAUTHORIZED = "mailbox_vendor_unauthorized"
    MAILBOX_VENDOR_UNAVAILABLE = "mailbox_vendor_unavailable"
    MAILBOX_VENDOR_UNKNOWN = "mailbox_vendor_unknown"
    MAILBOX_WORKER_UNREACHABLE = "mailbox_worker_unreachable"
    MEMBER_ACCESS_RESTRICTED = "member_access_restricted"
    MICROSOFT_CONSENT_MISSING = "microsoft_consent_missing"
    NOT_FOUND = "not_found"
    NOT_IMPLEMENTED = "not_implemented"
    NO_CONTACTS = "no_contacts"
    NO_LEADS = "no_leads"
    NO_ORGANIZATION = "no_organization"
    NO_REMAINING_LEADS = "no_remaining_leads"
    OAUTH_TOKEN_NOT_ALLOWED = "oauth_token_not_allowed"
    ORGANIZATION_CLOUD_CONNECTED = "organization_cloud_connected"
    OWNER_ACCESS_UNRESTRICTED = "owner_access_unrestricted"
    PASSKEY_USER_VERIFICATION_REQUIRED = "passkey_user_verification_required"
    PASSWORD_BREACHED = "password_breached"
    PASSWORD_CHANGED_SIGN_IN_AGAIN = "password_changed_sign_in_again"
    PLACEMENT_BATCH_EMPTY = "placement_batch_empty"
    PLACEMENT_BATCH_NOT_RUNNING = "placement_batch_not_running"
    PLACEMENT_BATCH_TOO_LARGE = "placement_batch_too_large"
    PLACEMENT_DAILY_BUDGET = "placement_daily_budget"
    PLACEMENT_INVALID_SEEDS = "placement_invalid_seeds"
    PLACEMENT_INVALID_TRACKING = "placement_invalid_tracking"
    PLACEMENT_NOT_ENTITLED = "placement_not_entitled"
    PLACEMENT_NOT_RUNNING = "placement_not_running"
    PLACEMENT_NO_SEEDS = "placement_no_seeds"
    PLACEMENT_PANEL_UNAVAILABLE = "placement_panel_unavailable"
    PLACEMENT_QUOTA_EXCEEDED = "placement_quota_exceeded"
    PLACEMENT_SEED_LIMIT = "placement_seed_limit"
    PLACEMENT_SEED_UNAVAILABLE = "placement_seed_unavailable"
    PLACEMENT_SENDER_BUSY = "placement_sender_busy"
    PLACEMENT_SENDER_UNAVAILABLE = "placement_sender_unavailable"
    PLACEMENT_TOO_MANY_BATCHES = "placement_too_many_batches"
    PLACEMENT_TOO_MANY_RUNNING = "placement_too_many_running"
    POOL_LINK_CLEARTEXT_MAILBOX = "pool_link_cleartext_mailbox"
    POOL_LINK_INSTANCE_URL = "pool_link_instance_url"
    POOL_LINK_OAUTH_BROWSER = "pool_link_oauth_browser"
    POOL_LINK_OAUTH_UNKNOWN = "pool_link_oauth_unknown"
    POOL_LINK_REDIRECT_NOT_FOUND = "pool_link_redirect_not_found"
    POOL_LINK_RETURN_URL = "pool_link_return_url"
    POOL_LINK_WORKSPACE_CONNECTED = "pool_link_workspace_connected"
    POOL_LINK_WORKSPACE_REQUIRED = "pool_link_workspace_required"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    REAUTH_LIMITED = "reauth_limited"
    REAUTH_NO_FACTOR = "reauth_no_factor"
    REAUTH_REQUIRED = "reauth_required"
    REGISTRATION_CLOSED = "registration_closed"
    REGISTRATION_INVITE_ONLY = "registration_invite_only"
    SALESFORCE_ERROR = "salesforce_error"
    SALESFORCE_RATE_LIMITED = "salesforce_rate_limited"
    SALESFORCE_RECONNECT_REQUIRED = "salesforce_reconnect_required"
    SALESFORCE_SYNC_OFF = "salesforce_sync_off"
    SALESFORCE_UNREACHABLE = "salesforce_unreachable"
    SELECTION_TOO_LARGE = "selection_too_large"
    SENDING_DOMAIN_BULK_INVALID = "sending_domain_bulk_invalid"
    SENDING_DOMAIN_NOT_IN_WORKSPACE = "sending_domain_not_in_workspace"
    SENDING_DOMAIN_SHARED_PROVIDER = "sending_domain_shared_provider"
    SERVICE_UNAVAILABLE = "service_unavailable"
    SETUP_ALREADY_COMPLETE = "setup_already_complete"
    SETUP_TOKEN_INVALID = "setup_token_invalid"
    SLACK_LINK_EMAIL_MISMATCH = "slack_link_email_mismatch"
    SLACK_LINK_INVALID = "slack_link_invalid"
    SLACK_NOT_CONFIGURED = "slack_not_configured"
    SLACK_NOT_CONNECTED = "slack_not_connected"
    SLACK_NOT_LINKED = "slack_not_linked"
    SLACK_VERIFY_FAILED = "slack_verify_failed"
    SLACK_VERIFY_UNAVAILABLE = "slack_verify_unavailable"
    SLACK_VERIFY_WRONG_ACCOUNT = "slack_verify_wrong_account"
    SSO_LINK_EXPIRED = "sso_link_expired"
    SSO_WRONG_BROWSER = "sso_wrong_browser"
    STORAGE_LIMIT_REACHED = "storage_limit_reached"
    TOO_MANY_ACCESS_GRANTS = "too_many_access_grants"
    TOO_MANY_COLUMNS = "too_many_columns"
    TOO_MANY_CONTACTS = "too_many_contacts"
    TOO_MANY_TASKS = "too_many_tasks"
    TRACKING_DOMAIN_TAKEN = "tracking_domain_taken"
    TRACKING_HOST_NOT_CONFIGURED = "tracking_host_not_configured"
    TWO_FA_INVALID_CODE = "two_fa_invalid_code"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN_VERIFICATION_PROVIDER = "unknown_verification_provider"
    UNKNOWN_VERIFICATION_STATUS = "unknown_verification_status"
    UNKNOWN_VIEW = "unknown_view"
    UNPROCESSABLE = "unprocessable"
    USAGE_CAP_EXCEEDED = "usage_cap_exceeded"


class WarmblyError(Exception):
    """Base class for every error raised by this SDK."""


class APIError(WarmblyError):
    """Base class for errors originating from an API interaction.

    Attributes:
        message: A human-readable description of the failure.
        body: The parsed response body, when one was returned.
        code: The machine-readable ``code`` from the error envelope, if present.
    """

    message: str
    body: object | None
    code: str | None

    def __init__(self, message: str, *, body: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.body = body
        code = body.get("code") if isinstance(body, dict) else None
        self.code = code

    @property
    def requires_reauth(self) -> bool:
        """Whether the server wants a fresh sign-in before it will do this.

        True for the ``reauth_required`` code, which the server answers with
        HTTP 403 (or 401 when there is no session) for a sensitive account
        change made from a dashboard session that has not recently confirmed
        the account holder at ``POST /auth/reauth``. API keys and OAuth tokens
        are never asked to; this only concerns a session token.

        The related ``reauth_no_factor`` code (the account has nothing to
        confirm with, so sign in again) and ``reauth_limited`` (too many failed
        confirmations this hour) are not covered by this flag; compare
        :attr:`code` against :attr:`ErrorCode.REAUTH_NO_FACTOR` and
        :attr:`ErrorCode.REAUTH_LIMITED` to tell them apart.
        """
        return self.code == ErrorCode.REAUTH_REQUIRED

    @property
    def access_restricted(self) -> bool:
        """Whether the caller's selected-resource access scope refused this.

        True for the ``member_access_restricted`` code (HTTP 403): the member,
        or the API key or OAuth app acting for them, is limited to selected
        campaigns, folders and mailboxes and the route is outside that scope.
        Widening the member's access needs the ``manage_team`` permission; retrying
        will not help.
        """
        return self.code == ErrorCode.MEMBER_ACCESS_RESTRICTED


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
    """HTTP 503: a dependency (AI provider, mail server, ...) is temporarily down."""


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
    if cls is RateLimitError:
        return RateLimitError(
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
