"""Integration tests for :class:`AsyncGatewayClient` against a fake gateway.

These drive the real client (its supervisor, receive loop, reply correlation,
presence and resume tracking, and dispatch) over a genuine WebSocket connection
to the in-process :class:`~tests.gateway.conftest.FakeGateway` fixture using a
``ws://`` base URL. All timeouts are short so the suite stays fast.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from conftest import FakeGateway
from warmbly.gateway import AsyncGatewayClient, GatewayEvent

# Bound every awaited rendezvous so a hang fails fast instead of stalling CI.
_TIMEOUT = 5.0


async def _make_client(gateway: FakeGateway) -> AsyncGatewayClient:
    client = AsyncGatewayClient(token="wmbly_test_token", base_url=gateway.base_url)
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
    return client


@pytest.mark.anyio
async def test_connect_opens_and_becomes_ready(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    try:
        assert client._ws is not None
    finally:
        await client.close()


@pytest.mark.anyio
async def test_subscribe_returns_join_reply(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    try:
        reply = await asyncio.wait_for(
            client.subscribe("org:org_123"), timeout=_TIMEOUT
        )
        assert reply == {"seq": 0, "resume_supported": True}
        assert reply["resume_supported"] is True
    finally:
        await client.close()


@pytest.mark.anyio
async def test_subscribe_sends_intents_in_join_params(
    fake_gateway: FakeGateway,
) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(
            client.subscribe("org:org_123", intents=["CAMPAIGN"]),
            timeout=_TIMEOUT,
        )
        assert fake_gateway.join_params["org:org_123"] == {"intents": ["CAMPAIGN"]}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_on_event_handler_receives_broadcast(
    fake_gateway: FakeGateway,
) -> None:
    client = await _make_client(fake_gateway)
    received: asyncio.Future[tuple[str, dict[str, Any]]] = (
        asyncio.get_running_loop().create_future()
    )

    @client.on_event(GatewayEvent.CAMPAIGN_STARTED)
    async def _handler(topic: str, payload: dict[str, Any]) -> None:
        if not received.done():
            received.set_result((topic, payload))

    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        await fake_gateway.broadcast(
            "org:org_123", GatewayEvent.CAMPAIGN_STARTED, {"campaign_id": "cmp_1"}
        )
        topic, payload = await asyncio.wait_for(received, timeout=_TIMEOUT)
        assert topic == "org:org_123"
        assert payload == {"campaign_id": "cmp_1"}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_wait_for_resolves_on_matching_event(
    fake_gateway: FakeGateway,
) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        waiter = asyncio.ensure_future(
            client.wait_for(GatewayEvent.EMAIL_SENT, timeout=_TIMEOUT)
        )
        # Give the waiter a tick to register before broadcasting.
        await asyncio.sleep(0)
        await fake_gateway.broadcast(
            "org:org_123", GatewayEvent.EMAIL_SENT, {"email_id": "eml_9"}
        )
        payload = await asyncio.wait_for(waiter, timeout=_TIMEOUT)
        assert payload == {"email_id": "eml_9"}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_wait_for_with_check_predicate(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        waiter = asyncio.ensure_future(
            client.wait_for(
                GatewayEvent.CAMPAIGN_PROGRESS,
                check=lambda _topic, p: p.get("pct") == 100,
                timeout=_TIMEOUT,
            )
        )
        await asyncio.sleep(0)
        # First broadcast fails the check and is ignored.
        await fake_gateway.broadcast(
            "org:org_123", GatewayEvent.CAMPAIGN_PROGRESS, {"pct": 50}
        )
        await fake_gateway.broadcast(
            "org:org_123", GatewayEvent.CAMPAIGN_PROGRESS, {"pct": 100}
        )
        payload = await asyncio.wait_for(waiter, timeout=_TIMEOUT)
        assert payload == {"pct": 100}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_wait_for_times_out(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        with pytest.raises((asyncio.TimeoutError, TimeoutError)):
            await client.wait_for("NEVER_FIRED", timeout=0.2)
    finally:
        await client.close()


@pytest.mark.anyio
async def test_presence_reflects_presence_state_broadcast(
    fake_gateway: FakeGateway,
) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        assert client.presence("org:org_123") == {}

        snapshot = {
            "usr_1": {"metas": [{"online_at": 1, "name": "Ada"}]},
            "usr_2": {"metas": [{"online_at": 2, "name": "Bob"}]},
        }
        # Wait on the dispatched event to know the frame was processed.
        waiter = asyncio.ensure_future(
            client.wait_for("presence_state", timeout=_TIMEOUT)
        )
        await asyncio.sleep(0)
        await fake_gateway.broadcast("org:org_123", "presence_state", snapshot)
        await asyncio.wait_for(waiter, timeout=_TIMEOUT)

        presence = client.presence("org:org_123")
        assert set(presence) == {"usr_1", "usr_2"}
        assert presence["usr_1"]["metas"][0]["name"] == "Ada"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_presence_diff_updates_state(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)

        state_waiter = asyncio.ensure_future(
            client.wait_for("presence_state", timeout=_TIMEOUT)
        )
        await asyncio.sleep(0)
        await fake_gateway.broadcast(
            "org:org_123",
            "presence_state",
            {"usr_1": {"metas": [{"online_at": 1}]}},
        )
        await asyncio.wait_for(state_waiter, timeout=_TIMEOUT)

        diff_waiter = asyncio.ensure_future(
            client.wait_for("presence_diff", timeout=_TIMEOUT)
        )
        await asyncio.sleep(0)
        await fake_gateway.broadcast(
            "org:org_123",
            "presence_diff",
            {
                "joins": {"usr_2": {"metas": [{"online_at": 3}]}},
                "leaves": {"usr_1": {"metas": [{"online_at": 1}]}},
            },
        )
        await asyncio.wait_for(diff_waiter, timeout=_TIMEOUT)

        presence = client.presence("org:org_123")
        assert set(presence) == {"usr_2"}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_seq_tracking_updates_from_broadcasts(
    fake_gateway: FakeGateway,
) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        assert client._resume.last_seq("org:org_123") is None

        for seq in (1, 2, 5):
            waiter = asyncio.ensure_future(
                client.wait_for(GatewayEvent.EMAIL_SENT, timeout=_TIMEOUT)
            )
            await asyncio.sleep(0)
            await fake_gateway.broadcast(
                "org:org_123", GatewayEvent.EMAIL_SENT, {"seq": seq}
            )
            await asyncio.wait_for(waiter, timeout=_TIMEOUT)

        # Highest observed seq wins; lower/out-of-order seqs don't regress it.
        assert client._resume.last_seq("org:org_123") == 5
    finally:
        await client.close()


@pytest.mark.anyio
async def test_push_resolves_with_reply(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    try:
        await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
        reply = await asyncio.wait_for(
            client.push("org:org_123", "ping", {"n": 1}), timeout=_TIMEOUT
        )
        # The fake replies ok with an empty response object.
        assert reply == {}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_clean_close_is_idempotent(fake_gateway: FakeGateway) -> None:
    client = await _make_client(fake_gateway)
    await asyncio.wait_for(client.subscribe("org:org_123"), timeout=_TIMEOUT)
    await asyncio.wait_for(client.close(), timeout=_TIMEOUT)
    assert client._ws is None
    # A second close must not raise.
    await asyncio.wait_for(client.close(), timeout=_TIMEOUT)
