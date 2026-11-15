"""The ``organization`` client option an agency API key names its client workspace with."""

from __future__ import annotations

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, ConflictError, ErrorCode, Warmbly
from warmbly.gateway import EVENT_PERMISSIONS, GatewayEvent

BASE_URL = "https://api.warmbly.com/v1"
ORG = "8b0c3f8e-1f1e-4c39-9a51-0d6f5a1f2b10"


@respx.mock
def test_sync_client_sends_the_organization_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WARMBLY_ORGANIZATION", raising=False)
    route = respx.get(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    with Warmbly(
        api_key="wmagency_test", organization=ORG, base_url=BASE_URL, max_retries=0
    ) as client:
        assert client.organization == ORG
        list(client.suppressions.list())
        request = route.calls.last.request
        assert request.headers["Warmbly-Organization"] == ORG
        assert request.headers["Authorization"] == "Bearer wmagency_test"

        other = "f2b7e0d4-0000-4000-8000-000000000001"
        list(
            client.suppressions.list(
                options={"headers": {"Warmbly-Organization": other}}
            )
        )
        assert route.calls.last.request.headers["Warmbly-Organization"] == other


@respx.mock
def test_workspace_key_sends_no_organization_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WARMBLY_ORGANIZATION", raising=False)
    route = respx.get(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    with Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0) as client:
        assert client.organization is None
        list(client.suppressions.list())
    assert "Warmbly-Organization" not in route.calls.last.request.headers


@pytest.mark.anyio
@respx.mock
async def test_async_client_reads_the_organization_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WARMBLY_ORGANIZATION", ORG)
    route = respx.get(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    async with AsyncWarmbly(
        api_key="wmagency_test", base_url=BASE_URL, max_retries=0
    ) as client:
        assert client.organization == ORG
        async for _ in client.suppressions.list():
            pass
    assert route.calls.last.request.headers["Warmbly-Organization"] == ORG


def test_new_error_codes_use_server_names() -> None:
    assert (
        ErrorCode.AGENCY_KEY_ORGANIZATION_REQUIRED == "agency_key_organization_required"
    )
    assert ErrorCode.AGENCY_CREDENTIAL_REQUIRED == "agency_credential_required"
    assert ErrorCode.IDEMPOTENCY_OUTCOME_UNKNOWN == "idempotency_outcome_unknown"
    assert ErrorCode.CONTACT_LIMIT_REACHED == "contact_limit_reached"
    assert ErrorCode.PARTNERSHIP_PLAN_REQUIRED == "partnership_plan_required"
    assert ErrorCode.TOOL_MIGRATION_RUNNING == "tool_migration_running"
    assert ErrorCode.REPORT_NOT_FOUND == "report_not_found"
    assert ErrorCode.CLIENT_LINK_REVOKED == "client_link_revoked"
    assert ErrorCode.COPY_DESTINATION_FORBIDDEN == "copy_destination_forbidden"


def test_email_bounced_is_a_campaign_event() -> None:
    assert GatewayEvent.EMAIL_BOUNCED == "EMAIL_BOUNCED"
    assert EVENT_PERMISSIONS[GatewayEvent.EMAIL_BOUNCED] == "view_campaigns"


@respx.mock
def test_outcome_unknown_conflict_is_not_retried() -> None:
    route = respx.post(f"{BASE_URL}/suppressions").mock(
        side_effect=[
            httpx.Response(500, json={"code": "internal_error"}),
            httpx.Response(
                409,
                json={"code": "idempotency_outcome_unknown", "message": "unknown"},
            ),
            httpx.Response(200, json={"added": 1}),
        ]
    )
    with Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=3) as client:
        client._retry_delay = lambda attempt, headers: 0.0  # type: ignore[method-assign]
        with pytest.raises(ConflictError) as info:
            client.suppressions.add(entries=["a@example.com"])
    assert info.value.code == ErrorCode.IDEMPOTENCY_OUTCOME_UNKNOWN
    assert route.call_count == 2
    keys = {call.request.headers["Idempotency-Key"] for call in route.calls}
    assert len(keys) == 1


@pytest.mark.anyio
@respx.mock
async def test_async_outcome_unknown_conflict_is_not_retried_but_others_are() -> None:
    route = respx.post(f"{BASE_URL}/suppressions").mock(
        side_effect=[
            httpx.Response(409, json={"code": "conflict"}),
            httpx.Response(409, json={"code": "idempotency_outcome_unknown"}),
        ]
    )
    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=3
    ) as client:
        client._retry_delay = lambda attempt, headers: 0.0  # type: ignore[method-assign]
        with pytest.raises(ConflictError):
            await client.suppressions.add(entries=["a@example.com"])
    assert route.call_count == 2


@respx.mock
def test_cursor_replaces_also_drops_the_option_query() -> None:
    route = respx.get(f"{BASE_URL}/forms/frm_1/submissions").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": "s1"}],
                    "pagination": {"next_cursor": "c2", "has_more": True},
                },
            ),
            httpx.Response(200, json={"data": [{"id": "s2"}], "pagination": {}}),
        ]
    )
    with Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0) as client:
        pages = client.forms.list_submissions(
            "frm_1", options={"query": {"before": "2026-11-01T00:00:00Z", "x": "1"}}
        )
        assert [s.id for s in pages] == ["s1", "s2"]
    first, second = (call.request.url.params for call in route.calls)
    assert first.get("before") == "2026-11-01T00:00:00Z"
    assert "before" not in second
    assert second.get("cursor") == "c2"
    assert second.get("x") == "1"


@pytest.mark.anyio
@respx.mock
async def test_async_cursor_replaces_also_drops_the_option_query() -> None:
    route = respx.get(f"{BASE_URL}/forms/frm_1/submissions").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": "s1"}],
                    "pagination": {"next_cursor": "c2", "has_more": True},
                },
            ),
            httpx.Response(200, json={"data": [{"id": "s2"}], "pagination": {}}),
        ]
    )
    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as client:
        pages = client.forms.list_submissions(
            "frm_1", options={"query": {"before": "2026-11-01T00:00:00Z"}}
        )
        assert [s.id async for s in pages] == ["s1", "s2"]
    assert "before" not in route.calls[1].request.url.params
