"""Tests for the ``suppressions`` and ``ai_tools`` resources, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


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


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


# -- suppressions -----------------------------------------------------------


@respx.mock
def test_suppressions_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "sup_1",
                        "email": "spam-trap.example",
                        "kind": "domain",
                        "source": "complaint",
                    }
                ]
            ),
        )
    )
    entries = list(client.suppressions.list(q="example", limit=25))
    assert entries[0].kind == "domain"
    request = _last(listing)
    assert request.url.params.get("q") == "example"
    assert request.url.params.get("limit") == "25"

    add = respx.post(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(200, json={"added": 2, "skipped": ["not an email"]})
    )
    result = client.suppressions.add(
        entries=[
            "a@example.com",
            {"value": "@rival.com", "reason": "competitor"},
            "not an email",
        ],
        reason="manual cleanup",
    )
    assert result.added == 2
    assert list(result.skipped) == ["not an email"]
    assert json.loads(_last(add).content) == {
        "entries": [
            {"value": "a@example.com"},
            {"value": "@rival.com", "reason": "competitor"},
            {"value": "not an email"},
        ],
        "reason": "manual cleanup",
    }

    remove = respx.delete(f"{BASE_URL}/suppressions/sup_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.suppressions.remove("sup_1").deleted is None
    assert _last(remove).url.path == "/v1/suppressions/sup_1"


@respx.mock
@pytest.mark.anyio
async def test_suppressions_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(200, json=_page([{"id": "sup_1"}]))
    )
    assert [s.id async for s in aclient.suppressions.list()] == ["sup_1"]
    assert _last(listing).url.path == "/v1/suppressions"

    add = respx.post(f"{BASE_URL}/suppressions").mock(
        return_value=httpx.Response(200, json={"added": 1, "skipped": []})
    )
    assert (await aclient.suppressions.add(entries=["b@example.com"])).added == 1
    assert json.loads(_last(add).content) == {"entries": [{"value": "b@example.com"}]}

    remove = respx.delete(f"{BASE_URL}/suppressions/sup_1").mock(
        return_value=httpx.Response(204)
    )
    await aclient.suppressions.remove("sup_1")
    assert _last(remove).method == "DELETE"


# -- ai_tools ---------------------------------------------------------------


@respx.mock
def test_ai_tools_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/ai/tools").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "name": "list_campaigns",
                        "description": "List campaigns",
                        "input_schema": {"type": "object", "properties": {}},
                    }
                ]
            ),
        )
    )
    tools = list(client.ai_tools.list())
    assert tools[0].name == "list_campaigns"
    assert tools[0].input_schema == {"type": "object", "properties": {}}
    assert "format" not in _last(listing).url.params

    openai = respx.get(f"{BASE_URL}/ai/tools").mock(
        return_value=httpx.Response(
            200,
            json=_page([{"type": "function", "function": {"name": "list_campaigns"}}]),
        )
    )
    fn = list(client.ai_tools.list(format="openai"))
    assert fn[0].type == "function"
    assert _last(openai).url.params.get("format") == "openai"

    call = respx.post(f"{BASE_URL}/ai/tools/list_campaigns/call").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"name": "list_campaigns", "result": {"campaigns": []}}},
        )
    )
    out = client.ai_tools.call("list_campaigns", arguments={"status": "active"})
    assert out.data is not None
    assert out.data.result == {"campaigns": []}
    assert json.loads(_last(call).content) == {"status": "active"}


@respx.mock
@pytest.mark.anyio
async def test_ai_tools_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/ai/tools").mock(
        return_value=httpx.Response(200, json=_page([{"name": "t"}]))
    )
    assert [t.name async for t in aclient.ai_tools.list(format="hermes")] == ["t"]
    assert _last(listing).url.params.get("format") == "hermes"

    call = respx.post(f"{BASE_URL}/ai/tools/t/call").mock(
        return_value=httpx.Response(200, json={"data": {"name": "t", "result": "ok"}})
    )
    out = await aclient.ai_tools.call("t")
    assert out.data is not None
    assert out.data.result == "ok"
    # A tool that takes no arguments still sends a valid empty JSON object.
    assert json.loads(_last(call).content) == {}
