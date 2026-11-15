"""Tests for the ``migrations`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly.resources.migrations import Migration, MigrationProviderList

BASE_URL = "https://api.warmbly.com/v1"
MIG_ID = "7d4f0c1e-1b2a-4c3d-9e8f-0a1b2c3d4e5f"
ORG_ID = "0b8c1d2e-3f40-4a5b-8c6d-7e8f9a0b1c2d"
TARGET_ID = "5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9"
CAMPAIGN_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


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


PROVIDERS: dict[str, Any] = {
    "data": [
        {
            "id": "snovio",
            "label": "Snov.io",
            "fields": [
                {"key": "client_id", "label": "Client ID", "secret": False},
                {
                    "key": "client_secret",
                    "label": "Client secret",
                    "secret": True,
                    "help": "Settings, API",
                    "optional": False,
                    "placeholder": "abc",
                    "options": ["us", "eu"],
                },
            ],
            "key_help": "Find it under Settings, API.",
            "key_url": "https://app.snov.io/account/api",
            "kinds": ["campaigns", "leads", "blocklist"],
            "workspaces": False,
            "multi_key": False,
            "mailbox_secrets": False,
            "notes": ["LinkedIn steps do not carry over."],
        }
    ]
}


def _migration(status: str = "running") -> dict[str, Any]:
    """A migration shaped like Go's models.ToolMigration."""
    return {
        "id": MIG_ID,
        "organization_id": ORG_ID,
        "created_by_user_id": "9f8e7d6c-5b4a-4392-8171-605f4e3d2c1b",
        "provider": "instantly",
        "label": "Instantly",
        "status": status,
        "accounts": [{"name": "Ada", "email": "ada@example.com", "plan": "Growth"}],
        "inventory": [
            {
                "workspace": {"id": "", "name": "Main", "key": 0},
                "inventory": {
                    "mailboxes": 3,
                    "campaigns": 2,
                    "leads": -1,
                    "blocklist": 10,
                    "campaign_summaries": [
                        {
                            "id": "c-1",
                            "name": "Q3 outbound",
                            "status": "active",
                            "steps": 4,
                            "leads": 120,
                        }
                    ],
                },
            },
            {
                "workspace": {"id": "ws-2", "name": "Client B", "key": 1},
                "inventory": {
                    "mailboxes": 0,
                    "campaigns": 0,
                    "leads": 0,
                    "blocklist": 0,
                },
                "error": "the key is not allowed to read this",
            },
        ],
        "options": {
            "kinds": ["blocklist", "campaigns", "leads"],
            "campaign_ids": ["c-1"],
            "in_flight": "restart",
            "skip_finished": True,
            "warmup": False,
        },
        "targets": [
            {
                "id": TARGET_ID,
                "migration_id": MIG_ID,
                "workspace": {"id": "", "name": "Main"},
                "organization_id": ORG_ID,
                "organization_name": "Acme",
                "status": "running",
                "phase": "leads",
                "counts": {
                    "blocklist_imported": 10,
                    "mailboxes_queued": 1,
                    "mailboxes_manual": 2,
                    "campaigns_created": 1,
                    "campaigns_skipped": 1,
                    "steps_created": 4,
                    "leads_read": 120,
                    "contacts_imported": 100,
                    "contacts_updated": 15,
                    "leads_enrolled": 90,
                    "leads_not_enrolled": 20,
                    "leads_suppressed": 5,
                    "leads_failed": 0,
                },
                "followup": {
                    "reconnect": [{"email": "bob@acme.com", "kind": "google"}],
                    "notes": ["Step 3 was a LinkedIn step and was left out."],
                    "campaigns": [
                        {
                            "source_id": "c-1",
                            "campaign_id": CAMPAIGN_ID,
                            "name": "Q3 outbound",
                            "missing_senders": ["bob@acme.com"],
                        }
                    ],
                },
                "mailbox_import_id": "2b3c4d5e-6f70-4a8b-9c0d-1e2f3a4b5c6d",
                "category_id": "3c4d5e6f-7081-4b9c-8d0e-1f2a3b4c5d6e",
                "started_at": "2026-11-15T10:00:00Z",
                "updated_at": "2026-11-15T10:05:00Z",
            }
        ],
        "credentials_held": True,
        "started_at": "2026-11-15T10:00:00Z",
        "created_at": "2026-11-15T09:58:00Z",
        "updated_at": "2026-11-15T10:05:00Z",
    }


