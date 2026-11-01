"""Gateway behaviour added by the server sync: handshake credentials, refused
handshakes, and the newer event families with realistic payloads."""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

import pytest
from websockets.datastructures import Headers
from websockets.exceptions import InvalidStatus
from websockets.http11 import Response

from conftest import FakeGateway
from warmbly.gateway import AsyncGatewayClient, FatalDisconnect, GatewayEvent
from warmbly.gateway import _connection as conn
from warmbly.gateway._connection import TransientDisconnect
from warmbly.gateway._sync import GatewayClient

_TIMEOUT = 5.0

# Payloads follow the Go event structs in internal/infrastructure/pubsub/events.go.
ORG = "7f3c2d0e-1b2a-4c3d-8e9f-0a1b2c3d4e5f"
NEW_EVENTS: dict[str, dict[str, Any]] = {
    GatewayEvent.WARMUP_PLACEMENT: {
        "event_type": "WARMUP_PLACEMENT",
        "org_id": ORG,
        "email_account_id": "a1",
        "email": "me@example.com",
        "status": "rescue_moved",
    },
    GatewayEvent.PLACEMENT_TEST_UPDATED: {
        "event_type": "PLACEMENT_TEST_UPDATED",
        "org_id": ORG,
        "test_id": "t1",
        "campaign_id": "c1",
        "status": "running",
    },
    GatewayEvent.MAILBOX_IMPORT_PROGRESS: {
        "event_type": "MAILBOX_IMPORT_PROGRESS",
        "org_id": ORG,
        "import_id": "i1",
        "status": "running",
    },
    GatewayEvent.CONTACT_IMPORT_PROGRESS: {
        "event_type": "CONTACT_IMPORT_PROGRESS",
        "org_id": ORG,
        "import_id": "i2",
        "status": "queued",
    },
    GatewayEvent.CRM_SYNCED: {
        "event_type": "CRM_SYNCED",
        "org_id": ORG,
        "objects": ["deals", "tasks"],
        "contact_id": "ct1",
    },
    GatewayEvent.DIRECT_EMAIL_OPENED: {
        "event_type": "DIRECT_EMAIL_OPENED",
        "org_id": ORG,
        "email_account_id": "a1",
        "contact_email": "lead@example.com",
        "machine": False,
        "client": "Gmail",
        "client_type": "webmail",
        "device_hidden": True,
        "device_type": "desktop",
        "os": "macOS",
        "browser": "Chrome",
        "country_code": "US",
        "city": "Austin",
    },
    GatewayEvent.DIRECT_EMAIL_CLICKED: {
        "event_type": "DIRECT_EMAIL_CLICKED",
        "org_id": ORG,
        "original_url": "https://example.com/p",
        "link_label": "Pricing",
    },
}


def test_event_constants_match_server_names() -> None:
    for name in NEW_EVENTS:
        assert getattr(GatewayEvent, name) == name


def _deliver(client: AsyncGatewayClient, event: str, payload: dict[str, Any]) -> None:
    client._handle_raw(json.dumps([None, None, f"org:{ORG}", event, payload]))


@pytest.mark.anyio
async def test_new_events_dispatch_with_all_fields(anyio_backend: str) -> None:
    client = AsyncGatewayClient(token="wmbly_x")
    seen: dict[str, dict[str, Any]] = {}

    async def handler(topic: str, payload: dict[str, Any]) -> None:
        seen[payload["event_type"]] = payload

    for name in NEW_EVENTS:
        client.on_event(name)(handler)
    for name, payload in NEW_EVENTS.items():
        _deliver(client, name, payload)
    await asyncio.sleep(0.05)
    assert seen == NEW_EVENTS
    assert seen["DIRECT_EMAIL_OPENED"]["os"] == "macOS"
    assert seen["CRM_SYNCED"]["objects"] == ["deals", "tasks"]


@pytest.mark.anyio
async def test_unknown_and_odd_events_never_raise(anyio_backend: str) -> None:
    client = AsyncGatewayClient(token="wmbly_x")
    got: list[str] = []

    async def handler(topic: str, payload: dict[str, Any]) -> None:
        got.append(payload.get("event_type", "?"))

    client.on_event("SOMETHING_NEW")(handler)
    _deliver(client, "SOMETHING_NEW", {"event_type": "SOMETHING_NEW", "seq": 3})
    _deliver(client, "other.thing", {"seq": "not-a-number"})
    client._handle_raw(json.dumps([None, None, "org:x", "NULL_PAYLOAD", None]))
    client._handle_raw(json.dumps([None, None, "org:x", 7, []]))
    client._handle_raw("not json")
    await asyncio.sleep(0.05)
    assert got == ["SOMETHING_NEW"]


# -- credentials ---------------------------------------------------------


@pytest.mark.parametrize("token", ["wmbly_abc123", "wmat_abc123"])
def test_long_lived_tokens_use_header_not_url(token: str) -> None:
    client = AsyncGatewayClient(token=token, base_url="wss://rt.example.com")
    url = client._build_url()
    assert token not in url
    assert url == "wss://rt.example.com/socket/websocket?vsn=2.0.0"
    assert client._token_in_header


