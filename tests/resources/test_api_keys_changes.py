"""API keys: permanent delete, the grantable catalog, and the analytics window."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, last, v  # noqa: F401


@respx.mock
@pytest.mark.anyio
async def test_api_keys_permanent_delete_and_catalog(dual: Any) -> None:
    c = dual.api_keys

    gone = respx.delete(f"{BASE_URL}/api-keys/ak_1/permanent").mock(
        return_value=httpx.Response(200, json={"status": "deleted"})
    )
    assert (await v(c.delete_permanently("ak_1"))).status == "deleted"
    assert last(gone).method == "DELETE"
    assert last(gone).url.path == "/v1/api-keys/ak_1/permanent"

    respx.get(f"{BASE_URL}/api-keys/permissions").mock(
        return_value=httpx.Response(
            200,
            json={
                "permissions": [
                    {
                        "name": "READ_EMAILS",
                        "value": 1,
                        "description": "View email accounts",
                        "category": "read",
                    }
                ],
                "presets": {"read_only": 1, "full_access": 3},
                "grantable": 1,
                "app_scopes": 2,
            },
        )
    )
    cat = await v(c.permissions())
    assert cat.permissions[0].name == "READ_EMAILS"
    assert cat.presets == {"read_only": 1, "full_access": 3}
    assert cat.grantable == 1
    assert cat.app_scopes == 2

    respx.get(f"{BASE_URL}/api-keys/usage/analytics").mock(
        return_value=httpx.Response(
            200,
            json={
                "api_key_id": "ak_1",
                "from": "2026-10-01T00:00:00Z",
                "to": "2026-10-02T00:00:00Z",
                "interval": "hour",
                "buckets": [{"bucket": "2026-10-01T00:00:00Z", "total": 3}],
                "endpoints": [{"endpoint": "/contacts", "count": 3}],
                "total": 3,
                "errors": 0,
            },
        )
    )
    an = await v(c.usage_analytics())
    assert an.from_ == "2026-10-01T00:00:00Z"
    assert an.to == "2026-10-02T00:00:00Z"
    assert an.interval == "hour"
    assert an.buckets[0]["total"] == 3
    assert an.endpoints[0]["endpoint"] == "/contacts"
    assert (an.total, an.errors) == (3, 0)
