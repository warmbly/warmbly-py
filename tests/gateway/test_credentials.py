"""Where the gateway client puts its credential on the handshake."""

from __future__ import annotations

import asyncio

import pytest

from conftest import FakeGateway
from warmbly.gateway import AsyncGatewayClient, GatewayClient

_TIMEOUT = 5.0


def _request(fake_gateway: FakeGateway):  # type: ignore[no-untyped-def]
    (connection,) = fake_gateway.connections
    return connection.request


@pytest.mark.parametrize("token", ["wmbly_abc123", "wmat_abc123"])
def test_long_lived_credentials_use_header_not_url(token: str) -> None:
    client = AsyncGatewayClient(token=token, base_url="wss://rt.example.com")
    assert client._build_headers() == {"X-Warmbly-Token": token}
    url = client._build_url()
    assert url == "wss://rt.example.com/socket/websocket?vsn=2.0.0"
    assert token not in url


def test_ticket_stays_in_query_without_header() -> None:
    client = AsyncGatewayClient(token="eyJ.ticket.sig", base_url="wss://rt.example.com")
    assert client._build_headers() == {}
    assert "token=eyJ.ticket.sig" in client._build_url()


@pytest.mark.anyio
async def test_async_handshake_sends_api_key_header(fake_gateway: FakeGateway) -> None:
    client = AsyncGatewayClient(token="wmbly_key", base_url=fake_gateway.base_url)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        request = _request(fake_gateway)
        assert request.headers["X-Warmbly-Token"] == "wmbly_key"
        assert "token=" not in request.path
    finally:
        await client.close()


@pytest.mark.anyio
async def test_async_handshake_sends_ticket_in_query(fake_gateway: FakeGateway) -> None:
    client = AsyncGatewayClient(token="ticket.jwt.x", base_url=fake_gateway.base_url)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        request = _request(fake_gateway)
        assert "X-Warmbly-Token" not in request.headers
        assert "token=ticket.jwt.x" in request.path
    finally:
        await client.close()


@pytest.mark.anyio
async def test_sync_handshake_sends_oauth_header(fake_gateway: FakeGateway) -> None:
    client = GatewayClient(token="wmat_tok", base_url=fake_gateway.base_url)
    try:
        await asyncio.to_thread(client.connect)
        assert _request(fake_gateway).headers["X-Warmbly-Token"] == "wmat_tok"
    finally:
        await asyncio.to_thread(client.close)
