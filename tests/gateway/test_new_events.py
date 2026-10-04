"""Events added to the gateway catalog: constants and end-to-end delivery."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from conftest import FakeGateway
from warmbly.gateway import AsyncGatewayClient, GatewayEvent

_TIMEOUT = 5.0

_NEW = {
    "DIRECT_EMAIL_OPENED",
    "DIRECT_EMAIL_CLICKED",
    "WARMUP_PLACEMENT",
    "PLACEMENT_TEST_UPDATED",
    "MAILBOX_IMPORT_PROGRESS",
    "CONTACT_IMPORT_PROGRESS",
}


@pytest.mark.parametrize("name", sorted(_NEW))
def test_new_event_constants_match_server_names(name: str) -> None:
    assert getattr(GatewayEvent, name) == name


@pytest.mark.parametrize(
    ("event", "payload"),
    [
        (
            GatewayEvent.PLACEMENT_TEST_UPDATED,
            {"org_id": "o1", "test_id": "t1", "status": "running", "campaign_id": "c1"},
        ),
        (
            GatewayEvent.PLACEMENT_TEST_UPDATED,
            {"org_id": "o1", "batch_id": "b1", "status": "completed"},
        ),
        (
            GatewayEvent.MAILBOX_IMPORT_PROGRESS,
            {"org_id": "o1", "import_id": "i1", "status": "running"},
        ),
        (
            GatewayEvent.CONTACT_IMPORT_PROGRESS,
            {"org_id": "o1", "import_id": "i2", "status": "queued", "extra": [1]},
        ),
        (
            GatewayEvent.WARMUP_PLACEMENT,
            {"email_account_id": "a1", "email": "x@y.z", "status": "spam"},
        ),
        (
            GatewayEvent.DIRECT_EMAIL_OPENED,
            {
                "email_account_id": "a1",
                "client_type": "webmail",
                "device_hidden": True,
                "os": "iOS",
                "browser": "Safari",
            },
        ),
    ],
)
@pytest.mark.anyio
async def test_new_events_reach_handlers_with_payload_intact(
    fake_gateway: FakeGateway, event: str, payload: dict[str, Any]
) -> None:
    client = AsyncGatewayClient(token="t", base_url=fake_gateway.base_url)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_1"), timeout=_TIMEOUT)
        waiter = asyncio.ensure_future(client.wait_for(event, timeout=_TIMEOUT))
        await asyncio.sleep(0)
        await fake_gateway.broadcast("org:org_1", event, payload)
        got = await asyncio.wait_for(waiter, timeout=_TIMEOUT)
        assert got == payload
    finally:
        await client.close()


@pytest.mark.anyio
async def test_unknown_event_is_delivered_without_error(
    fake_gateway: FakeGateway,
) -> None:
    client = AsyncGatewayClient(token="t", base_url=fake_gateway.base_url)
    try:
        await asyncio.wait_for(client.connect(), timeout=_TIMEOUT)
        await asyncio.wait_for(client.subscribe("org:org_1"), timeout=_TIMEOUT)
        waiter = asyncio.ensure_future(
            client.wait_for("SOMETHING_FROM_THE_FUTURE", timeout=_TIMEOUT)
        )
        await asyncio.sleep(0)
        await fake_gateway.broadcast(
            "org:org_1", "SOMETHING_FROM_THE_FUTURE", {"new_field": {"a": 1}}
        )
        assert await asyncio.wait_for(waiter, timeout=_TIMEOUT) == {
            "new_field": {"a": 1}
        }
    finally:
        await client.close()
