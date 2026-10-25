"""Helpers for tests that run one scenario against the sync and async clients.

A scenario is written once as an ``async def`` that awaits every call through
:func:`v` (and iterates pages through :func:`items`); the ``dual`` fixture (import ``dual_client``) runs
it with a :class:`warmbly.Warmbly` and again with a :class:`warmbly.AsyncWarmbly`.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture(name="dual", params=["sync", "async"])
async def dual_client(request: pytest.FixtureRequest) -> AsyncIterator[Any]:
    if request.param == "sync":
        c = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
        yield c
        c.close()
    else:
        async with AsyncWarmbly(
            api_key="wmbly_test", base_url=BASE_URL, max_retries=0
        ) as ac:
            yield ac


async def v(value: Any) -> Any:
    """Await *value* when it is awaitable (async client), else return it."""
    if inspect.isawaitable(value):
        return await value
    return value


async def items(page: Any) -> list[Any]:
    """Drain a sync or async auto-paging iterator into a list."""
    if hasattr(page, "__aiter__"):
        return [item async for item in page]
    return list(page)


def page(data: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "data": list(data),
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request
