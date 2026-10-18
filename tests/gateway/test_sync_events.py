"""Server-sync tests: new realtime event constants and the credential header."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from warmbly.gateway import AsyncGatewayClient, GatewayEvent
from warmbly.gateway import _connection as connection_module
from warmbly.gateway._connection import GatewayError

_NEW_EVENTS = {
    "DIRECT_EMAIL_OPENED",
    "DIRECT_EMAIL_CLICKED",
    "WARMUP_PLACEMENT",
    "MAILBOX_IMPORT_PROGRESS",
    "PLACEMENT_TEST_UPDATED",
    "CONTACT_IMPORT_PROGRESS",
    "CRM_SYNCED",
}


@pytest.mark.parametrize("name", sorted(_NEW_EVENTS))
def test_new_event_constants_match_server_names(name: str) -> None:
    assert getattr(GatewayEvent, name) == name


def test_intent_substring_matches_new_families() -> None:
    # The server keeps an event when any intent token is a substring of its
    # normalized name, so family tokens select the new events.
    assert "PLACEMENT" in GatewayEvent.PLACEMENT_TEST_UPDATED
    assert "IMPORT" in GatewayEvent.MAILBOX_IMPORT_PROGRESS
    assert "IMPORT" in GatewayEvent.CONTACT_IMPORT_PROGRESS


def test_credential_goes_in_handshake_header_not_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    async def fake_connect(url: str, **kwargs: Any) -> Any:
        seen["url"] = url
        seen["headers"] = kwargs["additional_headers"]
        raise OSError("stop here")

    monkeypatch.setattr(connection_module, "connect", fake_connect)
    client = AsyncGatewayClient(token="wmbly_secret", base_url="wss://rt.example.com")
    with pytest.raises(GatewayError):
        asyncio.run(client._open_socket())

    assert seen["headers"] == {"X-Warmbly-Token": "wmbly_secret"}
    assert seen["url"] == "wss://rt.example.com/socket/websocket?vsn=2.0.0"
    assert "wmbly_secret" not in seen["url"]
