"""Mailbox diagnostic participation, shared limits and send-hold recovery."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.emails import EmailAccount

BASE_URL = "https://api.warmbly.com/v1"
EMAIL_ID = "11111111-1111-1111-1111-111111111111"

ACCOUNT: dict[str, Any] = {
    "id": EMAIL_ID,
    "email": "sam@acme.io",
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 120,
    "rolling_recipient_limit": None,
}

RESOLUTION = {
    "held_task_id": "22222222-2222-2222-2222-222222222222",
    "held_reason": "unknown",
    "evidence_type": "operator_confirmed_sent",
    "message_id": "abc@example.com",
}

BODY: dict[str, Any] = {
    "test_mode": "diagnostic",
    "test_send_enabled": True,
    "test_receive_enabled": False,
    "shared_daily_limit": 120,
    "rolling_recipient_limit": 0,
    "send_recovery_resolution": RESOLUTION,
}


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


def _check(account: EmailAccount) -> None:
    assert account.test_mode == "diagnostic"
    assert account.test_send_enabled is True
    assert account.test_receive_enabled is False
    assert account.shared_daily_limit == 120
    assert account.rolling_recipient_limit is None


@respx.mock
def test_update_diagnostic_fields_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/{EMAIL_ID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check(client.emails.update(EMAIL_ID, **BODY))
    assert json.loads(route.calls.last.request.content) == BODY


@respx.mock
def test_update_omits_unset_diagnostic_fields_sync(client: Warmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/{EMAIL_ID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    client.emails.update(EMAIL_ID, name="Sam")
    assert json.loads(route.calls.last.request.content) == {"name": "Sam"}


@respx.mock
def test_retrieve_diagnostic_fields_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EMAIL_ID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check(client.emails.retrieve(EMAIL_ID))


@respx.mock
@pytest.mark.anyio
async def test_update_diagnostic_fields_async(aclient: AsyncWarmbly) -> None:
    route = respx.patch(f"{BASE_URL}/emails/{EMAIL_ID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check(await aclient.emails.update(EMAIL_ID, **BODY))
    assert json.loads(route.calls.last.request.content) == BODY


@respx.mock
@pytest.mark.anyio
async def test_retrieve_diagnostic_fields_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/emails/{EMAIL_ID}").mock(
        return_value=httpx.Response(200, json=ACCOUNT)
    )
    _check(await aclient.emails.retrieve(EMAIL_ID))