def _assert_migration(m: Migration) -> None:
    assert isinstance(m, Migration)
    assert m.id == MIG_ID
    assert m.organization_id == ORG_ID
    assert m.provider == "instantly"
    assert m.credentials_held is True
    assert m.accounts[0].email == "ada@example.com"
    assert m.accounts[0].plan == "Growth"
    inv = m.inventory[0]
    assert inv.workspace is not None and inv.workspace.name == "Main"
    assert inv.inventory is not None and inv.inventory.leads == -1
    assert inv.inventory.campaign_summaries[0].steps == 4
    assert m.inventory[1].error == "the key is not allowed to read this"
    assert m.inventory[1].workspace is not None and m.inventory[1].workspace.key == 1
    assert m.options is not None and m.options.in_flight == "restart"
    assert m.options.campaign_ids == ["c-1"]
    assert m.options.skip_finished is True
    target = m.targets[0]
    assert target.organization_name == "Acme"
    assert target.phase == "leads"
    assert target.counts is not None and target.counts.leads_enrolled == 90
    assert target.counts.contacts_updated == 15
    assert target.followup is not None
    assert target.followup.reconnect[0].kind == "google"
    assert target.followup.campaigns[0].campaign_id == CAMPAIGN_ID
    assert target.followup.campaigns[0].missing_senders == ["bob@acme.com"]
    assert target.mailbox_import_id is not None
    assert target.category_id is not None


def _page(data: list[dict[str, Any]], next_cursor: str | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "pagination": {
            "total": None,
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        },
    }


START_KWARGS: dict[str, Any] = {
    "kinds": ["campaigns", "leads"],
    "campaign_ids": ("c-1",),
    "in_flight": "restart",
    "skip_finished": True,
    "warmup": False,
    "targets": [{"workspace_id": "ws-2", "key": 1, "skip": True}],
}
START_BODY = {
    "options": {
        "kinds": ["campaigns", "leads"],
        "campaign_ids": ["c-1"],
        "in_flight": "restart",
        "skip_finished": True,
        "warmup": False,
    },
    "targets": [{"workspace_id": "ws-2", "key": 1, "skip": True}],
}


# -- providers -----------------------------------------------------------------


@respx.mock
def test_providers_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/migrations/providers").mock(
        return_value=httpx.Response(200, json=PROVIDERS)
    )
    out = client.migrations.providers()
    assert isinstance(out, MigrationProviderList)
    assert route.calls.last.request.method == "GET"
    p = out.data[0]
    assert p.id == "snovio"
    assert p.fields[1].key == "client_secret"
    assert p.fields[1].secret is True
    assert p.fields[1].options == ["us", "eu"]
    assert p.kinds == ["campaigns", "leads", "blocklist"]
    assert p.key_url == "https://app.snov.io/account/api"
    assert p.multi_key is False
    assert p.notes == ["LinkedIn steps do not carry over."]


@pytest.mark.anyio
@respx.mock
async def test_providers_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/migrations/providers").mock(
        return_value=httpx.Response(200, json=PROVIDERS)
    )
    out = await aclient.migrations.providers()
    assert route.calls.last.request.method == "GET"
    assert out.data[0].label == "Snov.io"
    assert out.data[0].key_help == "Find it under Settings, API."


# -- list ----------------------------------------------------------------------


@respx.mock
def test_list_sync_auto_pages(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/migrations").mock(
        side_effect=[
            httpx.Response(200, json=_page([_migration()], next_cursor="cur-2")),
            httpx.Response(200, json=_page([{**_migration("completed"), "id": "m2"}])),
        ]
    )
    items = list(client.migrations.list(limit=1))
    assert [m.id for m in items] == [MIG_ID, "m2"]
    _assert_migration(items[0])
    first, second = route.calls[0].request, route.calls[1].request
    assert first.method == "GET"
    assert first.url.params.get("limit") == "1"
    assert "cursor" not in first.url.params
    assert second.url.params.get("cursor") == "cur-2"


@pytest.mark.anyio
@respx.mock
async def test_list_async_auto_pages(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/migrations").mock(
        side_effect=[
            httpx.Response(200, json=_page([_migration()], next_cursor="cur-2")),
            httpx.Response(200, json=_page([{**_migration("failed"), "id": "m2"}])),
        ]
    )
    items = [m async for m in aclient.migrations.list(limit=1, cursor="cur-1")]
    assert [m.status for m in items] == ["running", "failed"]
    _assert_migration(items[0])
    assert route.calls[0].request.url.params.get("cursor") == "cur-1"
    assert route.calls[0].request.url.params.get("limit") == "1"
    assert route.calls[1].request.url.params.get("cursor") == "cur-2"


# -- create --------------------------------------------------------------------


@respx.mock
def test_create_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/migrations").mock(
        return_value=httpx.Response(201, json=_migration("scanning"))
    )
    m = client.migrations.create(
        provider="instantly", credentials=[{"api_key": "sk-src"}], label="Old tool"
    )
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "provider": "instantly",
        "label": "Old tool",
        "credentials": [{"api_key": "sk-src"}],
    }
    assert request.headers.get("idempotency-key")
    assert m.status == "scanning"
    _assert_migration(m)


