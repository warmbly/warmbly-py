"""Teams: the shape the server sends and the body it binds."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, page, v  # noqa: F401

TEAM = {
    "id": "tm_1",
    "organization_id": "org_1",
    "name": "Sales",
    "color": "#94a3b8",
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-02T00:00:00Z",
    "members": [
        {
            "user_id": "usr_1",
            "email": "a@x.com",
            "name": "Ada Lovelace",
            "added_at": "2026-10-01T00:00:00Z",
        }
    ],
}


@respx.mock
@pytest.mark.anyio
async def test_teams_shape_and_bodies(dual: Any) -> None:
    c = dual.teams

    respx.get(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(200, json=page([TEAM]))
    )
    team = (await items(c.list()))[0]
    assert (team.id, team.organization_id) == ("tm_1", "org_1")
    assert (team.name, team.color) == ("Sales", "#94a3b8")
    assert team.created_at == "2026-10-01T00:00:00Z"
    assert team.updated_at == "2026-10-02T00:00:00Z"
    member = team.members[0]
    assert (member.user_id, member.email) == ("usr_1", "a@x.com")
    assert (member.name, member.added_at) == (
        "Ada Lovelace",
        "2026-10-01T00:00:00Z",
    )

    create = respx.post(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(201, json=TEAM)
    )
    await v(c.create(name="Sales", color="#94a3b8"))
    assert json.loads(last(create).content) == {"name": "Sales", "color": "#94a3b8"}

    update = respx.patch(f"{BASE_URL}/teams/tm_1").mock(
        return_value=httpx.Response(200, json=TEAM)
    )
    await v(c.update("tm_1", name="Sales EU"))
    assert json.loads(last(update).content) == {"name": "Sales EU"}
