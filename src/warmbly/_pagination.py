"""Cursor-based pagination.

The Warmbly list endpoints return ``{"data": [...], "pagination": {"total",
"next_cursor", "has_more"}}``. These page objects expose the current ``data``
and transparently fetch subsequent pages, so callers can simply iterate::

    for key in client.api_keys.list():
        ...

    async for key in client.api_keys.list():
        ...

Each page holds a ``fetch_next`` callable supplied by the client, keeping the
pagination logic independent of the HTTP transport.
"""

from __future__ import annotations

from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    Sequence,
    TypeVar,
)

from ._exceptions import WarmblyError

__all__ = ["SyncCursorPage", "AsyncCursorPage"]

ModelT = TypeVar("ModelT")


class _BasePage(Generic[ModelT]):
    """Shared state for a single page of cursor-paginated results."""

    def __init__(
        self,
        *,
        data: Sequence[ModelT],
        next_cursor: str | None,
        has_more: bool,
        total: int | None,
    ) -> None:
        self.data: list[ModelT] = list(data)
        self.next_cursor = next_cursor
        self.has_more = has_more
        self.total = total

    def has_next_page(self) -> bool:
        """Return ``True`` if another page can be fetched."""
        return bool(self.has_more and self.next_cursor)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(items={len(self.data)}, "
            f"has_more={self.has_more}, next_cursor={self.next_cursor!r})"
        )


class SyncCursorPage(_BasePage[ModelT]):
    """A synchronous page that auto-fetches subsequent pages on iteration."""

    def __init__(
        self,
        *,
        data: Sequence[ModelT],
        next_cursor: str | None,
        has_more: bool,
        total: int | None,
        fetch_next: Callable[[str], SyncCursorPage[ModelT]] | None = None,
    ) -> None:
        super().__init__(
            data=data, next_cursor=next_cursor, has_more=has_more, total=total
        )
        self._fetch_next = fetch_next

    def get_next_page(self) -> SyncCursorPage[ModelT]:
        """Fetch and return the next page.

        Raises:
            WarmblyError: If there is no next page.
        """
        if not self.has_next_page() or self._fetch_next is None:
            raise WarmblyError("No next page available.")
        assert self.next_cursor is not None
        return self._fetch_next(self.next_cursor)

    def __iter__(self) -> Iterator[ModelT]:
        page: SyncCursorPage[ModelT] = self
        while True:
            yield from page.data
            if not page.has_next_page() or page._fetch_next is None:
                return
            page = page.get_next_page()


class AsyncCursorPage(_BasePage[ModelT]):
    """An asynchronous page that auto-fetches subsequent pages on ``async for``."""

    def __init__(
        self,
        *,
        data: Sequence[ModelT],
        next_cursor: str | None,
        has_more: bool,
        total: int | None,
        fetch_next: Callable[[str], Awaitable[AsyncCursorPage[ModelT]]] | None = None,
    ) -> None:
        super().__init__(
            data=data, next_cursor=next_cursor, has_more=has_more, total=total
        )
        self._fetch_next = fetch_next

    async def get_next_page(self) -> AsyncCursorPage[ModelT]:
        """Fetch and return the next page.

        Raises:
            WarmblyError: If there is no next page.
        """
        if not self.has_next_page() or self._fetch_next is None:
            raise WarmblyError("No next page available.")
        assert self.next_cursor is not None
        return await self._fetch_next(self.next_cursor)

    async def __aiter__(self) -> AsyncIterator[ModelT]:
        page: AsyncCursorPage[ModelT] = self
        while True:
            for item in page.data:
                yield item
            if not page.has_next_page() or page._fetch_next is None:
                return
            page = await page.get_next_page()