def test_connection_jwt_stays_in_query() -> None:
    client = AsyncGatewayClient(token="eyJ.a.b", base_url="wss://rt.example.com")
    assert "token=eyJ.a.b" in client._build_url()
    assert not client._token_in_header


@pytest.mark.anyio
@pytest.mark.parametrize(
    "token,expect_header", [("wmat_tok", True), ("eyJ.a.b", False)]
)
async def test_handshake_sends_credential_where_gateway_expects_it(
    anyio_backend: str,
    fake_gateway: FakeGateway,
    monkeypatch: pytest.MonkeyPatch,
    token: str,
    expect_header: bool,
) -> None:
    captured: dict[str, Any] = {}
    real_connect = conn.connect

    async def spy(url: str, **kwargs: Any) -> Any:
        captured["url"] = url
        captured["headers"] = kwargs["additional_headers"]
        return await real_connect(url, **kwargs)

    monkeypatch.setattr(conn, "connect", spy)
    client = AsyncGatewayClient(token=token, base_url=fake_gateway.base_url)
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
    await client.close()
    if expect_header:
        assert captured["headers"] == {"X-Warmbly-Token": token}
        assert "token=" not in captured["url"]
    else:
        assert captured["headers"] == {}
        assert f"token={token}" in captured["url"]


# -- refused handshakes ---------------------------------------------------


def _refused(body: dict[str, Any] | bytes, status: int = 403) -> InvalidStatus:
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    return InvalidStatus(Response(status, "Forbidden", Headers(), raw))


async def _open_with(
    monkeypatch: pytest.MonkeyPatch, exc: InvalidStatus
) -> AsyncGatewayClient:
    async def bad(*args: Any, **kwargs: Any) -> Any:
        raise exc

    monkeypatch.setattr(conn, "connect", bad)
    client = AsyncGatewayClient(token="wmat_t", base_url="ws://localhost:1")
    await client._open_socket()
    return client


@pytest.mark.anyio
async def test_refused_handshake_reports_code_and_reason(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    exc = _refused(
        {"code": 4004, "reason": "Access token revoked"},
    )
    with pytest.raises(FatalDisconnect) as info:
        await _open_with(monkeypatch, exc)
    assert info.value.code == 4004
    assert "Access token revoked" in str(info.value)
    assert "HTTP 403" in str(info.value)


@pytest.mark.anyio
async def test_credential_in_query_refusal_is_fatal(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    exc = _refused({"code": 4003, "reason": "Send API keys in the header"})
    with pytest.raises(FatalDisconnect) as info:
        await _open_with(monkeypatch, exc)
    assert info.value.code == 4003


@pytest.mark.anyio
@pytest.mark.parametrize("code", [4007, 4009])
async def test_rate_limited_handshake_is_transient_and_honors_retry(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    exc = _refused({"code": code, "reason": "slow down", "retry_after_ms": 2500})

    async def bad(*args: Any, **kwargs: Any) -> Any:
        raise exc

    monkeypatch.setattr(conn, "connect", bad)
    client = AsyncGatewayClient(token="wmat_t", base_url="ws://localhost:1")
    with pytest.raises(TransientDisconnect):
        await client._open_socket()
    assert client._retry_after == 2.5


@pytest.mark.anyio
async def test_rate_limited_handshake_without_retry_hint_is_transient(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(TransientDisconnect):
        await _open_with(
            monkeypatch, _refused({"code": 4007, "retry_after_ms": "soon"})
        )


@pytest.mark.anyio
@pytest.mark.parametrize("body", [b"", b"<html>", b"[1]", b'{"code": "x"}'])
async def test_unreadable_refusal_body_stays_fatal(
    anyio_backend: str, monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    with pytest.raises(FatalDisconnect) as info:
        await _open_with(monkeypatch, _refused(body))
    assert info.value.code is None
    assert "HTTP 403" in str(info.value)


# -- sync client ----------------------------------------------------------


@pytest.mark.anyio
async def test_sync_client_receives_new_event(
    anyio_backend: str, fake_gateway: FakeGateway
) -> None:
    gw = GatewayClient(token="wmat_test", base_url=fake_gateway.base_url)
    fired = threading.Event()
    seen: dict[str, Any] = {}

    @gw.on_event(GatewayEvent.PLACEMENT_TEST_UPDATED)
    def _h(topic: str, payload: dict[str, Any]) -> None:
        seen.update(payload)
        fired.set()

    try:
        await asyncio.wait_for(asyncio.to_thread(gw.connect), _TIMEOUT)
        await asyncio.wait_for(asyncio.to_thread(gw.subscribe, f"org:{ORG}"), _TIMEOUT)
        await fake_gateway.broadcast(
            f"org:{ORG}",
            "PLACEMENT_TEST_UPDATED",
            NEW_EVENTS["PLACEMENT_TEST_UPDATED"],
        )
        assert await asyncio.wait_for(asyncio.to_thread(fired.wait, _TIMEOUT), _TIMEOUT)
        assert seen["test_id"] == "t1"
        assert seen["campaign_id"] == "c1"
    finally:
        await asyncio.to_thread(gw.close)
