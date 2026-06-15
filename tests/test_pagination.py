"""Cursor-pagination tests for the sync and async clients.

Verifies that :class:`~warmbly.SyncCursorPage` / :class:`AsyncCursorPage`
auto-fetch subsequent pages on iteration (passing the ``cursor`` query param),
expose ``has_next_page``/``get_next_page``, and raise when exhausted. ``respx``
serves a two-page sequence so the cursor hand-off is observable.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly, WarmblyError
from warmbly._pagination import AsyncCursorPage, SyncCursorPage

BASE_URL = "https://api.warmbly.com/v1"

pytestmark = pytest.mark.anyio


@pytest.fixture
def sync_client() -> Warmbly:
    client = Warmbly(api_key="wmbly_test_key", base_url=BASE_URL)
    yield client
    client.close()


@pytest.fixture
async def async_client() -> AsyncWarmbly:
    client = AsyncWarmbly(api_key="wmbly_test_key", base_url=BASE_URL)
    yield client
    await client.close()


def _two_page_side_effect() -> list[httpx.Response]:
    """First page has_more with a next_cursor; second page is terminal."""
    return [
        httpx.Response(
            200,
            json={
                "data": [{"id": "k_1", "name": "one"}, {"id": "k_2", "name": "two"}],
                "pagination": {
                    "total": 3,
                    "next_cursor": "cursor_2",
                    "has_more": True,
                },
            },
        ),
        httpx.Response(
            200,
            json={
                "data": [{"id": "k_3", "name": "three"}],
                "pagination": {
                    "total": 3,
                    "next_cursor": None,
                    "has_more": False,
                },
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Auto-iteration across pages
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_iterates_across_pages(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys").mock(side_effect=_two_page_side_effect())
    ids = [item.id for item in sync_client.api_keys.list(limit=2)]

    assert ids == ["k_1", "k_2", "k_3"]
    assert route.call_count == 2
    # First call has no cursor, second call passes the returned cursor.
    assert "cursor" not in route.calls[0].request.url.params
    assert route.calls[0].request.url.params.get("limit") == "2"
    assert route.calls[1].request.url.params.get("cursor") == "cursor_2"


@respx.mock
async def test_async_iterates_across_pages(async_client: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys").mock(side_effect=_two_page_side_effect())
    ids = [item.id async for item in async_client.api_keys.list(limit=2)]

    assert ids == ["k_1", "k_2", "k_3"]
    assert route.call_count == 2
    assert "cursor" not in route.calls[0].request.url.params
    assert route.calls[1].request.url.params.get("cursor") == "cursor_2"


# ---------------------------------------------------------------------------
# has_next_page / get_next_page
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_has_next_page_and_get_next_page(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(side_effect=_two_page_side_effect())

    page1 = sync_client.api_keys.list(limit=2)
    assert isinstance(page1, SyncCursorPage)
    assert page1.has_next_page() is True
    assert page1.next_cursor == "cursor_2"
    assert page1.has_more is True
    assert page1.total == 3
    assert [m.id for m in page1.data] == ["k_1", "k_2"]

    page2 = page1.get_next_page()
    assert isinstance(page2, SyncCursorPage)
    assert page2.has_next_page() is False
    assert [m.id for m in page2.data] == ["k_3"]


@respx.mock
async def test_async_has_next_page_and_get_next_page(
    async_client: AsyncWarmbly,
) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(side_effect=_two_page_side_effect())

    # Awaiting the list() result yields the first concrete page.
    page1 = await async_client.api_keys.list(limit=2)
    assert isinstance(page1, AsyncCursorPage)
    assert page1.has_next_page() is True
    assert page1.next_cursor == "cursor_2"
    assert [m.id for m in page1.data] == ["k_1", "k_2"]

    page2 = await page1.get_next_page()
    assert isinstance(page2, AsyncCursorPage)
    assert page2.has_next_page() is False
    assert [m.id for m in page2.data] == ["k_3"]


# ---------------------------------------------------------------------------
# get_next_page raises when there is no more data
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_get_next_page_raises_when_exhausted(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "k_1", "name": "one"}],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    page = sync_client.api_keys.list()
    assert page.has_next_page() is False
    with pytest.raises(WarmblyError):
        page.get_next_page()


@respx.mock
async def test_async_get_next_page_raises_when_exhausted(
    async_client: AsyncWarmbly,
) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "k_1", "name": "one"}],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    page = await async_client.api_keys.list()
    assert page.has_next_page() is False
    with pytest.raises(WarmblyError):
        await page.get_next_page()


# ---------------------------------------------------------------------------
# has_next_page guards: has_more True but missing cursor -> no next page.
# ---------------------------------------------------------------------------
@respx.mock
def test_sync_has_more_without_cursor_is_terminal(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "k_1", "name": "one"}],
                # has_more True but cursor absent: still treated as no next page.
                "pagination": {"total": 1, "next_cursor": None, "has_more": True},
            },
        )
    )
    page = sync_client.api_keys.list()
    assert page.has_next_page() is False
    with pytest.raises(WarmblyError):
        page.get_next_page()


@respx.mock
def test_sync_single_page_iteration_one_request(sync_client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "k_1", "name": "one"}],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
        )
    )
    ids = [item.id for item in sync_client.api_keys.list()]
    assert ids == ["k_1"]
    assert route.call_count == 1


@respx.mock
def test_sync_models_carry_request_id(sync_client: Warmbly) -> None:
    respx.get(f"{BASE_URL}/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "k_1", "name": "one"}],
                "pagination": {"total": 1, "next_cursor": None, "has_more": False},
            },
            headers={"X-Request-Id": "req_page"},
        )
    )
    page = sync_client.api_keys.list()
    assert page.data[0].request_id == "req_page"
