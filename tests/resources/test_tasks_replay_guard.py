"""Dead-letter replay refusals and the ``resolved`` status filter."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, ConflictError, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
REFUSAL = {
    "error": "Conflict",
    "message": "This task cannot be replayed.",
    "code": "conflict",
    "request_id": "r1",
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


def _page() -> dict[str, object]:
    return {
        "data": [{"id": "d1", "status": "resolved", "task_type": "send"}],
        "pagination": {"next_cursor": None, "has_more": False, "total": 1},
    }


@respx.mock
def test_replay_refused_sync(client: Warmbly) -> None:
    respx.post(f"{BASE_URL}/tasks/dlq/d1/replay").mock(
        return_value=httpx.Response(409, json=REFUSAL, headers={"X-Request-Id": "r1"})
    )
    with pytest.raises(ConflictError) as info:
        client.tasks.replay("d1")
    assert info.value.status_code == 409
    assert info.value.request_id == "r1"


@respx.mock
def test_list_resolved_sync(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/tasks/dlq").mock(
        return_value=httpx.Response(200, json=_page())
    )
    rows = list(client.tasks.list_dead_letters(status="resolved"))
    assert route.calls.last.request.url.params["status"] == "resolved"
    assert rows[0].status == "resolved"


@respx.mock
@pytest.mark.anyio
async def test_replay_refused_async(aclient: AsyncWarmbly) -> None:
    respx.post(f"{BASE_URL}/tasks/dlq/d1/replay").mock(
        return_value=httpx.Response(409, json=REFUSAL)
    )
    with pytest.raises(ConflictError):
        await aclient.tasks.replay("d1")


@respx.mock
@pytest.mark.anyio
async def test_list_resolved_async(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/tasks/dlq").mock(
        return_value=httpx.Response(200, json=_page())
    )
    rows = [r async for r in aclient.tasks.list_dead_letters(status="resolved")]
    assert route.calls.last.request.url.params["status"] == "resolved"
    assert rows[0].status == "resolved"