@pytest.mark.anyio
@respx.mock
async def test_create_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/migrations").mock(
        return_value=httpx.Response(201, json=_migration("scanning"))
    )
    m = await aclient.migrations.create(
        provider="snovio",
        credentials=[{"client_id": "id-1", "client_secret": "s-1"}],
    )
    assert route.calls.last.request.method == "POST"
    assert json.loads(route.calls.last.request.content) == {
        "provider": "snovio",
        "credentials": [{"client_id": "id-1", "client_secret": "s-1"}],
    }
    _assert_migration(m)


# -- retrieve ------------------------------------------------------------------


@respx.mock
def test_retrieve_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/migrations/{MIG_ID}").mock(
        return_value=httpx.Response(200, json=_migration())
    )
    m = client.migrations.retrieve(MIG_ID)
    assert route.calls.last.request.method == "GET"
    _assert_migration(m)


@pytest.mark.anyio
@respx.mock
async def test_retrieve_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/migrations/{MIG_ID}").mock(
        return_value=httpx.Response(200, json=_migration())
    )
    m = await aclient.migrations.retrieve(MIG_ID)
    assert route.calls.last.request.method == "GET"
    _assert_migration(m)


# -- start ---------------------------------------------------------------------


@respx.mock
def test_start_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/migrations/{MIG_ID}/start").mock(
        return_value=httpx.Response(200, json=_migration())
    )
    m = client.migrations.start(MIG_ID, **START_KWARGS)
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == START_BODY
    _assert_migration(m)

    client.migrations.start(MIG_ID, kinds=["blocklist"])
    assert json.loads(route.calls.last.request.content) == {
        "options": {"kinds": ["blocklist"]}
    }


@pytest.mark.anyio
@respx.mock
async def test_start_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/migrations/{MIG_ID}/start").mock(
        return_value=httpx.Response(200, json=_migration())
    )
    m = await aclient.migrations.start(MIG_ID, **START_KWARGS)
    request = route.calls.last.request
    assert request.method == "POST"
    assert json.loads(request.content) == START_BODY
    _assert_migration(m)


# -- cancel / link-senders -----------------------------------------------------


@respx.mock
def test_cancel_and_link_senders_sync(client: Warmbly) -> None:
    cancel = respx.post(f"{BASE_URL}/migrations/{MIG_ID}/cancel").mock(
        return_value=httpx.Response(
            200, json={**_migration("canceled"), "credentials_held": False}
        )
    )
    m = client.migrations.cancel(MIG_ID)
    assert cancel.calls.last.request.method == "POST"
    assert m.status == "canceled"
    assert m.credentials_held is False

    link = respx.post(f"{BASE_URL}/migrations/{MIG_ID}/link-senders").mock(
        return_value=httpx.Response(200, json=_migration("completed"))
    )
    m = client.migrations.link_senders(MIG_ID)
    assert link.calls.last.request.method == "POST"
    assert m.status == "completed"
    assert m.targets[0].followup is not None
    assert m.targets[0].followup.campaigns[0].name == "Q3 outbound"


@pytest.mark.anyio
@respx.mock
async def test_cancel_and_link_senders_async(aclient: AsyncWarmbly) -> None:
    cancel = respx.post(f"{BASE_URL}/migrations/{MIG_ID}/cancel").mock(
        return_value=httpx.Response(200, json=_migration("canceled"))
    )
    m = await aclient.migrations.cancel(MIG_ID)
    assert cancel.calls.last.request.method == "POST"
    assert m.status == "canceled"

    link = respx.post(f"{BASE_URL}/migrations/{MIG_ID}/link-senders").mock(
        return_value=httpx.Response(200, json=_migration("completed"))
    )
    m = await aclient.migrations.link_senders(MIG_ID)
    assert link.calls.last.request.method == "POST"
    _assert_migration(m)


# -- delete --------------------------------------------------------------------


@respx.mock
def test_delete_sync(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/migrations/{MIG_ID}").mock(
        return_value=httpx.Response(204, headers={"x-request-id": "req_1"})
    )
    out = client.migrations.delete(MIG_ID)
    assert route.calls.last.request.method == "DELETE"
    assert out.request_id == "req_1"
    assert out.id is None


@pytest.mark.anyio
@respx.mock
async def test_delete_async(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/migrations/{MIG_ID}").mock(
        return_value=httpx.Response(204, headers={"x-request-id": "req_2"})
    )
    out = await aclient.migrations.delete(MIG_ID)
    assert route.calls.last.request.method == "DELETE"
    assert out.request_id == "req_2"
