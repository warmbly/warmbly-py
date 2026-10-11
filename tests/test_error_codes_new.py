"""ErrorCode constants and helpers added after the 2032b04 server sync."""

from __future__ import annotations

import pytest

from warmbly import ErrorCode
from warmbly._exceptions import APIError, make_status_error

_NEW_CODES = [
    "action_provider_mismatch",
    "admin_device_expired",
    "admin_device_resolved",
    "admin_device_slow_down",
    "api_key_holder_left",
    "api_key_mailbox_limited",
    "api_key_permissions_exceed_caller",
    "app_not_listable",
    "app_suspended",
    "approval_not_pending",
    "cli_auth_scopes_role",
    "cloud_link_managed_protocol",
    "cloud_link_upgrade_required",
    "cloud_link_workspace_required",
    "crm_contact_missing",
    "crm_managed_externally",
    "crm_not_connected",
    "crm_opted_out",
    "crm_owner_unmapped",
    "crm_provider_rejected",
    "crm_reauth_required",
    "crm_record_missing",
    "crm_stage_unknown",
    "crm_sync_running",
    "crm_unavailable",
    "developer_access_blocked",
    "import_running",
    "invalid_access_resource",
    "invalid_access_scope",
    "invalid_listing",
    "invalid_logo",
    "invalid_message_id",
    "invalid_recipient",
    "invalid_salesforce_domain",
    "invalid_salesforce_settings",
    "invalid_website",
    "listing_hidden",
    "listing_slug_taken",
    "mailbox_oauth_return_origin",
    "member_access_restricted",
    "oauth_token_not_allowed",
    "organization_cloud_connected",
    "owner_access_unrestricted",
    "pool_link_instance_url",
    "pool_link_oauth_browser",
    "pool_link_oauth_unknown",
    "pool_link_return_url",
    "pool_link_workspace_connected",
    "pool_link_workspace_required",
    "reauth_limited",
    "salesforce_error",
    "salesforce_rate_limited",
    "salesforce_reconnect_required",
    "salesforce_sync_off",
    "salesforce_unreachable",
    "slack_link_email_mismatch",
    "slack_verify_failed",
    "slack_verify_unavailable",
    "slack_verify_wrong_account",
    "too_many_access_grants",
    "tracking_domain_taken",
]


@pytest.mark.parametrize("code", _NEW_CODES)
def test_new_error_code_constant_matches_server_code(code: str) -> None:
    assert getattr(ErrorCode, code.upper()) == code


def test_error_codes_are_unique() -> None:
    values = [v for k, v in vars(ErrorCode).items() if k.isupper()]
    assert len(values) == len(set(values))


def test_access_restricted_true_for_scope_refusal() -> None:
    err = make_status_error(
        status_code=403,
        request_id="r1",
        headers=None,
        body={
            "error": "Forbidden",
            "message": "outside your access",
            "code": "member_access_restricted",
        },
    )
    assert isinstance(err, APIError)
    assert err.access_restricted is True
    assert err.code == ErrorCode.MEMBER_ACCESS_RESTRICTED
    assert err.requires_reauth is False


@pytest.mark.parametrize("body", [None, {"code": "forbidden"}, {"code": "new_code"}])
def test_access_restricted_false_otherwise(body: object) -> None:
    assert APIError("x", body=body).access_restricted is False


def test_reauth_siblings_do_not_set_requires_reauth() -> None:
    for code in (ErrorCode.REAUTH_LIMITED, ErrorCode.REAUTH_NO_FACTOR):
        assert APIError("x", body={"code": code}).requires_reauth is False
