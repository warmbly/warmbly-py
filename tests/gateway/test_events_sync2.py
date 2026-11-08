"""Gateway sync round 2: new event names, intent helpers, header credentials.

Covers the event types added since the previous sync, the intent/permission
mapping helpers, API-key and OAuth credentials moving to the
``X-Warmbly-Token`` handshake header, structured handshake refusals
(``{code, reason}`` over HTTP 403) and structured join errors.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from http import HTTPStatus
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import InvalidStatus
from websockets.http11 import Response

from conftest import FakeGateway
from warmbly.gateway import (
    EVENT_PERMISSIONS,
    AsyncGatewayClient,
    FatalDisconnect,
    GatewayClient,
    GatewayEvent,
    GatewayPushError,
    intent_matches,
    normalize_event_type,
)
from warmbly.gateway._connection import TransientDisconnect, _RetryableRefusal

_TIMEOUT = 5.0

# -- event constants ---------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "WARMUP_PLACEMENT",
        "WARMUP_ACTIVITY",
        "PLACEMENT_TEST_UPDATED",
        "MAILBOX_IMPORT_PROGRESS",
        "CONTACT_IMPORT_PROGRESS",
        "CRM_SYNCED",
        "DIRECT_EMAIL_OPENED",
        "DIRECT_EMAIL_CLICKED",
    ],
)
def test_new_event_constants_match_server_names(name: str) -> None:
    assert getattr(GatewayEvent, name) == name


def test_event_permissions_use_server_permission_names() -> None:
    assert EVENT_PERMISSIONS[GatewayEvent.PLACEMENT_TEST_UPDATED] == "view_analytics"
    assert EVENT_PERMISSIONS[GatewayEvent.MAILBOX_IMPORT_PROGRESS] == "manage_emails"
    assert EVENT_PERMISSIONS[GatewayEvent.CONTACT_IMPORT_PROGRESS] == "view_contacts"
    assert EVENT_PERMISSIONS[GatewayEvent.AI_DRAFT_READY] == "access_unibox"


# -- intent helpers ----------------------------------------------------------


def test_normalize_event_type_passes_canonical_through() -> None:
    assert normalize_event_type("EMAIL_SENT") == "EMAIL_SENT"
    assert normalize_event_type("") == ""


def test_normalize_event_type_collapses_separators() -> None:
    assert normalize_event_type("campaign.started") == "CAMPAIGN_STARTED"
    assert normalize_event_type("inbox: email-received") == "INBOX_EMAIL_RECEIVED"


def test_intent_matches_substring_and_default() -> None:
    assert intent_matches("PLACEMENT_TEST_UPDATED", None)
    assert intent_matches("PLACEMENT_TEST_UPDATED", [])
    assert intent_matches("PLACEMENT_TEST_UPDATED", ["placement"])
    assert intent_matches("WARMUP_ACTIVITY", ["CAMPAIGN", "WARMUP"])
    assert not intent_matches("CRM_SYNCED", ["CAMPAIGN"])


def test_intent_matches_never_raises_on_unknown_events() -> None:
    assert intent_matches("BRAND_NEW.event-type", ["brand"])
    assert not intent_matches("BRAND_NEW.event-type", ["other"])


# -- unknown events are delivered, never raise (async + sync) ----------------


@pytest.mark.anyio
async def test_unknown_and_new_events_reach_handlers(
    fake_gateway: FakeGateway,
) -> None:
    client = AsyncGatewayClient(token="t", base_url=fake_gateway.base_url)
    await asyncio.wait_for(client.connect(), _TIMEOUT)
    got: dict[str, asyncio.Future[dict[str, Any]]] = {
        n: asyncio.get_running_loop().create_future()
        for n in (GatewayEvent.PLACEMENT_TEST_UPDATED, "FUTURE_EVENT")
    }

    for name, fut in got.items():

        @client.on_event(name)
        async def _h(topic: str, payload: dict[str, Any], _f: Any = fut) -> None:
            _f.set_result(payload)

    try:
        await asyncio.wait_for(client.subscribe("org:o1"), _TIMEOUT)
        await fake_gateway.broadcast(
            "org:o1",
            "PLACEMENT_TEST_UPDATED",
            {"org_id": "o1", "test_id": "t1", "status": "running"},
        )
        await fake_gateway.broadcast("org:o1", "FUTURE_EVENT", {"x": 1})
        placement = await asyncio.wait_for(
            got[GatewayEvent.PLACEMENT_TEST_UPDATED], _TIMEOUT
        )
        assert placement["test_id"] == "t1"
        assert placement["status"] == "running"
        assert (await asyncio.wait_for(got["FUTURE_EVENT"], _TIMEOUT)) == {"x": 1}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_sync_client_receives_new_event(fake_gateway: FakeGateway) -> None:
    import threading

    gw = GatewayClient(token="t", base_url=fake_gateway.base_url)
    await asyncio.wait_for(asyncio.to_thread(gw.connect), _TIMEOUT)
    seen: dict[str, Any] = {}
    fired = threading.Event()

    @gw.on_event(GatewayEvent.CRM_SYNCED)
    def _h(topic: str, payload: dict[str, Any]) -> None:
        seen.update(payload)
        fired.set()

    try:
        await asyncio.wait_for(asyncio.to_thread(gw.subscribe, "org:o1"), _TIMEOUT)
        await fake_gateway.broadcast(
            "org:o1", "CRM_SYNCED", {"org_id": "o1", "objects": ["deals"]}
        )
        await asyncio.wait_for(asyncio.to_thread(fired.wait, _TIMEOUT), _TIMEOUT)
        assert seen["objects"] == ["deals"]
        assert seen["org_id"] == "o1"
    finally:
        await asyncio.to_thread(gw.close)


# -- credential placement ----------------------------------------------------


def test_api_key_and_oauth_token_go_in_header_not_url() -> None:
    for token in ("wmbly_abc", "wmat_xyz"):
        c = AsyncGatewayClient(token=token, base_url="wss://rt.example.com")
        assert c._build_headers() == {"X-Warmbly-Token": token}
        assert c._build_url() == "wss://rt.example.com/socket/websocket?vsn=2.0.0"
        assert token not in c._build_url()


def test_connection_jwt_goes_in_query() -> None:
    c = AsyncGatewayClient(token="eyJ.a/b", base_url="wss://rt.example.com")
    assert c._build_headers() == {}
    assert c._build_url() == (
        "wss://rt.example.com/socket/websocket?token=eyJ.a%2Fb&vsn=2.0.0"
    )


class _Capture:
    def __init__(self) -> None:
        self.headers: list[Headers] = []
        self.paths: list[str] = []
        self.refusals: list[tuple[int, bytes]] = []
        self.accepted = 0
        self.server: Any = None
        self.port = 0

    @property
    def base_url(self) -> str:
        return f"ws://localhost:{self.port}"

    def process_request(self, connection: ServerConnection, request: Any) -> Any:
        self.headers.append(request.headers)
        self.paths.append(request.path)
        if self.refusals:
            status, body = self.refusals.pop(0)
            return connection.respond(HTTPStatus(status), body.decode())
        self.accepted += 1
        return None


async def _noop(connection: ServerConnection) -> None:
    async for _ in connection:
        pass


@pytest.fixture
async def capture() -> AsyncIterator[_Capture]:
    cap = _Capture()
    cap.server = await serve(_noop, "localhost", 0, process_request=cap.process_request)
    cap.port = next(iter(cap.server.sockets)).getsockname()[1]
    try:
        yield cap
    finally:
        cap.server.close()
        await cap.server.wait_closed()


@pytest.mark.anyio
async def test_async_handshake_sends_header_credential(capture: _Capture) -> None:
    client = AsyncGatewayClient(token="wmbly_secret", base_url=capture.base_url)
    await asyncio.wait_for(client.connect(), _TIMEOUT)
    try:
        assert capture.headers[0]["X-Warmbly-Token"] == "wmbly_secret"
        assert "wmbly_secret" not in capture.paths[0]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_sync_handshake_sends_header_credential(capture: _Capture) -> None:
    gw = GatewayClient(token="wmat_secret", base_url=capture.base_url)
    await asyncio.wait_for(asyncio.to_thread(gw.connect), _TIMEOUT)
    try:
        assert capture.headers[0]["X-Warmbly-Token"] == "wmat_secret"
        assert "wmat_secret" not in capture.paths[0]
    finally:
        await asyncio.to_thread(gw.close)


@pytest.mark.anyio
async def test_jwt_handshake_has_no_header(capture: _Capture) -> None:
    client = AsyncGatewayClient(token="jwt.value", base_url=capture.base_url)
    await asyncio.wait_for(client.connect(), _TIMEOUT)
    try:
        assert "X-Warmbly-Token" not in capture.headers[0]
        assert "token=jwt.value" in capture.paths[0]
    finally:
        await client.close()


# -- structured handshake refusals ------------------------------------------


@pytest.mark.anyio
async def test_refusal_body_becomes_fatal_with_code_and_reason(
    capture: _Capture,
) -> None:
    body = {"code": 4004, "reason": "Token expired"}
    capture.refusals.append((403, json.dumps(body).encode()))
    client = AsyncGatewayClient(token="wmbly_x", base_url=capture.base_url)
    with pytest.raises(FatalDisconnect) as info:
        await asyncio.wait_for(client.connect(), _TIMEOUT)
    assert info.value.code == 4004
    assert "Token expired" in str(info.value)
    assert "HTTP 403" in str(info.value)
    await client.close()


@pytest.mark.anyio
async def test_sync_refusal_raises_fatal(capture: _Capture) -> None:
    capture.refusals.append(
        (403, json.dumps({"code": 4010, "reason": "Permission denied"}).encode())
    )
    gw = GatewayClient(token="wmbly_x", base_url=capture.base_url)
    with pytest.raises(FatalDisconnect) as info:
        await asyncio.wait_for(asyncio.to_thread(gw.connect), _TIMEOUT)
    assert info.value.code == 4010
    await asyncio.to_thread(gw.close)


@pytest.mark.anyio
async def test_rate_limited_refusal_is_retried(capture: _Capture) -> None:
    capture.refusals.append(
        (
            403,
            json.dumps({"code": 4007, "reason": "slow", "retry_after_ms": 10}).encode(),
        )
    )
    client = AsyncGatewayClient(token="wmbly_x", base_url=capture.base_url)
    await asyncio.wait_for(client.connect(), _TIMEOUT)
    try:
        assert capture.accepted == 1
        assert len(capture.headers) == 2
    finally:
        await client.close()


def _status(body: bytes) -> InvalidStatus:
    return InvalidStatus(Response(403, "Forbidden", Headers(), body))


def test_refusal_edge_shapes() -> None:
    refusal = AsyncGatewayClient._refusal
    # Not JSON, not an object, empty.
    for body in (b"", b"<html>", b"[1]", b'"s"'):
        exc = refusal(_status(body))
        assert isinstance(exc, FatalDisconnect)
        assert exc.code is None
        assert str(exc) == "gateway refused the connection (HTTP 403)"
    # Non-int code, non-string reason.
    exc = refusal(_status(b'{"code": "x", "reason": 5}'))
    assert isinstance(exc, FatalDisconnect)
    assert exc.code is None
    assert str(exc) == "gateway refused the connection (HTTP 403)"


def test_refusal_backpressure_variants() -> None:
    refusal = AsyncGatewayClient._refusal
    with_ms = refusal(_status(b'{"code": 4009, "retry_after_ms": 1500}'))
    assert isinstance(with_ms, _RetryableRefusal)
    assert isinstance(with_ms, TransientDisconnect)
    assert with_ms.retry_after == 1.5
    without = refusal(_status(b'{"code": 4007, "retry_after_ms": "soon"}'))
    assert isinstance(without, _RetryableRefusal)
    assert without.retry_after is None
    for bad in ("true", "-5", "0", "NaN", "Infinity"):
        hint = refusal(_status(b'{"code": 4007, "retry_after_ms": %s}' % bad.encode()))
        assert isinstance(hint, _RetryableRefusal)
        assert hint.retry_after is None


# -- structured join errors --------------------------------------------------


def test_push_error_exposes_code_and_reason() -> None:
    err = GatewayPushError(
        "org:o1", "phx_join", {"code": 4010, "reason": "not_a_member"}
    )
    assert err.code == 4010
    assert err.reason == "not_a_member"
    assert "not_a_member" in str(err)


def test_push_error_without_structure() -> None:
    err = GatewayPushError("t", "e", {"error": "boom"})
    assert err.code is None
    assert err.reason is None
    odd = GatewayPushError("t", "e", {"code": "4010", "reason": 7})
    assert odd.code is None
    assert odd.reason is None
