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
    "ErrorReason",
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
    """Machine-readable ``code`` values from the Warmbly error envelope.

    Compare against :attr:`APIError.code`, for example
    ``exc.code == ErrorCode.INSUFFICIENT_CREDITS``. The server may add codes
    at any time, so always keep a fallback for an unknown value.
    """

    ACCOUNT_HAS_SHARED_WORK = "account_has_shared_work"
    ACCOUNT_SENDING_SUSPENDED = "account_sending_suspended"
    ACCOUNT_SUSPENDED = "account_suspended"
    ACCOUNT_WORKSPACE_CREATE_SUSPENDED = "account_workspace_create_suspended"
    ACTION_PROVIDER_MISMATCH = "action_provider_mismatch"
    ADMIN_MFA_REQUIRED = "admin_mfa_required"
    AGENCY_AI_BALANCE_INSUFFICIENT = "agency_ai_balance_insufficient"
    AGENCY_API_KEY_NOT_FOUND = "agency_api_key_not_found"
    AGENCY_CLIENT_HAS_SUBSCRIPTION = "agency_client_has_subscription"
    AGENCY_CLIENT_INBOX_FORBIDDEN = "agency_client_inbox_forbidden"
    AGENCY_CLIENT_MAILBOXES_FORBIDDEN = "agency_client_mailboxes_forbidden"
    AGENCY_CLIENT_NOT_FOUND = "agency_client_not_found"
    AGENCY_CLIENT_NOT_OWNER = "agency_client_not_owner"
    AGENCY_CLIENT_TAKEN = "agency_client_taken"
    AGENCY_CREDENTIAL_REQUIRED = "agency_credential_required"
    AGENCY_FORBIDDEN = "agency_forbidden"
    AGENCY_KEY_HOLDER_LEFT = "agency_key_holder_left"
    AGENCY_KEY_IP_NOT_ALLOWED = "agency_key_ip_not_allowed"
    AGENCY_KEY_NOT_ALLOWED = "agency_key_not_allowed"
    AGENCY_KEY_NOT_CLIENT = "agency_key_not_client"
    AGENCY_KEY_ORGANIZATION_REQUIRED = "agency_key_organization_required"
    AGENCY_LEAVE_AGENCY_OWNER = "agency_leave_agency_owner"
    AGENCY_LEAVE_NOT_OWNER = "agency_leave_not_owner"
    AGENCY_LIMIT_REACHED = "agency_limit_reached"
    AGENCY_NOT_FOUND = "agency_not_found"
    AGENCY_PLAN_UNAVAILABLE = "agency_plan_unavailable"
    AGENCY_POOL_UNLIMITED = "agency_pool_unlimited"
    AGENCY_STAFF_NOT_FOUND = "agency_staff_not_found"
    AI_ALLOWANCE_USED = "ai_allowance_used"
    AI_NOT_CONFIGURED = "ai_not_configured"
    AI_OVERAGE_LIMIT_REACHED = "ai_overage_limit_reached"
    ALREADY_SENT = "already_sent"
    API_CREDENTIALS_REVOKE_UNSUPPORTED = "api_credentials_revoke_unsupported"
    API_KEY_HOLDER_LEFT = "api_key_holder_left"
    API_KEY_MAILBOX_LIMITED = "api_key_mailbox_limited"
    API_KEY_PERMISSIONS_EXCEED_CALLER = "api_key_permissions_exceed_caller"
    APOLLO_ENRICH_TOO_MANY = "apollo_enrich_too_many"
    APOLLO_KEY_FORBIDDEN = "apollo_key_forbidden"
    APOLLO_KEY_MISSING = "apollo_key_missing"
    APOLLO_KEY_REJECTED = "apollo_key_rejected"
    APOLLO_RATE_LIMITED = "apollo_rate_limited"
    APPROVAL_NOT_PENDING = "approval_not_pending"
    APP_ATTEST_FAILED = "app_attest_failed"
    APP_ATTEST_KEY_UNKNOWN = "app_attest_key_unknown"
    APP_ATTEST_UNAVAILABLE = "app_attest_unavailable"
    APP_NOT_LISTABLE = "app_not_listable"
    APP_PASSWORD_INVALID = "app_password_invalid"
    APP_SUSPENDED = "app_suspended"
    ATTEMPT_CHECK_UNAVAILABLE = "attempt_check_unavailable"
    AUTHENTICATION_REQUIRED = "authentication_required"
    BAD_REQUEST = "bad_request"
    CARD_DECLINED = "card_declined"
    CHARGE_IN_PROGRESS = "charge_in_progress"
    CLAY_WEBHOOK_MISSING = "clay_webhook_missing"
    CLAY_WEBHOOK_URL = "clay_webhook_url"
    CLIENT_LINKS_UNAVAILABLE = "client_links_unavailable"
    CLIENT_LINK_EXHAUSTED = "client_link_exhausted"
    CLIENT_LINK_EXPIRED = "client_link_expired"
    CLIENT_LINK_INVALID_EXPIRY = "client_link_invalid_expiry"
    CLIENT_LINK_INVALID_MAX_MAILBOXES = "client_link_invalid_max_mailboxes"
    CLIENT_LINK_INVALID_PROVIDERS = "client_link_invalid_providers"
    CLIENT_LINK_INVALID_TAGS = "client_link_invalid_tags"
    CLIENT_LINK_NOT_FOUND = "client_link_not_found"
    CLIENT_LINK_REVOKED = "client_link_revoked"
    CLI_AUTH_CODE_NOT_FOUND = "cli_auth_code_not_found"
    CLI_AUTH_CODE_USED = "cli_auth_code_used"
    CLI_AUTH_FORBIDDEN = "cli_auth_forbidden"
    CLI_AUTH_REQUEST = "cli_auth_request"
    CLI_AUTH_SCOPES = "cli_auth_scopes"
    CLI_AUTH_SCOPES_ROLE = "cli_auth_scopes_role"
    CLOUD_LINK_BAD_RESPONSE = "cloud_link_bad_response"
    CLOUD_LINK_CODE_EXPIRED = "cloud_link_code_expired"
    CLOUD_LINK_CONNECTED = "cloud_link_connected"
    CLOUD_LINK_DISCONNECTING = "cloud_link_disconnecting"
    CLOUD_LINK_EXECUTOR = "cloud_link_executor"
    CLOUD_LINK_LIFECYCLE = "cloud_link_lifecycle"
    CLOUD_LINK_MAILBOX_INACTIVE = "cloud_link_mailbox_inactive"
    CLOUD_LINK_MANAGED_PROTOCOL = "cloud_link_managed_protocol"
    CLOUD_LINK_NOT_CONNECTED = "cloud_link_not_connected"
    CLOUD_LINK_NO_KEY = "cloud_link_no_key"
    CLOUD_LINK_NO_PENDING = "cloud_link_no_pending"
    CLOUD_LINK_OAUTH_MAILBOX = "cloud_link_oauth_mailbox"
    CLOUD_LINK_SELF_EXECUTION_MANAGED = "cloud_link_self_execution_managed"
    CLOUD_LINK_SELF_EXECUTION_NOT_GRANTED = "cloud_link_self_execution_not_granted"
    CLOUD_LINK_SELF_EXECUTION_UNAVAILABLE = "cloud_link_self_execution_unavailable"
    CLOUD_LINK_SMTP_ASSOCIATION = "cloud_link_smtp_association"
    CLOUD_LINK_SMTP_ASSOCIATION_PROTOCOL = "cloud_link_smtp_association_protocol"
    CLOUD_LINK_UNREACHABLE = "cloud_link_unreachable"
    CLOUD_LINK_UPGRADE_REQUIRED = "cloud_link_upgrade_required"
    CLOUD_LINK_URL = "cloud_link_url"
    CLOUD_LINK_WORKSPACE_REQUIRED = "cloud_link_workspace_required"
    CLOUD_WARMUP_MANAGED = "cloud_warmup_managed"
    CLOUD_WARMUP_NOT_APPLIED = "cloud_warmup_not_applied"
    CLOUD_WARMUP_VALUE_UNSUPPORTED = "cloud_warmup_value_unsupported"
    CONFLICT = "conflict"
    CONNECT_GRANT_APP_REQUIRED = "connect_grant_app_required"
    CONNECT_GRANT_INPUT = "connect_grant_input"
    CONNECT_GRANT_MAILBOX_NOT_ALLOWED = "connect_grant_mailbox_not_allowed"
    CONNECT_GRANT_OFFLINE = "connect_grant_offline"
    CONNECT_GRANT_REDIRECT_URI = "connect_grant_redirect_uri"
    CONNECT_GRANT_REFUSED = "connect_grant_refused"
    CONNECT_GRANT_WRONG_MAILBOX = "connect_grant_wrong_mailbox"
    CONNECT_LINK_BROWSER = "connect_link_browser"
    CONNECT_LINK_CREATOR_LEFT = "connect_link_creator_left"
    CONNECT_LINK_DECLINED = "connect_link_declined"
    CONNECT_LINK_EMAIL = "connect_link_email"
    CONNECT_LINK_EXPIRY = "connect_link_expiry"
    CONNECT_LINK_NOT_FOUND = "connect_link_not_found"
    CONNECT_LINK_PROVIDER = "connect_link_provider"
    CONNECT_LINK_RETURN_URL = "connect_link_return_url"
    CONNECT_LINK_UNAVAILABLE = "connect_link_unavailable"
    CONNECT_LINK_WRONG_MAILBOX = "connect_link_wrong_mailbox"
    CONNECT_WARMUP = "connect_warmup"
    CONNECT_WARMUP_FAILED = "connect_warmup_failed"
    CONNECT_WARMUP_SETTINGS_FAILED = "connect_warmup_settings_failed"
    CONTACT_EMAIL_TAKEN = "contact_email_taken"
    CONTACT_INVALID = "contact_invalid"
    CONTACT_LIMIT_REACHED = "contact_limit_reached"
    COPY_DESTINATIONS_LIMIT = "copy_destinations_limit"
    COPY_DESTINATION_FORBIDDEN = "copy_destination_forbidden"
    COPY_TEMPLATES_LIMIT = "copy_templates_limit"
    CRM_CONTACT_MISSING = "crm_contact_missing"
    CRM_MANAGED_EXTERNALLY = "crm_managed_externally"
    CRM_NOT_CONNECTED = "crm_not_connected"
    CRM_OWNER_UNMAPPED = "crm_owner_unmapped"
    CRM_PROVIDER_REJECTED = "crm_provider_rejected"
    CRM_REAUTH_REQUIRED = "crm_reauth_required"
    CRM_RECORD_MISSING = "crm_record_missing"
    CRM_STAGE_UNKNOWN = "crm_stage_unknown"
    CRM_SYNC_RUNNING = "crm_sync_running"
    CRM_UNAVAILABLE = "crm_unavailable"
    CROSS_WORKSPACE_COPY_REQUIRES_SESSION = "cross_workspace_copy_requires_session"
    DEVELOPER_ACCESS_BLOCKED = "developer_access_blocked"
    DNS_NOT_HOSTED = "dns_not_hosted"
    DNS_RECORD_CONFLICT = "dns_record_conflict"
    DNS_RECORD_INVALID = "dns_record_invalid"
    DNS_RECORD_MANAGED = "dns_record_managed"
    DOMAIN_IN_USE = "domain_in_use"
    DOMAIN_NOT_READY = "domain_not_ready"
    DOMAIN_NOT_RENEWABLE = "domain_not_renewable"
    DOMAIN_PREMIUM = "domain_premium"
    DOMAIN_REDIRECT_CLOUD_UNAVAILABLE = "domain_redirect_cloud_unavailable"
    DOMAIN_REDIRECT_CLOUD_UNREACHABLE = "domain_redirect_cloud_unreachable"
    DOMAIN_REDIRECT_INVALID_TARGET = "domain_redirect_invalid_target"
    DOMAIN_REDIRECT_LIMIT = "domain_redirect_limit"
    DOMAIN_REDIRECT_LINKED = "domain_redirect_linked"
    DOMAIN_REDIRECT_TAKEN = "domain_redirect_taken"
    DOMAIN_REGISTERED_ELSEWHERE = "domain_registered_elsewhere"
    DOMAIN_REGISTERED_HERE = "domain_registered_here"
    DOMAIN_UNAVAILABLE = "domain_unavailable"
    DRAFT_DISCARDED = "draft_discarded"
    DUPLICATE_COLUMN = "duplicate_column"
    DUPLICATE_HEADER = "duplicate_header"
    DUPLICATE_QUERY_PARAMETER = "duplicate_query_parameter"
    EMPTY_STEP_BODY = "empty_step_body"
    FORBIDDEN = "forbidden"
    FORMS_DOMAIN_TAKEN = "forms_domain_taken"
    FORM_SUBMIT_FAILED = "form_submit_failed"
    FORWARDING_URL_INVALID = "forwarding_url_invalid"
    GOOGLE_APP_PASSWORD_REQUIRED = "google_app_password_required"
    GOOGLE_DELEGATION_UNAUTHORIZED = "google_delegation_unauthorized"
    #: The first request with this ``Idempotency-Key`` hit a server error or
    #: never finished, so whether it took effect is unknown. The SDK retries a
    #: write with the same key, so this can be what a retried ``5xx`` turns
    #: into. Retry with a new key only once you know the change did not happen.
    IDEMPOTENCY_OUTCOME_UNKNOWN = "idempotency_outcome_unknown"
    IDENTITY_NOT_FOUND = "identity_not_found"
    IMAGE_DIMENSIONS_TOO_LARGE = "image_dimensions_too_large"
    IMAGE_FORMAT_NOT_ALLOWED = "image_format_not_allowed"
    IMAGE_TOO_LARGE = "image_too_large"
    IMAGE_TOO_SMALL = "image_too_small"
    IMAGE_UNREADABLE = "image_unreadable"
    IMPORT_RUNNING = "import_running"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INSUFFICIENT_CREDITS = "insufficient_credits"
    INTERNAL_ERROR = "internal_error"
    INVALID_ACCESS_RESOURCE = "invalid_access_resource"
    INVALID_ACCESS_SCOPE = "invalid_access_scope"
    INVALID_ACTION = "invalid_action"
    INVALID_AGENCY_KEY_PERMISSIONS = "invalid_agency_key_permissions"
    INVALID_AGENCY_ROLE = "invalid_agency_role"
    INVALID_AI_AMOUNT = "invalid_ai_amount"
    INVALID_COLUMN = "invalid_column"
    INVALID_CURSOR = "invalid_cursor"
    INVALID_DRAFT = "invalid_draft"
    INVALID_EMAIL = "invalid_email"
    INVALID_ENGAGEMENT = "invalid_engagement"
    INVALID_FILTER = "invalid_filter"
    INVALID_FILTER_TAG = "invalid_filter_tag"
    INVALID_LAYOUT = "invalid_layout"
    INVALID_LEAD_STATUS = "invalid_lead_status"
    INVALID_LIMIT = "invalid_limit"
    INVALID_LISTING = "invalid_listing"
    INVALID_LOGO = "invalid_logo"
    INVALID_MAIL_HOST = "invalid_mail_host"
    INVALID_MESSAGE_ID = "invalid_message_id"
    INVALID_MONTHLY_AI_LIMIT = "invalid_monthly_ai_limit"
    INVALID_MONTHLY_SEND_LIMIT = "invalid_monthly_send_limit"
    INVALID_NAME = "invalid_name"
    INVALID_QUERY = "invalid_query"
    INVALID_RECIPIENT = "invalid_recipient"
    INVALID_REPORT_LINK = "invalid_report_link"
    INVALID_REPORT_RANGE = "invalid_report_range"
    INVALID_REPORT_SCHEDULE = "invalid_report_schedule"
    INVALID_REPORT_SCOPE = "invalid_report_scope"
    INVALID_REPORT_SECTIONS = "invalid_report_sections"
    INVALID_SALESFORCE_DOMAIN = "invalid_salesforce_domain"
    INVALID_SALESFORCE_SETTINGS = "invalid_salesforce_settings"
    INVALID_SETTING = "invalid_setting"
    INVALID_SLUG = "invalid_slug"
    INVALID_SORT = "invalid_sort"
    INVALID_SORT_BY = "invalid_sort_by"
    INVALID_SYNC_FOLDER = "invalid_sync_folder"
    INVALID_TEMPLATE = "invalid_template"
    INVALID_TLS_PIN = "invalid_tls_pin"
    INVALID_WEBSITE = "invalid_website"
    INVITATION_EXPIRED = "invitation_expired"
    INVITATION_INVALID = "invitation_invalid"
    INVITATION_ROLES_REMOVED = "invitation_roles_removed"
    INVITATION_USED_OR_EXPIRED = "invitation_used_or_expired"
    LAST_SIGN_IN_METHOD = "last_sign_in_method"
    LEADS_UNDELIVERABLE = "leads_undeliverable"
    LEAD_CC_CONTACT_NOT_FOUND = "lead_cc_contact_not_found"
    LEAD_CC_HAS_COPIES = "lead_cc_has_copies"
    LEAD_CC_LEAD_IS_COPIED = "lead_cc_lead_is_copied"
    LEAD_CC_LIMIT = "lead_cc_limit"
    LEAD_CC_SELF = "lead_cc_self"
    LEAD_FILTER_REQUIRES_CAMPAIGN = "lead_filter_requires_campaign"
    LEAD_PERSON_EXISTS = "lead_person_exists"
    LEAD_PERSON_NO_DOMAIN = "lead_person_no_domain"
    LEAD_PROVIDER_KEY = "lead_provider_key"
    LEAD_PROVIDER_NOT_CONNECTED = "lead_provider_not_connected"
    LEAD_PROVIDER_QUOTA = "lead_provider_quota"
    LEAD_PROVIDER_UNAVAILABLE = "lead_provider_unavailable"
    LEAD_SEARCH_AREA = "lead_search_area"
    LEAD_SEARCH_EMPTY = "lead_search_empty"
    LEAD_SEARCH_EXHAUSTED = "lead_search_exhausted"
    LEAD_SELECTION_TOO_LARGE = "lead_selection_too_large"
    LEAD_STEP_SENT = "lead_step_sent"
    LEAD_SYNC_TARGET_NOT_FOUND = "lead_sync_target_not_found"
    LISTING_HIDDEN = "listing_hidden"
    LISTING_SLUG_TAKEN = "listing_slug_taken"
    LIST_BOUNCE_RISK = "list_bounce_risk"
    LOCAL_PART_INVALID = "local_part_invalid"
    MAILBOX_ALLOWANCE_REACHED = "mailbox_allowance_reached"
    MAILBOX_AUTH_REFUSED = "mailbox_auth_refused"
    MAILBOX_CERTIFICATE_NOT_PINNED = "mailbox_certificate_not_pinned"
    MAILBOX_CLOUD_UNENROLL_FAILED = "mailbox_cloud_unenroll_failed"
    MAILBOX_EXISTS = "mailbox_exists"
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
    MAILBOX_LIMIT = "mailbox_limit"
    MAILBOX_NOT_CANCELLABLE = "mailbox_not_cancellable"
    MAILBOX_NOT_GOOGLE_SIGNIN = "mailbox_not_google_signin"
    MAILBOX_PROVIDER_NOT_CONFIGURED = "mailbox_provider_not_configured"
    MAILBOX_REAUTH_DELEGATED = "mailbox_reauth_delegated"
    MAILBOX_SEND_AS_UNKNOWN = "mailbox_send_as_unknown"
    MAILBOX_SEND_AS_UNSUPPORTED = "mailbox_send_as_unsupported"
    MAILBOX_SERVER_DECLINED = "mailbox_server_declined"
    MAILBOX_SIGNATURE_TOO_LARGE = "mailbox_signature_too_large"
    MAILBOX_TLS_FAILED = "mailbox_tls_failed"
    MAILBOX_UNREACHABLE = "mailbox_unreachable"
    MAILBOX_VALIDATION_TIMEOUT = "mailbox_validation_timeout"
    MAILBOX_VENDOR_DOMAIN_NOT_FOUND = "mailbox_vendor_domain_not_found"
    MAILBOX_VENDOR_DOMAIN_UNSUPPORTED = "mailbox_vendor_domain_unsupported"
    MAILBOX_VENDOR_INVALID_FIELDS = "mailbox_vendor_invalid_fields"
    MAILBOX_VENDOR_NO_WORKSPACE = "mailbox_vendor_no_workspace"
    MAILBOX_VENDOR_RATE_LIMITED = "mailbox_vendor_rate_limited"
    MAILBOX_VENDOR_RECONNECT_NONE = "mailbox_vendor_reconnect_none"
    MAILBOX_VENDOR_RECONNECT_UNAVAILABLE = "mailbox_vendor_reconnect_unavailable"
    MAILBOX_VENDOR_RECONNECT_UNSUPPORTED = "mailbox_vendor_reconnect_unsupported"
    MAILBOX_VENDOR_UNAUTHORIZED = "mailbox_vendor_unauthorized"
    MAILBOX_VENDOR_UNAVAILABLE = "mailbox_vendor_unavailable"
    MAILBOX_VENDOR_UNKNOWN = "mailbox_vendor_unknown"
    MAILBOX_WORKER_UNREACHABLE = "mailbox_worker_unreachable"
    MEMBER_ACCESS_RESTRICTED = "member_access_restricted"
    MICROSOFT_CONSENT_MISSING = "microsoft_consent_missing"
    MONTHLY_LIMIT_TOO_SMALL = "monthly_limit_too_small"
    NOT_FOUND = "not_found"
    NO_CONTACTS = "no_contacts"
    NO_LEADS = "no_leads"
    NO_ORGANIZATION = "no_organization"
    NO_REMAINING_LEADS = "no_remaining_leads"
    OAUTH_APP_CLIENT_ID = "oauth_app_client_id"
    OAUTH_APP_CLIENT_SECRET = "oauth_app_client_secret"
    OAUTH_APP_IN_USE = "oauth_app_in_use"
    OAUTH_APP_NOT_FOUND = "oauth_app_not_found"
    OAUTH_APP_PROVIDER = "oauth_app_provider"
    OAUTH_APP_REDIRECT_URL = "oauth_app_redirect_url"
    OAUTH_APP_REJECTED = "oauth_app_rejected"
    OAUTH_APP_SECRET_MISSING = "oauth_app_secret_missing"
    OAUTH_TOKEN_NOT_ALLOWED = "oauth_token_not_allowed"
    ORGANIZATION_CANCELLED = "organization_cancelled"
    ORGANIZATION_CLOUD_CONNECTED = "organization_cloud_connected"
    ORGANIZATION_SUSPENDED = "organization_suspended"
    OWNER_ACCESS_UNRESTRICTED = "owner_access_unrestricted"
    PARTNERSHIP_OAUTH_APP_REQUIRED = "partnership_oauth_app_required"
    PARTNERSHIP_PLAN_REQUIRED = "partnership_plan_required"
    PARTNER_MANAGED_MAILBOX = "partner_managed_mailbox"
    PASSKEY_USER_VERIFICATION_REQUIRED = "passkey_user_verification_required"
    PASSWORD_BREACHED = "password_breached"
    PASSWORD_CHANGED_SIGN_IN_AGAIN = "password_changed_sign_in_again"
    PASSWORD_CHANGE_EXPIRED = "password_change_expired"
    PASSWORD_CHANGE_REQUIRED = "password_change_required"
    PASSWORD_LOGIN_DISABLED = "password_login_disabled"
    PASSWORD_REUSED = "password_reused"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_METHOD_REQUIRED = "payment_method_required"
    PAYMENT_PROCESSING = "payment_processing"
    PHOTO_INVALID = "photo_invalid"
    PHOTO_LIMIT_REACHED = "photo_limit_reached"
    PHOTO_NOT_FOUND = "photo_not_found"
    PHOTO_STORAGE_UNAVAILABLE = "photo_storage_unavailable"
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
    PLAN_OFFER_REQUIRED = "plan_offer_required"
    PLAN_REQUIRED = "plan_required"
    POOL_LINK_ALREADY_ADOPTED = "pool_link_already_adopted"
    POOL_LINK_ARRIVAL_INVALID = "pool_link_arrival_invalid"
    POOL_LINK_ARRIVAL_NOT_FOUND = "pool_link_arrival_not_found"
    POOL_LINK_ARRIVAL_PENDING = "pool_link_arrival_pending"
    POOL_LINK_CLEARTEXT_MAILBOX = "pool_link_cleartext_mailbox"
    POOL_LINK_CLOSED = "pool_link_closed"
    POOL_LINK_CODE_NOT_FOUND = "pool_link_code_not_found"
    POOL_LINK_CODE_USED = "pool_link_code_used"
    POOL_LINK_COMMAND_ANSWERED = "pool_link_command_answered"
    POOL_LINK_COMMAND_NOT_FOUND = "pool_link_command_not_found"
    POOL_LINK_COMMAND_NOT_LEASED = "pool_link_command_not_leased"
    POOL_LINK_COMMAND_RESULT_INVALID = "pool_link_command_result_invalid"
    POOL_LINK_CREDENTIAL = "pool_link_credential"
    POOL_LINK_DENIED = "pool_link_denied"
    POOL_LINK_EXECUTOR = "pool_link_executor"
    POOL_LINK_EXECUTOR_CONFLICT = "pool_link_executor_conflict"
    POOL_LINK_EXECUTOR_CREDENTIAL = "pool_link_executor_credential"
    POOL_LINK_EXECUTOR_MANAGED = "pool_link_executor_managed"
    POOL_LINK_INSTANCE_NOT_FOUND = "pool_link_instance_not_found"
    POOL_LINK_INSTANCE_URL = "pool_link_instance_url"
    POOL_LINK_MAILBOX_BLOCKED = "pool_link_mailbox_blocked"
    POOL_LINK_MAILBOX_CONFLICT = "pool_link_mailbox_conflict"
    POOL_LINK_MAILBOX_INACTIVE = "pool_link_mailbox_inactive"
    POOL_LINK_MAILBOX_NOT_FOUND = "pool_link_mailbox_not_found"
    POOL_LINK_MAILBOX_NOT_SELF_EXECUTED = "pool_link_mailbox_not_self_executed"
    POOL_LINK_NOT_ADOPTABLE = "pool_link_not_adoptable"
    POOL_LINK_NOT_MANAGED = "pool_link_not_managed"
    POOL_LINK_OAUTH_BROWSER = "pool_link_oauth_browser"
    POOL_LINK_OAUTH_PENDING = "pool_link_oauth_pending"
    POOL_LINK_OAUTH_SESSION = "pool_link_oauth_session"
    POOL_LINK_OAUTH_UNKNOWN = "pool_link_oauth_unknown"
    POOL_LINK_OBSERVATION_INVALID = "pool_link_observation_invalid"
    POOL_LINK_REDIRECT_NOT_FOUND = "pool_link_redirect_not_found"
    POOL_LINK_REQUEST = "pool_link_request"
    POOL_LINK_RETURN_URL = "pool_link_return_url"
    POOL_LINK_REVOKED = "pool_link_revoked"
    POOL_LINK_SELF_EXECUTION_NOT_GRANTED = "pool_link_self_execution_not_granted"
    POOL_LINK_SELF_EXECUTION_UNAVAILABLE = "pool_link_self_execution_unavailable"
    POOL_LINK_SUBSCRIPTION_REQUIRED = "pool_link_subscription_required"
    POOL_LINK_WARMUP_UNAVAILABLE = "pool_link_warmup_unavailable"
    PRICE_CHANGED = "price_changed"
    PROFILE_PHOTO_MISSING = "profile_photo_missing"
    PROVIDER_MIXED = "provider_mixed"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PURCHASED_MAILBOX = "purchased_mailbox"
    QUOTE_NOT_FOUND = "quote_not_found"
    RATE_LIMITED = "rate_limited"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    REAUTH_EXPIRED = "reauth_expired"
    REAUTH_IDENTITY_MISMATCH = "reauth_identity_mismatch"
    REAUTH_LIMITED = "reauth_limited"
    REAUTH_NO_FACTOR = "reauth_no_factor"
    REAUTH_REQUIRED = "reauth_required"
    RECHARGE_TOO_SMALL = "recharge_too_small"
    RECIPIENT_SUPPRESSED = "recipient_suppressed"
    REDIRECT_TARGET_NOT_OWN_DOMAIN = "redirect_target_not_own_domain"
    REGISTRANT_REQUIRED = "registrant_required"
    REGISTRATION_CLOSED = "registration_closed"
    REGISTRATION_INVITE_ONLY = "registration_invite_only"
    RENEWAL_IN_PROGRESS = "renewal_in_progress"
    RENEWAL_NOT_DUE = "renewal_not_due"
    RENEWAL_WINDOW_CLOSED = "renewal_window_closed"
    REPORT_EMAILS_UNAVAILABLE = "report_emails_unavailable"
    REPORT_LIMIT_REACHED = "report_limit_reached"
    REPORT_LINKS_UNAVAILABLE = "report_links_unavailable"
    REPORT_NOT_FOUND = "report_not_found"
    RESET_LINK_INVALID = "reset_link_invalid"
    SALESFORCE_ERROR = "salesforce_error"
    SALESFORCE_RATE_LIMITED = "salesforce_rate_limited"
    SALESFORCE_RECONNECT_REQUIRED = "salesforce_reconnect_required"
    SALESFORCE_SYNC_OFF = "salesforce_sync_off"
    SALESFORCE_UNREACHABLE = "salesforce_unreachable"
    SCHEDULED_SEND_NOT_PENDING = "scheduled_send_not_pending"
    SELECTION_TOO_LARGE = "selection_too_large"
    SENDING_DOMAIN_BULK_INVALID = "sending_domain_bulk_invalid"
    SENDING_DOMAIN_NOT_IN_WORKSPACE = "sending_domain_not_in_workspace"
    SENDING_DOMAIN_SHARED_PROVIDER = "sending_domain_shared_provider"
    SEND_HOLD_CHANGED = "send_hold_changed"
    SEND_HOLD_NOT_FOUND = "send_hold_not_found"
    SEND_HOLD_NOT_RESOLVABLE = "send_hold_not_resolvable"
    SERVICE_UNAVAILABLE = "service_unavailable"
    SESSIONS_NOT_ENDED = "sessions_not_ended"
    SESSION_ENDED = "session_ended"
    SETUP_ALREADY_COMPLETE = "setup_already_complete"
    SIGN_IN_UNAVAILABLE = "sign_in_unavailable"
    SLACK_LINK_EMAIL_MISMATCH = "slack_link_email_mismatch"
    SLACK_LINK_INVALID = "slack_link_invalid"
    SLACK_NOT_CONFIGURED = "slack_not_configured"
    SLACK_NOT_CONNECTED = "slack_not_connected"
    SLACK_NOT_LINKED = "slack_not_linked"
    SLACK_VERIFY_FAILED = "slack_verify_failed"
    SLACK_VERIFY_UNAVAILABLE = "slack_verify_unavailable"
    SLACK_VERIFY_WRONG_ACCOUNT = "slack_verify_wrong_account"
    SSO_LINK_EXPIRED = "sso_link_expired"
    STALE_PAGE = "stale_page"
    STORAGE_LIMIT_REACHED = "storage_limit_reached"
    STORE_DISABLED = "store_disabled"
    STORE_ITEMS_INVALID = "store_items_invalid"
    STORE_MANAGED_BY_PARTNER = "store_managed_by_partner"
    STORE_PURCHASES_ACTIVE = "store_purchases_active"
    STORE_STATE_CONFLICT = "store_state_conflict"
    STORE_UNAVAILABLE = "store_unavailable"
    THREAD_NOT_FOUND = "thread_not_found"
    TLD_UNSUPPORTED = "tld_unsupported"
    TOOL_MIGRATION_IN_FLIGHT_UNSUPPORTED = "tool_migration_in_flight_unsupported"
    TOOL_MIGRATION_KEY_REJECTED = "tool_migration_key_rejected"
    TOOL_MIGRATION_LIMIT = "tool_migration_limit"
    TOOL_MIGRATION_NOT_FOUND = "tool_migration_not_found"
    TOOL_MIGRATION_NOT_READY = "tool_migration_not_ready"
    TOOL_MIGRATION_PERMISSION = "tool_migration_permission"
    TOOL_MIGRATION_PROVIDER_UNAVAILABLE = "tool_migration_provider_unavailable"
    TOOL_MIGRATION_PROVIDER_UNKNOWN = "tool_migration_provider_unknown"
    TOOL_MIGRATION_RUNNING = "tool_migration_running"
    TOOL_MIGRATION_TARGET_INVALID = "tool_migration_target_invalid"
    TOO_MANY_ACCESS_GRANTS = "too_many_access_grants"
    TOO_MANY_COLUMNS = "too_many_columns"
    TOO_MANY_CONTACTS = "too_many_contacts"
    TOO_MANY_TASKS = "too_many_tasks"
    TRACKING_DOMAIN_TAKEN = "tracking_domain_taken"
    TRACKING_HOST_NOT_CONFIGURED = "tracking_host_not_configured"
    TRANSFER_LOCKED = "transfer_locked"
    TWO_FA_CODE_USED = "two_fa_code_used"
    TWO_FA_INVALID_CODE = "two_fa_invalid_code"
    UNAUTHORIZED = "unauthorized"
    UNAVAILABLE = "unavailable"
    UNKNOWN_VERIFICATION_PROVIDER = "unknown_verification_provider"
    UNKNOWN_VERIFICATION_STATUS = "unknown_verification_status"
    UNKNOWN_VIEW = "unknown_view"
    UNPROCESSABLE = "unprocessable"
    USAGE_CAP_EXCEEDED = "usage_cap_exceeded"
    WARMUP_PLAN_RETIRED = "warmup_plan_retired"
    WORKSPACE_SENDING_SUSPENDED = "workspace_sending_suspended"
    WORKSPACE_SUBSCRIPTION_ACTIVE = "workspace_subscription_active"

    #: Send-admission diagnostics. These appear in campaign activity and
    #: task failure metadata, never as an HTTP ``code``.
    DIAG_CAMPAIGN_DAILY_LIMIT_REACHED = "CAMPAIGN_DAILY_LIMIT_REACHED"
    DIAG_MAILBOX_SENDING_PLAN_DENIED = "MAILBOX_SENDING_PLAN_DENIED"
    DIAG_MANUAL_SEND_LIMIT_REACHED = "MANUAL_SEND_LIMIT_REACHED"
    DIAG_RECIPIENT_SUPPRESSED = "RECIPIENT_SUPPRESSED"
    DIAG_SEND_ADMISSION_DENIED = "SEND_ADMISSION_DENIED"


class ErrorReason:
    """Finer ``reason`` keys some error codes carry alongside ``code``.

    Treat an unknown or missing reason as the plain code.
    """

    CERTIFICATE_UNTRUSTED = "certificate_untrusted"


class WarmblyError(Exception):
    """Base class for every error raised by this SDK."""


class APIError(WarmblyError):
    """Base class for errors originating from an API interaction.

    Attributes:
        message: A human-readable description of the failure.
        body: The parsed response body, when one was returned.
        code: The machine-readable ``code`` from the error envelope, if present.
        reason: The optional finer ``reason`` key some codes carry, if present.
            See :class:`ErrorReason`; treat an unknown value as the plain code.
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
