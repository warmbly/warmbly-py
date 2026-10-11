"""``GET /api-keys/permissions`` delegation masks and scope helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import (
    ALL_SCOPES,
    APP_GRANTABLE_SCOPES,
    SCOPES,
    AsyncWarmbly,
    Warmbly,
    mask_to_scopes,
)

BASE_URL = "https://api.warmbly.com/v1"

_BODY = {
    "permissions": [{"name": "read_emails", "value": 1, "category": "read"}],
    "presets": {"read_only": 1},
    "grantable": 3,
    "app_scopes": 8_388_607,
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


@respx.mock
def test_permissions_masks_sync(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(200, json=_BODY)
    )
    perms = client.api_keys.permissions()
    assert perms.grantable == 3
    assert perms.app_scopes == 8_388_607
    assert perms.presets == {"read_only": 1}


@respx.mock
@pytest.mark.anyio
async def test_permissions_masks_async(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(200, json=_BODY)
    )
    perms = await aclient.api_keys.permissions()
    assert perms.grantable == 3
    assert perms.app_scopes == 8_388_607


@respx.mock
def test_permissions_masks_absent_on_older_servers(client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(200, json={"permissions": [], "presets": {}})
    )
    perms = client.api_keys.permissions()
    assert perms.grantable is None
    assert perms.app_scopes is None


def test_app_grantable_scopes_excludes_only_api_keys() -> None:
    assert ALL_SCOPES & ~SCOPES["api_keys"] == APP_GRANTABLE_SCOPES
    assert "api_keys" not in mask_to_scopes(APP_GRANTABLE_SCOPES)
    assert len(mask_to_scopes(APP_GRANTABLE_SCOPES)) == len(SCOPES) - 1
