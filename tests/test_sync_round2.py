"""Sync round 2: error codes, scopes and webhook catalog changes."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

import warmbly
from warmbly import (
    APP_GRANTABLE_SCOPES,
    AsyncWarmbly,
    ErrorCode,
    ErrorReason,
    Warmbly,
    mask_to_scopes,
)
from warmbly._exceptions import APIError, make_status_error
from warmbly._utils import ROLE_PERMISSIONS, SCOPES

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture
def client() -> Iterator[Warmbly]:
    c = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
    yield c
    c.close()


@pytest.fixture
async def aclient() -> AsyncIterator[AsyncWarmbly]:
    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as c:
        yield c


# -- error codes -------------------------------------------------------------


def test_error_codes_are_exported_and_named_like_the_wire() -> None:
    assert warmbly.ErrorCode is ErrorCode
    assert ErrorCode.INSUFFICIENT_CREDITS == "insufficient_credits"
    assert ErrorCode.SEND_HOLD_CHANGED == "send_hold_changed"
    assert ErrorCode.API_KEY_PERMISSIONS_EXCEED_CALLER == (
        "api_key_permissions_exceed_caller"
    )
    assert ErrorCode.OAUTH_TOKEN_NOT_ALLOWED == "oauth_token_not_allowed"
    assert ErrorCode.DEVELOPER_ACCESS_BLOCKED == "developer_access_blocked"
    assert ErrorCode.PLACEMENT_QUOTA_EXCEEDED == "placement_quota_exceeded"
    assert ErrorCode.DIAG_RECIPIENT_SUPPRESSED == "RECIPIENT_SUPPRESSED"


def test_every_error_code_constant_is_its_lowercase_value() -> None:
    names = [n for n in vars(ErrorCode) if n.isupper() and not n.startswith("DIAG_")]
    assert len(names) > 250
    for name in names:
        assert getattr(ErrorCode, name) == name.lower()


def test_status_error_exposes_code_and_reason() -> None:
    exc = make_status_error(
        status_code=400,
        body={
            "error": "Bad Request",
            "message": "untrusted",
            "code": "mailbox_tls_failed",
            "reason": ErrorReason.CERTIFICATE_UNTRUSTED,
            "request_id": "r1",
        },
        headers={},
        request_id="r1",
    )
    assert exc.code == ErrorCode.MAILBOX_TLS_FAILED
    assert exc.reason == "certificate_untrusted"


def test_error_reason_defaults_to_none() -> None:
    assert APIError("x", body={"code": "a"}).reason is None
    assert APIError("x", body={"reason": 3}).reason is None
    assert APIError("x", body="plain").reason is None
    assert APIError("x").reason is None


# -- scopes ------------------------------------------------------------------


def test_app_grantable_scopes_exclude_only_api_keys() -> None:
    granted = set(mask_to_scopes(APP_GRANTABLE_SCOPES))
    assert granted == set(SCOPES) - {"api_keys"}
    assert not APP_GRANTABLE_SCOPES & SCOPES["api_keys"]


def test_role_permissions_cover_every_scope() -> None:
    assert set(ROLE_PERMISSIONS) == set(SCOPES)
    assert ROLE_PERMISSIONS["ai_research"] == ("view_contacts", "use_ai")
    assert ROLE_PERMISSIONS["realtime_subscribe"] == ()
    assert ROLE_PERMISSIONS["send_campaigns"] == ("send_campaigns",)


# -- webhook event catalog ---------------------------------------------------

_CATALOG = {
    "event_types": [
        {
            "type": "campaign.email_delivered",
            "category": "campaign",
            "description": "Deprecated, never delivered.",
            "firehose": False,
            "deprecated": True,
        },
        {
            "type": "template.created",
            "category": "campaign",
            "description": "An email template was created.",
            "firehose": False,
            "deprecated": False,
        },
    ],
    "pagination": {"next_cursor": None, "has_more": False, "total": 2},
}


@respx.mock
def test_event_types_parse_deprecated(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/webhooks/event-types").mock(
        return_value=httpx.Response(200, json=_CATALOG)
    )
    items = list(client.webhooks.event_types())
    assert [i.type for i in items] == ["campaign.email_delivered", "template.created"]
    assert items[0].deprecated is True
    assert items[1].deprecated is False
    assert items[1].category == "campaign"


@pytest.mark.anyio
@respx.mock
async def test_event_types_parse_deprecated_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/webhooks/event-types").mock(
        return_value=httpx.Response(200, json=_CATALOG)
    )
    items = [i async for i in aclient.webhooks.event_types()]
    assert items[0].deprecated is True
    assert items[1].type == "template.created"
