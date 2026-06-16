"""Edge-case coverage for pagination, timezones, and oauth_applications.

Targets remaining uncovered lines: multi-page cursor following on the sync and
async paginators, the ``has_next_page`` true/false branches, the timezones
``_wrap_bare_list`` validator (bare list AND envelope), and the
oauth_applications ``retrieve`` method on both sync and async clients.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly
from warmbly._exceptions import WarmblyError
from warmbly._pagination import AsyncCursorPage, SyncCursorPage

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


def _page(
    data: list[dict],
    *,
    next_cursor: str | None = None,
    has_more: bool = False,
) -> dict:
    return {
        "data": data,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total": len(data),
        },
    }


# ===========================================================================
# _pagination: sync multi-page auto-iteration follows the cursor
# ===========================================================================
@respx.mock
def test_sync_pagination_follows_cursor(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns").mock(
        side_effect=[
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_1", "name": "A", "status": "draft"}],
                    next_cursor="cur_2",
                    has_more=True,
                ),
            ),
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_2", "name": "B", "status": "draft"}],
                    next_cursor=None,
                    has_more=False,
                ),
            ),
        ]
    )

    ids = [c.id for c in client.campaigns.list()]

    assert ids == ["camp_1", "camp_2"]
    assert len(route.calls) == 2
    # First request carries no cursor; the second follows ?cursor=cur_2.
    assert route.calls[0].request.url.params.get("cursor") is None
    assert route.calls[1].request.url.params.get("cursor") == "cur_2"


@respx.mock
def test_sync_page_has_next_page_branches(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/campaigns").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [{"id": "camp_1", "name": "A", "status": "draft"}],
                next_cursor="cur_2",
                has_more=True,
            ),
        )
    )

    page = client.campaigns.list()
    assert isinstance(page, SyncCursorPage)
    # has_more True AND a truthy next_cursor -> True
    assert page.has_next_page() is True
    assert route.called


def test_has_next_page_false_when_cursor_falsy() -> None:
    # has_more True but next_cursor falsy -> False (line ~58 branch).
    page = SyncCursorPage(
        data=[1, 2],
        next_cursor=None,
        has_more=True,
        total=2,
    )
    assert page.has_next_page() is False

    # has_more False -> also False.
    page2 = SyncCursorPage(
        data=[1],
        next_cursor="cur_x",
        has_more=False,
        total=1,
    )
    assert page2.has_next_page() is False


def test_sync_get_next_page_raises_when_no_next() -> None:
    page = SyncCursorPage(data=[1], next_cursor=None, has_more=False, total=1)
    with pytest.raises(WarmblyError):
        page.get_next_page()


def test_sync_page_repr() -> None:
    page = SyncCursorPage(data=[1, 2], next_cursor="c", has_more=True, total=2)
    text = repr(page)
    assert "SyncCursorPage" in text
    assert "items=2" in text
    assert "has_more=True" in text
    assert "next_cursor='c'" in text


@pytest.mark.anyio
async def test_async_get_next_page_raises_when_no_next() -> None:
    page: AsyncCursorPage[int] = AsyncCursorPage(
        data=[1], next_cursor=None, has_more=False, total=1
    )
    with pytest.raises(WarmblyError):
        await page.get_next_page()


# ===========================================================================
# _pagination: async paginator (async for AND await-then-iterate-pages)
# ===========================================================================
@pytest.mark.anyio
@respx.mock
async def test_async_pagination_async_for_follows_cursor(
    aclient: AsyncWarmbly,
) -> None:
    route = respx.get(f"{BASE_URL}/campaigns").mock(
        side_effect=[
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_1", "name": "A", "status": "draft"}],
                    next_cursor="cur_2",
                    has_more=True,
                ),
            ),
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_2", "name": "B", "status": "draft"}],
                    next_cursor=None,
                    has_more=False,
                ),
            ),
        ]
    )

    ids = [c.id async for c in aclient.campaigns.list()]

    assert ids == ["camp_1", "camp_2"]
    assert len(route.calls) == 2
    assert route.calls[1].request.url.params.get("cursor") == "cur_2"


@pytest.mark.anyio
@respx.mock
async def test_async_pagination_await_then_get_next_page(
    aclient: AsyncWarmbly,
) -> None:
    route = respx.get(f"{BASE_URL}/campaigns").mock(
        side_effect=[
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_1", "name": "A", "status": "draft"}],
                    next_cursor="cur_2",
                    has_more=True,
                ),
            ),
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_2", "name": "B", "status": "draft"}],
                    next_cursor=None,
                    has_more=False,
                ),
            ),
        ]
    )

    # await -> first AsyncCursorPage.
    page = await aclient.campaigns.list(limit=1)
    assert [c.id for c in page.data] == ["camp_1"]
    assert page.has_next_page() is True

    # Follow the cursor explicitly.
    next_page = await page.get_next_page()
    assert [c.id for c in next_page.data] == ["camp_2"]
    assert next_page.has_next_page() is False
    assert route.calls[1].request.url.params.get("cursor") == "cur_2"


@pytest.mark.anyio
@respx.mock
async def test_async_pagination_await_then_aiter_page(
    aclient: AsyncWarmbly,
) -> None:
    respx.get(f"{BASE_URL}/campaigns").mock(
        side_effect=[
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_1", "name": "A", "status": "draft"}],
                    next_cursor="cur_2",
                    has_more=True,
                ),
            ),
            httpx.Response(
                200,
                json=_page(
                    [{"id": "camp_2", "name": "B", "status": "draft"}],
                    next_cursor=None,
                    has_more=False,
                ),
            ),
        ]
    )

    page = await aclient.campaigns.list()
    # Iterating the page itself auto-fetches subsequent pages.
    ids = [c.id async for c in page]
    assert ids == ["camp_1", "camp_2"]


# ===========================================================================
# timezones: _wrap_bare_list accepts a bare list AND a {"data": [...]} envelope
# ===========================================================================
@respx.mock
def test_timezones_bare_list(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/timezones").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"name": "America/New_York", "offset": "-05:00"},
                {"name": "UTC", "offset": "+00:00"},
            ],
        )
    )

    result = client.timezones.list()

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/timezones"
    assert [tz["name"] for tz in result.data] == ["America/New_York", "UTC"]


@respx.mock
def test_timezones_envelope(client: Warmbly) -> None:
    # The envelope passthrough branch (value is not a list).
    route = respx.get(f"{BASE_URL}/timezones").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"name": "Europe/London", "offset": "+00:00"}]},
        )
    )

    result = client.timezones.list()

    assert route.called
    assert [tz["name"] for tz in result.data] == ["Europe/London"]


@pytest.mark.anyio
@respx.mock
async def test_timezones_async_both_shapes(aclient: AsyncWarmbly) -> None:
    respx.get(f"{BASE_URL}/timezones").mock(
        return_value=httpx.Response(200, json=[{"name": "UTC"}])
    )
    bare = await aclient.timezones.list()
    assert [tz["name"] for tz in bare.data] == ["UTC"]

    respx.get(f"{BASE_URL}/timezones").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "Asia/Tokyo"}]})
    )
    envelope = await aclient.timezones.list()
    assert [tz["name"] for tz in envelope.data] == ["Asia/Tokyo"]


# ===========================================================================
# oauth_applications: retrieve (sync) + list (sync)
# ===========================================================================
@respx.mock
def test_oauth_applications_sync_retrieve(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "app_1",
                "name": "App",
                "client_id": "cid",
                "scopes": 7,
                "redirect_uris": ["https://e/cb"],
            },
        )
    )

    app = client.oauth_applications.retrieve("app_1")

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/oauth/applications/app_1"
    assert app.id == "app_1"
    assert app.client_id == "cid"
    assert app.scopes == 7
    assert list(app.redirect_uris) == ["https://e/cb"]


@respx.mock
def test_oauth_applications_sync_create_and_list(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(
            201,
            json={"id": "app_1", "name": "App", "client_secret": "wmcs_secret"},
        )
    )
    created = client.oauth_applications.create(
        name="App", scopes=3, redirect_uris=["https://e/cb"], description="d"
    )
    assert created.client_secret == "wmcs_secret"
    assert create.calls.last.request.method == "POST"

    list_route = respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(200, json=_page([{"id": "app_1", "name": "App"}]))
    )
    ids = [a.id for a in client.oauth_applications.list(limit=10)]
    assert ids == ["app_1"]
    assert list_route.calls.last.request.url.params.get("limit") == "10"


@respx.mock
def test_oauth_applications_sync_update(client: Warmbly) -> None:
    import json

    route = respx.patch(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(200, json={"id": "app_1", "name": "New"})
    )
    client.oauth_applications.update("app_1", name="New", scopes=5)
    assert json.loads(route.calls.last.request.content) == {
        "name": "New",
        "scopes": 5,
    }


@pytest.mark.anyio
@respx.mock
async def test_oauth_applications_async_retrieve(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/oauth/applications/app_2").mock(
        return_value=httpx.Response(
            200, json={"id": "app_2", "name": "App2", "client_id": "cid2"}
        )
    )

    app = await aclient.oauth_applications.retrieve("app_2")

    assert route.calls.last.request.method == "GET"
    assert route.calls.last.request.url.path == "/v1/oauth/applications/app_2"
    assert app.id == "app_2"
    assert app.client_id == "cid2"


@respx.mock
def test_oauth_applications_sync_delete_and_secrets(client: Warmbly) -> None:
    rotate = respx.post(f"{BASE_URL}/oauth/applications/app_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"client_secret": "wmcs_new"})
    )
    assert client.oauth_applications.rotate_secret("app_1").client_secret == (
        "wmcs_new"
    )
    assert rotate.calls.last.request.method == "POST"

    secret = respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "whsec_1"})
    )
    assert client.oauth_applications.webhook_secret("app_1").webhook_secret == (
        "whsec_1"
    )
    assert secret.calls.last.request.method == "GET"

    rotate_wh = respx.post(
        f"{BASE_URL}/oauth/applications/app_1/webhook-secret/rotate"
    ).mock(return_value=httpx.Response(200, json={"webhook_secret": "whsec_2"}))
    assert (
        client.oauth_applications.rotate_webhook_secret("app_1").webhook_secret
    ) == "whsec_2"
    assert rotate_wh.calls.last.request.method == "POST"

    delete = respx.delete(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.oauth_applications.delete("app_1") is None
    assert delete.calls.last.request.method == "DELETE"


@pytest.mark.anyio
@respx.mock
async def test_oauth_applications_async_full(aclient: AsyncWarmbly) -> None:
    import json

    create = respx.post(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(
            201, json={"id": "app_1", "name": "App", "client_secret": "s"}
        )
    )
    created = await aclient.oauth_applications.create(
        name="App", scopes=3, redirect_uris=["https://e/cb"], description="d"
    )
    assert created.client_secret == "s"
    assert json.loads(create.calls.last.request.content) == {
        "name": "App",
        "scopes": 3,
        "redirect_uris": ["https://e/cb"],
        "description": "d",
    }

    list_route = respx.get(f"{BASE_URL}/oauth/applications").mock(
        return_value=httpx.Response(200, json=_page([{"id": "app_1", "name": "App"}]))
    )
    assert [a.id async for a in aclient.oauth_applications.list()] == ["app_1"]
    assert list_route.called

    update = respx.patch(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(200, json={"id": "app_1", "name": "New"})
    )
    await aclient.oauth_applications.update("app_1", name="New", scopes=9)
    assert json.loads(update.calls.last.request.content) == {
        "name": "New",
        "scopes": 9,
    }

    respx.post(f"{BASE_URL}/oauth/applications/app_1/rotate-secret").mock(
        return_value=httpx.Response(200, json={"client_secret": "new"})
    )
    assert (
        await aclient.oauth_applications.rotate_secret("app_1")
    ).client_secret == "new"

    respx.get(f"{BASE_URL}/oauth/applications/app_1/webhook-secret").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "w1"})
    )
    assert (
        await aclient.oauth_applications.webhook_secret("app_1")
    ).webhook_secret == "w1"

    respx.post(f"{BASE_URL}/oauth/applications/app_1/webhook-secret/rotate").mock(
        return_value=httpx.Response(200, json={"webhook_secret": "w2"})
    )
    assert (
        await aclient.oauth_applications.rotate_webhook_secret("app_1")
    ).webhook_secret == "w2"

    delete = respx.delete(f"{BASE_URL}/oauth/applications/app_1").mock(
        return_value=httpx.Response(204)
    )
    assert await aclient.oauth_applications.delete("app_1") is None
    assert delete.calls.last.request.method == "DELETE"
